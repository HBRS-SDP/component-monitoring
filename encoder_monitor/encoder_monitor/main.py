import time
import uuid
import json
import datetime
from data_retriever import DataRetriever
from encoder_monitor import EncoderMonitor
from pyre_talker import PyreTalker

def create_msg(result):
    d = datetime.datetime.now()
    msg = {}
    msg["header"] = {}
    msg["header"]["type"] = "STATUS"
    msg["header"]["metamodel"] = "ropod-msg-schema.json"
    msg["header"]["msgId"] = str(uuid.uuid4())
    msg["header"]["timestamp"] = d.isoformat('T')
    payload = {}
    payload["metamodel"] = "ropod-status-schema.json"
    payload["robotId"] = "ropod_0"
    payload["status"] = result
    msg["payload"] = payload
    return msg

def main():
    p = PyreTalker('component_monitor', 'ROPOD')
    d = DataRetriever('localhost', 'logs')
    e = EncoderMonitor(velocity_threshold = 1.0, pivot_velocity_threshold = 1.0,
                       wheel_diameter = 0.073, inter_wheel_distance = 0.0893)
    window_size = 5.0
    while True:
        end_time = time.time()
        x = d.get_data(['ros__sw_ethercat_parser_data'], end_time, window_size)['ros__sw_ethercat_parser_data']
        result = e.run(x)
        if result:
            msg = create_msg(result)
            p.shout(json.dumps(msg))
        time.sleep(2)

if __name__ == "__main__":
    main()
