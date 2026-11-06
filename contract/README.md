# Shared contract 0.2.0

Source: Trustables/trustables, `apps/docs/generate_openapi.py::generate_sdk`.
Export with `python apps/docs/sdk/export.py /path/to/sdk` from that repository
following schema regeneration. Regenerate language types and run the SDK tests.
Do not edit snapshots or generated types independently. Backend contract changes
require reviewed snapshot updates in both SDK repositories; no automatic releases.

Simulator fixtures are extracted from backend pure helpers at a fixed UTC clock.
They are synthetic contract fixtures, not evidence of a live wallet exchange.

OpenAPI SHA-256: `3f123faea8440f2ce6ff199b49b1ff420243c09519a43fef6a6b8b7462270155`
