import json
import os
import sys
import kafka
from kafka import KafkaConsumer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from pigeon import Pigeon

pigeon = Pigeon()

def test_connector():
    return

def test_consumer():
    topic = os.getenv('KAFKA_OUTPUT_TOPIC')
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    mongo_ip = os.getenv('MONGO_HOSTNAME')
    mongo_port = int(os.getenv('MONGO_PORT'))

    try:
        pigeon.sendInfoMessage("Testing Kafka")
        consumer = KafkaConsumer(topic, bootstrap_servers=kafka_ip)
        pigeon.sendInfoMessage("Testing Kafka complete")

        pigeon.sendInfoMessage("Testing Mongo")
        client = MongoClient(mongo_ip, mongo_port, serverSelectionTimeoutMS=1000)

        # # TODO figure out solution, dont let this stdout mess up ecohub
        # f = open(os.devnull, 'w')
        # tmp = sys.stdout
        # sys.stdout = f
        client.admin.command('ismaster')
        # sys.stdout = tmp
    except kafka.errors.NoBrokersAvailable as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to Kafka server'
        })
    except ConnectionFailure as error:
        pigeon.sendUpdate({
            'status': 'error',
            'message': 'Cannot connect to MongoDB server'
        })
    else:
        pigeon.sendInfoMessage("Before connected")
        pigeon.sendUpdate({
            'status': 200,
            'message': 'Kafka and Mongo server connected'
        }, last=True) # REVIEW When does last=True?
        pigeon.sendInfoMessage("after connected")


if __name__ == "__main__":
    pigeon.sendInfoMessage("In test_connectivity.main()")
    test_consumer()
