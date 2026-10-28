# Trustables Python SDK

Server-side preview, version **0.1.0**. Requires Python 3.11+. Preview interfaces may change. Supports Simulator and provisioned Wallet Sandbox access.

## Install

```sh
python -m pip install trustables-sdk
```

## Install and test from source

```sh
git clone https://github.com/Trustables/trustables-python.git
cd trustables-python
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/generate_types.py --language python --check
```

Import `Trustables` and `verify_webhook` from `trustables`; typed request/response models live in `trustables.types`.

## Run the Simulator example

Provide `TRUSTABLES_BASE_URL` (your assigned HTTPS origin, without `/api`),
`TRUSTABLES_ORG_ID`, and `TRUSTABLES_API_KEY` through your secret manager or environment.
Use a Simulator key. Never place keys in browser code or commit an `.env` file.
Optionally set `TRUSTABLES_CAMPAIGN_ID` to reuse an existing campaign; otherwise the
example creates one (the service limits active campaigns).

```sh
python examples/simulator.py
```

The example displays an authorization URL for private, interactive use. Open it
unchanged and complete any hosted review before choosing an outcome. Do not log
these capability URLs in production. Save the session ID on your backend.
Synthetic results have `mode: simulator`, `simulated: true`, `billable: false`
and `verified_claims: null`. `accepted: true` does not imply customer eligibility.

## Wallet Sandbox

Sandbox requires provisioned organisation access, valid test certificates, a
signing instance, an approved redirect URI, permitted claims and a compatible test
wallet. Use a **wallet** API key and select `sandbox` explicitly. Production is not
supported by this preview. Switching headers cannot provision access.

Copy `examples/verification-request.json`, replace its placeholders, and set
`TRUSTABLES_REQUEST_FILE` to that file. Then run:

```sh
python examples/sandbox.py
```

The example creates a verification request and a fresh session, then polls while
you complete the wallet flow. Test credentials do not authorise production actions.
An unprovisioned environment can return `409 sandbox_onboarding_required`.

## Methods and failure handling

The client supports creating wallet requests, creating Simulator campaigns,
starting sessions, reading results, bounded polling, and explicit Simulator
inspect/complete capability calls. Capability calls send **no API key**. A hosted
review token is not a Simulator token; use the hosted browser flow when supplied.

Requests do not retry or follow redirects. Session creation currently uses GET but
creates a new session every time: after a timeout, reconcile the original attempt
before starting another. API errors expose HTTP status, structured detail and
Retry-After; messages do not include keys or response payloads. Treat error details
and returned claims as sensitive. Polling repeats only pending status reads and
stops on completion, failure, expiry, any other terminal status, or its deadline.
The Python client is synchronous; its HTTP timeout is a socket timeout. Polling deadlines are checked between operations and cap the next socket timeout, not a hard wall-clock cancellation of a streaming response.

`examples/webhook.py` demonstrates raw-body signature verification.
Pass the external URL path without a query string. The default timestamp tolerance
is five minutes. After signature verification, validate the event, organisation
and session and durably deduplicate the submission ID before returning success.
The SDK does not maintain a replay database or make eligibility decisions.

## Validation

Default tests run HTTP loopback fixtures for all five Simulator scenarios,
authentication boundaries, errors, redirects, polling and backend-signed webhook
vectors. They require no credentials and do not claim live service acceptance.

For live acceptance, set the same variables and an existing
`TRUSTABLES_CAMPAIGN_ID`, then run:

```sh
python examples/live_simulator.py
```

This explicitly creates five sessions and asks a person to choose each outcome in
the hosted browser. It does not bypass review steps. Live wallet acceptance remains
a separate test with your provisioned Sandbox credentials.

## Shared contract

`contract/openapi.json` and generated language models share version 0.1.0 with the
other SDK. See `contract/README.md` for provenance and the export/update procedure.
Both snapshots must be updated together for API changes. CI checks generated types,
compiles/packages the SDK, and runs tests. Version tags (`vX.Y.Z`) publish through GitHub Actions trusted publishing. Releases must match the package version and belong to `main`; version bumps are reviewed in a pull request before tagging.

Documentation: https://docs.trustables.de/sdks/

## License

MIT — see [LICENSE](LICENSE).
