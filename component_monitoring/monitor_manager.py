import json
import logging
from multiprocessing import Process
from typing import List, Optional

from jsonschema import validate
from kafka import KafkaProducer, KafkaConsumer

from component_monitoring.component import Component
from component_monitoring.config.config_params import ComponentMonitorConfig
from component_monitoring.messaging.enums import MessageType, Response
from component_monitoring.monitor_factory import MonitorFactory
from component_monitoring.storage.storage_manager import StorageManager


class MonitorManager(Component):
    """
    Monitor Manager
    """

    def __init__(self, hw_monitor_config_params: List[ComponentMonitorConfig],
                 sw_monitor_config_params: List[ComponentMonitorConfig],
                 storage: StorageManager,
                 server_address: str = 'localhost:9092',
                 control_channel: str = 'monitor_manager'):
        Component.__init__(self, 'monitor_manager', server_address=server_address, control_channel=control_channel)
        self.logger = logging.getLogger('monitor_manager')
        self.logger.setLevel(logging.INFO)
        self.storage = storage
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

        self.pending_helos = dict()

    def run(self) -> None:
        """
        Entry point of the Monitor Manager process

        @return: None
        """
        self.consumer = KafkaConsumer(bootstrap_servers=self.server_address, client_id=self._id,
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.consumer.subscribe([self.control_channel])
        self.producer = KafkaProducer(bootstrap_servers=self.server_address, value_serializer=self.serialize)
        for msg in self.consumer:
            self.logger.info(f"Processing {msg.value}")
            message = self.deserialize(msg)
            if self.validate_request(message):
                if not self._id == message['To']:
                    continue
                dialogue_id = message['Id']
                component = message['From']
                message_type = self.get_message_type(message)
                if message_type == MessageType.START:
                    for monitor in message[MessageType.START.value]:
                        self.start_monitor(message['From'], monitor['Id'], message['Id'])
                    if dialogue_id in self.pending_helos.keys():
                        self.send_response(dialogue_id, message['From'], Response.STARTING)
                    else:
                        monitors = list()
                        for monitor in message[MessageType.START.value]:
                            monitors.append(
                                {"mode": monitor['Id'], "id": self.monitors[component][monitor['Id']][1],
                                 "topic": self.monitors[component][monitor['Id']][2]})
                        self.send_response(dialogue_id, component, Response.OKAY, monitors)
                elif message_type == MessageType.STOP:
                    for monitor in message[MessageType.STOP.value]:
                        self.stop_monitor(message['From'], monitor)
                    self.send_response(message['Id'], message['From'], Response.STOPPING)
                elif message_type == MessageType.UPDATE:
                    self.logger.warning("UPDATE is currently not implemented for the Monitor Manager!")
            elif self.validate_response(message):
                pass
            elif self.validate_broadcast(message):
                message_type = self.get_message_type(message)
                try:
                    component = message[message_type.value]['Component']
                    mode = message[message_type.value]['Mode']
                    dialogue_id = message['Id']
                    self.monitors[component][mode][1] = message['From']
                    self.monitors[component][mode][2] = message[message_type.value]['Topic']
                    self.pending_helos[dialogue_id][component][mode] = True
                    if all(helo for helo in self.pending_helos[dialogue_id][component].values()):
                        monitors = list()
                        for monitor in self.pending_helos[dialogue_id][component]:
                            monitors.append({"mode": monitor, "id": self.monitors[component][mode][1],
                                             "topic": self.monitors[component][mode][2]})
                        self.send_response(dialogue_id, component, Response.OKAY, monitors)
                        self.logger.error(self.pending_helos)
                        del self.pending_helos[dialogue_id]
                        self.logger.error(self.pending_helos)
                except KeyError:
                    self.logger.warning(f"Received unawaited HELO from {message['Component']} {message['Mode']}")
            else:
                self.logger.warning("Control message could not be validated!")
                self.logger.warning(msg)
                continue

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

        @return: None

        """
        for component_name, monitors in self.monitors.items():
            for mode_name, monitor in monitors.items():
                self.stop_monitor(component_name, mode_name)

    def stop_monitor(self, component_name: str, mode_name: str) -> None:
        """
        Stop a single monitor, specified by its component and mode name

        @param component_name: The name of the component the monitor belongs to
        @param mode_name: The mode name of the monitor
        @return: None
        """
        self.monitors[component_name][mode_name].terminate()
        del self.monitors[component_name][mode_name]

    def start_monitor(self, component_name: str, mode_name: str, dialogue_id: str) -> None:
        """
        Start a single monitor, specified by its component and mode name

        @param component_name: The name of the component requesting monitoring
        @param mode_name: The mode name of the monitor to be started
        @return: If the monitor does not exist yet, returns the event topic the monitor is publishing on. Else, None is
        returned.
        """
        if component_name in self.monitors and mode_name in self.monitors[component_name]:
            self.logger.warning(f"Monitor {mode_name} of {component_name} is already started!")
            return
        monitor = MonitorFactory.get_monitor(self.monitor_config[component_name].type, component_name, dialogue_id,
                                             self.monitor_config[component_name].modes[mode_name],
                                             self.server_address, self.control_channel)
        try:
            self.monitors[component_name][mode_name] = [monitor, None, None]
        except KeyError:
            self.monitors[component_name] = dict()
            self.monitors[component_name][mode_name] = [monitor, None, None]
        monitor.start()
        try:
            self.pending_helos[dialogue_id][component_name][mode_name] = False
        except KeyError:
            try:
                self.pending_helos[dialogue_id][component_name] = dict()
                self.pending_helos[dialogue_id][component_name][mode_name] = False
            except KeyError:
                self.pending_helos[dialogue_id] = dict()
                self.pending_helos[dialogue_id][component_name] = dict()
                self.pending_helos[dialogue_id][component_name][mode_name] = False
