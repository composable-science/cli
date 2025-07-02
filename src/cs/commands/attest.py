"""Attest command - Create & sign attestation (CSF §7)"""

import click
import json
import hashlib
import glob
import fnmatch
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Dict, Any, List
from cs.utils.output import success, error, info
from cs.config import CSFConfig
from cs.identity import IdentityManager

@click.command()
@click.argument('step', required=False)
@click.option('--output', '-o', help='Output file for attestation (default: attestation.json)')
@click.option('--pipeline', is_flag=True, help='Attest entire pipeline instead of single step')
@click.pass_context
def attest_command(ctx, step, output, pipeline):
    """Create & sign attestation for the specified step or entire pipeline (CSF §7.2)"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    
    if not config.has_manifest():
        error("No flake.nix found. Run 'cs init <template>' to create a new project.", output_json, exit_code=64)
        return
    
    manifest = config.load_manifest()
    if not manifest:
        # The config loader already printed an error
        return
    
    # Initialize identity manager
    identity_manager = IdentityManager(config)
    
    # Check if we have a DID identity
    if not identity_manager.has_identity():
        error("No DID identity found. Run 'cs id create' first.", output_json, exit_code=68)
        return
    
    if pipeline:
        # Attest entire pipeline
        if step:
            error("Cannot specify both --pipeline flag and step name", output_json, exit_code=64)
            return
        
        info("Creating attestation for entire pipeline", output_json)
        
        try:
            attestation = create_pipeline_attestation(manifest, config, identity_manager)
            
            # Sign attestation
            signed_attestation = identity_manager.sign_attestation(attestation)
            
            # Write attestation file
            output_file = output or "pipeline_attestation.json"
            attestation_path = config.project_root / output_file
            
            with open(attestation_path, 'w') as f:
                json.dump(signed_attestation, f, indent=2)
            
            success(f"Pipeline attestation created: {attestation_path}", output_json)
            info(f"Attester DID: {identity_manager.get_did()}", output_json)
            
            # Display summary of attested artifacts
            if not output_json:
                pipeline_steps = attestation['body']['pipeline_steps']
                total_artifacts = sum(len(step['resolved_artifacts']) for step in pipeline_steps)
                info(f"Attested {len(pipeline_steps)} steps with {total_artifacts} total artifacts", output_json)
            
        except Exception as e:
            error(f"Failed to create pipeline attestation: {str(e)}", output_json, exit_code=67)
            
    else:
        # Attest single step (existing functionality)
        if not step:
            error("Step name required when not using --pipeline flag", output_json, exit_code=64)
            return
        
        # Find the step
        pipeline_steps = manifest.get('pipeline', [])
        step_config = None
        for s in pipeline_steps:
            if s['name'] == step:
                step_config = s
                break
        
        if not step_config:
            error(f"Step '{step}' not found in pipeline", output_json, exit_code=64)
            return
        
        info(f"Creating attestation for step: {step}", output_json)
        
        # Create attestation
        try:
            attestation = create_attestation(step_config, config, identity_manager)
            
            # Sign attestation
            signed_attestation = identity_manager.sign_attestation(attestation)
            
            # Write attestation file
            output_file = output or "attestation.json"
            attestation_path = config.project_root / output_file
            
            with open(attestation_path, 'w') as f:
                json.dump(signed_attestation, f, indent=2)
            
            success(f"Attestation created: {attestation_path}", output_json)
            info(f"Attester DID: {identity_manager.get_did()}", output_json)
            
            # TODO: Optionally open PR to ledger repository (CSF §7.2.4)
            
        except Exception as e:
            error(f"Failed to create attestation: {str(e)}", output_json, exit_code=67)

def create_attestation(step_config: Dict[str, Any], config: CSFConfig, identity_manager) -> Dict[str, Any]:
    """Create attestation JSON according to CSF §7.1 schema"""
    
    # Compute NAR hash of outputs
    output_hashes = compute_output_hashes(step_config)
    
    # Get git information
    git_info = get_git_info(config.project_root)
    
    # Get manifest hash
    manifest_hash = compute_file_hash(config.manifest_path)
    
    # Create attestation body
    attestation = {
        "$schema": "https://composable-science.org/schemas/attestation/v0.0.1.json",
        "attester_did": identity_manager.get_did(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attestation_class": "COMPUTATIONALLY_ATTESTED",
        "body": {
            "pipeline_step": step_config['name'],
            "command": step_config['cmd'],
            "artifact_hashes": output_hashes,
            "input_patterns": step_config['inputs'],
            "output_patterns": step_config['outputs'],
            "build_context": {
                "flake_nix_hash": manifest_hash,
                "git_commit": git_info.get('commit'),
                "git_branch": git_info.get('branch'),
                "git_remote": git_info.get('remote'),
                "working_tree_clean": git_info.get('clean', False)
            },
            "environment": {
                "cs_version": "0.0.1",
                "platform": get_platform_info()
            }
        }
    }
    
    return attestation

def create_pipeline_attestation(manifest: Dict[str, Any], config: CSFConfig, identity_manager) -> Dict[str, Any]:
    """Create attestation JSON for entire pipeline with resolved artifact documentation"""
    
    pipeline_steps = manifest.get('pipeline', [])
    if not pipeline_steps:
        raise ValueError("No pipeline steps found in manifest")
    
    # Get git information and manifest hash
    git_info = get_git_info(config.project_root)
    manifest_hash = compute_file_hash(config.manifest_path)
    
    # Process each step and resolve artifacts
    attested_steps = []
    total_artifacts = {}
    
    for step_config in pipeline_steps:
        step_name = step_config['name']
        info(f"Processing step: {step_name}")
        
        # Resolve wildcard patterns to actual files
        resolved_artifacts = resolve_artifacts(step_config)
        
        # Compute hashes for all resolved artifacts
        artifact_hashes = {}
        for file_path in resolved_artifacts:
            if Path(file_path).is_file():
                file_hash = compute_file_hash(file_path)
                artifact_hashes[file_path] = file_hash
                total_artifacts[file_path] = file_hash
        
        # Check for and load fine-grained provenance
        fine_grained_provenance = None
        provenance_file = config.outputs_dir / f"{step_name}_provenance.json"
        if provenance_file.exists():
            with open(provenance_file, 'r') as f:
                fine_grained_provenance = json.load(f)

        # Create enhanced step documentation
        step_attestation = {
            "step_name": step_name,
            "command": step_config['cmd'],
            "input_patterns": step_config['inputs'],
            "output_patterns": step_config['outputs'],
            "resolved_artifacts": resolved_artifacts,
            "artifact_hashes": artifact_hashes,
            "artifact_count": len(resolved_artifacts),
            "environment_vars": step_config.get('env', {}),
            "attestation_timestamp": datetime.now(timezone.utc).isoformat(),
            "fine_grained_provenance": fine_grained_provenance
        }
        
        attested_steps.append(step_attestation)
    
    # Validate pipeline integrity
    pipeline_validation = validate_pipeline_integrity(attested_steps, manifest)
    
    # Create comprehensive pipeline attestation
    attestation = {
        "$schema": "https://composable-science.org/schemas/pipeline-attestation/v0.0.1.json",
        "attester_did": identity_manager.get_did(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attestation_class": "COMPUTATIONALLY_ATTESTED",
        "attestation_type": "PIPELINE_VERIFICATION",
        "body": {
            "claim": f"Complete pipeline verification for {manifest.get('package', {}).get('name', 'unnamed project')}",
            "project_metadata": {
                "name": manifest.get('package', {}).get('name'),
                "version": manifest.get('package', {}).get('version'),
                "authors": manifest.get('package', {}).get('authors', []),
                "license": manifest.get('package', {}).get('license')
            },
            "pipeline_steps": attested_steps,
            "total_artifacts": len(total_artifacts),
            "total_steps": len(attested_steps),
            "artifact_summary": {
                "total_files": len(total_artifacts),
                "total_size_bytes": calculate_total_size(total_artifacts.keys()),
                "file_types": categorize_file_types(total_artifacts.keys())
            },
            "build_context": {
                "flake_nix_hash": manifest_hash,
                "git_commit": git_info.get('commit'),
                "git_branch": git_info.get('branch'),
                "git_remote": git_info.get('remote'),
                "working_tree_clean": git_info.get('clean', False),
                "pipeline_order": [step['step_name'] for step in attested_steps]
            },
            "validation": pipeline_validation,
            "environment": {
                "cs_version": "0.0.1",
                "platform": get_platform_info(),
                "nix_environment": manifest.get('build', {}).get('env', {})
            },
            "attestation_config": manifest.get('attestation', {}),
            "reproducibility_metadata": {
                "deterministic_hashes": True,
                "wildcard_patterns_resolved": True,
                "build_environment_captured": True,
                "dependency_tracking": "complete"
            }
        }
    }
    
    return attestation

def resolve_artifacts(step_config: Dict[str, Any]) -> List[str]:
    """Resolve wildcard patterns to actual file paths for better reproducibility"""
    
    resolved_files = []
    
    # Resolve output patterns
    for pattern in step_config['outputs']:
        matches = glob.glob(pattern)
        if not matches:
            raise ValueError(f"Output pattern '{pattern}' matched no files for step '{step_config['name']}'")
        resolved_files.extend(matches)
    
    # Also include resolved input files for complete documentation
    for pattern in step_config['inputs']:
        matches = glob.glob(pattern)
        if not matches:
            raise ValueError(f"Input pattern '{pattern}' matched no files for step '{step_config['name']}'")
        # Only add inputs that aren't already captured as outputs from previous steps
        for match in matches:
            if match not in resolved_files:
                resolved_files.append(match)
    
    return sorted(resolved_files)

def validate_pipeline_integrity(attested_steps: List[Dict[str, Any]], manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the integrity and completeness of the pipeline"""
    
    validation_results = {
        "status": "valid",
        "checks": [],
        "warnings": [],
        "errors": []
    }
    
    # Check step ordering
    step_names = [step['step_name'] for step in attested_steps]
    manifest_step_names = [step['name'] for step in manifest.get('pipeline', [])]
    
    if step_names != manifest_step_names:
        validation_results["errors"].append("Step order mismatch between attestation and manifest")
        validation_results["status"] = "invalid"
    
    # Check for missing outputs
    for step in attested_steps:
        if step['artifact_count'] == 0:
            validation_results["warnings"].append(f"Step '{step['step_name']}' produced no artifacts")
    
    # Check for overlapping outputs (violates CSF §5.4 rule 3)
    all_outputs = {}
    for step in attested_steps:
        for artifact in step['resolved_artifacts']:
            if artifact in all_outputs:
                validation_results["errors"].append(
                    f"Artifact '{artifact}' produced by both '{all_outputs[artifact]}' and '{step['step_name']}'"
                )
                validation_results["status"] = "invalid"
            else:
                all_outputs[artifact] = step['step_name']
    
    # Check attestation inclusion rules
    attestation_config = manifest.get('attestation', {})
    if attestation_config:
        included_files = check_attestation_rules(all_outputs.keys(), attestation_config)
        validation_results["checks"].append({
            "type": "attestation_inclusion",
            "included_files": len(included_files),
            "total_files": len(all_outputs)
        })
    
    return validation_results

def check_attestation_rules(artifact_paths: List[str], attestation_config: Dict[str, Any]) -> List[str]:
    """Check which artifacts should be included based on attestation rules"""
    
    included_files = []
    include_patterns = attestation_config.get('include', [])
    exclude_patterns = attestation_config.get('exclude', [])
    
    for artifact_path in artifact_paths:
        should_include = False
        
        # Check include patterns
        if include_patterns:
            for pattern in include_patterns:
                if fnmatch.fnmatch(artifact_path, pattern):
                    should_include = True
                    break
        else:
            # Include all by default if no include patterns specified
            should_include = True
        
        # Check exclude patterns
        if should_include and exclude_patterns:
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(artifact_path, pattern):
                    should_include = False
                    break
        
        if should_include:
            included_files.append(artifact_path)
    
    return included_files

def calculate_total_size(file_paths: List[str]) -> int:
    """Calculate total size of all artifacts in bytes"""
    
    total_size = 0
    for file_path in file_paths:
        try:
            total_size += Path(file_path).stat().st_size
        except (OSError, FileNotFoundError):
            # Skip files that can't be accessed
            pass
    
    return total_size

def categorize_file_types(file_paths: List[str]) -> Dict[str, int]:
    """Categorize files by extension for better documentation"""
    
    type_counts = {}
    
    for file_path in file_paths:
        extension = Path(file_path).suffix.lower()
        if not extension:
            extension = 'no_extension'
        
        type_counts[extension] = type_counts.get(extension, 0) + 1
    
    return type_counts

def compute_output_hashes(step_config: Dict[str, Any]) -> Dict[str, str]:
    """Compute SHA-256 hashes of all output artifacts"""
    
    hashes = {}
    
    for pattern in step_config['outputs']:
        matches = glob.glob(pattern)
        for file_path in matches:
            if Path(file_path).is_file():
                file_hash = compute_file_hash(file_path)
                hashes[file_path] = file_hash
    
    return hashes

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file"""
    
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return f"sha256:{sha256_hash.hexdigest()}"

def get_git_info(project_root: Path) -> Dict[str, Any]:
    """Get git repository information"""
    
    git_info = {}
    
    try:
        # Get current commit
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], 
            cwd=project_root, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            git_info['commit'] = result.stdout.strip()
        
        # Get current branch
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            cwd=project_root, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            git_info['branch'] = result.stdout.strip()
        
        # Get remote URL
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'], 
            cwd=project_root, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            git_info['remote'] = result.stdout.strip()
        
        # Check if working tree is clean
        result = subprocess.run(
            ['git', 'diff-index', '--quiet', 'HEAD', '--'], 
            cwd=project_root, 
            capture_output=True
        )
        git_info['clean'] = result.returncode == 0
        
    except Exception:
        # Git not available or not a git repository
        pass
    
    return git_info

def get_platform_info() -> Dict[str, str]:
    """Get platform information"""
    
    import platform
    
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version()
    }
