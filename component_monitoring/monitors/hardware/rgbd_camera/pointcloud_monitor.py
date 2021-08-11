import os
import time

import numpy as np
from sensor_msgs import point_cloud2

from component_monitoring.config.config_params import MonitorModeConfig, OutputConfig
from component_monitoring.monitor_base import MonitorBase
import rospy
from sensor_msgs.msg import PointCloud2

from component_monitoring.monitor_exception import ConfigurationError


class PointcloudMonitor(MonitorBase):
    def __init__(self, component_name, config_params: MonitorModeConfig, server_address: str, control_channel: str):
        super(PointcloudMonitor, self).__init__(component_name, config_params, server_address, control_channel)
        # parse the pointcloud monitor specific mappings
        if len(config_params.mappings) > 1:
            raise ConfigurationError("Only one mapping is expected for pointcloud monitor!")
        mapping = config_params.mappings[0]
        if len(mapping.inputs) > 1:
            raise ConfigurationError("More than one input topic for pointcloud subscription provided")
        self.ros_topic = mapping.inputs[0]
        output = mapping.outputs[0]
        if not isinstance(output, OutputConfig):
            raise ConfigurationError("No output configuration provided!")
        self.status_name = output.name
        if self.status_name == '':
            raise ConfigurationError("No output name provided!")
        self.status_type = output.obtained_value_type
        if self.status_type == '':
            raise ConfigurationError("No output type provided!")
        try:
            self.nan_threshold = float(output.expected_value)
        except ValueError:
            raise ConfigurationError("NaN threshold has to be a float!")
        self.event_schema['properties']['healthStatus']['properties'] = {"nan_ratio": {"type": "number"}}
        self.event_schema['properties']['healthStatus']['required'] = ["nan_ratio"]

    def run(self):
        super().run()
        # create ros topic subscriber
        rospy.init_node(f"{self.component}_{self.config_params.name}", disable_signals=True)
        self._subscriber = rospy.Subscriber(self.ros_topic, PointCloud2, self.callback)
        self.logger.info(f"subsribed to ros topic {self.ros_topic}")

    def callback(self, data):
        gen = point_cloud2.read_points(data, field_names=("x", "y", "z"))  # for yelding the errors
        # gen = point_cloud2.read_points(data, field_names=("x", "y", "z"), skip_nans=True) # smart getting rid of NaNs
        pointcloud = np.array(list(gen))
        nan_ratio = self.nan_ratio(pointcloud)
        self.healthstatus['nan_ratio'] = nan_ratio
        self.publish_status()

    def nan_ratio(self, pointcloud):
        nans_counts_in_each_row = np.count_nonzero(np.isnan(pointcloud), axis=1)
        nans_count = np.count_nonzero(nans_counts_in_each_row)
        return nans_count/pointcloud.shape[0]