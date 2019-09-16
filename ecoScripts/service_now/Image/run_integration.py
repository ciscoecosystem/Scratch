import subprocess
import os

from pigeon import Pigeon

pigeon = Pigeon()

def main():
    pigeon.sendInfoMessage("Starting integration")
    pipeline = subprocess.Popen('java -cp data-pipeline-bundled-0.1.jar org.cisco.aurora.pipeline.AuroraDataPipeline --runner=FlinkRunner --flinkMaster=localhost --filesToStage=target/data-pipeline-bun-0.1.jar --kafkaIP=$KAFKA_IP --kafkaPort=$KAFKA_PORT --kafkaInputTopic=$KAFKA_INPUT_TOPIC --kafkaOutputTopic=$KAFKA_OUTPUT_TOPIC --streaming=true --parallelism=1')
    consumer = subprocess.Popen(["python", "-m", "snow.consumer.app"])
    connector = subprocess.Popen(["python", "-m", "snow.snow-table-parser.aurora_snow_connector"])

    pipeline.wait()
    consumer.wait()
    connector.wait()

if __name__ == '__main__':
    main()
