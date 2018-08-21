from pyre import Pyre

from pyre import zhelper
import zmq
import uuid
import logging
import sys
import json

class PyreTalker(object):
    def __init__(self, name, group):
        self.name = name
        self.group = group
        self.node = Pyre(name)
        self.node.start()
        self.node.join(group)

        self.context = zmq.Context()
        self.listener_pipe = zhelper.zthread_fork(self.context, self.message_callback)

    def shout(self, message):
        self.node.shouts(self.group, message)

    def message_callback(self, context, pipe):
        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        poller.register(self.node.socket(), zmq.POLLIN)
        while True:
            items = dict(poller.poll())
            if pipe in items and items[pipe] == zmq.POLLIN:
                m = pipe.recv()
                # message to quit
                if m.decode('utf-8') == "$$STOP":
                    break
            else:
                msg = self.node.recv()

    def stop(self):
        self.listener_pipe.send("$$STOP".encode('utf-8'))
        self.node.leave(self.group)
        self.node.stop()
