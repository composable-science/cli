"""Configuration management for CSF CLI"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional
from cs.utils.output import error

class CSFConfig:
    """
    Manages CSF project configuration by loading it from `flake.nix`.
    
    The configuration is loaded by evaluating the `csConfig` attribute
    from the `flake.nix` in the project root.
    """
    
    def __init__(self, start_path=None):
        self.start_path = Path(start_path) if start_path else Path.cwd()
        self.project_root = self._find_project_root()
        self.manifest_path = self.project_root / "flake.nix" if self.project_root else None
        self.outputs_dir = self.project_root / ".csf" / "outputs" if self.project_root else None

    def _find_project_root(self) -> Optional[Path]:
        """Find the project root by searching for `flake.nix`"""
        d = self.start_path
        while d.parent != d:
            if (d / "flake.nix").is_file():
                return d
            d = d.parent
        # Check the last directory as well
        if (d / "flake.nix").is_file():
            return d
        return None

    def has_manifest(self) -> bool:
        """Check if a `flake.nix` was found"""
        return self.manifest_path is not None and self.manifest_path.is_file()

    def load_manifest(self) -> Optional[dict]:
        """Load the project configuration by evaluating `flake.nix`"""
        if not self.has_manifest():
            return None
        try:
            # Get the current system's identifier from `nix show-config`
            system_result = subprocess.run(
                ['nix', 'show-config', '--json'],
                capture_output=True, text=True, check=True
            )
            nix_config = json.loads(system_result.stdout)
            current_system = nix_config.get('system', {}).get('value')

            if not current_system:
                error("Could not determine current system from `nix show-config`.")
                return None

            # Use `nix eval` to extract the configuration for all systems
            result = subprocess.run(
                ['nix', 'eval', '--impure', '--no-write-lock-file', '.#csConfig', '--json'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            all_configs = json.loads(result.stdout)

            # The output of `nix eval` on a flake-utils `eachDefaultSystem` output
            # is a mapping from system identifiers to the actual flake output.
            if current_system in all_configs:
                return all_configs[current_system]
            else:
                error(f"Configuration for current system '{current_system}' not found in flake.nix.")
                return None

        except subprocess.CalledProcessError as e:
            error(f"Error evaluating flake.nix: {e.stderr}")
            return None
        except json.JSONDecodeError:
            error("Failed to parse JSON output from `nix eval`.")
            return None
        except Exception as e:
            error(f"An unexpected error occurred while loading configuration: {e}")
            return None
            
    def get_identity_dir(self) -> Path:
        """Get directory for DID keys and identity (CSF §8)"""
        identity_dir = Path.home() / ".config" / "composable-science"
        identity_dir.mkdir(parents=True, exist_ok=True)
        return identity_dir
