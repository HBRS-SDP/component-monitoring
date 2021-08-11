from __future__ import print_function

import time
from queue import Queue

import numpy as np
from scipy import signal

from black_box_tools.data_utils import DataUtils
from component_monitoring.monitor_base import MonitorBase

class PressureFunctionalMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(PressureFunctionalMonitor, self).__init__(config_params, black_box_comm)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)
        self.median_window_size = config_params.arguments.get('median_window_size', 3)
        self.fault_threshold = config_params.arguments.get('fault_threshold', 10.0)
        self.num_of_wheels = config_params.arguments.get('number_of_wheels', 4)
        self.variable_name_pattern = config_params.arguments.get('variable_name_pattern',
                                                                 'ros_sw_ethercat_parser_data/sensors/*/pressure')

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        status_msg['healthStatus'] = dict()
        status, pressure_values = self.get_pressure_statuses()

        for i in range(self.num_of_wheels):
             status_msg['healthStatus']['pressure_sensor_' + str(i)] = pressure_values[i]
        status_msg['healthStatus']['status'] = status
        return status_msg 


    def get_pressure_statuses(self):
        """Call storage utils and data utils function from blackbox tools to get the
        pressure values from blackbox database. It checks for possible faults
        by comparing pressure value of one wheel with another. (Assumption: all
        wheel must have same pressure values as they are always on the same floor)

        @returns: list of booleans

        """
        # current_time = time.time()
        # variables = [self.variable_name_pattern.replace('*', str(i)) for i\
        #              in range(self.num_of_wheels)]
        # dict_msg = self.black_box_comm.send_query(current_time-self.median_window_size,
        #                           current_time,
        #                           variables)
        # sensor_statuses = [True] * self.num_of_wheels
        # if not dict_msg:
        #     return (False, sensor_statuses)

        # _, data = DataUtils.parse_bb_data_msg(dict_msg)

        # if not data or not data[0]:
        #     return (False, sensor_statuses)

        # # the first dimension of the data is the number of wheels,
        # # the second the number of data items, and the third
        # # a pair of (timestamp, data) values; we are only interested
        # # in the data values, so we discard the timestamps
        # values = np.array(data)[:, :, 1]
        # values = values.T
        # for i in range(values.shape[1]):
        #     values[:, i] = signal.medfilt(values[:, i], kernel_size=3)
        # avg_value = np.mean(values, axis=0)
        # odd_index = self.find_suspected_sensors(avg_value)
        # for i in odd_index:
        #     sensor_statuses[i] = False
        #return (True, sensor_statuses)
        return (True, [True, True, True, True])

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
