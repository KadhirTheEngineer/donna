# Windows compute-station assessment

Assessment date: 2026-07-16

This report records sanitized, reproducible findings from the first read-only
assessment of the laptop that will host Donna. It intentionally omits the
machine name, user name, exact IP addresses, network names, hardware IDs, and
other private identifiers.

## Host

| Item | Observed value |
|---|---|
| Operating system | Windows 11 Home Insider Preview, 64-bit |
| OS build | 26220 (`10.0.26220`) |
| Logical processors | 12 |
| Physical memory | 63.8 GiB |
| Free space on system volume | 392.0 GiB |

The active Wi-Fi adapter has an RFC 1918 private IPv4 address and a private
default gateway. The exact addresses and network identity are deliberately not
checked in. A private-interface bind candidate therefore exists, but the first
service implementation remains loopback-only until transport identity and the
LAN exposure plan have been reviewed.

## GPU

| Item | Observed value |
|---|---|
| GPU | NVIDIA GeForce RTX 2070 with Max-Q Design |
| Dedicated VRAM | 8,192 MiB |
| Driver | 610.47 |
| Reported CUDA compatibility | 13.3 |
| Idle VRAM at assessment | 139 MiB used |

The GPU is the binding resource. Donna should initially admit one GPU inference
at a time and reserve headroom for speech recognition, as required by the
inference specification.

## Local tools and services

| Tool | Observed state |
|---|---|
| Python | 3.11.9 |
| Git | 2.24.1.windows.2 |
| Ollama | 0.30.11, running and reachable on loopback |
| Rust / Cargo | Not installed or discoverable on `PATH` or in the standard per-user Rust location |
| PostgreSQL / `psql` | Not installed or discoverable on `PATH` or under the standard Program Files location |
| Faster-Whisper | Not installed in the available Python environment |
| PyTorch | Not installed in the available Python environment |

Missing optional integrations must degrade independently. Rust and PostgreSQL
are real implementation prerequisites, but no system-wide installation or OS
configuration was attempted during this assessment.

## Ollama inventory

Endpoint: loopback default (`http://127.0.0.1:11434`). No Donna service should
proxy or expose this endpoint directly.

Model storage uses the ordinary per-user Ollama model store and consumes
approximately 13.51 GiB. The private absolute user-profile path is omitted.

| Model | Digest prefix | Parameters | Quantization | Advertised context | Capabilities |
|---|---|---:|---|---:|---|
| `qwen3:8b` | `500a1f067a9f` | 8.2B | Q4_K_M | 40,960 | completion, tools, thinking |
| `qwen3:14b` | `bdbd181c33f2` | 14.8B | Q4_K_M | 40,960 | completion, tools, thinking |

No models were downloaded, copied, or deleted. Neither installed model advertises
an embedding capability, so the `embedding` role is currently missing.

## Bounded Ollama benchmark

Method: Ollama `/api/chat`, non-streaming structured JSON, thinking disabled,
temperature zero, 2,048-token context, 64-token output cap, and a 33-token
classification prompt. A cold request followed by a warm request was run for
each installed model. Schema validity means the returned object parsed and
contained the required typed fields. Results are indicative rather than a full
quality evaluation.

| Model | State | Wall time | Load time | Output | Generation rate | Schema valid |
|---|---|---:|---:|---:|---:|---|
| `qwen3:8b` | cold | 6.50 s | 5.82 s | 17 tokens | 44.61 tok/s | yes |
| `qwen3:8b` | warm | 0.56 s | 0.18 s | 17 tokens | 49.07 tok/s | yes |
| `qwen3:14b` | cold | 14.04 s | 11.36 s | 17 tokens | 7.75 tok/s | yes |
| `qwen3:14b` | warm | 2.65 s | 0.20 s | 17 tokens | 7.42 tok/s | yes |

At a 2,048-token context, the 14B model reported 9.13 GiB total loaded size and
5.90 GiB in VRAM; NVIDIA reported 6,294 MiB total VRAM use. The model therefore
spills into system memory and is substantially slower. The 8B model reported a
4.91 GiB loaded size and is the current candidate for interactive conversation,
classification, planning, extraction, and initial synthesis roles. This is a
provisional mapping until schema-quality and larger-context tests are complete.

## Speech benchmark status

A Faster-Whisper benchmark was not possible during the read-only inventory:
neither Faster-Whisper nor its runtime is installed, and no speech-model files
were discovered through the available Python environment. This is an explicit
benchmark prerequisite, not evidence that the GPU cannot run speech recognition.

Before selecting a speech default, use a repository-local, pinned benchmark
environment and sanitized audio fixtures to measure Small (or a comparable
distilled model) for cold/warm latency, real-time factor, peak VRAM, transcript
quality, cancellation, and simultaneous residency with `qwen3:8b`. Do not change
drivers, global CUDA packages, or Ollama configuration for this benchmark.

## Initial role and dependency recommendation

- Map all non-embedding roles to `qwen3:8b` initially, with role-specific prompt,
  context, timeout, and keep-alive configuration. Do not make the tag a domain
  dependency; resolve it through the single inference adapter by digest.
- Leave `qwen3:14b` unassigned by default. It may be evaluated later as an
  explicitly admitted batch synthesizer when latency is unimportant.
- Report the missing embedding and speech roles as degraded health. Never
  download a replacement silently.
- Build the laptop service as the specified Python modular monolith, with a
  project-local locked environment and fake adapters for ordinary development.
- Keep PostgreSQL behind repository interfaces and migrations. Development and
  demo modes must remain runnable without a live database; production readiness
  still requires installing PostgreSQL through a separately reviewed host plan.
- Keep the API bound to loopback during development. A future LAN bind must use
  authenticated device identity and encrypted transport, not the observed IP as
  identity.

## Reproduction notes

The inventory used Windows CIM queries, `nvidia-smi`, executable discovery, disk
statistics, and Ollama's version, tags, show, and process APIs. The benchmark
used only installed models and transient inference requests. It made no registry,
firewall, service, startup, package-manager, or system configuration changes.
