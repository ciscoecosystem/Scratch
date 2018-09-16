"""
The purpose of this script is to call other scripts. There are no arguments to
this script. An environment variable named ACTION defines which action should
be taken (which script to run).

Keyword environment variables:
--ACTION: the purpose for running this container... FETCH, TEST_CONNECTIVITY,
    RUN_INTEGRATION, etc.
--DEBUG: determines if Pigeons are displayed minimized or with indentation to
    make them more readable

The user must supply either a credentials file *OR* the key and secret as
arguments, but not both.

Copyright (c) 2018 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.0 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Doron Chosnek"
__copyright__ = "Copyright (c) 2018 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.0"

import subprocess
import os
import json
import glob

def print_message(message):
    '''
    prints a JSON object with indentation if the DEBUG environment variable
    is set and without indentation if it is not set
    '''
    if os.getenv('DEBUG'):
        print json.dumps(message, indent=4)
    else:
        print json.dumps(message)

# return a message that the container has started
pigeon = {
    "status_code": 100,
    "data": {},
    "message": "Container has started."
}
print_message(pigeon)

if os.getenv('ACTION'):

    if os.environ['ACTION'] == 'VERIFY':
        pigeon['message'] = "Skipping connectivity tests."
        pigeon['status_code'] = 200
    elif os.environ['ACTION'] == 'RUN_INTEGRATION':
        subprocess.call(["python", "get_scope_ips.py"])
        subprocess.call(["pwsh", "Get-Inventory.ps1"])
        subprocess.call(["python", "upload_annotations.py"])
    elif os.environ['ACTION'] == 'CLEAR_CACHE':
        for file in glob.glob("/private/*.txt"):
            os.remove(file)
        for file in glob.glob("/private/*.csv"):
            os.remove(file)
        pigeon['message'] = "Local cache of annotations deleted."
        pigeon['status_code'] = 200
        print_message(pigeon)
    elif os.environ['ACTION'] == 'FETCH_ITEMS':
        subprocess.call(["python", "fetch_items.py"])
    elif os.environ['ACTION'] == 'CUSTOM':
        pigeon['message'] = "Requested action CUSTOM not implemented."
        pigeon['status_code'] = 400
        print_message(pigeon)
    else:
        pigeon['message'] = "Requested action not recognized."
        pigeon['status_code'] = 404
        print_message(pigeon)
else:
    pigeon['message'] = "The ACTION environment variable is not defined."
    pigeon['status_code'] = 404
    print_message(pigeon)

# print a message that the container has completed its work
pigeon['message'] = "Container is stopping."
pigeon['status_code'] = 100
print_message(pigeon)
