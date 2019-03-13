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
        self.num_of_wheels = config_params.arguments.get('number_of_wheels', 4)
        self.db_name = config_params.arguments.get('db_name', 'logs')
        self.collection_name = config_params.arguments.get('collection_name', 'ros_sw_ethercat_parser_data')

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        pressure_values = self.get_pressure_values()

        for i in range(self.num_of_wheels) :
            status_msg['healthStatus']['pressure_sensor_'+str(i)] =  pressure_values[i]
        return status_msg

    def get_pressure_values(self):
        """Call db utils and data utils function from blackbox tools to get the
        pressure values from blackbox database.
        :returns: list of floats

        """
        docs = DBUtils.get_docs_of_last_n_secs(
                self.db_name, 
                self.collection_name, 
                self.median_window_size)
        values = DataUtils.get_all_measurements(docs, 'sensors/*/pressure', self.num_of_wheels, Filters.MEDIAN)
        avg_value = np.mean(values, axis=0)
        fault_list = [True]*self.num_of_wheels
        odd_index = self.find_suspected_sensors(avg_value)
        for i in odd_index :
            fault_list[i] = False
        return fault_list

    def find_suspected_sensors(self, arr):
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

