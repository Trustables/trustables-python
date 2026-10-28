import json
from pathlib import Path
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from trustables import Trustables, TrustablesError, PollTimeoutError, verify_webhook
ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT/'contract/simulator-cases.json').read_text())
VECTOR = json.loads((ROOT/'contract/webhook-vector.json').read_text())


class ClientTests(unittest.TestCase):
    def server(self, handler, environment='simulator'):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self): self.respond()
            def do_POST(self): self.respond()
            def respond(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
                requests.append(dict(method=self.command, path=self.path, headers={k.lower():v for k,v in self.headers.items()}, body=json.loads(body) if body else None))
                status, value, headers = handler(requests[-1], len(requests))
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                for k,v in headers.items(): self.send_header(k,v)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def cleanup(): server.shutdown(); server.server_close(); thread.join()
        self.addCleanup(cleanup)
        client = Trustables(base_url=f'http://127.0.0.1:{server.server_port}', api_key='fixture-key', org_id='org', environment=environment, allow_insecure_localhost=True)
        return client, requests

    def test_widget_and_qr_routes_and_environment_guards(self):
        client, requests = self.server(lambda *_: (200, {'status': 'pending'}, {}), 'sandbox')
        client.get_widget_review('a/b')
        client.activate_widget('a/b')
        client.get_widget_status('a/b')
        client.cancel_widget('a/b')
        client.create_qr('https://merchant.example/handoff#opaque', size=240)
        self.assertEqual([(r['method'], r['path']) for r in requests], [
            ('GET', '/api/v1/rp/orgs/org/sessions/a%2Fb/widget'),
            ('POST', '/api/v1/rp/orgs/org/sessions/a%2Fb/widget'),
            ('GET', '/api/v1/rp/orgs/org/sessions/a%2Fb/widget/status'),
            ('POST', '/api/v1/rp/orgs/org/sessions/a%2Fb/widget/cancel'),
            ('POST', '/api/v1/rp/orgs/org/qr')])
        self.assertTrue(all(r['headers']['x-trustables-environment']=='sandbox' for r in requests))
        self.assertEqual(requests[-1]['body']['size'],240)
        simulator, unused = self.server(lambda *_: (200, {}, {}))
        with self.assertRaises(ValueError): simulator.activate_widget('a')
        self.assertEqual(unused, [])

    def test_private_http_requires_explicit_opt_in(self):
        opts=dict(base_url='http://api.internal:8000',api_key='test',org_id='org',environment='sandbox')
        with self.assertRaises(ValueError): Trustables(**opts)
        with self.assertRaises(ValueError): Trustables(**opts,allow_insecure_localhost=True)
        Trustables(**opts,allow_insecure_http=True)
        with self.assertRaises(ValueError): Trustables(**{**opts,'base_url':'http://user:password@api.internal'},allow_insecure_http=True)

    def test_all_simulator_flows(self):
        for fixture in CASES:
            with self.subTest(scenario=fixture['scenario']):
                campaign = dict(id='campaign', name='SDK test', purpose='contract test', profile='pid', mode='simulator', simulated=True)
                session = dict(session_id=fixture['result']['session_id'], authorization_request_url='https://assigned.example/review#opaque', expires_at=fixture['result']['expires_at'], mode='simulator', simulated=True, billable=False)
                client, requests = self.server(lambda req, _: (200, campaign if req['path'].endswith('/campaigns') else session if req['path'].endswith('/session') else fixture['result'], {}))
                self.assertEqual(client.create_simulator_campaign(dict(name='SDK test', purpose='contract test', profile='pid')), campaign)
                self.assertEqual(client.create_session(campaign['id']), session)
                self.assertEqual(client.complete_simulator('fixture-capability', fixture['scenario']), fixture['result'])
                self.assertEqual(client.get_session(session['session_id']), fixture['result'])
                self.assertEqual(requests[0]['headers']['authorization'], 'Bearer fixture-key')
                self.assertEqual(requests[0]['headers']['x-trustables-environment'], 'simulator')
                self.assertEqual(requests[0]['path'], '/api/v1/rp/orgs/org/simulator/campaigns')
                self.assertEqual(requests[0]['method'], 'POST')
                self.assertEqual(requests[1]['path'], '/api/v1/rp/orgs/org/verification-requests/campaign/session')
                self.assertEqual(requests[2]['path'], '/api/v1/rp/simulator/complete')
                self.assertEqual(requests[3]['path'], '/api/v1/rp/orgs/org/sessions/'+session['session_id']+'/status')
                self.assertEqual(requests[1]['method'], 'GET')
                self.assertNotIn('authorization', requests[2]['headers'])
                self.assertNotIn('x-trustables-environment', requests[2]['headers'])
                self.assertEqual(requests[2]['body']['scenario'], fixture['scenario'])
                self.assertTrue(fixture['result']['simulated'])
                self.assertFalse(fixture['result']['billable'])
                self.assertIsNone(fixture['result']['verified_claims'])
                if fixture['scenario'] == 'ineligible':
                    self.assertTrue(fixture['result']['accepted'])
                    self.assertEqual(fixture['result']['claims']['birth_date'], '2026-01-01')

    def test_sandbox(self):
        client, requests = self.server(lambda *_: (200, {'id':'request'}, {}), 'sandbox')
        body = dict(name='Sandbox', purpose='Verify age', credential_type='PID', policy_profile='high', requested_claims=[['age_over_18']], redirect_uri='https://app.example/callback')
        client.create_verification_request(body)
        self.assertEqual(requests[0]['body'], body)
        self.assertEqual(requests[0]['headers']['x-trustables-environment'], 'sandbox')
        with self.assertRaises(ValueError): client.create_simulator_campaign(dict(name='test', purpose='test'))

    def test_errors_no_retry(self):
        for status in [401, 403, 409, 422, 429, 503]:
            with self.subTest(status=status):
                client, requests = self.server(lambda *_: (status, {'detail':'fixture-error'}, {'Retry-After':'7'}))
                with self.assertRaises(TrustablesError) as caught: client.create_session('campaign')
                self.assertEqual(caught.exception.status, status)
                self.assertEqual(caught.exception.detail, 'fixture-error')
                self.assertEqual(caught.exception.retry_after, '7')
                self.assertNotIn('fixture-key', str(caught.exception))
                self.assertEqual(len(requests), 1)

    def test_no_redirect_and_encoded_id(self):
        client, requests = self.server(lambda *_: (302, {}, {'Location':'/unexpected'}))
        with self.assertRaises(TrustablesError): client.get_session('a/b?c')
        self.assertEqual(len(requests), 1)
        self.assertIn('a%2Fb%3Fc', requests[0]['path'])

    def test_polling(self):
        client, requests = self.server(lambda _, n: (200, {'status':'pending'} if n < 2 else CASES[0]['result'], {}))
        self.assertEqual(client.wait_for_session('session', interval=.001), CASES[0]['result'])
        self.assertEqual(len(requests), 2)
        pending, _ = self.server(lambda *_: (200, {'status':'pending'}, {}))
        with self.assertRaises(PollTimeoutError): pending.wait_for_session('session', timeout=.02, interval=.002)

    def test_webhook_backend_vector(self):
        v = VECTOR
        def verify(body=v['body'], path=v['path'], headers=v['headers'], now=v['now']):
            return verify_webhook(v['secret'], v['method'], path, body.encode(), headers, now=now)
        self.assertTrue(verify())
        self.assertFalse(verify(body=v['body']+' '))
        self.assertFalse(verify(path='/wrong'))
        self.assertFalse(verify(now=v['now']+301))
        self.assertFalse(verify(headers={**v['headers'], 'X-Trustables-Signature':'v1=abc'}))
        self.assertTrue(verify(headers={k.lower():v for k,v in v['headers'].items()}))

    def test_invalid_config(self):
        for url in ['http://public.example', 'https://user:pass@example.com', 'https://example.com/path', 'https://example.com?x=1']:
            with self.assertRaises(ValueError): Trustables(base_url=url, api_key='key', org_id='org', environment='simulator')

    def test_socket_timeout_no_retry(self):
        import socket
        import time
        calls = []
        class Stall(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(1)
                time.sleep(.2)
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1',0), Stall)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            client = Trustables(base_url=f'http://127.0.0.1:{server.server_port}',api_key='fixture-key',org_id='org',environment='simulator',allow_insecure_localhost=True,timeout=.03)
            with self.assertRaises((TimeoutError, socket.timeout)): client.create_session('campaign')
            self.assertEqual(len(calls),1)
        finally:
            server.shutdown(); server.server_close(); worker.join()
