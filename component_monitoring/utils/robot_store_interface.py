import time
import pymongo as pm

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
        try:
            client = pm.MongoClient(port=self.db_port)
            db = client[self.db_name]
            collection = db[self.component_collection_name]

            components = hardware_components + software_components
            for component_config in components:
                component_name = component_config.component_name
                doc = {'component_name': component_name,
                       'dependencies': component_config.component_dependencies,
                       'dependency_monitors': component_config.dependency_monitors,
                       'recovery_actions': component_config.recovery_actions}
                collection.replace_one({'component_name': component_name}, doc, upsert=True)
        except pm.errors.OperationFailure as exc:
            print('[component_monitoring/store_component_configuration] {0}'.format(exc))

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
        try:
            client = pm.MongoClient(port=self.db_port)
            db = client[self.db_name]
            collection = db[self.component_sm_state_collection_name]

            components = hardware_components + software_components
            for component_config in components:
                component_name = component_config.component_name
                doc = {'component_name': component_name,
                       'dependencies': 'unknown'}
                collection.replace_one({'component_name': component_name}, doc, upsert=True)
        except pm.errors.OperationFailure as exc:
            print('[component_monitoring/init_sm_state_collection] {0}'.format(exc))

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
        try:
            client = pm.MongoClient(port=self.db_port)
            db = client[self.db_name]
            collection = db[self.monitor_collection_name]

            for component_status in component_status_list:
                component_name = component_status['component_id']
                status_msg = {'id': component_name,
                              'timestamp': time.time(),
                              'monitor_status': component_status['modes']}
                collection.replace_one({'id': component_name}, status_msg, upsert=True)
        except pm.errors.OperationFailure as exc:
            print('[component_monitoring/store_monitor_msg] {0}'.format(exc))

    def read_component_sm_status(self, component_name):
        '''Reads the status of the fault-tolerant state machine associated
        with the given component.

        Keyword arguments:
        component_name: str -- name of a component

        '''
        try:
            client = pm.MongoClient(port=self.db_port)
            db = client[self.db_name]
            collection = db[self.component_sm_state_collection_name]
            state_doc = collection.find_one({'component_name': component_name})
            if state_doc:
                return state_doc['state']
        except pm.errors.OperationFailure as exc:
            print('[component_monitoring/read_component_sm_status] {0}'.format(exc))
        return 'unknown'
