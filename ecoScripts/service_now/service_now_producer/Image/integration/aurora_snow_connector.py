import os
import sys
import time
import json
import io
import avro.schema
from avro.io import DatumWriter
import yaml
import requests
from pykafka import KafkaClient
from pykafka.common import OffsetType
from datetime import datetime, timedelta, timezone

from ..utils.logger import Logger
from exception_handler import handle_exception
from kafka_utility import kafka_utils


class snow_data:
    @handle_exception
    def __init__(self):
        config_dict = self.load_config()
        self.logger = Logger.get_logger()

        # kafka details
        self.initial_offset = self.get_time(os.environ.get(config_dict['initial_offset']))      
        self.restart_from_offset = config_dict['restart_from_offset']

        # SNOW configs
        self.snow_url = os.environ.get(config_dict['snow_url'])
        self.snow_username = os.environ.get(config_dict['snow_username'])
        self.snow_password = os.environ.get(config_dict['snow_password'])
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
    def get_time(self, days):
        """
        returns current time - given paramater 'days'
        """
        return (datetime.now() - timedelta(days=int(days))).strftime('%Y-%m-%d %H:%M:%S')


    @handle_exception
    def get_offset(self):
        """
        gets the last_query_time from the kafka topic

        writing offset twice intially as there's a bug
        in current kafka library - latest record can only
        be read if there are two records in the kafka topic
        """
        offset_topic = self.kafka_utils.get_snow_offset_topic()
        self.kafka_utils.create_consumer_topic(topic,auto_offset_reset=-1,reset_offset_on_start=True,consumer_group=None)
        offset_consumer = self.kafka_utils.get_consumer()
        for p, op in offset_consumer._partitions.items():
            # if there are less than 2 records in kafka topic, write the offset twice
            if op.next_offset < 2:
                self.write_offset(self.initial_offset)
                self.write_offset(self.initial_offset)
            offsets = [(p, op.next_offset - 2)]
        offset_consumer.reset_offsets(offsets)
        return offset_consumer.consume().value.decode('utf-8')


    @handle_exception
    def write_offset(self, current_query_time):
        """
        writes the current_query_time to the kafka topic
        """
        offset_topic = self.kafka_utils.get_snow_offset_topic()
        offset_producer = offset_topic.get_sync_producer()
        current_query_time = str(current_query_time)
        offset_producer.produce(current_query_time)


    @handle_exception
    def read_data(self, table, query):
        """
        read the CI from SNOW
        """
        query_url = '{}/api/now/table/{}?{}'.format(self.snow_url, table, query)
        response = requests.get(query_url, auth=(self.snow_username, self.snow_password))
        response = response.json()
        self.logger.info(
            'Length of response of read data from table {}, length: {}'.format(table, len(response['result'])))
        return response


    @handle_exception
    def filter_table_data(self, response, query):
        """
        filter the response on the basis of the tables
        and make a query of that table
        and store the result in filtered_response
        """
        filtered_response = dict()
        filtered_response['result'] = []
        tables = set([ci['sys_class_name'] for ci in response['result']])
        for table_name in tables:
            # TODO: Replace ```table_name == 'cmdb_ci_vmware_instance'``` with ```table_name in self.child_tables``` in below if condition
            if table_name == 'cmdb_ci_vmware_instance':
                table_response = self.read_data(table_name, query)
                filtered_response['result'] += table_response['result']

        # mark_table = []
        # filtered_response = dict()
        # filtered_response['result']= []
        # for result in response['result']:
        #     table_name = result['sys_class_name']
        #     # TODO: Take table name from customer
        #     # TODO: Replace ```table_name == 'cmdb_ci_vmware_instance'``` with ```table_name in self.child_tables``` in below if condition
        #     if table_name == 'cmdb_ci_vmware_instance' and table_name not in mark_table:
        #         table_response = self.read_data(table_name, query)
        #         filtered_response['result'] += table_response['result']
        #         mark_table.append(table_name)
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
    def parse_and_write_to_kafka(response, schema_path):
        result = {'result': [], 'category': category, 'discovery_source': self.discovery_source,
                                  'source_instance': self.source_instance}
        for resp in response['result']:
            result['result'].append(self.kafka_utils.convert_to_schema( resp, schema_path))
        result = self.kafka_utils.convert_to_schema(result, "schema/ParentSchema.avsc")
        self.kafka_utils.write_data(result)


    @handle_exception
    def query_tables(self, tablename, last_query_time, current_query_time, query, to_filter, category):
        """
        queries the tables and writes the data in the kafka topic
        """
        self.logger.info(
            'Reading all the records from SNOW table {} updated between {} UTC and {} UTC'.format(tablename,
                                                                                                  last_query_time,
                                                                                                  current_query_time))
        if to_filter:
            response = self.read_data(tablename, '{}&sysparm_fields=sys_class_name'.format(query))
            self.logger.info('Filter the read table data')
            response = self.filter_table_data(response, query)
        else:
            response = self.read_data(tablename, query)

        if len(response['result']) > 0:
            # response = self.create_ci_info(response, category)
            self.logger.info('Writing the data in the kafka topic')

            if tablename == self.parent_table:
                self.parse_and_write_to_kafka(response, "schema/EPSchema.avsc")

            elif tablename == self.relationship_type_table:
                self.parse_and_write_to_kafka(response, "schema/ReltypeSchema.avsc")

            elif tablename == self.relationship_table:
                self.parse_and_write_to_kafka(response, "schema/RelSchema.avsc")
    
            elif tablename == self.delete_table:
                self.parse_and_write_to_kafka(response, "schema/DelSchema.avsc")


    @handle_exception
    def start_timer(self):
        time.sleep(self.polling_interval)


    def main(self):
        try:
            # starting the kafka producer
            # TODO: initial offset should be current day - n days, n should be configurable
            self.logger.info('Starting the kafka producer')
            self.kafka_utils = kafka_utils()
            self.kafka_utils.create_kafka_client()
            self.kafka_utils.create_producer_topic(self.kafka_utils.get_producer_output_topic(),max_request_size=50000000) 

            if self.restart_from_offset:
                # writing offset twice intially as there's a bug in current kafka library - latest record can only be read if there are two records in the kafka topic
                self.write_offset(self.initial_offset)
                self.write_offset(self.initial_offset)

            while True:
                # get the last query time and write current query time in the kafka topic
                last_query_time = self.get_offset()
                current_query_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

                query = 'sysparm_query=sys_updated_onBETWEENjavascript:\'{}\'@javascript:\'{}\''.format(last_query_time,
                                                                                                        current_query_time)
                self.query_tables(self.parent_table, last_query_time, current_query_time, query, True, 'ep')
                # TODO: validate need of time.sleep(1)
                # time.sleep(1)

                # TODO: remove query below
                if str(last_query_time) != str(self.initial_offset):
                    query = 'sysparm_query=sys_updated_onBETWEENjavascript:\'{}\'@javascript:\'{}\'&sysparm_fields=sys_class_name'.format(
                        last_query_time, current_query_time)
                else:
                    query = ''
                self.query_tables(self.relationship_type_table, last_query_time, current_query_time, query, False,
                                  'reltype')

                # This is to slow down the producer
                # because beam is not able to get rel_type while processing rel
                # slowing down the producers solves the probleam
                time.sleep(3)

                # TODO: remove type.sys_id filter from the below query and rel type should also be configurable by customer
                query = 'sysparm_query=sys_updated_onBETWEENjavascript:\'{}\'@javascript:\'{}\'&type.sys_id=1a9cb166f1571100a92eb60da2bce5c5'.format(
                    last_query_time, current_query_time)
                self.query_tables(self.relationship_table, last_query_time, current_query_time, query, False, 'rel')
                # time.sleep(1)

                if str(last_query_time) != str(self.initial_offset):
                    query = self.form_query(
                        'sysparm_query=sys_updated_onBETWEENjavascript:\'{}\'@javascript:\'{}\''.format(last_query_time,
                                                                                                        current_query_time))
                    self.query_tables(self.delete_table, last_query_time, current_query_time, query, False, 'delete')

                    # while True:
                    #     variable = input('Make the changes on the SNOW. Press y\n')
                    #     if variable != 'y':
                    #         continue
                    #     variable = input('Are you sure? Press y\n')
                    #     if variable != 'y':
                    #         continue
                    #     break

                self.write_offset(current_query_time)

                self.logger.info('Starting the timer')
                self.start_timer()
                self.logger.info('Timer over\n')
        except Exception as e:
            self.logger.error(e)
            self.logger.error('Exiting snow')
            sys.exit()


if __name__ == '__main__':
    sd = snow_data()
    sd.main()
