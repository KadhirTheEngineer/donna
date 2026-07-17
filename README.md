# Donna

Donna is a local-first personal command center. This repository contains its thin Rust terminal client and the first laptop-hosted read-only service slice.

Codex contributors should start from the repository root. AGENTS.md automatically loads the complete product and Windows handoff instructions.

This milestone deliberately uses realistic demo data. It settles what Donna should present and how it should feel before the orchestrator is built.

## Current features

- Calendar, tasks, important mail, research jobs, and market context
- Responsive wide, compact, focused, and undersized layouts
- Keyboard navigation and a command/ask palette
- Inspectable, granular permission policy
- Cross-platform configuration
- Render tests for square 1080-pixel window proportions and smaller terminals
- Loopback laptop health, authenticated pairing, dashboard snapshot, local cache,
  visible stale state, and WebSocket invalidation

## Run

Install Rust with rustup, then run:

    cargo run

Other useful commands:

    cargo run -- --help
    cargo run -- config path
    cargo run -- config example
    cargo test
    cargo build --release

The optimized result is target/release/donna, or donna.exe on Windows.

## Run the demo server

Python 3.11 is required. The server uses a project-local environment and needs
no credentials, PostgreSQL, GPU, Google account, or internet access in demo mode:

    scripts\bootstrap.cmd
    scripts\run-demo-server.cmd

Run every Python and Rust repository check locally with:

    scripts\check.cmd

Health is available at `http://127.0.0.1:8742/v1/health`. The server is
intentionally loopback-only until encrypted LAN transport is implemented.

To exercise connected client mode, create a pairing code on the laptop with
`.venv\Scripts\python -m donna_server pairing-code`, run `donna pair` on the
client, and set `show_demo_data = false` in the client configuration. Cached
data is shown as stale until reconnection. Only snapshots explicitly marked
`allow_local` by the server are written to the local cache.

## Keys

| Key | Action |
|---|---|
| Tab, Shift-Tab, arrows, hjkl | Navigate widgets |
| 1 through 5 | Jump to a widget |
| Enter | Focus selected widget |
| Esc | Return to dashboard |
| : or / | Open command and ask palette |
| p | Inspect permissions |
| r | Refresh |
| ? | Help |
| q, Ctrl-C | Quit |

Palette commands include calendar, tasks, mail, research, markets, permissions, and quit. Other text is treated as a Donna request; until the laptop service exists, it is shown as disconnected.

## Configuration

Donna reads config.toml from the platform-native user configuration directory. Run donna config path for the exact location and donna config example for a complete starting file.

The safe default is guarded mode: reads are allowed, consequential writes ask, and destructive actions always ask.

## Project map

    src/app.rs       interaction state and keyboard commands
    src/config.rs    cross-platform policy and connection configuration
    src/model.rs     dashboard data contract and demo data
    src/ui.rs        responsive Ratatui presentation
    src/main.rs      terminal lifecycle and command-line entry point
    docs/system-spec.md  product and system source of truth
    docs/orchestrator-spec.md  typed workflow and durability contract
    docs/ollama-interface.md   local inference adapter contract
    docs/serviceability.md     maintainability and owner-learning contract
    docs/handoff.md      entry point for the Windows implementation session
    docs/                architecture, API contract, and roadmap

The read-only service foundation is implemented; Google OAuth and connector work
remain gated on the design review required by the Windows handoff.

## Privacy stance

Donna is designed so personal content, embeddings, model prompts, and integration tokens stay on the laptop. Google still receives requests necessary to use Gmail, Calendar, and Tasks, and websites receive normal browser traffic during research. Local-first prevents Donna from introducing another cloud AI or hosted database; it cannot make upstream services disappear.

Financial output must preserve source, publication time, observed period, and retrieval time. Donna will organize evidence, not place trades or manufacture certainty.
