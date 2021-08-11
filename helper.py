import json

from bson import json_util
from kafka.consumer.fetcher import ConsumerRecord


def serialize(msg: dict) -> bytes:
    return json.dumps(msg, default=json_util.default).encode('utf-8')


def deserialize(msg: ConsumerRecord) -> dict:
    return json.loads(msg.value)