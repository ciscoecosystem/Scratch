# import argparse
import json
import os
import sys

import requests
from pykafka import KafkaClient



from pigeon import Pigeon

pigeon = Pigeon()


def test_snow():
    snow_url = os.getenv('SNOW_URL')
    snow_username = os.getenv('SNOW_USERNAME')
    snow_password = os.getenv('SNOW_PASSWORD')
    fetch_from_duration = os.getenv('FETCH_DURATION')
    table_name = 'cmdb_ci'

    try:
        pigeon.sendInfoMessage("Testing SNOW")
        
        if not fetch_from_duration.isdigit():
            pigeon.sendUpdate({
                'status': 'error',
                'message': 'Entered Fetch From Duration is not integer'
            })
            return False
        
        if int(fetch_from_duration) == 0 or int(fetch_from_duration) > 365:
            pigeon.sendUpdate({
                'status': 'error',
                'message': 'Entered Fetch From Duration should be greater than 0 and less than 366'
            })
            return False

        query_url = '{}/api/now/table/{}?sysparm_limit=1'.format(snow_url, table_name)
        response = requests.get(query_url, auth=(snow_username, snow_password))
        if response.status_code == 200 and json.loads(response.content)['result']:
            pigeon.sendInfoMessage("SNOW connected successfully")
            return True
        else:
            pigeon.sendUpdate({
                'status': 'error',
                'message': 'Cannot connect to SNOW server'
            })
            return False
    except Exception as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to SNOW server'
        })
        return False


def test_kafka(create_topics=False):
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    kafka_port = os.getenv('KAFKA_PORT')
    inp_topic = str(os.getenv('PRODUCER_TOPIC'))

    offset_topic = "offset_" + inp_topic
    try:
        host = '{}:{}'.format(kafka_ip, kafka_port)
        client = KafkaClient(hosts=host)

        pigeon.sendInfoMessage("Kafka connected successfully")
        pigeon.sendInfoMessage("Testing Kafka Input/Output topic")

        data_topics = [inp_topic, offset_topic]
        existing_topics = client.topics.keys()
        existing_topics_list = []
        for each in existing_topics:
            existing_topics_list.append(each.decode("utf-8"))
            
        for curr_topic in data_topics:
            if curr_topic in existing_topics_list:
                pigeon.sendUpdate({
                'status': 'error',
                'message': "Topic already exists: " + curr_topic
                })
                return False
                                
        if create_topics:
            for curr_topic in data_topics:
                #it will create new topic
                client.topics[curr_topic]
                pigeon.sendInfoMessage("Topic created: "+ curr_topic)
                #Below line is for creating new topic with python-kafka library. Since we are migrating to PyKafka \
                # so removing this. TODO find alternative way to specify number of partitions and replication factor while creating topic in PyKafka lib.
                #create_topics = [NewTopic(curr_topic, num_partitions=1, replication_factor=1)]

    except Exception as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to Kafka server'
        })
        return False
    else:
        return True


def validate():
    return test_snow() and test_kafka(create_topics=True)

if __name__ == "__main__":
    pigeon.sendInfoMessage("In validate.main()")
    if len(sys.argv) == 1:
        # REVIEW maybe change flow? `if` below not technically not needed as error pigeon will stop execution
        if validate():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Connectivity successful'
            }, last=True)  # REVIEW When does last=True?

    elif sys.argv[1] == 'snow':
        if test_snow():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test ServiceNow Connectivity successful'
            }, last=True)

    elif sys.argv[1] == 'kafka':
        if test_kafka(create_topics=False):
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Kafka Connectivity successful'
            }, last=True)  # REVIEW When does last=True?

