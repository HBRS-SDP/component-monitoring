from typing import Union, Dict

from jsonschema import validate
from kafka import KafkaProducer, KafkaConsumer

from component_monitoring.component import Component
from component_monitoring.config.config_params import MonitorModeConfig
from component_monitoring.messaging.enums import MessageType


class MonitorBase(Component):
    """
    Abstract class defining a component monitor on a high level
    """

    def __init__(self, component: str, dialogue_id: str, config_params: MonitorModeConfig, server_address: str, control_channel: str):
        Component.__init__(self, f"{component}_{config_params.name}")
        self.component = component
        self.dialogue_id = dialogue_id
        self.mode = config_params.name
        self.config_params = config_params
        self.event_topic = f"{self.component}_{self.config_params.name}"
        self.control_topic = control_channel
        self.server_address = server_address
        self.healthstatus = {}

    def run(self) -> None:
        """
        Entry point of the base monitor process; Setting up the Kafka consumer and producer

        @return: None
        """
        self.producer = KafkaProducer(bootstrap_servers=self.server_address, value_serializer=self.serialize)
        self.consumer = KafkaConsumer(bootstrap_servers=self.server_address, client_id=self.config_params.name,
                                      enable_auto_commit=True, auto_commit_interval_ms=5000)
        self.consumer.subscribe([self.event_topic, self.control_topic])
        self.send_helo(self.dialogue_id, self.event_topic)

    def send_helo(self, dialogue_id: str, topic: str):
        message = dict()
        message['Id'] = dialogue_id
        helo = dict()
        helo['Component'] = self.component
        helo['Mode'] = self.mode
        helo['Topic'] = topic
        message[MessageType.HELO.value] = helo
        self.logger.info(message)
        if self.validate_broadcast(message):
            self.send_control_message(message)
        else:
            self.logger.warning("HELO message could not be validated!")
            self.logger.warning(message)

    def send_bye(self):
        message = dict()
        bye = dict()
        bye['Component'] = self.component
        bye['Mode'] = self.mode
        message[MessageType.HELO.value] = bye
        self.logger.info(message)
        if self.validate_broadcast(message):
            self.send_control_message(message)
        else:
            self.logger.warning(f"BYE message of {self._id} could not be validated!")
            self.logger.warning(message)

    def get_status_message_template(self) -> Dict:
        """
        Get the basic event message template
        @return: Basic Event message template
        """
        msg = dict()
        return msg

    def valid_event_message(self, msg: dict) -> bool:
        """
        Validate the event message against the respective schema

        @param msg: JSON dict containing the event message
        @return: True, if the message conforms to the schema, False otheriwse
        """
        try:
            validate(instance=msg, schema=self.event_schema)
            return True
        except:
            return False

    def send_event_msg(self, msg: Union[str, dict, bytes]) -> None:
        """
        Send event message via the Kafka message bus

        @param msg: The event message to send
        @return: None
        """
        if isinstance(msg, bytes):
            self.producer.send(topic=self.event_topic, value=msg)
        else:
            self.producer.send(topic=self.event_topic, value=self.serialize(msg))

    def publish_status(self) -> None:
        """
        Publish the current health status of the component under monitoring via Kafka

        @return: None
        """
        msg = self.get_status_message_template()
        msg["monitorName"] = self.config_params.name
        msg["monitorDescription"] = self.config_params.description
        msg["healthStatus"] = self.healthstatus
        if self.valid_event_message(msg):
            self.send_event_msg(msg)
        else:
            self.logger.error(f"Validation of event message failed in {self.config_params.name}!")
            self.logger.error(msg)
