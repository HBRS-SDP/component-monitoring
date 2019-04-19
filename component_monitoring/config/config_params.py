class OutputConfig(object):
    def __init__(self):
        ## output value name
        self.name = ''

        ## output value
        self.obtained_value_type = ''

        ## expected output value
        self.expected_value = ''

class FunctionalMappingConfig(object):
    def __init__(self):
        ## a list of input parameters for the monitor mode
        self.inputs = list()

        ## a list of 'OutputConfig' objects specifying the
        ## output parameters of the monitor mode
        self.outputs = list()

        ## specifies whether the outputs are returned in a dictionary
        self.map_outputs = False

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

        ## a list of recovery actions to take in case
        ## the component is not operating as expected
        self.recovery_actions = list()
