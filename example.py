#!/usr/bin/env python3
"""
Example usage of the CSF CLI

This script demonstrates the core CSF workflow:
1. Create a new project
2. Build the pipeline  
3. Create attestations
4. Generate dashboard
"""

import subprocess
import tempfile
import os
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and show output"""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"stderr: {result.stderr}")
    
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        return False
    
    return True

def main():
    """Run CSF example workflow"""
    
    # Use a temporary directory for the example
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "example-project"
        project_dir.mkdir()
        
        print(f"🔬 CSF Example Workflow")
        print(f"📁 Working in: {project_dir}")
        print()
        
        # Change to project directory
        os.chdir(project_dir)
        
        # Get path to cs CLI
        cs_path = Path(__file__).parent / "src" / "cs" / "main.py"
        cs_cmd = f"python3 {cs_path}"
        
        # 1. Check doctor
        print("1️⃣  Running diagnostics...")
        if not run_command(f"{cs_cmd} doctor"):
            print("❌ Doctor check failed")
            return
        print()
        
        # 2. Create identity
        print("2️⃣  Creating DID identity...")
        if not run_command(f"{cs_cmd} id create"):
            print("❌ Identity creation failed")
            return
        print()
        
        # 3. Initialize project
        print("3️⃣  Initializing basic-lab project...")
        if not run_command(f"{cs_cmd} init basic-lab"):
            print("❌ Project initialization failed")
            return
        print()
        
        # 4. Check manifest
        print("4️⃣  Generated manifest:")
        if (project_dir / "composable.toml").exists():
            with open("composable.toml") as f:
                print(f.read())
        print()
        
        # 5. Build pipeline  
        print("5️⃣  Building pipeline...")
        if not run_command(f"{cs_cmd} build"):
            print("❌ Build failed")
            return
        print()
        
        # 6. Create attestations
        print("6️⃣  Creating attestations...")
        if not run_command(f"{cs_cmd} attest data"):
            print("❌ Attestation failed")
        
        if not run_command(f"{cs_cmd} attest analysis"):
            print("❌ Attestation failed") 
        print()
        
        # 7. Generate diagram
        print("7️⃣  Generating Mermaid diagram...")
        if not run_command(f"{cs_cmd} diagram"):
            print("❌ Diagram generation failed")
        else:
            if (project_dir / "pipeline.mmd").exists():
                print("Generated pipeline.mmd:")
                with open("pipeline.mmd") as f:
                    print(f.read())
        print()
        
        # 8. Generate dashboard
        print("8️⃣  Generating dashboard...")
        if not run_command(f"{cs_cmd} dashboard --no-open"):
            print("❌ Dashboard generation failed")
        else:
            dashboard_file = project_dir / "dashboard" / "index.html"
            if dashboard_file.exists():
                print(f"✅ Dashboard generated: {dashboard_file}")
        print()
        
        print("🎉 CSF example workflow completed!")
        print(f"📁 Project files created in: {project_dir}")
        
        # List created files
        print("\n📄 Generated files:")
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(project_dir)
                print(f"  {rel_path}")

if __name__ == "__main__":
    main()
