import json
import logging
from multiprocessing import Process
from typing import List, Optional

from bson import json_util
from jsonschema import validate
from kafka import KafkaProducer, KafkaConsumer
from kafka.producer.future import FutureRecordMetadata

from component_monitoring.config.config_params import ComponentMonitorConfig
from component_monitoring.monitor_factory import MonitorFactory


class MonitorManager(Process):
    CMD_SHUTDOWN = 'shutdown'
    CMD_START = 'activate'
    CMD_STORE = 'store'
    STATUS_FAILURE = 'failed'
    STATUS_SUCCESS = 'success'
    TYPE_ACK = 'ack'
    TYPE_CMD = 'cmd'
    STORAGE = 'storage'

    def __init__(self, hw_monitor_config_params: List[ComponentMonitorConfig],
                 sw_monitor_config_params: List[ComponentMonitorConfig], server_address: str = 'localhost:9092',
                 control_channel: str = 'monitor_manager'):
        Process.__init__(self)

        self.logger = logging.getLogger('monitor_manager')
        self.logger.setLevel(logging.INFO)

        self._id = 'manager'
        self.control_channel = control_channel
        self.server_address = server_address
        self.producer = KafkaProducer(bootstrap_servers=server_address, value_serializer=self.serialize)
        self.consumer = KafkaConsumer(bootstrap_servers=server_address, client_id='manager',
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.storage = None

        with open('component_monitoring/schemas/control.json', 'r') as schema:
            self.event_schema = json.load(schema)
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

    def __send_control_message(self, msg) -> FutureRecordMetadata:
        return self.producer.send(self.control_channel, msg)

    def __run(self):
        for msg in self.consumer:
            self.logger.info(f"Processing {msg.key}")
            message = self.deserialize(msg)
            if not self.validate_control_message(message):
                self.logger.warning("Control message could not be validated!")
            if self._id != message['source_id'] and message['type'] == self.TYPE_CMD:
                target_ids = message['target_id']
                source_id = message['source_id']
                cmd = message['message']['command']
                if cmd == self.CMD_SHUTDOWN:
                    for target_id in target_ids:
                        self.stop_monitor(target_id)
                elif cmd == self.CMD_START:
                    if len(target_ids) == 1 and target_ids[0] == self.STORAGE:
                        self.start_storage(source_id)
                    for target_id in target_ids:
                        try:
                            self.start_monitor(target_id)
                            self.send_status_message(source_id, self.STATUS_SUCCESS)
                        except Exception:
                            self.logger.warning(f"Monitor with ID {target_id} could not be started!")
                            self.send_status_message(source_id, self.STATUS_FAILURE)


    def start(self):
        # monitors = self.start_monitors()
        # for m in monitors:
        #     m.join()
        super().start()
        self.consumer.subscribe([self.control_channel])
        self.__run()

    def kill(self) -> None:
        self.stop_monitors()
        super().kill()

    def terminate(self) -> None:
        self.stop_monitors()
        super().terminate()

    def serialize(self, msg) -> bytes:
        return json.dumps(msg, default=json_util.default).encode('utf-8')

    def deserialize(self, msg) -> dict:
        return json.loads(msg.value)

    def validate_control_message(self, msg: dict) -> bool:
        try:
            validate(instance=msg, schema=self.event_schema)
            return True
        except:
            return False

    def start_monitors(self) -> List[Process]:
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

    def stop_monitors(self) -> None:
        """
        Call stop method of all monitors. The stop method is used for cleanup
        (specifically for shutting down pyre nodes)

        :return: None

        """
        for component_name, monitors in self.monitors.items():
            for monitor in monitors:
                monitor.stop()
                monitors.remove(monitor)

    def stop_monitor(self, component_id) -> None:
        for monitor in self.monitors[component_id]:
            print(component_id)
            monitor.stop()
            self.monitors[component_id].remove(monitor)

    def start_monitor(self, component_id) -> None:
        for mode_name, mode in self.monitor_config[component_id].items():
            monitor = MonitorFactory.get_hardware_monitor(component_id, mode, self.server_address,
                                                          self.control_channel)
            try:
                self.monitors[component_id].append(monitor)
            except KeyError:
                self.monitors[component_id] = list()
                self.monitors[component_id].append(monitor)
            monitor.start()
            monitor.join()

    def start_storage(self, component_id) -> None:
        storage_topics = list()
        for monitor in self.monitors[component_id]:
            storage_topics.append(monitor.event_topic)
        self.storage.update(storage_topics)

    def send_status_message(self, target_id: str, status: str) -> None:
        message = dict()
        message['source_id'] = self._id
        message['target_id'] = [target_id]
        message['message'] = dict()
        message['message']['status'] = status
        message['message']['command'] = ''
        message['type'] = self.TYPE_ACK
        self.__send_control_message(message)
