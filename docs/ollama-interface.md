# Ollama interface specification

Status: normative adapter contract

Donna integrates with the local Ollama HTTP API through one internal adapter. No route, connector, or tool calls Ollama directly.

## 1. Boundary

The Ollama endpoint is configured and defaults to:

    http://127.0.0.1:11434

Donna does not expose Ollama directly to the LAN. FastAPI is the authenticated application boundary. Cloud model references are denied by default because Donna's inference requirement is local.

The adapter uses explicit HTTP requests rather than depending on Ollama CLI text output. It may use a maintained HTTP library, but its own typed interface remains stable.

## 2. Required endpoints

Startup and periodic discovery:

- GET /api/version
- GET /api/tags
- POST /api/show
- GET /api/ps

Inference:

- POST /api/chat
- POST /api/embed

The first implementation does not create, pull, copy, or delete models automatically.

## 3. Startup discovery

At startup:

1. call version
2. list installed models
3. fetch show details for configured role candidates
4. record name, digest, size, family, parameter size, quantization, capabilities, and advertised context
5. list loaded models and their observed VRAM and active context
6. validate configured roles
7. publish inference health

Refresh:

- tags and role validation every five minutes
- running-model state before GPU admission and after inference
- immediate refresh after a model-not-found response

Model identity is name plus digest. Metrics and prompt records use the digest so changing a tag cannot silently mix results.

## 4. Adapter methods

The internal interface exposes:

- health()
- discover_models()
- running_models()
- chat_stream(request, cancellation)
- chat_structured(request, schema, cancellation)
- embed(request, cancellation)
- preload(role)
- unload(role)

Callers specify a model role. Only the registry resolves it to an installed model name.

## 5. Chat modes

Interactive conversation:

- POST /api/chat
- stream true
- accumulate content from newline-delimited JSON
- forward safe content deltas to Donna events
- retain final usage and duration fields

Classifiers, plans, extraction, and other structured work:

- POST /api/chat
- stream false
- format set to an explicit JSON schema
- temperature zero unless a tested prompt requires otherwise
- validate with the matching Pydantic model

The schema is also described in the prompt for model grounding. JSON parsing alone is insufficient; Pydantic validation is required.

Ollama-native tool calls are not executed directly in version one. The model produces a typed plan or proposed tool call, Donna validates it, policy evaluates it, and the separate tool executor runs it.

## 6. Thinking output

Thinking output is not stored as ordinary conversation content and is not sent to clients by default.

If a selected model supports configurable thinking:

- reasoning effort belongs to the model-role configuration
- only final content or structured output enters domain state
- telemetry may record that thinking was enabled, not private reasoning text

## 7. Generation configuration

Every call records:

- request and trace IDs
- role
- resolved model name and digest
- prompt name and version
- schema version
- options
- keep_alive
- start and completion time
- load duration
- prompt token count
- generated token count
- evaluation durations
- done reason
- retry count

Generation defaults live in configuration per model role. Individual callers cannot introduce arbitrary generation options.

## 8. Context budgeting

The adapter rejects a request that exceeds the configured role budget before sending it when token estimation is available.

Configured budget is the minimum of:

- role maximum
- tested reliable context
- model advertised context
- scheduler memory policy

Advertised maximum context is not automatically treated as operationally safe on an 8 GB GPU. The Windows benchmark establishes reliable context and VRAM behavior.

Reserve output capacity and safety margin. Context reduction happens in the orchestrator through source selection and summarization, not by silently truncating the start or end of an assembled prompt.

## 9. Keep-alive and GPU memory

Keep-alive classes:

- hot: interactive model, initially 10 minutes
- warm: classifier, initially 5 minutes
- batch: research model, initially 1 minute
- one_shot: unload immediately after completion

These are starting defaults and are benchmark-adjusted.

The adapter passes keep_alive per request. It does not globally change Ollama environment configuration.

Preload uses an empty generation request only when the scheduler has admitted the model. Unload uses keep_alive zero only when no active or queued admitted call needs that model.

## 10. Concurrency

Default until benchmarked:

- one GPU generation at a time
- embeddings serialized with generation when both use GPU
- CPU-only lightweight operations may run concurrently

The scheduler queries running models and observed VRAM. Maintain configurable VRAM headroom for speech recognition and the operating environment.

No component assumes Ollama can preempt a generation. Voice priority prevents new batch calls and requests cooperative cancellation of an active background stream.

## 11. Streaming

The stream parser:

- parses each NDJSON object independently
- accumulates content and any structured fields
- handles a mid-stream object containing error
- emits rate-limited client deltas
- records final done and done_reason
- treats connection close without a final object as incomplete

Partial streamed content is display-only until completion. It is not committed as a final assistant message or used as an authoritative tool instruction.

## 12. Cancellation

Cancellation closes the active HTTP response and marks the call cancelled locally.

Ollama hard-cancellation behavior must be measured on the installed Windows version. Until verified:

- closing a stream is considered best-effort cancellation
- scheduler admission assumes compute may continue briefly
- cancelled output is discarded
- unload is not used as a per-request kill mechanism when it could affect another call
- job state remains cancel_requested until the worker reaches a safe boundary

## 13. Timeouts

Separate timeouts:

- connect: 2 seconds on localhost
- discovery: 5 seconds
- time to first inference byte: role-specific, initially 60 seconds
- interactive idle stream: initially 30 seconds
- structured call total: initially 120 seconds
- background synthesis total: initially 10 minutes
- embedding batch total: initially 120 seconds

Timeout values are configuration with bounded minimums and maximums. A timeout produces a typed error and telemetry.

## 14. Errors and retries

Map Ollama errors into orchestrator categories.

- 400: validation or incompatible request; no automatic retry
- 404: model missing; refresh registry and fail role health
- 429: rate limited; bounded retry
- 500 or 502: provider unavailable; at most one inference retry when no external effect depends on ambiguous output
- malformed successful body: model_invalid_output
- mid-stream error: incomplete, never commit partial response

Structured validation failure receives at most one repair call using the validation errors and original schema. If that fails, use a configured role fallback or fail visibly.

Do not automatically replay an interactive stream after content has reached the user without marking the replacement attempt.

## 15. Embeddings

Embeddings use POST /api/embed with a dedicated embedding role.

Store:

- model digest
- vector dimension
- input content hash
- chunking version
- created time

Vectors from different model digests or dimensions are never mixed in one index generation. Changing the embedding model requires an explicit reindex job.

## 16. Security and redaction

- Ollama remains bound to loopback.
- Prompts are not logged by default.
- Telemetry stores hashes and counts, not personal content.
- Model responses are treated as untrusted until validated.
- Retrieved web, email, calendar, and file content is clearly delimited as data.
- No model output can modify policy, role configuration, or the tool registry.

## 17. Health states

- healthy: endpoint reachable and required roles valid
- degraded: optional role missing, fallback active, or latency threshold exceeded
- unavailable: endpoint unreachable or no conversation role
- resource_blocked: models exist but scheduler cannot safely admit the requested role

Health includes installed Ollama version, role mappings, loaded models, measured VRAM, and last successful inference without exposing prompts.

## 18. Benchmark matrix

On the Windows laptop, measure each candidate role with:

- cold start
- warm start
- short command classification
- structured schema compliance
- 4K, 8K, and practical larger context where supported
- tokens per second
- first-token latency
- peak VRAM
- simultaneous Faster-Whisper Small residency
- cancellation behavior
- keep-alive and unload behavior

Record results in a checked-in sanitized benchmark report. Do not select defaults solely from model parameter count.

## 19. Acceptance tests

- all inference goes through the adapter
- endpoint is never exposed by Donna to a LAN client
- unknown model role fails clearly
- tag digest change is detected
- structured output validates before use
- malformed structured output has one bounded repair
- mid-stream error does not commit a final message
- cancellation discards late output
- timeout releases the worker
- missing model is not silently downloaded
- model metrics include digest and prompt version
- embedding model change cannot mix vector generations

