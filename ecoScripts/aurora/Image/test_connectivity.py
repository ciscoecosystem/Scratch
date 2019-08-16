import json
import os
import kafka
from kafka import KafkaConsumer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from pigeon import Pigeon

pigeon = Pigeon()

def test_connector():
    pass

def test_consumer():
    topic = "KAFKA_OUTPUT_TOPIC" # TODO figure out how to pass these
    kafka_ip = "ec2-3-215-226-109.compute-1.amazonaws.com"
    mongo_ip = None
    mongo_port = None

    try:
        consumer = KafkaConsumer(topic, bootstrap_servers=kafka_ip)
        # client = MongoClient(mongo_ip, mongo_port, serverSelectionTimeoutMS=1000)
        # client.admin.command('ismaster')
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
        pigeon.sendUpdate({
            'status': 200,
            'message': 'Aurora Kafka consumer connected'
        })


if __name__ == "__main__":
    test_consumer()
