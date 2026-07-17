# Donna system architecture

## Decision

Build the interface first, then implement the service against a versioned contract.

The dashboard establishes the durable nouns: events, tasks, attention items, jobs, approvals, findings, sources, and portfolio observations. The orchestrator should produce these objects instead of leaking model-specific messages into the UI.

    Desktop or MacBook
    Donna Rust TUI
          |
          | HTTPS and WebSocket
          | per-device identity
          v
    Windows gaming laptop
    FastAPI edge
          |
    orchestrator -- durable scheduler -- domain services
          |
    Ollama -- browser workers -- parsers -- index workers
          |
    PostgreSQL -- content-addressed local storage

## Deployment boundary

The laptop is authoritative for Google OAuth tokens, connector synchronization, Ollama inference, browser research, long-running jobs, memory, summaries, policy evaluation, approvals, and audit history.

The client renders state, collects commands and approvals, and may operate on files that exist only on its own machine. This file access is the unavoidable exception to all processing being remote. Planning and inference stay on the laptop; a small client tool runner validates and applies an authorized operation locally.

## API edge

FastAPI owns the versioned REST API and WebSocket event stream. It validates device identity, creates request IDs, records audit events, and returns quickly. It never runs inference or browser work inside request handlers.

## Orchestrator

The orchestrator is a bounded decision engine, not one immortal agent loop:

1. Normalize the request.
2. Classify intent, domain, sensitivity, urgency, and duration.
3. Load only relevant context and capabilities.
4. Produce a typed plan with tools, budgets, and completion criteria.
5. Evaluate each step against policy.
6. Dispatch short work or create a durable job.
7. Validate tool output and attach provenance.
8. Checkpoint after each meaningful step.
9. Summarize into stable dashboard objects.

A small fast local model handles classification, extraction, routing, and routine summaries. Hard synthesis can escalate to the strongest practical local model. Routing should be based on measured quality and latency rather than parameter count.

## Durable scheduler

Long research cannot be an in-memory Python task. Each job has an immutable request, acceptance criteria, priority, deadline, compute class, resource budget, state machine, heartbeat, expiring lease, append-only events, checkpoints, capped retries, and cancellation.

Start with PostgreSQL workers using row locking with skip-locked semantics. This survives restarts without adding Redis prematurely. Add specialized queues only if profiling justifies them.

Job states are queued, leased, running, waiting for approval, paused, succeeded, failed, and cancelled.

## Resource scheduling

The 8 GB GPU is the scarce resource. Work declares a class:

- CPU light: connector sync, parsing, indexing
- CPU heavy: OCR and bulk transforms
- GPU interactive: chat and classification with latency priority
- GPU batch: research synthesis and embeddings
- network browser: search and retrieval

Keep an interactive model warm when measured memory allows. Batch work yields between inference units when interactive work arrives. Admit only one large GPU model at once until real VRAM measurements prove concurrency safe.

## Google connectors

Each connector supports health, incremental sync, fetch by ID, proposed mutation, applied mutation, and reconciliation.

- Calendar uses sync tokens and stable event IDs.
- Tasks synchronizes lists, completion, and due dates.
- Gmail synchronizes metadata first using history IDs, then fetches bodies only when needed.

OAuth occurs once on the laptop. Refresh tokens are protected by Windows credential protection and are never delivered to clients.

## Research

Free browser research is feasible, but free does not mean unrestricted. Sites have terms, rate limits, bot defenses, and copyright constraints.

Research should prefer SEC filings, investor relations, government statistics, central banks, and official releases; respect site rules; cache pages; record retrieval times and content hashes; distinguish extracted facts from inference; and show disagreement or missing data.

For equity work, normalize company profile, segment revenue, margins, cash flow, balance sheet, dilution, valuation inputs, guidance, risks, and catalysts. Deterministic code calculates metrics; the LLM explains them. Donna never emits or executes a trade.

## Data layer

PostgreSQL is the source of truth. Suggested schemas:

- identity: users, devices, credentials
- connectors: accounts, cursors, health, external IDs
- personal: events, tasks, messages, attention rules
- agent: requests, plans, jobs, steps, checkpoints, findings
- research: sources, snapshots, facts, citations
- finance: securities, watchlists, positions, observations, metrics
- safety: policies, approvals, tool calls, audit events

Large immutable artifacts use content-addressed local storage. PostgreSQL stores hashes and metadata. Add vector search later only when a concrete retrieval use case needs it.

## Network and identity

IP allowlisting is only an extra filter because local IPs can change or be spoofed. For the first LAN deployment:

1. Bind only to the private LAN interface.
2. Enroll each client with a short-lived pairing code shown on the laptop.
3. Issue a separate device key or certificate.
4. Sign requests or use mutual TLS.
5. Keep a device list with last-seen time and revocation.
6. Optionally apply an IP allowlist as defense in depth.

Tailscale can later provide encrypted transport and stable networking. Application identity remains useful.

## Permission model

Policy is evaluated per action across device, tool, operation, workspace or connector, sensitivity, effect, blast radius, and foreground versus unattended execution.

Decisions are allow, ask, or deny. YOLO mode may allow eligible non-destructive actions inside approved workspaces. It never removes path boundaries, audit logs, secret redaction, the purchase prohibition, or destructive confirmation.

Shell operations use argument arrays, explicit working directories, timeouts, output limits, environment allowlists, and process-tree cancellation. File changes show diffs. Deletion, unrecoverable overwrite, bulk moves, external sends, and invitation changes require preview by default.

## Privacy and observability

Donna-owned inference and storage stay local. Google necessarily processes data already held in Gmail, Calendar, and Tasks. Research sites see laptop requests. Public market data may be delayed or licensed only for personal display.

Every request receives a trace ID. Record the plan, policy decision, redacted tool parameters, result hashes, timing, model and template versions, source provenance, and approvals. Logs redact tokens, cookies, raw bodies, and secrets by construction.

