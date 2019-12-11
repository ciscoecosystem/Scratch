import os
import json
from pykafka import KafkaClient




class kafka_utils:
    def __init__(self):
        # kafka details
        self.kafka_hostname = os.getenv('KAFKA_HOSTNAME')
        self.kafka_port = os.environ.get('KAFKA_PORT')
        #os.environ.get('KAFKA_INPUT_TOPIC') is output topic for producer and input topic for beam module.
        self.kafka_output_topic = os.environ.get('KAFKA_INPUT_TOPIC')
        #os.environ.get('KAFKA_INPUT_TOPIC') is input topic for consumer and output topic for beam module.
        self.kafka_input_topic = os.environ.get('KAFKA_OUTPUT_TOPIC')
        self.kafka_error_topic = 'error_' + self.kafka_input_topic
        #using this topic to fetch data from input system(e.g SNOW) from 'n'-duration in days which configurable on runner config page.         
        self.kafka_offset_topic = "offset-" + self.kafka_output_topic + "-" + self.kafka_input_topic

    def create_kafka_client(self):
        self.client = KafkaClient(hosts='{}:{}'.format(self.kafka_hostname, self.kafka_port))

    def get_producer_output_topic(self):
        return self.client.topics[self.kafka_output_topic]
        
    def get_snow_offset_topic(self):
        return self.client.topics[self.kafka_offset_topic]
    
    def get_consumer_error_topic(self):
        return self.client.topics[self.kafka_error_topic]

    def write_data(self,write_data):
        """
        writes the data to kafka topic
        """
        self.producer.produce(str.encode(write_data))

    def get_consumer_input_topic(self):
        return self.client.topics[self.kafka_input_topic]

    def create_consumer_topic(self,topic,auto_offset_reset=-2,reset_offset_on_start=False,consumer_group=None):
        #auto_offset_reset -2 for earliest and -1 for latest. default is -2
        self.consumer = topic.get_simple_consumer(auto_offset_reset=auto_offset_reset, reset_offset_on_start=reset_offset_on_start,consumer_group=consumer_group )

    def create_producer_topic(self,topic, max_request_size):
        #default max_request_size for kafka is 1000012
        self.producer = topic.get_sync_producer(max_request_size = max_request_size)

    def get_consumer(self):
        return self.consumer
        
    