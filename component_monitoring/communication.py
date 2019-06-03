from copy import deepcopy
import time
import uuid
from ropod.pyre_communicator.base_class import RopodPyre
from black_box_tools.data_utils import DataUtils

class BlackBoxPyreCommunicator(RopodPyre):
    '''
    Pyre node to send queries to the black box query interface and to receive
    data

    Heavily based on /remote_monitoring/zyre_communicator.py
    '''
    def __init__(self, node_name, groups, black_box_id, data_timeout=2.):
        '''
        Keyword arguments:
        node_name -- name of the zyre node
        groups -- groups that the node should join
        data_timeout -- timeout (in seconds) for data queries and messages (default 10.)
        '''
        super(BlackBoxPyreCommunicator, self).__init__(node_name, groups, [])

        # timeout (in seconds) for data queries and messages
        self.__data_timeout = data_timeout

        # a dictionary in which the keys are session IDs
        # and the values are types of requests for the particular users
        self.__request_type = dict()

        # a dictionary in which the keys are session IDs
        # and the values are messages for the particular users
        self.__request_data = dict()

        self.black_box_id = black_box_id

        self.start()

    def receive_msg_cb(self, msg_content):
        '''Processes incoming messages. Only listens to messages of type
        "DATA-QUERY", "LATEST-DATA-QUERY"; ignores all other message types

        Keyword arguments:
        msg_content -- a zyre message in string format

        '''
        dict_msg = self.convert_zyre_msg_to_dict(msg_content)
        if dict_msg is None:
            return

        timestamp = dict_msg['header']['timestamp']
        message_type = dict_msg['header']['type']
        if message_type == 'DATA-QUERY' or \
           message_type == 'LATEST-DATA-QUERY':
            for session_id in self.__request_data:
                if dict_msg['payload']['senderId'] == session_id:
                    self.__request_data[session_id] = dict_msg

    def send_query(self, start_time, end_time, variables):
        """
        create and send a query message to black box query interface through
        pyre shout.

        :start_time: float
        :end_time: float
        :variables: list of strings
        :returns: None

        """
        msg_sender_id = str(uuid.uuid4())
        data_query_msg = DataUtils.get_bb_query_msg(msg_sender_id, self.black_box_id,
                                                    variables, start_time, end_time)
        return self.get_black_box_data(data_query_msg)

    def send_latest_data_query(self, variables):
        """
        create and send a query message to black box query interface through
        pyre shout.

        :variables: list of strings
        :returns: None

        """
        msg_sender_id = str(uuid.uuid4())
        data_query_msg = DataUtils.get_bb_latest_data_query_msg(
                msg_sender_id, self.black_box_id, variables)
        return self.get_black_box_data(data_query_msg)

    def get_black_box_data(self, query_msg):
        '''Queries data from a black box and waits for a response

        Keyword arguments:
        query_msg -- a dictionary black box query message

        '''
        session_id = query_msg['payload']['senderId']
        self.__request_data[session_id] = None
        self.shout(query_msg)
        data = self.__wait_for_data(session_id)
        return data

    def __wait_for_data(self, session_id):
        '''Waits for incoming data for the user with the provided session ID
        and returns the received data. Returns None if not data is received
        within "self.__data_timeout" seconds

        Keyword arguments:
        session_id -- Session ID of a user requesting data

        '''
        start_time = time.time()
        elapsed_time = 0.
        while not self.__request_data[session_id] and elapsed_time < self.__data_timeout:
            time.sleep(0.1)
            elapsed_time = time.time() - start_time

        data = None
        if self.__request_data[session_id]:
            data = self.__request_data[session_id]

        self.__request_data.pop(session_id)
        if session_id in self.__request_type:
            self.__request_type.pop(session_id)
        return data
