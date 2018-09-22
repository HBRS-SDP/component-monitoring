from __future__ import print_function
from component_monitoring.monitor_factory import MonitorFactory

class MonitorManager(object):
    def __init__(self, hw_monitor_config_params, sw_monitor_config_params):
        self.hardware_monitors = dict()
        self.software_monitors = dict()
        for monitor_config in hw_monitor_config_params:
            self.hardware_monitors[monitor_config.description] = list()
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_hardware_monitor(monitor_config.component_name,
                                                              monitor_mode_config)
                self.hardware_monitors[monitor_config.description].append(monitor)

        for monitor_config in sw_monitor_config_params:
            self.software_monitors[monitor_config.description] = list()
            for monitor_mode_config in monitor_config.modes:
                monitor = MonitorFactory.get_software_monitor(monitor_config.component_name,
                                                              monitor_mode_config)
                self.software_monitors[monitor_config.description].append(monitor)

    def monitor_components(self):
        component_status_msg = list()
        for monitor_name, monitors in self.hardware_monitors.items():
            hw_monitor_msg = dict()
            hw_monitor_msg['component'] = monitor_name
            hw_monitor_msg['modes'] = list()
            for monitor in monitors:
                monitor_status = monitor.get_status()
                hw_monitor_msg['modes'].append(monitor_status)
            component_status_msg.append(hw_monitor_msg)

        for monitor_name, monitors in self.software_monitors.items():
            sw_monitor_msg = dict()
            sw_monitor_msg['component'] = monitor_name
            sw_monitor_msg['modes'] = list()
            for monitor in monitors:
                monitor_status = monitor.get_status()
                sw_monitor_msg['modes'].append(monitor_status)
            component_status_msg.append(sw_monitor_msg)
        return component_status_msg
