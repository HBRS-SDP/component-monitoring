from component_monitoring.monitor_base import MonitorBase

class EncoderFunctionalMonitor(MonitorBase):
    def __init__(self, config_params):
        super(EncoderFunctionalMonitor, self).__init__(config_params)

        self.variable_names = list()
        self.status_names = list()
        for mapping in config_params.mappings:
            self.variable_names.append(mapping.inputs[0])
            for output_mapping in mapping.outputs:
                self.status_names.append(output_mapping.name)
        self.velocity_threshold = config_params.arguments['velocity_threshold']
        self.pivot_velocity_threshold = config_params.arguments['pivot_velocity_threshold']
        self.wheel_diameter = config_params.arguments['wheel_diameter']
        self.inter_wheel_distance = config_params.arguments['inter_wheel_distance']

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        return status_msg
