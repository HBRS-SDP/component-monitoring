#!/usr/bin/env python
from __future__ import print_function
import sys
import time
from os import listdir
from os.path import join, isfile
import json
import uuid
import argparse

from ropod.pyre_communicator.base_class import RopodPyre
from component_monitoring.config.config_file_reader import ComponentMonitorConfigFileReader
from component_monitoring.monitor_manager import MonitorManager
from component_monitoring.utils.robot_store_interface import RobotStoreInterface
from component_monitoring.communication import BlackBoxPyreCommunicator

def get_files(dir_name):
    file_names = list()
    for f_name in listdir(dir_name):
        f_path = join(dir_name, f_name)
        if isfile(f_path):
            file_names.append(f_name)
    return file_names

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
    parser.add_argument('ropod_id', type=str, default='001', help='ropod ID (as 3 digit number)')
    parser.add_argument('black_box_id', type=str, default='001', help='black box ID (as 3 digit number)')
    parser.add_argument('-d', '--debug', help='print debug output', action='store_true')

    args = parser.parse_args()
    robot_id = 'ropod_' + args.ropod_id
    black_box_id = 'black_box_' + args.black_box_id

    hw_monitor_config_dir_name = 'component_monitoring/monitor_config/robot/hardware'
    sw_monitor_config_dir_name = 'component_monitoring/monitor_config/robot/software'

    hw_config_files = get_files(hw_monitor_config_dir_name)
    hw_monitor_config_params = list()
    for config_file in hw_config_files:
        print('Reading parameters of hardware monitor {0}'.format(config_file))
        component_config_params = ComponentMonitorConfigFileReader.load(hw_monitor_config_dir_name,
                                                                        config_file)
        hw_monitor_config_params.append(component_config_params)

    sw_config_files = get_files(sw_monitor_config_dir_name)
    sw_monitor_config_params = list()
    for config_file in sw_config_files:
        print('Reading parameters of software monitor {0}'.format(config_file))
        component_config_params = ComponentMonitorConfigFileReader.load(sw_monitor_config_dir_name,
                                                                        config_file)
        sw_monitor_config_params.append(component_config_params)

    pyre_comm = RopodPyre(robot_id, ["MONITOR"], [])
    pyre_comm.start()
    robot_store_interface = RobotStoreInterface(db_name='robot_store',
                                                monitor_collection_name='status',
                                                db_port=27017)
    black_box_comm = BlackBoxPyreCommunicator('component_monitor_query_node', ['MONITOR', 'ROPOD'], black_box_id)
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
