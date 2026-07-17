# Donna

Donna is a local-first personal command center. This repository contains its thin Rust terminal client: a responsive dashboard intended to stay open on a second monitor while a future laptop-hosted service handles integrations, models, tools, and background work.

This milestone deliberately uses realistic demo data. It settles what Donna should present and how it should feel before the orchestrator is built.

## Current features

- Calendar, tasks, important mail, research jobs, and market context
- Responsive wide, compact, focused, and undersized layouts
- Keyboard navigation and a command/ask palette
- Inspectable, granular permission policy
- Cross-platform configuration
- Render tests for square 1080-pixel window proportions and smaller terminals

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
    docs/            service architecture, API contract, and roadmap

The service is designed in detail but intentionally not implemented in this milestone.

## Privacy stance

Donna is designed so personal content, embeddings, model prompts, and integration tokens stay on the laptop. Google still receives requests necessary to use Gmail, Calendar, and Tasks, and websites receive normal browser traffic during research. Local-first prevents Donna from introducing another cloud AI or hosted database; it cannot make upstream services disappear.

Financial output must preserve source, publication time, observed period, and retrieval time. Donna will organize evidence, not place trades or manufacture certainty.

