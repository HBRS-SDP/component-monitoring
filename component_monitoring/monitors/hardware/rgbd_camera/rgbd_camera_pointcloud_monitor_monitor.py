import json
from io import BytesIO, StringIO

import yaml
import numpy as np

from component_monitoring.monitor_base import MonitorBase
import rospy
from sensor_msgs.msg import PointCloud2
from kafka import KafkaConsumer, KafkaProducer

class RgbdCameraPointcloudMonitorMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        self.topic_name = '/hsrb/monitoring/rgbd'
        self.producer = KafkaProducer(bootstrap_servers='localhost:9092')
        super(RgbdCameraPointcloudMonitorMonitor, self).__init__(config_params, black_box_comm)
        self._subscriber = rospy.Subscriber('/hsrb/head_rgbd_sensor/pointcloud', PointCloud2, self.callback)
        self._pointcloud = None

    def callback(self, data):
        self._pointcloud = np.array(map(lambda x: np.nan if x=='nan' else x, data.data), dtype=np.float)

    def to_cpp(self, msg):
        """
        Serialize ROS messages to string
        :param msg: ROS message to be serialized
        :rtype: str
        """
        buf = StringIO()
        msg.serialize(buf)
        return buf.getvalue()

    def from_cpp(self, serial_msg, cls):
        """
        Deserialize strings to ROS messages
        :param serial_msg: serialized ROS message
        :type serial_msg: str
        :param cls: ROS message class
        :return: deserialized ROS message
        """
        msg = cls()
        return msg.deserialize(serial_msg)

    def get_status(self):
        event = {"monitorName": "rgbd_monitor",
                 "monitorDescription": "Monitor verifying that the pointcloud of the RGBD camera has no NaNs",
                 "healthStatus": {
                     "nans": False
                 }
                 }
        if np.isnan(self._pointcloud).any():
            event['healthStatus']['nans'] = True
            future = self.producer.send(self.topic_name, bytes(json.dumps(event)))
            result = future.get(timeout=60)
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
