import json
from bson import json_util
import numpy as np
from sensor_msgs import point_cloud2

from component_monitoring.config.config_params import MonitorModeConfig
from component_monitoring.monitor_base import MonitorBase
import rospy
from sensor_msgs.msg import PointCloud2


class RgbdCameraPointcloudMonitorMonitor(MonitorBase):
    def __init__(self, config_params: MonitorModeConfig, server_address: str, control_channel: str):
        super(RgbdCameraPointcloudMonitorMonitor, self).__init__(config_params, server_address, control_channel)
        self._subscriber = rospy.Subscriber('/hsrb/head_rgbd_sensor/pointcloud', PointCloud2, self.callback)
        # self.nan_threshold = self.config_params.mappings[0].outputs[0].expected

    def start(self):
        super(RgbdCameraPointcloudMonitorMonitor, self).start()
    
    def stop(self):
        super(RgbdCameraPointcloudMonitorMonitor, self).stop()

    def callback(self, data):
        gen = point_cloud2.read_points(data, field_names=("x", "y", "z"))  # for yelding the errors
        # gen = point_cloud2.read_points(data, field_names=("x", "y", "z"), skip_nans=True) # smart getting rid of NaNs
        self._pointcloud = np.array(gen)
        nan_ratio = np.isnan(self._pointcloud).sum()/np.prod(self._pointcloud)
        self.healthstatus['nans'] = nan_ratio
        self.logger.info(f"Detected {self.healthstatus['nans']*100}% NaN values in the pointcloud.")

    def publish_status(self):
        msg = {}
        msg["monitorName"] = self.config_params.name
        msg["monitorDescription"] = self.config_params.description
        msg["healthStatus"] = self.healthstatus
        if self.valid_status_message(msg):
            self.send_control_msg(json.dumps(msg, default=json_util.default).encode('utf-8'))
            # result = future.get(timeout=60) # potential result parsing
        else:
            self.logger.error(f"Validation of event message failed in {self.config_params.name}!")