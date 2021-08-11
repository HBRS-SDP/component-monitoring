import copy

from pymongo.cursor import Cursor

from storage import settings
from storage.abstract_storage_component import AbstractStorageComponent
from storage.models.event_monitor import EventLog


def create_storage_component(db_config):
    """
    This function is responsible to initialize the required Storage Component depending upon the application configuration.
    """
    db_type = db_config['type']
    if db_type == 'SQL':
        return SQLStorageComponent()
    if db_type == 'NOSQL' and db_config['name'] == 'mongodb':
        return MongoStorageComponent()


class SQLStorageComponent(AbstractStorageComponent):
    """
    SQLManager is responsible for all SQL operations on SQL-based Database.
    It uses the SQLAlchemy ORM to provide a generic way to switch between any SQL-based Database provider by minimal changes in configurations.
    """

    def __init__(self):
        self.session = settings.Session()

    def create_query(self, data):
        """
        This method runs the insert query on the required table of the SQL database.
        In short it inserts a row in the SQL table.
        It expects the data to be an object of extension of SQLAlchemy's Base class.
        """
        self.session.add(data)
        self.session.commit()

    def read_query(self,  data):
        """
        This method runs the select query on the required table of the SQL database.
        Inshort, it reads a row from the SQL table depending upon the timestamp.
        It expects the data to be an object of extension of SQLAlchemy's Base class.
        """
        return self.session.query(EventLog).filter_by(timestamp=data.timestamp)

    def update_query(self, data):
        """
        This method updates a data row in the required table of the SQL database.
        It expects the data to be an object of extension of SQLAlchemy's Base class.
        """
        event_obj: EventLog = self.read_query(data)
        event_obj.health_status = data.healthStatus
        event_obj.monitor_name = data.monitor_name
        self.session.commit()

    def delete_query(self, target_obj):
        """
        This method runs the delete query on the required table of the SQL database.
        Inshort it deletes a row in the SQL table.
        It expects the data to be an object of extension of SQLAlchemt's Base class.
        """
        self.session.delete(target_obj)
        self.session.commit()

    def list_query(self):
        """
        This method runs the `select *`` query on the required table of the SQL database and returns all the rows of the query.
        """
        self.session.query(EventLog).all()

    def __del__(self):
        print("[Storage_Manager] [SQLManger] Destroying Object")


class MongoStorageComponent(AbstractStorageComponent):
    def __init__(self):
        self.session = settings.Session

    def create_query(self, data):
        """
        This method inserts data into the required collection of the MonogDB.
        Inshort it inserts a document in the MonogDB collection.
        It expects the data to be a python dictionary object.
        """
        print("store")
        return self.session.insert_one(data)

    def read_query(self,  data):
        """
        This method reads the document from the required collection of the MonogDB having the particular timestamp.
        It expects the data to be a python dictionary object.
        """
        result = self.session.find({'timestamp': data['timestamp']})
        resp = [ob for ob in result]
        if len(resp) > 0:
            return copy.deepcopy(resp[0])
        return resp

    def update_query(self, data):
        """
        This method updates document into the required collection of the MonogDB.
        It expects the data to be a python dictionary object.
        """
        event_obj = self.read_query(data)
        if len(event_obj) == 0:
            return self.create_query(data)
        else:
            return self.session.replace_one(event_obj, data)

    def delete_query(self, data):
        """
        This method deletes document from the required collection of the MonogDB based on the timestamp attribute.
        It expects the data to be a python dictionary object.
        """
        return self.session.delete_one({"_id": data['timestamp']})

    def list_query(self):
        """
        This method lists all documents from the required collection of the MonogDB.
        """
        return self.session.find()

    def __del__(self):
        print("[Storage_Manager] [MongoManager] Destroying Object")