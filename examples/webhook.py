import json
from trustables import verify_webhook

def authenticate_event(raw_body, headers, secret):
    """Call from your HTTP handler before JSON parsing."""
    if not verify_webhook(secret, 'POST', '/webhooks/trustables', raw_body, headers):
        raise ValueError('Invalid webhook')
    event = json.loads(raw_body)
    # Before returning 2xx: validate event/organisation/session, durably record and
    # deduplicate Idempotency-Key. Simulator events are never identity evidence.
    return event
