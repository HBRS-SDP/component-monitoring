from component_monitoring.config.config_params import HardwareMonitorNames, SoftwareMonitorNames
from component_monitoring.monitor_base import MonitorBase

from component_monitoring.monitors.hardware.encoder.encoder_functional_monitor import EncoderFunctionalMonitor
from component_monitoring.monitors.hardware.encoder.encoder_diff_drive_kinematics_monitor import EncoderDiffDriveKinematicsMonitor
from component_monitoring.monitors.hardware.laser.laser_device_monitor import LaserDeviceMonitor

from component_monitoring.monitors.software.ros.ros_master_monitor import RosMasterMonitor
from component_monitoring.monitors.software.ros.ros_topic_monitor import RosTopicMonitor

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
    def get_hardware_monitor(monitor_config_params):
        if monitor_config_params.name == HardwareMonitorNames.LASER_DEVICE_MONITOR:
            monitor = LaserDeviceMonitor(monitor_config_params)
            return monitor
        elif monitor_config_params.name == HardwareMonitorNames.ENCODER_FUNCTIONAL_MONITOR:
            monitor = EncoderFunctionalMonitor(monitor_config_params)
            return monitor
        elif monitor_config_params.name == HardwareMonitorNames.ENCODER_DIFF_DRIVE_KINEMATICS_MONITOR:
            monitor = EncoderDiffDriveKinematicsMonitor(monitor_config_params)
            return monitor
        # elif (monitor_config_params.name == HardwareMonitorNames.LASER_FUNCTIONAL_MONITOR):
        #     monitor = LaserFunctionalMonitor(monitor_config_params)
        #     return monitor
        # elif (monitor_config_params.name == HardwareMonitorNames.LASER_HEARTBEAT_MONITOR):
        #     monitor = LaserHeartbeatMonitor(monitor_config_params)
        #     return monitor
        return MonitorBase(monitor_config_params)

    '''Returns a software monitor as specified by the given name

    Keyword arguments:
    @param monitor_name monitor description name as specified in 'config_enums/HardwareMonitorNames'

    '''
    @staticmethod
    def get_software_monitor(monitor_config_params):
        if monitor_config_params.name == SoftwareMonitorNames.ROS_MASTER_MONITOR:
            monitor = RosMasterMonitor(monitor_config_params)
            return monitor
        elif monitor_config_params.name == SoftwareMonitorNames.ROS_TOPIC_MONITOR:
            monitor = RosTopicMonitor(monitor_config_params)
            return monitor
        return MonitorBase(monitor_config_params)
