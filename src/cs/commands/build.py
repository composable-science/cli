"""Build command - Execute pipeline steps (CSF §6)"""

import click
import subprocess
import glob
from pathlib import Path
from typing import List, Optional
import os
import time
from cs.utils.output import success, error, info, warning
from cs.config import CSFConfig
from cs.commands.doctor import ensure_nix_shell

@click.command()
@click.argument('step', required=False)
@click.option('--force', '-f', is_flag=True, help='Force rebuild even if outputs are up-to-date')
@click.pass_context
def build_command(ctx, step, force):
    ensure_nix_shell()
    """Build entire pipeline or a single named step (CSF §6)"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    
    if not config.has_manifest():
        error("No flake.nix found. Run 'cs init <template>' to create a new project.", output_json, exit_code=64)
        return
    
    manifest = config.load_manifest()
    if not manifest:
        # The config loader already printed an error
        return
    
    # Validate manifest
    validation_errors = validate_manifest(manifest)
    if validation_errors:
        for err in validation_errors:
            error(err, output_json, exit_code=4)
        return
    
    pipeline_steps = manifest.get('pipeline', [])
    
    if step:
        # Build single step plus stale predecessors
        steps_to_build = get_steps_to_build_for_target(pipeline_steps, step, force)
    else:
        # Build entire pipeline
        steps_to_build = get_steps_to_build(pipeline_steps, force)
    
    if not steps_to_build:
        success("All outputs are up-to-date", output_json)
        return
    
    # Create outputs directory
    config.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Execute steps
    for step_config in steps_to_build:
        step_name = step_config['name']
        info(f"Building step: {step_name}", output_json)
        
        exit_code = execute_step(step_config, config, output_json)
        if exit_code != 0:
            error(f"Step '{step_name}' failed with exit code {exit_code}", output_json, exit_code=66)
            return
        
        success(f"Step '{step_name}' completed", output_json)
    
    success("Pipeline build completed", output_json)

def validate_manifest(manifest: dict) -> List[str]:
    """Validate manifest according to CSF §5.4"""
    errors = []
    
    # Check required sections
    if 'package' not in manifest:
        errors.append("Missing required [package] section")
    
    if 'pipeline' not in manifest:
        errors.append("Missing required [[pipeline]] section")
        return errors
    
    pipeline = manifest['pipeline']
    if not pipeline:
        errors.append("At least one [[pipeline]] step must exist")
        return errors
    
    # Check pipeline step validation
    step_names = set()
    all_outputs = set()
    
    for i, step in enumerate(pipeline):
        # Required fields
        for field in ['name', 'cmd', 'inputs', 'outputs']:
            if field not in step:
                errors.append(f"Pipeline step {i}: missing required field '{field}'")
        
        if 'name' in step:
            name = step['name']
            
            # Check name uniqueness (case-insensitive)
            name_lower = name.lower()
            if name_lower in step_names:
                errors.append(f"Duplicate step name: {name}")
            step_names.add(name_lower)
            
            # Check name format
            import re
            if not re.match(r'^[a-zA-Z0-9_\-]+$', name) or len(name) > 32:
                errors.append(f"Invalid step name '{name}': must be 1-32 chars, regex ^[a-zA-Z0-9_\\-]+$")
        
        # Check output uniqueness
        if 'outputs' in step:
            for output in step['outputs']:
                if output in all_outputs:
                    errors.append(f"Duplicate output declaration: {output}")
                all_outputs.add(output)
    
    return errors

def get_steps_to_build(pipeline_steps: List[dict], force: bool) -> List[dict]:
    """Get all steps that need building (CSF §6.3 - staleness check)"""
    steps_to_build = []
    
    for step in pipeline_steps:
        if force or is_step_stale(step):
            steps_to_build.append(step)
    
    return steps_to_build

def get_steps_to_build_for_target(pipeline_steps: List[dict], target_step: str, force: bool) -> List[dict]:
    """Get steps to build for a specific target step plus stale predecessors"""
    
    # Find target step
    target_index = None
    for i, step in enumerate(pipeline_steps):
        if step['name'] == target_step:
            target_index = i
            break
    
    if target_index is None:
        return []
    
    # Build all predecessors that are stale, plus the target
    steps_to_build = []
    
    for i in range(target_index + 1):
        step = pipeline_steps[i]
        if force or is_step_stale(step) or i == target_index:
            steps_to_build.append(step)
    
    return steps_to_build

def is_step_stale(step: dict) -> bool:
    """Check if step outputs are stale compared to inputs (CSF §6.3)"""
    
    # Get input files
    input_files = []
    for pattern in step['inputs']:
        matches = glob.glob(pattern)
        if not matches:
            # Input pattern doesn't match any files - step needs to run
            return True
        input_files.extend(matches)
    
    # Get output files
    output_files = []
    for pattern in step['outputs']:
        matches = glob.glob(pattern)
        output_files.extend(matches)
    
    # If no outputs exist, step is stale
    if not output_files:
        return True
    
    # Check if any input is newer than any output
    input_mtimes = [os.path.getmtime(f) for f in input_files if os.path.exists(f)]
    output_mtimes = [os.path.getmtime(f) for f in output_files if os.path.exists(f)]
    
    if not input_mtimes or not output_mtimes:
        return True
    
    # Step is stale if any input's mtime > any output's mtime
    max_input_mtime = max(input_mtimes)
    min_output_mtime = min(output_mtimes)
    
    return max_input_mtime > min_output_mtime

def execute_step(step: dict, config: CSFConfig, output_json: bool) -> int:
    """Execute a single pipeline step"""
    
    step_name = step['name']
    command = step['cmd']
    
    # Prepare environment
    env = os.environ.copy()
    if 'env' in step:
        env.update(step['env'])
        
    # Add provenance output path to environment
    provenance_file = config.outputs_dir / f"{step_name}_provenance.json"
    env['CS_PROVENANCE_OUTPUT'] = str(provenance_file)
    
    # Add provenance file to step outputs to ensure it's tracked
    if 'outputs' not in step:
        step['outputs'] = []
    step['outputs'].append(str(provenance_file))
    
    # Change to project root
    original_cwd = os.getcwd()
    if config.project_root:
        os.chdir(config.project_root)
    
    config_json_path = None
    try:
        # Validate inputs exist
        for pattern in step['inputs']:
            matches = glob.glob(pattern)
            if not matches:
                error(f"Input pattern '{pattern}' matches no files", output_json, exit_code=69)
                return 69
        
        # Execute command
        info(f"Executing: {command}", output_json)
        start_time = time.time()
        
        # Check if the command is 'cstex-compile'
        if command == "cstex-compile":
            manifest = config.load_manifest()
            if not manifest:
                error("Could not load manifest from flake.nix", output_json, exit_code=1)
                return 1
            
            csf_dir = config.project_root / ".csf"
            csf_dir.mkdir(exist_ok=True)
            config_json_path = csf_dir / "manifest.json"
            import json
            with open(config_json_path, 'w') as f:
                json.dump(manifest, f)

            # The main input file for cstex-compile is the first input of the step
            main_input = step['inputs'][0]
            
            # Construct the command to execute the cstex-compile command from the environment
            executable_command = ["cstex-compile", "--config", str(config_json_path), main_input]
            
            result = subprocess.run(
                " ".join(executable_command),
                shell=True,
                env=env,
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                command,
                shell=True,
                env=env,
                capture_output=True,
                text=True
            )
        
        duration = time.time() - start_time
        
        # Log output
        if result.stdout:
            info(f"stdout: {result.stdout.strip()}", output_json)
        if result.stderr:
            warning(f"stderr: {result.stderr.strip()}", output_json)
        
        info(f"Step completed in {duration:.2f}s", output_json)
        
        # Validate outputs were created
        missing_outputs = []
        for pattern in step['outputs']:
            matches = glob.glob(pattern)
            if not matches:
                # It's okay if the provenance file wasn't created; not all steps have fine-grained provenance.
                if pattern == str(provenance_file):
                    continue
                missing_outputs.append(pattern)
        
        if missing_outputs:
            error(f"Step '{step_name}' did not create expected outputs: {missing_outputs}",
                  output_json, exit_code=66)
            return 66
        
        return result.returncode
        
    finally:
        # Clean up temporary manifest file
        if config_json_path and os.path.exists(config_json_path):
            os.remove(config_json_path)
        # Restore working directory
        os.chdir(original_cwd)
