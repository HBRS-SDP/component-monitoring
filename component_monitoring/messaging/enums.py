from enum import Enum
from typing import Dict


class Response(Enum):
    OKAY = 200
    STARTING = 201
    STOPPING = 202
    FAILED = 400
    INCOMPLETE = 401
    NOT_FOUND = 404


class MessageType(Enum):
    START = 'START'
    STOP = 'STOP'
    UPDATE = 'UPDATE'
    HELO = 'HELO'
    BYE = 'BYE'
