import json
import threading
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from time import sleep

import requests
import yaml

# absolute imports
# from consumer.logger import Logger

# relative imports
from ..logger import Logger

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

    def __init__(self, protocol='https'):
        self.logger = Logger.get_logger()

        self.cookie = None
        self.session = requests.Session()
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        # get authentication parameters
        apic_host = os.getenv('APIC_HOSTNAME')
        aci_user = os.getenv('ACI_USERNAME')
        aci_pass = os.getenv('ACI_PASSWORD')

        if protocol != 'https' and protocol != 'http':
            pass # TODO raise error
            # TODO Mohit - Ask above message
        else:
            self.base_url = "{0}://{1}".format(protocol, apic_host)

        self.login_payload = {'aaaUser': {'attributes':{'pwd': aci_pass, 'name': aci_user}}}

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
            self.logger.info("Retrying")
            response = self.session.request(method, url, **kwargs)

        return response
