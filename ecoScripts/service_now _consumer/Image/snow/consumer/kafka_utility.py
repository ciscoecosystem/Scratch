import avro.schema
from kafka import KafkaConsumer
from avro.io import DatumWriter
from pykafka import KafkaClient
from pykafka.common import OffsetType
from datetime import datetime, timedelta, timezone


def load_config(filename):
    """
    loads the configuration from the yaml file
    """
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(filename, 'r') as stream:
        return yaml.safe_load(stream)


class kafka_utils:
    def __init__(self):
        # kafka details

        self.config['kafka_topic'] = os.getenv('KAFKA_OUTPUT_TOPIC')	
        self.config['kafka_ip'] = os.getenv('KAFKA_HOSTNAME')	
        self.config['kafka_error_topic'] = 'error_' + self.config['kafka_topic']
    
    def create_consumer(self):
        self.consumer = KafkaConsumer(self.config['kafka_topic'], bootstrap_servers=self.config['kafka_ip'], auto_offset_reset='earliest', group_id='test')

    def get_consumer(self):
        return self.consumer
        
    def create_producer(self):
        self.producer = KafkaProducer(bootstrap_servers=self.config['kafka_ip'], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
 
    def unparse_avro_from_kafka(self, msg, schema_path, from_kafka):
        schema = avro.schema.Parse(open(schema_path, 'r').read())
        if from_kafka:
            msg = msg.value
        bytes_reader = io.BytesIO(msg)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(schema)
        data = reader.read(decoder)
        data = json.loads(data)
        return data
    
    def produce_error(self,data):
        """
        writes the data to kafka topic
        """
        self.config['kafka_error_topic'].get_sync_producer().produce(data)






