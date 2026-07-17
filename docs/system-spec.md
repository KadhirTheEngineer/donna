# Donna system specification

Status: working specification

This document is the source of truth for Donna. It captures the intended product, system boundaries, interfaces, safety model, performance targets, and planned physical controller. Proposed changes should update this document before implementation when they alter a cross-component contract.

## 1. Product definition

Donna is a private, local-first personal secretary whose primary compute host is a Windows gaming laptop with:

- Intel Core i7-10750H, 6 cores
- NVIDIA RTX 2070 with 8 GB VRAM
- 64 GB DDR4 memory
- at least 100 GB dedicated local storage
- Ollama already installed

Donna provides:

- a persistent Rust terminal dashboard on the desktop and MacBook
- Google Calendar, Google Tasks, and Gmail awareness
- local LLM conversations and tool use
- durable background research
- macroeconomic, company, equity, portfolio, and market context
- guarded file, shell, email, calendar, and task actions
- low-latency voice control
- remote control of connected Donna CLIs
- an optional handheld physical controller

The product name, assistant name, and executable name are Donna and donna.

## 2. Core principles

1. The gaming laptop performs all substantial computation.
2. Personal content is not sent to a hosted LLM.
3. Clients remain thin, responsive, and useful when temporarily disconnected.
4. Known commands use deterministic routes instead of an LLM.
5. Long work is durable, resumable, inspectable, and cancellable.
6. Every consequential effect is governed by explicit policy.
7. Evidence and deterministic calculations remain separate from LLM interpretation.
8. Stale, partial, inferred, delayed, and failed data is visibly labeled.
9. Infrastructure is added only when a measured need justifies it.
10. The user can understand what Donna is doing and why.

## 3. Privacy boundary

Donna-owned prompts, inference, embeddings, indexes, email summaries, research notebooks, portfolio state, and audit records remain on user-controlled devices.

This does not make upstream services local:

- Google processes information already held in Gmail, Calendar, and Tasks.
- websites see normal research requests from the laptop
- market-data providers receive symbol and data requests
- Tailscale, if selected, coordinates device networking but cannot decrypt WireGuard data traffic

Raw microphone audio is processed on the gaming laptop. By default it is transient and is not stored. A setting may explicitly enable recordings for meeting transcription.

## 4. System topology

### 4.1 Gaming laptop

The laptop hosts:

- FastAPI edge service
- device enrollment and authentication
- REST API and WebSocket event stream
- Google connectors and OAuth tokens
- orchestrator and deterministic command router
- durable job scheduler and workers
- Ollama model registry and inference router
- local speech recognition
- browser research workers
- finance data ingestion and calculations
- PostgreSQL
- content-addressed artifact storage
- approval state and audit log

### 4.2 Desktop and MacBook

Each computer hosts:

- Donna Rust TUI
- encrypted persistent connection to the laptop
- cached non-sensitive dashboard snapshot
- optional narrowly scoped local companion
- approved-workspace file tool runner
- constrained local system-action adapter

Clients do not host an LLM, embedding model, speech recognizer, Google OAuth token, crawler, or research database.

### 4.3 Handheld controller

The optional controller is a thin input and display device:

- captures microphone audio
- streams audio to the laptop
- sends buttons and rotary-encoder events
- displays small structured cards
- remotely controls a selected Donna CLI
- receives short responses and approval prompts

It holds a revocable device credential but no Google, brokerage, email, or Ollama credentials.

## 5. Terminal application

### 5.1 Visual direction

The target is a clean OLED-dark interface:

- true black base background
- near-black elevated surfaces
- restrained borders
- high-contrast text
- one primary accent and limited semantic colors
- low visual noise
- visible focus without large bright regions
- no assumption that terminal pixels map to fixed rows and columns

The primary window is approximately 1080 by 1080 pixels. Donna uses current terminal cell dimensions and recomputes the layout on every resize.

Representative validation sizes include:

- 120 by 55 cells
- 100 by 45 cells
- 90 by 40 cells
- 70 by 25 cells
- explicit minimum-size fallback

### 5.2 Dashboard widgets

The overview includes:

- daily briefing
- next calendar events
- due and high-priority tasks
- email attention queue
- active and recent research jobs
- markets and watchlist
- laptop connection and sync freshness
- active model and compute activity
- pending approvals

### 5.3 Expanded views

Expanded views are full information screens, not merely larger widgets.

Calendar includes:

- day and agenda views
- time, duration, location, calendar, attendees, and description
- conflicts and travel or preparation warnings
- create, move, cancel, and RSVP previews

Tasks includes:

- inbox, project, due-date, and priority grouping
- completion, defer, edit, and creation actions
- origin and last synchronization state

Mail includes:

- sender, thread, received time, labels, and attachments
- why Donna surfaced it
- concise local summary
- thread preview
- draft, reply, archive, and mark-state actions

Research includes:

- request and acceptance criteria
- honest progress and current activity
- checkpoint timeline
- findings and contradictions
- primary and secondary sources
- citations, retrieval time, and content freshness
- pause, resume, cancel, and extend controls

Markets includes:

- dashboard sparklines
- full line and candlestick charts
- volume
- selectable intraday and historical periods
- moving averages and benchmark comparison
- price, change, high, low, open, close, and volume
- delayed or partial-feed label
- company metrics, filings, earnings, news, risks, and catalysts
- watchlist and manually entered portfolio exposure

### 5.4 Input

The TUI supports:

- keyboard navigation
- focused views
- command and conversation palette
- remote typed actions from the server
- remote navigation actions from the handheld
- visible permission and connection state

Remote control invokes typed application actions. It does not emulate arbitrary keystrokes.

## 6. Voice system

### 6.1 Modes

Version one supports push-to-talk on desktop, MacBook, and handheld.

Optional later modes:

- wake phrase followed by a command
- dictation
- meeting recording and transcription
- spoken response playback

Push-to-talk is the default because release provides an exact utterance endpoint, reduces false activation, saves handheld battery, and makes privacy obvious.

### 6.2 Audio path

1. Client captures mono microphone audio.
2. Client streams audio immediately over the encrypted connection.
3. Laptop performs voice activity detection and partial transcription.
4. On button release, the laptop finalizes the transcript.
5. Deterministic router attempts to match a known intent.
6. Policy engine evaluates the typed effect.
7. Laptop dispatches the action to the target device or domain service.
8. Clients receive transcript, status, result, and cancellation events.

The client performs only capture, buffering, and transport framing. Speech recognition remains on the laptop.

### 6.3 Speech models

Initial candidate:

- Faster-Whisper Small or an equivalent distilled model for interactive commands

Optional quality routes:

- Medium for important dictation
- quantized large model for offline recordings

Model selection is finalized only after benchmarking the RTX 2070 under simultaneous Ollama workload.

### 6.4 Latency service objective

For a preauthorized known command such as suspend:

- local network transport: 5 to 50 ms
- speech endpoint: immediate on push-to-talk release
- transcription finalization: target 150 to 600 ms
- deterministic routing: target under 30 ms
- policy evaluation: target under 10 ms
- action delivery: target 5 to 50 ms
- target action initiation: under 500 ms

Product objective: begin an eligible known action within two seconds of button release, with a stretch target below one second.

These are targets until measured on the real laptop.

### 6.5 Deterministic command lane

Frequent commands bypass the general LLM:

- open a Donna view
- navigate or scroll a connected CLI
- show an entity
- refresh data
- create or complete a simple task
- start a timer
- suspend an enrolled computer
- pause, resume, or cancel a research job

Ambiguous or compound requests go to the orchestrator:

- suspend after a particular download finishes
- move a meeting while avoiding conflicts
- research several companies and compare valuation assumptions

## 7. Remote CLI control

Each running CLI maintains a WebSocket event connection to the laptop.

The laptop tracks:

- device ID and friendly name
- online state
- last activity
- active view and selected entity
- supported capabilities
- controller-selected target

Target resolution:

1. An explicitly named device wins.
2. Otherwise use the handheld's selected target.
3. Otherwise use the most recently active eligible CLI.
4. Consequential actions show the resolved target.

Examples:

- Pull up my calendar.
- Show the latest research on my desktop.
- Open this email on the MacBook.
- Scroll down.
- Go back.
- Open the second result.
- Show this on the big screen.

Representative server event:

    type: client.action.requested
    target_device_id: desktop
    action: view.open
    parameters:
      view: calendar
      entity_id: optional

A closed CLI cannot receive events. A later local companion may launch or focus Donna, but it exposes only a small fixed action set and never arbitrary remote shell access.

## 8. Handheld controller specification

### 8.1 Recommended first prototype

- Raspberry Pi Zero 2 W
- 1.3 to 2.0 inch OLED
- digital I2S MEMS microphone
- central push-to-talk button
- rotary encoder with click
- back or cancel button
- one or two contextual action buttons
- physical microphone mute switch
- optional vibration motor
- optional small speaker
- rechargeable battery and purpose-built charging and protection board
- charging dock
- handheld enclosure

The original Pi Zero W offers lower power draw but is not preferred because its single-core processor leaves less headroom for encrypted audio streaming and responsive UI work. A future Pico-class design may improve battery life after the interaction model is stable.

### 8.2 Handheld interface

Home cards:

- next event
- urgent task
- important-email count
- research progress
- market alert
- pending approval
- selected target device
- controller battery and connection

Conversation cards show:

- live or final transcript
- Donna's short response
- action target
- countdown and cancellation option
- open-on-desktop handoff

Encoder behavior:

- rotate to select or scroll
- click to open or confirm
- long click to return home
- target-selection screen chooses desktop, MacBook, handheld, or all eligible displays

### 8.3 Power behavior

- screen sleeps after inactivity
- audio streams only during push-to-talk by default
- idle status updates are coalesced
- static OLED content shifts or blanks to reduce burn-in
- hardware input wakes the interface
- actual battery life is measured on the assembled prototype

## 9. Security model

Apartment Wi-Fi is considered untrusted.

### 9.1 Recommended network

Preferred:

- Tailscale on laptop, desktop, MacBook, and handheld
- access rules limited to enrolled Donna devices and service ports
- Donna application-level enrollment remains enabled

Alternative:

- Donna-managed mutual TLS over the LAN
- one-time pairing code
- per-device certificate
- certificate rotation and revocation

IP allowlisting may be an additional filter but is never the primary identity mechanism.

### 9.2 Device enrollment

1. Laptop displays a short-lived pairing code.
2. New client creates a private device key locally.
3. Pairing exchanges identity and capability metadata.
4. Laptop records the device and issues scoped credentials.
5. Device appears in a human-readable inventory.
6. User can revoke it independently.

No bearer credential is placed in a command-line argument or log. Device private keys use the platform credential store when available.

### 9.3 Transport

- TLS 1.3 preferred
- mutual device authentication
- request nonce and timestamp
- idempotency key for mutations
- replay rejection
- encrypted audio, events, commands, and approvals
- reconnection with event-sequence replay

## 10. Permission model

Decisions are allow, ask, or deny.

Policy dimensions:

- requesting device
- target device or connector
- tool and operation
- read, create, modify, delete, send, execute, or system effect
- approved workspace or account
- foreground or unattended execution
- scope and estimated blast radius

Guarded defaults:

- read synchronized personal data: allow
- read approved files: allow
- write files: ask
- delete files: ask
- send email: ask
- modify calendar or tasks: ask
- run shell command: ask
- purchases and trades: deny

YOLO mode may promote eligible actions inside explicit workspaces. It never removes:

- workspace boundaries
- audit logging
- secret redaction
- purchase and trading prohibition
- confirmation for destructive or unrecoverable actions

Exact convenience actions may be preauthorized per device:

- navigate Donna: allow
- show calendar: allow
- suspend desktop by voice: configurable allow
- restart or shut down: ask by default
- arbitrary shell from handheld: deny

Fast consequential actions may display a short cancellation countdown without requiring a full confirmation.

## 11. Orchestrator

The orchestrator is a typed workflow engine:

The normative implementation details are in docs/orchestrator-spec.md and docs/ollama-interface.md.

1. normalize request
2. classify domain, intent, sensitivity, urgency, and expected duration
3. choose deterministic route or planned route
4. load relevant context only
5. generate typed plan, budgets, and completion criteria
6. evaluate policy per step
7. execute or enqueue
8. validate results
9. checkpoint
10. produce stable findings and dashboard objects

Models cannot invoke raw tools directly. Model output proposes typed operations that code validates before policy evaluation.

## 12. Durable research

Jobs survive service and laptop restarts.

States:

- queued
- leased
- running
- waiting for approval
- paused
- succeeded
- failed
- cancelled

Every job records:

- immutable original request
- acceptance criteria
- priority and deadline
- source and compute budgets
- worker lease and heartbeat
- checkpoints
- retry category
- findings and contradictions
- citations and retrieval timestamps
- cancellation state

Begin with a PostgreSQL queue using row locking and expiring leases. Do not add Redis until measured contention or specialized scheduling requires it.

## 13. Compute scheduler

Work classes:

- CPU light
- CPU heavy
- GPU interactive
- GPU batch
- browser network

Voice and direct interaction receive priority over background research.

The scheduler:

- measures actual VRAM use
- keeps a fast interactive model warm when practical
- admits only compatible GPU workloads
- pauses batch inference between units for interactive work
- unloads or changes models when an 8 GB limit would be exceeded
- reports active compute state to clients

## 14. Google integration

OAuth and tokens live only on the laptop.

Google Calendar:

- incremental synchronization
- multiple calendar support
- create, move, update, cancel, and RSVP previews

Google Tasks:

- lists, tasks, due dates, completion, and edits
- preserves Google identifiers and synchronization state

Gmail:

- metadata-first incremental synchronization
- fetches bodies only when needed
- attention scoring and explanation
- thread summaries
- draft, reply, send, archive, and label previews

Connector mutations are idempotent and reconciled with remote state.

## 15. Markets and financial intelligence

Initial scope:

- macroeconomic research
- watchlists
- manually entered portfolio positions
- company and equity research
- historical and delayed market visualization
- no brokerage trading
- no purchases

Alpaca is the initial market-data candidate. The free tier is sufficient for early historical charts and personal watchlists, with clear labeling that live free stock data is IEX rather than the complete consolidated market.

Finance records preserve:

- provider and feed
- symbol and security identity
- value and unit
- observed period
- market timestamp
- retrieval timestamp
- adjustment method
- delayed or partial coverage

Company research prioritizes:

- SEC filings
- investor relations material
- earnings releases and transcripts
- government and central-bank data
- deterministic revenue, margin, cash flow, balance sheet, dilution, and valuation calculations

Donna presents evidence, assumptions, scenarios, risks, and missing information. It does not issue or execute buy or sell instructions.

## 16. Storage

PostgreSQL is the source of truth for:

- devices and identity
- connector state
- personal synchronized objects
- conversations
- jobs and checkpoints
- sources and extracted facts
- finance observations
- policies and approvals
- audit events

Large immutable artifacts use content-addressed local storage. Database rows reference hashes. Retention, export, backup, and deletion controls are required before storing large personal archives.

## 17. Protocol requirements

REST handles snapshots, queries, mutations, approvals, and pagination.

WebSocket handles:

- invalidation
- streaming assistant text
- voice transcript updates
- client actions
- research progress
- approval requests
- device presence

All events include:

- event ID
- sequence
- timestamp
- type
- source and target device where applicable
- resource ID
- trace ID
- typed data

Mutation requests include an idempotency key and effect hash.

## 18. Reliability and observability

Clients:

- clearly mark disconnected and stale data
- cache only appropriate snapshots
- reconnect with event sequence
- request a fresh snapshot when replay retention expires

Server records:

- trace ID
- typed plan
- policy decision
- redacted tool parameters
- tool result hashes and timing
- model and prompt-template versions
- source provenance
- approvals
- compute and token usage

Secrets, cookies, OAuth tokens, raw email bodies, and raw microphone audio are excluded from ordinary logs.

## 19. Build phases

### Phase A: TUI design revision

- OLED theme
- richer expanded screens
- charts and financial detail
- remote-action reducer
- voice and device status surfaces

### Phase B: read-only laptop service

- FastAPI and PostgreSQL
- device pairing and encrypted events
- dashboard snapshot
- Google Calendar, Tasks, and Gmail read-only sync
- Rust reconnect and stale-state handling

### Phase C: low-latency voice

- push-to-talk client capture
- audio stream
- Faster-Whisper benchmark
- deterministic intent lane
- transcript and cancellation UX
- GPU priority scheduling

### Phase D: remote control and guarded actions

- target-device registry
- typed remote CLI actions
- policy and approval engine
- email, calendar, and task mutations
- approved file workspaces
- constrained shell and system adapters

### Phase E: durable research and finance

- persistent jobs and browser workers
- source archive and citations
- company research schema
- Alpaca historical data and charts
- portfolio and macro views

### Phase F: handheld prototype

- Pi Zero 2 W client
- OLED cards and encoder navigation
- push-to-talk
- target selection and desktop handoff
- battery and latency measurement
- enclosure revision

### Phase G: hardening

- backup and restore
- retention and export
- device revocation testing
- failure injection
- permission bypass tests
- signed client builds
- Tailscale remote access

## 20. Acceptance targets

- TUI remains legible across supported terminal sizes.
- Voice known-command action begins within two seconds of push-to-talk release.
- Navigational handheld command changes a connected CLI within 250 ms after classification.
- Restart loses no committed connector state or job checkpoint.
- Consequential replay does not duplicate an effect.
- Every financial figure exposes source, unit, period, and freshness.
- Every material research claim has a citation or is labeled inference.
- Unknown devices cannot access Donna.
- Revoked devices cannot reconnect.
- Loss of network never displays cached data as current.

## 21. Deferred decisions

These require prototype measurements or user selection:

- exact OLED accent palette and information density
- speech model after RTX 2070 benchmarks
- whether spoken replies are required
- wake-word implementation and default state
- Tailscale versus Donna-managed mutual TLS for first deployment
- market chart timeframes and technical indicators
- exact handheld display, microphone, battery, and enclosure
- whether a background desktop companion may launch Donna
- portfolio import format
- retention periods for email bodies, web snapshots, and recordings
