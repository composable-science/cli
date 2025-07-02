#!/usr/bin/env python3
"""
Composable Science Framework CLI

Command-line interface for the CSF as specified in SPEC.md §3.
"""

import click
import sys
import os
from pathlib import Path

# Add the src directory to the path for proper imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from cs.commands.init import init_command
from cs.commands.build import build_command
from cs.commands.attest import attest_command
from cs.commands.diagram import diagram_command
from cs.commands.dashboard import dashboard_command
from cs.commands.doctor import doctor_command
from cs.commands.identity import identity_command
from cs.commands.view import view_command
from cs.config import CSFConfig
from cs.utils.output import console, success, error, info

@click.group(invoke_without_command=True)
@click.option('--json', 'output_json', is_flag=True, help='Output machine-readable JSON')
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def main(ctx, output_json, version):
    """
    Composable Science Framework CLI
    
    Standardises how computational research pipelines are declared, executed, 
    verified, and shared. (CSF Specification §3)
    """
    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj['config'] = CSFConfig()
    ctx.obj['output_json'] = output_json
    
    if version:
        if output_json:
            click.echo('{"version": "0.0.1", "specification": "v0.0.1"}')
        else:
            click.echo("Composable Science Framework CLI v0.0.1")
            click.echo("Specification: v0.0.1")
        return
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

# Register commands (CSF §3.2)
main.add_command(init_command, name="init")
main.add_command(build_command, name="build")  
main.add_command(attest_command, name="attest")
main.add_command(diagram_command, name="diagram")
main.add_command(dashboard_command, name="dashboard")
main.add_command(doctor_command, name="doctor")
main.add_command(identity_command, name="id")
main.add_command(view_command, name="view")

if __name__ == '__main__':
    main()
