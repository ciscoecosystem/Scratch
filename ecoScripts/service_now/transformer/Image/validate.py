# import argparse
import json
import os
import sys
import kafka
from elasticsearch import Elasticsearch
import requests
from kafka.admin import KafkaAdminClient, NewTopic


from pigeon import Pigeon

pigeon = Pigeon()



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


def test_es():
    es_ip = os.getenv('ES_HOSTNAME')
    port = os.getenv('ES_PORT')
    try:
        pigeon.sendInfoMessage("Testing ES")
        es = Elasticsearch(
            hosts=[{'host': es_ip, 'port': port}],
            verify_certs=True,
        )
        if not es.ping():
            raise ValueError("Connection failed")
        else:
            pigeon.sendInfoMessage('ES connected successfully')
    except Exception as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to ES server'
        })
        return False
    else:
        return True


def test_flink():
    flink_ip = os.getenv('FLINK_HOSTNAME')
    flink_port = os.getenv('FLINK_PORT')
    try:
        flinkUrl = "http://" + flink_ip + ':' + flink_port
        pigeon.sendInfoMessage("Testing Flink : " + flinkUrl)
        response = requests.get(flinkUrl)
        pigeon.sendInfoMessage("response.status_code : " + str(response.status_code))
        print(response.status_code)
        if response.status_code == 200:
            pigeon.sendInfoMessage("Flink connected successfully")
        else:
            raise ValueError("Connection failed")
    except Exception as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to Flink server'
        })
        return False
    else:
        return True


def validate():
    return test_kafka() and test_es() and test_flink()


if __name__ == "__main__":
    pigeon.sendInfoMessage("In validate.main()")
    if len(sys.argv) == 1:
        # REVIEW maybe change flow? `if` below not technically not needed as error pigeon will stop execution
        if validate():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Connectivity successful'
            }, last=True)  # REVIEW When does last=True?

    elif sys.argv[1] == 'kafka':
        if test_kafka():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Kafka Connectivity successful'
            }, last=True)  # REVIEW When does last=True?

    elif sys.argv[1] == 'es':
        if test_es():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test ES Connectivity successful'
            }, last=True)

    elif sys.argv[1] == 'flink':
        if test_flink():
            pigeon.sendUpdate({
                'status': 200,
                'message': 'Test Flink Connectivity successful'
            }, last=True)
