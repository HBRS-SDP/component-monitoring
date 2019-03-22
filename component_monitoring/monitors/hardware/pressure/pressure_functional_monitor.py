from __future__ import print_function

import time
from queue import Queue
import uuid

import numpy as np
from scipy import signal

from ropod.pyre_communicator.base_class import RopodPyre
from black_box_tools.data_utils import DataUtils
from component_monitoring.monitor_base import MonitorBase

class PressureFunctionalMonitor(MonitorBase):
    def __init__(self, config_params):
        super(PressureFunctionalMonitor, self).__init__(config_params)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)
        self.median_window_size = config_params.arguments.get('median_window_size', 3)
        self.fault_threshold = config_params.arguments.get('fault_threshold', 10.0)
        self.num_of_wheels = config_params.arguments.get('number_of_wheels', 4)
        self.variable_name_pattern = config_params.arguments.get('variable_name_pattern',
                                                                 'ros_sw_ethercat_parser_data/sensors/*/pressure')
        self.black_box_id = config_params.arguments.get('black_box_id', 'black_box_001')
        self.wait_threshold = config_params.arguments.get('wait_threshold', 2.0)
        self.pyre_comm = PyreCommunicator(['MONITOR', 'ROPOD'], self.black_box_id)

    def stop(self):
        self.pyre_comm.shutdown()

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        status, pressure_values = self.get_pressure_statuses()

        for i in range(self.num_of_wheels):
            status_msg['healthStatus']['pressure_sensor_' + str(i)] = pressure_values[i]
        status_msg['healthStatus']['status'] = status
        return status_msg

    def get_pressure_statuses(self):
        """Call db utils and data utils function from blackbox tools to get the
        pressure values from blackbox database. It checks for possible faults
        by comparing pressure value of one wheel with another. (Assumption: all
        wheel must have same pressure values as they are always on the same floor)

        @returns: list of booleans

        """
        current_time = time.time()
        variables = [self.variable_name_pattern.replace('*', str(i)) for i\
                     in range(self.num_of_wheels)]
        self.pyre_comm.send_query(current_time-self.median_window_size,
                                  current_time,
                                  variables)
        wait_start_time = time.time()
        while self.pyre_comm.data_queue.empty() and \
                wait_start_time + self.wait_threshold > time.time():
            time.sleep(0.1)
        sensor_statuses = [True] * self.num_of_wheels
        if self.pyre_comm.data_queue.empty():
            return (False, sensor_statuses)

        data = self.pyre_comm.data_queue.get()
        if [] in data:
            return (False, sensor_statuses)

        # the first dimension of the data is the number of wheels,
        # the second the number of data items, and the third
        # a pair of (timestamp, data) values; we are only interested
        # in the data values, so we discard the timestamps
        values = np.array(data)[:, :, 1]
        values = values.T
        for i in range(values.shape[1]):
            values[:, i] = signal.medfilt(values[:, i], kernel_size=3)
        avg_value = np.mean(values, axis=0)
        odd_index = self.find_suspected_sensors(avg_value)
        for i in odd_index:
            sensor_statuses[i] = False
        return (True, sensor_statuses)

    def find_suspected_sensors(self, arr):
        """find an odd value if one exist out of a list of 4 values and return
        the index of that value. Returns None if no odd values are found.

        Parameters
        @arr: list of floats (length of this list if num_of_wheels)

        @returns: list of int

        """
        safe_set = set()
        suspected_set = set()
        for i in range(len(arr)-1):
            for j in range(i+1, len(arr)):
                if abs(arr[i] - arr[j]) < self.fault_threshold:
                    safe_set.add(i)
                    safe_set.add(j)
                    if i in suspected_set:
                        suspected_set.remove(i)
                    if j in suspected_set:
                        suspected_set.remove(j)
                else:
                    if i not in safe_set:
                        suspected_set.add(i)
                    if j not in safe_set:
                        suspected_set.add(j)
        return list(suspected_set)

class PyreCommunicator(RopodPyre):
    """Communicates with black box query interface through pyre messages and
    provides that information through function calls

    :groups: list of string (pyre groups)
    :black_box_id: string

    """
    def __init__(self, groups, black_box_id):
        super(PyreCommunicator, self).__init__('pyre_bb_comp_monitor_communicator',
                                               groups, list(), verbose=False)
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
        msg_sender_id = str(uuid.uuid4())
        data_query_msg = DataUtils.get_bb_query_msg(msg_sender_id, self.black_box_id,
                                                    variables, start_time, end_time)
        self.variables = variables
        self.sender_ids.append(msg_sender_id)
        self.shout(data_query_msg)

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
            _, data = DataUtils.parse_bb_data_msg(dict_msg)
            self.sender_ids.remove(receiver_id)
            self.data_queue.put(data)
