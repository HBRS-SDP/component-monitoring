#!/usr/bin/env python
from __future__ import print_function
import sys
import component_monitoring.monitors as monitors
from os import mkdir
from os.path import join, dirname

def print_usage():
    print('Usage: add_monitors.py monitor_config_dir host_name ' + \
                                 'monitor_name component_name mode_names')
    print()
    print('monitor_config_dir     Path to the component monitor config directory')
    print('host_name              Name of the host on which the monitors are running ' + \
                                 '(either robot or black-box)')
    print('monitor_type           Type of monitor (either hardware or software)')
    print('component_name         Name of the component to be monitored')
    print('mode_names             A list of component monitor modes separated by space')

def create_monitor_file(config_dir, component_name, mode_names):
    monitor_config_file = open(join(config_dir, component_name + '_monitor.yaml'), 'w')
    monitor_config_file.write('name: ' + component_name + '_monitor\n')
    monitor_config_file.write('description: ' + component_name + '_monitor\n')
    monitor_config_file.write('component_name: ' + component_name + '\n')
    monitor_config_file.write('modes: [')
    for i in range(len(mode_names)-1):
        monitor_config_file.write(component_name + '/' + mode_names[i] + '.yaml, ')
    monitor_config_file.write(component_name + '/' + mode_names[-1] + '.yaml')
    monitor_config_file.write(']\n')
    monitor_config_file.write('dependencies: []\n')
    monitor_config_file.close()

def create_mode_config_file(mode_config_dir, component_name, mode_name):
    config_file = open(join(mode_config_dir, mode_name + '.yaml'), 'w')
    config_file.write('name: ' + component_name + '_' + mode_name + '_monitor\n')
    config_file.write('description: ' + component_name + '_' + mode_name + '_monitor\n')
    config_file.write('mappings:\n')
    config_file.write('    - mapping:\n')
    config_file.write('        inputs: []\n')
    config_file.write('        outputs:\n')
    config_file.write('            - output:\n')
    config_file.write('                name: \n')
    config_file.write('                type:\n')
    config_file.close()

def create_mode_source_file(monitor_source_dir, component_name, mode_name):
    class_name = component_name.title() + mode_name.title() + 'Monitor'
    source_file_name = component_name + '_' + mode_name + '_monitor.py'

    source_file = open(join(monitor_source_dir, source_file_name), 'w')
    source_file.write('from component_monitoring.monitor_base import MonitorBase\n\n')
    source_file.write('class ' + class_name + '(MonitorBase):\n')
    source_file.write('    def __init__(self, config_params, black_box_comm):\n')
    source_file.write('        super(' + class_name + ', self).__init__(config_params, black_box_comm)\n\n')
    source_file.write('    def get_status(self):\n')
    source_file.write('        status_msg = self.get_status_message_template()\n')
    source_file.write('        status_msg["monitorName"] = self.config_params.name\n')
    source_file.write('        status_msg["monitorDescription"] = self.config_params.description\n')
    source_file.write('        status_msg["healthStatus"] = dict()\n')
    source_file.write('        status_msg["healthStatus"]["status"] = False\n')
    source_file.write('        return status_msg\n')
    source_file.close()

if __name__ == '__main__':
    if '--help' in sys.argv or len(sys.argv) < 6:
        print_usage()
        sys.exit()

    monitor_config_dir = sys.argv[1]
    host_name = sys.argv[2]
    monitor_type = sys.argv[3]
    component_name = sys.argv[4]
    mode_names = sys.argv[5:]

    print('Creating monitor config file')
    type_config_dir = join(monitor_config_dir, host_name, monitor_type)
    create_monitor_file(type_config_dir, component_name, mode_names)

    print('Creating mode config directory')
    mode_config_dir = join(type_config_dir, component_name)
    mkdir(mode_config_dir)
    for mode_name in mode_names:
        print('Creating config file for monitor mode "{0}"'.format(mode_name))
        create_mode_config_file(mode_config_dir, component_name, mode_name)

    print('Creating monitor source package')
    source_dir = dirname(monitors.__file__)
    monitor_source_dir = join(source_dir, monitor_type, component_name)
    mkdir(monitor_source_dir)
    init_file_handle = open(join(monitor_source_dir, '__init__.py'), 'w+')
    init_file_handle.close()
    for mode_name in mode_names:
        print('Creating source file for monitor mode "{0}"'.format(mode_name))
        create_mode_source_file(monitor_source_dir, component_name, mode_name)
