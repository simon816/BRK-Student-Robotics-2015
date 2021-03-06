"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

SERVO_MAP = { # type: (Min rotation, Max rotation, servo board, servo slot)
    'CAMERA_PIVOT': (-100, 62, 0, 0)
}

class ServoController(object):
    def __init__(self, robot, type):
        if type.upper() in SERVO_MAP:
            data = SERVO_MAP[type.upper()]
        else:
            raise TypeError("Unknown servo type %s" % type)

        board, slot = data[2:4]
        if len(robot.servos) - 1 < board:
            raise IndexError("Unknown servo board %d" % board)
        if slot < 0 or slot > 7:
            raise IndexError("There are only 8 servo outputs on a servo board")
        self._servo = (robot.servos[board], slot)
        self.MIN, self.MAX = data[:2]

    def set_angle(self, angle):
        if angle < self.MIN or angle > self.MAX:
            raise ValueError("Cannot set angle greater or less than max or min")
        self._servo[0][self._servo[1]] = angle

    def get_angle(self):
        angle = self._servo[0][self._servo[1]]
        if angle < self.MIN:
            self.set_angle(self.MIN)
            angle = self.MIN
        elif angle > self.MAX:
            self.set_angle(self.MAX)
            angle = self.MAX
        return angle
