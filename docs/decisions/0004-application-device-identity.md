# 0004: Keep application device identity in addition to network security

Status: accepted

Date: 2026-07-16

## Context

Private IP addresses and an apartment network do not identify a trusted Donna
client. Tailscale or TLS protects transport but does not provide Donna's device
inventory, capability scopes, independent revocation, or replay semantics.

## Decision

Enroll each client with a short-lived one-time code and issue an independent
device credential. Authenticate requests with the device identity, timestamp,
nonce, and body-bound signature. Store replay state durably in production.

## Alternatives

- IP allowlisting: rejected as primary identity because addresses change and can
  be spoofed.
- One shared bearer token: rejected because it cannot revoke or scope one device.
- Network identity alone: rejected because Donna still needs application-level
  device presence and audit identity.

## Consequences

Clients need secure credential storage and clock synchronization. Every transport
must share signing fixtures. Demo storage may be in memory but must report that
restart loses enrollment; production requires PostgreSQL persistence.
