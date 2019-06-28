"""
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

__author__ = "Brandon Beck"
__copyright__ = "Copyright (c) 2019 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.0"

import os
import re
import logging
import logging.handlers
import threading
import csv
from tempfile import NamedTemporaryFile
from threading import Thread
from collections import deque
from time import sleep, time
import tempfile
import argparse
import getpass
import yaml

from pxgrid import PxgridControl
from config import Config
import urllib.request
import base64
import json

import asyncio
from asyncio.tasks import FIRST_COMPLETED
import sys
from websockets import ConnectionClosed
from ws_stomp import WebSocketStomp

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from tetpyclient import MultiPartOption, RestClient

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ====================================================================================
# Globals
# ------------------------------------------------------------------------------------
SETTINGS_FILE = 'config/settings.yml'


# ====================================================================================
# Logging
# ------------------------------------------------------------------------------------
root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

LOG_FILENAME = os.path.dirname(os.path.realpath("__file__")) + "/logs/py-grid.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level

        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())

        def flush(self):
            pass

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)


class StoppableThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class Track(StoppableThread):
    def __init__(self, settings):
        super(Track, self).__init__()
        self.daemon = True
        self.settings = settings
        self.log = deque([], maxlen=10)
        self.annotations = {}
        self.sgt_tags = {}
        self.lock = threading.Lock()
        self.config = Config(settings)
        self.pxgrid = PxgridControl(config=self.config)
        while self.pxgrid.account_activate()['accountState'] != 'ENABLED':
            sleep(60)
        self.get_trustsec_definitions()

    def reset(self):
        self._stop_event = threading.Event()

    def run(self):
        th = Thread(target=self.upload_annotations)
        th.daemon = True
        th.start()
        self.th = th
        self.track()

    def pxgrid_query(self, url, secret, payload):
        handler = urllib.request.HTTPSHandler(context=self.config.get_ssl_context())
        opener = urllib.request.build_opener(handler)
        rest_request = urllib.request.Request(url=url, data=str.encode(payload))
        rest_request.add_header('Content-Type', 'application/json')
        rest_request.add_header('Accept', 'application/json')
        b64 = base64.b64encode((self.config.get_node_name() + ':' + secret).encode()).decode()
        rest_request.add_header('Authorization', 'Basic ' + b64)
        rest_response = opener.open(rest_request)
        content = json.loads(rest_response.read().decode())
        print('  response status=' + str(rest_response.getcode()))
        return content

    def get_trustsec_definitions(self):
        logger.info("Getting all trustsec definitions")
        service_lookup_response = self.pxgrid.service_lookup('com.cisco.ise.config.trustsec')
        service = service_lookup_response['services'][0]
        node_name = service['nodeName']
        url = service['properties']['restBaseUrl'] + '/getSecurityGroups'
        secret = self.pxgrid.get_access_secret(node_name)['secret']
        content = self.pxgrid_query(url, secret, '{}')
        self.sgt_tags.clear()
        for d in content['securityGroups']:
            self.sgt_tags[d['name']] = {
                "tag": str(d['tag'])
            }
    
    def get_all_sessions(self):
        logger.info("Getting all sessions")
        service_lookup_response = self.pxgrid.service_lookup('com.cisco.ise.session')
        service = service_lookup_response['services'][0]
        node_name = service['nodeName']
        url = service['properties']['restBaseUrl'] + '/getSessions'
        secret = self.pxgrid.get_access_secret(node_name)['secret']
        content = self.pxgrid_query(url, secret, '{}')
        try:
            self.lock.acquire()
            for session in content['sessions']:
                for ip in session['ipAddresses']:
                    self.annotations[ip] = {
                        'sgt_user': session['userName'] if 'ctsSecurityGroup' in session.keys() else None,
                        'sgt_tag_name': session['ctsSecurityGroup'] if 'ctsSecurityGroup' in session.keys() else None
                    }
        finally:
            logger.info(json.dumps(self.annotations,indent=4))
            self.lock.release()

    def upload_annotations(self):
        logger.debug('Inside upload annotations!')
        restclient = RestClient(
            self.settings["tetration_endpoint"],
            api_key=self.settings["tetration_api_key"],
            api_secret=self.settings["tetration_api_secret"],
            verify=False)
        # sleep for 30 seconds to stagger uploading

        fieldnames = [ a['column_name'] for a in self.settings['annotations'].values() if a['enabled'] ]
        if len(fieldnames) == 0:
            logger.warn('No annotation columns are enabled!')
            return
        fieldnames.insert(0, "IP")

        while True:
            if self.stopped():
                logger.info("Cleaning up annotation thread")
                return
            if self.annotations:
                tag_names = list(set([a['sgt_tag_name'] for a in self.annotations.values() ]))
                missing_tags = False
                for tag in tag_names:
                    if tag not in self.sgt_tags.keys():
                        missing_tags = True
                        break
                if missing_tags:
                    self.get_trustsec_definitions()
                for k in self.annotations:
                    self.annotations[k]['sgt_tag_id'] = self.sgt_tags[self.annotations[k]['sgt_tag_name']]['tag'] if self.annotations[k]['sgt_tag_name'] else None
                try:
                    # Acquire the lock so we don't have a sync issue
                    # if an endpoint receives an event while we upload
                    # data to Tetration
                    self.lock.acquire()
                    logger.info(json.dumps(self.annotations,indent=4))
                    logger.info("Writing Annotations (Total: %s) " % len(
                        self.annotations))
                    with open('annotations.csv', 'w') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for k,v in self.annotations.items():
                            row = {
                                'IP': k
                            }
                            for key in [ k for k in v.keys() if self.settings['annotations'][k]['enabled'] ]:
                                row[self.settings['annotations'][key]['column_name']] = v[key]
                            writer.writerow(row)
                    req_payload = [
                        MultiPartOption(
                            key='X-Tetration-Oper', val='add')
                    ]
                    logger.debug('/openapi/v1/assets/cmdb/upload/{}'.format(self.settings["vrf"]))
                    resp = restclient.upload(
                        'annotations.csv', '/openapi/v1/assets/cmdb/upload/{}'.format(
                            self.settings["vrf"]), req_payload)
                    if resp.ok:
                        logger.info("Uploaded Annotations")
                        self.log.append({
                            "timestamp": time(),
                            "message":
                            "{} annotations".format(len(self.annotations))
                        })
                        self.annotations.clear()
                    else:
                        logger.error("Failed to Upload Annotations")
                        logger.error(resp.text)
                finally:
                    self.lock.release()
            else:
                logger.debug("No new annotations to upload")
            logger.debug("Waiting {} seconds".format(int(self.settings["frequency"])))
            sleep(int(self.settings["frequency"]))

    async def future_read_message(self, ws, future):
        try:
            message = await ws.stomp_read_message()
            future.set_result(message)
            return True
        except ConnectionClosed:
            logger.info('Websocket connection closed')

    async def subscribe_loop(self, config, secret, ws_url, topic, pubsub_node_name):
        ws = WebSocketStomp(ws_url, config.get_node_name(), secret, config.get_ssl_context())
        await ws.connect()
        await ws.stomp_connect(pubsub_node_name)
        await ws.stomp_subscribe(topic)
        # setup keyboard callback
        stop_event = asyncio.Event()
        while True:
            future = asyncio.Future()
            future_read = self.future_read_message(ws, future)
            await asyncio.wait([stop_event.wait(), future_read], return_when=FIRST_COMPLETED)
            message = json.loads(future.result())
            logger.info('Reading session updates')
            try:
                self.lock.acquire()
                for session in message['sessions']:
                    for ip in session['ipAddresses']:
                        self.annotations[ip] = {
                            'sgt_user': session['userName'] if 'ctsSecurityGroup' in session.keys() else None,
                            'sgt_tag_name': session['ctsSecurityGroup'] if 'ctsSecurityGroup' in session.keys() else None
                        }
            finally:
                self.lock.release()

    def track(self):
        logger.info("Collecting existing sessions")
        self.get_all_sessions()
        # lookup for session service
        service_lookup_response = self.pxgrid.service_lookup('com.cisco.ise.session')
        service = service_lookup_response['services'][0]
        pubsub_service_name = service['properties']['wsPubsubService']
        topic = service['properties']['sessionTopic']

        # lookup for pubsub service
        service_lookup_response = self.pxgrid.service_lookup(pubsub_service_name)
        pubsub_service = service_lookup_response['services'][0]
        pubsub_node_name = pubsub_service['nodeName']
        secret = self.pxgrid.get_access_secret(pubsub_node_name)['secret']
        ws_url = pubsub_service['properties']['wsUrl']

        asyncio.get_event_loop().run_until_complete(self.subscribe_loop(self.config, secret, ws_url, topic, pubsub_node_name))

def main():
    """
    Main execution routine
    """
    settings = yaml.load(open(SETTINGS_FILE), Loader=yaml.Loader)

    tracker = Track(settings)
    tracker.run()

if __name__ == '__main__':
    main()