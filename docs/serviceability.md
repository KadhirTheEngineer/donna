# Serviceability and maintainability specification

Status: normative engineering contract

Donna must remain understandable and changeable by its owner. A feature is not complete merely because it works once. It is complete when its behavior, boundaries, configuration, tests, and failure modes can be understood without reconstructing the original author's reasoning.

## 1. Primary objective

For every important behavior, the owner should be able to answer:

- where does the input enter?
- which component owns the decision?
- which configuration changes it?
- which model or deterministic rule was used?
- which policy allowed or blocked it?
- which external systems were called?
- where is state stored?
- how can it be reproduced with fake data?
- how can it be disabled or replaced?

If these questions require reading the entire codebase, the architecture has failed.

## 2. Prefer boring components

Use the smallest conventional stack that meets measured requirements:

- Rust and Ratatui for the client
- Python and FastAPI for the service boundary
- Pydantic for typed Python contracts
- PostgreSQL for durable relational state
- ordinary HTTP and WebSocket protocols
- Ollama behind one adapter

Do not introduce a framework, message broker, vector database, workflow engine, dependency-injection container, plugin framework, or distributed service merely because it might become useful. Add one only with a documented requirement and decision record.

## 3. Modular monolith first

The laptop service begins as one deployable modular monolith with background worker processes using the same domain packages.

Modules communicate through typed interfaces and domain records, not imports into each other's internal implementation.

Required dependency direction:

    API and workers
          |
    application services
          |
    domain interfaces and records
          |
    adapters for database, Ollama, Google, markets, browser, and devices

Domain packages do not import FastAPI, SQLAlchemy models, HTTP clients, or provider SDK objects.

Do not split into networked microservices until profiling or independent failure isolation provides a concrete reason.

## 4. Repository organization

The repository should make component ownership obvious:

    clients/
      donna-tui/
      donna-controller/
    server/
      src/donna_server/
      tests/
      migrations/
    contracts/
      schemas/
      examples/
    docs/
      decisions/
      runbooks/
      tutorials/
    scripts/

The existing Rust client may move into clients/donna-tui only in a dedicated mechanical commit after the server begins. Do not combine a repository move with behavior changes.

Each top-level component has a README describing:

- purpose
- public interface
- dependency direction
- development commands
- configuration
- important tests
- known limitations

## 5. Explicit contracts

Cross-component messages are defined once:

- OpenAPI for REST
- JSON Schema for WebSocket events and structured records
- versioned examples in contracts/examples

Generate client types where practical. Do not maintain subtly different handwritten Python and Rust versions of the same protocol.

Contract changes require:

- schema version
- compatibility assessment
- fixture update
- server test
- client test
- migration or fallback behavior when breaking

Unknown fields are tolerated where safe. Unknown event types are logged and ignored rather than crashing a client.

## 6. Configuration

Behavioral choices live in typed configuration, not scattered constants.

Configuration has:

- documented defaults
- schema validation at startup
- environment-specific override rules
- redacted diagnostic output
- an example file kept current by tests
- no secrets in committed files

Separate:

- ordinary user preferences
- permission policy
- model-role configuration
- connector credentials
- deployment settings

Startup fails with a precise message for invalid required configuration. Optional integrations degrade independently.

## 7. Decision records

Material architectural decisions use short records under docs/decisions.

Each record contains:

- context
- decision
- alternatives considered
- consequences
- date and status

Required decisions include:

- modular monolith
- PostgreSQL job queue before Redis
- deterministic command lane before LLM
- Ollama adapter boundary
- application identity in addition to network security
- generated cross-language contracts

Decision records explain why. Specifications explain what. Code comments explain non-obvious local mechanics.

## 8. Code clarity

Rules:

- descriptive names over abbreviations
- small functions with one level of responsibility
- explicit state machines
- typed error categories
- no boolean parameters whose meaning is unclear at the call site
- no hidden global mutable state
- no provider SDK object outside its adapter
- no model prompt embedded inside business logic
- no shell command assembled through string interpolation
- no catch-all exception that silently continues
- no unexplained retry loop
- no dead code retained for hypothetical future features

Comments explain why a surprising choice exists. They do not narrate obvious syntax.

## 9. Traceable execution

Every user request has a trace view understandable without reading logs.

The trace shows:

- normalized request
- deterministic match or classifier result
- selected model role and digest
- plan
- policy decisions
- tool steps and durations
- retries
- source IDs
- checkpoint
- final or partial result

Sensitive content is redacted, but redaction must not make the execution path impossible to understand.

The TUI eventually exposes a compact Why or Details view for the latest action.

## 10. Development modes

Donna supports:

- demo: deterministic fixtures, no external services
- development: local server and replaceable fake adapters
- integration: real selected providers in a dedicated test account where available
- production: personal laptop deployment

The full TUI must run against demo fixtures.

The server must start without Google, Alpaca, a browser worker, or a GPU by using fakes. Ollama-dependent tests use a fake inference adapter unless explicitly marked as local integration tests.

## 11. Fixtures and replay

Keep sanitized fixtures for:

- dashboard snapshot
- calendar synchronization page
- Gmail attention item
- task mutation preview
- Alpaca bars
- Ollama streamed chat
- structured classifier output
- malformed structured output
- approval request
- research checkpoint
- device action

Recorded fixtures contain no personal data or credentials.

Important production failures should be reducible to a sanitized replay fixture and regression test.

## 12. Testing pyramid

Required layers:

- unit tests for deterministic logic and state transitions
- contract tests for schemas and generated clients
- adapter tests against fakes
- integration tests for PostgreSQL transactions and migrations
- end-to-end demo test from command to client event
- optional machine-local tests for installed Ollama and real connectors

Tests never require personal Google credentials by default.

Critical properties:

- idempotency
- cancellation
- lease ownership
- approval effect hashing
- permission denial
- stale client behavior
- schema compatibility
- model-output validation

## 13. One-command workflows

Provide documented cross-platform developer entry points:

- bootstrap project-local dependencies
- run client
- run demo server
- run unit checks
- run all repository checks
- run database migrations
- validate configuration
- generate contracts
- verify generated files are current

Use a small checked-in task runner or scripts with clear implementations. Do not hide essential behavior behind an opaque automation layer.

Every CI command is runnable locally.

## 14. Database migrations

All schema changes use checked-in migrations.

Rules:

- never mutate a production schema manually
- migration has upgrade and documented recovery behavior
- destructive migrations use expand, migrate, contract phases
- application remains compatible through rolling local process restarts where practical
- fixtures cover migration from the previous supported schema
- backup and restore are tested before storing irreplaceable personal history

## 15. Dependencies

Each component:

- pins or locks dependencies
- documents why non-obvious dependencies exist
- minimizes provider-specific SDKs
- avoids abandoned libraries
- separates development dependencies from runtime dependencies
- updates dependencies in dedicated commits

Do not add two libraries for the same responsibility without removing or justifying one.

## 16. Observability for humans

Health output reports:

- component
- state
- last success
- last error category
- dependency health
- actionable remediation

Logs are structured but readable. Error messages state what failed, relevant identity, whether retry is safe, and the trace ID.

Provide runbooks for:

- laptop cannot reach Ollama
- model missing or too large
- Google token expired
- synchronization stuck
- PostgreSQL unavailable
- job stuck on a lease
- client cannot pair
- certificate revoked
- handheld offline
- market provider rate limited
- disk nearly full
- backup restore

## 17. Feature flags and replacement

Experimental features are disabled by default and have typed flags.

Provider boundaries must allow:

- replacing Ollama with another local inference adapter
- replacing Alpaca with another market provider
- replacing Faster-Whisper with another local speech engine
- running without the handheld
- disabling all mutation tools

Replacement means implementing an interface and passing its contract tests, not rewriting orchestrator or UI domain logic.

## 18. Documentation as part of completion

A new feature is incomplete until it includes:

- user-facing behavior
- configuration reference
- architecture or decision update when applicable
- tests
- failure behavior
- troubleshooting note
- example or fixture

Code and documentation changes land together.

## 19. Learning path for the owner

Maintain short tutorials that build understanding incrementally:

1. run the Rust TUI with demo data
2. change a widget and its fixture
3. run the demo server
4. trace one dashboard request
5. add a deterministic command
6. inspect an Ollama structured response
7. add a read-only tool
8. inspect a durable job checkpoint
9. modify a permission rule
10. add a fake provider adapter

Tutorials use real project code and are verified periodically. The goal is for the owner to make ordinary changes confidently without relying on an agent.

## 20. Change discipline

Commits are small, coherent, and use short messages.

Avoid:

- mass rewrites mixed with features
- drive-by formatting across unrelated files
- generated files without their source
- implementation before a cross-component contract
- changing a specification silently to match accidental code

When implementation reveals a bad specification, document the mismatch and change the specification deliberately.

## 21. Serviceability acceptance gates

Before a milestone is complete:

- a new developer can run demo mode from the README
- all checks run with one documented command
- the important request path can be traced by ID
- external providers can be replaced with fakes
- configuration can explain active behavior
- migrations reproduce the database
- failure messages identify a useful next step
- no personal credentials are required for ordinary tests
- protocol examples validate against current schemas
- the owner-facing tutorial for the new concept exists
- no unexplained framework or infrastructure component remains

