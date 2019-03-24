from os import stat

from component_monitoring.monitor_base import MonitorBase

class LaserDeviceMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(LaserDeviceMonitor, self).__init__(config_params, black_box_comm)
        self.dev_names = list()
        self.dev_status_names = list()
        for mapping in config_params.mappings:
            self.dev_names.append(mapping.inputs[0])
            self.dev_status_names.append(mapping.outputs[0].name)

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        status_msg['healthStatus'] = dict()
        status = True
        for i, dev_name in enumerate(self.dev_names):
            status_msg['healthStatus'][self.dev_status_names[i]] = self.__device_exists(dev_name)
            if not status_msg['healthStatus'][self.dev_status_names[i]]:
                status = False
        status_msg['healthStatus']['status'] = status
        return status_msg

    def __device_exists(self, dev_name):
        try:
            stat(dev_name)
            return True
        except OSError:
            return False
