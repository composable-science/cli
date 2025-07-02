{
  description = "CSF Project Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    texMini.url = "github:alexmill/texMini";
  };

  outputs = { self, nixpkgs, flake-utils, texMini }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Create a wrapper script for the cs command
        csWrapper = pkgs.writeShellScriptBin "cs" ''
          # Find the cs source directory by looking upwards from current directory
          find_cs_src() {
            local dir="$PWD"
            while [ "$dir" != "/" ]; do
              if [ -f "$dir/src/cs/main.py" ]; then
                echo "$dir"
                return 0
              fi
              dir="$(dirname "$dir")"
            done
            return 1
          }
          
          FLAKE_DIR=$(find_cs_src)
          if [ -n "$FLAKE_DIR" ] && [ -f "$FLAKE_DIR/src/cs/main.py" ]; then
            export PYTHONPATH="$FLAKE_DIR/src:$PYTHONPATH"
            exec ${pythonEnv}/bin/python "$FLAKE_DIR/src/cs/main.py" "$@"
          else
            echo "Error: Could not find cs module source directory (src/cs/main.py)"
            echo "Please run 'cs' from within a CSF project directory or its subdirectories"
            exit 1
          fi
        '';

        pythonEnv = pkgs.python313.withPackages (ps: [
          ps.click
          ps.toml
          ps.cryptography
          ps.requests
          ps.rich
          ps.pandas
          ps.numpy
          ps.matplotlib
          ps.pytest
        ]);

      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            python313Full
            python313Packages.pip
            git
            texMini.packages.${system}.texMiniBiblio
            csWrapper
          ];

          shellHook = ''
            echo "🔬 CSF Project Environment Ready"
            echo "📋 Available commands:"
            echo "  cs build        # Build pipeline"
            echo "  cs attest <step> # Create attestation"
            echo "  cs dashboard    # Open dashboard"
          '';
        };
      }
    );
}