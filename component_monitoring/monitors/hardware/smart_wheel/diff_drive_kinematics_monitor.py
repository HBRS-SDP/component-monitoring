from __future__ import print_function
import numpy as np

import time
import uuid

from component_monitoring.monitor_base import MonitorBase
from black_box_tools.data_utils import DataUtils

class DiffDriveKinematicsMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(DiffDriveKinematicsMonitor, self).__init__(config_params, black_box_comm)

        self.variable_names = list()
        self.status_names = list()
        for mapping in config_params.mappings:
            self.variable_names.extend(mapping.inputs)
            for output_mapping in mapping.outputs:
                self.status_names.append(output_mapping.name)
        self.num_wheels = config_params.arguments['number_of_wheels']
        self.pivot_velocity_threshold = config_params.arguments['pivot_velocity_threshold']
        self.wheel_diameter = config_params.arguments['wheel_diameter']
        self.inter_wheel_distance = config_params.arguments['inter_wheel_distance']

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        result, overall_result = self.get_diff_drive_statuses()

        status_msg['healthStatus'] = dict()
        status_msg['healthStatus']['result'] = result
        status_msg['healthStatus']['status'] = overall_result
        return status_msg

    def get_diff_drive_statuses(self):
        # current_time = time.time()
        # variables = []
        # for inp in self.variable_names:
        #     v = [inp.replace('*', str(i)) for i\
        #                  in range(self.num_wheels)]
        #     variables.extend(v)
        # dict_msg = self.black_box_comm.send_query(current_time-1.0,
        #                                           current_time,
        #                                           variables)
        # var_names, data = DataUtils.parse_bb_data_msg(dict_msg)
        # result, overall_result = self.__process_data(var_names, data)
        #return result, overall_result
        return None, None

    def __process_data(self, var_names, data):
        if not data or all(not x for x in data):
            return {}, False

        encoder1_vel = [[] for i in range(self.num_wheels)]
        encoder2_vel = [[] for i in range(self.num_wheels)]
        pivot_encoder_vel = [[] for i in range(self.num_wheels)]

        wheel_num_pos = self.variable_names[0].find('*')
        for index, v in enumerate(var_names):
            data_list = data[index]
            wheel_index = int(v[wheel_num_pos])
            if v.endswith('velocity_1'):
                for data_instance in data_list:
                    data_instance = data_instance if data_instance else [0.0, 0.0]
                    encoder1_vel[wheel_index].append(data_instance[1])
            elif v.endswith('velocity_2'):
                for data_instance in data_list:
                    data_instance = data_instance if data_instance else [0.0, 0.0]
                    encoder2_vel[wheel_index].append(data_instance[1])
            elif v.endswith('velocity_pivot'):
                for data_instance in data_list:
                    data_instance = data_instance if data_instance else [0.0, 0.0]
                    pivot_encoder_vel[wheel_index].append(data_instance[1])

        result = {}
        overall_result = True
        for i in range(self.num_wheels):
            wheel = 'wheel_{0}'.format(i+1)
            diff_kinematics_consistent, residual = self.__is_diff_kinematics_consistent(encoder1_vel[i],
                                                                                        encoder2_vel[i],
                                                                                        pivot_encoder_vel[i])

            overall_result = overall_result and diff_kinematics_consistent
            result[wheel] = {}
            result[wheel][self.status_names[0]] = diff_kinematics_consistent
            result[wheel][self.status_names[1]] = residual
        return result, overall_result

    def __is_diff_kinematics_consistent(self, enc1_v, enc2_v, pivot_enc_v):
        r = self.wheel_diameter / 2.0
        l = self.inter_wheel_distance
        diffs = []
        for i in range(len(enc1_v)):
            # calculate expected pivot angular velocity
            x = -r * (enc1_v[i] + enc2_v[i]) / l
            diffs.append(np.abs(x - pivot_enc_v[i]))

        if np.median(diffs) < self.pivot_velocity_threshold:
            return True, np.median(diffs)
        return False, np.median(diffs)
