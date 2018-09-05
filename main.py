#!/usr/bin/env python
from __future__ import print_function
from os import listdir
from os.path import join, isfile
from time import sleep

from component_monitoring.config.config_file_reader import ComponentMonitorConfigFileReader
from component_monitoring.monitor_manager import MonitorManager

def get_files(dir_name):
    file_names = list()
    for f_name in listdir(dir_name):
        f_path = join(dir_name, f_name)
        if isfile(f_path):
            file_names.append(f_name)
    return file_names

if __name__ == '__main__':
    hw_monitor_config_dir_name = 'component_monitoring/monitor_config/hardware'
    sw_monitor_config_dir_name = 'component_monitoring/monitor_config/software'

    hw_config_files = get_files(hw_monitor_config_dir_name)
    hw_monitor_config_params = list()
    for config_file in hw_config_files:
        print('Reading parameters of hardware monitor {0}'.format(config_file))
        component_config_params = ComponentMonitorConfigFileReader.load(hw_monitor_config_dir_name,
                                                                        config_file)
        hw_monitor_config_params.append(component_config_params)

    sw_config_files = get_files(sw_monitor_config_dir_name)
    sw_monitor_config_params = list()
    for config_file in sw_config_files:
        print('Reading parameters of software monitor {0}'.format(config_file))
        component_config_params = ComponentMonitorConfigFileReader.load(sw_monitor_config_dir_name,
                                                                        config_file)
        sw_monitor_config_params.append(component_config_params)

    monitor_manager = MonitorManager(hw_monitor_config_params, sw_monitor_config_params)
    try:
        while True:
            monitor_manager.monitor_components()
            sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        print('Component monitors exiting')

    ### debugging printout
    # hardware_monitor_config_params = ComponentMonitorConfigFileReader.load(hw_monitor_config_dir_name,
    #                                                                          "laser_monitor.yaml");
    # print('Monitor name: {0}'.format(hardware_monitor_config_params.name))
    # for mode_params in hardware_monitor_config_params.modes:
    #     print('    Mode name: {0}'.format(mode_params.name))
    #     for fn_mapping_params in mode_params.mappings:
    #         print('    Inputs:\n')
    #         for monitor_input in fn_mapping_params.inputs:
    #             print('        {0}'.format(monitor_input))
    #
    #         print('    Outputs:\n')
    #         for monitor_output in fn_mapping_params.outputs:
    #             print('        {0}'.format(monitor_output.name))
    #             print('        {0}'.format(monitor_output.obtained_value_type))
    #             print('        {0}'.format(monitor_output.expected_value))
    #     print()
