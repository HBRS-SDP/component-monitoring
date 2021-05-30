import json
from bson import json_util
from io import BytesIO, StringIO
import yaml
import numpy as np
from sensor_msgs import point_cloud2
from component_monitoring.monitor_base import MonitorBase
import rospy
from sensor_msgs.msg import PointCloud2
from kafka import KafkaConsumer, KafkaProducer

class RgbdCameraPointcloudMonitorMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        self.topic_name = 'hsrb_monitoring_rgbd'
        self.producer = KafkaProducer(bootstrap_servers='localhost:9092')
        super(RgbdCameraPointcloudMonitorMonitor, self).__init__(config_params, black_box_comm)
        self._subscriber = rospy.Subscriber('/hsrb/head_rgbd_sensor/pointcloud', PointCloud2, self.callback)
        self._pointcloud = None

    def callback(self, data):
        gen = point_cloud2.read_points(data, field_names=("x", "y", "z")) # for yelding the errors
        #gen = point_cloud2.read_points(data, field_names=("x", "y", "z"), skip_nans=True) # smart getting rid of NaNs
        self._pointcloud = list(gen)

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
        if self._pointcloud:
            if np.isnan(np.array(self._pointcloud)).any():
                event['healthStatus']['nans'] = True
                rospy.logwarn("Detected NaN values in the pointcloud.")
                future = self.producer.send(self.topic_name, 
                                            json.dumps(event, 
                                            default=json_util.default).encode('utf-8'))
                result = future.get(timeout=60)
            else:
                rospy.loginfo("Correct values in the pointcloud.")
                event['healthStatus']['nans'] = False
                future = self.producer.send(self.topic_name, 
                                            json.dumps(event,
                                            default=json_util.default).encode('utf-8'))
                result = future.get(timeout=60)

        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = False
        if self._pointcloud is not None:
            rospy.loginfo("Poincloud from component received.")
        else:
            rospy.logwarn("No poincloud from component received.")
        return status_msg
