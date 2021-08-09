from multiprocessing import Process

from typing import List
from db.storage_component import create_storage_component
from helper import convert_message
from kafka import KafkaConsumer
from settings import init
import helper


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

    def __init__(self, storage_config, hw_monitor_config_params: List,
                 sw_monitor_config_params: List, server_address: str = 'localhost:9092', ):
        super(StorageManager, self).__init__()
        Process.__init__(self)
        self.storage_config = storage_config
        configs = [hw_monitor_config_params, sw_monitor_config_params]

        # Fetching all the names of the monitors in the systems
        self.monitor_names = [monitor_config.component_name for config in configs for monitor_config in config]

        # initializing the event listener
        self.event_listener = KafkaConsumer(bootstrap_servers=server_address, client_id='storage_manager',
                                            enable_auto_commit=True, auto_commit_interval_ms=5000)

    def __run(self):
        self.store_messages()

    def run(self):
        """
        Starting the process for the storage manager
        """
        super().run()
        self.start_storage()
        self.__run()

    def store_messages(self):
        """
        If the storage is configured,
        this method keeps reading the message stream on Kafka Topic
        and stores them to configured Storage Component.
        """
        if self.storage_config['enable_storage']:
            storage_name = self.storage_config['config']['storage_name']
            storage_config = self.storage_config['available_storages'][storage_name]
            init(storage_config)
            storage_manager = create_storage_component(storage_config)

            for message in self.event_listener:

                if message.topic == self.storage_config['control_channel']:
                    # If the received message is on control channel,
                    # we need to update our kafka consumer.
                    self.update_storage_event_listener(helper.deserialize(message))
                else:
                    # else we store the message to the configured storage component
                    event_log = convert_message(message, storage_config['type'])
                    storage_manager.create_query(event_log)

    def start_storage(self):
        """
        If the storage has been enabled,
        this method attaches the kafka consumer to available Kafka Topics
        """
        if self.storage_config['enable_storage']:
            topics = list(self.event_listener.topics())
            topics = [topic_name for monitor_name in self.monitor_names for topic_name in topics if
                      monitor_name in topic_name]
            topics.append(self.storage_config['control_channel'])
            self.event_listener.subscribe(topics)

    def update_storage_event_listener(self, msg):
        """
        Depending upon the received command signal, we attach or detach from kafka topics
        """
        message = msg['message']
        target_ids = msg['target_id']
        msg_type = msg['type']

        if msg_type == 'cmd':
            topics = self.monitor_names.copy()

            if message['command'] == 'activate':
                for target in target_ids:
                    if target not in self.monitor_names:
                        topics.append(target)

            if message['command'] == 'shutdown':
                for target in target_ids:
                    if target in self.monitor_names:
                        topics.remove(target)

            if topics != self.monitor_names:
                topics.append(self.storage_config['control_channel'])
                self.event_listener.subscribe(topics)
