"""Dashboard command - Generate HTML dashboard (CSF §12)"""

import click
from pathlib import Path
import json
import webbrowser
from cs.utils.output import success, error, info
from cs.config import CSFConfig
from cs.commands.diagram import generate_mermaid_diagram

@click.command()
@click.option('--output', '-o', default='dashboard', help='Output directory for dashboard')
@click.option('--port', '-p', default=8080, help='Port for local server')
@click.option('--no-open', is_flag=True, help='Do not auto-open browser')
@click.option('--enhanced', is_flag=True, help='Generate enhanced interactive dashboard')
@click.option('--legacy', is_flag=True, help='Generate legacy Mermaid-only dashboard')
@click.pass_context
def dashboard_command(ctx, output, port, no_open, enhanced, legacy):
    """Generate HTML dashboard with Mermaid diagram (CSF §12)"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    
    if not config.has_manifest():
        error("No flake.nix found. Run 'cs init <template>' to create a new project.", output_json, exit_code=64)
        return
    
    manifest = config.load_manifest()
    if not manifest:
        # The config loader already printed an error
        return
    
    # Create dashboard directory
    dashboard_dir = Path(output)
    dashboard_dir.mkdir(exist_ok=True)
    
    # Generate dashboard content
    info("Generating dashboard...", output_json)
    
    # Generate Mermaid diagram
    mermaid_content = generate_mermaid_diagram(manifest)
    
    # Choose dashboard type
    use_enhanced = enhanced or (not legacy and not enhanced)  # Default to enhanced
    
    if use_enhanced:
        info("Creating enhanced interactive dashboard...", output_json)
        html_content = generate_enhanced_dashboard_html(manifest, mermaid_content, config)
        # Generate additional data files for enhanced dashboard
        generate_enhanced_dashboard_data_files(dashboard_dir, manifest, config)
        
        # Generate LaTeX configuration for CSF linking
        try:
            latex_config_path = generate_csf_latex_config(config, manifest)
            info(f"Generated LaTeX configuration: {latex_config_path}", output_json)
        except Exception as e:
            info(f"Warning: Could not generate LaTeX config: {e}", output_json)
    else:
        info("Creating legacy Mermaid-only dashboard...", output_json)
        html_content = generate_dashboard_html(manifest, mermaid_content, config)
    
    # Write dashboard files
    index_path = dashboard_dir / "index.html"
    with open(index_path, 'w') as f:
        f.write(html_content)
    
    # Write Mermaid diagram separately
    diagram_path = dashboard_dir / "pipeline.mmd"
    with open(diagram_path, 'w') as f:
        f.write(mermaid_content)
    
    success(f"Dashboard generated: {index_path}", output_json)
    
    # Check if should auto-open
    build_config = manifest.get('build', {})
    should_open = build_config.get('open_dashboard', True) and not no_open
    
    if should_open:
        try:
            webbrowser.open(f"file://{index_path.absolute()}")
            info("Dashboard opened in browser", output_json)
        except Exception:
            info(f"Please open {index_path} in your browser", output_json)

def generate_dashboard_html(manifest: dict, mermaid_content: str, config: CSFConfig) -> str:
    """Generate HTML dashboard content (CSF §12)"""
    
    package_info = manifest.get('package', {})
    pipeline_steps = manifest.get('pipeline', [])
    
    # Get step status information
    step_status = get_pipeline_status(pipeline_steps, config)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSF Dashboard - {package_info.get('name', 'Untitled Project')}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8fafc;
        }}
        .header {{
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 24px;
        }}
        .project-title {{
            font-size: 24px;
            font-weight: 600;
            color: #1e293b;
            margin: 0 0 8px 0;
        }}
        .project-meta {{
            color: #64748b;
            font-size: 14px;
        }}
        .main-content {{
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 24px;
        }}
        .diagram-section {{
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        .status-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .step-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .step-item {{
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .step-item:last-child {{
            border-bottom: none;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            margin-right: 12px;
            min-width: 80px;
            text-align: center;
        }}
        .status-up-to-date {{
            background-color: #dcfce7;
            color: #166534;
        }}
        .status-stale {{
            background-color: #fef3c7;
            color: #92400e;
        }}
        .status-failed {{
            background-color: #fecaca;
            color: #dc2626;
        }}
        .step-name {{
            font-weight: 500;
            color: #1e293b;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: #1e293b;
            margin: 0 0 16px 0;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
        }}
        .refresh-btn {{
            background: #3b82f6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        .refresh-btn:hover {{
            background: #2563eb;
        }}
        @media (max-width: 768px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="project-title">{package_info.get('name', 'Untitled Project')}</h1>
        <div class="project-meta">
            Version: {package_info.get('version', '0.0.1')} | 
            License: {package_info.get('license', 'Unknown')} |
            Generated: {get_current_timestamp()}
        </div>
    </div>

    <div class="main-content">
        <div class="diagram-section">
            <h2 class="section-title">Pipeline Diagram</h2>
            <div class="mermaid">
{mermaid_content}
            </div>
        </div>

        <div class="sidebar">
            <div class="status-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h3 class="section-title" style="margin: 0;">Pipeline Status</h3>
                    <button class="refresh-btn" onclick="location.reload()">Refresh</button>
                </div>
                <ul class="step-list">
{generate_step_status_html(step_status)}
                </ul>
            </div>

            <div class="status-card">
                <h3 class="section-title">Quick Actions</h3>
                <p style="margin: 0 0 12px 0; color: #64748b; font-size: 14px;">
                    Run these commands in your terminal:
                </p>
                <code style="display: block; background: #f1f5f9; padding: 12px; border-radius: 4px; font-size: 12px; margin-bottom: 8px;">
                    cs build
                </code>
                <code style="display: block; background: #f1f5f9; padding: 12px; border-radius: 4px; font-size: 12px;">
                    cs attest &lt;step&gt;
                </code>
            </div>
        </div>
    </div>

    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def get_pipeline_status(pipeline_steps: list, config: CSFConfig) -> list:
    """Get status of each pipeline step"""
    
    status_list = []
    
    for step in pipeline_steps:
        # Import here to avoid circular imports
        from cs.commands.build import is_step_stale
        
        step_name = step['name']
        
        try:
            if is_step_stale(step):
                status = "stale"
            else:
                status = "up-to-date"
        except Exception:
            status = "failed"
        
        status_list.append({
            'name': step_name,
            'status': status,
            'command': step['cmd']
        })
    
    return status_list

def generate_step_status_html(step_status: list) -> str:
    """Generate HTML for step status list"""
    
    html_items = []
    
    for step in step_status:
        status_class = f"status-{step['status'].replace('-', '-')}"
        status_text = step['status'].replace('-', ' ').title();
        
        html_items.append(f'''                    <li class="step-item">
                        <span class="status-badge {status_class}">{status_text}</span>
                        <span class="step-name">{step['name']}</span>
                    </li>''')
    
    return '\n'.join(html_items)

def get_current_timestamp() -> str:
    """Get current timestamp for display"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_enhanced_dashboard_html(manifest: dict, mermaid_content: str, config: CSFConfig) -> str:
    """Generate enhanced interactive dashboard HTML with multi-pane interface"""
    project_name = manifest.get('package', {}).get('name', 'Unnamed Project')
    steps = manifest.get('pipeline', [])
    
    # Generate enhanced CSS and JavaScript
    enhanced_css = generate_enhanced_css()
    enhanced_js = generate_enhanced_js()
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSF Enhanced Dashboard - {project_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script src="https://unpkg.com/monaco-editor@0.44.0/min/vs/loader.js"></script>
    <style>
{enhanced_css}
    </style>
</head>
<body>
    <div class="enhanced-dashboard">
        <div class="header">
            <div class="project-title">{project_name}</div>
            <div class="project-meta">Enhanced CSF Dashboard • Interactive Pipeline Explorer</div>
        </div>

        <div class="main-content">
            <!-- Pipeline Overview Pane -->
            <div class="pipeline-pane">
                <div class="section-title">Pipeline Overview</div>
                <div class="mermaid" id="pipeline-diagram">
{mermaid_content}
                </div>
                <div class="pipeline-status">
                    {generate_pipeline_status_html(steps)}
                </div>
            </div>

            <!-- Explorer Tree Pane -->
            <div class="explorer-pane">
                <div class="section-title">Project Explorer</div>
                <div class="explorer-toolbar">
                    <input type="text" id="explorer-search" placeholder="Search files..." />
                    <button id="refresh-tree">🔄</button>
                </div>
                <div id="file-tree" class="file-tree">
                    <!-- Populated by JavaScript -->
                </div>
            </div>

            <!-- Content Viewer Pane -->
            <div class="content-pane">
                <div class="section-title">Content Viewer</div>
                <div class="content-toolbar">
                    <span id="selected-file">Select a file to view</span>
                    <div class="content-actions">
                        <button id="copy-path">📋 Copy Path</button>
                        <button id="view-attestation">🔒 Attestation</button>
                    </div>
                </div>
                <div id="content-viewer" class="content-viewer">
                    <div class="empty-state">
                        <div class="empty-icon">📁</div>
                        <div>Click on a pipeline step or file to explore</div>
                    </div>
                </div>
                <div id="file-metadata" class="file-metadata"></div>
            </div>
        </div>
    </div>

    <script>
{enhanced_js}
    </script>
</body>
</html>"""
    
    return html_content


def generate_enhanced_css():
    """Generate CSS for enhanced dashboard"""
    return """
        /* Enhanced Dashboard Styles */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8fafc;
            height: 100vh;
            overflow: hidden;
        }

        .enhanced-dashboard {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header {
            background: white;
            padding: 16px 24px;
            border-bottom: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .project-title {
            font-size: 20px;
            font-weight: 600;
            color: #1e293b;
            margin: 0 0 4px 0;
        }

        .project-meta {
            color: #64748b;
            font-size: 14px;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 300px 400px;
            gap: 1px;
            background: #e2e8f0;
            flex: 1;
            overflow: hidden;
        }

        .pipeline-pane, .explorer-pane, .content-pane {
            background: white;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
            padding: 16px 20px 12px 20px;
            border-bottom: 1px solid #f1f5f9;
            background: #fafafa;
        }

        .mermaid {
            padding: 20px;
            flex: 1;
            overflow: auto;
        }

        .pipeline-status {
            border-top: 1px solid #f1f5f9;
            padding: 16px 20px;
            background: #fafafa;
        }

        .step-item {
            display: flex;
            align-items: center;
            padding: 8px 0;
            cursor: pointer;
            border-radius: 4px;
            transition: background-color 0.2s;
        }

        .step-item:hover {
            background-color: #f8fafc;
        }

        .step-item.selected {
            background-color: #e0f2fe;
        }

        .status-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 500;
            margin-right: 8px;
            min-width: 60px;
            text-align: center;
        }

        .status-up-to-date {
            background-color: #dcfce7;
            color: #166534;
        }

        .status-stale {
            background-color: #fef3c7;
            color: #92400e;
        }

        .status-failed {
            background-color: #fecaca;
            color: #dc2626;
        }

        .explorer-toolbar {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9;
            gap: 8px;
        }

        #explorer-search {
            flex: 1;
            padding: 6px 10px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            font-size: 12px;
        }

        #refresh-tree {
            padding: 6px 8px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            background: white;
            cursor: pointer;
            font-size: 12px;
        }

        .file-tree {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }

        .tree-node {
            display: flex;
            align-items: center;
            padding: 4px 8px;
            cursor: pointer;
            border-radius: 3px;
            font-size: 13px;
            user-select: none;
        }

        .tree-node:hover {
            background-color: #f8fafc;
        }

        .tree-node.selected {
            background-color: #e0f2fe;
        }

        .tree-icon {
            margin-right: 6px;
            width: 16px;
            text-align: center;
        }

        .tree-children {
            margin-left: 16px;
            border-left: 1px dotted #d1d5db;
            padding-left: 8px;
        }

        .content-toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9;
            background: #fafafa;
        }

        #selected-file {
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
        }

        .content-actions {
            display: flex;
            gap: 8px;
        }

        .content-actions button {
            padding: 4px 8px;
            border: 1px solid #d1d5db;
            border-radius: 3px;
            background: white;
            cursor: pointer;
            font-size: 11px;
        }

        .content-viewer {
            flex: 1;
            overflow: auto;
            background: #fafafa;
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #94a3b8;
            text-align: center;
        }

        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        #monaco-editor {
            height: 100%;
            width: 100%;
        }

        .image-viewer {
            padding: 20px;
            text-align: center;
        }

        .image-viewer img {
            max-width: 100%;
            max-height: 400px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 4px;
        }

        .file-metadata {
            border-top: 1px solid #f1f5f9;
            padding: 12px 16px;
            background: #fafafa;
            font-size: 12px;
            color: #64748b;
        }

        .metadata-item {
            margin-bottom: 4px;
        }

        /* Node type styling for Mermaid */
        .node-script {
            fill: #2E3192 !important;
            stroke: #1e40af !important;
        }

        .node-data-static {
            fill: #6B7280 !important;
            stroke: #4b5563 !important;
        }

        .node-data-derived {
            fill: #10B981 !important;
            stroke: #059669 !important;
        }

        .node-step {
            fill: #FFC107 !important;
            stroke: #d97706 !important;
        }

        .node-document {
            fill: #8B5CF6 !important;
            stroke: #7c3aed !important;
        }
    """


def generate_enhanced_js():
    """Generate JavaScript for enhanced dashboard interactivity"""
    return r'''
        // Enhanced Dashboard JavaScript
        class EnhancedDashboard {
            constructor() {
                this.selectedNode = null;
                this.selectedFile = null;
                this.fileTree = null;
                this.monacoEditor = null;
                this.init();
            }

            async init() {
                // Initialize Mermaid
                mermaid.initialize({ 
                    startOnLoad: true,
                    theme: 'default',
                    flowchart: {
                        useMaxWidth: true
                    }
                });

                // Load file tree data
                await this.loadFileTree();
                
                // Set up event listeners
                this.setupEventListeners();
                
                // Initialize Monaco Editor
                this.initMonacoEditor();
            }

            async loadFileTree() {
                try {
                    const response = await fetch('./data/files.json');
                    this.fileTree = await response.json();
                    this.renderFileTree();
                } catch (error) {
                    console.warn('Could not load file tree data:', error);
                    this.renderStaticFileTree();
                }
            }

            renderFileTree() {
                const treeContainer = document.getElementById('file-tree');
                if (!this.fileTree) return;

                treeContainer.innerHTML = this.renderTreeNode(this.fileTree, '');
            }

            renderStaticFileTree() {
                // Fallback static file tree
                const treeContainer = document.getElementById('file-tree');
                treeContainer.innerHTML = `
                    <div class="tree-node" data-path="scripts/">
                        <span class="tree-icon">📁</span>
                        scripts/
                    </div>
                    <div class="tree-children">
                        <div class="tree-node" data-path="scripts/make_figures.py">
                            <span class="tree-icon">🐍</span>
                            make_figures.py
                        </div>
                        <div class="tree-node" data-path="scripts/generate_sample_data.py">
                            <span class="tree-icon">🐍</span>
                            generate_sample_data.py
                        </div>
                    </div>
                    <div class="tree-node" data-path="data/">
                        <span class="tree-icon">📁</span>
                        data/
                    </div>
                    <div class="tree-children">
                        <div class="tree-node" data-path="data/raw/">
                            <span class="tree-icon">📁</span>
                            raw/
                        </div>
                    </div>
                    <div class="tree-node" data-path="figures/">
                        <span class="tree-icon">📁</span>
                        figures/
                    </div>
                    <div class="tree-children">
                        <div class="tree-node" data-path="figures/temperature_measurement.png">
                            <span class="tree-icon">🖼️</span>
                            temperature_measurement.png
                        </div>
                        <div class="tree-node" data-path="figures/measurement_distribution.png">
                            <span class="tree-icon">🖼️</span>
                            measurement_distribution.png
                        </div>
                    </div>
                    <div class="tree-node" data-path="paper.tex">
                        <span class="tree-icon">📄</span>
                        paper.tex
                    </div>
                `;
            }

            renderTreeNode(node, path) {
                let html = '';
                if (node.type === 'directory') {
                    html += `<div class="tree-node" data-path="${path}${node.name}/">`;
                    html += `<span class="tree-icon">📁</span>`;
                    html += `${node.name}/`;
                    html += `</div>`;
                    
                    if (node.children && node.children.length > 0) {
                        html += `<div class="tree-children">`;
                        for (const child of node.children) {
                            html += this.renderTreeNode(child, `${path}${node.name}/`);
                        }
                        html += `</div>`;
                    }
                } else {
                    const icon = this.getFileIcon(node.name);
                    html += `<div class="tree-node" data-path="${path}${node.name}">`;
                    html += `<span class="tree-icon">${icon}</span>`;
                    html += `${node.name}`;
                    html += `</div>`;
                }
                return html;
            }

            getFileIcon(filename) {
                const ext = filename.split('.').pop().toLowerCase();
                const icons = {
                    'py': '🐍',
                    'js': '📜',
                    'tex': '📄',
                    'pdf': '📕',
                    'png': '🖼️',
                    'jpg': '🖼️',
                    'jpeg': '🖼️',
                    'csv': '📊',
                    'json': '📋',
                    'md': '📝',
                    'txt': '📝'
                };
                return icons[ext] || '📄';
            }

            setupEventListeners() {
                // Pipeline step clicks
                document.addEventListener('click', (e) => {
                    if (e.target.classList.contains('step-item')) {
                        this.selectPipelineStep(e.target);
                    }
                });

                // File tree clicks
                document.addEventListener('click', (e) => {
                    if (e.target.closest('.tree-node')) {
                        const node = e.target.closest('.tree-node');
                        this.selectFile(node.dataset.path);
                    }
                });

                // Toolbar actions
                document.getElementById('copy-path')?.addEventListener('click', () => {
                    if (this.selectedFile) {
                        navigator.clipboard.writeText(this.selectedFile);
                    }
                });

                document.getElementById('refresh-tree')?.addEventListener('click', () => {
                    this.loadFileTree();
                });

                // Search
                document.getElementById('explorer-search')?.addEventListener('input', (e) => {
                    this.filterFileTree(e.target.value);
                });
            }

            selectPipelineStep(stepElement) {
                // Remove previous selection
                document.querySelectorAll('.step-item').forEach(el => {
                    el.classList.remove('selected');
                });
                
                stepElement.classList.add('selected');
                
                const stepName = stepElement.querySelector('.step-name')?.textContent;
                if (stepName) {
                    // Load files for this step
                    this.loadStepFiles(stepName);
                }
            }

            loadStepFiles(stepName) {
                // Map step names to directories
                const stepDirs = {
                    'data': 'data/',
                    'figures': 'figures/',
                    'paper': './' // root for paper files
                };
                
                const targetDir = stepDirs[stepName];
                if (targetDir) {
                    // Highlight relevant files in tree
                    this.highlightTreePath(targetDir);
                }
            }

            highlightTreePath(path) {
                document.querySelectorAll('.tree-node').forEach(node => {
                    node.classList.remove('selected');
                    if (node.dataset.path.startsWith(path)) {
                        node.classList.add('selected');
                    }
                });
            }

            async selectFile(path) {
                this.selectedFile = path;
                
                // Update toolbar
                document.getElementById('selected-file').textContent = path;
                
                // Clear previous selection
                document.querySelectorAll('.tree-node').forEach(node => {
                    node.classList.remove('selected');
                });
                
                // Select current file
                const node = document.querySelector(`[data-path="${path}"]`);
                if (node) {
                    node.classList.add('selected');
                }
                
                // Load file content
                await this.loadFileContent(path);
                
                // Update metadata
                this.updateFileMetadata(path);
            }

            async loadFileContent(path) {
                const viewer = document.getElementById('content-viewer');
                
                try {
                    // Check if it's an image
                    if (path.match(/\\.(png|jpg|jpeg|gif|svg)$/i)) {
                        viewer.innerHTML = `
                            <div class="image-viewer">
                                <img src="../${path}" alt="${path}" />
                            </div>
                        `;
                        return;
                    }
                    
                    // Try to load file content
                    const response = await fetch(`../api/content?path=${encodeURIComponent(path)}`);
                    if (response.ok) {
                        const content = await response.text();
                        this.displayCodeContent(content, path);
                    } else {
                        this.displayErrorMessage('Could not load file content');
                    }
                } catch (error) {
                    console.warn('Could not load file:', error);
                    this.displaySampleContent(path);
                }
            }

            displayCodeContent(content, path) {
                const language = this.getLanguageFromPath(path);
                
                if (this.monacoEditor) {
                    const model = monaco.editor.createModel(content, language);
                    this.monacoEditor.setModel(model);
                    document.getElementById('content-viewer').innerHTML = '<div id="monaco-editor"></div>';
                    this.monacoEditor = monaco.editor.create(
                        document.getElementById('monaco-editor'),
                        {
                            model: model,
                            theme: 'vs',
                            readOnly: true,
                            minimap: { enabled: false },
                            scrollBeyondLastLine: false
                        }
                    );
                }
            }

            displaySampleContent(path) {
                // Display sample content based on file type
                const viewer = document.getElementById('content-viewer');
                const ext = path.split('.').pop().toLowerCase();
                
                let sampleContent = '';
                if (ext === 'py' && path.includes('make_figures')) {
                    sampleContent = `#!/usr/bin/env python3
"""Generate figures for LaTeX paper"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

def main():
    # Ensure figures directory exists
    Path("figures").mkdir(exist_ok=True)
    
    # Load data
    data_files = list(Path("data/raw").glob("*.csv"))
    if not data_files:
        print("No CSV files found in data/raw/")
        return
    
    df = pd.read_csv(data_files[0])
    
    # Generate scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(df['temperature'], df['measurement'], alpha=0.6, s=30)
    plt.xlabel('Temperature (°C)')
    plt.ylabel('Measurement Value')
    plt.title('Temperature vs Measurement')
    plt.grid(True, alpha=0.3)
    plt.savefig('figures/temperature_measurement.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    main()`;
                } else if (ext === 'tex') {
                    sampleContent = `\\documentclass{article}
\\usepackage{graphicx}
\\usepackage{amsmath}

\\title{CSF Paper Template}
\\author{Your Name}
\\date{\\today}

\\begin{document}

\\maketitle

\\section{Introduction}

This is a sample paper created with the Composable Science Framework.
All computational steps are reproducible and verifiable.

\\section{Results}

\\begin{figure}[h]
\\centering
\\includegraphics[width=0.8\\textwidth]{figures/temperature_measurement.png}
\\caption{Temperature vs Measurement Analysis}
\\label{fig:temperature}
\\end{figure}

Figure \\ref{fig:temperature} shows the relationship between temperature and measurements.

\\end{document}`;
                } else {
                    sampleContent = `# ${path}

Content preview not available.
This is a placeholder showing the file structure.`;
                }
                
                viewer.innerHTML = `<pre style="padding: 20px; margin: 0; white-space: pre-wrap; font-family: 'Monaco', 'Courier New', monospace; font-size: 12px; line-height: 1.4;">${sampleContent}</pre>`;
            }

            displayErrorMessage(message) {
                const viewer = document.getElementById('content-viewer');
                viewer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">⚠️</div>
                        <div>${message}</div>
                    </div>
                `;
            }

            getLanguageFromPath(path) {
                const ext = path.split('.').pop().toLowerCase();
                const languages = {
                    'py': 'python',
                    'js': 'javascript',
                    'ts': 'typescript',
                    'tex': 'latex',
                    'json': 'json',
                    'md': 'markdown',
                    'txt': 'plaintext',
                    'csv': 'csv'
                };
                return languages[ext] || 'plaintext';
            }

            initMonacoEditor() {
                // Initialize Monaco Editor when first needed
                if (typeof monaco !== 'undefined') {
                    this.monacoReady = true;
                } else {
                    // Fallback - Monaco not available
                    this.monacoReady = false;
                }
            }

            updateFileMetadata(path) {
                const metadata = document.getElementById('file-metadata');
                // This would normally fetch real file metadata
                metadata.innerHTML = `
                    <div class="metadata-item"><strong>Path:</strong> ${path}</div>
                    <div class="metadata-item"><strong>Type:</strong> ${this.getFileType(path)}</div>
                    <div class="metadata-item"><strong>Modified:</strong> Recently</div>
                `;
            }

            getFileType(path) {
                const ext = path.split('.').pop().toLowerCase();
                const types = {
                    'py': 'Python Script',
                    'tex': 'LaTeX Document',
                    'png': 'PNG Image',
                    'csv': 'CSV Data',
                    'json': 'JSON Data'
                };
                return types[ext] || 'File';
            }

            filterFileTree(query) {
                const nodes = document.querySelectorAll('.tree-node');
                nodes.forEach(node => {
                    const text = node.textContent.toLowerCase();
                    const matches = text.includes(query.toLowerCase());
                    node.style.display = matches || !query ? 'flex' : 'none';
                });
            }
        }

        // Initialize enhanced dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new EnhancedDashboard();
        });
    '''


def generate_pipeline_status_html(steps):
    """Generate HTML for pipeline status section"""
    html = '<div class="pipeline-steps">'
    
    for step in steps:
        step_name = step.get('name', 'unknown')
        # For demo, assume all steps are up-to-date
        status = 'up-to-date'
        status_class = 'status-up-to-date'
        
        html += f'        <div class="step-item" data-step="{step_name}">\n'
        html += f'            <span class="status-badge {status_class}">Up To Date</span>\n'
        html += f'            <span class="step-name">{step_name}</span>\n'
        html += '        </div>\n'
    
    html += '</div>'
    return html


def generate_enhanced_dashboard_data_files(dashboard_dir, manifest, config):
    """Generate data files for enhanced dashboard"""
    import os
    import json
    from pathlib import Path
    
    # Create data directory
    data_dir = dashboard_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Generate pipeline metadata
    pipeline_data = {
        "steps": manifest.get('pipeline', []),
        "package": manifest.get('package', {}),
        "generated_at": "2025-07-01T00:00:00Z"
    }
    
    with open(data_dir / "pipeline.json", 'w') as f:
        json.dump(pipeline_data, f, indent=2)
    
    # Generate file tree structure
    project_root = Path.cwd()
    file_tree = scan_directory_tree(project_root)
    
    with open(data_dir / "files.json", 'w') as f:
        json.dump(file_tree, f, indent=2)
    
    # Check for attestation data
    attestation_file = project_root / "pipeline_attestation.json"
    if attestation_file.exists():
        import shutil
        shutil.copy(attestation_file, data_dir / "attestation.json")


def scan_directory_tree(root_path, max_depth=3, current_depth=0):
    """Scan directory tree and return structured data"""
    if current_depth >= max_depth:
        return None
    
    try:
        items = []
        for item in root_path.iterdir():
            # Skip hidden files and common build directories
            if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules', '.git']:
                continue
                
            if item.is_dir():
                children = scan_directory_tree(item, max_depth, current_depth + 1)
                items.append({
                    "name": item.name,
                    "type": "directory",
                    "children": children if children else []
                })
            else:
                items.append({
                    "name": item.name,
                    "type": "file",
                    "size": item.stat().st_size if item.exists() else 0
                })
        
        return sorted(items, key=lambda x: (x["type"] == "file", x["name"]))
    except PermissionError:
        return []

def generate_csf_latex_config(config, manifest):
    """Generate LaTeX configuration files for CSF integration"""
    from pathlib import Path
    import hashlib
    import subprocess
    from datetime import datetime
    
    # Create .csf directory
    csf_dir = Path('.csf')
    csf_dir.mkdir(exist_ok=True)
    
    # Generate project ID from git remote + current commit if available
    project_id = generate_project_id()
    
    # Get dashboard base URL from manifest or use default
    dashboard_url = manifest.get('build', {}).get('dashboard_base_url', 'https://dashboard.composable-science.org')
    
    # Get current commit hash
    commit_hash = get_git_commit_hash()
    
    # Generate LaTeX config file
    latex_config = f"""% .csf/config.tex (auto-generated by CSF)
% Generated: {datetime.now().isoformat()}

\\def\\csfprojectid{{{project_id}}}
\\def\\csfbaseurl{{{dashboard_url}}}
\\def\\csfcommit{{{commit_hash}}}
"""
    
    config_path = csf_dir / 'config.tex'
    with open(config_path, 'w') as f:
        f.write(latex_config)
    
    return config_path


def generate_project_id():
    """Generate a unique project ID based on git remote and path"""
    import subprocess
    import hashlib
    from pathlib import Path
    
    try:
        # Try to get git remote origin URL
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, check=True)
        remote_url = result.stdout.strip();
        
        # Combine with current working directory path
        cwd = str(Path.cwd())
        combined = f"{remote_url}:{cwd}"
        
        # Generate hash
        project_hash = hashlib.sha256(combined.encode()).hexdigest()[:12]
        return project_hash
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: use directory name + hash of path
        cwd = Path.cwd()
        fallback = f"{cwd.name}:{str(cwd)}"
        project_hash = hashlib.sha256(fallback.encode()).hexdigest()[:12]
        return project_hash


def get_git_commit_hash():
    """Get current git commit hash"""
    import subprocess
    
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()[:8]  # Short hash
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'unknown'
