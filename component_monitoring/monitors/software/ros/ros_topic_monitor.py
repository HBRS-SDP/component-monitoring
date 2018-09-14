from __future__ import print_function
import rospy
import rosnode
from rospy.msg import AnyMsg
from multiprocessing import Process, Manager

from component_monitoring.monitor_base import MonitorBase

class RosTopicMonitor(MonitorBase):
    def __init__(self, config_params):
        super(RosTopicMonitor, self).__init__(config_params)
        self.process_manager = Manager()

        self.topic_names = list()
        self.topic_statuses = self.process_manager.dict()
        self.status_name = self.status_name = config_params.mappings[0].outputs[0].name
        self.subscribers = dict()
        for topic in config_params.mappings[0].inputs:
            self.topic_names.append(topic)
            self.topic_statuses[topic] = False
        self.node_initialised = False
        self.node_thread = None

    def get_status(self):
        try:
            rospy.get_master().getPid()
            if not self.node_initialised:
                self.node_thread = Process(target=self.__create_node)
                self.node_thread.start()
                self.node_initialised = True
        except:
            if self.node_initialised:
                rosnode.kill_nodes('ros_topic_monitor')
                self.node_thread.terminate()
            self.node_initialised = False
            for topic in self.topic_names:
                self.topic_statuses[topic] = False

        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        status = True
        for topic in self.topic_names:
            status_msg['healthStatus'][topic] = dict()
            status_msg['healthStatus'][topic][self.status_name] = self.topic_statuses[topic]
            if (not 'published' in self.topic_statuses.keys() or not self.topic_statuses[topic]['published']):
                status = False
        status_msg['healthStatus']['status'] = status

        return status_msg

    def __create_node(self):
        rospy.init_node('ros_topic_monitor', disable_signals=True)
        self.__init_subscribers()
        rospy.spin()

    def __init_subscribers(self):
        for topic in self.topic_names:
            self.subscribers[topic] = rospy.Subscriber(topic, AnyMsg, self.__topic_sub, topic)

    def __topic_sub(self, msg, topic_name):
        global_ns_topic_name = '/' + topic_name
        if (topic_name in self.topic_names) or (global_ns_topic_name in self.topic_names):
            self.topic_statuses[topic_name] = True
