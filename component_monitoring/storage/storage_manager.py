import json
import logging
from multiprocessing import Process
from typing import Optional, Dict, Union

from jsonschema import validate
from kafka import KafkaConsumer, KafkaProducer
from kafka.consumer.fetcher import ConsumerRecord
from kafka.producer.future import FutureRecordMetadata

from component_monitoring.messaging.enums import Command, MessageType, ResponseCode
from component_monitoring.storage.models.event_monitor import EventLog
from component_monitoring.storage.settings import init
from component_monitoring.storage.storage_component import create_storage_component
from helper import deserialize, serialize


# from storage import DB_Manager
# Convert threads into Processes.
# Update the list of DB Processes
# Fault Tolerant DB Manager

# from storage import DB_Manager

class StorageManager(Process):
    """
    This class supports multiprocess approach to store the monitoring data.
    It makes use of Configured Data Storage to store the incoming messages from the subscribed Kafka Topic.
    """

    def __init__(self, storage_config, server_address: str = 'localhost:9092'):
        Process.__init__(self)
        self._id = "storage_manager"
        self.storage_config = storage_config
        self.server_address = server_address
        self.monitors = dict()

        self.logger = logging.getLogger("storage_manager")
        self.logger.setLevel(logging.INFO)

        with open('component_monitoring/messaging/schemas/control.json', 'r') as schema:
            self.control_schema = json.load(schema)

        # initializing the event listener
        self.consumer = None
        self.producer = None

    def __send_control_message(self, msg) -> FutureRecordMetadata:
        """

        @param msg:
        @return:
        """
        result =  self.producer.send(self.storage_config['control_channel'], msg)
        return result

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

            for message in self.consumer:
                print(message)
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
        self.consumer = KafkaConsumer(bootstrap_servers=self.server_address, client_id='storage_manager',
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.producer = KafkaProducer(bootstrap_servers=self.server_address, value_serializer=serialize)
        if self.storage_config['enable_storage']:
            topics = [self.storage_config['control_channel']]
            self.consumer.subscribe(topics)

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
            print(message_body)
            # process message body for STORE and STOP_STORE REQUEST
            cmd = Command(message_body['command'])
            if cmd == Command.START_STORE:
                for monitor in message_body['monitors']:
                    self.monitors[monitor['name']] = monitor['topic']
            elif cmd == Command.STOP_STORE:
                for monitor in message_body['monitors']:
                    del self.monitors[monitor['name']]
            else:
                return
            topics = list(self.monitors.copy().values())
            if topics != self.monitors.values():
                topics.append(self.storage_config['control_channel'])
                print(topics)
                self.consumer.subscribe(topics)
            self.send_response(component, ResponseCode.SUCCESS, None)

    def send_response(self, receiver: str, code: ResponseCode, msg: Optional[Dict]) -> None:
        """
        Send a RESPONSE message over the control channel

        @param receiver: The component the message is addressed to
        @param code: The ResponseCode to be sent
        @param msg: The optional message to be included in the response
        @return: None
        """
        message = dict()
        message['from'] = self._id
        message['to'] = receiver
        message['message'] = MessageType.RESPONSE.value
        message['body'] = dict()
        message['body']['code'] = code.value
        if msg:
            for key, value in msg.items():
                message['body'][key] = value
        self.__send_control_message(message)

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
