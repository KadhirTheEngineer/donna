# Donna Codex instructions

These instructions apply to the entire repository.

## Required reading

Before planning, editing, installing project dependencies, or running benchmarks, read these files completely in order:

1. docs/handoff.md
2. docs/system-spec.md
3. docs/orchestrator-spec.md
4. docs/ollama-interface.md
5. docs/api-contract.md
6. docs/serviceability.md
7. docs/architecture.md
8. docs/roadmap.md
9. README.md

Also read every accepted decision record under docs/decisions before changing a boundary covered by that decision.

Do not ask the user to repeat the product requirements from chat. The checked-in specifications are the source of truth. docs/system-spec.md owns product behavior; the more specific normative specifications refine implementation behavior.

## Session startup

Inspect the current repository, branch, status, recent commits, and available toolchain before acting.

When running on the Windows gaming laptop, begin with the assessment in docs/handoff.md:

- Windows edition and build
- NVIDIA GPU, driver, CUDA compatibility, and observed VRAM
- Ollama version, endpoint, installed models, loaded models, and storage
- Python, Git, Rust, PostgreSQL availability, and free disk
- LAN identity and candidate private bind addresses
- safe Ollama and Faster-Whisper benchmarks

Write sanitized findings into checked-in documentation. Never commit hostnames, usernames, IP addresses, serial numbers, credentials, tokens, cookies, personal messages, or other private machine identifiers.

After assessment, continue autonomously with the recommended first read-only vertical slice in docs/handoff.md. Use safe defaults from the specifications instead of stopping for non-blocking preferences. Record genuine blockers in the repository with their exact evidence and continue other unblocked work.

## Unattended scope

Allowed without additional prompting:

- read-only machine and repository inspection
- non-destructive benchmarks that do not change system configuration
- repository-local source code, tests, fixtures, documentation, and configuration examples
- project-local dependency environments
- dependency downloads declared and locked in project manifests
- formatting, linting, tests, contract generation, and release builds
- local demo processes bound only to loopback
- small coherent Git commits and pushes to the current feature branch

YOLO or approval-free mode does not broaden the product or safety scope.

Do not perform these unattended:

- OS, bootloader, kernel, driver, registry, firewall, service, startup, or package-manager configuration
- systemwide package installation
- binding a service to a public or LAN interface
- opening ports or weakening authentication
- Google OAuth enrollment or real Google mutations
- sending email
- modifying real calendars or tasks
- downloading Ollama models automatically
- deleting or overwriting user files
- purchases, trades, brokerage actions, or bank access
- destructive database or Git operations
- weakening tests, permissions, security boundaries, or specifications to make checks pass

If a prohibited action becomes necessary, document the proposed action, reason, exact target, risk, and verification plan, then stop that path while continuing safe work elsewhere.

## Engineering rules

- Serviceability is a release requirement.
- Begin as a modular monolith.
- Keep Ollama behind the single inference adapter.
- Route known commands deterministically before model inference.
- Models propose typed operations; they never execute raw tools directly.
- Keep provider SDK objects inside their adapters.
- Use typed configuration and stable error categories.
- Use fake adapters and sanitized deterministic fixtures by default.
- Ordinary tests must not require personal credentials, a GPU, or internet access.
- Cross-component contracts must have one versioned schema source.
- Database changes require checked-in migrations.
- Long work must be durable, resumable, bounded, cancellable, and inspectable.
- Do not introduce Redis, a message broker, vector database, workflow platform, microservices, or a broad model framework without a documented measured requirement and accepted decision record.
- Do not mix repository moves, bulk formatting, dependency upgrades, and behavioral changes in one commit.
- Do not silently change specifications to match accidental implementation.

## Documentation and learning

A feature is incomplete without:

- user-visible behavior documentation
- typed configuration reference
- tests and sanitized fixtures
- failure and recovery behavior
- relevant architecture or decision updates
- a short owner-facing explanation when the feature introduces a new concept

Prefer code that can be followed from API entry to application service, domain decision, adapter, state change, event, and client presentation.

## Verification

Run the narrowest relevant checks while developing and all available repository checks before committing.

Current Rust checks:

    cargo fmt --check
    cargo test --locked
    cargo clippy --locked --all-targets --all-features -- -D warnings
    cargo build --release

When server tooling is added, document one local command that runs its formatting, static analysis, unit tests, contract checks, and migration validation. CI commands must remain runnable locally.

Do not claim completion when required checks were skipped. State what was and was not verified.

## Git

- Work on the current feature branch unless the handoff explicitly calls for a new one.
- Preserve unrelated user changes.
- Make small coherent commits with short messages.
- Use author name kadhirtheengineer.
- Push completed safe work to the current upstream feature branch.
- Do not force-push, rewrite history, delete branches, or merge to main unattended.

