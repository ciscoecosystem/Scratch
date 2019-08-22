from os import getenv
from requests import Session, exceptions
import requests.packages.urllib3
from pigeon import Pigeon
import json
import kafka.errors
from kafka import KafkaConsumer

requests.packages.urllib3.disable_warnings()
pigeon = Pigeon()

REQUIRED_ENVS_USERPASS = [
    'APIC_HOSTNAME',
    'ACI_USERNAME',
    'ACI_PASSWORD'
]

REQUIRED_ENVS_CERTIFICATE = [
    'APIC_HOSTNAME',
    'ACI_CERTIFICATE',
    'ACI_PRIVATE_KEY'
]

CONNECTION_TYPES = [
    'USERPASS',
    'CERTIFICATE'
]

VALID_ACTIONS = [
    'TEST_CONNECTIVITY'
]

CERT_PATH = '/tmp/aci_client.crt'
KEY_PATH = '/tmp/aci_key.key'

def ensure_requirements():
    missing_vars = []
    connection_type = getenv('CONNECTION_TYPE')
    if not connection_type or connection_type.upper() not in CONNECTION_TYPES:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'A proper connection type was not defined'
        })
        exit()
    elif connection_type.upper() == 'USERPASS':
        for requirement in REQUIRED_ENVS_USERPASS:
            if not getenv(requirement):
                missing_vars.append(requirement)
    else:
        for requirement in REQUIRED_ENVS_CERTIFICATE:
            if not getenv(requirement):
                missing_vars.append(requirement)
    if len(missing_vars) > 0:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'The following required ENV variables are missing: %s' % ', '.join(missing_vars)
        })
        exit()

def test_connectivity():
    session = Session()
    session.headers.update({
        'Content-Type': "application/json",
        'cache-control': "no-cache",
    })
    session.verify = False

    uri = 'https://%s' % getenv('APIC_HOSTNAME')

    if getenv('CONNECTION_TYPE').upper() == 'USERPASS':
        payload = {
            "aaaUser":{
                "attributes":{
                    "name": getenv('ACI_USERNAME'),
                    "pwd": getenv('ACI_PASSWORD')
                }
            }
        }
    else:
        with open(CERT_PATH) as cert_file:
            cert_file.write(getenv('ACI_CERTIFICATE'))
        with open(KEY_PATH) as key_file:
            key_file.write(getenv('ACI_PRIVATE_KEY'))
        session.cert = (CERT_PATH, KEY_PATH)
    try:
        resp = session.post('%s/api/aaaLogin.json' % uri, data=json.dumps(payload), timeout=10)
        # consumer = KafkaConsumer(getenv('KAFKA_TOPIC'), bootstrap_servers=getenv('KAFKA_IP'))

    # most likely a DNS issue
    except exceptions.ConnectionError or exceptions.ConnectTimeout or exceptions.Timeout:
        pigeon.sendUpdate({
            'status': 'not-found',
            'message': "A connection error occurred while trying to reach the APIC"
        })
    except exceptions.ConnectTimeout or exceptions.Timeout:
        pigeon.sendUpdate({
            'status': 'not-found',
            'message': "A timeout occurred while trying to reach the APIC"
        })
    except exceptions.InvalidURL:
        pigeon.sendUpdate({
            'status': 'error',
            'message': "Invalid hostname entered"
        })
    # except kafka.errors.NoBrokersAvailable as error:
    #     pigeon.sendUpdate({
    #         'status': 'error',
    #         'message': 'Cannot connect to Kafka server'
    #     })
    except:
        pigeon.sendUpdate({
            'status': 'error',
            'message': "Unknown error connecting to APIC"
        })
    else:
        status = 204 if resp.status_code == 200 else resp.status_code
        return_msg = ''
        if resp.status_code >= 400:
            error = resp.json()['imdata'][0]['error']['attributes']
            return_msg = '{code}: {text}'.format(code=error['code'], text=error['text'])
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
