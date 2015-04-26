"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import logging
import threading
import time

from controllers.motor import MotorController
from controllers.ruggeduino import RuggeduinoController

class MechSystem:
    def __init__(self, srBot):
        self.log = logging.getLogger('Robot.Mech')
        self.log.debug("Setup motor controller")
        try:
            self.motor = MotorController(srBot, type='ARM', id='MAIN')
            self.switch = RuggeduinoController(srBot, type='arm_switch',
                                               id='SW1')
        except Exception as e:
            self.log.exception(e)
            raise e

    def up(self, async=False):
        """Moves the arm to the up position.
        See MovementSystem#forward for info on the async parameter."""
        self.log.debug("Move arm up")
        def run():
            self.motor.backward(80)
            while self.switch.read():
                time.sleep(0.1)
            time.sleep(2.2)
            self.motor.stop()
        return self._do(run, async)

    def down(self, async=False):
        """Moves the arm to the down position.
        See MovementSystem#forward for info on the async parameter."""
        self.log.debug("Move arm down")
        def run():
            self.motor.forward(90)
            stop_time = time.time() + 2
            while not self.switch.read() and time.time() < stop_time:
                time.sleep(0.1)
            self.motor.stop()
        return self._do(run, async)

    def _do(self, run, async):
        if not async:
            run()
            return lambda: None
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        return thread.join
