"""
The purpose of this script is to call other scripts. There are no arguments to
this script. An environment variable named ACTION defines which action should
be taken (which script to run).
"""

import subprocess
from os import getenv
from pigeon import Pigeon

# Python Path
PYTHON_PATH = 'runner/bin/python'

# Define pigeon messenger
pigeon = Pigeon()
VALID_TARGET_TYPES = [
    'ACI_USER',
    'ACI_CERT'
    'TETRATION',
    'AWX'
    ]

if getenv('TARGET_TYPE').upper() in VALID_TARGET_TYPES:
    pigeon.sendInfoMessage('Starting subprocess for: %s' % getenv('TARGET_TYPE'))
    options = {
        'ACI': lambda : subprocess.call(["%s" % PYTHON_PATH, "aci.py"]),
        'TETRATION': lambda : subprocess.call(["%s" % PYTHON_PATH, "tetration.py"]),
        'AWX': lambda : subprocess.call(["%s" % PYTHON_PATH, "awx.py"]),
    }
    result = options[str(getenv('TARGET_TYPE')).upper()]()
else:
    pigeon.sendInfoMessage('ECO_ACTION FAILED')
    pigeon.sendUpdate({
        'status': 'unknown',
        'message': 'Target Type: ' + getenv('TARGET_TYPE') + 'not implemented'
    })

# print a message that the container has completed its work
pigeon.sendInfoMessage('Action complete')
