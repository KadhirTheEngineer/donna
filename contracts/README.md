# Donna contracts

The versioned JSON Schemas in `schemas/` are the source of truth for messages
that cross the server/client boundary. Sanitized examples live in `examples/`
and are validated by the server and Rust client tests.

`auth-signature.v1.json` contains an intentionally public deterministic test key,
never a production credential. It binds the Python and Rust HMAC canonicalization.

Compatibility rules:

- additive optional fields are permitted within a major version;
- consumers ignore unknown event types and safe unknown fields;
- required-field removal or semantic changes require a new major schema;
- every schema change updates examples and both component contract tests.

Run `python scripts/check_contracts.py` from the repository environment to
validate every checked-in example.
