from enum import Enum


class Command(Enum):
    START = 'activate'
    SHUTDOWN = 'shutdown'
    START_STORE = 'start_store'
    STOP_STORE = 'stop_store'

class ResponseCode(Enum):
    SUCCESS = 200
    FAILURE = 400

class MessageType(Enum):
    RESPONSE = 'response'
    REQUEST = 'request'
    INFO = 'info'