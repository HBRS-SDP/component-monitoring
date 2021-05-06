from component_monitoring.monitor_base import MonitorBase
import subprocess

class DockerContainerMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(DockerContainerMonitor, self).__init__(config_params, black_box_comm)

        self.image_names = list()
        self.image_statuses = dict()
        self.status_names = dict()
        for mapping in config_params.mappings:
            image = mapping.inputs[0]
            self.image_names.append(image)
            self.image_statuses[image] = False
            self.status_names[image] = mapping.outputs[0].name
        self.status_msg = self.__init_status_msg()

    def __init_status_msg(self):
        '''
        Initialises a status message dictionary so that it doesn't have to
        be recreated every time the status is requested
        '''
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['monitorDescription'] = self.config_params.description
        status_msg['healthStatus'] = dict()
        for image in self.image_names:
            status_msg['healthStatus'][self.status_names[image]] = False
        status_msg['healthStatus']['status'] = False
        return status_msg

    def get_status(self):
        self.update_statuses()
        for image in self.image_names:
            self.status_msg['healthStatus'][self.status_names[image]] = self.image_statuses[image]
        if False not in self.image_statuses.values():
            self.status_msg['healthStatus']['status'] = True
        return self.status_msg

    def update_statuses(self):
        '''
        The output of docker ps is as follows:
        CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                  NAMES
        353221f6972f        overpass:latest     "/usr/local/sbin/doc…"   36 minutes ago      Up 36 minutes       0.0.0.0:8000->80/tcp   hopeful_jones

        We extract the image names, and compare them to the set of docker images we expect to be running as containers
        '''
        # for k in self.image_statuses.keys():
        #     self.image_statuses[k] = False

        # output = subprocess.check_output(["docker", "ps"]).splitlines()
        # if len(output) < 2: # only header is printed; i.e. no containers running
        #     return

        # image_list = output[1:] # remove header
        # for i in image_list:
        #     fields = i.split()
        #     img_name = fields[1].decode('utf-8') # get the second field (i.e. image name)
        #     if img_name in self.image_names:
        #         self.image_statuses[img_name] = True
        # return
        return
