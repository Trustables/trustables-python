import os
from config import client
api = client('simulator')
campaign_id = os.environ.get('TRUSTABLES_CAMPAIGN_ID') or api.create_simulator_campaign({'name':'SDK example','purpose':'Test integration outcomes','profile':'pid'})['id']
print('Save campaign ID for reuse:', campaign_id)
session = api.create_session(campaign_id)
assert session['simulated'] and session['mode'] == 'simulator' and session['billable'] is False
# Capability-bearing URL: show only to the test participant; never log in production.
print('Open privately in your browser and complete the hosted flow:', session['authorization_request_url'])
result = api.wait_for_session(session['session_id'], timeout=300)
print({'session_id':result['session_id'], 'status':result['status'], 'simulated':result['simulated']})
# accepted=True does not establish business eligibility; apply your own policy.
