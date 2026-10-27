"""Opt-in live acceptance; a person selects each outcome in the hosted UI."""
from datetime import datetime, timezone
from config import client, required
api = client('simulator')
campaign_id = required('TRUSTABLES_CAMPAIGN_ID')
for scenario, status, accepted in [('approved','completed',True),('consent_rejected','failed',False),('missing_attributes','failed',False),('ineligible','completed',True),('timeout','expired',False)]:
    session = api.create_session(campaign_id)
    print(f'Open privately and select {scenario}:', session['authorization_request_url'])
    result = api.wait_for_session(session['session_id'], timeout=300)
    assert result['session_id'] == session['session_id']
    assert result['status'] == status and result['accepted'] is accepted
    assert result['mode'] == 'simulator' and result['simulated'] is True
    assert result['billable'] is False and result['verified_claims'] is None
    assert result['trust_status'] == 'not_evaluated'
    if not accepted: assert result['failure_reason'] == scenario
    if scenario == 'missing_attributes': assert 'birth_date' not in result['claims']
    if scenario == 'ineligible': assert result['claims']['birth_date'] == datetime.now(timezone.utc).date().isoformat()
    print(f'Passed {scenario}')
