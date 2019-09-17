#!/usr/bin/env python
import time
import json
import uuid
import argparse

from ropod.pyre_communicator.base_class import RopodPyre
from component_monitoring.config.config_utils import ConfigUtils
from component_monitoring.monitor_manager import MonitorManager
from component_monitoring.recovery_manager import RecoveryManager
from component_monitoring.utils.robot_store_interface import RobotStoreInterface
from component_monitoring.utils.component_network import ComponentNetwork
from component_monitoring.communication import BlackBoxPyreCommunicator

def generate_robot_status_msg(robot_id):
    '''Returns a status message dictionary with the following format:

    {
        "header":
        {
            "type": "HEALTH-STATUS",
            "metamodel": "ropod-msg-schema.json",
            "msgId": <unique-message-ID>,
            "timestamp": <current-timestamp>
        },
        "payload":
        {
            "metamodel": "ropod-component-monitor-schema.json",
            "robotId": [robot_id],
            "monitors": {}
        }
    }

    Keyword arguments:
    robot_id: str -- robot ID/name for the status message

    '''
    msg = dict()

    msg["header"] = dict()
    msg["header"]["type"] = "HEALTH-STATUS"
    msg["header"]["metamodel"] = "ropod-msg-schema.json"
    msg["header"]["msgId"] = str(uuid.uuid4())
    msg["header"]["timestamp"] = time.time()

    msg["payload"] = dict()
    msg["payload"]["metamodel"] = "ropod-component-monitor-schema.json"
    msg["payload"]["robotId"] = robot_id
    msg["payload"]["monitors"] = {}
    return msg

if __name__ == '__main__':
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
    hw_monitor_config_params = ConfigUtils.get_config_params(hw_monitor_config_dir)
    sw_monitor_config_params = ConfigUtils.get_config_params(sw_monitor_config_dir)

    # we populate the parameters of the configuration utilities
    # to simplify runtime access to the configuration data
    ConfigUtils.config_data = config_data
    ConfigUtils.hw_monitor_config_params = hw_monitor_config_params
    ConfigUtils.sw_monitor_config_params = sw_monitor_config_params

    # we initialise a communicator for querying the black box
    black_box_comm = BlackBoxPyreCommunicator(config_data['black_box']['zyre_node_name'],
                                              config_data['black_box']['zyre_groups'],
                                              config_data['black_box']['id'])

    # we create a status communicator
    pyre_comm = RopodPyre({'node_name': 'component_monitoring_'+robot_id,
                           'groups': config_data['status_communication']['zyre_groups'],
                           'message_types': []})
    pyre_comm.start()

    # we create an interface to the robot store interface for saving the status
    robot_store_interface = RobotStoreInterface(db_name=config_data['robot_store_interface']['db_name'],
                                                monitor_collection_name=config_data['robot_store_interface']['monitor_collection_name'],
                                                db_port=config_data['robot_store_interface']['db_port'])

    # we store the component configuration in the database
    robot_store_interface.store_component_configuration(hw_monitor_config_params,
                                                        sw_monitor_config_params)

    # we initialise a manager for the monitors that will continuously
    # update the component status message
    monitor_manager = MonitorManager(hw_monitor_config_params,
                                     sw_monitor_config_params,
                                     robot_store_interface,
                                     black_box_comm)

    component_network = ComponentNetwork(config_file_path)

    recovery_config = config_data['recovery_config']
    recovery_manager = RecoveryManager(robot_id, recovery_config, component_network)

    # we initialise an overall status message that will continuously
    # be updated with the component statuses
    overall_status_msg = generate_robot_status_msg(robot_id)
    try:
        monitor_manager.start_monitors()
        recovery_manager.start_manager()
        while True:
            overall_status_msg["header"]["timestamp"] = time.time()
            overall_status_msg["payload"]["monitors"] = monitor_manager.get_component_status_list()
            if args.debug:
               print(json.dumps(overall_status_msg, indent=2))
            pyre_comm.shout(overall_status_msg)
            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        print('Component monitors exiting')
        pyre_comm.shutdown()
        monitor_manager.stop_monitors()
        black_box_comm.shutdown()
        recovery_manager.stop()
