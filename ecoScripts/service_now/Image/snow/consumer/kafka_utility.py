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
        kafka_config_dict = load_config('kafka_config.yaml')
        

        # kafka details
        self.kafka_hostname = os.environ.get(kafka_config_dict['kafka_hostname'])
        self.kafka_port = os.environ.get(kafka_config_dict['kafka_port'])
        self.kafka_input_topic = os.environ.get(kafka_config_dict['kafka_input_topic'])
        self.kafka_output_topic = os.environ.get(kafka_config_dict['kafka_output_topic'])
        self.config['kafka_error_topic'] = 'error_' + self.config['kafka_output_topic']
        
        self.kafka_offset_topic = "offset-" + self.kafka_input_topic + "-" + self.kafka_output_topic

    def get_kafka_client(self):
        self.client = KafkaClient(hosts='{}:{}'.format(self.kafka_hostname, self.kafka_port))
        return self.client

    def convert_to_schema(self, data, schema_path):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), schema_path)
        schema = avro.schema.Parse(open(schema_path, 'r').read())
        writer = avro.io.DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)
        value = bytes_writer.getvalue()
        return value

    def get_topics(self):
        data_topic = self.client.topics[self.kafka_input_topic]
        return data_topic
    
    def get_offset_topic(self):
        offset_topic = self.client.topics[self.kafka_offset_topic]
        return offset_topic


    def write_data(self, producer, write_data):
        """
        writes the data to kafka topic
        """
        producer.produce(write_data)

    def create_cosumer(self):
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






