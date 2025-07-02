#!/usr/bin/env bash
# CSF CLI wrapper script for development

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH to include the src directory
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Run the main CLI script
exec python3 "${SCRIPT_DIR}/src/cs/main.py" "$@"
