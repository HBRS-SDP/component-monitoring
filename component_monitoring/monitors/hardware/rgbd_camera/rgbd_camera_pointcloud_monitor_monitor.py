from component_monitoring.monitor_base import MonitorBase

class Rgbd_CameraPointcloud_MonitorMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(Rgbd_CameraPointcloud_MonitorMonitor, self).__init__(config_params, black_box_comm)

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = False
        return status_msg
