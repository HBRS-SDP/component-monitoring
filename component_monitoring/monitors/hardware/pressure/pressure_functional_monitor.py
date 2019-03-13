from __future__ import print_function

import numpy as np
from component_monitoring.monitor_base import MonitorBase
from black_box_tools.data_utils import DataUtils
from black_box_tools.db_utils import DBUtils
from black_box_tools.data_utils import Filters

class PressureFunctionalMonitor(MonitorBase):
    def __init__(self, config_params):
        super(PressureFunctionalMonitor, self).__init__(config_params)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)
        self.median_window_size = config_params.arguments.get('median_window_size', 3)
        self.fault_threshold = config_params.arguments.get('fault_threshold', 10.0)

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        pressure_values = self.get_pressure_values()

        for i in range(4) :
            status_msg['healthStatus']['fault_wheel_'+str(i)] =  pressure_values[i]
        return status_msg

    def get_pressure_values(self):
        """Call db utils and data utils function from blackbox tools to get the
        pressure values from blackbox database.
        :returns: list of floats

        """
        newest_doc = DBUtils.get_newest_doc('logs', 'ros_sw_ethercat_parser_data')
        newest_timestamp = newest_doc['timestamp']
        docs = DBUtils.get_docs_of_last_n_secs(
                'logs', 
                'ros_sw_ethercat_parser_data', 
                self.median_window_size)
        values = DataUtils.get_all_measurements(docs, 'sensors/*/pressure', 4, Filters.MEDIAN)
        avg_value = np.mean(values, axis=0)
        fault_list = [False]*4
        odd_index = self.find_single_odd_value(avg_value)
        for i in odd_index :
            fault_list[i] = True
        return fault_list

    def find_single_odd_value(self, arr):
        """find an odd value if one exist out of a list of 4 values and return 
        the index of that value. Returns None if no odd values are found.

        :arr: list of 4 floats
        :returns: int/None

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

