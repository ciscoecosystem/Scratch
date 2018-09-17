"""
This script is set up to fetch data from Tetration (SCOPES).

It returns one of those as a  list in the 'data' portion of an ecohub pigeon
message. It takes this format:
[
    {'label': 'item1', 'value': 'item1'},
    {'label': 'item2', 'value': 'item2'},
    {'label': 'item3', 'value': 'item3'}
]

Keyword environment variables:
--APPSCOPE_NAME: name of scope from which we want to retrieve all IP addresses
--TETRATION_ENDPOINT: URL of the Tetration UI
--TETRATION_API_KEY: key for Tetration API access
--TETRATION_API_SECRET: secret for the above key
--VCENTER_HOST: hostname or IP address for vCenter
--VCENTER_USER: username with proper capabilities in vCenter
--VCENTER_PWD: password for vCenter
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

# pylint: disable=invalid-name

import os
import ssl
import json

import requests.packages.urllib3
from tetpyclient import RestClient
requests.packages.urllib3.disable_warnings()

TARGET_ITEM = os.environ['FETCH_TARGET']

# =============================================================================
# Functions
# -----------------------------------------------------------------------------

def tet_connect():
    ''' Connects to Tetration using params stored in environment variables. '''
    return RestClient(
            os.environ['TETRATION_ENDPOINT'],
            api_key=os.environ['TETRATION_API_KEY'],
            api_secret=os.environ['TETRATION_API_SECRET'],
            verify=False
        )

def tet_get_roles():
    ''' Returns list of all ROLES '''
    restclient = tet_connect()
    resp = restclient.get('/openapi/v1/roles')
    return sorted([ x["name"] for x in resp.json() ])


# =============================================================================
# Main
# -----------------------------------------------------------------------------

# Display the name of the target being fetched

# pigeon = {
#     "status_code": 100,
#     "data": [],
#     "message": "Starting to fetch {}...".format(TARGET_ITEM)
# }
# print json.dumps(pigeon)

# Start with a large IF statement that checks for the possible values for
# the FETCH_TARGET environment variable.

if TARGET_ITEM == 'ROLES':
    roles = tet_get_roles()
    fetched = [{'label': x, 'value': x} for x in roles]

else:
    fetched = []

# Format the pigeon to return results to ecohub. If nothing was found (data
# contains an empty list), then that must be an error.
if len(fetched):
    pigeon = {
        "status_code": 200,
        "data": fetched,
        "message": "Fetching {} and found {} items.".format(TARGET_ITEM, len(fetched))
    }
else:
    pigeon = {
        "status_code": 400,
        "data": [],
        "message": "Unabled to fetch '{}'.".format(TARGET_ITEM)
    }

# send the pigeon... if DEBUG is enabled, then send it with indentation;
# otherwise send it as minified JSON
if os.getenv('DEBUG'):
    print json.dumps(pigeon, indent=4)
else:
    print json.dumps(pigeon)