# Runbook: disk nearly full

1. Inspect the sanitized storage component in `/v1/health`; it reports free GiB
   and the configured 100 GiB floor without exposing a user path.
2. Pause new research and artifact ingestion before space reaches the operating
   reserve. Do not delete user files or database history automatically.
3. Identify Donna-owned growth by category: PostgreSQL, content-addressed
   artifacts, model cache, logs, and client cache. Keep personal paths and file
   names out of shared diagnostics.
4. Apply the reviewed retention/export policy. Deleting immutable artifacts or
   database rows requires a recoverable plan and audit event.
5. Run database maintenance only with measured need and sufficient temporary
   space. Verify backup integrity before any destructive compaction.
6. Confirm health returns above the threshold and exercise a small write plus
   read before resuming background work.
