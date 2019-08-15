from typing import Dict

import os
import time
import subprocess
import threading
import yaml
import networkx as nx
import pymongo as pm

from component_monitoring.config.config_params import ComponentRecoveryConfig

class RecoveryManager(object):
    def __init__(self, recovery_config_file: str, component_network: nx.DiGraph,
                 robot_store_db_name='robot_store',
                 robot_store_db_port=27017,
                 robot_store_status_collection='status'):
        if not 'COMPONENT_MONITORING_ROOT' in os.environ:
            raise AssertionError('The COMPONENT_MONITORING_ROOT environment variable has to be set to the path of the component monitoring application')

        self.component_network = component_network

        config_abs_path = os.path.join(os.environ['COMPONENT_MONITORING_ROOT'], recovery_config_file)
        self.config_params_map = self.__read_config_file(config_abs_path)

        self.db_name = robot_store_db_name
        self.db_port = robot_store_db_port
        self.status_collection_name = robot_store_status_collection

        self.running = False
        self.monitoring_thread = None

    def start(self):
        self.running = True
        self.monitoring_thread = threading.Thread(target=self.monitor_components)
        self.monitoring_thread.start()

    def stop(self):
        self.running = False
        self.monitoring_thread.join()
        self.monitoring_thread = None

    def monitor_components(self) -> None:
        recovered_components = []
        while self.running:
            collection = self.__get_collection(self.status_collection_name)
            for component, recovery_params in self.config_params_map.items():
                # we look for the status document of the monitored component
                # and then take the status of the desired monitor
                component_name, monitor_name = recovery_params.monitor.split('/')
                status_doc = collection.find_one({'id': component_name})
                monitor_status = None
                for monitor_data in status_doc['monitor_status']:
                    # we skip the monitor if it's not the one we are interested in
                    if monitor_data['monitorName'] != monitor_name:
                        continue

                    # we take the status of the monitor we are interested in
                    monitor_status = monitor_data['healthStatus']
                    break

                if monitor_status is None:
                    print('[monitor_components] No monitor {0} found for component {1}'.format(recovery_params.monitor,
                                                                                               component))
                    continue

                if not monitor_status[recovery_params.monitored_param] and not component in recovered_components:
                    recovered_components.extend(self.perform_recovery(component, recovery_params, []))

            # we clear the list of recovered components before going through the component statuses again
            recovered_components = []

            # we sleep for a while before checking the statuses again
            time.sleep(0.5)
            print()

    def perform_recovery(self, component_name: str,
                         recovery_params: ComponentRecoveryConfig,
                         recovered_components=[]):
        print('[perform_recovery] Recovering {0}'.format(component_name))
        component_type = recovery_params.component_type
        if component_type == 'systemd':
            cmd_output = subprocess.check_output('systemctl', 'restart',
                                                 recovery_params.executable_to_restart)
            # TODO: process the command output

            recovered_components.append(component_name)
        else:
            print('[perform_recovery] Unknown component type {0} for component {1}'.format(component_type,
                                                                                           component_name))

        # if the children need to be recovered as well, we make a recursive call
        # for each child so that descendants at all levels can be recovered
        if recovery_params.recover_children:
            children = self.component_network.predecessors(component_name)
            for child in children:
                # we do not recover the component if it has already been recovered
                if child in recovered_components:
                    print('[perform_recovery] Skipping recovery of {0} since it was already recovered'.format(child))
                    continue

                print('[perform_recovery] {0} Recovering child {1}'.format(component_name, child))
                recovered_components = self.perform_recovery(child,
                                                             self.config_params_map[child],
                                                             recovered_components)
        return recovered_components

    def __read_config_file(self, config_file_path: str) -> Dict[str, ComponentRecoveryConfig]:
        config_params = None
        with open(config_file_path, 'r') as config_file:
            config_params = yaml.load(config_file)

        config_param_map = dict()
        for component, recovery_params in config_params.items():
            component_recovery_config = ComponentRecoveryConfig()
            component_recovery_config.name = component
            component_recovery_config.monitor = recovery_params['monitor']
            component_recovery_config.monitored_param = recovery_params['monitored_parameter']
            component_recovery_config.executable_to_restart = recovery_params['restart']
            component_recovery_config.component_type = recovery_params['component_type']

            if 'recover_children' in recovery_params:
                component_recovery_config.recover_children = recovery_params['recover_children']
            config_param_map[component] = component_recovery_config
        return config_param_map

    def __get_collection(self, collection_name) -> pm.collection.Collection:
        '''Returns a MongoDB collection with the given name
        from the "self.db" database.

        Keyword arguments:
        collection_name: str -- name of a MongoDB collection

        '''
        client = pm.MongoClient(port=self.db_port)
        db = client[self.db_name]
        collection = db[collection_name]
        return collection

if __name__ == '__main__':
    from component_monitoring.config.config_utils import ConfigUtils
    from component_monitoring.utils.component_network import ComponentNetwork

    config_file_path = 'config/component_monitoring_config.yaml'
    config_data = ConfigUtils.read_config(config_file_path)

    component_network = ComponentNetwork(config_file_path)
    recovery_manager = RecoveryManager(config_data['recovery_config'],
                                       component_network.network)

    try:
        recovery_manager.start()
        while True:
            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        print('Recovery manager exiting')
        recovery_manager.stop()
