import importlib

from component_monitoring.config.config_params import MonitorModeConfig
from component_monitoring.monitor_base import MonitorBase

'''A factory for creating component monitors

@author Alex Mitrevski, Santosh Thoduka
@contact aleksandar.mitrevski@h-brs.de, santosh.thoduka@h-brs.de
'''
class MonitorFactory(object):
    '''Returns a hardware monitor as specified by the given name

    Keyword arguments:
    @param monitor_name monitor description name as specified in 'config_enums/HardwareMonitorNames'

    '''
    @staticmethod
    def get_monitor(monitor_type:str, component_name: str, monitor_config_params: MonitorModeConfig,
                             server_address: str, control_channel: str) -> MonitorBase:
        try:
            monitor_name = monitor_config_params.name
            module_name = 'component_monitoring.monitors.' + monitor_type + '.' \
                          + component_name + '.' + monitor_name
            class_name = ''.join(x.title() for x in monitor_name.split('_'))
            MonitorClass = getattr(importlib.import_module(module_name),
                                   class_name)
            return MonitorClass(component_name, monitor_config_params, server_address=server_address, control_channel=control_channel)
        except Exception as e:
            print("While initialising", component_name, "got exception", str(e))
            return MonitorBase(monitor_config_params, server_address=server_address, control_channel=control_channel)
