from abc import abstractmethod

class MonitorBase(object):
    def __init__(self, config_params, black_box_comm):
        self.config_params = config_params
        self.black_box_comm = black_box_comm

    @abstractmethod
    def get_status(self):
        pass

    def stop(self):
        pass

    def get_status_message_template(self):
        msg = dict()
        return msg
