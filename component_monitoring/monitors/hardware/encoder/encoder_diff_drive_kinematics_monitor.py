import numpy as np

from component_monitoring.monitor_base import MonitorBase

class EncoderDiffDriveKinematicsMonitor(MonitorBase):
    def __init__(self, config_params):
        super(EncoderDiffDriveKinematicsMonitor, self).__init__(config_params)

        self.variable_names = list()
        self.status_names = list()
        for mapping in config_params.mappings:
            self.variable_names.append(mapping.inputs[0])
            for output_mapping in mapping.outputs:
                self.status_names.append(output_mapping.name)
        self.num_wheels = config_params.arguments['number_of_wheels']
        self.pivot_velocity_threshold = config_params.arguments['pivot_velocity_threshold']
        self.wheel_diameter = config_params.arguments['wheel_diameter']
        self.inter_wheel_distance = config_params.arguments['inter_wheel_distance']

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        # TODO: use the black box query interface to get the desired data
        data = list()
        status_msg['healthStatus'] = self.__process_data(data)
        return status_msg

    def __process_data(self, data):
        if not data:
            return False

        encoder1_vel = [[] for i in range(self.num_wheels)]
        encoder2_vel = [[] for i in range(self.num_wheels)]
        pivot_encoder_vel = [[] for i in range(self.num_wheels)]

        times = []
        for item in data:
            for i in range(len(item['sensors'])):
                encoder1_vel[i].append(item['sensors'][i]['velocity_1'])
                encoder2_vel[i].append(item['sensors'][i]['velocity_2'])
                pivot_encoder_vel[i].append(item['sensors'][i]['velocity_pivot'])
            times.append(item['timestamp'])

        result = {}
        for i in range(self.num_wheels):
            wheel = 'wheel_{0}'.format(i+1)
            diff_kinematics_consistent = self.__is_diff_kinematics_consistent(encoder1_vel[i],
                                                                              encoder2_vel[i],
                                                                              pivot_encoder_vel[i])

            result[wheel] = {}
            result[wheel][self.status_names[0]] = diff_kinematics_consistent
        return result

    def __is_diff_kinematics_consistent(self, enc1_v, enc2_v, pivot_enc_v):
        r = self.wheel_diameter / 2.0
        l = self.inter_wheel_distance
        diffs = []
        for i in range(len(enc1_v)):
            # calculate expected pivot angular velocity
            x = -r * (enc1_v[i] + enc2_v[i]) / l
            diffs.append(np.abs(x - pivot_enc_v[i]))

        if np.median(diffs) < self.pivot_velocity_threshold:
            return True
        return False
