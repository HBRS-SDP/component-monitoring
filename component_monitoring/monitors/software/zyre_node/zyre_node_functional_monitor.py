from component_monitoring.monitor_base import MonitorBase
from ropod.pyre_communicator.base_class import RopodPyre

class ZyreNodeFunctionalMonitor(MonitorBase, RopodPyre):
    def __init__(self, config_params, black_box_comm):
        MonitorBase.__init__(self, config_params, black_box_comm)
        RopodPyre.__init__(self, 'zyre_node_functional_monitor', ['ROPOD', 'MONITOR'], [])
        self.mappings = config_params.mappings
        print(self.mappings)
        self.start()

    def get_status(self):
        print(self.peer_directory)
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = False
        return status_msg
