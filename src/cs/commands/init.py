"""Init command - Create new CSF project from template (CSF §3.2)"""

import click
from pathlib import Path
import shutil
import toml
import subprocess
from cs.utils.output import success, error, info
from cs.config import CSFConfig

TEMPLATES = {
    "basic-lab": {
        "description": "Minimal 2‑step pipeline, README quick‑start",
        "audience": "Solo researchers"
    },
    "paper-latex": {
        "description": "Figures + PDF build",
        "audience": "Traditional publishing"
    },
    "dataset-pipeline": {
        "description": "Download, clean, analyse dataset",
        "audience": "Data wrangling"
    },
    "software-package": {
        "description": "Build binary + docs, attest tarball",
        "audience": "CLI/library release"
    }
}

@click.command()
@click.argument('template', type=click.Choice(list(TEMPLATES.keys())))
@click.option('--name', help='Project name (defaults to current directory)')
@click.pass_context
def init_command(ctx, template, name):
    """Create a new project from a starter template (CSF §11)"""
    
    output_json = ctx.obj.get('output_json', False)
    current_dir = Path.cwd()
    
    # Check if already a CSF project
    if (current_dir / "flake.nix").exists():
        error("Current directory already contains a flake.nix", output_json, exit_code=1)
        return
    
    project_name = name or current_dir.name
    
    info(f"Creating {template} project: {project_name}", output_json)
    
    # Create project structure (CSF §4)
    create_project_structure(current_dir, template)
    
    # Create flake.nix with embedded pipeline configuration
    create_flake_nix(current_dir, template, project_name)

    # Initialize git repository
    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=current_dir, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], cwd=current_dir, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "--no-gpg-sign", "-m", "Initial commit"], cwd=current_dir, check=True, capture_output=True, text=True)
        info("Initialized and committed git repository.", output_json)
    except (subprocess.CalledProcessError, FileNotFoundError):
        info("Could not initialize git repository (is git installed?).", output_json)
    
    success(f"Created {template} project in {current_dir}", output_json)
    info("Next steps:", output_json)
    info("  1. cs build         # Build the pipeline", output_json)
    info("  2. cs attest <step> # Create attestation", output_json)
    info("  3. cs dashboard     # View results", output_json)

# This function is now removed as the logic is integrated into create_flake_nix
# def create_manifest_for_template(template: str, project_name: str) -> dict:
#    ...

def create_project_structure(project_dir: Path, template: str):
    """Create the project directory structure (CSF §4)"""
    
    # Create standard directories
    (project_dir / "outputs").mkdir(exist_ok=True)
    (project_dir / "scripts").mkdir(exist_ok=True)
    (project_dir / "docs").mkdir(exist_ok=True)
    
    # Create .gitignore
    gitignore_content = """# CSF build outputs
outputs/
.nix-*
result*

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# OS
.DS_Store
Thumbs.db
"""
    
    with open(project_dir / ".gitignore", 'w') as f:
        f.write(gitignore_content)
    
    # Template-specific files
    if template == "basic-lab":
        create_basic_lab_files(project_dir)
    elif template == "paper-latex":
        create_paper_latex_files(project_dir)
    elif template == "dataset-pipeline":
        create_dataset_pipeline_files(project_dir)
    elif template == "software-package":
        create_software_package_files(project_dir)

def create_basic_lab_files(project_dir: Path):
    """Create files for basic-lab template"""
    
    # Create a simple data generation script
    script_content = '''#!/usr/bin/env python3
"""Generate sample data for CSF basic lab template"""

print("Generating data for CSF pipeline...")
# Add your data generation logic here
'''
    
    with open(project_dir / "scripts" / "generate_data.py", 'w') as f:
        f.write(script_content)
    
    # Create README
    readme_content = '''# CSF Basic Lab Project

This is a basic CSF project demonstrating the pipeline workflow.

## Usage

```bash
# Build the entire pipeline
cs build

# Create attestation
cs attest data
cs attest analysis

# View dashboard
cs dashboard
```

## Pipeline Steps

1. **data**: Generate sample data
2. **analysis**: Analyze the data
'''
    
    with open(project_dir / "README.md", 'w') as f:
        f.write(readme_content)

def create_paper_latex_files(project_dir: Path):
    """Create files for paper-latex template"""
    
    # Create directories
    (project_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (project_dir / "figures").mkdir(exist_ok=True)
    
    # Create sample data generation script
    data_script_content = '''#!/usr/bin/env python3
"""Generate sample data for LaTeX paper"""

import pandas as pd
import numpy as np
from pathlib import Path

def main():
    # Create sample dataset
    np.random.seed(42)
    n_samples = 100
    
    # Generate sample research data
    data = {
        'experiment_id': range(1, n_samples + 1),
        'temperature': np.random.normal(25, 5, n_samples),
        'pressure': np.random.normal(1013, 50, n_samples),
        'measurement': np.random.normal(100, 15, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Save to raw data
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/raw/experiments.csv", index=False)
    
    print(f"Generated sample dataset with {len(df)} experiments")
    print("Saved to data/raw/experiments.csv")

if __name__ == "__main__":
    main()
'''
    
    with open(project_dir / "scripts" / "generate_sample_data.py", 'w') as f:
        f.write(data_script_content)
    
    # Create figure generation script
    script_content = '''#!/usr/bin/env python3
"""Generate figures for LaTeX paper"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

def main():
    # Ensure figures directory exists
    Path("figures").mkdir(exist_ok=True)
    
    # Load data
    data_files = list(Path("data/raw").glob("*.csv"))
    if not data_files:
        print("No CSV files found in data/raw/")
        return
    
    df = pd.read_csv(data_files[0])
    
    # Generate scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(df['temperature'], df['measurement'], alpha=0.6, s=30)
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Measurement Value')
    plt.title('Temperature vs Measurement')
    plt.grid(True, alpha=0.3)
    plt.savefig('figures/temperature_measurement.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Generate histogram
    plt.figure(figsize=(8, 6))
    plt.hist(df['measurement'], bins=20, alpha=0.7, edgecolor='black')
    plt.xlabel('Measurement Value')
    plt.ylabel('Frequency')
    plt.title('Distribution of Measurements')
    plt.grid(True, alpha=0.3)
    plt.savefig('figures/measurement_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Figures generated successfully!")
    print("  - figures/temperature_measurement.png")
    print("  - figures/measurement_distribution.png")

if __name__ == "__main__":
    main()
'''
    
    with open(project_dir / "scripts" / "make_figures.py", 'w') as f:
        f.write(script_content)

    # Create stats calculation script
    stats_script_content = '''#!/usr/bin/env python3
"""Calculate summary statistics"""

import pandas as pd
import json
from pathlib import Path

def main():
    # Ensure outputs directory exists
    Path("outputs").mkdir(exist_ok=True)
    
    # Load data
    df = pd.read_csv("data/raw/experiments.csv")
    
    # Calculate stats
    mean_temp = df['temperature'].mean()
    
    # Save to JSON
    with open("outputs/stats.json", 'w') as f:
        json.dump({"mean_temperature": mean_temp}, f, indent=2)
        
    print("Calculated summary statistics and saved to outputs/stats.json")

if __name__ == "__main__":
    main()
'''
    with open(project_dir / "scripts" / "calculate_stats.py", 'w') as f:
        f.write(stats_script_content)
    
    # Create minimal LaTeX paper
    latex_content = r'''\documentclass{article}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{../templates/composable}

\title{CSF Paper Template}
\author{Your Name}
\date{\today}

\begin{document}

\maketitle

\section{Introduction}

This is a sample paper created with the Composable Science Framework.
All computational steps are reproducible and verifiable.

The mean temperature was \csfvaluelink{mean_temp}{float,round2} C.

\section{Results}

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{figures/temperature_measurement.png}
\caption{Temperature vs Measurement Analysis}
\label{fig:temperature}
\end{figure}

Figure \ref{fig:temperature} shows the relationship between temperature and measurements from our reproducible computation.

\section{Conclusion}

This paper demonstrates CSF pipeline integration with LaTeX.

\end{document}
'''
    
    with open(project_dir / "paper.tex", 'w') as f:
        f.write(latex_content)

def create_dataset_pipeline_files(project_dir: Path):
    """Create files for dataset-pipeline template"""
    
    # Create directories
    (project_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (project_dir / "data" / "clean").mkdir(parents=True, exist_ok=True)
    (project_dir / "results").mkdir(exist_ok=True)
    (project_dir / "figures").mkdir(exist_ok=True)
    
    # Download script
    download_script = '''#!/usr/bin/env python3
"""Download sample dataset"""

import pandas as pd
import numpy as np
from pathlib import Path

def main():
    # Create synthetic dataset
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'feature_1': np.random.normal(0, 1, n_samples),
        'feature_2': np.random.normal(2, 1.5, n_samples),
        'target': np.random.choice([0, 1], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Save to raw data
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/raw/dataset.csv", index=False)
    
    print(f"Downloaded dataset with {len(df)} samples")

if __name__ == "__main__":
    main()
'''
    
    with open(project_dir / "scripts" / "download_data.py", 'w') as f:
        f.write(download_script)

def create_software_package_files(project_dir: Path):
    """Create files for software-package template"""
    
    # Create src directory
    (project_dir / "src").mkdir(exist_ok=True)
    
    # Create setup.py
    setup_content = '''from setuptools import setup, find_packages

setup(
    name="csf-package",
    version="0.0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
    author="Your Name",
    author_email="your.email@example.com",
    description="A CSF software package",
    python_requires=">=3.8",
)
'''
    
    with open(project_dir / "setup.py", 'w') as f:
        f.write(setup_content)

def create_flake_nix(project_dir: Path, template: str, project_name: str):
    """Create flake.nix with embedded csConfig for the specified template."""

    # Define pipeline structures for each template
    pipelines = {
        "basic-lab": """
          pipeline = [
            {
              name = "data";
              cmd = "echo 'Hello, CSF!' > data.txt";
              inputs = [ ];
              outputs = [ "data.txt" ];
            }
            {
              name = "analysis";
              cmd = "wc -w data.txt > analysis.txt";
              inputs = [ "data.txt" ];
              outputs = [ "analysis.txt" ];
            }
          ];
        """,
        "paper-latex": """
          pipeline = [
            {
              name = "data";
              cmd = "python3 scripts/generate_sample_data.py";
              inputs = [ "scripts/generate_sample_data.py" ];
              outputs = [ "data/raw/experiments.csv" ];
              buildInputs = [ pkgs.python311Packages.pandas ];
            }
            {
              name = "figures";
              cmd = "python3 scripts/make_figures.py";
              inputs = [ "data/raw/experiments.csv" "scripts/make_figures.py" ];
              outputs = [ "figures/temperature_measurement.png" "figures/measurement_distribution.png" ];
              buildInputs = [ pkgs.python311Packages.matplotlib pkgs.python311Packages.pandas ];
            }
            {
              name = "stats";
              cmd = "python3 scripts/calculate_stats.py";
              inputs = [ "data/raw/experiments.csv" "scripts/calculate_stats.py" ];
              outputs = [ "outputs/stats.json" ];
              buildInputs = [ pkgs.python311Packages.pandas ];
            }
            {
              name = "paper";
              cmd = "cstex-compile";
              inputs = [ "paper.tex" "figures/temperature_measurement.png" "figures/measurement_distribution.png" "outputs/stats.json" ];
              outputs = [ "paper.pdf" ];
              buildInputs = [ cstex.packages.${system}.cstex-compile ];
            }
          ];
          values = [
            {
              name = "mean_temp";
              file = "outputs/stats.json";
              query = ".mean_temperature";
            }
          ];
        """,
        "dataset-pipeline": """
          pipeline = [
            {
              name = "download";
              cmd = "python3 scripts/download_data.py";
              inputs = [ "scripts/download_data.py" ];
              outputs = [ "data/raw/dataset.csv" ];
              buildInputs = [ pkgs.python311Packages.pandas ];
            },
            {
              name = "clean";
              cmd = "python3 scripts/clean_data.py";
              inputs = [ "data/raw/dataset.csv" "scripts/clean_data.py" ];
              outputs = [ "data/clean/dataset.csv" ];
              buildInputs = [ pkgs.python311Packages.pandas ];
            },
            {
              name = "analyze";
              cmd = "python3 scripts/analyze.py";
              inputs = [ "data/clean/dataset.csv" "scripts/analyze.py" ];
              outputs = [ "results/summary.json" ];
              buildInputs = [ pkgs.python311Packages.pandas ];
            }
          ];
        """,
        "software-package": """
          pipeline = [
            {
              name = "build";
              cmd = "python3 setup.py bdist_wheel";
              inputs = [ "src/**/*.py" "setup.py" ];
              outputs = [ "dist/*.whl" ];
              buildInputs = [ pkgs.python311Packages.setuptools pkgs.python311Packages.wheel ];
            },
            {
              name = "test";
              cmd = "python3 -m pytest";
              inputs = [ "src/**/*.py" "tests/**/*.py" ];
              outputs = [ ]; # No outputs, just run tests
              buildInputs = [ pkgs.python311Packages.pytest ];
            }
          ];
        """
    }

    flake_template = f"""
{{
  description = "A Composable Science Project: {project_name}";

  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    cs.url = "github:composable-science/cli";
    cstex.url = "github:composable-science/cstex";
  }};

  outputs = {{ self, nixpkgs, flake-utils, cs, cstex }}:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {{ inherit system; }};

        cs-pipeline = {{
          package = {{
            name = "{project_name}";
            version = "0.1.0";
          }};
          {pipelines.get(template, "")}
        }};

        # Combine all buildInputs from the pipeline steps
        pipeline-dependencies = pkgs.lib.lists.unique (builtins.concatMap (step: step.buildInputs or []) cs-pipeline.pipeline);

      in
      {{
        # The CS tool reads this configuration directly
        csConfig = cs-pipeline;

        # The dev shell includes the 'cs' command and all pipeline dependencies
        devShells.default = pkgs.mkShell {{
          buildInputs = [
            cs.packages.${{system}}.cs
            cstex.packages.${{system}}.cstex-compile
          ] ++ pipeline-dependencies;

          shellHook = ''
            echo "🔬 CSF Project Environment Ready"
            echo "📋 Available commands: cs view, cs build, cs attest"
          '';
        }};
      }}
    );
}}
"""
    with open(project_dir / "flake.nix", 'w') as f:
        f.write(flake_template)

# This function is deprecated and should be removed or updated to use the new system.
# def create_test_project(...):
