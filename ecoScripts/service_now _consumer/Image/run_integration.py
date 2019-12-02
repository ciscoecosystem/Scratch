import subprocess
import os
import json
import requests
from shlex import split
from pigeon import Pigeon

pigeon = Pigeon()


def main():
    pigeon.sendInfoMessage("Starting integration")

    flink_ip = os.getenv('FLINK_HOSTNAME')
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    kafka_port = os.getenv('KAFKA_PORT')
    kafka_input_topic = os.getenv('KAFKA_INPUT_TOPIC')
    kafka_output_topic = os.getenv('KAFKA_OUTPUT_TOPIC')
    kafka_error_topic = "error_" + kafka_input_topic
    
    subprocess.Popen(["sh", "install_avro.sh"]).wait()

    
    consumer = subprocess.Popen(["python", "-m", "snow.consumer.app"])   
    consumer.wait()
        


if __name__ == '__main__':
    main()
