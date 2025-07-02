# Product
**Composable Science** is a decentralized protocol and backend platform for creating a verifiable, public record of scientific knowledge. It provides the core infrastructure, client tools, and a public API to enable a new generation of scientific publishing, where every computational result and data source is backed by a signed, structured **attestation**.

# Tech Stack
*   **Core Technology:** Nix (for reproducible builds), Git (for versioning and history)
*   **Languages & Frameworks:** Python (for services & tooling), Shell Script (for client tools), FastAPI (for API server)
*   **Database:** SQLite (for the verifiable ledger artifact)
*   **Infrastructure:** GitHub (for source code, PRs), a public Nix binary cache (e.g., Cachix free tier) for artifact distribution, IaaS (e.g., AWS, DigitalOcean) for bot and API hosting.

# Functional Requirements
*   The system shall provide a client tool (`attest`) for users to create and sign attestations.
*   The system's protocol shall support two classes of attestations: `verifiable` and `qualitative`.
*   The system shall define a `public_data_ingestion` verifiable attestation to create a canonical, cached Nix artifact from an external public dataset.
*   The system's protocol shall define a `private_computation_proof` qualitative attestation type for claims on private data.
*   The system shall manage a `composable-science/submissions` repository as a public inbox for new attestations.
*   The system shall use a trusted bot (`Ledger Maintainer Bot`) to batch submissions and commit them to the canonical `composable-science/core` ledger repository.
*   The system shall build the entire ledger into a single, verifiable SQLite database artifact using a Nix Flake.
*   The system shall provide a public API with endpoints necessary to power an external web-based visualizer for exploring the knowledge graph.
*   The system shall provide an identity manager (`id-manager`) for users to create and manage a `did:key` decentralized identity.

# Non-functional Requirements
*   **Verifiability:** `verifiable` attestations must be machine-checkable. The ledger database itself must be a byte-for-byte reproducible artifact.
*   **Security:** All attestations must be cryptographically signed. The Ledger Maintainer Bot must have a secure, auditable process.
*   **API Stability:** The public API must be versioned and maintain backward compatibility where possible.
*   **Efficiency:** The system must use the binary cache to prevent redundant data downloads. API queries on the Ledger must be low-latency.
*   **Privacy:** The system should provide a clear path for making verifiable claims about research on sensitive data without revealing that data, though the most common use case should be based around the sharing of open data.

# Acceptance Tests
*   **Scenario: Submitting a computational verification**
    *   Given a user has a valid DID and a verifiable Nix claim.
    *   When they run `attest verify-computation <claim_url> <store_path>`.
    *   Then a signed `computational_verification` attestation is submitted as a PR to the `submissions` repository.
*   **Scenario: Importing external data for efficiency**
    *   Given a trusted curator bot and a URL to a large public dataset.
    *   When the bot runs the `fetch-and-verify` primitive.
    *   Then a `verifiable`, `public_data_ingestion` attestation is added to the Ledger, associating the data with a canonical Nix store path.
*   **Scenario: Querying data for the front-end visualizer**
    *   Given a claim in the ledger depends on both a verifiable artifact and a ZKP-backed artifact.
    *   When an external client sends a GET request to `/api/v1/artifact/{hash}/dependencies`.
    *   Then the API returns a JSON object correctly identifying the distinct node types (`verifiable_computation`, `private_zkp_proof`) for each dependency.

# File Map
```
/composable-science-core/
|-- flake.nix
|-- docs/
|   |-- SPEC.md
|   `-- GUIDE.md
|-- packages/
|   |-- attest/
|   |   `-- attest.sh
|   |-- id-manager/
|   |   `-- id-manager.py
|-- services/
|   |-- api/
|   |   |-- main.py
|   |   `-- requirements.txt
|   `-- ledger-bot/
|       `-- bot.py
|-- verifiers/
|   |-- nix-build.sh
|   `-- fetch-and-verify.sh
|-- ledger/
|   |-- attestations/ # Contains batched .tar.gz archives
/composable-science-submissions/
|-- .github/
|   `-- workflows/
|       `-- pr-validator.yml
```

# Stretch Goals
*   Develop a full suite of qualitative attestation types (`peer_review`, `significance_assessment`, `citation`).
*   Implement advanced `verifiable` primitives (`pdf-visual-audit`, `license-scan`).
*   Create a GraphQL endpoint for more flexible and powerful data queries from the front-end.
*   Build a user-friendly toolchain (`cs-zkp-toolkit`) to help researchers easily create ZKP circuits.