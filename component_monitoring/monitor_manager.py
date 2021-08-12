import json
import logging
from multiprocessing import Process
from typing import List, Optional, Dict

from bson import json_util
from jsonschema import validate
from kafka import KafkaProducer, KafkaConsumer
from kafka.producer.future import FutureRecordMetadata

from component_monitoring.config.config_params import ComponentMonitorConfig
from component_monitoring.messages.enums import MessageType, Command, ResponseCode
from component_monitoring.monitor_factory import MonitorFactory
from component_monitoring.storage.storage_manager import StorageManager


class MonitorManager(Process):
    """
    Monitor Manager
    """

    def __init__(self, hw_monitor_config_params: List[ComponentMonitorConfig],
                 sw_monitor_config_params: List[ComponentMonitorConfig],
                 storage: StorageManager,
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

        self.storage = storage

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
                    response = dict()
                    response['monitors'] = list()
                    code = ResponseCode.SUCCESS
                    for monitor in message_body['monitors']:
                        try:
                            topic = self.start_monitor(component, monitor)
                            print(topic)
                            response['monitors'].append({"name": monitor, "topic": topic})
                        except Exception as e:
                            self.logger.warning(f"Monitor of component {component} with ID {monitor} could not be started!")
                            response['monitors'].append({"name": monitor, "exception": e})
                            code = ResponseCode.FAILURE
                    self.send_response(component, code, response)

    def log_off(self) -> None:
        """

        @return:
        """
        for component in self.monitors.keys():
            self.send_info(component, "manager shutting down")

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

    def start_monitor(self, component_name: str, mode_name: str) -> Optional[str]:
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
        return monitor.event_topic

    def send_info(self, receiver: str, info: str):
        message = dict()
        message['from'] = self._id
        message['to'] = receiver
        message['message'] = MessageType.RESPONSE.value
        message['body'] = dict()
        message['body']['message'] = info
        self.__send_control_message(message)

    def send_response(self, receiver: str, code: ResponseCode, msg: Optional[Dict]) -> None:
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
        message['body']['code'] = code.value
        if msg:
            for key, value in msg.items():
                message['body'][key] = value
        self.__send_control_message(message)
