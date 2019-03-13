from __future__ import print_function
from component_monitoring.monitor_factory import MonitorFactory
from fault_recovery.component_recovery.recovery_action_factory import RecoveryActionFactory

class MonitorManager(object):
    def __init__(self, hw_monitor_config_params, sw_monitor_config_params, robot_store_interface):
        self.hw_monitors = dict()
        self.sw_monitors = dict()

        self.hw_component_descriptions = dict()
        self.sw_component_descriptions = dict()
        self.robot_store_interface = robot_store_interface

        self.hw_recovery_managers = dict()
        self.sw_recovery_managers = dict()
        for monitor_config in hw_monitor_config_params:
            self.hw_monitors[monitor_config.component_name] = list()
            self.hw_component_descriptions[monitor_config.component_name] = monitor_config.description
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_hardware_monitor(monitor_config.component_name,
                                                              monitor_mode_config)
                self.hw_monitors[monitor_config.component_name].append(monitor)

            if monitor_config.recovery_actions:
                rec_manager = RecoveryActionFactory.get_hw_rec_manager(monitor_config.component_name)
                self.hw_recovery_managers[monitor_config.component_name] = rec_manager

        for monitor_config in sw_monitor_config_params:
            self.sw_monitors[monitor_config.component_name] = list()
            self.sw_component_descriptions[monitor_config.component_name] = monitor_config.description
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_software_monitor(monitor_config.component_name,
                                                              monitor_mode_config)
                self.sw_monitors[monitor_config.component_name].append(monitor)

            if monitor_config.recovery_actions:
                rec_manager = RecoveryActionFactory.get_sw_rec_manager(monitor_config.component_name)
                self.sw_recovery_managers[monitor_config.component_name] = rec_manager

    def monitor_components(self):
        component_status_msg = list()
        for component_name, monitors in self.hw_monitors.items():
            hw_monitor_msg = dict()
            hw_monitor_msg['component'] = self.hw_component_descriptions[component_name]
            hw_monitor_msg['component_sm_state'] = self.robot_store_interface.read_component_sm_status(self.hw_component_descriptions[component_name])
            hw_monitor_msg['modes'] = list()
            for monitor in monitors:
                monitor_status = monitor.get_status()
                hw_monitor_msg['modes'].append(monitor_status)
            component_status_msg.append(hw_monitor_msg)

        for component_name, monitors in self.sw_monitors.items():
            sw_monitor_msg = dict()
            sw_monitor_msg['component'] = self.sw_component_descriptions[component_name]
            sw_monitor_msg['component_sm_state'] = self.robot_store_interface.read_component_sm_status(self.sw_component_descriptions[component_name])
            sw_monitor_msg['modes'] = list()
            for monitor in monitors:
                monitor_status = monitor.get_status()
                sw_monitor_msg['modes'].append(monitor_status)
            component_status_msg.append(sw_monitor_msg)
        return component_status_msg
