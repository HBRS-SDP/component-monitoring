from __future__ import print_function

import time
from component_monitoring.monitor_base import MonitorBase
from black_box_tools.data_utils import DataUtils

class EStopFunctionalMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(EStopFunctionalMonitor, self).__init__(config_params, black_box_comm)

        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)

        self.num_of_wheels = config_params.arguments.get('number_of_wheels', 4)
        self.variable_name_pattern = config_params.arguments.get('variable_name_pattern',
                                                                 'ros_sw_ethercat_parser_data/sensors/*/status1')

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status, e_stop_pressed = self.get_e_stop_info()
        status_msg["healthStatus"][self.output_names[0]] = e_stop_pressed
        status_msg["healthStatus"]["status"] = status
        return status_msg

    def get_e_stop_info(self):
        """Sends a query to bb query interface. Parses the data to
        get the required info.
        :returns: (bool, bool)  == (status, e_stop_pressed)

        """
        # variables = [self.variable_name_pattern.replace('*', str(i)) for i\
        #              in range(self.num_of_wheels)]
        # dict_msg = self.black_box_comm.send_latest_data_query(variables)

        # if dict_msg is None:
        #     return (False, True)

        # _, data = DataUtils.parse_bb_latest_data_msg(dict_msg)
        # if not data or all(not x for x in data):
        #     return (False, True)

        # for i in data:
        #     if i is None:
        #         return (False, True)
        # status_list = [i[1] for i in data]

        # # if different wheel have different status
        # if status_list.count(status_list[0]) != len(status_list):
        #     return (False, True)

        # e_stop_pressed_list = []
        # for wheel_number in range(self.num_of_wheels):
        #     status1 = status_list[wheel_number]
        #     # list of flags as described in https://git.ropod.org/ropod/smartwheel/blob/master/README.md
        #     flag_list = [i == '1' for i in list(bin(int(status1))[2:].zfill(5))[::-1]]
        #     e_stop_pressed_list.append(flag_list[2])
        #return (True, all(e_stop_pressed_list))
        return (True, False)
