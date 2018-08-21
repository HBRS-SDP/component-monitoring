import numpy as np

class EncoderMonitor(object):
    def __init__(self, velocity_threshold = 1.0, pivot_velocity_threshold = 1.0,
                 wheel_diameter = 0.073, inter_wheel_distance = 0.0893):
        self.velocity_threshold = velocity_threshold
        self.pivot_velocity_threshold = pivot_velocity_threshold
        self.wheel_diameter = wheel_diameter
        self.inter_wheel_distance = inter_wheel_distance

    def run(self, data):
        if len(data) > 0:
            num_wheels = len(data[0]['sensors'])
        else:
            return False
        encoder1_position = [[] for i in range(num_wheels)]
        encoder1_velocity = [[] for i in range(num_wheels)]
        encoder2_position = [[] for i in range(num_wheels)]
        encoder2_velocity = [[] for i in range(num_wheels)]
        encoderp_position = [[] for i in range(num_wheels)]
        encoderp_velocity = [[] for i in range(num_wheels)]
        times = []

        for item in data:
            for i in range(len(item['sensors'])):
                encoder1_position[i].append(item['sensors'][i]['encoder_1'])
                encoder1_velocity[i].append(item['sensors'][i]['velocity_1'])

                encoder2_position[i].append(item['sensors'][i]['encoder_2'])
                encoder2_velocity[i].append(item['sensors'][i]['velocity_2'])

                encoderp_position[i].append(item['sensors'][i]['encoder_pivot'])
                encoderp_velocity[i].append(item['sensors'][i]['velocity_pivot'])

            times.append(item['timestamp'])

        result = {}
        for i in range(num_wheels):
            wheel = "wheel_" + str(i+1)
            result[wheel] = {}
            result[wheel]['encoder_1_vel'] = self.is_velocity_within_threshold(
                          encoder1_position[i], encoder1_velocity[i], times)
            result[wheel]['encoder_2_vel'] = self.is_velocity_within_threshold(
                          encoder2_position[i], encoder2_velocity[i], times)
            result[wheel]['encoder_pivot_vel'] = self.is_velocity_within_threshold(
                          encoderp_position[i], encoderp_velocity[i], times)
            result[wheel]['differential_kinematics'] = self.is_differential_kinematics_consistent(
                          encoder1_velocity[i], encoder2_velocity[i], encoderp_velocity[i], times)
        return result

    def is_velocity_within_threshold(self, position, velocity, timestamp):
        diffs = [0.0]
        for i, dat in enumerate(position):
            position_diff = self.get_smallest_angular_diff(dat, position[i-1])
            time_diff = timestamp[i] - timestamp[i-1]
            differential = position_diff / time_diff
            diffs.append(np.abs(differential - velocity[i]))
        if np.median(diffs) < self.velocity_threshold:
            return True
        else:
            return False

    def is_differential_kinematics_consistent(self, enc1_v, enc2_v, encp_v, timestamp):
        r = self.wheel_diameter / 2.0
        l = self.inter_wheel_distance
        diffs = []
        for i, dat in enumerate(enc1_v):
            # calculate expected pivot angular velocity
            x = -r*(enc1_v[i] + enc2_v[i]) / l
            diffs.append(np.abs(x - encp_v[i]))
        if np.median(diffs) < self.pivot_velocity_threshold:
            return True
        else:
            return False

    def get_smallest_angular_diff(self, a1, a2):
        return np.arctan2(np.sin(a1-a2), np.cos(a1-a2))
