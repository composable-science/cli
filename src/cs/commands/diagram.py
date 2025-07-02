"""Diagram command - Render Mermaid diagrams (CSF §12)"""

import click
from pathlib import Path
from cs.utils.output import success, error, info
from cs.config import CSFConfig

@click.command()
@click.option('--output', '-o', default='pipeline.mmd', help='Output file for Mermaid diagram')
@click.pass_context
def diagram_command(ctx, output):
    """Render a Mermaid diagram without HTML (CSF §12)"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    
    if not config.has_manifest():
        error("No flake.nix found. Run 'cs init <template>' to create a new project.", output_json, exit_code=64)
        return
    
    manifest = config.load_manifest()
    if not manifest:
        # The config loader already printed an error
        return
    
    # Generate Mermaid diagram
    mermaid_content = generate_mermaid_diagram(manifest)
    
    # Write diagram file
    diagram_path = Path(output)
    with open(diagram_path, 'w') as f:
        f.write(mermaid_content)
    
    success(f"Mermaid diagram written to: {diagram_path}", output_json)

def generate_mermaid_diagram(manifest: dict) -> str:
    """Generate Mermaid flowchart from pipeline steps showing data flow (CSF §12)"""
    
    pipeline_steps = manifest.get('pipeline', [])
    
    if not pipeline_steps:
        return "graph TD\n    A[No pipeline steps defined]"
    
    # Start flowchart
    lines = ["graph TD"]
    
    # Track all files in the pipeline
    all_files = set()
    file_producers = {}  # file -> step that produces it
    file_consumers = {}  # file -> list of steps that consume it
    
    # First pass: collect all files and their relationships
    for i, step in enumerate(pipeline_steps):
        step_name = step['name']
        
        # Process outputs (what this step produces)
        for output_pattern in step.get('outputs', []):
            all_files.add(output_pattern)
            file_producers[output_pattern] = i
        
        # Process inputs (what this step consumes)
        for input_pattern in step.get('inputs', []):
            all_files.add(input_pattern)
            if input_pattern not in file_consumers:
                file_consumers[input_pattern] = []
            file_consumers[input_pattern].append(i)
    
    # Add nodes for each step
    for i, step in enumerate(pipeline_steps):
        step_name = step['name']
        step_cmd = step['cmd'][:25] + "..." if len(step['cmd']) > 25 else step['cmd']
        
        # Create node with step info
        node_id = f"step_{i}"
        node_label = f"{step_name}\\n{step_cmd}"
        lines.append(f"    {node_id}[\"{node_label}\"]")
    
    # Add nodes for files and create data flow connections
    file_counter = 0
    for file_pattern in sorted(all_files):
        file_id = f"file_{file_counter}"
        file_counter += 1
        
        # Create file node
        lines.append(f"    {file_id}([{file_pattern}])")
        
        # Connect producer to file
        if file_pattern in file_producers:
            producer_step = file_producers[file_pattern]
            lines.append(f"    step_{producer_step} --> {file_id}")
        
        # Connect file to consumers
        if file_pattern in file_consumers:
            for consumer_step in file_consumers[file_pattern]:
                lines.append(f"    {file_id} --> step_{consumer_step}")
    
    # Add styling
    lines.extend([
        "",
        "    classDef stepNode fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
        "    classDef fileNode fill:#f3e5f5,stroke:#4a148c,stroke-width:1px"
    ])
    
    # Apply classes
    for i in range(len(pipeline_steps)):
        lines.append(f"    class step_{i} stepNode")
    
    for i in range(file_counter):
        lines.append(f"    class file_{i} fileNode")
    
    return "\n".join(lines)
