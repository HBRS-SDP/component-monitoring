import subprocess
from component_monitoring.monitor_base import MonitorBase

class SystemdServicesActiveMonitor(MonitorBase):
    def __init__(self, config_params):
        super(SystemdServicesActiveMonitor, self).__init__(config_params)
        self.service_names = list()
        self.service_statuses = dict()
        self.status_name = self.status_name = config_params.mappings[0].outputs[0].name
        for service in config_params.mappings[0].inputs:
            self.service_names.append(service)
            self.service_statuses[service] = False

    def get_status(self):
        self.__update_service_statuses()

        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        status_msg['healthStatus'] = dict()
        for service in self.service_names:
            status_msg['healthStatus'][service] = dict()
            status_msg['healthStatus'][service][self.status_name] = self.service_statuses[service]

        status = True
        if len(self.service_statuses.values()) == 0 or False in self.service_statuses.values():
            status = False
        status_msg['healthStatus']['status'] = status
        return status_msg

    def __update_service_statuses(self):
        '''Updates self.service_statuses based on whether the services are active
        '''
        for service in self.service_names:
            status_code = subprocess.call(['systemctl', 'status', service],
                                          stdout=subprocess.DEVNULL)
            # Systemd status codes are documented on the following page:
            # https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8;
            # a status code equal to 0 means that the service is active
            self.service_statuses[service] = (status_code == 0)
