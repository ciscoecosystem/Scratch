import json
import threading
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from time import sleep

import requests
import yaml

# absolute imports
# from app.logger import Logger

# relative imports
from .logger import Logger



class APIC:
    """Interface for HTTP requests to APIC
    Manages logins and session cookies
    """
    __apic = None

    @classmethod
    def get_apic(cls):
        if cls.__apic == None:
            cls.__apic = APIC()
        return cls.__apic

    def __init__(self):
        self.logger = Logger.get_logger()

        self.cookie = None
        self.session = requests.Session()
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        with open(filename, 'r') as stream:
            creds = yaml.safe_load(stream)
        self.base_url = creds['aci_ip']
        self.login_payload = {'aaaUser': {'attributes':{'pwd': creds['aci_password'], 'name': creds['aci_username']}}}

    def close(self):
        return self.session.close()

    def refresh(self):
        self.logger.info("Refreshing APIC token")
        return self.request('GET', "/api/aaaRefresh.json")

    def login(self):
        self.logger.info("Logging into APIC")
        url = self.base_url + "/api/aaaLogin.json"
        return self.session.request('POST', url, data=json.dumps(self.login_payload), verify=False)

    def logout(self):
        self.logger.info("Logging out of APIC")
        url = self.base_url + "/api/aaaLogout.json"
        return self.session.request('GET', url, verify=False)

    def request(self, method, url, **kwargs):
        kwargs['verify'] = False
        url = self.base_url + url

        response = self.session.request(method, url, **kwargs)
        if response.status_code == 403:
            self.logger.error("APIC request failed.  Attempting login")
            self.login()
            response = self.session.request(method, url, **kwargs)
        elif response.status_code == 400:
            self.logger.error("Request failed: {}".format(response.text))

        return response
