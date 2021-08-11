import json
import logging
from enum import Enum
from multiprocessing import Process
from typing import List, Optional, Dict

from bson import json_util
from jsonschema import validate
from kafka import KafkaProducer, KafkaConsumer
from kafka.producer.future import FutureRecordMetadata

from component_monitoring.config.config_params import ComponentMonitorConfig
from component_monitoring.monitor_factory import MonitorFactory


class Command(Enum):
    START = 'activate'
    SHUTDOWN = 'shutdown'
    START_STORE = 'store'
    STOP_STORE = 'unstore'

class ResponseCode(Enum):
    SUCCESS = 200
    FAILURE = 400

class MessageType(Enum):
    RESPONSE = 'response'
    REQUEST = 'request'
    INFO = 'info'


class MonitorManager(Process):
    """
    Monitor Manager
    """

    def __init__(self, hw_monitor_config_params: List[ComponentMonitorConfig],
                 sw_monitor_config_params: List[ComponentMonitorConfig],
                 server_address: str = 'localhost:9092',
                 control_channel: str = 'monitor_manager'):
        Process.__init__(self)
        self.logger = logging.getLogger('monitor_manager')
        self.logger.setLevel(logging.INFO)

        self._id = 'manager'
        self.control_channel = control_channel
        self.server_address = server_address
        self.producer = None
        self.consumer = None

        with open('component_monitoring/schemas/control.json', 'r') as schema:
            self.event_schema = json.load(schema)
        self.monitors = dict()
        self.monitor_config = dict()

        self.component_descriptions = dict()

        for monitor_config in hw_monitor_config_params:
            self.monitors[monitor_config.component_name] = dict()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            self.monitor_config[monitor_config.component_name] = monitor_config

        for monitor_config in sw_monitor_config_params:
            self.monitors[monitor_config.component_name] = dict()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            self.monitor_config[monitor_config.component_name] = monitor_config

    def __send_control_message(self, msg) -> FutureRecordMetadata:
        """

        @param msg:
        @return:
        """
        result =  self.producer.send(self.control_channel, msg)
        self.producer.flush()
        return result

    def run(self) -> None:
        """

        @return:
        """
        self.consumer = KafkaConsumer(bootstrap_servers=self.server_address, client_id='manager',
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.consumer.subscribe([self.control_channel])
        self.producer = KafkaProducer(bootstrap_servers=self.server_address, value_serializer=self.serialize)
        for msg in self.consumer:
            self.logger.info(f"Processing {msg.value}")
            message = self.deserialize(msg)
            if not self.validate_control_message(message):
                self.logger.warning("Control message could not be validated!")
                self.logger.warning(msg)
            message_type = MessageType(message['message'])
            if self._id == message['to'] and MessageType.REQUEST == message_type:
                component = message['from']
                message_body = message['body']
                # process message body for REQUEST
                cmd = Command(message_body['command'])
                if cmd == Command.SHUTDOWN:
                    for monitor in message_body['monitors']:
                        self.stop_monitor(component, monitor)
                elif cmd == Command.START:
                    for monitor in message_body['monitors']:
                        try:
                            self.start_monitor(component, monitor)
                            self.send_response(component, ResponseCode.SUCCESS, '')
                        except Exception:
                            self.logger.warning(f"Monitor of component {component} with ID {monitor} could not be started!")
                            self.send_response(component, ResponseCode.FAILURE, '')
                    topic_list = list()
                    for monitor in message_body['monitors']:
                        try:
                            topic_list.append(self.monitors[component][monitor].event_topic)
                        except KeyError:
                            pass

    def log_off(self) -> None:
        """

        @return:
        """
        for component in self.monitors.keys():
            msg = {"source_id": self._id, "target_id": [component], "info": "log"}
            self.__send_control_message(msg)

    def serialize(self, msg) -> bytes:
        """

        @param msg:
        @return:
        """
        return json.dumps(msg, default=json_util.default).encode('utf-8')

    def deserialize(self, msg) -> dict:
        """

        @param msg:
        @return:
        """
        return json.loads(msg.value)

    def validate_control_message(self, msg: dict) -> bool:
        """

        @param msg:
        @return:
        """
        try:
            validate(instance=msg, schema=self.event_schema)
            return True
        except Exception as e:
            self.logger.warning(e)
            return False

    def start_monitors(self) -> None:
        """
        Create all monitors specified in the configuration and start them
        """
        self.monitoring = True
        for component_name, monitor_config in self.monitor_config.items():
            for mode_name, mode in monitor_config.modes.items():
                self.start_monitor(component_name, mode_name)

    def stop_monitors(self) -> None:
        """
        Call stop method of all monitors. The stop method is used for cleanup
        (specifically for shutting down pyre nodes)

        :return: None

        """
        for component_name, monitors in self.monitors.items():
            for mode_name, monitor in monitors.items():
                self.stop_monitor(component_name, mode_name)

    def stop_monitor(self, component_name: str, mode_name: str) -> None:
        """

        @param component_name:
        @param mode_name:
        @return:
        """
        self.monitors[component_name][mode_name].stop()
        del self.monitors[component_name][mode_name]

    def start_monitor(self, component_name: str, mode_name: str) -> None:
        """

        @param component_name:
        @param mode_name:
        @return:
        """
        if component_name in self.monitors and mode_name in self.monitors[component_name]:
            self.logger.warning(f"Monitor {mode_name} of {component_name} is already started!")
            return
        monitor = MonitorFactory.get_monitor(self.monitor_config[component_name].type, component_name,
                                             self.monitor_config[component_name].modes[mode_name],
                                             self.server_address, self.control_channel)
        try:
            self.monitors[component_name][mode_name] = monitor
        except KeyError:
            self.monitors[component_name] = dict()
            self.monitors[component_name][mode_name] = monitor
        monitor.run()

    def send_response(self, receiver: str, code: ResponseCode, msg: str) -> None:
        """

        @param receiver:
        @param code:
        @param msg:
        @return:
        """
        message = dict()
        message['from'] = self._id
        message['to'] = receiver
        message['message'] = MessageType.RESPONSE.value
        message['body'] = dict()
        message['body']['status'] = dict()
        message['body']['status']['code'] = code.value
        message['body']['status']['message'] = msg
        self.__send_control_message(message)
