"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import logging
import math
import threading
import time

from controllers.motor import MotorController

class MovementSystem:
    def __init__(self, srBot):
        self.log = logging.getLogger('Robot.Movement')
        self.log.debug("Setup motor controllers")
        try:
            self.l_wheel = MotorController(srBot, type='WHEEL', id='LEFT')
            self.r_wheel = MotorController(srBot, type='WHEEL', id='RIGHT')
        except Exception as e:
            self.log.exception(e)
            raise e

    def forward(self, distance, speed, async=False):
        """Drives straight forwards for the given distance (meters) and speed.
        Setting async to True will return immediately and drive in a separate
        thread, otherwise will block until the calculated delay has elapsed.
        Returns a function that blocks until the operation has completed, this
        does nothing if async=False."""
        self.log.debug("Forwards %.2fm %d%%", distance, speed)
        return self._drive(self.l_wheel.forward, self.r_wheel.forward,
                           distance, distance, speed, async)

    def backward(self, distance, speed, async=False):
        """Drives straight backwards for the given distance and speed.
        See MovementSystem#forward for info on the async parameter."""
        self.log.debug("Backwards %.2fm %d%%", distance, speed)
        return self._drive(self.l_wheel.backward, self.r_wheel.backward,
                           distance, distance, speed, async)

    def right(self, degree, speed, pivot='center', async=False):
        """Rotates the robot right given the degree and speed.
        If pivot is set to 'center', the robot will rotate on a spot,
        if set to 'wheel', the robot will rotate about the wheel.
        See MovementSystem#forward for info on the async parameter."""
        self.log.debug("Right %.2fdeg %d%% about %s", degree, speed, pivot)
        l_dist, r_dist = self._calc_driving_dist(degree, pivot)
        return self._drive(self.l_wheel.forward, self.r_wheel.backward,
                           l_dist, r_dist, speed, async)

    def left(self, degree, speed, pivot='center', async=False):
        """Rotates the robot left given the degree and speed.
        See MovementSystem#left for info on the pivot parameter and
        see MovementSystem#forward for info on the async parameter."""
        self.log.debug("Left %.2fdeg %d%% about %s", degree, speed, pivot)
        r_dist, l_dist = self._calc_driving_dist(degree, pivot)
        return self._drive(self.l_wheel.backward, self.r_wheel.forward,
                           l_dist, r_dist, speed, async)

    def _drive(self, l_action, r_action, l_dist, r_dist, speed, async):
        time1 = self.l_wheel.calc_wait_time(l_dist, speed)
        time2 = self.r_wheel.calc_wait_time(r_dist, speed)
        def run():
            self.log.debug("Waiting %.4f on left, %.4f on right", time1, time2)
            l_action(speed)
            r_action(speed)
            time.sleep(min(time1, time2))
            if time1 > time2:
                self.r_wheel.stop()
            elif time1 < time2:
                self.l_wheel.stop()
            time.sleep(abs(time1 - time2))
            self.l_wheel.stop()
            self.r_wheel.stop()
        if not async:
            run()
            return lambda: None
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        return thread.join

    def _calc_driving_dist(self, degree, pivot):
        from main import Robot
        if pivot not in ['wheel', 'center']:
            raise Execption("Invalid pivot %r" % pivot)
        dist = (math.pi * Robot.WHEEL_SPAN * abs(degree)) / 360
        if pivot == 'wheel':
            return dist * 2, 0
        elif pivot == 'center':
            return dist, dist
