from __future__ import print_function

import time
from component_monitoring.monitor_base import MonitorBase
from black_box_tools.data_utils import DataUtils

class BatteryFunctionalMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(BatteryFunctionalMonitor, self).__init__(config_params, black_box_comm)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)

        self.num_of_wheels = config_params.arguments.get('number_of_wheels', 4)
        self.highest_voltage = config_params.arguments.get('highest_voltage', 30.0)
        self.lowest_voltage = config_params.arguments.get('lowest_voltage', 10.0)
        self.variable_name_pattern = config_params.arguments.get('variable_name_pattern',
                                                                 'ros_sw_ethercat_parser_data/sensors/*/voltage_bus')

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status, battery_level = self.get_avg_battery()
        status_msg["healthStatus"][self.output_names[0]] = battery_level
        status_msg["healthStatus"]["status"] = status
        return status_msg

    def get_avg_battery(self):
        """Send a query message to bb query interface for voltage values for
        each wheel. Take average voltage and find percentage.
        :returns: (bool, float) == (status, percentage)

        """
        variables = [self.variable_name_pattern.replace('*', str(i)) for i\
                     in range(self.num_of_wheels)]
        dict_msg = self.black_box_comm.send_latest_data_query(variables)
        if dict_msg is None:
            return (False, 0.0)

        _, data = DataUtils.parse_bb_latest_data_msg(dict_msg)
        if not data or all(not x for x in data):
            return (False, 0.0)

        for i in data:
            if i is None:
                return (False, 0.0)
        battery_voltage = sum([i[1] for i in data])/self.num_of_wheels
        battery_percentage = ((battery_voltage - self.lowest_voltage) / \
                (self.highest_voltage - self.lowest_voltage)) * 100.0
        return (True, battery_percentage)
