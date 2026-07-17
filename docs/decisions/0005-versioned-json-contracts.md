# 0005: Use versioned JSON Schema as the cross-language contract source

Status: accepted

Date: 2026-07-16

## Context

Donna's Python service and Rust clients must not evolve subtly different REST and
event records. Handwritten duplicates are hard to audit and make compatibility
failures appear only at runtime.

## Decision

Keep versioned JSON Schemas and sanitized examples under `contracts/`. Both the
server and Rust client validate those examples. Generate language types where
the generator remains small and deterministic; otherwise contract tests bind
explicit domain types to the single schema source.

## Alternatives

- Python models as the only source: rejected because Rust compatibility becomes
  indirect.
- Separate handwritten contracts: rejected because drift is inevitable.
- A broad schema registry service: rejected as unnecessary infrastructure.

## Consequences

Contract changes include compatibility assessment, example updates, and tests in
both components. Generated output must remain reproducible and reviewed with its
schema source.
