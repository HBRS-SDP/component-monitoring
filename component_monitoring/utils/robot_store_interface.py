import time
import pymongo as pm

class RobotStoreInterface(object):
    def __init__(self, db_name='robot_store',
                 monitor_collection_name='status',
                 component_sm_state_collection_name='component_sm_states',
                 db_port=27017):
        self.db_name = db_name
        self.db_port = db_port
        self.monitor_collection_name = monitor_collection_name
        self.component_sm_state_collection_name = component_sm_state_collection_name

    def store_monitor_msg(self, component_status_list):
        try:
            client = pm.MongoClient(port=self.db_port)
            db = client[self.db_name]
            collection = db[self.monitor_collection_name]

            status_msg = dict()
            status_msg['id'] = 'status'
            status_msg['timestamp'] = time.time()
            status_msg['status'] = component_status_list
            collection.replace_one({'id': 'status'}, status_msg, upsert=True)
        except pm.errors.OperationFailure as exc:
            print('[component_monitoring/store_monitor_msg] {0}'.format(exc))

    def read_component_sm_status(self, component_name):
        try:
            client = pm.MongoClient(port=self.db_port)
            db = client[self.db_name]
            collection = db[self.component_sm_state_collection_name]
            state_doc = collection.find_one({'component_name': component_name})
            if state_doc:
                return state_doc['state']
        except pm.errors.OperationFailure as exc:
            print('[component_monitoring/read_component_sm_status] {0}'.format(exc))
        return 'unknown'
