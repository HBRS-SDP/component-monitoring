#! /usr/bin/env python
from __future__ import print_function
import os
import sys
import uuid
import time

from ropod.pyre_communicator.base_class import RopodPyre

from component_monitoring.config.config_utils import ConfigUtils

class ComponentMonitoringQueryInterface(RopodPyre):
    '''An interface for querying config files for component monitoring.

    '''
    def __init__(self, config_file, main_dir):
        config_data = ConfigUtils.read_config(config_file)
        self.robot_id = config_data['robot_id']
        self.config_file = config_file
        self.main_dir = main_dir
        super(ComponentMonitoringQueryInterface, self).__init__(
                'component_monitoring_query_interface_' + self.robot_id,
                 ['ROPOD'], 
                 list(),
                 verbose=True)
        self.start()

    def zyre_event_cb(self, zyre_msg):
        '''Listens to "SHOUT" and "WHISPER" messages and returns a response
        if the incoming message is a query message for this black box
        '''
        if zyre_msg.msg_type in ("SHOUT", "WHISPER"):
            response_msg = self.receive_msg_cb(zyre_msg.msg_content)
            if response_msg:
                self.whisper(response_msg, zyre_msg.peer_uuid)

    def receive_msg_cb(self, msg):
        '''Processes requests for component monitoring config queries;
        returns a dictionary representing a JSON response message

        Only listens to "COMP-MON-CONFIG" message for this robot id;
        ignores all other messages (i.e. returns no value in such cases)

        @param msg a message in JSON format
        '''
        dict_msg = self.convert_zyre_msg_to_dict(msg)

        # sanity check
        if dict_msg is None:
            return
        if 'header' not in dict_msg or 'payload' not in dict_msg or 'type' not in\
                dict_msg['header'] or 'robotId' not in dict_msg['payload'] or \
                'senderId' not in dict_msg['payload']:
            return

        message_type = dict_msg['header']['type']
        if message_type == 'COMP-MON-CONFIG':
            robot_id = dict_msg['payload']['robotId']
            if robot_id != self.robot_id:
                return

            config = self.get_config()
            response_msg = self.__get_response_msg_skeleton(message_type)
            response_msg['payload']['receiverId'] = dict_msg['payload']['senderId']
            response_msg['payload']['config'] = config
            return response_msg

    def __get_response_msg_skeleton(self, msg_type):
        '''Returns a dictionary representing a query response for the given message type.
        The dictionary has the following format:
        {
            "header":
            {
                "metamodel": "ropod-msg-schema.json",
                "type": msg_type,
                "msgId": message-uuid,
                "timestamp": current-time
            },
            "payload":
            {
                "receiverId": ""
            }
        }

        Keyword arguments:
        @param msg_type a string representing a message type

        '''
        response_msg = dict()
        response_msg['header'] = dict()
        response_msg['header']['metamodel'] = 'ropod-msg-schema.json'
        response_msg['header']['type'] = msg_type
        response_msg['header']['msgId'] = str(uuid.uuid4())
        response_msg['header']['timestamp'] = time.time()
        response_msg['payload'] = dict()
        response_msg['payload']['receiverId'] = ''
        return response_msg

    def get_config(self):
        """Get all configuration for component monitoring and return it in a 
        single dict.

        :returns: dict

        """
        config = dict()
        config_data = ConfigUtils.read_config(self.config_file)
        config['main_config'] = config_data

        hw_monitor_config_dir = os.path.join(self.main_dir, config_data['config_dirs']['hardware'])
        hw_monitor_config_params = ConfigUtils.get_config_params(hw_monitor_config_dir)
        config['hw_config'] = [i.get_dict() for i in hw_monitor_config_params]
        sw_monitor_config_dir = os.path.join(self.main_dir, config_data['config_dirs']['software'])
        sw_monitor_config_params = ConfigUtils.get_config_params(sw_monitor_config_dir)
        config['sw_config'] = [i.get_dict() for i in sw_monitor_config_params]

        return config

if __name__ == "__main__":
    util_dir = os.path.abspath(os.path.dirname(__file__))
    code_dir = os.path.dirname(util_dir)
    main_dir = os.path.dirname(code_dir)
    config_file = os.path.join(main_dir, "config/component_monitoring_config.yaml")

    if len(sys.argv) < 2 :
        print("USAGE: python3 query_interface.py CONFIG_FILE.yaml")
        print("No config file provided. Using default config file")
    else :
        config_file = sys.argv[1]
    comp_mon_query_interface = ComponentMonitoringQueryInterface(config_file, main_dir)

    try:
        while True:
            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        comp_mon_query_interface.shutdown()
        print('Query interface interrupted; exiting')
