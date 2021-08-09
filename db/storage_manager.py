import json
from signal import SIGINT, signal
from multiprocessing import Process

import yaml

from db.storage_component import create_storage_component
from helper import convert_message
from kafka import KafkaConsumer
from settings import init


# from db import DB_Manager
# Convert threads into Processes.
# Update the list of DB Processes
# Fault Tolerant DB Manager

# from db import DB_Manager

class StorageManager(Process):
    """
    This class supports multi-threaded approach to store the monitoring data.
    It makes use of Configured Data Storage to store the incoming messages from the subscribed Kafka Topic.
    """

    def __init__(self, storage_config,server_address: str = 'localhost:9092'):
        super(StorageManager, self).__init__()
        Process.__init__(self)

        self.storage_config = storage_config

        self.event_listener = KafkaConsumer(bootstrap_servers=server_address, client_id='storage_manager', enable_auto_commit=True, auto_commit_interval_ms=5000)

        # self.event_listener = KafkaConsumer(
        #     self.storage_config['storage_kafka_topic'], value_deserializer=lambda m: json.loads(m.decode('utf-8')),client_id='storage_manager',
        #                               enable_auto_commit=True, auto_commit_interval_ms=5000,bootstrap_servers=server_address)

    def __run(self):

        self.store_messages()

    def run(self):
        super().run()
        self.event_listener.subscribe(self.storage_config['storage_kafka_topic'])
        print('\n\nSubscribing\n\n')
        self.__run()

    def store_messages(self):
        """
        If the storage is configured, this method keeps reading the message stream on Kafka Topic and stores them to configured Storage Component.
        """
        if self.storage_config['enable_storage']:
            storage_name = self.storage_config['config']['storage_name']
            storage_config = self.storage_config['available_storages'][storage_name]
            init(storage_config)
            storage_manager = create_storage_component(storage_config)
            # print("="*50)
            # print("configured storage!")
            # print("="*50)
            response = self.event_listener.poll()
            print("="*50)
            print(f"Got response in {response}")
            print("="*50)
            for message in self.event_listener:
                print("="*50)
                print("Got message in DB")
                print("="*50)
                event_log = convert_message(message, storage_config['type'])
                storage_manager.create_query(event_log)

    def start_storage(self):
        pass

    def stop_storage(self):
        pass


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

    db_storage = StorageManager(
        config_data, topic_name="hsrb_monitoring_feedback_rgbd")
    db_storage.store_messages()
