# Windows implementation handoff

This file is the entry point for a Codex session running on the gaming laptop.

## Read first

1. docs/system-spec.md
2. docs/orchestrator-spec.md
3. docs/ollama-interface.md
4. docs/api-contract.md
5. docs/architecture.md
6. docs/roadmap.md
7. README.md

The system specification wins when older documents differ. Update it when a reviewed product decision changes.

## First Windows session

The first Windows session should investigate before changing the operating environment:

- inventory Windows edition and build
- inventory NVIDIA GPU, driver, CUDA compatibility, and observed VRAM
- inventory Ollama version, models, endpoints, and storage
- inventory Python, Git, Rust, PostgreSQL availability, and free disk
- measure LAN identity and candidate service bind addresses
- benchmark candidate Whisper models
- benchmark installed Ollama models under realistic contention
- propose the service development environment and dependency strategy

Do not begin Google OAuth, background-service setup, firewall changes, startup configuration, or package installation until the user reviews the findings and plan. Preserve the global safety instructions in effect for the Codex environment.

The unattended-safe scope is read-only assessment, benchmarks that do not alter system configuration, documentation, tests, and repository-local implementation. YOLO mode does not authorize OS configuration, public network exposure, Google mutations, email sending, file deletion, purchases, trades, or destructive actions.

Do not automatically download Ollama models. Inventory and benchmark installed models, map candidates to the roles in docs/orchestrator-spec.md, and report missing roles.

## Recommended first implementation slice

Build a read-only vertical slice:

1. laptop health endpoint
2. authenticated device pairing
3. dashboard snapshot with mock server data
4. Rust client connection and stale-state handling
5. WebSocket invalidation
6. one read-only Google connector after OAuth design review

This validates the cross-machine contract before introducing an orchestrator.

## Existing repository state

- branch: feat/cli-dashboard
- first implementation commit: 36ed6e6
- Rust TUI with demo data
- locked dependencies and pinned toolchain
- tests for several terminal dimensions

Run:

    cargo fmt --check
    cargo test --locked
    cargo clippy --locked --all-targets --all-features -- -D warnings
    cargo build --release
