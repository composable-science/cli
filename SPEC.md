# Composable Science Framework – **Specification v0.0.1**

*(July 2025)*

> **Status:** Initial public draft. Defines the foundational pipeline‑step model, manifest schema, CLI surface, provenance workflow, and dashboard with built‑in Mermaid diagrams.

---

## 0 · Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Glossary](#2-glossary)
3. [Command‑Line Interface (`cs`)](#3-command‑line-interface-cs)
4. [Project Layout](#4-project-layout)
5. [`composable.toml` Format](#5-composabletoml-format)
6. [Pipeline Execution](#6-pipeline-execution)
7. [Attestations](#7-attestations)
8. [Identity & Signing](#8-identity--signing)
9. [Ledger & Provenance Storage](#9-ledger--provenance-storage)
10. [CI / Canary Policies](#10-ci--canary-policies)
11. [Starter Templates](#11-starter-templates)
12. [Dashboard & Mermaid Diagrams](#12-dashboard--mermaid-diagrams)
13. [Public API](#13-public-api)
14. [Error‑Code Catalogue](#14-error‑code-catalogue)
15. [Security Considerations](#15-security-considerations)
16. [Versioning](#16-versioning)
17. [Acknowledgements](#17-acknowledgements)

---

## 1 · Purpose & Scope

The **Composable Science Framework (CSF)** standardises how computational research pipelines are **declared, executed, verified, and shared**. It ships as a CLI (`cs`), a manifest format (`composable.toml`), a cryptographic attestation workflow, and a public ledger for provenance.

---

## 2 · Glossary

| Term              | Meaning                                                           |
| ----------------- | ----------------------------------------------------------------- |
| **Pipeline**      | Ordered list of build **steps**.                                  |
| **Pipeline Step** | One build action: consumes *inputs* and produces *outputs*.       |
| **Attestation**   | Signed JSON binding an artifact hash to its build context.        |
| **DID**           | *Decentralised Identifier*; default method `did:key`.             |
| **Ledger**        | Append‑only, cryptographically‑verifiable provenance database.    |
| **NAR**           | *Nix ARchive* storing build outputs reproducibly.                 |
| **Mermaid**       | Text syntax for graphs; used to visualise pipelines in dashboard. |

---

## 3 · Command‑Line Interface (`cs`)

### 3.1 Invocation

```bash
cs <command> [options] [args]
# or via Nix
nix run github:composable-science/cli -- cs <command> ...
```

### 3.2 Commands

| Command            | Purpose                                                 |
| ------------------ | ------------------------------------------------------- |
| `init <template>`  | Create a new project from a starter template            |
| `build [<step>]`   | Build entire pipeline or a single named step            |
| `diagram`          | Render a Mermaid diagram (`pipeline.mmd`) without HTML  |
| `dashboard [opts]` | Generate HTML dashboard **with Mermaid diagram**        |
| `attest <step>`    | Create & sign attestation for the specified step        |
| `doctor`           | Diagnose environment & config                           |
| `id <subcmd>`      | DID management (`create`, `status`, `rotate`, `revoke`) |

`--json` flag produces machine‑readable output for all commands.

---

## 4 · Project Layout

```
repo/
├── composable.toml    # Manifest (see §5)
├── flake.nix          # Dev & CI environment
├── outputs/           # Build artifacts (git‑ignored)
├── scripts/           # Helper scripts (optional)
└── docs/              # Additional documentation (optional)
```

---

## 5 · `composable.toml` Format

### 5.1 Requirements

* TOML v1.0.0, UTF‑8.
* Exactly one `[package]` table.
* One or more **ordered** `[[pipeline]]` tables.
* Optional `[build]` and `[attestation]` tables.

### 5.2 Top‑level Tables

| Table           | Required | Purpose                               |
| --------------- | -------- | ------------------------------------- |
| `[package]`     | ✔︎       | Project metadata                      |
| `[build]`       |          | Global build & UX settings            |
| `[[pipeline]]`  | ✔︎ (≥1)  | Ordered pipeline steps                |
| `[attestation]` |          | File‑selection rules for attestations |

> **Note:** Projects using Nix for reproducible environments should define a `[build.env]` table. See below for the format.

### 5.2.1 Nix Environment Table (`[build.env]`)

#### 5.2.1 Nix Environment Table (`[build.env]`)

Projects that require a reproducible Nix environment MUST declare the reference packages under a `[build.env]` table.

| Field      | Type            | Required | Notes                                                                 |
| ---------- | --------------- | -------- | --------------------------------------------------------------------- |
| `kind`     | string          | ✔︎       | Must be `"nix"` for Nix-based envs                                    |
| `packages` | array\<string\> | ✔︎       | Ordered list of Nixpkgs attribute names (e.g. `"python311"`, `"texMiniDefault"`, `"python311Packages.numpy"`) |

The first package providing a `python` binary determines the default interpreter for human-readable commands (e.g., `python script.py`). No shell variables or wrappers are required if the environment provides the executable on `$PATH`.

Example:

```toml
[build.env]
kind     = "nix"
packages = [
  "python311",
  "texMiniDefault",  # from github:alexmill/texMini
  "graphviz",
  "python311Packages.numpy",
  "python311Packages.pandas",
  "python311Packages.matplotlib",
  "python311Packages.seaborn",
  "python311Packages.jupyterlab"
]
```

### 5.3 `[[pipeline]]` Step Table

| Field     | Type          | Required | Notes                                             |
| --------- | ------------- | -------- | ------------------------------------------------- |
| `name`    | string        | ✔︎       | Unique, 1‑32 chars, regex `^[a-zA-Z0-9_\-]+$`     |
| `cmd`     | string        | ✔︎       | Shell command to execute. The command is executed in the context of the reference environment as defined by `[build.env]` (if present). The default Nix shell must provide all required binaries (e.g., `python`) on `$PATH` for human-readable commands. |
| `inputs`  | array<string> | ✔︎       | File globs evaluated **before** step runs         |
| `outputs` | array<string> | ✔︎       | Declared outputs; must be unique across all steps |
| `env`     | table         |          | Additional environment variables                  |

### 5.4 Validation Rules

1. All `name` values must be unique (case‑insensitive).
2. Every `inputs` glob must match at least one file present at step runtime.
3. No two steps may declare overlapping `outputs`.
4. At least one `[[pipeline]]` step must exist.

### 5.5 Example Manifest

```toml
[package]
name    = "org.example.paper"
version = "0.0.1"
license = "MIT"
authors = ["Alice Example <alice@example.org>"]

[build]
open_dashboard = true      # auto‑open HTML dashboard in browser

[build.env]
kind     = "nix"
packages = [
  "python311",
  "texMiniDefault",  # ultra-lean LaTeX via alexmill/texMini
  "graphviz",
  "python311Packages.numpy",
  "python311Packages.pandas",
  "python311Packages.matplotlib",
  "python311Packages.seaborn",
  "python311Packages.jupyterlab"
]

[[pipeline]]
name    = "figures"
cmd     = "python scripts/make_figures.py"
inputs  = ["data/raw/*.csv", "scripts/make_figures.py"]
outputs = ["figures/*.png"]

[[pipeline]]
name    = "paper"
cmd     = "latexmk -pdf paper.tex"
inputs  = ["paper.tex", "figures/*.png"]
outputs = ["paper.pdf"]

[attestation]
include = ["paper.pdf", "figures/*.png"]
exclude = ["drafts/*"]
```

---

## 6 · Pipeline Execution

1. **Order** — Steps run strictly in file order.
2. **Selective Build** — `cs build <name>` builds that step plus any stale predecessors.
3. **Staleness** — Step is stale if any input’s mtime > any output’s mtime.
4. **Parallelism** — Implementation MAY parallelise independent steps.
5. **Exit Codes**

   * 65 — stale outputs
   * 66 — build failure
   * 69 — pipeline order violation (missing input)

---

## 7 · Attestations

### 7.1 Schema (JSON Schema 2020‑12)

*(truncated here for brevity in spec; full schema identical to reference implementation)*

### 7.2 Workflow

1. Run `cs attest <step>` after successful build.
2. CLI computes SHA‑256 of NAR output, gathers metadata, canonicalises JSON.
3. CLI signs JSON with builder’s DID key and writes `attestation.json`.
4. Optionally opens a PR to the ledger repository.

---

## 8 · Identity & Signing

* Default key type: Ed25519 via `did:key`.
* Keys stored in OS keyring; fallback encrypted file.
* Commands: `cs id create | status | rotate | revoke`.

---

## 9 · Ledger & Provenance Storage

* Single source‑of‑truth SQLite ledger (**append‑only**).
* Each attestation row stores: artifact hash, builder DID, timestamp, Sigstore OCI ref.
* A GitHub bot verifies builds & merges attestation PRs.

---

## 10 · CI / Canary Policies

* **Pull request**: run full pipeline, validate attestation, signature, and schema.
* **Merge**: ledger bot re‑builds step, updates ledger.
* **Nightly canary**: rebuild 5 % random artifacts; open issue on mismatch.

---

## 11 · Starter Templates

| Template           | Audience               | Description                                 |
| ------------------ | ---------------------- | ------------------------------------------- |
| `basic‑lab`        | Solo researchers       | Minimal 2‑step pipeline, README quick‑start |
| `paper‑latex`      | Traditional publishing | Figures + PDF build                         |
| `dataset‑pipeline` | Data wrangling         | Download, clean, analyse dataset            |
| `software‑package` | CLI/library release    | Build binary + docs, attest tarball         |

All templates ship with a pre‑rendered Mermaid diagram in `docs/`.

---

## 12 · Dashboard & Mermaid Diagrams

* `cs dashboard` renders **`dashboard/index.html`** comprising:

  * Mermaid flowchart of pipeline (auto‑generated from `[[pipeline]]` order).
  * Live status badges per step (up‑to‑date / stale / failed).
  * Links to build logs and attestations.
* `cs diagram` outputs raw Mermaid syntax (`pipeline.mmd`) for integration into other docs or papers.
* `[build].open_dashboard = true/false` toggles auto‑open behaviour.

---

## 13 · Public API

| Method                            | Path                                  | Returns                     |
| --------------------------------- | ------------------------------------- | --------------------------- |
| GET                               | `/api/v1/artifact/{hash}`             | Artifact metadata           |
| GET                               | `/api/v1/artifact/{hash}/attestation` | Raw attestation JSON        |
| GET                               | `/api/v1/search?q=<term>`             | Array of matching artifacts |
| All responses `application/json`. |                                       |                             |

---

## 14 · Error‑Code Catalogue

| Code | Meaning                                  | Remedy                       |
| ---- | ---------------------------------------- | ---------------------------- |
| E01  | Secret key not found                     | `cs id create`               |
| E02  | Signature expired                        | `cs id rotate`               |
| E03  | Hash mismatch                            | Rebuild step                 |
| E04  | Schema invalid                           | `cs validate`                |
| E64  | Step not found                           | Fix name in manifest         |
| E65  | Stale outputs                            | Re‑run `cs build`            |
| E66  | Build failure                            | Check logs                   |
| E67  | Signing error                            | Check key permissions        |
| E68  | DID missing                              | `cs id create`               |
| E69  | Pipeline order violation (missing input) | Fix manifest order or inputs |

---

## 15 · Security Considerations

* Builds run in clean, immutable Nix sandboxes.
* Attestations require DID signatures.
* Ledger commits protected by branch rules; any tampering is detectable.

---

## 16 · Versioning

* **0.y.z** indicates *initial development*; breaking changes may occur until v1.0.0.
* Semantic versioning applies after v1.0.0.

---

## 17 · Acknowledgements

Inspired by Nix, Sigstore, Cargo, and the ReScience community.

---

*End of Specification v0.0.1.*
