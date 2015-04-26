"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import threading
import time
from event_bus import EventBus

class RobotThreads:
    def __init__(self, robot):
        self.threads = []
        self.bot = robot
        self.add_thread(BumpThread(robot))

    def add_thread(self, thread):
        thread.daemon = False # Doesn't seem to work when True
        thread.can_run = lambda: self.bot.running
        self.threads.append(thread)

    def run(self):
        for thread in self.threads:
            thread.start()

class BumpThread(threading.Thread):
    def __init__(self, bot):
        super(BumpThread, self).__init__()
        self.sensors = bot.bump['__all__']
        self.sensors.insert(0, bot.flag_sens)
        self.bot = bot

    def run(self):
        while True:
            got_flag = False
            bumped_sensors = []
            for sensor in self.sensors:
                if sensor.read():
                    if sensor == self.bot.flag_sens:
                        got_flag = True
                        EventBus.GLOBAL.post('flag_plate_touch')
                    else:
                        if sensor == self.bot.bump['front']['middle'] and got_flag:
                            continue
                        else:
                            bumped_sensors.append(sensor)
            if len(bumped_sensors) != 0:
                EventBus.GLOBAL.post('bump', bumped_sensors)
            time.sleep(0.2)
