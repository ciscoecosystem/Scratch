import subprocess
import os
import json
import requests
from shlex import split
from pigeon import Pigeon

pigeon = Pigeon()


def main():
    pigeon.sendInfoMessage("Starting Service now-kafka integration")

    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    kafka_port = os.getenv('KAFKA_PORT')
    kafka_input_topic = os.getenv('KAFKA_INPUT_TOPIC')
    kafka_output_topic = os.getenv('KAFKA_OUTPUT_TOPIC')
    kafka_error_topic = "error_" + kafka_input_topic



    
    connector = subprocess.Popen(["python", "-m", "integration.aurora_snow_connector"])
    connector.wait()


if __name__ == '__main__':
    main()
