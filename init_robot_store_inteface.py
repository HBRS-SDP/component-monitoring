#!/usr/bin/env python3
import argparse
from component_monitoring.config.config_utils import ConfigUtils
from component_monitoring.utils.robot_store_interface import RobotStoreInterface

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialise robot store interface',
                                     epilog='EXAMPLE: python3 init_robot_store_interface.py config.yaml')
    parser.add_argument('--config_file', type=str,
                        default='config/component_monitoring_config.yaml',
                        help='Path to a configuration file for the component monitoring')

    args = parser.parse_args()
    config_file_path = args.config_file
    config_data = ConfigUtils.read_config(config_file_path)

    robot_id = config_data['robot_id']
    hw_monitor_config_dir = config_data['config_dirs']['hardware']
    sw_monitor_config_dir = config_data['config_dirs']['software']

    # we read the parameters of the hardware and software monitors
    print('Reading the configuration of the hardware monitors')
    hw_monitor_config_params = ConfigUtils.get_config_params(hw_monitor_config_dir)

    print('Reading the configuration of the software monitors')
    sw_monitor_config_params = ConfigUtils.get_config_params(sw_monitor_config_dir)

    # we create an interface to the robot store interface
    robot_store_interface = RobotStoreInterface(db_name=config_data['robot_store_interface']['db_name'],
                                                monitor_collection_name=config_data['robot_store_interface']['monitor_collection_name'],
                                                db_port=config_data['robot_store_interface']['db_port'])

    # we store the component configuration in the database
    print('Saving the component configuration in the robot store interface')
    robot_store_interface.store_component_configuration(hw_monitor_config_params,
                                                        sw_monitor_config_params)
