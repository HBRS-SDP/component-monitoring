from multiprocessing import Process
from typing import List

from kafka import KafkaProducer, KafkaConsumer

from component_monitoring.config.config_params import ComponentMonitorConfig
from component_monitoring.monitor_factory import MonitorFactory

class MonitorManager(object):
    def __init__(self, hw_monitor_config_params: List[ComponentMonitorConfig],
                 sw_monitor_config_params: List[ComponentMonitorConfig], server_address: str = 'localhost:9092',
                 control_channel: str = 'monitor_manager'):
        self.producer = KafkaProducer(bootstrap_servers=server_address, value_serializer=self.serialize)
        self.consumer = KafkaConsumer(bootstrap_servers=server_address, client_id='manager',
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.monitors = dict()

        self.component_descriptions = dict()

        for monitor_config in hw_monitor_config_params:
            self.monitors[monitor_config.component_name] = list()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_hardware_monitor(monitor_config.component_name,
                                                              monitor_mode_config, server_address, control_channel)
                self.monitors[monitor_config.component_name].append(monitor)

        for monitor_config in sw_monitor_config_params:
            self.monitors[monitor_config.component_name] = list()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_software_monitor(monitor_config.component_name,
                                                              monitor_mode_config, server_address, control_channel)
                self.monitors[monitor_config.component_name].append(monitor)

        self.component_monitor_data = [(component_id, monitors) for (component_id, monitors)
                                       in self.monitors.items()]
        self.manager = Process(target=self.__run)
        self.manager.start()

    def __run(self):
        for msg in self.consumer:
            return

    def serialize(self, msg) -> bytes:
        return b't'


    def start_monitors(self):
        self.monitoring = True
        processes = []
        for component_id, monitors in self.component_monitor_data:
            for monitor in self.monitors[component_id]:
                processes.append(monitor)
                monitor.start()
        return processes

    def stop_monitors(self):
        """Call stop method of all monitors. The stop method is used for cleanup
        (specifically for shutting down pyre nodes)

        :return: None

        """
        for component_name, monitors in self.monitors.items():
            for monitor in monitors:
                monitor.stop()
