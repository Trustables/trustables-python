import json
import math
import time
from typing import Any, Literal, cast
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .types import (Campaign, CampaignBody, CreateVerificationRequestBody,
                    VerificationRequestResponse, VerificationSessionResponse,
                    SessionStatusResponse, SimulatorInspect, SimulatorResult)


class TrustablesError(Exception):
    def __init__(self, status: int, detail: Any, retry_after: str | None = None):
        super().__init__(f'Trustables API returned HTTP {status}')
        self.status, self.detail, self.retry_after = status, detail, retry_after


class PollTimeoutError(TimeoutError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Trustables:
    def __init__(self, *, base_url: str, api_key: str, org_id: str,
                 environment: Literal['simulator', 'sandbox'], timeout: float = 10,
                 allow_insecure_localhost: bool = False,
                 allow_insecure_http: bool = False):
        url = urlsplit(base_url)
        local = (allow_insecure_http or (allow_insecure_localhost and url.hostname in {'localhost', '127.0.0.1', '::1'})) and url.scheme == 'http' # explicit trusted-network opt-in
        # Legacy localhost opt-in stays supported.
        if (url.scheme != 'https' and not local) or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in {'', '/'}:
            raise ValueError('base_url must be an HTTPS origin (no path, credentials, query or fragment)')
        if not api_key or '\r' in api_key or '\n' in api_key or not org_id:
            raise ValueError('api_key and org_id are required')
        if environment not in {'simulator', 'sandbox'}:
            raise ValueError('Unsupported environment')
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('timeout must be positive')
        self._base = base_url.rstrip('/')
        self._key = api_key
        self._org_path = '/api/v1/rp/orgs/' + self._id(org_id)
        self._environment, self._timeout = environment, timeout
        self._opener = build_opener(_NoRedirect())

    def _request(self, method: str, path: str, body: Any = None, *, capability: bool = False, timeout: float | None = None) -> Any:
        headers = {'Accept': 'application/json'}
        if not capability:
            headers.update({'Authorization': f'Bearer {self._key}', 'X-Trustables-Environment': self._environment})
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        request = Request(self._base + path, data=data, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=timeout or self._timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read())
                detail = payload.get('detail') if isinstance(payload, dict) else None
            except (ValueError, UnicodeDecodeError):
                detail = None
            finally:
                exc.close()
            raise TrustablesError(exc.code, detail, exc.headers.get('Retry-After')) from None

    def create_verification_request(self, body: CreateVerificationRequestBody) -> VerificationRequestResponse:
        if self._environment != 'sandbox':
            raise ValueError('Wallet verification requires sandbox; use create_simulator_campaign for simulator')
        return cast(VerificationRequestResponse, self._request('POST', self._org_path + '/verification-requests', body))

    def create_simulator_campaign(self, body: CampaignBody) -> Campaign:
        self._require_simulator()
        return cast(Campaign, self._request('POST', self._org_path + '/simulator/campaigns', body))

    def create_session(self, request_id: str) -> VerificationSessionResponse:
        return cast(VerificationSessionResponse, self._request('GET', self._org_path + '/verification-requests/' + self._id(request_id) + '/session'))

    def get_session(self, session_id: str) -> SessionStatusResponse:
        return cast(SessionStatusResponse, self._request('GET', self._org_path + '/sessions/' + self._id(session_id) + '/status'))

    def get_widget_review(self, session_id: str) -> dict[str, Any]:
        self._require_sandbox()
        return self._request('GET', self._org_path + '/sessions/' + self._id(session_id) + '/widget')

    def activate_widget(self, session_id: str) -> dict[str, Any]:
        self._require_sandbox()
        return self._request('POST', self._org_path + '/sessions/' + self._id(session_id) + '/widget', {})

    def get_widget_status(self, session_id: str) -> dict[str, Any]:
        self._require_sandbox()
        return self._request('GET', self._org_path + '/sessions/' + self._id(session_id) + '/widget/status')

    def cancel_widget(self, session_id: str) -> dict[str, Any]:
        self._require_sandbox()
        return self._request('POST', self._org_path + '/sessions/' + self._id(session_id) + '/widget/cancel', {})

    def create_qr(self, data: str, *, size: int = 220) -> dict[str, Any]:
        return self._request('POST', self._org_path + '/qr', {'data': data, 'size': size})

    def _require_sandbox(self) -> None:
        if self._environment != 'sandbox':
            raise ValueError('Widget operations require sandbox environment')

    def inspect_simulator(self, token: str) -> SimulatorInspect:
        self._require_simulator()
        return cast(SimulatorInspect, self._request('POST', '/api/v1/rp/simulator/inspect', {'token': token}, capability=True))

    def complete_simulator(self, token: str, scenario: Literal['approved', 'consent_rejected', 'missing_attributes', 'ineligible', 'timeout']) -> SimulatorResult:
        self._require_simulator()
        return cast(SimulatorResult, self._request('POST', '/api/v1/rp/simulator/complete', {'token': token, 'scenario': scenario}, capability=True))

    def wait_for_session(self, session_id: str, *, timeout: float = 60, interval: float = 1) -> SessionStatusResponse:
        if not math.isfinite(timeout) or not math.isfinite(interval) or timeout <= 0 or interval <= 0:
            raise ValueError('Polling timeout and interval must be positive')
        deadline = time.monotonic() + timeout
        path = self._org_path + '/sessions/' + self._id(session_id) + '/status'
        while time.monotonic() < deadline:
            try:
                result = self._request('GET', path, timeout=min(self._timeout, max(.001, deadline - time.monotonic())))
            except Exception:
                if time.monotonic() >= deadline:
                    raise PollTimeoutError('Session polling deadline reached') from None
                raise
            if result['status'] != 'pending':
                return cast(SessionStatusResponse, result)
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
        raise PollTimeoutError('Session polling deadline reached')

    @staticmethod
    def _id(value: str) -> str:
        if not value or value in {'.', '..'}:
            raise ValueError('Invalid identifier')
        return quote(value, safe='')

    def _require_simulator(self) -> None:
        if self._environment != 'simulator':
            raise ValueError('Simulator operation requires simulator environment')
