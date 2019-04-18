#!/usr/bin/env python
from __future__ import print_function
import time
import json
import uuid
import argparse
import yaml

from ropod.pyre_communicator.base_class import RopodPyre
from component_monitoring.config.config_file_reader import ComponentMonitorConfigFileReader
from component_monitoring.config.config_utils import ConfigUtils
from component_monitoring.monitor_manager import MonitorManager
from component_monitoring.utils.robot_store_interface import RobotStoreInterface
from component_monitoring.communication import BlackBoxPyreCommunicator

def get_config_data(config_file_path):
    config_data = {}
    with open(config_file_path, 'r') as config_file:
        config_data = yaml.load(config_file)
    return config_data

def generate_robot_msg(status_msg, robot_id):
    msg = dict()
    msg["header"] = dict()
    msg["header"]["type"] = "HEALTH-STATUS"
    msg["header"]["metamodel"] = "ropod-msg-schema.json"
    msg["header"]["msgId"] = str(uuid.uuid4())
    msg["header"]["timestamp"] = time.time()
    payload = dict()
    payload["metamodel"] = "ropod-component-monitor-schema.json"
    payload["robotId"] = robot_id
    payload["monitors"] = status_msg
    msg["payload"] = payload
    return json.dumps(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor component status',
                                     epilog='EXAMPLE: python3 main.py 001 001')
    parser.add_argument('config_file', type=str,
                        default='config/component_monitoring_config',
                        help='Path to a configuration file')
    parser.add_argument('-d', '--debug', help='print debug output', action='store_true')

    args = parser.parse_args()
    config_file_path = args.config_file
    config_data = get_config_data(config_file_path)
    robot_id = config_data['robot_id']

    hw_monitor_config_dir = config_data['config_dirs']['hardware']
    sw_monitor_config_dir = config_data['config_dirs']['software']

    hw_config_files = ConfigUtils.get_file_names_in_dir(hw_monitor_config_dir)
    hw_monitor_config_params = list()
    for config_file in hw_config_files:
        print('Reading parameters of hardware monitor {0}'.format(config_file))
        component_config_params = ComponentMonitorConfigFileReader.load(hw_monitor_config_dir,
                                                                        config_file)
        hw_monitor_config_params.append(component_config_params)

    sw_config_files = ConfigUtils.get_file_names_in_dir(sw_monitor_config_dir)
    sw_monitor_config_params = list()
    for config_file in sw_config_files:
        print('Reading parameters of software monitor {0}'.format(config_file))
        component_config_params = ComponentMonitorConfigFileReader.load(sw_monitor_config_dir,
                                                                        config_file)
        sw_monitor_config_params.append(component_config_params)

    pyre_comm = RopodPyre(robot_id, config_data['status_communication']['zyre_groups'], [])
    pyre_comm.start()

    robot_store_interface = RobotStoreInterface(db_name=config_data['robot_store_interface']['db_name'],
                                                monitor_collection_name=config_data['robot_store_interface']['monitor_collection_name'],
                                                db_port=config_data['robot_store_interface']['db_port'])
    black_box_comm = BlackBoxPyreCommunicator(config_data['black_box']['zyre_node_name'],
                                              config_data['black_box']['zyre_groups'],
                                              config_data['black_box']['id'])
    monitor_manager = MonitorManager(hw_monitor_config_params,
                                     sw_monitor_config_params,
                                     robot_store_interface,
                                     black_box_comm)
    try:
        while True:
            status_msg = monitor_manager.monitor_components()
            robot_store_interface.store_monitor_msg(status_msg)

            robot_msg = generate_robot_msg(status_msg, robot_id)
            if (args.debug):
                print(json.dumps(status_msg, indent=2))
            pyre_comm.shout(robot_msg)
            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        print('Component monitors exiting')
        pyre_comm.shutdown()
        monitor_manager.stop_monitors()
        black_box_comm.shutdown()

    ### debugging printout
    # hardware_monitor_config_params = ComponentMonitorConfigFileReader.load(hw_monitor_config_dir_name,
    #                                                                          "laser_monitor.yaml");
    # print('Monitor name: {0}'.format(hardware_monitor_config_params.name))
    # for mode_params in hardware_monitor_config_params.modes:
    #     print('    Mode name: {0}'.format(mode_params.name))
    #     for fn_mapping_params in mode_params.mappings:
    #         print('    Inputs:\n')
    #         for monitor_input in fn_mapping_params.inputs:
    #             print('        {0}'.format(monitor_input))
    #
    #         print('    Outputs:\n')
    #         for monitor_output in fn_mapping_params.outputs:
    #             print('        {0}'.format(monitor_output.name))
    #             print('        {0}'.format(monitor_output.obtained_value_type))
    #             print('        {0}'.format(monitor_output.expected_value))
    #     print()
