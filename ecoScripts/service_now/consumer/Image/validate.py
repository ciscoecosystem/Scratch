# import argparse
import json
import os
import sys

from pykafka import KafkaClient
import requests
from pymongo import MongoClient
# from kafka.admin import KafkaAdminClient, NewTopic
from pymongo.errors import ConnectionFailure
from integration.apic import APIC

from pigeon import Pigeon

pigeon = Pigeon()


def test_aci():
    # TODO query for existence of tenant and AP
    tenant_name = os.getenv('TENANT_NAME')
    ap_name = os.getenv('AP_NAME')

    apic = APIC.get_apic()

    login_response = apic.login()
    if login_response.status_code != 200:
        pigeon.sendUpdate({
            'status': 'error',
            'message': "Cannot login into APIC"
        })
        test_response = False
    else:
        tenant_response = apic.request('GET',
                                       '/api/node/class/fvTenant.json?query-target-filter=eq(fvTenant.name,"{}")'.format(
                                           tenant_name))
        if tenant_response.status_code == 200 and json.loads(tenant_response.content)['imdata'] != []:
            pigeon.sendInfoMessage("Tenant {} Exists".format(tenant_name))
            test_response = True
        else:
            pigeon.sendInfoMessage("Tenant {} Does Not Exists. Creating new Tenant {}".format(tenant_name, tenant_name))
            tenant_payload = {
                "fvTenant": {
                    "attributes": {
                        "dn": "uni/tn-{}".format(tenant_name)
                    }
                }
            }
            create_tenant = apic.request('POST', '/api/node/mo/uni/tn-{}.json'.format(tenant_name), json=tenant_payload)
            if create_tenant.status_code == 200:
                pigeon.sendInfoMessage("New Tenant {} Created".format(tenant_name))
                test_response = True
            else:
                pigeon.sendUpdate({
                    'status': 'error',
                    'message': "Tenant {} NOT created".format(tenant_name)
                })
                test_response = False

        # AP check and create.
        ap_response = apic.request('GET',
                                   '/api/node/class/fvAp.json?query-target-filter=eq(fvAp.name,"{}")'.format(ap_name))
        if ap_response.status_code == 200 and json.loads(ap_response.content)['imdata'] != []:
            pigeon.sendInfoMessage("AP {} Exists".format(ap_name))
            test_response = True
        else:
            pigeon.sendInfoMessage("AP {} Does Not Exists. Creating new AP {}".format(ap_name, ap_name))
            ap_payload = {
                "fvAp": {
                    "attributes": {
                        "dn": "uni/tn-{}/ap-{}".format(tenant_name, ap_name)
                    }
                }
            }
            create_ap = apic.request('POST', '/api/node/mo/uni/tn-{}/ap-{}.json'.format(tenant_name, ap_name),
                                     json=ap_payload)
            if create_ap.status_code == 200:
                pigeon.sendInfoMessage("New AP {} in Tenant {} Created".format(ap_name, tenant_name))
                test_response = True
            else:
                pigeon.sendUpdate({
                    'status': 'error',
                    'message': "AP {} NOT created".format(ap_name)
                })
                test_response = False

    apic.logout()
    apic.close()
    return test_response


def test_kafka():
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    kafka_port = os.getenv('KAFKA_PORT')
    out_topic = os.getenv('CONSUMER_TOPIC')

    output_error_topic = "error_" + out_topic

    try:
        host = '{}:{}'.format(kafka_ip, kafka_port)
        client = KafkaClient(hosts=host)

        pigeon.sendInfoMessage("Kafka connected successfully")
        pigeon.sendInfoMessage("Testing Kafka Input/Output topic")

        data_topics = [out_topic, output_error_topic]
        existing_topics = client.topics.keys()
        existing_topics_list = []
        for each in existing_topics:
            existing_topics_list.append(each.decode("utf-8"))
            
        topic_exists = False
        for curr_topic in data_topics:
            if curr_topic not in existing_topics_list:
                #it will create new topic pa
                client.topics[curr_topic]
                #Below line is for creating new topic with python-kafka library. Since we are migrating to PyKafka
                #so removing this. TODO find alternative way to specify number of partitions and replication factor while creating topic in PyKafka lib.
                #create_topics = [NewTopic(curr_topic, num_partitions=1, replication_factor=1)]
                pigeon.sendInfoMessage("Topics created")
            else:
                pigeon.sendInfoMessage("Topic already exists: " + curr_topic)
                topic_exists = True
            


        if topic_exists:
            pigeon.sendUpdate({
                'status': 'error',
                'message': 'Topic already exists.Please enter different input and output topic names.'
            })
            return False

        ''' In case there is need to delete the topics 
            for curr_topic in broker_topics:
                 print(curr_topic)
            client.delete_topics(broker_topics)
        '''

    except Exception as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to Kafka server'
        })
        return False
    else:
        return True


def test_mongo():
    mongo_ip = os.getenv('MONGO_HOSTNAME')
    mongo_port = int(os.getenv('MONGO_PORT'))

    try:
        pigeon.sendInfoMessage("Testing Mongo")
        client = MongoClient(mongo_ip, mongo_port, serverSelectionTimeoutMS=1000)

        # # TODO figure out solution, dont let this stdout mess up ecohub
        # f = open(os.devnull, 'w')
        # tmp = sys.stdout
        # sys.stdout = f
        client.admin.command('ismaster')
        # sys.stdout = tmp
    except ConnectionFailure as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to MongoDB server'
        })
        return False
    else:
        return True


def validate():
    return test_mongo() and test_kafka() and test_aci()


if __name__ == "__main__":
    pigeon.sendInfoMessage("In validate.main()")
    if len(sys.argv) == 1:
        # REVIEW maybe change flow? `if` below not technically not needed as error pigeon will stop execution
        if validate():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Connectivity successful'
            }, last=True)  # REVIEW When does last=True?

    elif sys.argv[1] == 'aci':
        if test_aci():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test ACI successful'
            }, last=True)

    elif sys.argv[1] == 'kafka':
        if test_kafka():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Kafka Connectivity successful'
            }, last=True)  # REVIEW When does last=True?

