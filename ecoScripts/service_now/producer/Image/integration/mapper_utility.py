import os
import yaml
import json
from .kafka_utility import kafka_utils


class Mapper:
    def __init__(self):
        self.mapper_dict = self.load_config('mapper.yaml')
        self.kafka_utils = kafka_utils()

    def load_config(self,filename):
        """
        loads the configuration from the yaml file
        """
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)

    def map_input_to_aurora(self, response,input_config , schema_path):
        category = input_config['category']
        result = {'result': [], 'category': category, 'discovery_source': input_config['discovery_source'],
                                  'source_instance': input_config['source_instance']}
        for each in response['result']:
            resp = {}
            for key in self.mapper_dict[category].keys():
                resp[key] = each[self.mapper_dict[category][key]]
            result['result'].append(self.kafka_utils.convert_to_schema(resp, schema_path))
        result = self.kafka_utils.convert_to_schema(result, "schema/ParentSchema.avsc")
        return result
