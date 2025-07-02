# Composable Science Framework - Core Implementation

This is the core implementation of the Composable Science Framework (CSF), a tool for creating and managing reproducible computational research projects.

## 🚀 Quick Start

### Using Nix (Recommended)

```bash
# Enter development environment
nix develop

# Create a new project (try the paper-latex template!)
cs init paper-latex my-research
cd my-research

# Enter the project's Nix environment
nix develop

# View the status of your pipeline
cs view

# Build the entire pipeline
cs build

# Create attestation for reproducibility
cs attest --pipeline

# View interactive dashboard
cs dashboard
```

## 📋 Commands

The CSF CLI implements all commands specified in CSF §3.2:

| Command | Purpose | Example |
|---------|---------|---------|
| `cs init <template>` | Create new project from template | `cs init basic-lab` |
| `cs view` | Display a rich summary of the pipeline status | `cs view` |
| `cs build [<step>]` | Build pipeline or specific step | `cs build figures` |
| `cs diagram` | Generate Mermaid diagram | `cs diagram -o pipeline.mmd` |
| `cs dashboard` | Generate HTML dashboard | `cs dashboard` |
| `cs attest <step>` | Create signed attestation | `cs attest figures` |
| `cs id <subcmd>` | DID identity management | `cs id create` |
| `cs doctor` | Diagnose environment | `cs doctor` |

## 🏗️ Project Structure

CSF projects follow a standard layout:

```
my-project/
├── flake.nix          # Single source of truth for environment and pipeline
├── outputs/           # Build artifacts (git-ignored)
├── scripts/           # Helper scripts
├── data/raw/          # Raw data files
├── figures/           # Generated figures
├── docs/              # Documentation
└── .gitignore         # Git ignore rules
```

## ⚙️ Configuration (`flake.nix`)

The `flake.nix` file is the **single source of truth** for your project. It defines both the computational environment (dependencies) and the pipeline workflow. The `cs` tool reads its configuration from the `csConfig` attribute within the flake.

```nix
{
  description = "A Composable Science Project";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: {
    # The cs tool reads this attribute for all configuration.
    csConfig = {
      package = {
        name = "my-research";
        version = "0.1.0";
      };
      pipeline = [
        {
          name = "data";
          cmd = "python scripts/generate_data.py";
          inputs = ["scripts/generate_data.py"];
          outputs = ["data.csv"];
          # Dependencies are co-located with the step
          buildInputs = [ nixpkgs.python311Packages.pandas ];
        }
        {
          name = "analysis";
          cmd = "python scripts/analyze.py";
          inputs = ["data.csv", "scripts/analyze.py"];
          outputs = ["results.json", "figures/*.png"];
          buildInputs = [ nixpkgs.python311Packages.matplotlib ];
        }
      ];
    };

    # The dev shell includes all dependencies from all steps
    devShells.default = pkgs.mkShell {
      buildInputs = [
        pkgs.python311
      ] ++ (builtins.concatMap (step: step.buildInputs) self.csConfig.pipeline);
    };
  };
}
```

## Pipeline Management

### Viewing the Pipeline Status

The `cs view` command provides a rich, real-time summary of your pipeline's status directly in your terminal.

```bash
cs view
```

This command will display each step, its inputs and outputs, and their current status (`up-to-date`, `stale`, or `missing`), helping you understand what needs to be run.

### Executing the Pipeline

CSF executes pipeline steps in order with staleness detection (CSF §6):

```bash
# Build entire pipeline
cs build

# Build specific step (and its predecessors)
cs build analysis

# Force rebuild
cs build --force
```

## 🔐 Identity & Attestation

CSF uses Ed25519 keys with `did:key` identifiers to create cryptographically signed attestations for your entire pipeline.

```bash
# Create a new DID identity (only needs to be done once)
cs id create

# Create a signed attestation for the entire pipeline
cs attest --pipeline

# View the attestation
cat pipeline_attestation.json
```

## 🧪 Starter Templates

CSF provides production-ready starter templates. Use `cs init <template-name>` to get started. All templates are now based on the unified `flake.nix` configuration.

---

*This core implementation enables reproducible computational science through a unified, flake-based configuration and cryptographically verifiable pipeline attestations.*
