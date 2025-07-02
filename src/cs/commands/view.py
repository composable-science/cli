"""View command - Display a rich summary of the pipeline status"""

import click
import glob
import os
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from cs.config import CSFConfig
from cs.utils.output import error
from cs.commands.build import is_step_stale

@click.command()
@click.pass_context
def view_command(ctx):
    """Display a rich, real-time summary of the pipeline status."""
    
    config = ctx.obj['config']
    console = Console()
    
    if not config.has_manifest():
        error("No flake.nix found. Run 'cs init <template>' to create a new project.", exit_code=64)
        return
        
    manifest = config.load_manifest()
    if not manifest:
        # The config loader already printed an error
        return

    # --- Project Panel ---
    project_name = manifest.get('package', {}).get('name', 'Unnamed Project')
    project_version = manifest.get('package', {}).get('version', 'N/A')
    project_info = f"[bold cyan]{project_name}[/bold cyan] [yellow]v{project_version}[/yellow]"
    console.print(Panel(project_info, title="Project", expand=False))

    # --- Pipeline Tree ---
    pipeline_steps = manifest.get('pipeline', [])
    if not pipeline_steps:
        console.print("[yellow]No pipeline steps defined in your flake.nix.[/yellow]")
        return

    tree = Tree("📦 [bold]Pipeline Status[/bold]", guide_style="bold bright_blue")

    for step in pipeline_steps:
        stale = is_step_stale(step)
        status_icon = "[yellow]Stale[/yellow]" if stale else "[green]Up-to-date[/green]"
        step_tree = tree.add(f"🔹 [bold]{step['name']}[/bold] ({status_icon})")
        
        # Inputs
        inputs_tree = step_tree.add("📥 [cyan]Inputs[/cyan]")
        for pattern in step.get('inputs', []):
            matches = glob.glob(pattern)
            if not matches:
                inputs_tree.add(f"[red]• {pattern} (missing)[/red]")
            else:
                for match in matches:
                    inputs_tree.add(f"[dim]• {match}[/dim]")

        # Outputs
        outputs_tree = step_tree.add("📤 [cyan]Outputs[/cyan]")
        for pattern in step.get('outputs', []):
            matches = glob.glob(pattern)
            if not matches:
                outputs_tree.add(f"[red]• {pattern} (missing)[/red]")
            else:
                for match in matches:
                    # Check mtime vs inputs
                    output_stale = False
                    input_mtimes = []
                    for in_pattern in step.get('inputs', []):
                        for in_match in glob.glob(in_pattern):
                            input_mtimes.append(os.path.getmtime(in_match))
                    
                    if input_mtimes and os.path.exists(match):
                        if max(input_mtimes) > os.path.getmtime(match):
                            output_stale = True
                    
                    status = "[yellow](stale)[/yellow]" if output_stale else "[green](up-to-date)[/green]"
                    outputs_tree.add(f"• {match} {status}")

    console.print(tree)