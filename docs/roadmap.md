# Delivery roadmap

## Milestone 0: interface prototype

This repository state provides a responsive dashboard, demo data, focus navigation, command palette, help, permission viewer, configuration, multi-size rendering tests, architecture, and API contract.

Exit gate: it remains legible in a roughly 1080 by 1080 pixel terminal window and scales down gracefully.

## Milestone 1: connected read-only dashboard

- asynchronous REST and WebSocket Rust client
- pairing and credential storage
- reconnect, cache, stale markers, and event replay
- FastAPI edge and PostgreSQL
- read-only Calendar, Tasks, and Gmail synchronization

Exit gate: restarts are safe, stale data is unmistakable, and Google tokens never reach clients.

## Milestone 2: conversation and Ollama

- streaming command palette and conversation view
- Ollama model registry and health measurement
- typed intent classifier and deterministic direct routes
- conversation persistence and source-aware responses

Exit gate: routine commands do not require a large model and failures remain inspectable.

## Milestone 3: guarded actions

- previews for Gmail, Calendar, and Tasks mutations
- policy engine, approval queue, idempotency, effect hashing, and audit
- approved client workspaces, file patches, and constrained shell execution

Exit gate: every consequential effect is previewable and replay cannot duplicate it.

## Milestone 4: durable research

- PostgreSQL job leases, heartbeats, checkpoints, pause, resume, and cancellation
- browser workers with caching, throttling, and provenance
- fact and inference separation
- model routing and GPU admission control
- research notebook and finding drill-down

Exit gate: a reboot during hours-long work loses at most one checkpoint interval and reports cite material claims.

## Milestone 5: financial intelligence

- security master, watchlists, and manual portfolio positions
- SEC, company, and government primary-source ingestion
- deterministic metrics and comparable-period normalization
- earnings, balance sheet, dilution, valuation, catalyst, and risk views

Exit gate: every figure has units, period, retrieval time, and source. Donna offers evidence, not trade instructions.

## Milestone 6: remote access and hardening

- Tailscale
- backup, restore, and retention
- encrypted secret and artifact verification
- signed client builds
- load, failure-injection, permission-bypass, and recovery tests

Exit gate: a clean-laptop restore works and revoked devices cannot reconnect.

## Principles

- Add infrastructure only when measured requirements justify it.
- Prefer typed workflows over open-ended agent loops.
- Separate raw evidence and deterministic calculations from summaries.
- Make stale, partial, inferred, and failed states explicit.
- Profile GPU memory, latency, and throughput on the actual laptop.
- Keep cached views useful while visibly disconnected.

