from os import listdir
from os.path import join, isfile
from typing import List

import yaml

from component_monitoring.config.config_file_reader import ComponentMonitorConfigFileReader
from component_monitoring.config.config_params import ComponentMonitorConfig


class ConfigUtils(object):
    # a dictionary of configuration parameters for the component monitoring application
    config_data = None

    # a list of component_monitoring.config.config_params.ComponentMonitorConfig
    # objects representing the configurations of all hardware monitors
    hw_monitor_config_params = []

    # a list of component_monitoring.config.config_params.ComponentMonitorConfig
    # objects representing the configuration of all software monitors
    sw_monitor_config_params = []

    @staticmethod
    def read_config(config_file_path):
        '''Reads a YAML configuration file containing parameters for the
        component monitoring application and returns a dictionary with the
        file contents.

        Keyword arguments:
        config_file_path: str -- path to a YAML configuration file of the component
                                 monitoring application

        '''
        config_data = {}
        with open(config_file_path, 'r') as config_file:
            config_data = yaml.safe_load(config_file)
        return config_data

    @staticmethod
    def get_config_params(monitor_config_dir, config_file=None) -> List[ComponentMonitorConfig]:
        '''Returns a list of component_monitoring.config.config_params.ComponentMonitorConfig
        objects representing the configuration of the monitors specified
        in the given directory.

        Keyword arguments:
        monitor_config_dir: str -- a directory containing component monitor
                                   configuration files

        '''
        monitor_config_params = []
        if config_file:
            print('Reading parameters of monitor {0}'.format(config_file))
            component_config_params = ComponentMonitorConfigFileReader.load(monitor_config_dir,
                                                                            config_file)
            monitor_config_params.append(component_config_params)
            return monitor_config_params
        config_files = ConfigUtils.get_file_names_in_dir(monitor_config_dir)
        for config_file in config_files:
            print('Reading parameters of monitor {0}'.format(config_file))
            component_config_params = ComponentMonitorConfigFileReader.load(monitor_config_dir,
                                                                            config_file)
            monitor_config_params.append(component_config_params)
        return monitor_config_params

    @staticmethod
    def get_file_names_in_dir(dir_name):
        '''Returns a list file names in the given directory.

        Keyword arguments:
        dir_name: str -- directory name

        '''
        file_names = list()
        for f_name in listdir(dir_name):
            f_path = join(dir_name, f_name)
            if isfile(f_path):
                file_names.append(f_name)
        return file_names

    @staticmethod
    def get_component_dependencies(component_name):
        '''Returns a list with names of the components on which
        the given component depends.

        Raises a ValueError if the given component is unknown.

        Keyword arguments:
        component_name: str -- name of a component

        '''
        component_config = ConfigUtils.get_component_config(component_name)
        if not component_config:
            raise ValueError('[get_component_dependencies] Unknown component {0}'.format(component_name))
        return component_config.component_dependencies

    @staticmethod
    def get_component_config(component_name):
        '''Returns a component_monitoring.config.config_params.ComponentMonitorConfig
        object representing the

        Raises a ValueError if either "ConfigUtils.hw_monitor_config_params" or
        "ConfigUtils.sw_monitor_config_params" is None.

        Keyword arguments:
        component_name: str -- name of a component

        '''
        component_config = None

        if not ConfigUtils.hw_monitor_config_params or not ConfigUtils.sw_monitor_config_params:
            raise AssertionError('ConfigUtils parameters not set')

        # we look for the component in the hardware components
        for config in ConfigUtils.hw_monitor_config_params:
            if config.component_name == component_name:
                component_config = config
                break

        if component_config:
            return component_config

        # if the component could not be found in the hardware components,
        # we look for it in the software components
        for config in ConfigUtils.sw_monitor_config_params:
            if config.component_name == component_name:
                component_config = config
                break
        return component_config
