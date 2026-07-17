# Orchestrator implementation specification

Status: normative implementation contract

This document defines the first orchestrator implementation. It refines docs/system-spec.md. When the two disagree, update both before implementation.

## 1. Scope

The orchestrator converts requests into typed, policy-checked, durable work. It is not a free-running autonomous loop and is not allowed to execute model-generated text as code.

The first implementation supports:

- deterministic commands
- conversation without tools
- typed planning
- registered read tools
- durable research jobs
- approval suspension and resumption
- cancellation
- model and tool telemetry

Write tools, Google mutations, client file changes, shell execution, and computer system actions are added only after the policy and approval path is proven.

## 2. Package boundaries

Suggested Python package:

    donna_server/
      api/             FastAPI routes and event transport
      auth/            device identity and scopes
      commands/        deterministic intent grammar
      orchestrator/    request normalization, planning, execution
      inference/       Ollama adapter, registry, prompts, schemas
      policy/          allow, ask, deny evaluation
      tools/           typed registry and executors
      jobs/            durable leases, workers, cancellation
      connectors/      Google and market providers
      research/        retrieval, extraction, source handling
      storage/         database and artifact repositories
      events/          transactional outbox and WebSocket fanout
      telemetry/       traces, metrics, and redaction

Domain code does not import FastAPI request objects or the Ollama client directly. It depends on typed interfaces.

## 3. Request lifecycle

Every request follows:

1. authenticate device
2. assign request ID and trace ID
3. normalize text, target, locale, and client context
4. apply deterministic command router
5. if unmatched, classify with a structured model response
6. choose synchronous conversation or durable planned job
7. build bounded context
8. produce and validate a typed plan when tools are required
9. evaluate policy before every effect
10. execute one step
11. validate and persist the observation
12. checkpoint and emit an event
13. continue, wait for approval, or finish
14. create stable findings and a user-facing result

The API handler persists the request and returns. Long execution never remains attached to an ordinary HTTP request.

## 4. Deterministic command router

Known low-latency commands are parsed before model inference.

Inputs:

- normalized transcript or typed text
- source device
- selected target device
- active CLI view and selected entity

Outputs:

- matched boolean
- typed intent
- typed parameters
- confidence from deterministic parsing rules
- ambiguity reason when not executable

Initial intents:

- view.open
- view.back
- view.scroll
- view.select
- dashboard.refresh
- research.pause
- research.resume
- research.cancel
- task.complete
- device.suspend

Rules may use exact phrases, aliases, constrained slots, and entity lookup. They may not use fuzzy matching for consequential targets unless the result is unique.

## 5. Core records

Request:

- request_id
- trace_id
- actor_device_id
- target_device_id
- text
- input_kind
- client_context
- created_at
- status

Classification:

- domain
- intent
- sensitivity
- urgency
- expected_duration
- required_capabilities
- requires_plan
- confidence
- ambiguity

Plan:

- plan_id
- request_id
- schema_version
- objective
- completion_criteria
- assumptions
- budgets
- ordered steps
- created_by_model_digest
- prompt_template_version

Plan step:

- step_id
- kind
- capability
- typed arguments
- dependencies
- expected_output_schema
- policy_effect
- timeout_seconds
- retry_policy
- status

Observation:

- step_id
- tool identity and version
- sanitized input hash
- output artifact or typed output
- source references
- started_at and completed_at
- status and error category

Finding:

- statement
- evidence IDs
- inference boolean
- confidence label
- contradiction IDs
- freshness

## 6. Plan constraints

A plan is rejected unless:

- schema validation succeeds
- all tools exist in the registry
- argument schemas validate
- dependencies reference earlier valid steps
- no cycle exists
- budgets are within policy
- effects are accurately declared
- completion criteria are present
- the plan contains no raw shell or source code in place of a typed operation

Default limits until configured:

- synchronous request: 30 seconds
- interactive plan: 8 steps
- background research plan: 40 steps per checkpointed run
- tool calls: 50 per job before explicit extension
- plan repair attempts: 2
- structured-response repair attempts: 1
- wall-clock research budget: 2 hours
- source retrieval budget: 50 documents
- per-source maximum fetched body: configured and bounded

Limit exhaustion produces a partial result with the exact exhausted budget. It never silently extends itself.

## 7. Tool registry

Each tool declares:

- stable name and version
- description for planning
- Pydantic input and output schemas
- effect class
- required device or connector scope
- foreground and unattended eligibility
- default timeout
- idempotency behavior
- redaction fields
- cancellation support

Tool effect classes:

- read
- create
- modify
- delete
- send
- execute
- system
- financial_transaction

The registry returns a validated proposed call. A separate executor performs the call only after policy evaluation.

Tool output is untrusted data. Web pages, email, files, and tool output cannot redefine the system prompt, policy, plan schema, or tool registry.

## 8. Policy and approval

Policy evaluation receives:

- actor and target
- tool and typed arguments
- effect class
- scope and count
- unattended boolean
- current job
- applicable user policy

Result:

- allow
- ask with preview and effect hash
- deny with stable reason code

An ask result moves the job to waiting_for_approval and commits its checkpoint. Approval is accepted only for the exact effect hash. Any changed arguments require a new preview.

## 9. Execution state machines

Request states:

- received
- classified
- planned
- running
- waiting_for_approval
- completed
- failed
- cancelled

Step states:

- pending
- ready
- running
- waiting_for_approval
- succeeded
- failed
- skipped
- cancelled

Job states are defined in docs/system-spec.md.

Every transition is validated in code and appended as an event. State cannot be changed by directly assigning arbitrary strings.

## 10. Database consistency

Use PostgreSQL transactions for:

- state transition plus event append
- checkpoint plus lease renewal
- approval decision plus runnable-state transition

Use a transactional outbox. WebSocket delivery reads committed outbox events. A process crash may redeliver an event, so clients deduplicate by event ID and sequence.

Workers claim jobs using an expiring lease and row locking. A worker may act only while it owns the lease. External mutations also require an idempotency key because a lease can expire after an external effect but before local commit.

## 11. Retry policy

Errors are categorized:

- validation
- policy_denied
- approval_expired
- authentication
- not_found
- rate_limited
- transient_network
- provider_unavailable
- timeout
- model_invalid_output
- tool_permanent
- cancelled
- internal

Only explicitly retryable categories retry automatically. Default maximum is three attempts with capped exponential backoff and jitter. External mutations retry only when their connector provides an idempotency guarantee or reconciliation proves the effect did not occur.

Model output validation uses at most one repair request. Repeated invalid output fails the step or escalates to a configured stronger model; it never enters an unbounded correction loop.

## 12. Cancellation and pause

Cancellation sets cancel_requested in durable state before signaling a worker.

Workers check cancellation:

- before model inference
- while consuming a stream
- before and after every tool
- before checkpoint commit

No new external effect begins after cancellation is observed. An effect already accepted by an external service is reconciled and reported rather than falsely marked undone.

Pause occurs only at checkpoint-safe boundaries. Waiting for approval is durable and consumes no worker lease.

## 13. Context construction

Context is assembled from typed sources with token budgets:

1. stable system policy
2. task-specific prompt template
3. user request
4. relevant current entities
5. selected prior findings
6. source excerpts with IDs
7. tool schemas required for this step

Conversation history is summarized when needed. Raw history is never concatenated until the context window overflows. Every excerpt retains its source ID, and retrieved content is delimited as untrusted evidence.

## 14. Prompt registry

Prompts are repository files with:

- stable name
- semantic version
- purpose
- expected model role
- input contract
- output schema version
- test fixtures

The database records prompt name, version, model digest, generation options, token counts, and latency for each inference. Prompts are not edited in the database.

## 15. Model roles

Configuration references roles rather than hardcoded model names:

- classifier_fast
- command_fallback
- planner
- conversation
- synthesizer
- extractor
- embedding

Each role has:

- preferred model
- optional fallback model
- required capabilities
- maximum context budget
- generation defaults
- keep-alive class
- concurrency limit

The Windows assessment maps installed models to roles after benchmarks. Missing roles are reported as health degradation, not resolved by silently downloading models.

## 16. Resource priority

Priority order:

1. voice deterministic command
2. interactive typed command
3. approval response
4. interactive conversation
5. connector synchronization
6. background research
7. maintenance and reindexing

Background GPU work yields between inference calls. The scheduler does not assume that Ollama can preempt an active generation. Admission is based on observed loaded-model VRAM and configured headroom.

## 17. Completion

A job completes only when:

- completion criteria have evaluated true or the result is explicitly partial
- no required step remains runnable
- findings have evidence or inference labels
- unresolved contradictions are included
- source and freshness metadata are present
- final output validates
- checkpoint and completion event commit together

## 18. Required tests

- deterministic commands do not call a model
- ambiguous device target does not execute
- invalid plan schema does not reach a tool
- unknown tool does not execute
- policy ask commits before worker release
- changed effect invalidates approval
- duplicate event is harmless
- expired lease cannot commit a step
- cancellation prevents the next effect
- mutation retry cannot duplicate an effect
- prompt injection in a web page cannot add a tool
- malformed model output has a bounded repair path
- job resumes from the last committed checkpoint
- partial budget exhaustion is reported honestly

