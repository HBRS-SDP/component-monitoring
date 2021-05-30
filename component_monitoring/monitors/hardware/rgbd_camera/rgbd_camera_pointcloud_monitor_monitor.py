import json
from bson import json_util
import yaml

from component_monitoring.monitor_base import MonitorBase
import rospy
from sensor_msgs.msg import PointCloud2
from kafka import KafkaConsumer, KafkaProducer

class RgbdCameraPointcloudMonitorMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        self.producer = KafkaProducer(bootstrap_servers='localhost:9092')
        super(RgbdCameraPointcloudMonitorMonitor, self).__init__(config_params, black_box_comm)
        self._subscriber = rospy.Subscriber('/hsrb/head_rgbd_sensor/pointcloud', PointCloud2, self.callback)
        self._pointcloud = None

    def msg2json(self, msg):
        ''' Convert a ROS message to JSON format'''
        y = yaml.load(str(msg))
        return json.dumps(y, indent=4)

    def callback(self, data):
        self._pointcloud = data.data

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = False

        message = json.dumps(status_msg)
        
        future = self.producer.send('hsrb_monitoring_rgbd', json.dumps(message, default=json_util.default).encode('utf-8'))
        result = future.get(timeout=60)

        if self._pointcloud is not None:
            rospy.loginfo("I got poincloud!")
        else:
            rospy.logwarn("Oh no I have no poincloud :-( .")
        return status_msg
