from os.path import join
import yaml
from component_monitoring.config.config_params import ComponentMonitorConfig, MonitorModeConfig, \
                                                      FunctionalMappingConfig, OutputConfig

class ComponentMonitorConfigFileReader(object):
    '''An interface for reading component monitor configuration files

    @author Alex Mitrevski, Santosh Thoduka
    @contact aleksandar.mitrevski@h-brs.de, santosh.thoduka@h-brs.de
    '''
    @staticmethod
    def load(root_dir, config_file_name):
        '''Loads the configuration parameters of a component monitor from the given YAML file

        Keyword arguments:
        @param root_dir component monitor configuration file directory
        @param config_file_name absolute path of a config file

        '''
        params = ComponentMonitorConfig()

        file_path = join(root_dir, config_file_name)
        root = ComponentMonitorConfigFileReader.__read_yaml_file(file_path)
        if 'component_name' in root:
            params.component_name = root['component_name']
        else:
            raise AssertionError('{0}: component_name not specified'.format(config_file_name))

        if 'description' in root:
            params.description = root['description']
        else:
            raise AssertionError('{0}: description not specified'.format(config_file_name))

        if 'dependencies' in root:
            params.component_dependencies = root['dependencies']

        if 'dependency_monitors' in root:
            params.dependency_monitors = root['dependency_monitors']

        if 'recovery_actions' in root:
            params.recovery_actions = root['recovery_actions']

        if 'modes' in root:
            for mode_config_file in root['modes']:
                mode_config = ComponentMonitorConfigFileReader.__load_mode_config(root_dir,
                                                                                  mode_config_file)
                params.modes[mode_config.name] = mode_config
        else:
            raise AssertionError('{0}: modes not specified'.format(config_file_name))

        return params

    @staticmethod
    def __load_mode_config(root_dir, config_file_name):
        '''Loads the configuration parameters of a component monitor mode from the given YAML file

        Keyword arguments:
        @param root_dir component monitor configuration file directory
        @param config_file_name absolute path of a config file

        '''
        params = MonitorModeConfig()

        file_path = join(root_dir, config_file_name)
        root = ComponentMonitorConfigFileReader.__read_yaml_file(file_path)

        if 'name' in root.keys():
            params.name = root['name']
        else:
            raise AssertionError('{0}: name not specified'.format(config_file_name))

        if 'description' in root.keys():
            params.description = root['description']
        else:
            raise AssertionError('{0}: description not specified'.format(config_file_name))

        if 'arguments' in root.keys():
            params.arguments = root['arguments']

        if 'mappings' in root.keys():
            for mapping in root['mappings']:
                mapping_node = mapping['mapping']

                fn_mapping_params = FunctionalMappingConfig()
                fn_mapping_params.inputs = mapping_node['inputs']

                if 'map_outputs' in mapping_node.keys():
                    fn_mapping_params.map_outputs = mapping_node['map_outputs']

                for output in mapping_node['outputs']:
                    output_node = output['output']

                    output_params = OutputConfig()
                    output_params.name = output_node['name']
                    output_params.obtained_value_type = output_node['type']
                    # output_params.topic = output_node['topic']
                    if 'expected' in output_node.keys():
                        output_params.expected_value = output_node['expected']
                    fn_mapping_params.outputs.append(output_params)
                params.mappings.append(fn_mapping_params)
        else:
            raise AssertionError('{0}: mappings not specified'.format(config_file_name))

        return params

    @staticmethod
    def __read_yaml_file(file_name):
        file_handle = open(file_name, 'r')
        data = yaml.safe_load(file_handle)
        file_handle.close()
        return data
