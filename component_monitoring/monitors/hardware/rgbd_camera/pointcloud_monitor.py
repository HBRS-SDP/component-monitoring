import signal
import uuid

import numpy as np
import rospy
from kafka.consumer.fetcher import ConsumerRecord
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud2

from component_monitoring.config.config_params import MonitorModeConfig, OutputConfig
from component_monitoring.messaging.enums import MessageType, Response
from component_monitoring.monitor_base import MonitorBase
from component_monitoring.monitor_exception import ConfigurationError


class PointcloudMonitor(MonitorBase):
    """
    Pointcloud monitor, implementing monitoring for the pointcloud produced by the head camera of a Toyota HSR robot
    """

    def __init__(self, component_name: str, dialogue_id: str, config_params: MonitorModeConfig, server_address: str,
                 control_channel: str):
        super(PointcloudMonitor, self).__init__(component_name, dialogue_id, config_params, server_address,
                                                control_channel)
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
        if self.status_type in ["float", "int", "double", "long"]:
            self.status_schema_type = "number"
        self.event_schema['properties']['healthStatus']['properties'] = {
            self.status_name: {"type": self.status_schema_type}}
        self.event_schema['properties']['healthStatus']['required'] = [self.status_name]

        self.pending_requests = dict()

    def run(self) -> None:
        """
        Entry point of the Pointcloud Monitor
        @return: None
        """
        super().run()
        # create ros topic subscriber
        rospy.init_node(f"{self.component}_{self.config_params.name}", disable_signals=True)
        self._subscriber = rospy.Subscriber(self.ros_topic, PointCloud2, self.callback)
        self.logger.info(f"subsribed to ros topic {self.ros_topic}")
        for msg in self.consumer:
            msg: ConsumerRecord
            if msg.topic == self.control_topic:
                self.logger.info(f"Processing {msg}")
                message = self.deserialize(msg)
                if self.validate_request(message):
                    request_type = self.get_message_type(message)
                    self.logger.error(self._id)
                    self.logger.error(message['To'])
                    self.logger.error(request_type == MessageType.UPDATE)
                    if self._id == message['To'] and request_type == MessageType.UPDATE:
                        self.logger.error("1111111111111111111111111111")
                        update = message[request_type.value]
                        if update['Params']['Store']:
                            dialogue_id = message['Id']
                            self.pending_requests[dialogue_id] = (
                                Response.OKAY, message['From'], (Response.OKAY, None))
                            self.send_start(dialogue_id, "storage_manager", None)
                elif self.validate_response(message):
                    dialogue_id = message['Id']
                    if self._id == message['To'] and dialogue_id in self.pending_requests:
                        if self.pending_requests[dialogue_id][0] == Response(message['Response']['Code']):
                            self.send_response(dialogue_id, self.pending_requests[dialogue_id][1],
                                               *self.pending_requests[dialogue_id][2])
                else:
                    self.logger.warning("Request could not be validated!")
                    self.logger.warning(msg)
                    continue

    def callback(self, data) -> None:
        """
        Callback to be executed when a PointCloud2 message was received on the ROS topic

        @param data: message received on ROS topic
        @return: None
        """
        gen = point_cloud2.read_points(data, field_names=("x", "y", "z"))  # for yelding the errors
        # gen = point_cloud2.read_points(data, field_names=("x", "y", "z"), skip_nans=True) # smart getting rid of NaNs
        pointcloud = np.array(list(gen))
        nan_ratio = self.nan_ratio(pointcloud)
        self.healthstatus['nan_ratio'] = nan_ratio
        self.publish_status()

    def nan_ratio(self, pointcloud: np.ndarray) -> float:
        """
        Calculate the ratio of NaNs contained in the given PointCloud

        @param pointcloud: Numpy array containing the PointCloud
        @return: NaN ratio
        """
        nans_counts_in_each_row = np.count_nonzero(np.isnan(pointcloud), axis=1)
        nans_count = np.count_nonzero(nans_counts_in_each_row)
        return nans_count / pointcloud.shape[0]
