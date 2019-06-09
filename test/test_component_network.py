from os.path import abspath, dirname, join
import unittest

from component_monitoring.utils.component_network import ComponentNetwork

class ComponentNetworkTester(unittest.TestCase):
    def test_acyclic_dependency_network(self):
        test_dir = abspath(dirname(__file__))
        root_dir = dirname(test_dir)
        config_file_path = join(root_dir, 'config/component_monitoring_config.yaml')

        component_network = ComponentNetwork(config_file_path, root_dir)
        print('Verifying that the component dependency graph is acyclic')
        assert component_network.is_acyclic()

if __name__ == '__main__':
    unittest.main()
