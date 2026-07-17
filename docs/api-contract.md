# Proposed CLI and server contract

The contract is versioned under /v1. JSON uses stable IDs, RFC 3339 timestamps, source metadata, and entity tags. The server owns synchronized state.

## Transport

- REST for snapshots, commands, approvals, and pagination
- WebSocket at /v1/events for invalidations, job progress, approvals, and streamed text
- HTTPS on the LAN
- per-device identity, nonce, and timestamp
- idempotency key on every mutation

## Core endpoints

- GET /v1/health
- POST /v1/pairing/codes (laptop loopback only)
- POST /v1/pairing/complete
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

The health endpoint is safe before enrollment and contains sanitized component
state, last success, stable error category, dependency health, details, and an
actionable remedy. It never exposes hostnames, IP addresses, user paths, tokens,
prompts, or personal content.

During pairing, the client generates an Ed25519 private key in its platform
credential store and sends only the public key with the one-time code, friendly
name, and requested capabilities. The server returns the device ID; it never
receives or issues a recoverable device signing secret.

Authenticated requests carry `X-Donna-Device-Id`, RFC 3339
`X-Donna-Timestamp`, a unique `X-Donna-Nonce`, and base64url
`X-Donna-Signature`. The signed bytes are UTF-8:

    UPPERCASE_METHOD + "\n" + PATH + "\n" + TIMESTAMP + "\n" + NONCE + "\n" + SHA256_HEX(BODY)

The server verifies the Ed25519 signature, clock window, capability, revocation,
and durable nonce claim. Query parameters are validated by the endpoint but are
not part of the version-one canonical path. Every new mutation additionally
requires the specified idempotency key and effect hash.

Dashboard snapshots declare `cache_policy` as `allow_local` or `memory_only`.
The client persists only `allow_local` snapshots and always marks a restored
snapshot stale until the server confirms current state.

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

