from component_monitoring.monitor_base import MonitorBase

class LaserDeviceMonitor(MonitorBase):
    def __init__(self, config_params):
        super(LaserDeviceMonitor, self).__init__(config_params)
        self.device_names = list()
        self.device_status_names = list()
        for mapping in config_params.mappings:
            self.device_names.append(mapping.inputs[0])
            self.device_status_names.append(mapping.outputs[0].name)

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        for i, device_name in enumerate(self.device_names):
            status_msg['healthStatus'][self.device_status_names[i]] = False
        return status_msg
