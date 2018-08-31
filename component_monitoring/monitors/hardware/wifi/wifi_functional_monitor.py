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
        first_interface = self.wifi_values[0]
        status_msg['healthStatus']["wifi_quality"] =  first_interface["quality"]
        status_msg['healthStatus']["wifi_strength"] = first_interface["strength"]
        return status_msg

    '''
    Returns : a tuple of dictionaries where each dictionary object has 3 items
                name : string of length less than 9 char
                quality : float between 0.0 and 100.0
                strength : int between -30 and -90

    Calculates the quality of the wifi signal percentage and signal strength (in dbm)
    from "iwconfig" shell command
    '''
    def get_wifi_strength(self) :
        output = subprocess.Popen("iwconfig",  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()
        quality_lines = []
        output = output.split("\n")
        name = ""
        names = []
        for line in output :
            if line[:9] != "         " :
                name = line[:9]
            if "Link Quality" in line :
                quality_lines.append(line)
                names.append(name)
        if len(quality_lines) == 0 :
            return ({"name":"", "quality":0.0, "strength":-90})
        '''
        example of a single quality_line
        quality_line = "Link Quality=68/70  Signal level=-42 dBm"
        '''
        answer = []
        for i in range(len(names)) :
            name = names[i]
            quality_line = quality_lines[i]
            quality = quality_line.split()[1].split("=")[1]
            actual, total = map(float, quality.split("/"))
            quality_percent = (actual*100)/total
            signal_strength = quality_line.split()[3].split("=")[1]
            signal_strength_int = int(signal_strength)
            interface = {}
            interface["name"] = name.strip()
            interface["quality"] = quality_percent
            interface["strength"] = signal_strength_int
            answer.append(interface)
        return tuple(answer)

