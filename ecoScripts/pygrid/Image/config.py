import argparse
import ssl


class Config_Arguments:
    def __init__(self, settings):
        self.hostname = settings['controller_hostname']
        self.nodename = settings['node_name']
        self.password = settings['password'] if 'password' in settings else None
        self.description = settings['description'] if 'description' in settings else None
        self.clientcert = settings['client_cert']
        self.clientkey = settings['client_key']
        self.clientkeypassword = settings['client_key_password']
        self.servercert = settings['server_cert']

class Config:
    def __init__(self, settings):
        self.config = Config_Arguments(settings)
    def get_host_name(self):
        return self.config.hostname
    def get_node_name(self):
        return self.config.nodename
    def get_password(self):
        if self.config.password is not None:
            return self.config.password
        else:
            return ''
    def get_description(self):
        return self.config.description

    def get_ssl_context(self):
        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        if self.config.clientcert is not None:
            context.load_cert_chain(certfile=self.config.clientcert,
                                    keyfile=self.config.clientkey,
                                    password=self.config.clientkeypassword)
        context.load_verify_locations(capath=self.config.servercert)
        return context
