from __future__ import print_function
import rospy
import rosnode

from component_monitoring.monitor_base import MonitorBase

class RosNodeMonitor(MonitorBase):
    def __init__(self, config_params):
        super(RosNodeMonitor, self).__init__(config_params)

        self.node_names = list()
        self.node_statuses = dict()
        self.status_names = dict()
        for mapping in config_params.mappings:
            node = mapping.inputs[0]
            self.node_names.append(node)
            self.node_statuses[node] = False
            self.status_names[node] = mapping.outputs[0].name

        self.status_msg = self.__init_status_msg()

    def __init_status_msg(self):
        '''Initialises a status message dictionary so that it doesn't have to
        be recreated every time the status is requested
        '''
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        status_msg['healthStatus'] = dict()
        for node in self.node_names:
            status_msg['healthStatus'][self.status_names[node]] = False
        status_msg['healthStatus']['status'] = True
        return status_msg

    def get_status(self):
        self.update_statuses()
        for node in self.node_names:
            self.status_msg['healthStatus'][self.status_names[node]] = self.node_statuses[node]
        self.status_msg['healthStatus']['status'] = False not in self.node_statuses.values()
        return self.status_msg

    def update_statuses(self):
        """Update node_statuses dictionary

        :returns: None

        """
        # if ros master is not running then set false to all nodes
        master_running = True
        try:
            rospy.get_master().getPid()
        except:
            master_running = False
        if not master_running:
            for node in self.node_names:
                self.node_statuses[node] = False
            return

        active_nodes = rosnode.get_node_names()
        for node in self.node_names:
            self.node_statuses[node] = '/'+node in active_nodes
