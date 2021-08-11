import pymongo

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def init(conn_details):
    """
    This function initializes the configured storage component
    """
    conn_type = conn_details["type"]
    if conn_type == "SQL":
        init_sql(conn_details)
    if conn_type == "NOSQL":
        init_nosql(conn_details)


def init_sql(conn_details):
    """
    This function initializes the global SQLAlchemy engine based upon the configuration provided for the Storage Component.
    # Reference Link:
    # https://stackoverflow.com/q/63368099
    """

    global engine, Session
    engine = create_engine(conn_details['connection_string'])
    Session = sessionmaker(bind=engine)


def init_nosql(conn_details):
    """
    This function initializes the global NOSQL engine based upon the configuration provided for the Storage Component.
    Currently it is implemented only to support the requirements of MongoDB, but it can be extended.

    # Reference Link:
    # https://stackoverflow.com/q/63368099
    """
    global Session
    db_name = conn_details['name']
    if db_name == 'mongodb':
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        database = client[conn_details['database_name']]
        Session = database[conn_details['collection_name']]
