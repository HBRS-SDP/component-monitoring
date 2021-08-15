import json
import logging
from multiprocessing import Process
from typing import Optional, Dict, Union

from jsonschema import validate
from kafka import KafkaConsumer, KafkaProducer
from kafka.consumer.fetcher import ConsumerRecord
from kafka.producer.future import FutureRecordMetadata

from component_monitoring.component import Component
from component_monitoring.messaging.enums import MessageType, Response
from component_monitoring.storage.models.event_monitor import EventLog
from component_monitoring.storage.settings import init
from component_monitoring.storage.storage_component import create_storage_component
from helper import deserialize, serialize


# from storage import DB_Manager
# Convert threads into Processes.
# Update the list of DB Processes
# Fault Tolerant DB Manager

# from storage import DB_Manager

class StorageManager(Component):
    """
    This class supports multiprocess approach to store the monitoring data.
    It makes use of Configured Data Storage to store the incoming messaging from the subscribed Kafka Topic.
    """

    def __init__(self, storage_config, server_address: str = 'localhost:9092'):
        Component.__init__(self, 'storage_manager', server_address=server_address, control_channel=storage_config['control_channel'])
        self._id = "storage_manager"
        self.storage_config = storage_config
        self.monitors = dict()
        self.topics = list()

        # initializing the event listener
        self.consumer = None
        self.producer = None

    def run(self):
        """
        Starting the process for the storage manager
        """
        super().run()
        self.start_storage()
        self.store_messages()

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

            for msg in self.consumer:

                if msg.topic == self.storage_config['control_channel']:
                    # If the received message is on control channel,
                    # we need to update our kafka consumer.
                    message = self.deserialize(msg)
                    print(self.validate_request(message))
                    if self.validate_request(message) and message['To'] == self._id:
                        self.update_storage_event_listener(message)
                    elif self.validate_broadcast(message):
                        self.update_active_monitors(message)
                elif msg.topic in self.topics:
                    # else we store the message to the configured storage component
                    print(self.deserialize(msg))
                    event_log = self.convert_message(msg, storage_config['type'])
                    storage_manager.create_query(event_log)

    def update_active_monitors(self, message: Dict) -> None:
        message_type = self.get_message_type(message)
        if message_type == MessageType.HELO:
            helo = message[message_type.value]
            self.monitors[message['From']] = helo['Topic']
        elif message_type == MessageType.BYE:
            bye = message[message_type.value]
            del self.monitors[message['From']]

    def start_storage(self):
        """
        If the storage has been enabled,
        this method attaches the kafka consumer to available Kafka Topics
        """
        self.consumer = KafkaConsumer(bootstrap_servers=self.server_address, client_id='storage_manager',
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.producer = KafkaProducer(bootstrap_servers=self.server_address, value_serializer=serialize)
        if self.storage_config['enable_storage']:
            self.topics = [self.storage_config['control_channel']]
            self.consumer.subscribe(self.topics)

    def update_storage_event_listener(self, message):
        """
        Depending upon the received command signal, we attach or detach from kafka topics
        """
        message_type = self.get_message_type(message)
        print(message)
        if message_type == MessageType.START:
            print("################################")
            self.topics.append(self.monitors[message['From']])
            self.consumer.subscribe(list(self.topics))
            self.send_response(message['Id'], message['From'], Response.OKAY, None)

    @staticmethod
    def convert_message(message: ConsumerRecord, db_type: str) -> Union[EventLog, Dict]:
        """
        Convert a Kafka ConvumerRecord into a Database entry
        @param message: Event message to be converted
        @param db_type: Database type: One of [SQL, NOSQL]
        @return: For SQL database: EventLog; For NOSQL: JSON Dict of the converted event message
        """
        timestamp = message.timestamp
        value = deserialize(message)
        monitor_name = value['monitorName']
        health_status = json.dumps(value['healthStatus'])
        if db_type == 'SQL':
            return EventLog(timestamp, monitor_name, health_status)
        json_msg = {"_id": message.timestamp, "timestamp": message.timestamp,
                    "monitorName": monitor_name, "healthStatus": health_status}
        return json_msg
