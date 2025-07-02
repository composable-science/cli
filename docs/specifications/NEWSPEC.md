# **Product Vision: Composable Science**

**Composable Science** is an open-source platform for creating a trustworthy, public record of scientific knowledge. It achieves this through two tightly integrated components:

1.  A **local-first framework** (`cs` tool) for authoring **verifiable papers**, where every artifact—from a single figure to the final manuscript—is produced by a reproducible, Nix-powered pipeline.
2.  A **decentralized protocol and public ledger** for submitting, verifying, and connecting these results into a global, explorable knowledge graph.

The platform's core axiom is that **verifiable claims require a verifiable process.** The `cs` command-line tool provides the means for individual researchers to build their work reproducibly, while the public ledger provides the social and technical infrastructure to make those results a permanent, citable, and machine-actionable part of the scientific record.

---

### **Core User Journey**

1.  **Local Development (The Lab Notebook):** A researcher uses `cs init` to bootstrap a new project. They define their entire workflow—data, code, computational environments, and manuscript—in a single `composable.toml` file. They use `cs <target>` to build artifacts and `cs dashboard` to visualize and understand their local project's dependency graph. This is their private, perfectly reproducible workspace.
2.  **Public Attestation (The Publication):** Once their paper is complete, they run `cs attest paper`. This command:
    *   Builds the final `paper.pdf` and all its dependencies to ensure they are up-to-date.
    *   Bundles the `composable.toml` blueprint, the resulting artifacts, and their Nix store paths into a structured package.
    *   Cryptographically signs this package using the researcher's decentralized identity (`did:key`).
    *   Submits the signed attestation as a pull request to the public `composable-science/submissions` repository.
3.  **Global Verification & Discovery (The Library):** The platform's automated `Ledger Maintainer Bot` validates the submission, runs the verification process, and merges it into the canonical ledger. The new result is now part of the global knowledge graph, discoverable via a public API and explorable through web-based visualizers. Other researchers can not only cite the work but also download the attestation and perfectly reproduce the result using the same `cs` tool.

---

### **Tech Stack**

*   **Core Technology:** **Nix** (for universal reproducibility), **Git** (for versioning), **TOML** (for configuration), **Python 3.11+**, **Shell Scripting**.
*   **Unified Client Application (`cs`):** A Python application (`typer`, `toma`) that handles both local project management and public attestation submission.
*   **Backend Services:** A **FastAPI** server providing a public API over the ledger, and a trusted Python bot for ledger maintenance.
*   **Data & State:**
    *   **Local:** A `composable.toml` file per project.
    *   **Global:** A central `composable-science/core` Git repository acting as the source of truth, compiled into a single, distributable **SQLite** database artifact.
*   **Visualization:** **Mermaid.js** for the interactive local dashboard. The public API will provide structured JSON to power more advanced external visualizers.
*   **Distribution:**
    *   **Tooling:** All client tools (`cs`) are distributed via a single Nix Flake at `github:composable-science/tools`.
    *   **Artifacts:** A public Nix binary cache (e.g., Cachix) is used for efficient distribution of verified computational results.

---

### **Functional Requirements**

**Local Framework (`cs` tool):**
*   **Declarative Blueprint (`composable.toml`):** Defines `[[artifact]]`s, `[[process]]`es, `[environments]`, and `[sweep]`s for parameter sweeps.
*   **Unified CLI (`cs`):**
    *   `cs init`: Bootstraps new projects from templates.
    *   `cs <target>`: Builds any artifact by executing its dependency chain.
    *   `cs dashboard`: Generates a local, interactive Mermaid.js graph of the project.
    *   `cs sweep`: Executes declarative parameter sweeps.
    *   **`cs attest <target>`:** The bridge command. It builds the target, generates a signed attestation package, and submits it to the public ledger.
    *   **`cs id <subcommand>`:** An integrated identity manager for creating and managing the user's `did:key`.

**Public Platform (Backend & Protocol):**
*   **Attestation Protocol:** Defines the structure of signed attestations, supporting both `verifiable` (machine-checkable Nix builds) and `qualitative` (e.g., peer reviews, claims on private data) types.
*   **Public Submission Inbox:** A `composable-science/submissions` Git repository receives attestations via pull requests.
*   **Automated Ledger Maintenance:** A trusted bot validates, batches, and commits submissions to the canonical `composable-science/core` ledger repository.
*   **Verifiable Ledger Artifact:** The entire ledger is built via Nix into a single, reproducible SQLite database.
*   **Public API:** A versioned, public API (e.g., `/api/v1/artifact/{hash}/dependencies`) to query the knowledge graph.

---

### **Non-functional Requirements**

*   **Axiom of Provenance & Verifiability:** The local tool enforces that every artifact has a pipeline, and the public platform ensures `verifiable` attestations are machine-checkable.
*   **Zero Host Dependencies:** A user needs only Nix installed to both create *and* verify any artifact on the platform.
*   **Declarative & Visual-First:** The user experience is centered on the `composable.toml` blueprint and the visual dependency graphs (both local and global).
*   **Security & Identity:** All contributions to the public ledger are cryptographically signed with decentralized identities.
*   **Portability & Efficiency:** Projects are self-contained, and the public binary cache prevents redundant computation and downloads across the network.

---

### **Acceptance Test**

*   **Scenario: Full end-to-end lifecycle from research to publication**
    1.  **Given** a researcher is in an empty directory.
    2.  **When** they run `cs init -t latex-python`.
    3.  **Then** the directory is populated with a `composable.toml` and project template.
    4.  **And** they run `cs id create` to generate a new keypair.
    5.  **When** they run `cs paper`.
    6.  **Then** the `cs` tool builds the entire dependency graph and produces a `paper.pdf`.
    7.  **When** they run `cs attest paper`.
    8.  **Then** the tool signs a bundle containing the `paper.pdf`'s provenance and submits it as a PR to the `composable-science/submissions` repository.
    9.  **And** after the platform's bot merges the submission...
    10. **When** an external client queries `GET /api/v1/artifact/{paper_hash}`.
    11. **Then** the API returns a JSON object containing the paper's metadata, its creator's DID, and a list of its verifiable dependencies.

---

### **File Map**

```
# Public Infrastructure Repositories
/composable-science-core/       # The canonical ledger
|-- flake.nix                   # Builds the SQLite ledger artifact
|-- ledger/
|   `-- attestations/
`-- ... (protocol docs, verifier scripts)

/composable-science-submissions/ # Public inbox for new attestations (mostly PRs)

/services-and-bots/             # Private repo for backend service code
|-- api-server/
`-- ledger-bot/

# The Unified Tooling Repository
/composable-science-tools/      # github:composable-science/tools
|-- flake.nix                   # Defines the master `cs` app and all templates
|-- packages/
|   |-- cs-cli/
|   |   |-- main.py             # Core `cs` CLI logic (Typer)
|   |   |-- builder.py          # Local build engine
|   |   |-- dashboard.py        # Local dashboard generator
|   |   |-- attestation.py      # Logic for `cs attest`
|   |   `-- identity.py         # Logic for `cs id`
|   `-- cs-mermaid-theme.css    # Professional, custom Mermaid theme
|-- templates/
|   |-- latex-python/           # A complete, working project template
|   |   |-- flake.nix
|   |   `-- composable.toml
|   `-- ... (other templates)

# What the User Sees
/user-project-directory/        # After `cs init`
|-- flake.nix
|-- composable.toml
|-- .cs/
|   `-- identity.key            # User's private key for signing
|-- paper.tex
|-- analysis/
|   `-- main.py
|-- output/
|   |-- .gitignore
|   `-- (Generated artifacts: paper.pdf, dashboard.html, etc.)
```

---

### ** Stretch Goals (Prioritized)**

1.  **Pipeline Caching:** A robust local cache to avoid re-running unchanged processes. This is critical for a smooth user experience.
2.  **Cloud Execution:** `cs run <process> --on-cloud` to offload heavy computation, making the tool practical for large-scale science.
3.  **GraphQL API:** Implement a GraphQL endpoint alongside the REST API for more flexible and powerful data queries, empowering third-party app developers.
4.  **Expanded Attestation Suite:** Develop a full suite of `qualitative` (`peer_review`, `citation`) and advanced `verifiable` (`pdf-visual-audit`) attestation types.
5.  **ZKP Toolkit:** Create a `cs-zkp-toolkit` to help researchers create verifiable claims on private data.