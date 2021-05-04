import time
import threading
from component_monitoring.monitor_factory import MonitorFactory
#from fault_recovery.component_recovery.recovery_action_factory import RecoveryActionFactory

class MonitorManager(object):
    def __init__(self, hw_monitor_config_params, sw_monitor_config_params,
                 robot_store_interface, black_box_comm):
        self.monitors = dict()

        self.component_descriptions = dict()
        self.component_descriptions = dict()
        self.robot_store_interface = robot_store_interface

        for monitor_config in hw_monitor_config_params:
            self.monitors[monitor_config.component_name] = list()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_hardware_monitor(monitor_config.component_name,
                                                              monitor_mode_config, black_box_comm)
                self.monitors[monitor_config.component_name].append(monitor)

        for monitor_config in sw_monitor_config_params:
            self.monitors[monitor_config.component_name] = list()
            self.component_descriptions[monitor_config.component_name] = monitor_config.description
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_software_monitor(monitor_config.component_name,
                                                              monitor_mode_config, black_box_comm)
                self.monitors[monitor_config.component_name].append(monitor)

        self.component_monitor_data = [(component_id, monitors) for (component_id, monitors)
                                       in self.monitors.items()]

        self.monitor_status_msgs = dict()
        self.monitor_threads = dict()
        self.monitoring = False
        self.monitor_status_dict_lock = threading.Lock()
        self.robot_store_connections = dict()
        for component_id, monitors in self.component_monitor_data:
            monitor_msg = dict()
            component_name = self.component_descriptions[component_id]
            monitor_msg['component'] = component_name
            monitor_msg['component_id'] = component_id
            monitor_msg['component_sm_state'] = 'unknown'
            monitor_msg['modes'] = []
            self.robot_store_connections[component_id] = self.robot_store_interface.get_connection()
            self.monitor_status_msgs[component_id] = monitor_msg
            self.monitor_threads[component_id] = threading.Thread(target=self.monitor_components,
                                                                  args=(component_id, monitors))

    def start_monitors(self):
        self.monitoring = True
        for component_id, monitors in self.component_monitor_data:
            self.monitor_threads[component_id].start()

    def monitor_components(self, component_id, monitors):
        while self.monitoring:
            monitor_msgs = []
            for monitor in monitors:
                monitor_status = monitor.get_status()
                monitor_msgs.append(monitor_status)
            self.monitor_status_dict_lock.acquire()
            self.monitor_status_msgs[component_id]['modes'] = monitor_msgs
            self.monitor_status_msgs[component_id]['component_sm_state'] = \
                self.robot_store_interface.read_component_sm_status(component_id,
                                                                    self.robot_store_connections[component_id])
            self.robot_store_interface.store_component_status_msg(component_id,
                                                                  self.monitor_status_msgs[component_id],
                                                                  self.robot_store_connections[component_id])
            self.monitor_status_dict_lock.release()
            time.sleep(1.0)

    def get_component_status_list(self):
        return [self.robot_store_interface.get_component_status_msg(component_id, self.robot_store_connections[component_id])
                for component_id in self.monitor_status_msgs.keys()
                if self.monitor_status_msgs[component_id]['modes']]

    def stop_monitors(self):
        """Call stop method of all monitors. The stop method is used for cleanup
        (specifically for shutting down pyre nodes)

        :return: None

        """
        for component_name, monitors in self.monitors.items():
            for monitor in monitors:
                monitor.stop_monitor()

        self.monitoring = False
        for component_id, monitors in self.component_monitor_data:
            self.monitor_threads[component_id].join()
