import json

from db.models.event_monitor import EventLog
from kafka.consumer.fetcher import ConsumerRecord
import json
from bson import json_util
from jsonschema import validate

def convert_message(message: ConsumerRecord, db_type: str):
    timestamp = message.timestamp
    value = deserialize(message)
    monitor_name = value['monitorName']
    health_status = json.dumps(value['healthStatus'])
    if db_type == 'SQL':
        return EventLog(timestamp, monitor_name, health_status)
    json_msg = {"_id": message.timestamp, "timestamp": message.timestamp,
                "monitorName": monitor_name, "healthStatus": health_status}
    return json_msg

def validate_control_message(self, msg: dict) -> bool:
    try:
        validate(instance=msg, schema=self.event_schema)
        return True
    except:
        return False

def serialize(msg: dict) -> bytes:
    return json.dumps(msg, default=json_util.default).encode('utf-8')


def deserialize(msg:ConsumerRecord) -> dict:
    return json.loads(msg.value)


def create_eventlog(message, db_type):
    # print(f"[Helper] db_type : {db_type}")
    if db_type == 'SQL':
        timestamp = message["timestamp"]
        value = message["value"]
        monitor_name = value['monitorName']
        health_status = json.dumps(value['healthStatus'])
        return EventLog(timestamp, monitor_name, health_status)
    message['_id'] = message["timestamp"]
    return message
