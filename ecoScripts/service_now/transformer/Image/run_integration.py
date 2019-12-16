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
    es_host = os.getenv('ES_HOSTNAME')
    es_port = os.getenv('ES_PORT')

    flinkUrl = "http://" + flink_ip + ":8081/jobs/overview"
    process_running = False
    response = requests.get(flinkUrl)
    resp_dict = json.loads(response.content)
    for job in resp_dict.get('jobs'):
        if job.get('state') == 'RUNNING' and job.get('name').find('auroradatapipeline') >= 0:
            print(job.get('name'))
            flink_job_id=job.get('jid')
            process_running = True
            break

    # Avro installation
    subprocess.Popen(["sh", "install_avro.sh"]).wait()

    # TODO: get consumer and connector out of if else
    if not process_running:
        pigeon.sendInfoMessage("Start pipeline process!!")
        pipeline = subprocess.Popen(["java", "-jar", "/app/data-pipeline-bundled-0.1.jar", "--runner=FlinkRunner",
                                     "--flinkMaster={}".format(flink_ip),
                                     "--kafkaIP={}".format(kafka_ip),
                                     "--kafkaPort={}".format(kafka_port),
                                     "--kafkaInputTopic={}".format(kafka_input_topic),
                                     "--kafkaOutputTopic={}".format(kafka_output_topic),
                                     "--kafkaErrorTopic={}".format(kafka_error_topic),
                                     "--esHost={}".format(es_host),
                                     "--esPort={}".format(es_port),
                                     "--streaming=true",
                                     "--parallelism=1"])
        pipeline.wait()
        
    else:
        pigeon.sendInfoMessage("Not starting flink pipeline as it is already running with id: "+flink_job_id+" on "+flinkUrl)

if __name__ == '__main__':
    main()
