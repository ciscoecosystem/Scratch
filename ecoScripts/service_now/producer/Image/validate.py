# import argparse
import json
import os
import sys

import kafka
import requests

from kafka.admin import KafkaAdminClient, NewTopic


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


def test_kafka():
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    kafka_port = os.getenv('KAFKA_PORT')
    inp_topic = os.getenv('KAFKA_INPUT_TOPIC')
    out_topic = os.getenv('KAFKA_OUTPUT_TOPIC')

    # offset_topic = os.getenv("KAFKA_OFFSET_TOPIC")
    offset_topic = "offset_" + inp_topic + "_" + out_topic
    input_error_topic = "error_" + inp_topic
    output_error_topic = "error_" + out_topic

    try:
        host = '{}:{}'.format(kafka_ip, kafka_port)
        client = KafkaAdminClient(bootstrap_servers=host)
        simple_client = kafka.SimpleClient(host)

        pigeon.sendInfoMessage("Kafka connected successfully")
        pigeon.sendInfoMessage("Testing Kafka Input/Output topic")

        broker_topics = simple_client.topic_partitions
        data_topics = [inp_topic, out_topic, offset_topic, input_error_topic, output_error_topic]
        topic_exists = False
        for curr_topic in data_topics:
            if curr_topic:
                if curr_topic not in broker_topics:
                    create_topics = [NewTopic(curr_topic, num_partitions=1, replication_factor=1)]
                    client.create_topics(create_topics)
                    pigeon.sendInfoMessage("Topics created")
                else:
                    pigeon.sendInfoMessage("Topic already exists: " + curr_topic)
                    topic_exists = True
            else:
                pigeon.sendInfoMessage("Topic does not exist")

        client.close()
        simple_client.close()

        if topic_exists:
            pigeon.sendUpdate({
                'status': 'error',
                'message': 'Topic already exists.Please enter different input and output topic names.'
            })
            return False

        client.close()
        simple_client.close()

        ''' In case there is need to delete the topics 
            for curr_topic in broker_topics:
                 print(curr_topic)
            client.delete_topics(broker_topics)
        '''

    except kafka.errors.NoBrokersAvailable as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to Kafka server'
        })
        return False
    else:
        return True


def validate():
    return test_kafka() and test_snow()

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
        if test_kafka():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Kafka Connectivity successful'
            }, last=True)  # REVIEW When does last=True?

