"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import logging
import time

class Tests:
    def __init__(self, robot):
        self.log = logging.getLogger('Robot.Tests')
        self.bot = robot

    def movement(self):
        for i in range(12):
            self.log.info("Driving 1.8m")
            self.bot.wheels.forward(1.8, 50)
            self.log.info("Turning right 90deg")
            self.bot.wheels.right(90, 50)
        self.log.info("Mission Complete")

    def cameraRotation(self):
        while True:
            self.bot.camera.look_forward()
            time.sleep(3)
            self.bot.camera.look_behind()
            time.sleep(3)

    def driveSShape(self):
        self.bot.wheels.forward(1, 60)
        self.bot.wheels.right(50, 60)
        self.bot.wheels.forward(1, 60)
        self.bot.wheels.left(40, 60)
        self.bot.wheels.forward(1, 60)
        self.bot.wheels.backward(1, 60)
        self.bot.wheels.right(40, 60)
        self.bot.wheels.backward(1, 60)
        self.bot.wheels.left(50, 60)
        self.bot.wheels.backward(1, 60)

    def arm(self):
        while True:
            self.log.info("Down")
            self.bot.arm.down()
            time.sleep(1)
            self.log.info("Up")
            self.bot.arm.up()
            time.sleep(1)

    def someTest(self):
        success = False
        while not success:
            markers = None
            while markers is None or markers.is_empty:
                self.log.info("Finding markers")
                markers = self.bot.camera.get_markers()
                self.log.info("Found: %s", markers)
            marker = markers.get_closest()
            success = self.bot.navigate_to_marker(marker, 60)
        self.bot.arm.down()
        self.bot.wheels.backward(1, 60)
        self.bot.wheels.right(180, 60)
        self.bot.arm.up()
        self.bot.wheels.backward(0.5, 60)

    def nav(self):
        marker = self.bot.camera.get_markers().get_closest()
        self.bot.navigate_to_marker(marker, 60)

    def captureFlag(self):
        while True:
            flags = self.bot.camera.get_markers() \
                    .filter(lambda m: m.info.marker_type == 'flag')
            if not flags.is_empty:
                break
        f = flags.get_closest()
        if f.rot_y < 0:
            self.bot.wheels.left(f.rot_y, 70)
        else:
            self.bot.wheels.right(f.rot_y, 70)
        self.bot.wheels.forward(f.dist, 70)
        self.bot.arm.down()
        self.bot.camera.look_behind()
        self.bot.wheels.backward(1, 70)
        self.bot.arm.up()
        self.bot.camera.look_forward()
        self.captureFlag()

    def bumpTest(self):
        from event_bus import EventBus
        def bump(sensors):
            self.log.info("Bump on sensors %s", sensors)
        EventBus.GLOBAL.register('bump', bump)
        def flag():
            self.log.info("Flag plate touch")
        EventBus.GLOBAL.register('flag_plate_touch', flag)

def testRunner(robot):
    test = Tests(robot)
    test.bumpTest()
