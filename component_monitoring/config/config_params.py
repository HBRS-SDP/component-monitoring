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
        ## monitor mode name
        self.name = ''

        ## a list of 'FunctionalMappingConfig' objects specifying
        ## the parameters of the monitor mode inputs and outputs
        self.mappings = list()

        ## a dictionary of monitor mode arguments
        self.arguments = dict()

class ComponentMonitorConfig(object):
    def __init__(self):
        ## name of the monitor
        self.name = ''

        ## name of the monitored component
        self.component_name = ''

        ## a list of 'MonitorModeConfig' objects specifying
        ## the parameters of the monitor modes
        self.modes = list()

        ## a list of components on which the component depends
        self.component_dependencies = list()
