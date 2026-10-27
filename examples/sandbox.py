import json
from pathlib import Path
from config import client, required
api = client('sandbox')
# Use permitted claims, an approved redirect and your provisioned certificate/instance IDs.
body = json.loads(Path(required('TRUSTABLES_REQUEST_FILE')).read_text())
request = api.create_verification_request(body)
session = api.create_session(request['id'])
assert not session['simulated'] and session['mode'] == 'wallet'
print('Open privately with your test wallet:', session['authorization_request_url'])
result = api.wait_for_session(session['session_id'], timeout=300)
print({'session_id':result['session_id'], 'status':result['status'], 'accepted':result['accepted']})
# Validate verified_claims and business policy; these remain test credentials.
