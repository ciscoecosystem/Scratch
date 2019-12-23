import os
import signal
import inspect

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# absolute import
# from consumer.logger import Logger
# relative import
from .logger import Logger

# TODO handle pymongo.errors
class Database:

    def __init__(self, host='localhost', port=27017):
        self.logger = Logger.get_logger()
        self.logger.info("Connecting to MongoDB")
        try:
            self.client = MongoClient(host, port, serverSelectionTimeoutMS=1000)
            self.client.admin.command('ismaster') # cheap/no auth connection check
        except ConnectionFailure as error:
            self.logger.error("Connection to database failed. Error = "+str(error))
            # TODO exit
            self.logger.error("Shutting down")
            # os.kill(os.getpid(), signal.SIGINT)
            raise

        self.db = self.client.aurora
        # TODO create appropriate indices?
        # db.['epgs'].create_index("epg_name")

    def clear_database(self):
        self.client.drop_database('aurora')
        self.logger.info("Dropped database 'aurora'")

    ##### Endpoint Collection ######

    def get_endpoint(self, name, identifier='id'):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'sys_id':
            filter = {'sys_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        collection = self.db['endpoints']
        return collection.find_one(filter=filter)

    def insert_endpoint(self, doc):
        collection = self.db['endpoints']
        collection.insert_one(doc)

    def update_endpoint(self, name, update, identifier='id'):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        collection = self.db['endpoints']
        collection.update_one(filter, update)

    def delete_endpoint(self, name, identifier='id'):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        collection = self.db['endpoints']
        collection.delete_one(filter)

    ##### EPG Collection #####

    def update_endpoint_membership(self, old_epg, new_epg, ep_id):
        epg_collection = self.db['epgs']
        end_collection = self.db['endpoints']

        epg_collection.update_one({"name": old_epg}, {'$pullAll': {'members':[ep_id]}})
        epg_collection.update_one({"name": new_epg}, {'$push': {'members':[ep_id]}})
        end_collection.update_one({'_id': ep_id}, {'$set': {'epg': new_epg}})

    def get_epg(self, name, identifier='id', tenant=None, ap=None):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name' and tenant and ap:
            filter = {'name': name, 'tenant': tenant, 'ap': ap}
        else:
            return

        collection = self.db['epgs']
        return collection.find_one(filter=filter)

    def insert_epg(self, document):
        """Create a new document in the 'epgs' collection for a given epg
        Does not modify database if EPG already exist
        """
        collection = self.db['epgs']
        collection.insert_one(document)

        collection_epg_count = self.db['epgCount']
        collection_epg_count.insert_one(document)

    def count_epgs(self):
        count = self.db['epgCount'].count_documents({})
        return count

    def delete_epg(self, name, identifier='id'):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        collection = self.db['epgs']
        collection.delete_one(filter)

    def update_epg_membership(self, name, update, remove=False, identifier='id'):
        """Set endpoints membership to list given by update
        If remove=True, remove all endpoints in the update list
        """
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        # TODO remove membership from old EPG if endpoint was previously in different EPG
        # logger.debug("Adding endpoint {} to EPG {}".format(ep_id, epg_name))
        # update = {'$setOnInsert': epg, '$addToSet': {'members': ep_id}}
        # update = {'$pullAll': {'members': list(removed)}, '$push': {'members': {'$each': list(added)}}}
        if remove:
            update = {'$pullAll': {'members': update}}
        else:
            update = {'$set': {'members': update}}

        epg_collection = self.db['epgs']
        end_collection = self.db['endpoints']
        return epg_collection.update_one(filter, update)

    ##### Contract Collection #####

    def add_contract(self, role, epg_id, contract_id):
        """Add contract to EPG document as provider or consumer"""
        assert role == 'consumed' or role == 'provided'

        collection = self.db['epgs']
        collection.update_one({'_id': epg_id}, {'$addToSet': {role: contract_id}})


    def add_contract_by_name(self, role, epg_name, contract_id):
        """Add contract to EPG document as provider or consumer"""
        assert role == 'consumed' or role == 'provided'

        collection = self.db['epgs']
        collection.update_one({'name': epg_name}, {'$addToSet': {role: contract_id}})


    def remove_contract(self, role, epg_id, contract_id):
        """Remove contract from EPG document"""
        assert role == 'consumed' or role == 'provided'

        collection = self.db['epgs']
        collection.update_many({'_id': epg_id}, {'$pullAll': {role: [contract_id]}})


    def remove_contract_by_name(self, role, epg_name, contract_id):
        """Remove contract from EPG document"""
        assert role == 'consumed' or role == 'provided'

        collection = self.db['epgs']
        collection.update_many({'name': epg_name}, {'$pullAll': {role: [contract_id]}})

    def update_contract_filter(self, name, aci_filter, entries, identifier='id'):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        update = {'$set': {'filter_entries': entries, 'filter_name': aci_filter}}

        collection = self.db['contracts']
        return collection.update_one(filter, update)

    def update_contract_membership(self, name, role, update, identifier='id', remove=False):
        """Set contract providers or consumers to list given by update
        If remove=True, remove all EPGs in the update list instead
        """
        assert role == 'consumed' or role == 'provided'
        role = 'consumer_epg' if role == 'consumed' else 'provider_epg'

        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        if remove:
            update = {'$pullAll': {role: remove}}
        else:
            update = {'$set': {role: update}}

        collection = self.db['contracts']
        return collection.update_one(filter, update)

    def get_contract(self, name, identifier='id'):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        collection = self.db['contracts']
        return collection.find_one(filter=filter)


    def insert_contract(self, doc):
        collection = self.db['contracts']
        collection.insert_one(doc)
        # Below is to maintain the count of contracts
        collection_contract_count = self.db['contractCount']
        collection_contract_count.insert_one(doc)


    def count_contracts(self):
        count = self.db['contractCount'].count_documents({})
        return count


    def delete_contract(self, name, identifier='id'):
        if identifier == 'id':
            filter = {'_id': name}
        elif identifier == 'name':
            filter = {'name': name}
        else:
            return

        collection = self.db['contracts']
        collection.delete_one(filter)

    ##### Filter Collection ######

    def get_filter(self, name):
        # REVIEW if implemented by matching filter_entries, might need to maintain
        # sorted arrays in docs for query performance

        filter = {'_id': name}

        collection = self.db['filters']
        return collection.find_one(filter=filter)


    def insert_filter(self, name, tenant, entries):
        document = {'_id': name, 'tenant': tenant, 'entries': entries}

        collection = self.db.filters
        collection.insert_one(document)


def operation(func):
    def db_function(*args):
        try:
            func(*args)
        except OperationFailure as e:
            self.logger.error("Database operation failed")

    return db_function

if __name__ == '__main__':
    c = MongoClient()
    db = c.aurora.epgs
