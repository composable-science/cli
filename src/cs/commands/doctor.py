"""Doctor command - Diagnose environment & config (CSF §3.2)"""

import click
import subprocess
import sys
import glob
from pathlib import Path
from cs.utils.output import success, error, info, warning, table_data
from cs.config import CSFConfig
from cs.identity import IdentityManager

def ensure_nix_shell():
    # Nix sets IN_NIX_SHELL=1 in the environment
    import os
    if not os.environ.get("IN_NIX_SHELL"):
        error(
            "You must run this command inside the Nix shell for full reproducibility.\n"
            "Use 'nix develop' or 'nix-shell' in your project root, or run via 'nix run'.\n\n"
            "This ensures all dependencies (Python, packages, binaries) are provided as specified in [build.env] or flake.nix.",
            json_output=False,
            exit_code=1
        )

@click.command()
@click.pass_context
def doctor_command(ctx):
    """Diagnose environment & config (CSF §3.2)"""
    
    ensure_nix_shell()
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    
    info("🔬 CSF Environment Diagnostics", output_json)
    
    # Check results
    checks = []
    warnings_found = []
    issues_found = []
    
    # 1. Check Python version (always first)
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_ok = sys.version_info >= (3, 8)
    python_checks = [[
        "Python Version", 
        python_version, 
        "✅ OK" if python_ok else "❌ FAIL (need >= 3.8)"
    ]]
    if not python_ok:
        issues_found.append("Python version too old. Install Python 3.8 or newer.")

    # 2. Check for manifest
    has_manifest = config.has_manifest()
    manifest_checks = [[
        "CSF Manifest",
        str(config.manifest_path) if config.manifest_path else "Not found",
        "✅ Found" if has_manifest else "❌ Missing (run 'cs init')"
    ]]
    if not has_manifest:
        issues_found.append("No flake.nix found. Run 'cs init <template>' to create a project.")
        checks = python_checks + manifest_checks
        return display_results(checks, warnings_found, issues_found, output_json)

    # 3. Check manifest validity and pipeline issues
    manifest = config.load_manifest()
    manifest_valid = manifest is not None
    manifest_checks.append([
        "Manifest Valid",
        "flake.nix",
        "✅ Valid" if manifest_valid else "❌ Invalid TOML"
    ])
    if not manifest_valid:
        issues_found.append("flake.nix contains invalid syntax.")
        checks = python_checks + manifest_checks
        return display_results(checks, warnings_found, issues_found, output_json)

    # 4. Check pipeline and identify missing inputs
    pipeline_steps = manifest.get('pipeline', [])
    pipeline_summary = []
    if pipeline_steps:
        pipeline_summary.append([
            "Pipeline Steps",
            f"{len(pipeline_steps)} steps: " + ", ".join([step.get('name', '?') for step in pipeline_steps]),
            "✅ Present"
        ])
        # Check each step for missing inputs
        missing_inputs = []
        for step in pipeline_steps:
            step_name = step.get('name', 'unknown')
            inputs = step.get('inputs', [])
            for input_pattern in inputs:
                matches = glob.glob(input_pattern)
                if not matches:
                    missing_inputs.append((step_name, input_pattern))
        if missing_inputs:
            missing_count = len(missing_inputs)
            pipeline_summary.append([
                "Input Files",
                f"{missing_count} missing",
                "⚠️ Issues found"
            ])
            for step_name, pattern in missing_inputs:
                warnings_found.append(f"Step '{step_name}' expects input '{pattern}' but no matching files found.")
                if pattern.endswith('.csv'):
                    warnings_found.append(f"  → Consider running the data generation step first, or check if the path is correct.")
                elif pattern.startswith('scripts/'):
                    warnings_found.append(f"  → Create the script file: {pattern}")
                else:
                    warnings_found.append(f"  → Check if '{pattern}' exists or run previous pipeline steps.")
        else:
            pipeline_summary.append([
                "Input Files",
                "All inputs available",
                "✅ OK"
            ])
    else:
        pipeline_summary.append([
            "Pipeline Steps",
            "No pipeline defined",
            "⚠️ Empty"
        ])
        warnings_found.append("No pipeline steps defined in flake.nix")
        if manifest_valid:
            has_package = 'package' in manifest
            has_pipeline = 'pipeline' in manifest and len(manifest['pipeline']) > 0
            pipeline_summary.append([
                "Package Section",
                "[package]",
                "✅ Present" if has_package else "❌ Missing"
            ])
            pipeline_summary.append([
                "Pipeline Steps",
                f"{len(manifest.get('pipeline', []))} steps",
                "✅ Present" if has_pipeline else "❌ No steps defined"
            ])

    # 5. Check DID identity
    identity_manager = IdentityManager(config)
    has_identity = identity_manager.has_identity()
    identity_checks = [[
        "DID Identity",
        identity_manager.get_did() if has_identity else "Not created",
        "✅ Available" if has_identity else "⚠️  Missing (run 'cs id create')"
    ]]

    # 6. Check Git repository and remote/branch/status
    git_checks = []
    git_available = check_git_available()
    git_checks.append([
        "Git",
        "git command",
        "✅ Available" if git_available else "❌ Not found"
    ])
    if config.project_root:
        git_repo = check_git_repository(config.project_root)
        git_checks.append([
            "Git Repository",
            str(config.project_root),
            "✅ Git repo" if git_repo else "⚠️  Not a git repository"
        ])
        if git_repo:
            # Get remote URL
            try:
                remote_url = subprocess.check_output([
                    'git', 'remote', 'get-url', 'origin'
                ], cwd=config.project_root).decode().strip()
            except Exception:
                remote_url = "None"
            git_checks.append([
                "Git Remote",
                remote_url,
                "✅ Set" if remote_url != "None" else "⚠️  Not set"
            ])
            # Get branch
            try:
                branch = subprocess.check_output([
                    'git', 'rev-parse', '--abbrev-ref', 'HEAD'
                ], cwd=config.project_root).decode().strip()
            except Exception:
                branch = "Unknown"
            git_checks.append([
                "Git Branch",
                branch,
                "✅ Current"
            ])
            # Get status (ahead/behind/clean/dirty)
            try:
                status_out = subprocess.check_output([
                    'git', 'status', '-sb'
                ], cwd=config.project_root).decode().strip()
                if 'ahead' in status_out:
                    status = 'ahead'
                elif 'behind' in status_out:
                    status = 'behind'
                elif 'diverged' in status_out:
                    status = 'diverged'
                elif '[ahead' in status_out or '[behind' in status_out:
                    status = 'out of sync'
                elif '*' in status_out:
                    status = 'dirty'
                else:
                    status = 'up to date'
            except Exception:
                status = "Unknown"
            git_checks.append([
                "Git Status",
                status,
                "✅" if status == 'up to date' else "⚠️  " + status
            ])

    # 7. Check Nix
    nix_checks = []
    nix_available = check_nix_available()
    nix_checks.append([
        "Nix",
        "nix command",
        "✅ Available" if nix_available else "⚠️  Not found (recommended)"
    ])
    # Nix env summary if present
    if manifest.get('build', {}).get('env'):
        env = manifest['build']['env']
        if env.get('kind') == 'nix':
            pkgs = env.get('packages', [])
            nix_checks.append([
                "Nix Environment",
                f"kind: nix, {len(pkgs)} packages",
                "✅ Present"
            ])

    # 8. Check outputs directory
    outputs_checks = []
    if config.outputs_dir:
        outputs_exists = config.outputs_dir.exists()
        outputs_checks.append([
            "Outputs Directory",
            str(config.outputs_dir),
            "✅ Exists" if outputs_exists else "⚠️  Will be created"
        ])

    # 9. Check Python dependencies (grouped, renamed)
    deps_status = check_python_dependencies()
    python_dep_checks = []
    for dep_name, dep_status in deps_status.items():
        python_dep_checks.append([
            f"--import {dep_name}",
            dep_status.get('version', 'Unknown'),
            "✅ Available" if dep_status.get('available') else "❌ Missing"
        ])

    # 10. Attestation summary
    attestation_checks = []
    if 'attestation' in manifest:
        att = manifest['attestation']
        included = att.get('include', [])
        excluded = att.get('exclude', [])
        attestation_checks.append([
            "Attestation",
            f"include: {', '.join(included)}; exclude: {', '.join(excluded)}",
            "✅ Present"
        ])

    # 11. Dashboard open summary
    dashboard_checks = []
    if manifest.get('build', {}).get('open_dashboard'):
        dashboard_checks.append([
            "Dashboard",
            "Auto-open enabled",
            "✅"
        ])

    # Compose all checks in desired order
    checks = (
        python_checks +
        python_dep_checks +
        manifest_checks +
        pipeline_summary +
        attestation_checks +
        dashboard_checks +
        identity_checks +
        git_checks +
        nix_checks +
        outputs_checks
    )

    # Display results
    if output_json:
        table_data(checks, ["Component", "Value", "Status"], output_json)
    else:
        table_data(checks, ["Component", "Value", "Status"], output_json)
    
    # Summary
    failed_checks = [check for check in checks if "❌" in check[2]]
    warning_checks = [check for check in checks if "⚠️" in check[2]]
    
    if failed_checks:
        error(f"❌ {len(failed_checks)} critical issues found", output_json, exit_code=0)
        for check in failed_checks:
            error(f"  - {check[0]}: {check[2]}", output_json, exit_code=0)
    
    if warning_checks:
        warning(f"⚠️  {len(warning_checks)} warnings", output_json)
        for check in warning_checks:
            warning(f"  - {check[0]}: {check[2]}", output_json)
    
    if not failed_checks and not warning_checks:
        success("🎉 All checks passed! Your CSF environment is ready.", output_json)

def display_results(checks, warnings_found, issues_found, output_json):
    table_data(checks, ["Component", "Value", "Status"], output_json)
    if issues_found:
        error(f"❌ {len(issues_found)} critical issues found", output_json, exit_code=0)
        for msg in issues_found:
            error(f"  - {msg}", output_json, exit_code=0)
    if warnings_found:
        warning(f"⚠️  {len(warnings_found)} warnings", output_json)
        for msg in warnings_found:
            warning(f"  - {msg}", output_json)
    if not issues_found and not warnings_found:
        success("🎉 All checks passed! Your CSF environment is ready.", output_json)

def check_git_available() -> bool:
    """Check if git command is available"""
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_git_repository(project_root: Path) -> bool:
    """Check if directory is a git repository"""
    try:
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'], 
            cwd=project_root, 
            capture_output=True, 
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_nix_available() -> bool:
    """Check if nix command is available"""
    try:
        subprocess.run(['nix', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_python_dependencies() -> dict:
    """Check Python dependencies"""
    
    dependencies = {
        'click': 'click',
        'toml': 'toml', 
        'cryptography': 'cryptography',
        'requests': 'requests',
        'rich': 'rich'
    }
    
    status = {}
    
    for dep_name, import_name in dependencies.items():
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'Unknown')
            status[dep_name] = {
                'available': True,
                'version': version
            }
        except ImportError:
            status[dep_name] = {
                'available': False,
                'version': 'Not installed'
            }
    
    return status
