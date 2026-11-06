import os
from trustables import Environment, Trustables

def required(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f'Set {name}')
    return value

def client(environment):
    configured = Environment(os.environ.get('TRUSTABLES_ENVIRONMENT', environment))
    if configured != environment:
        raise ValueError('TRUSTABLES_ENVIRONMENT must match the selected example')
    options = {'base_url': os.environ['TRUSTABLES_BASE_URL']} if 'TRUSTABLES_BASE_URL' in os.environ else {}
    return Trustables(api_key=required('TRUSTABLES_API_KEY'), org_id=required('TRUSTABLES_ORG_ID'), environment=configured, **options)
