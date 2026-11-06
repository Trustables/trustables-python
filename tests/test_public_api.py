import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from trustables import Trustables


class PublicApiTests(unittest.TestCase):
    def test_default_origin_and_versioned_authenticated_request(self):
        for environment in ('simulator', 'sandbox'):
            with self.subTest(environment=environment), patch('trustables.client.build_opener') as build:
                build.return_value.open.return_value.__enter__.return_value.read.return_value = b'{"status":"pending"}'
                client = Trustables(api_key='fixture', org_id='org', environment=environment)
                client.get_session('session')
                request = build.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url, 'https://api.trustables.de/v1/rp/orgs/org/sessions/session/status')
                self.assertEqual(request.get_header('Authorization'), 'Bearer fixture')
                self.assertEqual(request.get_header('X-trustables-environment'), environment)

    def test_example_uses_configured_environment_and_optional_origin(self):
        spec = importlib.util.spec_from_file_location('example_config', Path(__file__).resolve().parents[1]/'examples/config.py')
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        for mode in ('simulator', 'sandbox'):
            with patch.dict(os.environ, {'TRUSTABLES_API_KEY':'fixture', 'TRUSTABLES_ORG_ID':'org', 'TRUSTABLES_ENVIRONMENT':mode}, clear=True), patch.object(config, 'Trustables') as constructor:
                config.client(mode)
                self.assertEqual(constructor.call_args.kwargs['environment'], mode)
                self.assertNotIn('base_url', constructor.call_args.kwargs)
                os.environ['TRUSTABLES_BASE_URL'] = 'https://api.dev.trustables.de'
                config.client(mode)
                self.assertEqual(constructor.call_args.kwargs['base_url'], 'https://api.dev.trustables.de')
        with patch.dict(os.environ, {'TRUSTABLES_ENVIRONMENT':'sandbx'}, clear=True):
            with self.assertRaises(ValueError): config.client('sandbox')
        with patch.dict(os.environ, {'TRUSTABLES_ENVIRONMENT':'sandbox'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'match'): config.client('simulator')
