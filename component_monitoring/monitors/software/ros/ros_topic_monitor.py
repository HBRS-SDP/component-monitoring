from __future__ import print_function
import rospy
import rosnode
from rospy.msg import AnyMsg
import threading

from component_monitoring.monitor_base import MonitorBase

class RosTopicMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(RosTopicMonitor, self).__init__(config_params, black_box_comm)

        self.topic_names = list()
        self.topic_statuses = dict()
        self.status_names = dict()
        self.subscribers = dict()
        for mapping in config_params.mappings:
            topic = mapping.inputs[0]
            self.topic_names.append(topic)
            self.topic_statuses[topic] = False
            self.status_names[topic] = mapping.outputs[0].name

        self.node_initialised = False
        self.node_thread = None
        self.status_msg = self.__init_status_msg()

    def get_status(self):
        try:
            rospy.get_master().getPid()
            if not self.node_initialised:
                self.node_thread = Thread(target=self.__create_node)
                self.node_thread.start()
                self.node_initialised = True
        except:
            if self.node_initialised:
                self.node_thread.terminate()
            self.node_initialised = False
            for topic in self.topic_names:
                self.topic_statuses[topic] = False

        overall_status = True
        for topic in self.topic_names:
            self.status_msg['healthStatus'][topic] = dict()
            self.status_msg['healthStatus'][self.status_names[topic]] = self.topic_statuses[topic]
            if not self.topic_statuses[topic]:
                overall_status = False
        self.status_msg['healthStatus']['status'] = overall_status
        return self.status_msg

    def __init_status_msg(self):
        '''Initialises a status message dictionary so that it doesn't have to
        be recreated every time the status is requested
        '''
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        status_msg['healthStatus'] = dict()
        for topic in self.topic_names:
            status_msg['healthStatus'][self.status_names[topic]] = False
        status_msg['healthStatus']['status'] = False
        return status_msg

    def __create_node(self):
        self.__init_subscribers()
        rospy.spin()

    def __init_subscribers(self):
        for topic in self.topic_names:
            self.subscribers[topic] = rospy.Subscriber(topic, AnyMsg, self.__topic_sub, topic)

    def __topic_sub(self, msg, topic_name):
        global_ns_topic_name = '/' + topic_name
        if (topic_name in self.topic_names) or (global_ns_topic_name in self.topic_names):
            self.topic_statuses[topic_name] = True
