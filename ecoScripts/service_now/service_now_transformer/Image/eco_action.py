import subprocess
import os
import json
import glob
import time

from pigeon import Pigeon

pigeon = Pigeon()

def print_message(message):
    '''
    prints a JSON object with indentation if the DEBUG environment variable
    is set and without indentation if it is not set
    '''
    if os.getenv('DEBUG'):
        print(json.dumps(message, indent=4))
    else:
        print(json.dumps(message))

# return a message that the container has started
pigeon.sendInfoMessage("Container has started.")
pigeon.sendInfoMessage(json.dumps(dict(os.environ), indent=2))

if os.getenv('ACTION'):
    
    # time.sleep(0.5) # TODO remove or figure out, giving server time to startup

    pigeon.sendInfoMessage("Starting action")
    if os.environ['ACTION'] == 'TEST_KAFKA_CONNECTIVITY':
        subprocess.call(["python", "validate.py", "kafka"])
    elif os.environ['ACTION'] == 'TEST_ES_CONNECTIVITY':
        subprocess.call(["python", "validate.py", "es"])
    elif os.environ['ACTION'] == 'TEST_FLINK_CONNECTIVITY':
        subprocess.call(["python", "validate.py", "flink"])
    elif os.environ['ACTION'] == 'VALIDATE':
        subprocess.call(["python", ".py"])
    elif os.environ['ACTION'] == 'RUN_INTEGRATION':
        subprocess.call(["python", "run_integravalidatetion.py"])
    elif os.environ['ACTION'] == 'CUSTOM':
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Requested action CUSTOM not implemented.'
        })
    else:
        pigeon.sendUpdate({
            'status': 404,
            'message': 'Requested action not recognized.'
        })

else:
    pigeon.sendUpdate({
        'status': 404,
        'message': 'The ACTION environment variable is not defined.'
    })


# print a message that the container has completed its work
pigeon.sendInfoMessage("Container is stopping.")
