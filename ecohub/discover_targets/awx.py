from os import getenv
import requests.packages.urllib3
from pigeon import Pigeon
from requests import Session

requests.packages.urllib3.disable_warnings()
pigeon = Pigeon()

REQUIRED_ENVS = [
    'AWX_ENDPOINT',
    'AWX_TOKEN'
]
VALID_ACTIONS = [
    'TEST_CONNECTIVITY'
]


class AWX(object):
    def __init__(self, endpoint, token):
        self.session = Session()
        self.session.headers.update({
            'Authorization': 'Bearer ' + token
        })
        self.session.verify = False
        self.uri = 'https://' + endpoint + '/api/v2/'

    def test_connectivity(self):
        resp = self.session.get(self.uri + 'job_templates')
        session.delete()
        if resp.status_code != 200:
            return {'status': 'error', 'message': 'Unable to reach AWX with provided credentials'}
        return {'status': 204, 'message': 'Connectivity verified'}

def ensure_requirements():
    missing_vars = []
    for requirement in REQUIRED_ENVS:
        if not getenv(requirement):
            missing_vars.append(requirement)
    if len(missing_vars) > 0:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'The following required ENV variables are missing: %s' % ', '.join(missing_vars)
        })
        exit()

def test_connectivity():
    try:
        awx = AWX(
            endpoint=getenv('AWX_ENDPOINT'),
            token=getenv('AWX_TOKEN')
        )
        resp = awx.test_connectivity()
        pigeon.sendUpdate(resp,last=True)
        return
    except Exception as e:
        pigeon.sendUpdate({
            'status': 'error',
            'message' : 'An exception occurred while testing connectivity: {}'.format(str(e)),
            'data' : {}
        })

ensure_requirements()
if getenv('ACTION').upper() in VALID_ACTIONS:
    pigeon.sendInfoMessage('Starting action: %s for type: %s' % (getenv('ACTION'), getenv('TARGET_TYPE')))
    options = {
        'TEST_CONNECTIVITY': test_connectivity,
    }
    result = options[str(getenv('ACTION')).upper()]()
else:
    pigeon.sendUpdate({
        'status': 'unknown',
        'message': 'ACTION: %s for TARGET_TYPE: %s not implemented' % (getenv('ACTION'), getenv('TARGET_TYPE'))
    })