from enum import Enum


class KafkaTopicCommands(Enum):
    CMD_SHUTDOWN = 'shutdown'
    CMD_START = 'activate'
    STATUS_FAILURE = 'failed'
    STATUS_SUCCESS = 'success'
    TYPE_ACK = 'ack'
    TYPE_CMD = 'cmd'
    STORAGE = 'storage'
