import importlib
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
    def get_hardware_monitor(component_name, monitor_config_params):
        try:
            monitor_name = monitor_config_params.name
            module_name = 'component_monitoring.monitors.hardware.' \
                          + component_name + '.' + monitor_name
            class_name = ''.join(x.title() for x in monitor_name.split('_'))
            MonitorClass = getattr(importlib.import_module(module_name),
                                   class_name)
            return MonitorClass(monitor_config_params)
        except Exception as e:
            print("While initialising", component_name, "got exception", str(e))
            return MonitorBase(monitor_config_params)

    '''Returns a software monitor as specified by the given name

    Keyword arguments:
    @param monitor_name monitor description name as specified in 'config_enums/HardwareMonitorNames'

    '''
    @staticmethod
    def get_software_monitor(component_name, monitor_config_params):
        try:
            monitor_name = monitor_config_params.name
            module_name = 'component_monitoring.monitors.software.' \
                          + component_name + '.' + monitor_name
            class_name = ''.join(x.title() for x in monitor_name.split('_'))
            MonitorClass = getattr(importlib.import_module(module_name),
                                   class_name)
            return MonitorClass(monitor_config_params)
        except Exception as e:
            print("While initialising", component_name, "got exception", str(e))
            return MonitorBase(monitor_config_params)
