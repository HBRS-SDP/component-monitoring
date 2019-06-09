#!/usr/bin/env python3
from os.path import abspath, dirname, join
from typing import Sequence
import networkx as nx
import matplotlib.pyplot as plt

from component_monitoring.config.config_params import ComponentMonitorConfig
from component_monitoring.config.config_utils import ConfigUtils

class ComponentNetwork(object):
    '''
    @author Alex Mitrevski
    @contact aleksandar.mitrevski@h-brs.de
    '''
    def __init__(self, config_file_path: str, root_dir: str):
        '''Keyword arguments:

        config_file_path -- path to a configuration file for the component monitoring application
        root_dir -- root directory of the component monitoring application

        '''
        self.root_dir = root_dir
        self.config_data = ConfigUtils.read_config(config_file_path)
        self.network = self.__create_network()

    def __create_network(self) -> nx.DiGraph:
        '''Creates a directed networkx graph in which the nodes represent components
        and the edges represent dependencies between the components (an arrow from
        component A to component B signifies that A depends on B).

        The resulting graph combines both hardware and software components.
        '''
        # we get a network of the hardware components
        hw_monitor_config_dir = self.config_data['config_dirs']['hardware']
        hw_component_config = self.__get_monitor_config(join(self.root_dir,
                                                             hw_monitor_config_dir))
        hw_component_network = self.__get_component_graph(hw_component_config)

        # we get a network of the software components
        sw_monitor_config_dir = self.config_data['config_dirs']['software']
        sw_component_config = self.__get_monitor_config(join(self.root_dir,
                                                             sw_monitor_config_dir))
        sw_component_network = self.__get_component_graph(sw_component_config)

        # the two networks are finally composed
        network = nx.compose(hw_component_network, sw_component_network)
        return network

    def __get_monitor_config(self, config_dir: str) -> Sequence[ComponentMonitorConfig]:
        '''Reads all component configuration parameters from the given config directory.

        Keyword arguments:
        config_dir -- absolute path to a component configuration directory

        '''
        monitor_config_params = ConfigUtils.get_config_params(config_dir)
        return monitor_config_params

    def __get_component_graph(self, component_config: Sequence[ComponentMonitorConfig]) -> nx.DiGraph:
        '''Creates a directed networkx graph from the given configuration parameters,
        such that the graph nodes represent components and the edges represent
        dependencies between the components (an arrow from component A to component B
        means that A depends on B).
        '''
        network = nx.DiGraph()
        for component in component_config:
            network.add_node(component.component_name)
            for dependency in component.component_dependencies:
                network.add_edge(component.component_name, dependency)
        return network

if __name__ == '__main__':
    util_dir = abspath(dirname(__file__))
    package_dir = dirname(util_dir)
    root_dir = dirname(package_dir)

    config_file = join(root_dir, 'config/component_monitoring_config.yaml')
    component_network = ComponentNetwork(config_file, root_dir)
    nx.draw_planar(component_network.network, with_labels=True)
    plt.show()
