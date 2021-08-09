import json
import logging
from abc import abstractmethod
from multiprocessing import Process
from typing import Union

from jsonschema import validate
from kafka import KafkaProducer, KafkaConsumer

from component_monitoring.config.config_params import MonitorModeConfig


class MonitorBase(Process):

    def __init__(self, config_params: MonitorModeConfig, server_address: str, control_channel: str):
        Process.__init__(self)
        self.config_params = config_params
        self.event_topic = f"{self.config_params.name}_eventbus"
        self.control_topic = control_channel
        self.logger = logging.Logger(f"monitor_{self.config_params.name}")
        self.producer = KafkaProducer(bootstrap_servers=server_address)
        self.consumer = KafkaConsumer(bootstrap_servers=server_address, client_id=self.config_params.name,
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        with open('component_monitoring/schemas/event.json', 'r') as schema:
            self.event_schema = json.load(schema)
        self.healthstatus = {}
        #print(self.event_topic)

    def valid_status_message(self, msg: dict) -> bool:
        try:
            validate(instance=msg, schema=self.event_schema)
            return True
        except:
            return False

    def send_event_msg(self, msg: Union[str, bytes]):
        if isinstance(msg, bytes):
            self.producer.send(topic=self.event_topic, value=msg)
        else:
            self.producer.send(topic=self.event_topic, value=self.serialize(msg))

    @abstractmethod
    def start(self):
        self.consumer.subscribe([self.event_topic, self.control_topic])
        super().start()

    @abstractmethod
    def stop(self):
        self.consumer.unsubscribe()
        super().terminate()

    @abstractmethod
    def serialize(self, msg) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def publish_status(self):
        raise NotImplementedError()
