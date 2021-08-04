class ComponentRecoveryConfig(object):
    def __init__(self):
        ## component name
        self.name = ''

        ## name of a monitor for the component
        self.monitor = ''

        ## name of a parameter to monitor
        self.monitored_param = ''

        ## name of a component to restart on failure
        self.executable_to_restart = ''

        ## indicates whether to recover the children of the component
        ## when the component itself is recovered
        self.recover_children = False

    def __repr__(self):
        obj = self.get_dict()
        return str(obj)

    def get_dict(self):
        obj = dict()
        obj['name'] = self.name
        obj['monitor'] = self.monitor
        obj['monitored_parameter'] = self.monitored_param
        obj['executable_to_restart'] = self.executable_to_restart
        obj['component_type'] = self.component_type
        obj['recover_children'] = self.recover_children
        return obj

class OutputConfig(object):
    def __init__(self):
        ## output value name
        self.name = ''

        ## output value
        self.obtained_value_type = ''

        ## expected output value
        self.expected_value = ''

        ## Apache kafka topic for publishing
        # self.topic = ''

    def __repr__(self):
        obj = self.get_dict()
        return str(obj)

    def get_dict(self):
        obj = dict()
        obj['name'] = self.name
        obj['obtained_value_type'] = self.obtained_value_type
        obj['expected_value'] = self.expected_value
        # obj['topic'] = self.topic
        return obj

class FunctionalMappingConfig(object):
    def __init__(self):
        ## a list of input parameters for the monitor mode
        self.inputs = list()

        ## a list of 'OutputConfig' objects specifying the
        ## output parameters of the monitor mode
        self.outputs = list()

        ## specifies whether the outputs are returned in a dictionary
        self.map_outputs = False

    def __repr__(self):
        obj = self.get_dict()
        return str(obj)

    def get_dict(self):
        obj = dict()
        obj['inputs'] = self.inputs
        obj['outputs'] = [i.get_dict() for i in self.outputs]
        obj['map_outputs'] = self.map_outputs
        return obj

class MonitorModeConfig(object):
    def __init__(self):
        ## monitor mode name (snake case should be used if the name has multiple words)
        self.name = ''

        ## monitor mode description
        self.description = ''

        ## a list of 'FunctionalMappingConfig' objects specifying
        ## the parameters of the monitor mode inputs and outputs
        self.mappings = list()

        ## a dictionary of monitor mode arguments
        self.arguments = dict()

    def __repr__(self):
        obj = self.get_dict()
        return str(obj)

    def get_dict(self):
        obj = dict()
        obj['name'] = self.name
        obj['description'] = self.description
        obj['mappings'] = [i.get_dict() for i in self.mappings]
        obj['arguments'] = self.arguments
        return obj

class ComponentMonitorConfig(object):
    def __init__(self):
        ## name of the monitored component
        self.component_name = ''

        ## monitor description
        self.description = ''

        ## a list of 'MonitorModeConfig' objects specifying
        ## the parameters of the monitor modes
        self.modes = list()

        ## a list of components on which the component depends
        self.component_dependencies = list()

        ## a dictionary in which each key corresponds to one
        ## of the dependencies in self.component_dependencies
        ## and the values are dictionaries of monitor descriptions
        self.dependency_monitors = dict()

        ## a list of recovery actions to take in case
        ## the component is not operating as expected
        self.recovery_actions = list()

    def get_dict(self):
        obj = dict()
        obj['component_name'] = self.component_name
        obj['description'] = self.description
        obj['modes'] = [i.get_dict() for i in self.modes]
        obj['component_dependencies'] = self.component_dependencies
        obj['dependency_monitors'] = self.dependency_monitors
        obj['recovery_actions'] = self.recovery_actions
        return obj

    def __repr__(self):
        obj = self.get_dict()
        return str(obj)
