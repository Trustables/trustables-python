# Changelog

## 0.1.4

- Default to https://api.trustables.de with an optional base URL override.
- Use /v1 customer API routes and consistent TRUSTABLES_ example settings.

## 0.1.3

- Add opt-in, bounded retries for transient status polling errors, respecting Retry-After and the overall deadline.
- Keep authentication failures and all session creation single-attempt.


## 0.1.2

- Export typed Environment values and validate environment configuration at startup.
- Preserve supported string values and reject unavailable Production explicitly.
- Document typed setup and update integration examples.

## 0.1.0 (unreleased)

Private preview: typed integration client, explicit Simulator/Sandbox routing, polling, webhook verification, shared contract fixtures and runnable examples. No public package release or production support.
