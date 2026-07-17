# How Donna works

This is the owner-facing map of Donna. It explains how the pieces fit together,
what exists today, and which specifications own the detailed behavior. It is a
guide, not a second specification: when wording differs, `system-spec.md` and
the more specific normative specifications win.

## The short version

Donna has a thin Rust terminal client and one Python service on the Windows
compute laptop. The client displays state and collects commands. The laptop
owns authentication, planning, local models, provider connections, durable
state, policy, and audit history.

A request follows one understandable path:

    Rust CLI
      -> authenticated FastAPI endpoint
      -> deterministic command router
      -> orchestrator, only when more work is needed
      -> policy decision
      -> typed adapter operation
      -> PostgreSQL state and outbox event
      -> WebSocket invalidation
      -> refreshed CLI view

Known commands take the deterministic lane and do not need an LLM. An LLM may
classify an unknown request or propose a typed plan, but model text is never
executed as a tool call. Policy evaluates the typed operation before an adapter
can execute it.

Reads may proceed when policy allows them. Any Google write, send, deletion, or
other consequential external effect must stop at `waiting_for_approval`. The
CLI shows an exact preview and effect hash; execution resumes only after the
owner approves that unchanged effect in the CLI. Changing the proposed effect
invalidates the approval.

## What is implemented now

The current branch is the first read-only vertical slice, not the complete
orchestrator milestone.

- The Rust TUI has demo and connected modes, secure local key storage, signed
  requests, reconnect behavior, explicit stale state, cache-policy enforcement,
  and WebSocket invalidation.
- The FastAPI service has loopback-only defaults, health reporting, one-time
  device pairing, Ed25519 request authentication, replay protection, dashboard
  snapshots, redacted request tracing, and stable error categories.
- PostgreSQL adapters persist devices, replay nonces, and the event outbox.
  Demo mode uses replaceable in-memory adapters.
- Cross-language JSON Schemas and deterministic fixtures define the implemented
  snapshot, event, signature, and calendar-page contracts.
- A fake Calendar adapter proves the provider boundary. Real Google OAuth and
  Calendar synchronization have not begun because owner review is required.
- Ollama and Faster-Whisper were assessed and benchmarked on this laptop. The
  full inference adapter, orchestrator, durable job scheduler, policy engine,
  and real read tools remain specified future work.

This distinction matters: a behavior described in a normative specification is
the required design, but it is not necessarily implemented yet. The roadmap
defines milestone order; tests and component documentation describe current
code.

## Stack ownership

| Part | Responsibility | Current location | Detailed source |
|---|---|---|---|
| Rust CLI | Render state, collect requests and approvals, retain device key, show stale/offline state | `src/` | `README.md`, `api-contract.md` |
| API edge | Authenticate, validate, trace, return quickly, publish events | `server/src/donna_server/api/` | `api-contract.md` |
| Application layer | Coordinate dashboard and identity use cases | `server/src/donna_server/application/` | `architecture.md` |
| Domain layer | Provider-independent records, interfaces, and errors | `server/src/donna_server/domain/` | `architecture.md`, `serviceability.md` |
| Orchestrator | Route, classify, plan, checkpoint, and finish bounded work | specified, not yet implemented | `orchestrator-spec.md` |
| Policy and approvals | Decide allow, ask, or deny for each typed effect | specified, not yet implemented | `system-spec.md`, `orchestrator-spec.md` |
| Local inference | Resolve model roles and isolate Ollama HTTP details | specified and benchmarked, not yet implemented | `ollama-interface.md` |
| Connectors | Translate Google or other providers into Donna records | fake Calendar boundary implemented | `architecture.md`, Google OAuth design |
| Durable state | Store authoritative relational state and transactional events | identity and outbox foundation implemented | migrations, `architecture.md` |
| Contracts | Version messages shared by Python and Rust | implemented under `contracts/` | `api-contract.md`, `contracts/README.md` |
| Operations | Bootstrap, checks, migrations, recovery, and diagnostics | initial scripts and runbooks implemented | `serviceability.md`, `docs/runbooks/` |

The dependency direction is always inward: API and adapters depend on
application and domain interfaces. Domain code never imports FastAPI, Ollama,
Google SDK objects, or PostgreSQL implementation details. Replacing a provider
should mean implementing one typed interface and passing its contract tests,
not rewriting the orchestrator or client.

## Three representative flows

### Opening the dashboard today

1. The client signs `GET /v1/dashboard` with its Ed25519 private key.
2. The API verifies device identity, timestamp, nonce, signature, and scope.
3. The dashboard application service asks domain interfaces for current state.
4. The response declares whether local caching is permitted.
5. The client renders it as online. A restored cached snapshot is always marked
   stale until the server confirms it.
6. A committed outbox event invalidates the view over WebSocket; the client
   deduplicates events by sequence and refreshes the snapshot.

### Handling a future read request

1. The API persists the authenticated request and returns promptly.
2. The deterministic router handles known commands before inference.
3. If needed, a configured local model returns a schema-validated
   classification or typed plan through the single inference adapter.
4. The orchestrator rejects unknown tools, invalid arguments, cycles, or plans
   outside configured budgets.
5. Policy allows an eligible read; a registered adapter executes it.
6. Donna validates the observation, records provenance, checkpoints durable
   work, updates stable domain objects, and emits an event.

### Handling a future write request

1. Routing and planning produce a typed proposed operation, never raw model code.
2. Policy classifies the effect and creates an exact preview plus effect hash.
3. The durable job enters `waiting_for_approval`; nothing is written externally.
4. The CLI displays the preview. Only an explicit owner decision can resume it.
5. The server verifies that the approved hash still matches, then calls the
   connector with an idempotency key.
6. The result is reconciled with the provider and recorded in the audit trail.

## Data, cache, and privacy

PostgreSQL on the laptop is authoritative. Provider tokens stay on the laptop
and never reach the Rust client. Local client caching is allowed when the server
marks a response `allow_local`; the cache may contain the normalized records
needed for a useful offline view. Cache policy remains server-controlled so a
future sensitive view can be `memory_only` without changing the client.

The local-first boundary does not hide activity from an upstream provider:
Google sees Google API requests, and websites see research traffic. Logs and
health responses omit credentials, raw personal content, prompts, host identity,
and private paths by construction.

## Failure and recovery model

Optional components fail independently. Missing Google credentials do not stop
demo mode; missing Ollama does not prevent deterministic dashboard behavior; a
stale client does not present cached data as current. Long work is durable,
bounded, cancellable, checkpointed, and inspectable rather than tied to one HTTP
request or process lifetime.

Errors use stable categories such as `authentication`, `validation`,
`rate_limited`, `provider_unavailable`, and `timeout`. Request and trace IDs join
client-visible failures to redacted server diagnostics. Runbooks under
`docs/runbooks/` explain operational recovery as each component lands.

## Recommended reading order

For a product-level understanding, read:

1. this guide;
2. `system-spec.md` for the complete intended behavior;
3. `architecture.md` for component boundaries;
4. `orchestrator-spec.md` for request planning and durable execution;
5. `ollama-interface.md` for local-model isolation and scheduling;
6. `api-contract.md` for the client/server wire protocol;
7. `serviceability.md` for maintainability and owner-learning requirements;
8. `roadmap.md` for implementation order;
9. `design/google-read-only-oauth.md` before authorizing Google enrollment.

Decision records under `docs/decisions/` explain why important boundaries were
chosen. JSON Schemas under `contracts/` are the executable source for messages
already implemented across languages.

## How to verify the current slice

Run the deterministic demo without credentials:

    scripts\bootstrap.cmd
    scripts\run-demo-server.cmd

Run every repository check locally:

    scripts\check.cmd

The connected walkthrough is in `docs/tutorials/connected-dashboard.md`. The
fake provider walkthrough is in `docs/tutorials/fake-calendar-connector.md`.
