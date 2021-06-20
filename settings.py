import pymongo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def init(conn_details):
    # print(f"[Settings] Connection Details : {conn_details}")
    conn_type = conn_details["type"]
    if conn_type == "SQL":
        init_sql(conn_details)
    if conn_type == "NOSQL":
        init_nosql(conn_details)


def init_sql(conn_details):

    # Reference Link:
    # https://stackoverflow.com/q/63368099
    global engine, Session
    engine = create_engine(conn_details['connection_string'])
    Session = sessionmaker(bind=engine)
    #print("[Settings] Init Session", Session)


def init_nosql(conn_details):
    global Session
    db_name = conn_details['name']
    if db_name == 'mongodb':
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        database = client[conn_details['database_name']]
        Session = database[conn_details['collection_name']]
    # print(f'[Settings] Init NOSQL - {db_name}')
