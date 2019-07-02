from tetpyclient import RestClient
from os import getenv
import requests.packages.urllib3
from pigeon import Pigeon

requests.packages.urllib3.disable_warnings()
pigeon = Pigeon()

REQUIRED_ENVS = [
    'TETRATION_ENDPOINT',
    'TETRATION_API_KEY',
    'TETRATION_API_SECRET'
]
VALID_ACTIONS = [
    'TEST_CONNECTIVITY'
]

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
    restclient = RestClient(
        'https://%s' % getenv('TETRATION_ENDPOINT'),
        api_key = getenv('TETRATION_API_KEY'),
        api_secret = getenv('TETRATION_API_SECRET'),
        verify = False
    )

    try:
        resp = restclient.get('/inventory/search/dimensions')

    # most likely a DNS issue
    except requests.exceptions.ConnectionError:
        pigeon.sendUpdate({
            'status': 'not-found',
            'message': "Error connecting to Tetration endpoint"
        })
    except:
        pigeon.sendUpdate({
            'status': 'error',
            'message': "Unknown error connecting to Tetration"
        })
    else:
        if resp.status_code == 200:
            try:
                resp.json()
            except:
                pigeon.sendUpdate({
                    'status': 'error',
                    'message': 'Incorrect URL entered'
                })
                exit()
        status = 204 if resp.status_code == 200 else resp.status_code
        return_msg = ''
        if resp.status_code >= 400:
            return_msg = "Tetration " + str(resp.text).rstrip()
        pigeon.sendUpdate({
            'status': status,
            'message': return_msg
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