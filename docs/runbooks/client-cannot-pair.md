# Runbook: client cannot pair

1. Check `GET http://127.0.0.1:8742/v1/health` on the laptop. If unreachable,
   start the demo service and retain the response request ID.
2. Create a new code with `python -m donna_server pairing-code`. Codes are
   single-use and expire after the configured TTL.
3. Verify the client server URL matches the laptop API. Do not put the code or
   issued credential in command arguments, logs, chat, or configuration.
4. Run `donna pair` and enter the new code at its prompt.
5. If platform credential storage fails, inspect the safe error category and
   confirm the user session can access its credential manager. Do not fall back
   to a plaintext credential file.
6. In demo mode, server restart intentionally loses enrollment; pair again. In
   production, this symptom means the PostgreSQL identity adapter is unhealthy
   and production startup should already have refused readiness.
