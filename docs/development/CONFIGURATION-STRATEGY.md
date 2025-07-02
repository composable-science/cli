# Configuration Unification Strategy

*Version: 2025-07-02*

## 1. Overview

This document outlines the strategy for unifying the project's configuration management by consolidating all workflow and environment definitions into a single `flake.nix` file. This change will eliminate the need for `composable.toml`, making the Nix flake the single source of truth and strengthening the project's reproducibility guarantees.

## 2. The Problem: Dual Configuration

The project currently uses two separate files for configuration:

- **`composable.toml`**: Defines the pipeline workflow (steps, commands, inputs, outputs).
- **`flake.nix`**: Defines the computational environment (system dependencies).

This separation creates several challenges:
- **Redundancy**: Project metadata and dependencies are implicitly linked but defined in two places.
- **Synchronization Overhead**: Changes to the workflow in `composable.toml` (e.g., using a new tool) require manual updates to `flake.nix` to add the corresponding dependency.
- **Increased Complexity**: New contributors must understand both TOML and Nix to fully grasp the project's structure.

## 3. The Solution: `flake.nix` as the Single Source of Truth

We will adopt `flake.nix` as the sole configuration file. The pipeline definition, previously in `composable.toml`, will be migrated directly into the `flake.nix` using Nix's attribute sets.

### Example of a Unified `flake.nix`

```nix
{
  description = "A Composable Science Project";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # Define the pipeline directly in Nix
        cs-pipeline = {
          package = {
            name = "paper-example";
            version = "0.1.0";
          };
          pipeline = [
            {
              name = "generate-data";
              cmd = "python scripts/generate_sample_data.py";
              inputs = [ "scripts/generate_sample_data.py" ];
              outputs = [ "data/raw/experiments.csv" ];
              # Dependencies are co-located with the step
              buildInputs = [ pkgs.python311Packages.pandas ];
            }
            {
              name = "make-figures";
              cmd = "python scripts/make_figures.py";
              inputs = [ "data/raw/experiments.csv" "scripts/make_figures.py" ];
              outputs = [ "figures/temperature_measurement.png" ];
              buildInputs = [ pkgs.python311Packages.matplotlib ];
            }
          ];
        };

      in
      {
        # The CS tool can read this configuration directly
        csConfig = cs-pipeline;

        # The dev shell includes all dependencies from all steps
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.python311
          ] ++ (builtins.concatMap (step: step.buildInputs) cs-pipeline.pipeline);
        };
      }
    );
}
```

## 4. Implementation Plan

1.  **Modify `core/src/cs/config.py`**: Update the configuration loader to execute `nix eval .#csConfig --json` to read the pipeline definition from the active `flake.nix`. The `composable.toml` loading logic will be removed.

2.  **Update `cs` Commands**: Refactor the `build`, `attest`, and other commands to work with the configuration structure provided by the Nix evaluation.

3.  **Update Project Templates**: Modify all project templates to use this new, unified `flake.nix` structure, removing `composable.toml`.

4.  **Update Documentation**: Update all tutorials and documentation to reflect the new configuration strategy.

## 5. Benefits

- **Radical Simplicity**: By consolidating all configuration into a single file, we eliminate cognitive overhead. The entire project—what it is, what it does, and how it runs—is defined in one place.
- **Absolute Reproducibility**: The entire project—workflow and environment—is defined in a single, verifiable file. There is no possibility of divergence between the specified workflow and the environment it runs in.
- **Zero Synchronization Overhead**: The workflow and its dependencies are managed as a single atomic unit, eliminating a major source of errors and friction.
- **Philosophical Consistency**: Fully aligns the project with its stated goal of being a flake-native, reproducible framework.

## 6. Strategic Implications: The Scientific Flake Manager

This technical consolidation enables a significant strategic pivot. By making `flake.nix` the core of the user experience, we are positioning our tool as a **Scientific Flake Manager**.

Our core value proposition is no longer just "reproducible science," but "the simplest way to build, manage, and share fully reproducible computational projects." The `cs` tool becomes a high-level interface for generating and managing the underlying flake, which is the ultimate artifact of reproducibility.

This has implications for our product and marketing strategy:
- **Product Focus**: The `cs` CLI and associated UI should be seen as a user-friendly "flake generator." Commands like `cs add step` or `cs add dependency` would programmatically edit the `flake.nix` file.
- **Marketing Focus**: We can target a broader audience beyond those already familiar with Nix. The message is not "you need to learn Nix," but "we use Nix to make your science so reproducible that you don't have to think about it."

## 7. User Experience: Science-Oriented Workflow Abstraction

While the technical foundation is a DevOps workflow (managing flakes), the user experience must remain focused on the scientific workflow.

- **The UI is the Abstraction Layer**: The user interacts with scientific concepts (e.g., "pipeline," "step," "artifact," "dependency"). The UI translates these concepts into the underlying Nix configuration.
- **Progressive Disclosure of Complexity**:
    - **Beginner**: A user can initialize a template (`cs init paper`), run the pipeline (`cs build`), and never touch the `flake.nix` file.
    - **Intermediate**: A user can add a new Python dependency for a step using a simple command (`cs add dependency --step make-figures --pkg numpy`), which handles the flake modification automatically.
    - **Advanced**: A user who needs full control can directly edit the `flake.nix` file, using the full power of the Nix ecosystem.

By hiding the complexity of the flake management behind a science-oriented interface, we provide a gentle on-ramp to best-in-class reproducibility, making it accessible to all researchers.