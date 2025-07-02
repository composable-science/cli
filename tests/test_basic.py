"""Basic tests for CSF CLI"""

import pytest
import tempfile
import os
from pathlib import Path
import subprocess
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cs.config import CSFConfig
from cs.identity import IdentityManager

def test_config_no_manifest():
    """Test config when no flake.nix is present"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            config = CSFConfig()
            assert not config.has_manifest()
            assert config.load_manifest() is None
        finally:
            os.chdir(original_cwd)

def test_identity_creation():
    """Test DID identity creation"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock config
        class MockConfig:
            def get_identity_dir(self):
                return Path(temp_dir)
        
        config = MockConfig()
        identity_manager = IdentityManager(config)
        
        # Initially no identity
        assert not identity_manager.has_identity()
        
        # Create identity
        did = identity_manager.create_identity()
        
        # Check identity was created
        assert identity_manager.has_identity()
        assert did.startswith("did:key:z")
        assert identity_manager.get_did() == did

def test_cli_help():
    """Test CLI help command"""
    # Test that the CLI can be imported and run
    try:
        from cs.main import main
        # This would normally be tested with click.testing.CliRunner
        # but for now just check that imports work
        assert main is not None
    except ImportError as e:
        pytest.skip(f"CLI dependencies not available: {e}")

if __name__ == "__main__":
    pytest.main([__file__])
