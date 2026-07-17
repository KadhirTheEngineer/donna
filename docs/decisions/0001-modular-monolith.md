# 0001: Begin as a modular monolith

Status: accepted

Date: 2026-07-16

## Context

Donna has many domains, but it begins on one personal laptop and must remain understandable and changeable by one owner. Premature services would introduce deployment, networking, tracing, compatibility, and failure complexity.

## Decision

Build one FastAPI application and one or more background worker processes from the same Python package. Enforce internal module boundaries through typed interfaces and tests. Use PostgreSQL for shared durable state.

## Alternatives

- Microservices: rejected until independent scaling or isolation is measured.
- One unstructured application module: rejected because domain ownership would become unclear.
- External workflow platform: deferred until PostgreSQL jobs are proven insufficient.

## Consequences

Local development and deployment remain simple. Internal boundaries require discipline and tests rather than network isolation. A future service split remains possible at an adapter or application-service boundary.

