#!/usr/bin/env python
from __future__ import print_function
import sys
from os import mkdir
from os.path import join

def print_usage():
    print('Usage: add_monitors.py component_monitoring_dir host_name ' + \
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
    monitor_config_file.write('component_name: ' + component_name + '\n')
    monitor_config_file.write('modes: [')
    for i in range(len(mode_names)-1):
        monitor_config_file.write(component_name + '/' + mode_names[i] + ', ')
    monitor_config_file.write(component_name + '/' + mode_names[-1])
    monitor_config_file.write(']\n')
    monitor_config_file.write('dependencies: []\n')
    monitor_config_file.close()

def create_mode_config_file(mode_config_dir, component_name, mode_name):
    config_file = open(join(mode_config_dir, mode_name + '.yaml'), 'w')
    config_file.write('name: ' + component_name + '_' + mode_name + '_monitor\n')
    config_file.write('mappings:\n')
    config_file.write('    - mapping:\n')
    config_file.write('        inputs: []\n')
    config_file.write('        outputs:\n')
    config_file.write('            - output:\n')
    config_file.write('                name: \n')
    config_file.write('                type:\n')
    config_file.close()

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
