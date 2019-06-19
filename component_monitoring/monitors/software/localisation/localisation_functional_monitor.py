from component_monitoring.monitor_base import MonitorBase
from black_box_tools.data_utils import DataUtils

class LocalisationFunctionalMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(LocalisationFunctionalMonitor, self).__init__(config_params, black_box_comm)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)

        self.avg_variance_threshold = config_params.arguments.get('avg_variance_threshold', 0.01)
        self.bb_variable_name = config_params.arguments.get('bb_variable_name',
                                                                 'ros_amcl_pose/pose/covariance')

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        status, *output = self._get_localisation_avg_variance()
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = status
        for i, output_name in enumerate(self.output_names):
            status_msg["healthStatus"][output_name] = output[i]
        return status_msg

    def _get_localisation_avg_variance(self):
        """Provide a localisation average variance along with status after querying
        black box.
        :returns: (bool, float, float, float, bool)

        """
        dict_msg = self.black_box_comm.send_latest_data_query([self.bb_variable_name])
        if not dict_msg:
            return (False, 0.0, 0.0, 0.0, False)

        _, data = DataUtils.parse_bb_latest_data_msg(dict_msg)
        if not data or not data[0]:
            return (False, 0.0, 0.0, 0.0, False)
        covariance_matrix = data[0][1]
        avg_variance = (covariance_matrix[0] + covariance_matrix[7] + covariance_matrix[35])/3.0
        return (True, covariance_matrix[0], covariance_matrix[7],
                covariance_matrix[35], avg_variance<self.avg_variance_threshold)
