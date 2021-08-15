import datetime
import json
import logging
import sys
from multiprocessing import Process
from typing import Optional, Dict, List, Union

from bson import json_util
from jsonschema import validate, ValidationError
from kafka.consumer.fetcher import ConsumerRecord
from kafka.producer.future import FutureRecordMetadata

from component_monitoring.messaging.enums import MessageType, Response
from helper import CustomFormatter


class Component(Process):
    def __init__(self, _id: str, control_channel='monitor_manager', server_address='localhost:9092'):
        Process.__init__(self)
        self._id = _id
        self.control_channel = control_channel
        self.server_address = server_address

        # setup logging
        self.__log_level = logging.INFO
        self.logger = logging.getLogger(self._id)
        self.logger.setLevel(self.__log_level)
        # create console handler with custom formatter
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(self.__log_level)
        ch.setFormatter(CustomFormatter())
        self.logger.addHandler(ch)

        self.producer = None
        self.consumer = None

        with open('component_monitoring/messaging/schemas/event.json', 'r') as schema:
            self.event_schema = json.load(schema)
        with open('component_monitoring/messaging/schemas/request.json', 'r') as schema:
            self.request_schema = json.load(schema)
        with open('component_monitoring/messaging/schemas/broadcast.json', 'r') as schema:
            self.broadcast_schema = json.load(schema)
        with open('component_monitoring/messaging/schemas/response.json', 'r') as schema:
            self.response_schema = json.load(schema)

    def send_control_message(self, msg: Dict) -> Optional[FutureRecordMetadata]:
        """
        Send a control message over the control channel

        @param msg: The control message as a JSON Dict
        @return: FutureRecordMetadata: resolves to RecordMetadata or None if message is invalid
        """
        return self.producer.send(self.control_channel, msg)

    def validate_request(self, msg: dict) -> bool:
        """
        Validate a request message against the respective schema.

        @param msg: Message as JSON Dict to be validated
        @return: True if the validation was successful against the respective schemas, False otherwise.
        """
        try:
            validate(instance=msg, schema=self.request_schema)
            return True
        except Exception as e:
            self.logger.debug(e)
            return False

    def validate_response(self, msg: dict) -> bool:
        """
        Validate a response message against the respective schema.

        @param msg: Message as JSON Dict to be validated
        @return: True if the validation was successful against the respective schemas, False otherwise.
        """
        try:
            validate(instance=msg, schema=self.response_schema)
            return True
        except Exception as e:
            self.logger.debug(e)
            return False

    def validate_broadcast(self, msg: dict) -> bool:
        """
        Validate a broadcast message against the respective schema.

        @param msg: Message as JSON Dict to be validated
        @return: True if the validation was successful against the respective schemas, False otherwise.
        """
        try:
            validate(instance=msg, schema=self.broadcast_schema)
            return True
        except Exception as e:
            self.logger.debug(e)
            return False

    def serialize(self, msg) -> bytes:
        """
        Serializes any message to be sent via the Kafka message bus

        @param msg: JSON serializable message
        @return: serialized message
        """
        return json.dumps(msg, default=json_util.default).encode('utf-8')

    def deserialize(self, msg: ConsumerRecord) -> dict:
        """
        Deserializes any message received via the Kadka message bus

        @param msg: A Kafka ConsumerRecord, whose message value should be deserialized. It is expected, that the message
                    value is JSON serializable
        @return: The message value as JSON Dict
        """
        return json.loads(msg.value)

    def send_start(self, dialogue_id: str, receiver: str, targets: Optional[List[Dict[str, Union[str, Dict]]]]) -> Dict:
        message = self.setup_message_header(dialogue_id, receiver)
        if targets:
            message['START'] = targets
        else:
            message['START'] = list()
        self.send_control_message(message)
        return message

    def send_stop(self, dialogue_id: str, receiver: str, targets: List[str]):
        message = self.setup_message_header(dialogue_id, receiver)
        message['STOP'] = targets
        self.send_control_message(message)

    def send_update(self, dialogue_id: str, receiver: str, params: Dict) -> None:
        """
        Send an INFO message over the control channel.

        @param receiver: The component the message is addressed to
        @param params: The parameters of the component tp be updated
        @return: None
        """
        message = self.setup_message_header(dialogue_id, receiver)
        message['UPDATE'] = dict()
        message['UPDATE']['params'] = params
        self.send_control_message(message)

    def send_response(self, dialogue_id: str, receiver: str, code: Response,
                      additional_parameters: Optional[Union[Dict, List, str]] = None) -> None:
        """
        Send a RESPONSE message over the control channel

        @param dialogue_id: The temporary unique dialogue ID that the response is concerned with
        @param receiver: The component the message is addressed to
        @param code: The Response to be sent
        @param additional_parameters: Additional message content
        @return: None
        """
        message = self.setup_message_header(dialogue_id, receiver)
        message['Response'] = dict()
        message['Response']['Code'] = code.value
        message['Response']['Message'] = additional_parameters
        self.logger.info(f"Sending response to request {dialogue_id}: {message}")
        if self.validate_response(message):
            self.send_control_message(message)
        else:
            self.logger.warning(f"Validation of response to {dialogue_id} failed!")

    def setup_message_header(self, dialogue_id: str, receiver: str) -> Dict:
        message = dict()
        message['Id'] = dialogue_id
        message['From'] = self._id
        message['To'] = receiver
        return message

    def get_message_type(self, message: Dict) -> Optional[MessageType]:
        for key in message.keys():
            if key in [item.value for item in MessageType]:
                return MessageType(key)
        return None

    def receive_control_response(self, dialogue_id: str, expected_response_code: Response,
                                 response_timeout=5) -> bool:
        start_time = datetime.datetime.now()
        try:
            for message in self.consumer:
                try:
                    if message.value['To'] != self._id:
                        continue
                    # Validate the correctness of the response message
                    validate(
                        instance=message.value,
                        schema=self.consumer
                    )
                    if message.value['To'] == self._id and message.value['Id'] == dialogue_id:
                        response_code = Response(message.value['Code'])
                        if response_code == expected_response_code:
                            return True
                        else:
                            try:
                                description = message.value['Description']
                            except KeyError:
                                description = None
                            self.logger.warning(f"Received {response_code}: {description}")
                            return False
                except ValidationError:
                    self.logger.warning("Invalid format of the acknowledgement.")
                except KeyError:
                    # If message does not contain "To" field it could be a broadcast, hence this does not have to
                    # indicate an error and can be ignored.
                    pass
                if datetime.datetime.now() - start_time > datetime.timedelta(seconds=response_timeout):
                    raise TimeoutError

            # self.logger.warning('[{}][{}] No response from the monitor manager.'.
            #               format(self.name, self._id))
            # return False
        except TimeoutError:
            self.logger.warning(f'Timeout occurred while waiting for response on Request with ID {dialogue_id}')
            return False
