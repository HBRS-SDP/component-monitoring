from __future__ import print_function
import subprocess

from component_monitoring.monitor_base import MonitorBase

class WifiFunctionalMonitor(MonitorBase):
    def __init__(self, config_params):
        super(WifiFunctionalMonitor, self).__init__(config_params)
        self.output_names = list()
        for output in config_params.mappings[0].outputs:
            self.output_names.append(output.name)

    def get_status(self):
        status_msg = self.get_status_message_template()
        status_msg['monitorName'] = self.config_params.name
        status_msg['healthStatus'] = dict()
        self.wifi_values = self.get_wifi_strength()
        for i, output_name in enumerate(self.output_names):
            status_msg['healthStatus'][output_name] = self.wifi_values[i]
        return status_msg

    '''
    Returns : a tuple (float, int) where
                float is between 0.0 and 100.0
                int is generally negative

    Calculates the quality of the wifi signal percentage and signal strength 
    from "iwconfig" shell command
    Assumes linux OS
    '''
    def get_wifi_strength(self) :
        output = subprocess.Popen("iwconfig",  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.readlines()
        quality_line = 0
        for line in output :
            if "Link Quality" in line :
                quality_line = line
                break
        if quality_line == 0 :
            return 0.0
        '''
        example of quality_line
        quality_line = "Link Quality=68/70  Signal level=-42 dBm"
        '''
        quality = quality_line.split()[1].split("=")[1]
        actual, total = map(float, quality.split("/"))
        quality_percent = (actual*100)/total
        signal_strength = quality_line.split()[3].split("=")[1]
        signal_strength_int = int(signal_strength)
        return (quality_percent, signal_strength_int)

