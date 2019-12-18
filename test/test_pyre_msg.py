#!/usr/bin/env python

from ropod.pyre_communicator.base_class import RopodPyre
import time

class PyreCommunicator(RopodPyre):

    """Test if component monitor is shouting any messages or not

    :groups: list of string (pyre groups)
    :black_box_id: string

    """

    def __init__(self, groups, black_box_id):
        super(PyreCommunicator, self).__init__({
                'node_name': 'comp_monitor_test',
                'groups': groups, 
                'message_types': list()},
                verbose=False)
        self.msg_counter = 0
        self.start()

    def zyre_event_cb(self, zyre_msg):
        '''Listens to "SHOUT" messages '''
        if zyre_msg.msg_type == "SHOUT":
            self.receive_msg_cb(zyre_msg.msg_content)

    def receive_msg_cb(self, msg):
        '''Processes the incoming messages 

        :msg: string (a message in JSON format)

        '''
        dict_msg = self.convert_zyre_msg_to_dict(msg)
        if dict_msg is None:
            return

        if 'header' not in dict_msg or 'type' not in dict_msg['header']:
            return None
        message_type = dict_msg['header']['type']
        if message_type != "HEALTH-STATUS" :
            return

        try:
            assert('payload' in dict_msg)
            assert('robotId' in dict_msg['payload'])
            assert('monitors' in dict_msg['payload'])
            self.msg_counter += 1
        except Exception as e:
            print("Invalid component monitor message received")

if __name__ == "__main__":
    pyre_comm = PyreCommunicator(['MONITOR'], 'ropod_001')
    test_start_time = time.time()
    test_duration = 15
    print("Testing ... (for", test_duration, "seconds)")
    while test_start_time + test_duration > time.time():
        time.sleep(0.1)
    try:
        assert(pyre_comm.msg_counter > 0)
        print("Test PASSED")
    except Exception as e:
        print("Test FAILED", str(e))
    pyre_comm.shutdown()
