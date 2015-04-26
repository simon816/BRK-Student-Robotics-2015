"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

class EventBus(object):

    GLOBAL = None

    def __init__(self):
        self.reg = {}

    def post(self, channel, payload=None):
        if channel not in self.reg:
            return
        for handler in self.reg[channel]:
            try:
                if payload is None:
                    handler()
                else:
                    handler(payload)
            except Exception as e:
                if channel != '__bus_error__':
                    self.post('__bus_error__', (channel, handler, e))
                else:
                    raise e

    def register(self, channel, handler):
        if not channel in self.reg:
            self.reg[channel] = []
        self.reg[channel].append(handler)

    def unregister(self, channel, handler):
        if not channel in self.reg:
            return
        if not handler in self.reg[channel]:
            return
        self.reg[channel].remove(handler)

EventBus.GLOBAL = EventBus()
