# 0003: Isolate Ollama behind one adapter

Status: accepted

Date: 2026-07-16

## Context

Ollama is the initial local inference provider, but provider request objects, streaming formats, model tags, and runtime behavior should not spread throughout Donna.

## Decision

Only the inference adapter communicates with Ollama. Application code requests configured model roles through a typed interface. Model identity includes its digest. Structured responses are schema-validated before use.

## Alternatives

- Call Ollama from each feature: rejected because configuration, telemetry, retries, and replacement become inconsistent.
- Adopt a broad multi-provider framework immediately: rejected because it adds abstraction before a second provider exists.

## Consequences

Ollama behavior and failures have one owner. Replacing it requires a new adapter and contract tests. The adapter itself must remain narrow and avoid becoming a second orchestrator.

