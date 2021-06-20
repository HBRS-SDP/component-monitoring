import json

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

Base = declarative_base()


class EventLog(Base):

    __tablename__ = "eventlog"
    timestamp = Column('TIMESTAMP', String, primary_key=True)
    monitor_name = Column('MONITOR_NAME', String)
    health_status = Column('HEALTH_STATUS', String)

    def __init__(self, timestamp, monitor_name, health_status):
        self.timestamp = timestamp
        self.monitor_name = monitor_name
        self.health_status = health_status

    def __str__(self):
        return f"EVENTLOG [ TIMESTAMP : {self.timestamp}, MONITOR_NAME : {self.monitor_name}, HEALTH_STATUS : {json.dumps(self.health_status)}]"

    def __repr__(self):
        return f"EVENTLOG [ TIMESTAMP : {self.timestamp}, MONITOR_NAME : {self.monitor_name}, HEALTH_STATUS : {json.dumps(self.health_status)}]"
