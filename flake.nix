{
  description = "The Composable Science (cs) command-line tool.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # Define the Python environment with all CSF dependencies
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          click
          toml
          cryptography
          requests
          rich
          pandas
          numpy
          matplotlib
          pytest
        ]);

        # Package the 'cs' command
        cs-cli = pkgs.writeShellScriptBin "cs" ''
          #!${pkgs.stdenv.shell}
          # Set the PYTHONPATH to include the 'src' directory within this flake
          export PYTHONPATH=${self}/src:$PYTHONPATH
          exec ${pythonEnv}/bin/python ${self}/src/cs/main.py "$@"
        '';

      in
      {
        # Expose the 'cs' command as a package
        packages = {
          default = cs-cli;
          cs = cs-cli;
        };

        # Expose the 'cs' command as a runnable app
        apps = {
          default = flake-utils.lib.mkApp { drv = cs-cli; };
          cs = flake-utils.lib.mkApp { drv = cs-cli; };
        };

        # A dev shell for working on the 'cs' tool itself
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            cs-cli
          ];
        };
      }
    );
}