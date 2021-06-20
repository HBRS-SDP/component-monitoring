import json

from db.models.event_monitor import EventLog
from kafka.consumer.fetcher import ConsumerRecord


def convert_message(message: ConsumerRecord, db_type) -> EventLog:
    if db_type == 'SQL':
        timestamp = message.timestamp
        value = message.value
        monitor_name = value['monitorName']
        health_status = json.dumps(value['healthStatus'])
        return EventLog(timestamp, monitor_name, health_status)
    json_msg = {"_id": message.timestamp, "timestamp": message.timestamp,
                "monitorName": message.value['monitorName'], "healthStatus": message.value['healthStatus']}
    return json_msg


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
