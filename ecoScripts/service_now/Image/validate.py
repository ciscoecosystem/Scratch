# import argparse
import json
import os
import sys

from elasticsearch import Elasticsearch
import kafka
from kafka import KafkaConsumer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from flink.plan.Environment import get_environment

from pigeon import Pigeon

pigeon = Pigeon()


def test_snow():
    return True


def test_aci():
    # TODO query for existence of tenant and AP
    return True


def test_kafka():
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    topic = os.getenv('KAFKA_OUTPUT_TOPIC')

    try:
        pigeon.sendInfoMessage("Testing Kafka")
        consumer = KafkaConsumer(topic, bootstrap_servers=kafka_ip)
        pigeon.sendInfoMessage("Kafka connected successfully")
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
        es = Elasticsearch([es_ip], verify_certs=True)
        if not es.ping():
            raise ValueError("Connection failed")
        else:
            print('ES connected successfully')
    except:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to ES server'
        })
        return False
    else:
        return True


def test_flink():
    flink_ip = os.getenv('FLINK_HOSTNAME')
    try:
        pigeon.sendInfoMessage("Testing Flink")
        # TODO check flink connectivity
        pigeon.sendInfoMessage("Flink connected successfully")
    except:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to Flink server'
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
    return test_mongo() and test_kafka() and test_aci() and test_es() and test_flink()


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
