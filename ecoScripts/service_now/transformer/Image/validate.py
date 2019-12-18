# import argparse
import json
import os
import sys
from pykafka import KafkaClient
from elasticsearch import Elasticsearch
import requests


from pigeon import Pigeon

pigeon = Pigeon()



def test_kafka():
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    kafka_port = os.getenv('KAFKA_PORT')
    inp_topic = os.getenv('PRODUCER_TOPIC')
    out_topic = os.getenv('CONSUMER_TOPIC')

    offset_topic = "offset_" + inp_topic + "_" + out_topic
    input_error_topic = "error_" + inp_topic

    try:
        host = '{}:{}'.format(kafka_ip, kafka_port)
        client = KafkaClient(hosts=host)

        pigeon.sendInfoMessage("Kafka connected successfully")
        pigeon.sendInfoMessage("Testing Kafka Input/Output topic")

        data_topics = [inp_topic, out_topic, offset_topic, input_error_topic]
        existing_topics = client.topics.keys()
        existing_topics_list = []
        for each in existing_topics:
            existing_topics_list.append(each.decode("utf-8"))
            
        topic_exists = False
        for curr_topic in data_topics:
            client.topics[curr_topic]
            #Below line is for creating new topic with python-kafka library. Since we are migrating to PyKafka \
            # so removing this. TODO find alternative way to specify number of partitions and replication factor while creating topic in PyKafka lib.
            #create_topics = [NewTopic(curr_topic, num_partitions=1, replication_factor=1)]
            pigeon.sendInfoMessage("Topics created")




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
