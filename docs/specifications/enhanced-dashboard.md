# Enhanced CSF Dashboard & Artifact Linking — Feature Specification

*Version: 2025-07-01*

> **Purpose**: Specification for enhanced dashboard interactivity and document-embedded artifact linking in the Composable Science Framework, built on Nix flakes architecture.

---

## 0 · Executive Summary

This specification defines two major enhancements to the CSF ecosystem, implemented through a Nix flakes-based architecture:

1. **Interactive Dashboard Enhancement**: Transform the static Mermaid diagram into a rich, multi-pane interface with content exploration and visual artifact classification
2. **Document Artifact Linking**: Enable LaTeX documents to embed live links from figures back to their computational provenance in the CSF dashboard

These features bridge the gap between computational artifacts and their presentation in traditional academic documents, providing unprecedented transparency in scientific communication through reproducible, declarative Nix-based tooling.

---

## 0.1 · Nix Flakes Architecture

### 0.1.1 Core Repositories

The CSF ecosystem is built around specialized GitHub repositories providing Nix flakes for different functionality:

#### Primary Repositories

- **`github:composable-science/cli`** - Main CSF command-line interface
  - `#dashboard` - Enhanced interactive dashboard generator
  - `#legacy-dashboard` - Static Mermaid dashboard (compatibility)
  - `#attest` - Cryptographic attestation tools
  - `#doctor` - Environment validation

- **`github:composable-science/cstex`** - CSF-enhanced LaTeX toolchain (wrapper around texMini)
  - `#compile` - Intelligent LaTeX compilation with automatic CSF integration
  - `#preview` - Live preview with embedded provenance links
  - `#template` - Document templates with zero-configuration CSF integration
  - `#metadata-extract` - Extract computational metadata from pipeline artifacts

- **`github:composable-science/templates`** - Project templates
  - `#paper-latex` - Academic paper with CSF integration
  - `#basic-lab` - Minimal research pipeline
  - `#dataset-pipeline` - Data processing workflow

#### Command Paradigm

All CSF operations use Nix flakes for reproducible execution:

```bash
# Generate enhanced dashboard
nix run github:composable-science/cli#dashboard

# Compile paper with automatic CSF integration
nix run github:composable-science/cstex#compile

# Create new project from template
nix run github:composable-science/templates#paper-latex

# Compile LaTeX with CSF linking
nix run github:composable-science/cstex#compile -- paper.tex

# Initialize new CSF project
nix run github:composable-science/templates#paper-latex

# Validate environment
nix run github:composable-science/cli#doctor
```

### 0.1.2 Integration with `composable.toml`

The manifest format is extended to specify Nix flakes for each pipeline step:

```toml
[package]
name = "research.example.paper"
version = "0.1.0"

[build]
dashboard_flake = "github:composable-science/cli#dashboard"
dashboard_base_url = "https://dashboard.composable-science.org"

[[pipeline]]
name = "figures"
flake = "github:composable-science/python-sci"
cmd = "python scripts/make_figures.py"
inputs = ["data/raw/*.csv", "scripts/make_figures.py"]
outputs = ["figures/*.png"]

[[pipeline]]
name = "paper"
flake = "github:composable-science/cstex#compile"
cmd = "compile-csf paper.tex"
inputs = ["paper.tex", "figures/*.png", "composable.sty"]
outputs = ["paper.pdf"]

[attestation]
include = ["paper.pdf", "figures/*.png"]
```

---

## 0.2 · Intelligent Document Integration Paradigm

### 0.2.1 Zero-Configuration Linking

The `cstex` toolchain automatically discovers and links computational artifacts without requiring manual metadata specification. Instead of users having to write:

```latex
\csfigure{figures/histogram.png}{
  caption={Distribution of measurements},
  step={figures},
  script={scripts/make_figures.py},
  line={42}
}
```

Users simply write standard LaTeX:

```latex
\includegraphics{figures/histogram.png}
\caption{Distribution of measurements}
```

The `cstex` compiler automatically:
1. Scans the pipeline definition (`composable.toml`)
2. Identifies which step generated `figures/histogram.png`
3. Extracts the source script and line number from the pipeline
4. Injects provenance links into the compiled document
5. Generates dashboard URLs for each artifact

### 0.2.2 Structured Metadata Processing

`cstex` leverages structured data from multiple sources:

#### Pipeline Analysis
- Parses `composable.toml` to understand artifact dependencies
- Analyzes pipeline attestations for cryptographic verification
- Maps file outputs to their generating steps and scripts

#### Source Code Analysis
- Scans Python/R/Julia scripts for figure generation calls
- Identifies exact line numbers where artifacts are saved
- Extracts variable names and computational context

#### Document Structure Analysis
- Understands LaTeX document structure and cross-references
- Maintains mapping between document elements and computational artifacts
- Enables bidirectional linking (document ↔ computation)

### 0.2.3 Cross-Format Generalization

The paradigm is designed to generalize beyond LaTeX:

```bash
# LaTeX compilation
nix run github:composable-science/cstex#compile paper.tex

# Markdown compilation (future)
nix run github:composable-science/csmd#compile report.md

# Word document processing (future)
nix run github:composable-science/csdocx#process report.docx
```

Each format-specific tool follows the same pattern:
1. **Discover** computational artifacts in the document
2. **Analyze** the pipeline to understand provenance
3. **Inject** appropriate linking mechanisms for the format
4. **Generate** cross-references to the dashboard

### 0.2.4 Enhanced User Experience

#### For Document Authors
- Write natural LaTeX/Markdown without CSF-specific syntax
- Automatic figure and table linking
- Live preview with embedded provenance
- Intelligent error messages for missing artifacts

#### For Document Readers
- Click any figure/table to see its computational context
- Verify cryptographic attestations inline
- Download reproduction scripts with one click
- Navigate full dependency graphs

---

## 1 · Feature 1: Enhanced Dashboard Design & Interactivity

### 1.1 Current State Analysis

Based on index.html and SPEC.md §12, the current dashboard:
- Generates static Mermaid flowcharts from `composable.toml` pipeline definitions
- Shows basic step status (up-to-date/stale/failed)
- Links to build logs and attestations

### 1.2 Enhanced Architecture

#### 1.2.1 Multi-Pane Interface Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    CSF Enhanced Dashboard                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Pipeline      │   Explorer      │      Content Viewer         │
│   Overview      │   Tree          │                             │
│                 │                 │                             │
│  [Mermaid DAG]  │  📁 scripts/    │  ┌─────────────────────────┐ │
│                 │  📁 data/       │  │ make_figures.py         │ │
│  ┌─────────┐    │  📁 figures/    │  │                         │ │
│  │  data   │    │  📄 paper.tex   │  │ import matplotlib.pyplot│ │
│  │ (click) │    │                 │  │ import pandas as pd     │ │
│  └─────────┘    │  Selected:      │  │                         │ │
│       ↓         │  📄 scripts/    │  │ def create_histogram(): │ │
│  ┌─────────┐    │     make_figs.py│  │   ...                   │ │
│  │ figures │    │                 │  └─────────────────────────┘ │
│  └─────────┘    │                 │                             │
│       ↓         │                 │  File info: 2.3KB, Python  │
│  ┌─────────┐    │                 │  Last modified: 2h ago     │
│  │  paper  │    │                 │                             │
│  └─────────┘    │                 │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

#### 1.2.2 Visual Artifact Classification System

Based on the `composable.toml` format and pipeline definitions:

**Node Types & Visual Design:**

1. **Scripts/Executables** 
   - Shape: Rectangle with rounded corners
   - Color: Blue (#2E3192 - primary brand color)
   - Icon: Code symbol `<>`

2. **Static Data** (inputs not generated by pipeline)
   - Shape: Cylinder
   - Color: Gray (#6B7280)
   - Icon: Database symbol

3. **Derived Data** (outputs from pipeline steps)
   - Shape: Cylinder 
   - Color: Green (#10B981)
   - Icon: Generated data symbol

4. **Pipeline Steps** (active execution)
   - Shape: Hexagon
   - Color: Yellow (#FFC107 - accent color)
   - Icon: Gear/process symbol

5. **Documents/Reports**
   - Shape: Document icon
   - Color: Purple (#8B5CF6)
   - Icon: Document symbol

#### 1.2.3 Interactive Features

**Clickable Node Behavior:**
- **Left Click**: Select node and populate Explorer Tree + Content Viewer
- **Right Click**: Context menu (View attestation, Open in editor, Copy path)
- **Hover**: Tooltip with file size, modification time, step status

**Explorer Tree Features:**
- Hierarchical file browser rooted at project directory
- Expand/collapse directories up to 2 levels deep
- File type icons and size indicators
- Search/filter functionality

**Content Viewer Features:**
- Syntax-highlighted code display for text files
- Image preview for figures
- CSV/data preview for datasets
- JSON viewer for attestations
- Directory listing for folders

### 1.3 Attestation Integration

When `pipeline_attestation.json` exists, enhance the display:

```javascript
// Example: Resolve wildcards from attestation
{
  "step": "figures",
  "inputs": ["data/raw/*.csv"],
  "outputs": ["figures/*.png"],
  "resolved_inputs": ["data/raw/dataset1.csv", "data/raw/dataset2.csv"],
  "resolved_outputs": ["figures/histogram.png", "figures/scatter.png"]
}
```

**Visual Enhancements:**
- Show actual filenames instead of glob patterns
- Color-code files based on attestation status
- Display attestation metadata in Content Viewer
- Link to cryptographic verification

### 1.4 Implementation Requirements

#### 1.4.1 Nix Flake Structure for Dashboard

The dashboard generator is implemented as a Nix flake at `github:composable-science/cli#dashboard`:

```nix
# flake.nix for composable-science/cli
{
  description = "Composable Science Framework CLI Tools";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        csfDashboard = pkgs.writeShellApplication {
          name = "csf-dashboard";
          runtimeInputs = with pkgs; [ nodejs mermaid-cli ];
          text = ''
            ${builtins.readFile ./scripts/generate-dashboard.sh}
          '';
        };

        csfLegacyDashboard = pkgs.writeShellApplication {
          name = "csf-legacy-dashboard";
          runtimeInputs = with pkgs; [ nodejs mermaid-cli ];
          text = ''
            ${builtins.readFile ./scripts/generate-legacy-dashboard.sh}
          '';
        };

      in {
        packages = {
          dashboard = csfDashboard;
          legacy-dashboard = csfLegacyDashboard;
          default = csfDashboard;
        };
      });
}
```

#### 1.4.2 Command Interface

Users invoke dashboard generation through Nix flakes:

```bash
# Enhanced interactive dashboard (default)
nix run github:composable-science/cli#dashboard

# Legacy Mermaid-only dashboard
nix run github:composable-science/cli#legacy-dashboard

# Specify output directory
nix run github:composable-science/cli#dashboard -- --output ./custom-dashboard

# Auto-open in browser
nix run github:composable-science/cli#dashboard -- --open
```

#### 1.4.3 Dashboard Generation Script

The Nix flake executes a shell script that:

1. **Parses `composable.toml`** to extract pipeline metadata
2. **Scans project directory** to build file tree structure
3. **Loads attestation data** if available
4. **Generates static assets** (HTML, CSS, JS) with embedded data
5. **Creates dashboard directory** with complete standalone interface

```bash
#!/usr/bin/env bash
# scripts/generate-dashboard.sh

set -euo pipefail

# Parse command line arguments
OUTPUT_DIR="dashboard"
OPEN_BROWSER=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --open)
      OPEN_BROWSER=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate composable.toml exists
if [[ ! -f "composable.toml" ]]; then
  echo "Error: No composable.toml found in current directory"
  exit 1
fi

# Generate enhanced dashboard
echo "Generating enhanced CSF dashboard..."
mkdir -p "$OUTPUT_DIR"/{assets,data}

# Generate pipeline metadata
python3 -c "
import tomllib
import json
import os
from pathlib import Path

with open('composable.toml', 'rb') as f:
    manifest = tomllib.load(f)

# Extract pipeline data
pipeline_data = {
    'package': manifest.get('package', {}),
    'pipeline': manifest.get('pipeline', []),
    'build': manifest.get('build', {}),
    'generated_at': '$(date -Iseconds)'
}

with open('$OUTPUT_DIR/data/pipeline.json', 'w') as f:
    json.dump(pipeline_data, f, indent=2)
"

# Generate file tree
find . -type f -name "*.py" -o -name "*.tex" -o -name "*.csv" -o -name "*.png" \
  | grep -v __pycache__ | sort | python3 -c "
import json
import sys
from pathlib import Path

files = []
for line in sys.stdin:
    path = line.strip().lstrip('./')
    if path:
        files.append({
            'path': path,
            'type': 'file',
            'size': Path(path).stat().st_size if Path(path).exists() else 0
        })

with open('$OUTPUT_DIR/data/files.json', 'w') as f:
    json.dump(files, f, indent=2)
"

# Copy attestation data if exists
if [[ -f "pipeline_attestation.json" ]]; then
  cp pipeline_attestation.json "$OUTPUT_DIR/data/attestation.json"
fi

# Generate HTML template
cat > "$OUTPUT_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSF Enhanced Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="assets/dashboard.css">
</head>
<body>
    <div id="csf-dashboard">
        <!-- Dashboard content populated by JavaScript -->
    </div>
    <script src="assets/dashboard.js"></script>
</body>
</html>
EOF

# Generate CSS and JavaScript assets
# (Embedded assets from the enhanced dashboard implementation)

echo "Dashboard generated in: $OUTPUT_DIR"

if [[ "$OPEN_BROWSER" == "true" ]]; then
  if command -v open >/dev/null; then
    open "$OUTPUT_DIR/index.html"
  elif command -v xdg-open >/dev/null; then
    xdg-open "$OUTPUT_DIR/index.html"
  fi
fi
```

#### 1.4.4 Frontend Implementation

**Technology Stack:**
- HTML5 + CSS3 + Vanilla JavaScript (maintain CSF's minimal dependencies)
- Mermaid.js for DAG visualization (CDN)
- Monaco Editor for syntax highlighting (CDN)
- File Tree component (custom implementation)
- Static generation (no server required)
│   └── attestation.json    # Attestation data (if exists)
└── api/
    └── content.json        # File content endpoint
```

---

## 2 · Feature 2: Intelligent Document Artifact Linking

### 2.1 Current State Analysis

Based on the `paper-latex` template, the current workflow:
- LaTeX documents include figures via `\includegraphics{figures/plot.png}`
- No connection between document and computational provenance
- Manual citation of computational methods

### 2.2 CSTeX: Intelligent LaTeX Integration

#### 2.2.1 Paradigm Shift: From Manual to Automatic

Instead of requiring users to specify metadata manually, `cstex` automatically discovers and links computational artifacts. Users write standard LaTeX:

```latex
\documentclass{article}

\begin{document}

\section{Results}

\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{figures/temperature_measurement.png}
\caption{Temperature vs Measurement Analysis}
\label{fig:temperature}
\end{figure}

Figure \ref{fig:temperature} shows the relationship between temperature and measurements.

\end{document}
```

The `cstex` compiler automatically:
1. **Discovers** that `figures/temperature_measurement.png` exists in the document
2. **Analyzes** `composable.toml` to find which pipeline step generates this file
3. **Extracts** metadata from the source script (`scripts/make_figures.py`)
4. **Injects** provenance links into the compiled PDF
5. **Generates** dashboard URLs for verification

#### 2.2.2 CSTeX Flake Architecture

The CSF LaTeX toolchain is implemented as `github:composable-science/cstex` - a wrapper around texMini with enhanced metadata processing:

```nix
# flake.nix for composable-science/cstex
{
  description = "CSF-enhanced LaTeX compilation with automatic provenance linking";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    texMini.url = "github:alexmill/texMini";  # Ultra-lean LaTeX
  };

  outputs = { self, nixpkgs, texMini }:
    nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-darwin" "x86_64-darwin" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # CSF metadata processor
        csfMetadataProcessor = pkgs.writeShellApplication {
          name = "csf-metadata-processor";
          runtimeInputs = with pkgs; [ python3 jq ];
          text = ''
            ${builtins.readFile ./scripts/process-metadata.py}
          '';
        };

        # CSF-enhanced LaTeX compiler
        cstexCompile = pkgs.writeShellApplication {
          name = "cstex-compile";
          runtimeInputs = with pkgs; [ 
            texMini.packages.${system}.default
            csfMetadataProcessor
            git
          ];
          text = ''
            # Pre-process document to inject CSF metadata
            csf-metadata-processor "$1" > "/tmp/csf-enhanced-$(basename "$1")"
            
            # Compile with texMini
            ${texMini.packages.${system}.default}/bin/texmini "/tmp/csf-enhanced-$(basename "$1")"
          '';
        };

        # Live preview with embedded provenance
        cstexPreview = pkgs.writeShellApplication {
          name = "cstex-preview";
          runtimeInputs = with pkgs; [ 
            cstexCompile
            entr  # File watcher
            python3
          ];
          text = ''
            ${builtins.readFile ./scripts/live-preview.sh}
          '';
        };

      in {
        packages = {
          compile = cstexCompile;
          preview = cstexPreview;
          metadata-extract = csfMetadataProcessor;
          default = cstexCompile;
        };
      });
}
```

#### 2.2.3 Intelligent Command Interface

```bash
# Automatic compilation with CSF linking
nix run github:composable-science/cstex#compile -- paper.tex

# Live preview with real-time provenance updates
nix run github:composable-science/cstex#preview -- paper.tex

# Extract metadata only (for debugging)
nix run github:composable-science/cstex#metadata-extract -- paper.tex

# Compile specific figure with metadata
nix run github:composable-science/cstex#compile -- --figure figures/plot.png paper.tex
```

#### 2.2.3 CSF LaTeX Package Integration

The `composable.sty` package is automatically available in the CSTeX environment:

```latex
\usepackage{composable}

% Enhanced figure inclusion with CSF linking
\csfigure{figures/histogram.png}{
  caption={Distribution of measurements},
  label={fig:histogram},
  step={figures},                    % Pipeline step that generated this
  script={scripts/make_figures.py},  % Source script
  line={42}                          % Line number where figure is saved
}
```

#### 2.2.4 Metadata Injection and URL Generation

The `\csfigure` command generates enhanced LaTeX with embedded provenance:

```latex
% Expanded output
\begin{figure}[htbp]
  \centering
  \includegraphics{figures/histogram.png}
  \caption{Distribution of measurements 
    \href{https://dashboard.example.com/project/abc123/artifact/histogram.png}{
      \textcolor{blue}{[🔗 View computational provenance]}
    }}
  \label{fig:histogram}
  
  % Invisible metadata for tools
  \CSFMetadata{
    artifact=figures/histogram.png,
    step=figures,
    script=scripts/make_figures.py,
    line=42,
    hash=sha256:a1b2c3d4...,
    project_id=abc123
  }
\end{figure}
```

#### 2.2.3 Dashboard URL Generation

**URL Structure:**
```
https://{dashboard_host}/project/{project_id}/artifact/{artifact_path}
# Example:
https://dashboard.composable-science.org/project/abc123/artifact/figures/histogram.png
```

**Dashboard Artifact Page Features:**
- Full pipeline context for the specific artifact
- Source code viewer showing the exact lines that generated it
- Dependency tree showing all inputs that contributed
- Attestation verification status
- Download links for reproduction

### 2.3 Implementation Strategy

#### 2.3.1 LaTeX Package Implementation

```latex
% composable.sty
\ProvidesPackage{composable}[2025/07/01 Composable Science Framework]

\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{url}
\RequirePackage{hyperref}

% Read project configuration
\newread\csfconfig
\openin\csfconfig=.csf/config.tex
\input{.csf/config.tex}
\closein\csfconfig

% Enhanced figure command
\newcommand{\csfigure}[2]{%
  \begin{figure}[htbp]
    \centering
    \includegraphics{#1}
    \caption{#2[caption] \csflink{#1}{#2}}
    \label{#2[label]}
  \end{figure}
}

% Generate dashboard link
\newcommand{\csflink}[2]{%
  \href{\csfbaseurl/project/\csfprojectid/artifact/#1}{%
    \textcolor{blue}{\small [🔗 Computational provenance]}
  }
}
```

#### 2.3.2 CSF CLI Integration

Enhance `cs build` to generate LaTeX configuration:

```bash
cs build paper  # Automatically generates .csf/config.tex
```

Generated configuration:
```latex
% .csf/config.tex (auto-generated)
\def\csfprojectid{abc123}
\def\csfbaseurl{https://dashboard.composable-science.org}
\def\csfcommit{git-sha-hash}
```

#### 2.3.3 Dashboard Artifact Pages

Extend the frontend dashboard with artifact-specific routes:

```typescript
// New route: /project/[id]/artifact/[...path]
export default function ArtifactPage({ params }: {
  params: { id: string; path: string[] }
}) {
  const artifactPath = params.path.join('/');
  
  return (
    <div className="artifact-detail">
      <ArtifactHeader path={artifactPath} />
      <EnhancedPipelineView focusedArtifact={artifactPath} />
      <SourceCodeViewer artifact={artifactPath} />
      <AttestationVerification artifact={artifactPath} />
    </div>
  );
}
```

---

## 3 · Technical Implementation Plan

### 3.1 Phase 1: Nix Flakes Infrastructure (Weeks 1-2)

**Week 1: Core Repository Setup**
- Create `github:composable-science/cli` repository with flake structure
- Implement `#dashboard` and `#legacy-dashboard` outputs
- Create `github:composable-science/cstex` repository
- Port existing dashboard generation to Nix-based scripts

**Week 2: CSTeX Integration** 
- Implement `#compile` and `#preview` outputs for CSTeX
- Integrate texMini for minimal LaTeX environment
- Create enhanced `composable.sty` package
- Test compilation pipeline with CSF linking

### 3.2 Phase 2: Enhanced Dashboard (Weeks 3-4)

**Week 3: Multi-Pane Interface**
- Implement enhanced dashboard HTML/CSS/JS generation
- Create interactive Mermaid integration with clickable nodes
- Build file explorer tree component
- Add visual artifact classification system

**Week 4: Content Viewer & Integration**
- Implement syntax-highlighted code viewer
- Add image preview and metadata display
- Integrate attestation wildcard resolution
- Test with existing projects using new Nix commands

### 3.3 Phase 3: Document Linking (Weeks 5-6)

**Week 5: LaTeX Enhancement**
- Finalize `\csfigure` command implementation
- Create automatic project ID generation from git context
- Implement dashboard URL generation in LaTeX compilation
- Test CSF metadata embedding

**Week 6: Frontend Dashboard Extensions**
- Add artifact-specific routes to web dashboard
- Implement artifact detail pages with source code integration
- Create provenance link resolution
- End-to-end testing of document → dashboard workflow

### 3.4 Repository Structure

#### 3.4.1 `github:composable-science/cli`

```
cli/
├── flake.nix                    # Main flake definition
├── scripts/
│   ├── generate-dashboard.sh    # Enhanced dashboard generator
│   ├── generate-legacy.sh       # Legacy dashboard (compatibility)
│   └── validate-env.sh          # Environment validation
├── templates/
│   ├── dashboard.html           # Enhanced dashboard template
│   ├── dashboard.css            # Dashboard styling
│   └── dashboard.js             # Interactive functionality
└── lib/
    ├── parse-toml.py            # TOML parsing utilities
    ├── file-tree.py             # Directory scanning
    └── attestation.py           # Attestation handling
```

#### 3.4.2 `github:composable-science/cstex`

```
cstex/
├── flake.nix                    # LaTeX compilation flake
├── scripts/
│   ├── compile-with-csf.sh      # CSF-enhanced compilation
│   └── preview-with-csf.sh      # Live preview with provenance
├── latex/
│   ├── composable.sty           # CSF LaTeX package
│   └── templates/               # Document templates
└── lib/
    ├── project-id.py            # Project ID generation
    ├── git-metadata.py          # Git context extraction
    └── url-generation.py        # Dashboard URL creation
```

#### 3.4.3 `github:composable-science/templates`

```
templates/
├── flake.nix                    # Template initialization flake
├── paper-latex/
│   ├── paper.tex                # Enhanced LaTeX template
│   ├── composable.toml          # Pipeline configuration
│   └── scripts/                 # Sample analysis scripts
├── basic-lab/
│   └── ...                      # Minimal research template
└── dataset-pipeline/
    └── ...                      # Data processing template
```

### 3.5 Command Integration

#### 3.5.1 Unified Workflow

Users interact with CSF through consistent Nix commands:

```bash
# 1. Initialize project
nix run github:composable-science/templates#paper-latex

# 2. Run analysis pipeline
nix develop  # Enter development environment
python scripts/make_figures.py

# 3. Generate dashboard
nix run github:composable-science/cli#dashboard

# 4. Compile paper with CSF linking
nix run github:composable-science/cstex#compile -- paper.tex

# 5. Attest and verify
nix run github:composable-science/cli#attest -- figures
```

#### 3.5.2 Backward Compatibility

Existing `cs` commands map to Nix flake equivalents:

```bash
# Legacy → Nix Flake → Expected Behavior
cs dashboard  →  nix run github:composable-science/cli#dashboard
cs build      →  nix develop -c make  # or custom build command
cs attest     →  nix run github:composable-science/cli#attest
```

### 3.6 Testing Strategy

**Enhanced Dashboard Testing:**
- Test Nix flake execution across Linux/macOS
- Verify dashboard generation with sample projects
- Test multi-pane interface interaction and file content viewing

**CSTeX Integration Testing:**
- Validate LaTeX compilation with CSF linking
- Test figure provenance link generation
- Verify PDF output with embedded metadata

**End-to-End Workflow Testing:**
- Create sample project using templates
- Generate figures and compile paper
- Test dashboard → document linking flow

### 3.1 Phase 1: Enhanced Dashboard (Weeks 1-3)

**Week 1: Backend Infrastructure**
- Extend `cs dashboard` command to generate enhanced HTML
- Create file tree scanning and metadata collection
- Implement content serving for text files and directories

**Week 2: Frontend Development**  
- Implement multi-pane dashboard layout
- Create interactive Mermaid integration
- Build file explorer tree component

**Week 3: Integration & Testing**
- Add visual artifact classification
- Implement attestation wildcard resolution
- Test with existing `paper-latex` template

### 3.2 Phase 2: Document Linking (Weeks 4-6)

**Week 4: LaTeX Package**
- Develop `composable.sty` package
- Implement `\csfigure` command
- Create URL generation logic

**Week 5: Dashboard Extensions**
- Add artifact-specific routes to frontend
- Implement artifact detail pages
- Create source code integration

**Week 6: Template Integration**
- Update `paper-latex` template
- Test end-to-end workflow
- Documentation and examples

---

## 4 · User Experience Flow

### 4.1 Enhanced Dashboard Experience

1. **Researcher runs** `cs dashboard` in project directory
2. **Enhanced dashboard opens** with three-pane interface
3. **Click on "figures" step** in pipeline → Explorer shows `figures/` directory
4. **Click on `histogram.png`** → Content viewer shows image preview + metadata
5. **Click on "scripts" step** → Explorer shows script files
6. **Click on `make_figures.py`** → Content viewer shows syntax-highlighted code

### 4.2 Document Linking Experience

1. **Researcher writes LaTeX** using `\csfigure{figures/plot.png}{...}`
2. **Runs** `cs build paper` → Generates PDF with embedded CSF links
3. **Reader clicks provenance link** → Opens dashboard artifact page
4. **Dashboard shows** complete computational context for that specific figure
5. **Reader can verify** the exact code and data that produced the figure

---

## 5 · Success Metrics

### 5.1 Enhanced Dashboard

- **Engagement**: Users spend >2x longer in enhanced dashboard vs. static version
- **Discovery**: >50% of users explore file contents via Content Viewer  
- **Workflow**: Reduced time to understand project structure by >40%

### 5.2 Document Linking

- **Adoption**: >30% of LaTeX figures use `\csfigure` in new projects
- **Transparency**: >80% of embedded CSF links successfully resolve
- **Impact**: Measurable increase in computational reproducibility verification

---

## 6 · Test Requirements & Validation

### 6.1 Template Generation Tests

#### 6.1.1 LaTeX Template Compliance

**Requirement**: The `cs init paper-latex` command must generate a LaTeX file that conforms to the new CSF paradigm as specified in this document.

**Test Criteria**:

1. **Standard LaTeX Structure**: Generated `paper.tex` must use standard LaTeX commands without manual CSF metadata injection
2. **Zero-Configuration Provenance**: LaTeX should contain no explicit `\csfigure` or similar commands - provenance linking is handled automatically by `cstex`
3. **Comments Indicating Auto-Injection**: LaTeX file should include comments explaining that provenance is automatically injected by the CSF toolchain
4. **Template Consistency**: Generated LaTeX must match the structure and approach demonstrated in `core/test/paper/paper.tex`

**Example Expected Output**:
```latex
\documentclass{article}
\usepackage{graphicx}
\usepackage{composable}  % CSF package for automatic provenance

\title{Sample Research Paper}
\author{Research Team}
\date{\today}

\begin{document}
\maketitle

% Figures are automatically linked to their computational provenance
% by the cstex toolchain - no manual metadata required
\begin{figure}[h]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/measurement_distribution.png}
    \caption{Distribution of temperature measurements across all sensors.}
    \label{fig:measurement_distribution}
\end{figure}

% The CSF framework automatically:
% 1. Detects referenced artifacts (figures, data files)
% 2. Links them to pipeline steps in composable.toml
% 3. Injects interactive provenance links in the compiled PDF
\end{document}
```

#### 6.1.2 Flake Integration Test

**Requirement**: Generated project must use Nix flakes for all operations.

**Test Criteria**:
1. `composable.toml` includes `flake` fields for all pipeline steps
2. Dashboard generation uses `nix run github:composable-science/cli#dashboard`
3. LaTeX compilation uses `nix run github:composable-science/cstex#compile`
4. All dependencies are declaratively specified in the flake

### 6.2 Dashboard Functionality Tests

#### 6.2.1 Interactive Dashboard

**Test Cases**:
1. **Three-Pane Interface**: Dashboard loads with Pipeline View, File Explorer, and Content Viewer
2. **Pipeline Navigation**: Clicking pipeline steps updates File Explorer
3. **File Preview**: Clicking files shows content in Content Viewer
4. **Artifact Classification**: Different file types show appropriate icons and metadata

#### 6.2.2 Provenance Linking

**Test Cases**:
1. **Automatic Detection**: `cstex` automatically detects figure references in LaTeX
2. **Link Generation**: Compiled PDF contains clickable provenance links
3. **Dashboard Integration**: Links open correct artifact pages in dashboard
4. **Cross-Reference Validation**: All linked artifacts exist and are accessible

### 6.3 Nix Flakes Integration Tests

#### 6.3.1 Command Equivalence

**Test Matrix**:
```bash
# Legacy → Nix Flake → Expected Behavior
cs dashboard  →  nix run github:composable-science/cli#dashboard  →  Enhanced dashboard opens
cs build      →  nix develop -c make                               →  Pipeline executes
cs attest     →  nix run github:composable-science/cli#attest      →  Cryptographic attestation
cs init       →  nix run github:composable-science/templates#*    →  Project initialized
```

#### 6.3.2 Reproducibility Tests

**Requirements**:
1. **Deterministic Builds**: Same inputs produce identical outputs across systems
2. **Dependency Isolation**: No reliance on system-installed packages
3. **Version Pinning**: All dependencies locked to specific versions
4. **Cross-Platform**: Works on macOS, Linux, and NixOS

### 6.4 End-to-End Workflow Tests

#### 6.4.1 Complete Research Pipeline

**Test Scenario**: New researcher uses CSF from project creation to paper publication

**Steps**:
1. Initialize project: `cs init paper-latex`
2. Verify generated files match specification requirements
3. Add computational pipeline to `composable.toml`
4. Run analysis: `nix develop -c python scripts/make_figures.py`
5. Generate dashboard: `nix run github:composable-science/cli#dashboard`
6. Compile paper: `nix run github:composable-science/cstex#compile -- paper.tex`
7. Verify provenance links work in resulting PDF
8. Attest results: `nix run github:composable-science/cli#attest`

**Success Criteria**:
- All commands execute without error
- Generated LaTeX follows new paradigm (no manual CSF commands)
- Dashboard shows interactive three-pane interface
- PDF contains functional provenance links
- Attestation validates computational integrity

#### 6.4.2 Legacy Migration Test

**Test Scenario**: Existing CSF project migrates to new Nix flakes paradigm

**Steps**:
1. Start with project using old `cs` commands
2. Update `composable.toml` to include flake fields
3. Replace manual CSF LaTeX commands with standard LaTeX
4. Verify all functionality preserved with new toolchain

### 6.5 Performance & Usability Tests

#### 6.5.1 Dashboard Performance

**Metrics**:
- Dashboard load time: <3 seconds for typical project
- File explorer responsiveness: <500ms for directory changes
- Content viewer loading: <1 second for files <10MB

#### 6.5.2 Compilation Performance

**Metrics**:
- LaTeX compilation with cstex: <2x overhead vs. standard LaTeX
- Provenance link injection: <10% additional compilation time
- Dashboard generation: <30 seconds for projects with <100 artifacts

### 6.6 Validation Checklist

**Pre-Release Requirements**:

- [ ] `cs init paper-latex` generates LaTeX matching new paradigm
- [ ] Generated `composable.toml` uses flake-based commands
- [ ] Enhanced dashboard displays three-pane interface
- [ ] `cstex` automatically injects provenance without manual LaTeX commands
- [ ] All Nix flake commands execute reproducibly
- [ ] Legacy `cs` commands map correctly to flake equivalents
- [ ] End-to-end workflow completes without errors
- [ ] Performance metrics meet specified thresholds
- [ ] Cross-platform compatibility verified (macOS, Linux, NixOS)
- [ ] Documentation updated to reflect new paradigm

---

*This specification aligns with Composable Science Framework v0.0.1 as defined in SPEC.md and extends the dashboard (§12) and template (§11) specifications.*
