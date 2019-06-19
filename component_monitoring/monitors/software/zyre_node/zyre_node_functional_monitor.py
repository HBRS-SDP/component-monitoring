import os
from component_monitoring.monitor_base import MonitorBase
from ropod.pyre_communicator.base_class import RopodPyre

class ZyreNodeFunctionalMonitor(MonitorBase, RopodPyre):
    def __init__(self, config_params, black_box_comm):
        MonitorBase.__init__(self, config_params, black_box_comm)
        RopodPyre.__init__(self, 'zyre_node_functional_monitor', ['ROPOD', 'MONITOR'], [])
        robot_id = os.environ.get('ROPOD_ID', 'ropod_001')
        try:
            self.ropod_id = robot_id.split('_')[1]
        except Exception as e:
            self.ropod_id = '001'
        self.lookup_dict = {}
        for mapping in config_params.mappings:
            self.lookup_dict[mapping.inputs[0].replace('ROPODID', self.ropod_id)] \
                    = mapping.outputs[0].name
        self.start()

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()

        zyre_nodes = list(self.peer_directory.values())
        overall_status = True
        for zyre_node_name in self.lookup_dict:
            if zyre_node_name in zyre_nodes:
                status_msg["healthStatus"][self.lookup_dict[zyre_node_name]] = True
            else:
                status_msg["healthStatus"][self.lookup_dict[zyre_node_name]] = False
                overall_status = False
        status_msg["healthStatus"]["status"] = overall_status
        return status_msg

    def stop_monitor(self):
        self.shutdown()
