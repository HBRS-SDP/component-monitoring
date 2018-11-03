import subprocess
from component_monitoring.monitor_base import MonitorBase

class SystemdServicesActiveMonitor(MonitorBase):
    def __init__(self, config_params):
        super(SystemdServicesActiveMonitor, self).__init__(config_params)
        self.service_names = list()
        self.service_statuses = dict()
        self.status_names = dict()
        for mapping in config_params.mappings:
            service = mapping.inputs[0]
            self.service_names.append(service)
            self.service_statuses[service] = False
            self.status_names[service] = mapping.outputs[0].name
        self.status_msg = self.__init_status_msg()

    def get_status(self):
        overall_status = True
        for service in self.service_names:
            service_active = self.__service_active(service)
            self.status_msg['healthStatus'][self.status_names[service]] = service_active
            if not service_active:
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
        for service in self.service_names:
            status_msg['healthStatus'][self.status_names[service]] = False
        status_msg['healthStatus']['status'] = False
        return status_msg

    def __service_active(self, service):
        '''Checks whether the given service is active or not
        '''
        status_code = subprocess.call(['systemctl', 'status', service],
                                      stdout=subprocess.DEVNULL)
        # Systemd status codes are documented on the following page:
        # https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8;
        # a status code equal to 0 means that the service is active
        return status_code == 0
