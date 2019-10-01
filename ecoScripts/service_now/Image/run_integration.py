import subprocess
import os
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

    pigeon.sendInfoMessage("Start pipeline process!!")
    pipeline = subprocess.Popen(split(["java", "-jar", "/app/data-pipeline-bundled-0.1.jar", "--runner=FlinkRunner",
                                       "--flinkMaster={}".format(flink_ip), "--kafkaIP={}".format(kafka_ip),
                                       "--kafkaPort={}".format(kafka_port),
                                       "--kafkaInputTopic={}".format(kafka_input_topic),
                                       "--kafkaOutputTopic={}".format(kafka_output_topic), "--streaming=true",
                                       "--parallelism=1"]), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pigeon.sendInfoMessage("Getting job id from pipeline now")
    str_job = "Submitting job"
    job_id = ""
    while True:
        line = pipeline.stdout.readline()
        if not line:
            break
        if str_job in line:
            print("Got line having job id from the pipeline process from run_integration.py :", line.rstrip())
            job_id_str = line.rstrip().split(str_job)[1].lstrip().split(' ')
            job_id = job_id_str[0]
            print("Got job id from run_integration.py ", job_id)

    pigeon.sendInfoMessage("Got job id from pipeline now", job_id)
    consumer = subprocess.Popen(["python", "-m", "snow.consumer.app"])
    connector = subprocess.Popen(["python", "-m", "snow.snow-table-parser.aurora_snow_connector"])

    pipeline.wait()
    consumer.wait()
    connector.wait()


if __name__ == '__main__':
    main()
