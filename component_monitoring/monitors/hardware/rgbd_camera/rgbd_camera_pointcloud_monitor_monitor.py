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
        self._nans_threshold_ratio = 0.65 # arbitrary chosen threshold
        self._pointcloud = None
        self._status = True # monitor thinks that the component is healthy

    def callback(self, data):
        gen = point_cloud2.read_points(data, field_names=("x", "y", "z"))
        self._pointcloud = np.array(list(gen))

    def pointcloud_rejection_policy(self, pointcloud):
        nans_counts_in_each_row = np.count_nonzero(np.isnan(pointcloud), axis=1)
        nans_count = np.count_nonzero(nans_counts_in_each_row)

        if nans_count > pointcloud.shape[0]*self._nans_threshold_ratio:
            return True
        return False

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
                 

        if not self._pointcloud is None:
            self._status = True

            rospy.loginfo("Poincloud from component received.")
            
            if self.pointcloud_rejection_policy(self._pointcloud):
                self._status = False

                event['healthStatus']['nans'] = True
                rospy.logwarn("Number of NaN values in the pointcloud exceede a threshold of {}.".
                format(int(self._nans_threshold_ratio*self._pointcloud.shape[0])))
                
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
        
        else:
            self._status = False
            rospy.logwarn("No poincloud from component received.")

        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = self._status

        return status_msg
