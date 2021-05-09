from component_monitoring.monitor_base import MonitorBase
import rospy
from sensor_msgs.msg import PointCloud2

class RgbdCameraPointcloudMonitorMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(RgbdCameraPointcloudMonitorMonitor, self).__init__(config_params, black_box_comm)
        self._subscriber = rospy.Subscriber('/hsrb/head_rgbd_sensor/depth_registered/points', PointCloud2, self.callback)
        self._pointcloud = None

    def callback(self, data):
        self._pointcloud = data.data

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = False
        if self._pointcloud is not None:
            rospy.loginfo("I got poincloud!")
        else:
            rospy.logwarn("Oh no I have no poincloud :-( .")
        return status_msg
