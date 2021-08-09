import json
from multiprocessing import Process
from signal import SIGINT, signal
from threading import Thread

import yaml

from db.Storage_Manager import SQLManager, create_manager
from helper import convert_message
from kafka import KafkaConsumer
from settings import init

# from db import DB_Manager


class DB_Storage(Process):
    """
    This class supports multi-threaded approach to store the monitoring data.
    It makes use of Configured Data Storage to store the incoming messages from the subscribed Kafka Topic.
    """

    def __init__(self, config, topic_name="hsrb_monitoring_feedback_rgbd"):
        super(DB_Storage, self).__init__()
        self.topic_name = topic_name
        self.event_listener = KafkaConsumer(
            topic_name, value_deserializer=lambda m: json.loads(m.decode('utf-8')))
        self.config = config

    def start(self):
        self.store_messages()

    def store_messages(self):
        """
        If the storage is configured, this method keeps reading the message stream on Kafka Topic and stores them to configured Storage Component.
        """
        if self.config['enable_storage']:
            db_name = self.config['config']['storage_name']
            db_config = self.config['available_storages'][db_name]
            init(db_config)
            storage_manager = create_manager(db_config)
            for message in self.event_listener:
                event_log = convert_message(message, db_config['type'])
                storage_manager.create_query(event_log)


def exit_handler(signal_received, frame):
    """
    If this file was run as the python program, we can capture the signal and take required action.
    Currently this method detects ctrl-c key combo and prints the message that the program is Exiting.
    But this function can be updated as per the requirements.
    # Handle any cleanup here
    """
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
    db_storage.start()
    db_storage.join()
