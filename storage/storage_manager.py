import json
import logging
from multiprocessing import Process

from typing import List

from jsonschema import validate
from kafka.consumer.fetcher import ConsumerRecord

from component_monitoring.monitor_manager import Command, MessageType
from storage.models.event_monitor import EventLog
from storage.storage_component import create_storage_component
from helper import deserialize
from kafka import KafkaConsumer
from storage.settings import init


# from storage import DB_Manager
# Convert threads into Processes.
# Update the list of DB Processes
# Fault Tolerant DB Manager

# from storage import DB_Manager

class StorageManager(Process):
    """
    This class supports multi-threaded approach to store the monitoring data.
    It makes use of Configured Data Storage to store the incoming messages from the subscribed Kafka Topic.
    """

    def __init__(self, storage_config, server_address: str = 'localhost:9092', ):
        Process.__init__(self)
        self._id = "storage_manager"
        self.storage_config = storage_config
        self.server_address = server_address

        self.logger = logging.getLogger("storage_manager")
        self.logger.setLevel(logging.INFO)

        with open('component_monitoring/schemas/control.json', 'r') as schema:
            self.control_schema = json.load(schema)

        self.monitors = dict()

        # initializing the event listener
        self.event_listener = None

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
                    self.update_storage_event_listener(deserialize(message))
                else:
                    # else we store the message to the configured storage component
                    event_log = self.convert_message(message, storage_config['type'])
                    storage_manager.create_query(event_log)

    def start_storage(self):
        """
        If the storage has been enabled,
        this method attaches the kafka consumer to available Kafka Topics
        """
        self.event_listener = KafkaConsumer(bootstrap_servers=self.server_address, client_id='storage_manager',
                                            enable_auto_commit=True, auto_commit_interval_ms=5000)
        if self.storage_config['enable_storage']:
            topics = [self.storage_config['control_channel']]
            self.event_listener.subscribe(topics)

    def update_storage_event_listener(self, message):
        """
        Depending upon the received command signal, we attach or detach from kafka topics
        """
        try:
            validate(instance=message, schema=self.control_schema)
        except:
            self.logger.warning("Control message could not be validated!")
            self.logger.warning(message)
            return

        message_type = MessageType(message['message'])
        if self._id == message['to'] and MessageType.REQUEST == message_type:
            component = message['from']
            message_body = message['body']
            # process message body for STORE and STOP_STORE REQUEST
            cmd = Command(message_body['command'])
            if cmd == Command.START_STORE:
                for monitor in message_body['monitors']:
                    self.monitors[monitor['name']] = monitor['topic']
            elif cmd == Command.STOP_STORE:
                for monitor in message_body['monitors']:
                    del self.monitors[monitor]
            self.event_listener.subscribe(list(self.monitors.values()))

    @staticmethod
    def convert_message(message: ConsumerRecord, db_type: str):
        timestamp = message.timestamp
        value = deserialize(message)
        monitor_name = value['monitorName']
        health_status = json.dumps(value['healthStatus'])
        if db_type == 'SQL':
            return EventLog(timestamp, monitor_name, health_status)
        json_msg = {"_id": message.timestamp, "timestamp": message.timestamp,
                    "monitorName": monitor_name, "healthStatus": health_status}
        return json_msg
