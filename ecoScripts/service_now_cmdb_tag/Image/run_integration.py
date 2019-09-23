import subprocess
import os

from pigeon import Pigeon

pigeon = Pigeon()

def main():
    pigeon.sendInfoMessage("Starting integration")

    flink_ip = os.getenv('FLINK_HOSTNAME')
    kafka_ip = os.getenv('KAFKA_HOSTNAME')
    kafka_port = os.getenv('KAFKA_PORT')
    kafka_input_topic = os.getenv('KAFKA_INPUT_TOPIC')
    kafka_output_topic = os.getenv('KAFKA_OUTPUT_TOPIC')

    pipeline = subprocess.Popen(["java", "-jar", "/app/data-pipeline-bundled-0.1.jar", "--runner=FlinkRunner", "--flinkMaster={}".format(flink_ip), "--kafkaIP={}".format(kafka_ip), "--kafkaPort={}".format(kafka_port), "--kafkaInputTopic={}".format(kafka_input_topic), "--kafkaOutputTopic={}".format(kafka_output_topic), "--streaming=true", "--parallelism=1"])
    consumer = subprocess.Popen(["python", "-m", "snow.consumer.app"])
    connector = subprocess.Popen(["python", "-m", "snow.snow-tag-parser.aurora_snow_tag_connector"])

    pipeline.wait()
    consumer.wait()
    connector.wait()

if __name__ == '__main__':
    main()

