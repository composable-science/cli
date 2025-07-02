# CSF Enhanced Integration Paradigm Summary

*Version: 2025-07-01*

> **Summary**: The Composable Science Framework now implements intelligent document integration through Nix flakes, enabling zero-configuration computational transparency.

---

## Key Paradigm Shifts

### 1. From Manual to Automatic Metadata

**Before** (Manual specification):
```latex
\csfigure{figures/histogram.png}{
  caption={Distribution of measurements},
  step={figures},
  script={scripts/make_figures.py},
  line={42}
}
```

**After** (Automatic discovery):
```latex
\includegraphics{figures/histogram.png}
\caption{Distribution of measurements}
```

The `cstex` compiler automatically discovers provenance without user intervention.

### 2. From Local CLI to Distributed Flakes

**Before** (Local installation):
```bash
cs dashboard
cs build paper
```

**After** (Nix flakes):
```bash
nix run .#cs -- dashboard
nix run .#cstex-compile -- paper.tex
```

No local installation required - reproducible execution from GitHub.

### 3. From Format-Specific to Cross-Platform

**Current** (LaTeX):
```bash
nix run .#cstex-compile -- paper.tex
```

**Future** (Multiple formats):
```bash
nix run github:composable-science/csmd#compile -- report.md
nix run github:composable-science/csdocx#process -- report.docx
nix run github:composable-science/csjupyter#render -- analysis.ipynb
```

---

## Architecture Overview

### Core Repositories

- **`./cli`** - Flake for the main CSF command-line tools.
  - `cs dashboard`
  - `cs attest`
- **`./compile`** - Flake for the CSTeX compilation toolchain.
  - `cstex-compile`

- **`github:composable-science/templates`** - Project templates
  - `#paper-latex` - Academic paper with zero-config CSF
  - `#basic-lab` - Minimal research pipeline

### Intelligent Processing Pipeline

1. **Pipeline Analysis**: Parse `composable.toml` to understand artifact dependencies
2. **Document Scanning**: Find computational artifacts in LaTeX source
3. **Metadata Extraction**: Map artifacts to pipeline steps and source code
4. **Link Injection**: Automatically embed provenance links in compiled document
5. **Dashboard Generation**: Create interactive exploration interface

---

## User Experience

### For Document Authors

1. Write standard LaTeX with no CSF-specific syntax
2. Compile with `nix run github:composable-science/cstex#compile -- paper.tex`
3. Get automatic provenance linking for all computational artifacts
4. View live preview with embedded dashboard links

### For Document Readers

1. Click any figure to see its computational context
2. Navigate to dashboard for full pipeline visualization
3. Verify cryptographic attestations inline
4. Download reproduction scripts with one click

---

## Implementation Status

### Completed
- ✅ Enhanced dashboard specification
- ✅ Nix flakes architecture design
- ✅ Automatic metadata processing design
- ✅ Cross-format extensibility framework

### Next Steps
1. Implement `cstex` metadata processor
2. Create `github:composable-science/cstex` flake
3. Build enhanced dashboard as `github:composable-science/cli#dashboard`
4. Test end-to-end workflow with paper template
5. Extend to Markdown (`csmd`) and other formats

---

## Benefits

### Technical
- **Zero-configuration**: No manual metadata specification required
- **Reproducible**: Nix flakes ensure consistent execution environments
- **Distributed**: No local installation dependencies
- **Cross-platform**: Architecture generalizes to multiple document formats

### Research Workflow
- **Seamless transparency**: Computational provenance embedded automatically
- **Interactive exploration**: Enhanced dashboard for understanding pipelines
- **Verification**: Cryptographic attestations linked to every artifact
- **Collaboration**: Shared flakes ensure reproducible environments

---

*This paradigm represents a fundamental shift toward intelligent computational transparency in scientific communication.*
