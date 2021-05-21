import time

class RobotStoreInterface(object):
    def __init__(self, db_name='robot_store',
                 component_collection_name='components',
                 monitor_collection_name='status',
                 component_sm_state_collection_name='component_sm_states',
                 db_port=27017):
        self.db_name = db_name
        self.db_port = db_port
        self.component_collection_name = component_collection_name
        self.monitor_collection_name = monitor_collection_name
        self.component_sm_state_collection_name = component_sm_state_collection_name

    def store_component_configuration(self, hardware_components, software_components):
        '''Stores the configuration of the components in the robot database.
        In particular, creates one document per component of the form:

        {
            "component_name": <name-of-the-component>,
            "dependencies": <list-of-component-dependencies>,
            "recovery_actions": <list-of-recovery-actions-on-failures>
        }

        Keyword arguments:
        hardware_components: List[component_monitoring.config.config_params.ComponentMonitorConfig]
        software_components: List[component_monitoring.config.config_params.ComponentMonitorConfig]

        '''
        return

    def init_sm_state_collection(self, hardware_components, software_components):
        '''Initialises a collection for storing the statuses of the
        fault-tolerant state machines of the components.
        In particular, creates one document per component of the form:

        {
            "component_name": <name-of-the-component>,
            "state": "unknown"
        }

        Keyword arguments:
        hardware_components: List[component_monitoring.config.config_params.ComponentMonitorConfig]
        software_components: List[component_monitoring.config.config_params.ComponentMonitorConfig]

        '''
        return

    def store_component_status_msg(self, component_name, component_status_msg, client):
        '''Stores the status message of "component" into the database.

        Keyword arguments:
        component_name: str -- name of a monitored component
        component_status_msg: List[Dict] -- message containing the statuses of potentially
                                            multiple component monitoring modes
        client: MongoClient -- mongodb client

        '''
        return

    def store_monitor_msg(self, component_status_list):
        '''Stores the given status of all components into the database.
        In particular, creates or updates a one document per component
        with the following format:

        {
            "id": <component-name>,
            "timestamp": <current-time>,
            "monitor_status": <list-of-component-monitor-statuses>
        }

        Keyword arguments:
        component_status_list: List[dict] -- list of component status dictionaries

        '''
        return

    def read_component_sm_status(self, component_name, client):
        '''Reads the status of the fault-tolerant state machine associated
        with the given component.

        Keyword arguments:
        component_name: str -- name of a component
        client: MongoClient -- mongodb client

        '''
        return

    def get_component_status_msg(self, component_id, client):
        '''Reads the status message of the given component.

        Keyword arguments:
        component_id: str -- ID of a component
        client: MongoClient -- mongodb client

        '''
        return

    def get_connection(self):
        '''Returns a MongoClient object
        '''
        return
