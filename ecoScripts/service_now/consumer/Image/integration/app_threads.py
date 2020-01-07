"""
TODO:
1. Writing to Error topic should be configurable/optional. A flag should be set true/false.
2. Add comments with format expected for every message
3. Transfer all the APIC api caller function to another file
4. Create a overloader function to all the API call functions. It should check for the status and pass Success or failure message
"""

import json
import os
import threading
import pymongo
import pymongo.errors
import requests
import yaml
from pymongo import MongoClient

# absolute import
# from consumer.apic import APIC
# from consumer.logger import Logger
# from consumer.database import Database

# relative imports
from .apic import APIC
from .logger import Logger
from .database import Database
from .kafka_utility import kafka_utils


class AuroraThread(threading.Thread):
    """Base thread class; initializes logging and exit conditions"""

    def __init__(self, exit, lock):
        super(AuroraThread, self).__init__()
        self.logger = Logger.get_logger()
        self.exit = exit
        self.lock = lock


class APICThread(AuroraThread):
    """Logs into APIC and refreshes session cookies every 270 seconds"""

    def __init__(self, exit, lock):
        super(APICThread, self).__init__(exit, lock)

    def run(self):
        with self.lock:
            apic = APIC.get_apic()

        login_response = apic.login()
        if login_response.status_code != 200:
            apic.logger.error('Unable to login into APIC.  Error: {}'.format(login_response.text))
            apic.logger.error("Shutting down")
            self.exit.set()
            return

        self.exit.wait(270) # initial login just occurred, no need to refresh immediately; essentially a do-while
        while not self.exit.is_set():
            apic.refresh()
            self.exit.wait(270)

        apic.logout()
        apic.close()
        self.logger.info("APIC thread exited successfully")


class CheckpointException(Exception):
    """Raise exception with the checkpointing message"""

    def __init__(self,  error_type, final_dest, msg, error_msg):
        self.data = {
            'error_type' : error_type,
            'final_dest' : final_dest,
            'msg'        : msg,
            'error_msg'  : error_msg
        }


class ConsumerThread(AuroraThread):
    """Class for consumer thread.

    Set up APIC, Kafka consumer, and database and wait for messages on Kafka
    Take each message and process them based on message type
    """
    PARENT_SCHEMA = 'schema/ParentSchema.avsc'
    CHILD_SCHEMA = {'ep':'schema/APICEpSchema.avsc','epg':'schema/APICEpgSchema.avsc','contract':'schema/APICContractSchema.avsc'}
    def __init__(self, exit, lock):
        super(ConsumerThread, self).__init__(exit, lock)

    def set_config(self):
        # Reading configuration from environment variables
        self.config = {}
        self.config['tenant'] = os.getenv('TENANT_NAME')
        self.config['application_profile'] = os.getenv('AP_NAME')
        self.config['mongo_host'] = os.getenv('MONGO_HOST')
        self.config['mongo_port'] = int(os.getenv('MONGO_PORT'))


    def get_epg_from_db(self, key):
        epg = self.db.get_epg(key)
        if epg is None:
            self.logger.error('Epg not found')
            raise Exception("Epg not found")
        return epg


    def run(self):
        self.logger.info("Reading configuration from file")
        self.set_config()

        try:
            self.logger.info("Connecting to Kafka server")
            self.kafka_utils = kafka_utils()
            self.kafka_utils.create_kafka_client()
            topic = self.kafka_utils.get_consumer_input_topic()
            self.kafka_utils.create_consumer_topic(topic,auto_offset_reset=-2,reset_offset_on_start=True,consumer_group= 'test')
            self.logger.info("Successfully connected to Kafka")

            self.logger.info("Connecting to MongoDB")
            self.db = Database(host=self.config['mongo_host'], port=self.config['mongo_port'])
            self.logger.info("Successfully connected to MongoDB")
        except Exception as error:
            self.logger.error(str(error))
            self.exit.set()
            self.logger.info("Consumer thread exiting")
            return

        with self.lock:
            self.apic = APIC.get_apic()

        self.logger.info("Waiting for messages from Kafka")
        self.consumer = self.kafka_utils.get_consumer()
        while not self.exit.is_set():
            # This is for commit sync in Kafka.
            
            for msg in self.consumer:
                self.logger.info("Received message from Kafka")
                self.process_message(msg)
                if self.exit.is_set():
                    break
        self.logger.info("Closing Kafka consumer")
        self.kafka_utils.get_consumer().close()
        self.logger.info("Consumer thread exited successfully")
        
    def process_message(self, msg):
        """Take msg as string and get dictionary
        Do basic key/value processing and call appropriate function for message type
        """
        try:
            try:
                props = self.kafka_utils.unparse_avro_from_kafka(msg, self.PARENT_SCHEMA,True)
                category = props['category']
                del props['category']
                props = self.kafka_utils.unparse_avro_from_kafka(props['result'], self.CHILD_SCHEMA.get(category),False)                                 
                props['_id'] = props['uuid']
                status = props['status']
                del props['uuid'], props['status']
            except Exception as e:
                raise CheckpointException('Parsing', 'APIC and DB', msg, "Some error occurred while processing endpoint message, Error: {}".format(str(e)))
            
            if category == 'ep':
                self.logger.info("Received endpoint message")
                self.process_endpoint_message(props, status)
            elif category == 'epg':
                self.logger.info("Received grouping message")
                self.process_grouping_message(props, status)
            elif category == 'contract':
                self.logger.info("Received contract message")
                self.process_contract_message(props, status)
            else:
                self.logger.error("Received invalid message type")
        except CheckpointException as e:
            self.logger.error("Dumping message to error topic {}".format(str(e.data)))
            error_topic = self.kafka_utils.get_consumer_error_topic()
            self.kafka_utils.create_producer_topic(error_topic)
            self.kafka_utils.write_data(str.encode(str(e.data)))


    def process_endpoint_message(self, props, status):
        """Process endpoint message"""

        try:
            tenant = self.config['tenant']
            ap = self.config['application_profile']

            if status == 'create' or status == 'update':
                endpoint = self.db.get_endpoint(props['_id'])
                if not endpoint:
                    self.db.insert_endpoint(props)
                    self.logger.info("Added endpoint {} to DB".format(props['name']))
                    epg_name = self.get_epg_from_db(props['epg'])['name']
                    ep_res = self.create_ep(tenant, ap, epg_name, props)
                    if ep_res == 'Successful':
                        self.logger.info('Successfully created EP in APIC')
                    else:
                        self.logger.error('EP creation failed for EP {}, Error: {}'.format(endpoint, ep_res))
                        raise CheckpointException('EP', 'APIC', props, ep_res)
                else:
                    self.db.update_endpoint(props['_id'], {'$set': props})
                    self.logger.info("Updated endpoint {} in DB".format(props['name']))

                    if props['epg'] != endpoint['epg']:
                        # For update, first delete and then create
                        
                        epg_name = self.get_epg_from_db(props['epg'])['name']
                        ep_res_del = self.create_ep(tenant, ap, epg_name, props, delete=True)
                        if ep_res_del == 'Successful':
                            self.logger.info('Successfully deleted EP in APIC')
                        else:
                            self.logger.info('EP deletion failed for EP {}, Error: {}'.format(endpoint, ep_res_del))
                            raise CheckpointException('EP', 'APIC', props, ep_res_del)
                        epg_name = self.get_epg_from_db(props['epg'])['name']
                        ep_res = self.create_ep(tenant, ap, epg_name, props)
                        if ep_res == 'Successful':
                            self.logger.info('Successfully created EP in APIC')
                        else:
                            self.logger.error('EP creation failed for EP {}, Error: {}'.format(endpoint, ep_res))
                            raise CheckpointException('EP', 'APIC', props, ep_res)
                    else:
                        # This will occur when EP is updated apart from its EPG
                        # TODO: API to update the updated EP
                        pass

            elif status == 'delete':
                endpoint = self.db.get_endpoint(props['_id'])
                self.db.delete_endpoint(props['_id'])
                self.logger.info("Deleted endpoint {} in DB".format(props['name']))

                if not endpoint:
                    self.logger.info("Endpoint does not exist")
                else:
                    epg_name = self.get_epg_from_db(endpoint['epg'])['name']
                    ep_res = self.create_ep(tenant, ap, epg_name, props, delete=True)
                    if ep_res == 'Successful':
                        self.logger.info('Successfully deleted EP in APIC')
                    else:
                        self.logger.error('EP deletion failed for EP {}, Error: {}'.format(endpoint, ep_res))
                        raise CheckpointException('EP', 'APIC', props, ep_res)
            else:
                self.logger.error("Could not process EP because the status is: {}".format(status))
                raise CheckpointException('EP', 'APIC and DB', props, "Status of EP is {}, expected: create/update/delete".format(status))
        except CheckpointException as e:
            raise e
        except Exception as e:
            raise CheckpointException('EP', 'APIC and DB', props, "Some error occurred while processing endpoint message, Error: {}".format(str(e)))


    def process_grouping_message(self, props, status):
        """Process grouping message"""

        try:
            tenant = self.config['tenant']
            ap = self.config['application_profile']

            if status == 'create' or status == 'update':
                # get EPG if exists
                epg = self.db.get_epg(props['_id'])
                if not epg:
                    # Creatin new EPG in DB and APIC
                    epg_count = self.db.count_epgs()
                    epg_count = epg_count + 1
                    epg_name = "EPG_" + str(epg_count)
                    props['name'] = epg_name
                    props['consumed'] = [] # for db
                    props['provided'] = [] # for db
                    self.db.insert_epg(props)
                    self.logger.info("Inserted EPG {} in DB".format(props['name']))

                    epg_response = self.create_epg(tenant, ap, props['name'])
                    if epg_response == 'Successful':
                        self.logger.debug("Created EPG {} on APIC".format(props['name']))
                    else:
                        self.logger.debug(epg_response)
                        raise CheckpointException('Grouping/EPG', 'APIC', props, epg_response)
                else:
                    # Update existing EPG's members in DB
                    # EP gets updated in APIC when they are added or removed from APIC
                    props['name'] = epg['name']
                    prev = set(epg['members'])
                    update = set(props['members'])
                    if prev != update:
                        self.logger.info("Updating {} membership".format(props['name']))
                        self.db.update_epg_membership(props['_id'], props['members'])
                        self.logger.info("Updated EPG {} in DB".format(props['name']))
                    else:
                        self.logger.info("EPG {} already exists".format(props['name']))
            elif status == 'delete':
                epg = self.db.get_epg(props['_id'])
                if not epg:
                    self.logger.info('Epg does not exist')
                else:
                    props['name'] = epg['name']
                    # The message is received from beam do not have 'members' in it
                    # thus fetch members from db
                    for member in epg['members']:
                        self.db.delete_endpoint(member, identifier='name')
                        self.logger.info("Deleted EP {} from DB".format(member))
                    self.db.delete_epg(props['_id'])
                    self.logger.info("Deleted EPG {} and its EP in DB".format(props['name']))
                    epg_response = self.create_epg(tenant, ap, epg['name'], delete=True)
                    if epg_response == 'Successful':
                        self.logger.info('Successfully deleted grouping from APIC')
                    else:
                        self.logger.debug(epg_response)
                        raise CheckpointException('Grouping/EPG', 'APIC', props, epg_response)
            else:
                self.logger.error("Could not process Group because the status is: {}".format(status))
                raise CheckpointException('EPG', 'APIC and DB', props, "Status of EPG is {}, expected: create/update/delete")
        except CheckpointException as e:
            raise e
        except Exception as e:
            raise CheckpointException('EPG', 'APIC and DB', props, "Some error occurred while processing grouping message, Error: {}".format(str(e)))


    def process_contract_message(self, props, status):
        """Process contract message"""

        try:
            tenant = self.config['tenant']
            ap = self.config['application_profile']

            if status == 'create' or status == 'update':
                # TODO determine if/how/what filter info will contain
                if 'filter_entries' not in props: # TODO figure out filter_entries, current messages missing field
                    props['filter_entries'] = "ANY"
                if 'action' not in props:
                    props['action'] = 'deny'

                # find filter
                if props['filter_entries'] == "ANY":
                    filter_name = tenant + "-any"
                else:
                    # REVIEW current naming scheme below limited; filter names on apic limited to 64 characters
                    # TODO revise naming below depending on msg format for filter entries
                    filter_name = "-".join([tenant] + list(map(str, props['filter_entries'])))

                filter = self.db.get_filter(filter_name)
                if not filter: # create filter in APIC as well as DB
                    self.db.insert_filter(filter_name, tenant, props['filter_entries'])
                    self.logger.info("Inserted filter {} to DB".format(filter_name))

                    filter_response = self.create_filter(tenant, filter_name, props['filter_entries'])
                    if filter_response == 'Successful':
                        self.logger.info('Successfully created filter')
                    else:
                        self.logger.error('Filter creation failed, Error: {}'.format(filter_name))
                        raise CheckpointException('Contract', 'APIC', props, filter_response)

                props['filter_name'] = filter_name

                # REVIEW what is `action` options in msg
                if props['action'] == 'ALLOW':
                    props['action'] = 'permit'

                # Getting EPG name stored in DB using the uuid and put it into props
                #to do
                #we can remove these 2 lines
                props['consumer_epg'] = self.get_epg_from_db(props['consumer_epg'])['name']
                props['provider_epg'] = self.get_epg_from_db(props['provider_epg'])['name']


                # `contract` represents old entry in DB
                # `props` represents new to be updated entry
                contract = self.db.get_contract(props['_id'], identifier='id')
                if not contract:
                    contract_count = self.db.count_contracts()
                    contract_count = contract_count + 1
                    contract_name = "CONTRACT_" + str(contract_count)
                    props['name'] = contract_name
                    contract = props
                    self.db.insert_contract(props)
                    self.logger.info("Inserted contract {} in DB".format(props['name']))

                    contract_response = self.create_contract(tenant, props['name'], filter_name, props['action'])
                    if contract_response == 'Successful':
                        self.logger.info('Successfully created contract')
                    else:
                        self.logger.error('Contract creation failed, Error: {}'.format(contract_response))
                        raise CheckpointException('Contract', 'APIC', props, contract_response)

                    # For attaching contracts to EPGs
                    added_con = contract['consumer_epg']
                    added_prov = contract['provider_epg']
                    # removed_con = None
                    # removed_prov = None

                    self.db.add_contract_by_name('consumed', added_con, contract['_id'])
                    self.logger.info("Contract {} added to DB".format(added_con))

                    attach_contract_response = self.attach_contract('consumed', tenant, ap, added_con, contract['name'])
                    if attach_contract_response == 'Successful':
                        self.logger.info('Successfully attached contract')
                    else:
                        self.logger.error('Contract creation failed, Error: {}'.format(attach_contract_response))
                        raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

                    self.db.add_contract_by_name('provided', added_prov, contract['_id'])
                    self.logger.info("Contract {} added to DB".format(added_prov))

                    attach_contract_response = self.attach_contract('provided', tenant, ap, added_prov, contract['name'])
                    if attach_contract_response == 'Successful':
                        self.logger.info('Successfully attached contract')
                    else:
                        self.logger.error('Contract creation failed, Error: {}'.format(attach_contract_response))
                        raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

                """
                Code needed to avoid update of a contract. No need for contract update usecase in AURORA.
                """
                # elif props['consumer_epg'] == contract['consumer_epg'] and props['provider_epg'] == contract['provider_epg']:
                #     self.logger.info("Contract already exists")
                #     added_con = None
                #     added_prov = None
                #     removed_con = None
                #     removed_prov = None

                """
                Below line of code is not reachable because a contraact will never be updated as per the present implementation.
                Useful only when there is many to many relationships for a Contract.
                """
                # else:
                #     props['name'] = contract['name']
                #     # update filter entry
                #     if filter_name != contract['filter_name']:
                #         change_filter_res = self.change_contract_filter(tenant, props['name'], filter_name, contract['filter_name'],
                #                                     props['action'])
                #         if change_filter_res == 'Successful':
                #             self.logger.info('Successfully updated contract filter')
                #         else:
                #             self.logger.info('Contract creation failed, Error: {}'.format(change_filter_res))
                #             raise CheckpointException('Contract', 'APIC', props, change_filter_res)
                #         self.db.update_contract_filter(props['_id'], filter_name, props['filter_entries'])

                #     # update consumer/provider
                #     self.db.update_contract_membership(props['_id'], 'consumed', props['consumer_epg'])
                #     self.db.update_contract_membership(props['_id'], 'provided', props['provider_epg'])
                #     self.logger.info("Determining contract cons/prov updates")

                #     # For attaching new contract to EPG and removing the old contracts
                #     added_con = props['consumer_epg']
                #     added_prov = props['provider_epg']
                #     removed_con = contract['consumer_epg'] if not props['consumer_epg'] == contract['consumer_epg'] else None
                #     removed_prov = contract['provider_epg'] if not props['provider_epg'] == contract['provider_epg'] else None

                """
                Code needed with above elif and else conditions only!
                """
                # # attach contract consumer/producer on APIC
                # # associate contracts to EPG entries in database
                # # assuming epgs are already created
                # if added_con:
                #     self.db.add_contract_by_name('consumed', added_con, contract['_id'])
                #     attach_contract_response = self.attach_contract('consumed', tenant, ap, added_con, contract['name'])
                #     if attach_contract_response == 'Successful':
                #         self.logger.info('Successfully attached contract')
                #     else:
                #         self.logger.info('Contract creation failed, Error: {}'.format(attach_contract_response))
                #         raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

                # if added_prov:
                #     self.db.add_contract_by_name('provided', added_prov, contract['_id'])
                #     attach_contract_response = self.attach_contract('provided', tenant, ap, added_prov, contract['name'])
                #     if attach_contract_response == 'Successful':
                #         self.logger.info('Successfully attached contract')
                #     else:
                #         self.logger.info('Contract creation failed, Error: {}'.format(attach_contract_response))
                #         raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

                # if removed_con:
                #     self.db.remove_contract_by_name('consumed', removed_con, contract['_id'])
                #     attach_contract_response = self.attach_contract('consumed', tenant, ap, removed_con, contract['name'], delete=True)
                #     if attach_contract_response == 'Successful':
                #         self.logger.info('Successfully attached contract')
                #     else:
                #         self.logger.info('Contract deletion failed, Error: {}'.format(attach_contract_response))
                #         raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

                # if removed_prov:
                #     self.db.remove_contract_by_name('provided', removed_prov, contract['_id'])
                #     attach_contract_response = self.attach_contract('provided', tenant, ap, removed_prov, contract['name'], delete=True)
                #     if attach_contract_response == 'Successful':
                #         self.logger.info('Successfully attached contract')
                #     else:
                #         self.logger.info('Contract deletion failed, Error: {}'.format(attach_contract_response))
                #         raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

            elif status == 'delete':
                contract = self.db.get_contract(props['_id'], identifier='id')
                if not contract:
                    self.logger.info('Contract does not exist')
                else:
                    # For attaching contracts to EPGs
                    removed_con = contract['consumer_epg']
                    removed_prov = contract['provider_epg']

                    self.db.remove_contract_by_name('consumed', removed_con, props['_id'])
                    self.logger.info("Removed consumed contract {} from DB".format(removed_con))
                    self.db.remove_contract_by_name('provided', removed_prov, props['_id'])
                    self.logger.info("Removed provided contract {} from DB".format(removed_prov))
                    self.db.delete_contract(props['_id'])
                    self.logger.info("Deleted contract {} from DB".format(props['_id']))

                    attach_contract_response = self.attach_contract('consumed', tenant, ap, removed_con, contract['name'], delete=True)
                    if attach_contract_response == 'Successful':
                        self.logger.info('Successfully attached contract')
                    else:
                        self.logger.error('Contract deletion failed, Error: {}'.format(attach_contract_response))
                        raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

                    attach_contract_response = self.attach_contract('provided', tenant, ap, removed_prov, contract['name'], delete=True)
                    if attach_contract_response == 'Successful':
                        self.logger.info('Successfully attached contract')
                    else:
                        self.logger.error('Contract deletion failed, Error: {}'.format(attach_contract_response))
                        raise CheckpointException('Contract', 'APIC', props, attach_contract_response)

                    props['name'] = contract['name']
                    contract_response = self.create_contract(tenant, props['name'], filter=None, action=None, delete=True)
                    if contract_response == 'Successful':
                        self.logger.info('Successfully deleted contract')
                    else:
                        self.logger.error('Contract deletion failed, Error: {}'.format(contract_response))
                        raise CheckpointException('Contract', 'APIC', props, contract_response)

            else:
                self.logger.error("Could not process Contract because the status is: {}".format(status))
                raise CheckpointException('Contract', 'APIC and DB', props, "Status of contract is {}, expected: create/update/delete")
        except CheckpointException as e:
            raise e
        except Exception as e:
            raise CheckpointException('Contract', 'APIC and DB', props, "Some error occurred while processing contract message, Error: {}".format(str(e)))


    def attach_contract(self, role, tenant, ap, epg, contract, status='created,modified', delete=False):
        """Attach a contract to an EPG
        Create fvRsCons or fvRsProv on APIC

        :param role: str
            `'consumed'` or `'provided'`
        :param tenant: str
        :param ap: str
        :param epg: str
        :param contract: str
        :param status: str
            `'created,modified'` or `'deleted'`
        :return:
        """

        if role == 'consumed':
            class_ = 'fvRsCons'
        elif role == 'provided':
            class_ = 'fvRsProv'

        status = 'deleted' if delete else 'created,modified'

        debug_action = 'Setting' if status == 'created,modified' else 'Deleting'
        role_log = 'consumer' if role == 'consumed' else 'provider'
        self.logger.info("{} EPG '{}' as {} for contract '{}' on APIC".format(debug_action, epg, role_log, contract))

        url = "/api/node/mo/uni/tn-{}/ap-{}/epg-{}.json".format(tenant, ap, epg)
        payload = {
          class_: {
            "attributes": {
              "tnVzBrCPName": contract,
              "status": status
            }
          }
        }
        res = self.apic.request("POST", url, data=json.dumps(payload))
        if res.status_code == 200:
            self.logger.info("Successfully processed contract '{}' for EPG '{}'".format(contract, epg))
            return 'Successful'
        else:
            self.logger.error("API call for Contract '{}' to APIC failed, Error: {}, Status Code: {}".format(contract, res.content, res.status_code))
            return "API call for Contract '{}' to APIC failed, Error: {}, Status Code: {}".format(contract, res.content, res.status_code)


    def create_ep(self, tenant, ap, epg, endpoint, delete=False):
        """
        Creating and Deleting an static endpoint
        """

        mac_address = endpoint['mac_address']
        ip_address = endpoint['ip_address']
        dn = 'uni/tn-{}/ap-{}/epg-{}/stcep-{}-type-silent-host'.format(tenant, ap, epg, mac_address)
        url = '/api/node/mo/{}.json'.format(dn)
        if not delete:
            payload = {
                "fvStCEp": {
                    "attributes": {
                        "dn": dn,
                        "mac": mac_address,
                        "ip": ip_address,
                        "encap": "vlan-1"
                    },
                    "children": [
                        {
                            "fvRsStCEpToPathEp": {
                                "attributes": {
                                    "tDn": "topology/pod-1/paths-101/pathep-[eth1/1]",
                                    "status": "created"
                                },
                                "children": []
                            }
                        }
                    ]
                }
            }
            self.logger.info('Creating Endpoint whose mac address is {}'.format(mac_address))
            res = self.apic.request("POST", url, data=json.dumps(payload))
        else:
            payload = {
                "fvStCEp": {
                    "attributes": {
                        "dn": dn
                    },
                    "children": [
                        {
                            "tagTag": {
                                "attributes": {
                                "key": "os",
                                "status": "deleted"
                                }
                            }
                        }
                    ]
                }
            }
            self.logger.info('Deleting endpoint: {}'.format(dn))
            res = self.apic.request("DELETE", url, data=json.dumps(payload))
        if res.status_code == 200:
            self.logger.info('Successfully created/deleted endpoint whose mac address is {}'.format(mac_address))
            return 'Successful'
        elif res.status_code == 400 and 'already exists' in res.text:
            self.logger.info('Endpoint whose mac address is {}, already exists'.format(mac_address))
            return 'Successful'
        else:
            self.logger.error('Following error occurred while creating mac address - {}'.format(mac_address))
            return "API call for EP(mac:{}) creation/deletion failed, Error: {}, Status Code: {}".format(mac_address, res.content, res.status_code)

    
    def create_epg(self, tenant, ap, epg, status='created,modified', delete=False):
        """Make an endpoint group
        Create fvAEPg on APIC

        :param tenant: str
        :param ap: str
        :param epg: str
        :param status: str
            `'created,modified'` or `'deleted'`
        :return:
        """

        status = 'deleted' if delete else 'created,modified'
        debug_action = 'Creating' if status == 'created,modified' else 'Deleting'
        self.logger.info("{} EPG '{}' on APIC".format(debug_action, epg))

        url = "/api/node/mo/uni/tn-{}/ap-{}/epg-{}.json".format(tenant, ap, epg)
        payload = {
          "fvAEPg": {
            "attributes": {
              "name": epg,
              "status": status
            }
          }
        }
        res = self.apic.request("POST", url, data=json.dumps(payload))
        if res.status_code == 200:
            self.logger.info("API call for EPG '{}' to APIC successful".format(epg))
            return 'Successful'
        else:
            self.logger.error("API call for EPG '{}' to APIC failed, Error: {}, Status Code: {}".format(epg, res.content, res.status_code))
            return "API call for EPG '{}' to APIC failed, Error: {}, Status Code: {}".format(epg, res.content, res.status_code)


    def create_contract(self, tenant, contract, filter, action, status='created,modified', delete=False):
        """Make a contract
        Create vzBrCP and vzSubj on APIC

        :param tenant: str
        :param contract: str
        :param filter: str
        :param status: str
            `'created,modified'` or `'deleted'`
        :return:
        """
        assert status == 'created,modified' or 'deleted'
        status = 'deleted' if delete else 'created,modified'
        debug_action = 'Creating' if status == 'created,modified' else 'Deleting'
        self.logger.info("{} contract '{}' on APIC".format(debug_action, contract))

        url = "/api/node/mo/uni/tn-{0}/brc-{1}.json".format(tenant, contract)

        payload = {
          "vzBrCP": {
            "attributes": {
              "name": contract,
              "status": status
            },
            "children": [
              {
                "vzSubj": {
                  "attributes": {
                    "name": "contract-subject",
                    "status": status
                  }
                }
              }
            ]
          }
        }
        if status != "deleted": # REVIEW or maybe if filter == None? maybe want to delete filter sometimes
            filt_att = [
              {
                "vzRsSubjFiltAtt": {
                  "attributes": {
                    "status": status,
                    "tnVzFilterName": filter,
                    "directives": "none",
                    "action": action.lower()
                  }
                }
              }
            ]
            payload["vzBrCP"]["children"][0]['vzSubj']["children"] = filt_att

        res = self.apic.request('POST', url, data=json.dumps(payload))
        if res.status_code == 200:
            self.logger.info("API call for Contract '{}' to APIC successful".format(contract))
            return 'Successful'
        else:
            self.logger.error("API call for Contract '{}' to APIC failed, Error: {}, Status Code: {}".format(contract, res.content, res.status_code))
            return "API call for Contract '{}' to APIC failed, Error: {}, Status Code: {}".format(contract, res.content, res.status_code)


    def change_contract_filter(self, tenant, contract, new_filter, old_filter, action):
        url = "/api/node/mo/uni/tn-{0}/brc-{1}/subj-contract-subject.json".format(tenant, contract)
        self.logger.info("Changing filter for contract {}".format(contract))

        payload = {
            "vzSubj": {
                "attributes": {
                    "name": "contract-subject",
                    "status": "created,modified"
                },
                "children": [
                    {
                      "vzRsSubjFiltAtt": {
                        "attributes": {
                          "status": "deleted",
                          "tnVzFilterName": old_filter,
                          "directives": "none",
                          "action": action.lower(),
                        }
                      }
                    },
                    {
                      "vzRsSubjFiltAtt": {
                        "attributes": {
                          "status": "created,modified",
                          "tnVzFilterName": new_filter,
                          "directives": "none",
                          "action": action.lower()
                        }
                      }
                    }
                ]
            }
        }

        res = self.apic.request('POST', url, data=json.dumps(payload))
        if res.status_code == 200:
            self.logger.info("Successfully updated filter for contract '{}' in APIC".format(contract))
            return 'Successful'
        else:
            self.logger.error("API call for Filter updation for contract '{}' to APIC failed, Error: {}, Status Code: {}".format(contract, res.content, res.status_code))
            return "API call for Contract '{}' to APIC failed, Error: {}, Status Code: {}".format(contract, res.content, res.status_code)


    def create_filter(self, tenant, filter, ports, status='created,modified', delete=False):
        """Make a filter
        Create vzFilter and vzEntry on APIC

        :param tenant: str
        :param filter: str
        :param entries: str
        :param status: str
            `'created,modified'` or `'deleted'`
        :return:
        """
        assert status == 'created,modified' or 'deleted'

        status = 'deleted' if delete else 'created,modified'

        debug_action = 'Creating' if status == 'created,modified' else 'Deleting'
        self.logger.info("{} filter '{}' on APIC".format(debug_action, filter))

        def entry_payload(port):
            payloads = (
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "tcp_{}".format(port),
                            "etherT": "ip",
                            "prot": "tcp",
                            "dFromPort": port,
                            "dToPort": port,
                            "status": status
                        }
                    }
                },
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "udp_{}".format(port),
                            "etherT": "ip",
                            "prot": "udp",
                            "dFromPort": port,
                            "dToPort": port,
                            "status": status
                        }
                    }
                }
            )
            return payloads

        # create correct filter
        if ports == 'ANY': # REVIEW can we NOT create an entry if we want to allow all for the filter?
            entries = [
              {
                "vzEntry": {
                  "attributes": {
                    "name": "any",
                    "status": status
                  }
                }
              }
            ]
        else:
            entries = [entry for port in ports for entry in entry_payload(port)]

        url = "/api/node/mo/uni/tn-{0}/flt-{1}.json".format(tenant, filter)
        payload = {
          "vzFilter": {
            "attributes": {
              "name": filter,
              "status": status
            },
            "children": entries
          }
        }
        res = self.apic.request('POST', url, data=json.dumps(payload))
        if res.status_code == 200:
            self.logger.info("API call for Filter '{}' to APIC successful".format(filter))
            return 'Successful'
        else:
            self.logger.error("API call for Filter '{}' to APIC failed, Error: {}, Status Code: {}".format(filter, res.content, res.status_code))
            return "API call for Filter '{}' to APIC failed, Error: {}, Status Code: {}".format(filter, res.content, res.status_code)
