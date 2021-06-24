import copy

from pymongo.cursor import Cursor

import settings
from db.AbstractStorageManager import AbstractStorageManager
from db.models.event_monitor import EventLog


def create_manager(db_config):
    # print(f"[Storage_Manager] dbConfig: {db_config}")
    db_type = db_config['type']
    if db_type == 'SQL':
        return SQLManager()
    if db_type == 'NOSQL' and db_config['name'] == 'mongodb':
        return MongoManager()


class SQLManager(AbstractStorageManager):
    def __init__(self):
        # print("[SQLManager] Init Done")
        self.session = settings.Session()

    def create_query(self, data):
        # print('[SQLManager] [create_query] Adding Object!')
        self.session.add(data)
        self.session.commit()

    def read_query(self,  data):
        return self.session.query(EventLog).filter_by(timestamp=data.timestamp)

    def update_query(self, data):
        event_obj: EventLog = self.read_query(data)
        event_obj.health_status = data.healthStatus
        event_obj.monitor_name = data.monitor_name
        self.session.commit()

    def delete_query(self, target_obj):
        self.session.delete(target_obj)
        self.session.commit()

    def list_query(self):
        self.session.query(EventLog).all()

    def __del__(self):
        # body of destructor
        print("[Storage_Manager] [SQLManger] Destroying Object")


class MongoManager(AbstractStorageManager):
    def __init__(self):
        self.session = settings.Session

    def create_query(self, data):
        return self.session.insert_one(data)
#

    def read_query(self,  data):
        result = self.session.find({'timestamp': data['timestamp']})
        resp = [ob for ob in result]
        if len(resp) > 0:
            return copy.deepcopy(resp[0])
        return resp

    def update_query(self, data):
        event_obj = self.read_query(data)
        if len(event_obj) == 0:
            return self.create_query(data)
        else:
            return self.session.replace_one(event_obj, data)

    def delete_query(self, data):
        return self.session.delete_one({"_id": data['timestamp']})

    def list_query(self):
        # print([d for d in self.session.find()])
        return self.session.find()

    def __del__(self):
        # body of destructor
        print("[Storage_Manager] [MongoManager] Destroying Object")
