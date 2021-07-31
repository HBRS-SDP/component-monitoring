import json
from multiprocessing import Process
from typing import List

from bson import json_util
from kafka import KafkaProducer, KafkaConsumer

from component_monitoring.config.config_params import ComponentMonitorConfig
from component_monitoring.monitor_factory import MonitorFactory


class MonitorManager(object):
    CMD_SHUTDOWN = 'shutdown'
    CMD_START = 'activate'
    STATUS_FAILURE = 'failed'
    STATUS_SUCCESS = 'success'
    TYPE_ACK = 'ack'

    def __init__(self, hw_monitor_config_params: List[ComponentMonitorConfig],
                 sw_monitor_config_params: List[ComponentMonitorConfig], server_address: str = 'localhost:9092',
                 control_channel: str = 'monitor_manager'):
        self.control_channel = control_channel
        self.server_address = server_address
        self.producer = KafkaProducer(bootstrap_servers=server_address, value_serializer=self.serialize)
        self.consumer = KafkaConsumer(bootstrap_servers=server_address, client_id='manager',
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.monitors = dict()
        self.monitor_config = dict()

        self.component_descriptions = dict()

        for monitor_config in hw_monitor_config_params:
            self.monitors[monitor_config.component_name] = list()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            self.monitor_config[monitor_config.component_name] = dict()
            for monitor_mode_config in monitor_config.modes:
                self.monitor_config[monitor_config.component_name][monitor_mode_config.name] = monitor_mode_config
                monitor = MonitorFactory.get_hardware_monitor(monitor_config.component_name,
                                                              monitor_mode_config, server_address, control_channel)
                self.monitors[monitor_config.component_name].append(monitor)

        for monitor_config in sw_monitor_config_params:
            self.monitors[monitor_config.component_name] = list()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            self.monitor_config[monitor_config.component_name] = dict()
            for monitor_mode_config in monitor_config.modes:
                self.monitor_config[monitor_config.component_name][monitor_mode_config.name] = monitor_mode_config
                monitor = MonitorFactory.get_software_monitor(monitor_config.component_name,
                                                              monitor_mode_config, server_address, control_channel)
                self.monitors[monitor_config.component_name].append(monitor)

        self.component_monitor_data = [(component_id, monitors) for (component_id, monitors)
                                       in self.monitors.items()]
        self.manager = Process(target=self.__run)
        self.manager.start()

    def __run(self):
        self.consumer.subscribe([self.control_channel])
        for msg in self.consumer:
            print(msg)
            message = self.deserialize(msg)
            target_ids = message['target_id']
            source_id = message['source_id']
            if message['type'] == 'cmd':
                cmd = message['message']['command']
                if cmd == self.CMD_SHUTDOWN:
                    for target_id in target_ids:
                        self.stop_monitor(target_id)
                elif cmd == self.CMD_START:
                    for target_id in target_ids:
                        try:
                            self.start_monitor(target_id)
                            self.send_status_message(source_id, self.STATUS_SUCCESS)
                        except Exception:
                            self.send_status_message(source_id, self.STATUS_FAILURE)

    def __send_control_message(self, msg):
        self.producer.send(self.control_channel, msg)

    def serialize(self, msg) -> bytes:
        return json.dumps(msg, default=json_util.default).encode('utf-8')

    def deserialize(self, msg) -> dict:
        return json.loads(msg.value)

    def start_monitors(self):
        """
        Create all monitors specified in the configuration and start them
        """
        self.monitoring = True
        processes = []
        for component_id, monitors in self.component_monitor_data:
            for monitor in self.monitors[component_id]:
                processes.append(monitor)
                monitor.start()
        return processes

    def stop_monitors(self):
        """
        Call stop method of all monitors. The stop method is used for cleanup
        (specifically for shutting down pyre nodes)

        :return: None

        """
        for component_name, monitors in self.monitors.items():
            for monitor in monitors:
                monitor.stop()

    def stop_monitor(self, component_id):
        for monitor in self.monitors[component_id]:
            print(component_id)
            monitor.stop()
            self.monitors[component_id].remove(monitor)

    def start_monitor(self, component_id):
        print(component_id)
        for mode_name, mode in self.monitor_config[component_id].items():
            print(mode_name)
            monitor = MonitorFactory.get_hardware_monitor(component_id, mode, self.server_address,
                                                          self.control_channel)
            try:
                self.monitors[component_id].append(monitor)
            except KeyError:
                self.monitors[component_id] = list()
                self.monitors[component_id].append(monitor)
            monitor.start()

    def send_status_message(self, target_id: str, status: str):
        message = dict()
        message['target_id'] = target_id
        message['message'] = dict()
        message['message']['status'] = status
        message['type'] = self.TYPE_ACK
        self.producer.send(self.control_channel, message)
