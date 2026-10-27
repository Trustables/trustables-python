import hashlib
import hmac
import math
import re
import time
from collections.abc import Mapping


def verify_webhook(secret: str, method: str, path: str, raw_body: bytes,
                   headers: Mapping[str, str], *, now: float | None = None,
                   tolerance_seconds: float = 300) -> bool:
    """Verify raw bytes; callers must validate the event and durably deduplicate."""
    normalized = {k.lower(): v for k, v in headers.items()}
    timestamp = normalized.get('x-trustables-timestamp', '')
    submission_id = normalized.get('idempotency-key', '')
    signature = normalized.get('x-trustables-signature', '')
    clock = time.time() if now is None else now
    if (not secret or not submission_id or not re.fullmatch(r'[0-9]{1,16}', timestamp)
            or not re.fullmatch(r'v1=[0-9a-f]{64}', signature)
            or not math.isfinite(clock) or not math.isfinite(tolerance_seconds)
            or tolerance_seconds < 0 or abs(clock - int(timestamp)) > tolerance_seconds):
        return False
    canonical = '\n'.join(['v1', timestamp, method.upper(), path,
                           hashlib.sha256(raw_body).hexdigest(), submission_id])
    expected = 'v1=' + hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
