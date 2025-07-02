import unittest
import os
import json
from pathlib import Path
from click.testing import CliRunner
from cs.main import main

# A minimal flake.nix content for testing
FLAKE_CONTENT = """
{
  description = "A test flake for the cs CLI";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: {
    csConfig = {
      package = {
        name = "view-test-project";
        version = "1.0.0";
      };
      pipeline = [
        {
          name = "generate-data";
          cmd = "echo 'data' > data.csv";
          inputs = [];
          outputs = ["data.csv"];
        }
        {
          name = "process-data";
          cmd = "echo 'processed' > processed.txt";
          inputs = ["data.csv"];
          outputs = ["processed.txt"];
        }
      ];
    };
  };
}
"""

class TestViewCommandWithFlake(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.test_dir = Path("test_view_project_flake")
        self.test_dir.mkdir(exist_ok=True)
        os.chdir(self.test_dir)

        # Create a sample flake.nix
        with open("flake.nix", "w") as f:
            f.write(FLAKE_CONTENT)

    def tearDown(self):
        os.chdir("..")
        for f in self.test_dir.glob("*"):
            f.unlink()
        self.test_dir.rmdir()

    def test_view_command_initial_state(self):
        """Test `cs view` when no artifacts have been built, using flake.nix."""
        result = self.runner.invoke(main, ['view'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("view-test-project", result.output)
        self.assertIn("generate-data", result.output)
        self.assertIn("process-data", result.output)
        self.assertIn("(missing)", result.output)

    def test_view_command_after_build(self):
        """Test `cs view` after building the pipeline, using flake.nix."""
        # Build the first step
        result = self.runner.invoke(main, ['build', 'generate-data'])
        self.assertEqual(result.exit_code, 0, result.output)
        
        # Run view
        result = self.runner.invoke(main, ['view'])
        self.assertEqual(result.exit_code, 0, result.output)
        
        # The first step's output should be up-to-date
        self.assertIn("data.csv (up-to-date)", result.output)
        # The second step should now be stale, but its output is still missing
        self.assertIn("process-data (Stale)", result.output)
        self.assertIn("processed.txt (missing)", result.output)

        # Build the second step
        result = self.runner.invoke(main, ['build', 'process-data'])
        self.assertEqual(result.exit_code, 0, result.output)

        # Run view again
        result = self.runner.invoke(main, ['view'])
        self.assertEqual(result.exit_code, 0, result.output)

        # Everything should be up-to-date
        self.assertIn("data.csv (up-to-date)", result.output)
        self.assertIn("processed.txt (up-to-date)", result.output)
        self.assertIn("Up-to-date", result.output)
        self.assertNotIn("(missing)", result.output)
        self.assertNotIn("(stale)", result.output)

if __name__ == '__main__':
    unittest.main()