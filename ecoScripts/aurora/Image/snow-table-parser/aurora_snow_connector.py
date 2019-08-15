import os
import sys
import time
import json
import yaml
import queue
import requests
from bs4 import BeautifulSoup
from pykafka import KafkaClient
from pykafka.common import OffsetType
from datetime import datetime, timedelta, timezone

from logger import Logger
from exception_handler import handle_exception

class snow_data:
    @handle_exception
    def __init__(self):
        config_dict = self.load_config()
        self.logger = Logger.get_logger()
        
        # kafka details
        self.kafka_ip = os.environ.get(config_dict['kafka_ip'])
        self.kafka_port = os.environ.get(config_dict['kafka_port'])
        self.initial_offset = config_dict['initial_offset']
        self.kafka_data_topic = os.environ.get(config_dict['kafka_data_topic'])
        self.kafka_offset_topic = os.environ.get(config_dict['kafka_offset_topic'])
        self.restart_from_offset = config_dict['restart_from_offset']
        
        # SNOW configs
        self.snow_url = config_dict['snow_url']
        self.snow_username = config_dict['snow_username']
        self.snow_password = config_dict['snow_password']
        self.source_instance = config_dict['source_instance']
        self.discovery_source = config_dict['discovery_source']

        # polling interval
        self.polling_interval = config_dict['polling_interval']
        
        # SNOW tables
        self.parent_table = config_dict['parent_table']
        self.child_tables = config_dict['child_tables']
        self.delete_table = config_dict['delete_table']
        self.relationship_table = config_dict['relationship_table']
        self.relationship_type_table = config_dict['relationship_type_table']

    
    @handle_exception
    def load_config(self):
        """
        loads the configuration from the yaml file
        """
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)

    
    @handle_exception
    def get_checkpoint(self, client):
        """
        gets the last_query_time from the kafka topic
        """
        offset_topic = client.topics[self.kafka_offset_topic]
        offset_consumer = offset_topic.get_simple_consumer(auto_offset_reset=OffsetType.LATEST, reset_offset_on_start=True)
        for p, op in offset_consumer._partitions.items():
            if op.next_offset < 2:
                self.write_checkpoint(client, self.initial_offset)
                self.write_checkpoint(client, self.initial_offset)
            offsets = [(p, op.next_offset - 2)]
        offset_consumer.reset_offsets(offsets)
        return offset_consumer.consume().value.decode('utf-8')

    
    @handle_exception
    def write_checkpoint(self, client, current_query_time):
        """
        writes the current_query_time to the kafka topic
        """
        offset_topic = client.topics[self.kafka_offset_topic]
        offset_producer = offset_topic.get_sync_producer()
        current_query_time = str(current_query_time)
        offset_producer.produce(str.encode(current_query_time))

    
    @handle_exception
    def read_data(self, table, query):
        """
        read the CI from SNOW
        """
        query_url = '{}/api/now/table/{}?{}'.format(self.snow_url, table, query)
        response = requests.get(query_url, auth=(self.snow_username, self.snow_password))
        self.logger.debug('Response of read data from table {}: {}'.format(table, response.text))
        return response.json()

    
    @handle_exception
    def filter_table_data(self, response, query):
        """
        filter the response on the basis of the tables
        and make a query of that table
        and store the result in filtered_response
        """
        mark_table = []
        filtered_response = dict()
        filtered_response['result']= []
        for result in response['result']:
            table_name = result['sys_class_name']
            # TODO: Replace ```table_name == 'cmdb_ci_vmware_instance'``` with ```table_name in self.child_tables``` in below if condition
            if table_name == 'cmdb_ci_vmware_instance' and table_name not in mark_table:
                table_response = self.read_data(table_name, query)
                filtered_response['result'] += table_response['result']
                mark_table.append(table_name)
        return filtered_response

    
    @handle_exception
    def form_query(self, time_filter):
        """
        forms the query for delete table
        query includes time filter, child tables and rel tables
        """
        query = time_filter
        query = '{}^tablename={}'.format(query, self.relationship_table)
        for table in self.child_tables:
            query = '{}^ORtablename={}'.format(query, table)
        return query

    
    @handle_exception
    def create_ci_info(self, response, category):
        """
        adds the discovery_source, source_instance and category
        to the response
        """
        response['discovery_source'] = self.discovery_source
        response['source_instance'] = self.source_instance
        response['category'] = category
        return response

    
    @handle_exception
    def write_data(self, producer, write_data):
        """
        writes the data to kafka topic
        """
        value = json.dumps(write_data)
        value = value.encode('utf-8')
        producer.produce(value)

    
    @handle_exception
    def query_tables(self, tablename, last_query_time, current_query_time, query, to_filter, category, data_producer):
        """
        queries the tables and writes the data in the kafka topic
        """
        self.logger.info('Reading all the records from SNOW table {} updated between {} UTC and {} UTC'.format(tablename, last_query_time, current_query_time))
        response = self.read_data(tablename, query)
        if to_filter:
            self.logger.info('Filter the read table data')
            response = self.filter_table_data(response, query)
        if len(response['result']) > 0:
            response = self.create_ci_info(response, category)
            self.logger.info('Writing the data in the kafka topic')
            self.write_data(data_producer, response)


    @handle_exception
    def start_timer(self):
        time.sleep(self.polling_interval)


    def main(self):
        try:
            # starting the kafka producer
            self.logger.info('Starting the kafka producer')
            client = KafkaClient(hosts = '{}:{}'.format(self.kafka_ip, self.kafka_port))
            data_topic = client.topics[self.kafka_data_topic]
            data_producer = data_topic.get_sync_producer()

            if self.restart_from_offset:
                self.write_checkpoint(client, self.initial_offset)
                self.write_checkpoint(client, self.initial_offset)

            while True:
                # get the last query time and write current query time in the kafka topic
                last_query_time = self.get_checkpoint(client)
                current_query_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                self.write_checkpoint(client, current_query_time)

                query = 'sysparm_query=sys_updated_onBETWEENjavascript:\'{}\'@javascript:\'{}\''.format(last_query_time, current_query_time)
                self.query_tables(self.parent_table, last_query_time, current_query_time, query, True, 'ep', data_producer)
                time.sleep(1)

                # TODO: add read query in below line
                query = ''
                self.query_tables(self.relationship_type_table, last_query_time, current_query_time, query, False, 'reltype', data_producer)
                time.sleep(1)

                # TODO: remove type.sys_id filter from the below query
                query = 'sysparm_query=sys_updated_onBETWEENjavascript:\'{}\'@javascript:\'{}\'&type.sys_id=1a9cb166f1571100a92eb60da2bce5c5'.format(last_query_time, current_query_time)
                self.query_tables(self.relationship_table, last_query_time, current_query_time, query, False, 'rel', data_producer)
                time.sleep(1)

                if str(last_query_time) != str(self.initial_offset):
                    query = self.form_query('sysparm_query=sys_updated_onBETWEENjavascript:\'{}\'@javascript:\'{}\''.format(last_query_time, current_query_time))
                    self.query_tables(self.delete_table, last_query_time, current_query_time, query, False, 'delete', data_producer)

                while True:
                    variable = input('Make the changes on the SNOW. Press y\n')
                    if variable != 'y':
                        continue
                    variable = input('Are you sure? Press y\n')
                    if variable != 'y':
                        continue
                    break
                
                # self.logger.info('Starting the timer')
                # self.start_timer()
                # self.logger.info('Timer over\n')
        except Exception as e:
            self.logger.error(e)
            self.logger.error('Exiting code')
            sys.exit()
            

if __name__ == '__main__':
    sd = snow_data()
    sd.main()
