# Proposed CLI and server contract

The contract is versioned under /v1. JSON uses stable IDs, RFC 3339 timestamps, source metadata, and entity tags. The server owns synchronized state.

## Transport

- REST for snapshots, commands, approvals, and pagination
- WebSocket at /v1/events for invalidations, job progress, approvals, and streamed text
- HTTPS on the LAN
- per-device identity, nonce, and timestamp
- idempotency key on every mutation

## Core endpoints

- GET /v1/dashboard?window=today
- POST /v1/commands
- GET /v1/jobs
- GET /v1/jobs/{id}
- POST /v1/jobs/{id}/pause
- POST /v1/jobs/{id}/resume
- POST /v1/jobs/{id}/cancel
- GET /v1/jobs/{id}/findings
- POST /v1/approvals/{id}/decision

Dashboard entries include opaque ID, source, source ID, timestamps, detail URL, and freshness. The CLI never infers an external identifier from display text.

A command contains text, a client request ID, current view context, selected IDs, execution mode, and optional time budget. The server returns a result, an accepted durable job, or an approval requirement.

## Jobs

A job response exposes state, current activity, sources found, checkpoints, resource budget, and terminal outcome. Only show a percentage when the denominator is genuinely known.

## Approvals

Approval choices are deny, approve once, approve for this job, or update persistent policy. Each preview has an effect hash. The server rejects approval if the effect changes after preview.

## Client-side file tools

When the laptop needs a desktop-only operation, it emits a tool request containing a tool call ID, workspace ID, relative path, expected content hash, proposed patch, effect hash, and approval requirement.

The client resolves the path beneath a configured canonical workspace, rejects traversal and symlink escapes, shows the diff, obtains approval when required, verifies the expected hash, applies atomically, and returns a result. It never trusts a server-supplied absolute path.

## Events and reconnection

Each event contains event ID, monotonically increasing sequence, occurrence time, type, resource ID, and typed data. The client stores the last sequence in non-sensitive local state. Reconnection requests later events; if retention expired, the server requests a fresh snapshot.

## Errors

Errors contain code, safe display message, request ID, retryable flag, and optional structured fields. They never contain secrets. Machine codes remain stable when wording changes.

