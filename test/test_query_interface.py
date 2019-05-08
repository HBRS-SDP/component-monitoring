from __future__ import print_function
import time
import os.path
import json
import unittest

from ropod.pyre_communicator.base_class import RopodPyre
from ropod.utils.models import MessageFactory
from ropod.utils.uuid import generate_uuid

from component_monitoring.config.config_utils import ConfigUtils
from component_monitoring.utils.component_monitoring_query_interface import ComponentMonitoringQueryInterface

class QueryTest(RopodPyre):
    def __init__(self):
        super(QueryTest, self).__init__('comp_mon_query_test', ['ROPOD', 'MONITOR'], [], verbose=True, acknowledge=True)
        self.response = None
        self.start()

    def send_request(self, msg_type, payload_dict=None):
        query_msg = MessageFactory.get_header(msg_type, recipients=[])

        query_msg['payload'] = {}
        query_msg['payload']['senderId'] = generate_uuid()
        if payload_dict is not None :
            for key in payload_dict.keys() :
                query_msg['payload'][key] = payload_dict[key]

        print(json.dumps(query_msg, indent=2, default=str))
        self.shout(query_msg)

    def receive_msg_cb(self, msg_content):
        message = self.convert_zyre_msg_to_dict(msg_content)
        if message is None:
            return

        self.response = message

class QueryInterfaceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_dir = os.path.abspath(os.path.dirname(__file__))
        main_dir = os.path.dirname(test_dir)
        config_file = os.path.join(main_dir, "config/component_monitoring_config.yaml")
        cls.config_data = ConfigUtils.read_config(config_file)
        cls.robot_id = cls.config_data['robot_id']
        cls.query_interface = ComponentMonitoringQueryInterface(
                config_file, main_dir)
        cls.test_pyre_node = QueryTest()
        cls.timeout_duration = 3
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.query_interface.shutdown()
        cls.test_pyre_node.shutdown()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_config(self):
        msg_type = "COMP-MON-CONFIG"
        message = self.send_request_get_response(msg_type, payload_dict={'robotId':self.robot_id})

        self.assertNotEqual(message, None)
        self.assertIn('header', message)
        self.assertIn('type', message['header'])
        self.assertEqual(message['header']['type'], msg_type)
        self.assertIn('payload', message)
        self.assertIn('config', message['payload'])
        self.assertIn('main_config', message['payload']['config'])
        self.assertEqual(message['payload']['config']['main_config'], self.config_data)

    def send_request_get_response(self, msg_type, payload_dict = None):
        self.test_pyre_node.send_request(msg_type, payload_dict)
        start_time = time.time()
        while self.test_pyre_node.response is None and \
                start_time + self.timeout_duration > time.time():
            time.sleep(0.2)
        message = self.test_pyre_node.response
        self.test_pyre_node.response = None
        return message

if __name__ == '__main__':
    unittest.main()
