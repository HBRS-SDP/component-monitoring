from component_monitoring.monitor_base import MonitorBase
import numpy as np
import time
import threading
import rospy
import geometry_msgs.msg
from ropod_ros_msgs.srv import ToggleObjectPublisher

class CartAttachmentVisual3DMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(CartAttachmentVisual3DMonitor, self).__init__(config_params, black_box_comm)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)

        self.cart_pose_topic_name = config_params.arguments.get('cart_pose_topic_name', '/cart_plane_detector/plane_pose')
        self.cart_attached_param_name = config_params.arguments.get('cart_attached_param_name',
                                                            '/manuever_navigation/is_load_attached')
        self.toggle_publisher_srv_name = config_params.arguments.get('toggle_publisher_srv_name', '/cart_plane_detector/toggle_object_publisher')
        self.nominal_plane_distance = config_params.arguments.get('nominal_plane_distance', 0.55)
        self.plane_distance_tolerance = config_params.arguments.get('plane_distance_tolerance', 0.05)
        self.cart_state = dict()
        self.cart_state['cart_pose'] = None
        self.cart_state['last_received_time'] = time.time()
        self.node_initialised = False

    def get_status(self):
        try:
            rospy.get_master().getPid()
            if not self.node_initialised:
                self.node_thread = threading.Thread(target=self.__create_node)
                self.node_thread.start()
                self.node_initialised = True
                time.sleep(2.0)
        except:
            if self.node_initialised:
                self.node_thread.terminate()
            self.node_initialised = False

        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status, output = self._get_cart_status()
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = status
        status_msg["healthStatus"][self.output_names[0]] = output
        return status_msg

    def __create_node(self):
        self.__init_subscribers()
        loop_rate = rospy.Rate(2.0)
        while not rospy.is_shutdown():
            loop_rate.sleep()


    def __init_subscribers(self):
        self.cart_pose_sub = rospy.Subscriber(self.cart_pose_topic_name, geometry_msgs.msg.PoseStamped, self.pose_callback)
        self.toggle_cart_publisher_client = rospy.ServiceProxy(self.toggle_publisher_srv_name, ToggleObjectPublisher)
        self.toggle_cart_publisher_client(enable_publisher=True)

    def pose_callback(self, msg):
        self.cart_state['cart_pose'] = msg.pose
        self.cart_state['last_received_time'] = time.time()

    def _get_cart_status(self):
        """
        If cart is not supposed to be attached, returns True
        If cart is supposed to be attached, checks last known distance of cart and
        returns True if cart is within threshold
        :returns: (bool, bool)

        """
        is_cart_attached = False
        try:
            rospy.get_master().getPid()
            is_cart_attached = rospy.get_param(self.cart_attached_param_name, False)
        except:
            print('[cart_attachment_visual_3d_monitor] ROS master not running')


        if not is_cart_attached:
            return True, True

        if self.cart_state['cart_pose'] is None or \
           (time.time() - self.cart_state['last_received_time']) > 10.0:
            self.toggle_cart_publisher_client = rospy.ServiceProxy(self.toggle_publisher_srv_name, ToggleObjectPublisher)
            self.toggle_cart_publisher_client(enable_publisher=True)
            return False, False

        dist = np.linalg.norm([self.cart_state['cart_pose'].position.x, self.cart_state['cart_pose'].position.y])
        if (dist < self.nominal_plane_distance + self.plane_distance_tolerance and
            dist > self.nominal_plane_distance - self.plane_distance_tolerance):
            return True, True
        else:
            return False, False
