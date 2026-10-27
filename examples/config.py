import os
from trustables import Trustables

def required(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f'Set {name}')
    return value

def client(environment):
    return Trustables(base_url=required('TRUSTABLES_BASE_URL'), api_key=required('TRUSTABLES_API_KEY'), org_id=required('TRUSTABLES_ORG_ID'), environment=environment)
