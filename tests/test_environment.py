import unittest
from unittest.mock import patch
from trustables import Environment, Trustables


class EnvironmentTests(unittest.TestCase):
    def test_enum_and_legacy_strings_send_identical_headers(self):
        for environment in (Environment.SIMULATOR, Environment.SANDBOX, 'simulator', 'sandbox'):
            with self.subTest(environment=environment):
                api = Trustables(base_url='https://api.example', api_key='fixture', org_id='org', environment=environment)
                with patch.object(api._opener, 'open') as request:
                    request.return_value.__enter__.return_value.read.return_value = b'{}'
                    api.get_session('session')
                    self.assertEqual(request.call_args.args[0].get_header('X-trustables-environment'), str(environment))

    def test_invalid_and_unavailable_values_fail_before_network(self):
        self.assertEqual(Environment('production'), Environment.PRODUCTION)
        for value in ('Simulator', '', 'sandbx', None, [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Invalid environment'):
                Trustables(base_url='https://api.example', api_key='fixture', org_id='org', environment=value)
        for value in ('production', Environment.PRODUCTION):
            with self.assertRaisesRegex(ValueError, 'Production is not supported'):
                Trustables(base_url='https://api.example', api_key='fixture', org_id='org', environment=value)
