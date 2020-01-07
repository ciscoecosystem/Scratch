import os
import json
import io
import avro.schema
from pykafka import KafkaClient
from avro.io import DatumWriter




class kafka_utils:
    def __init__(self):
        # kafka details
        self.kafka_hostname = os.getenv('KAFKA_HOSTNAME')
        self.kafka_port = os.environ.get('KAFKA_PORT')
        #Since this kafka_utility is same for producer and consumer, we have put if condition.
        if os.environ.get('PRODUCER_TOPIC'):
            #os.environ.get('PRODUCER_TOPIC') is output topic for producer and input topic for beam module.
            self.producer_topic = os.environ.get('PRODUCER_TOPIC')
            #using this topic to fetch data from input system(e.g SNOW) from 'n'-duration in days which configurable on runner config page.         
            self.kafka_offset_topic = "offset_" + self.producer_topic
        
        if os.environ.get('CONSUMER_TOPIC'):
            #os.environ.get('CONSUMER_TOPIC') is input topic for consumer and output topic for beam module.
            self.consumer_topic = os.environ.get('CONSUMER_TOPIC')
            self.kafka_error_topic = 'error_' + self.consumer_topic

    def create_kafka_client(self):
        #There is some issue in pykafka library. Here 3000 ms = 30 seconds
        self.client = KafkaClient(hosts='{}:{}'.format(self.kafka_hostname, self.kafka_port), socket_timeout_ms=3000)

    def convert_to_schema(self, data, schema_path):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), schema_path)
        schema = avro.schema.Parse(open(schema_path, 'r').read())
        writer = avro.io.DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)
        value = bytes_writer.getvalue()
        return value

    def get_producer_output_topic(self):
        return self.client.topics[self.producer_topic]
        
    def get_snow_offset_topic(self):
        return self.client.topics[self.kafka_offset_topic]
    
    def get_consumer_error_topic(self):
        return self.client.topics[self.kafka_error_topic]

    def write_data(self,write_data):
        """
        writes the data to kafka topic
        """
        self.producer.produce(write_data)

    def get_consumer_input_topic(self):
        return self.client.topics[self.consumer_topic]

    def create_consumer_topic(self, topic,auto_offset_reset=-2,reset_offset_on_start=False,consumer_group=None):
        #auto_offset_reset -2 for earliest and -1 for latest. default is -2
        self.consumer = topic.get_simple_consumer(auto_offset_reset=auto_offset_reset, reset_offset_on_start=reset_offset_on_start,consumer_group=consumer_group )

    def create_producer_topic(self, topic, max_request_size=1000012):
        #default max_request_size for kafka is 1000012
        self.producer = topic.get_sync_producer(max_request_size = max_request_size)

    def get_consumer(self):
        return self.consumer
    def unparse_avro_from_kafka(self, msg, schema_path, from_kafka):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), schema_path)
        schema = avro.schema.Parse(open(schema_path, 'r').read())
        if from_kafka:
            msg = msg.value
        bytes_reader = io.BytesIO(msg)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(schema)
        data = reader.read(decoder)
        return data
    
