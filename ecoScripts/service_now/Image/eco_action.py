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
    pigeon.sendInfoMessage("Starting mongo")
    subprocess.Popen(["mongod", "--config", "/etc/mongod.conf"], stdout=subprocess.DEVNULL).wait()
    # time.sleep(0.5) # TODO remove or figure out, giving server time to startup

    pigeon.sendInfoMessage("Starting action")
    if os.environ['ACTION'] == 'TEST_CONNECTIVITY':
        subprocess.call(["python", "test_connectivity.py"])
    elif os.environ['ACTION'] == 'VALIDATE':
        subprocess.call(["python", "test_connectivity.py"])
    elif os.environ['ACTION'] == 'RUN_INTEGRATION':
        subprocess.call(["python", "run_integration.py"])
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

subprocess.Popen(["mongo", "127.0.0.1/admin", "--eval", "db.shutdownServer()"], stdout=subprocess.DEVNULL)

# print a message that the container has completed its work
pigeon.sendInfoMessage("Container is stopping.")
