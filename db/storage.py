import json
import logging
from multiprocessing import Process

from typing import List

from bson import json_util
from jsonschema import validate
from kafka.consumer.fetcher import ConsumerRecord

from db.models.event_monitor import EventLog
from db.storage_manager import create_storage_component
from kafka import KafkaConsumer
from db.settings import init


class Storage(Process):
    """
    This class supports multi-threaded approach to store the monitoring data.
    It makes use of Configured Data Storage to store the incoming messages from the subscribed Kafka Topic.
    """

    def __init__(self, storage_config, server_address: str = 'localhost:9092', ):
        Process.__init__(self)
        self.logger = logging.getLogger('storage')
        self.logger.setLevel(logging.INFO)
        self.storage_config = storage_config
        self.topics = list()

        with open('component_monitoring/schemas/event.json', 'r') as schema:
            self.event_schema = json.load(schema)

        # initializing the event listener
        self.event_listener = KafkaConsumer(bootstrap_servers=server_address, client_id='storage_manager',
                                            enable_auto_commit=True, auto_commit_interval_ms=5000)

    def run(self) -> None:
        """
        If the storage is configured,
        this method keeps reading the message stream on Kafka Topic
        and stores them to configured Storage Component.
        """
        if self.storage_config['enable_storage']:
            storage_name = self.storage_config['config']['storage_name']
            storage_config = self.storage_config['available_storages'][storage_name]
            self.logger.info(f"Initializing {storage_name}")
            init(storage_config)
            storage_manager = create_storage_component(storage_config)
            self.logger.info(f"{storage_name} initialized")
            for msg in self.event_listener:
                # else we store the message to the configured storage component
                event_log = self.convert_message(msg, storage_config['type'])
                storage_manager.create_query(event_log)

    def remove(self, topics: List[str]):
        self.logger.info(f"Removing {topics}")
        for topic in topics:
            self.topics.remove(topic)
        self.event_listener.subscribe(self.topics)

    def add(self, topics: List[str]):
        self.logger.info(f"Adding {topics}")
        self.topics.extend(topics)
        self.event_listener.subscribe(self.topics)

    def convert_message(self, msg: ConsumerRecord, db_type: str):
        try:
            validate(instance=msg, schema=self.event_schema)
        except:
            self.logger.warning("Message could not be validated!")
        timestamp = msg.timestamp
        value = self.deserialize(msg)
        monitor_name = value['monitorName']
        health_status = json.dumps(value['healthStatus'])
        if db_type == 'SQL':
            return EventLog(timestamp, monitor_name, health_status)
        json_msg = {"_id": msg.timestamp, "timestamp": msg.timestamp,
                    "monitorName": monitor_name, "healthStatus": health_status}
        return json_msg

    @staticmethod
    def deserialize(msg: ConsumerRecord) -> dict:
        return json.loads(msg.value)
