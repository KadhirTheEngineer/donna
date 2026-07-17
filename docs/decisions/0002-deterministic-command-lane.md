# 0002: Route known commands before models

Status: accepted

Date: 2026-07-16

## Context

Voice and navigation commands must respond quickly and predictably. Sending every request through a large model adds latency, resource contention, ambiguity, and debugging difficulty.

## Decision

Run normalized input through a deterministic typed command router before model classification. Consequential targets must resolve uniquely. Unmatched or compound requests continue to the orchestrator.

## Alternatives

- LLM for every command: rejected for latency and serviceability.
- Client-side command interpretation: rejected because behavior would diverge across devices.

## Consequences

Common commands are fast, testable, and traceable. New aliases require explicit fixtures. Natural-language flexibility remains available through the fallback orchestrator.

