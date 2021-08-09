import json
from signal import SIGINT, signal

import yaml

from db.storage_component import SQLStorageComponent, create_storage_component
from helper import convert_message
from kafka import KafkaConsumer
from settings import init

# from db import DB_Manager


class DB_Storage:
    # def __init__(self, config, topic_name="hsrb_monitoring_rgbd"):
    def __init__(self, config, topic_name="hsrb_monitoring_feedback_rgbd"):

        # Constant to connect to kafka topic
        self.topic_name = topic_name

        # Kakfa topic listener
        self.event_listener = KafkaConsumer(
            topic_name, value_deserializer=lambda m: json.loads(m.decode('utf-8')))

        self.config = config

    def store_messages(self):
        if self.config['enable_storage']:
            db_name = self.config['config']['storage_name']
            db_config = self.config['available_storages'][db_name]
            init(db_config)
            storage_manager = create_storage_component(db_config)
            for message in self.event_listener:
                event_log = convert_message(message, db_config['type'])
                storage_manager.create_query(event_log)


def exit_handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully! Cheers :D')
    exit(0)


if __name__ == '__main__':

    # Reference Link:
    # https://www.devdungeon.com/content/python-catch-sigint-ctrl-c
    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, exit_handler)

    # use yaml
    with open('properties.yaml') as json_file:
        config_data = yaml.safe_load(json_file)

    db_storage = DB_Storage(
        config_data, topic_name="hsrb_monitoring_feedback_rgbd")
    db_storage.store_messages()
