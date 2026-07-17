# Runbook: PostgreSQL unavailable

1. Read `/v1/health` and retain the request and trace IDs. Production startup
   refuses to substitute ephemeral storage when durable adapters are required.
2. Confirm PostgreSQL is running locally. Donna permits only a loopback DSN and
   never logs the DSN or accepts a password embedded in it.
3. Set the development `DONNA_DATABASE_DSN` without putting it in process
   arguments. Run `scripts\migrate.cmd`; checksum mismatch means migration
   history changed and must not be bypassed.
4. Query `service.schema_migrations` and verify every checked-in version is
   present. Do not edit a recorded migration or mutate tables manually.
5. Check free disk and PostgreSQL logs for the exact startup failure. Preserve
   the data directory; do not reinitialize it as a repair.
6. After recovery, restart Donna and verify a previously paired test device can
   authenticate and replay events. If not, restore from the last verified backup
   rather than silently re-pairing every production device.

The project-local PostgreSQL cluster used by machine integration tests is
disposable and is not a production backup or service configuration.
