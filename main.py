#!/usr/bin/env python
import time
import json
import uuid
import argparse
import rospy

#from ropod.pyre_communicator.base_class import RopodPyre
from component_monitoring.config.config_utils import ConfigUtils
from component_monitoring.monitor_manager import MonitorManager
#from component_monitoring.recovery_manager import RecoveryManager
from component_monitoring.utils.robot_store_interface import RobotStoreInterface
from component_monitoring.utils.component_network import ComponentNetwork
#from component_monitoring.communication import BlackBoxPyreCommunicator
from db.db_main import DB_Storage


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

    # we store the component configuration in the database
    #robot_store_interface.store_component_configuration(hw_monitor_config_params,
    #                                                    sw_monitor_config_params)

    # we initialise a manager for the monitors that will continuously
    # update the component status message
    monitor_manager = MonitorManager(hw_monitor_config_params,
                                     sw_monitor_config_params)

    component_network = ComponentNetwork(config_file_path)

    try:
        monitor_manager.start()
        monitor_manager.join()

        db_config = config_data['db_config']
        db_storage = DB_Storage(
            db_config, topic_name="hsrb_monitoring_feedback_rgbd")
        # db_storage.store_messages()
        db_storage.start()

    except (KeyboardInterrupt, SystemExit):
        print('Component monitors exiting')
