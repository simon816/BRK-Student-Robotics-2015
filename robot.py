"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import sys
import logging
import os
import time
from subprocess import Popen

from sr.robot import Robot as SRBot

COMP_MODE = True

TEST_MODE = False

def setup_logger(root):
    logger = logging.getLogger('Robot')
    logger.setLevel(logging.DEBUG)

    live_log = logging.StreamHandler(sys.stdout)
    live_log.setLevel(logging.INFO)
    live_log.setFormatter(logging.Formatter('%(asctime)s.%(msecs)d [%(levelname)s] [%(name)s] %(message)s', "%M:%S"))
    logger.addHandler(live_log)

    path = os.path.join(root, "comp" if COMP_MODE else "", time.strftime("%Y-%m-%d",  time.localtime()))
    if not os.path.exists(path):
        os.makedirs(path)
    filename = os.path.join(path, time.strftime("%H.%M.%S", time.localtime()) + ".log")
    i = 0
    while os.path.exists(filename):
        filename = os.path.join(path, time.strftime("%H.%M.%S", time.localtime()) + "_%d.log" % i)
        i += 1
    file_log = logging.FileHandler(filename)
    file_log.setLevel(logging.DEBUG)
    file_log.setFormatter(logging.Formatter('%(asctime)s@%(threadName)s [%(levelname)s] [%(name)s,%(funcName)s:%(lineno)d] %(message)s'))
    logger.addHandler(file_log)

    return logger

def set_time(ziproot):
    try:
        mtime = os.path.getmtime(os.path.join(ziproot, 'robot.zip'))
        if time.time() > mtime:
            return
        date = time.strftime('%d %b %Y %H:%M:%S', time.gmtime(mtime))
        print "[PreInit] Setting time to " + date
        Popen(["date", "-s", date]).wait()
    except Exception as e:
        print "[PreInit] Setting time failed %s " % e
        pass

def setup():
    # A bad way to detect whether running in simulator
    if sys.platform.startswith('win'):
        ### SIMULATOR ONLY ###
        SRBot.zone, SRBot.sim = getInfo() # I made this to make simlator work
    srBot = SRBot.setup()
    srBot.init()
    set_time(srBot.usbkey)
    logger = setup_logger(srBot.usbkey)
    logger.info('Battery Voltage: %.2f' % (srBot.power.battery.voltage))
    srBot.wait_start()
    try:
        from main import Robot
        robot = Robot(srBot)
    except:
        logger.exception("Robot could not initialize")
        raise
    return robot, srBot.zone

if __name__ == '__main__' or __name__ == '__builtin__':
    robot, corner = setup()
    if TEST_MODE:
        import tests
        tests.testRunner(robot)
    else:
        import gamelogic
        gamelogic.PlayGame(robot, corner)
