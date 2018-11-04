import rospy

from component_monitoring.monitor_base import MonitorBase

class RosMasterMonitor(MonitorBase):
    def __init__(self, config_params):
        super(RosMasterMonitor, self).__init__(config_params)

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        status_msg['healthStatus'] = dict()

        master_running = True
        try:
            rospy.get_master().getPid()
        except:
            master_running = False

        status_msg['healthStatus']['status'] = master_running
        return status_msg
