# 0004: Keep application device identity in addition to network security

Status: accepted

Date: 2026-07-16

## Context

Private IP addresses and an apartment network do not identify a trusted Donna
client. Tailscale or TLS protects transport but does not provide Donna's device
inventory, capability scopes, independent revocation, or replay semantics.

## Decision

Enroll each client with a short-lived one-time code. The client generates an
Ed25519 private key locally, stores it in its platform credential manager, and
sends only the public key during pairing. Authenticate requests with device identity, timestamp,
nonce, body-bound signature, and durable replay state.

## Alternatives

- IP allowlisting: rejected as primary identity because addresses change and can
  be spoofed.
- One shared bearer token: rejected because it cannot revoke or scope one device.
- Network identity alone: rejected because Donna still needs application-level
  device presence and audit identity.

## Consequences

Clients need secure private-key storage and clock synchronization. The server
stores no recoverable device signing secret. Every transport must share signing
fixtures. Demo storage may be in memory but must report that restart loses
enrollment; production requires PostgreSQL persistence.
