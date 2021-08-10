#!/usr/bin/env python
import argparse
import rospy

from component_monitoring.config.config_utils import ConfigUtils
from component_monitoring.monitor_manager import MonitorManager
from component_monitoring.utils.component_network import ComponentNetwork
from db.db_main import Storage

import logging
# This sets the root logger to write to stdout (your console).
# Your script/app needs to call this somewhere at least once.
logging.basicConfig()

# By default the root logger is set to WARNING and all loggers you define
# inherit that value. Here we set the root logger to NOTSET. This logging
# level is automatically inherited by all existing and new sub-loggers
# that do not set a less verbose level.
logging.root.setLevel(logging.INFO)

# The following line sets the root logger level as well.
# It's equivalent to both previous statements combined:
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    rospy.init_node('component_monitor', disable_signals=True)
    parser = argparse.ArgumentParser(description='Monitor component status',
                                     epilog='EXAMPLE: python3 main.py 001 001')
    parser.add_argument('config_file', type=str,
                        default='config/component_monitoring_config',
                        help='Path to a configuration file')
    parser.add_argument('-d', '--debug', help='print debug output', action='store_true')

    args = parser.parse_args()
    config_file_path = args.config_file
    config_data = ConfigUtils.read_config(config_file_path)

    robot_id = config_data['robot_id']
    hw_monitor_config_dir = config_data['config_dirs']['hardware']
    sw_monitor_config_dir = config_data['config_dirs']['software']

    # we read the parameters of the hardware and software monitors
    hw_monitor_config_params = ConfigUtils.get_config_params(hw_monitor_config_dir,
                                config_file='rgbd_camera.yaml')
    sw_monitor_config_params = []#ConfigUtils.get_config_params(sw_monitor_config_dir)

    # we populate the parameters of the configuration utilities
    # to simplify runtime access to the configuration data
    ConfigUtils.config_data = config_data
    ConfigUtils.hw_monitor_config_params = hw_monitor_config_params
    ConfigUtils.sw_monitor_config_params = sw_monitor_config_params

    # we initialise a manager for the monitors that will continuously
    # update the component status message
    monitor_manager = MonitorManager(hw_monitor_config_params,
                                     sw_monitor_config_params)

    component_network = ComponentNetwork(config_file_path)

    try:
        monitor_manager.start()
        monitor_manager.join()

        db_config = config_data['db_config']
        db_storage = Storage(
            db_config, topic_name="hsrb_monitoring_feedback_rgbd")
        db_storage.start()

    except (KeyboardInterrupt, SystemExit):
        print('Component monitors exiting')
