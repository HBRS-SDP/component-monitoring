from __future__ import print_function

import numpy as np
from scipy import signal
from queue import Queue
from ropod.pyre_communicator.base_class import RopodPyre
from component_monitoring.monitor_base import MonitorBase
import uuid
import time
import ast

class PressureFunctionalMonitor(MonitorBase):
    def __init__(self, config_params):
        super(PressureFunctionalMonitor, self).__init__(config_params)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)
        self.median_window_size = config_params.arguments.get('median_window_size', 3)
        self.fault_threshold = config_params.arguments.get('fault_threshold', 10.0)
        self.num_of_wheels = config_params.arguments.get('number_of_wheels', 4)
        self.collection_name = config_params.arguments.get('collection_name', 'ros_sw_ethercat_parser_data')
        self.black_box_id = config_params.arguments.get('black_box_id', 'black_box_001')
        self.wait_threshold = config_params.arguments.get('wait_threshold', 2.0)
        self.pyre_comm = PyreCommunicator(['MONITOR', 'ROPOD'], self.black_box_id)

    def stop(self):
        self.pyre_comm.shutdown()

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        pressure_values = self.get_pressure_statuses()

        for i in range(self.num_of_wheels) :
            status_msg['healthStatus']['pressure_sensor_'+str(i)] =  pressure_values[i]
        return status_msg

    def get_pressure_statuses(self):
        """Call db utils and data utils function from blackbox tools to get the
        pressure values from blackbox database. It checks for possible faults
        by comparing pressure value of one wheel with another. (Assumption: all 
        wheel must have same pressure values as they are always on the same floor)

        @returns: list of booleans

        """
        current_time = time.time()
        variables = [self.collection_name+"/sensors/"+str(i)+"/pressure" for i\
                in range(self.num_of_wheels)]
        self.pyre_comm.send_query(
                current_time-self.median_window_size, 
                current_time,
                variables)
        wait_start_time = time.time()
        while self.pyre_comm.data_queue.empty() and \
                wait_start_time + self.wait_threshold > time.time():
            time.sleep(0.1)
        sensor_statuses = [True]*self.num_of_wheels
        if self.pyre_comm.data_queue.empty():
            return sensor_statuses

        data = self.pyre_comm.data_queue.get()
        if [] in data:
            return sensor_statuses
        values = np.array(data)
        values = values.T
        for i in range(values.shape[1]):
            values[:,i] = signal.medfilt(values[:,i], kernel_size=3)
        avg_value = np.mean(values, axis=0)
        odd_index = self.find_suspected_sensors(avg_value)
        for i in odd_index :
            sensor_statuses[i] = False
        return sensor_statuses

    def find_suspected_sensors(self, arr):
        """find an odd value if one exist out of a list of 4 values and return 
        the index of that value. Returns None if no odd values are found.

        Parameters
        @arr: list of floats (length of this list if num_of_wheels)

        @returns: list of int

        """
        safe_set = set()
        suspected_set = set()
        for i in range(len(arr)-1) :
            for j in range(i+1, len(arr)) :
                if abs(arr[i] - arr[j]) < self.fault_threshold :
                    safe_set.add(i)
                    safe_set.add(j)
                    if i in suspected_set :
                        suspected_set.remove(i)
                    if j in suspected_set :
                        suspected_set.remove(j)
                else :
                    if i not in safe_set :
                        suspected_set.add(i)
                    if j not in safe_set :
                        suspected_set.add(j)
        return list(suspected_set)

class PyreCommunicator(RopodPyre):

    """Communicates with black box query interface through pyre messages and 
    provides that information through function calls

    :groups: list of string (pyre groups)
    :black_box_id: string

    """

    def __init__(self, groups, black_box_id):
        super(PyreCommunicator, self).__init__(
                'pyre_bb_comp_monitor_communicator', groups, list(), verbose=False)
        self.data_queue = Queue()
        self.sender_ids = []
        self.black_box_id = black_box_id
        self.variables = None
        self.start()

    def send_query(self, start_time, end_time, variables):
        """create and send a query message to black box query interface through
        pyre shout.

        :start_time: float
        :end_time: float
        :returns: None

        """
        msg = dict()
        msg['header'] = dict()
        msg['header']['metamodel'] = 'ropod-msg-schema.json'
        msg['header']['type'] = "DATA-QUERY"
        msg['header']['msgId'] = str(uuid.uuid4())
        msg['header']['timestamp'] = time.time()
        msg['payload'] = dict()
        msg_sender_id = str(uuid.uuid4())
        msg['payload']['senderId'] = msg_sender_id
        msg['payload']['startTime'] = start_time
        msg['payload']['endTime'] = end_time
        msg['payload']['blackBoxId'] = self.black_box_id
        msg['payload']['variables'] = variables
        self.variables = variables

        self.sender_ids.append(msg_sender_id)
        self.shout(msg)

    def zyre_event_cb(self, zyre_msg):
        '''Listens to "SHOUT" and "WHISPER" messages and stores the message
        if it is relevant.
        '''
        if zyre_msg.msg_type in ("SHOUT", "WHISPER"):
            self.receive_msg_cb(zyre_msg.msg_content)

    def receive_msg_cb(self, msg):
        '''Processes the incoming messages 
        returns a dictionary representing a JSON response message

        :msg: string (a message in JSON format)

        '''
        dict_msg = self.convert_zyre_msg_to_dict(msg)
        if dict_msg is None:
            return

        if 'header' not in dict_msg or 'type' not in dict_msg['header'] or \
                'payload' not in dict_msg or 'receiverId' not in dict_msg['payload']:
            return None
        message_type = dict_msg['header']['type']
        receiver_id = dict_msg['payload']['receiverId']

        if message_type == "DATA-QUERY" and receiver_id in self.sender_ids:
            data = self.parse_bb_data_msg(dict_msg)
            self.sender_ids.remove(receiver_id)
            self.data_queue.put(data)
            
    def parse_bb_data_msg(self, bb_data_msg):
        '''Returns a list of lists where each element is a list of values of 
        a variable

        Keyword arguments:
        bb_data_msg -- a black box data query response

        '''
        ans_list = list()
        if bb_data_msg:
            for var_name in self.variables:
                var_data = bb_data_msg['payload']['dataList'][var_name]
                ans_list.append([ast.literal_eval(item)[1] for item in var_data])
        return ans_list
