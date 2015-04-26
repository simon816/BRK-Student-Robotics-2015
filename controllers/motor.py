"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import math

# TODO
MOTOR_RPM = {  # model: RPM
    '919D1481': 106, # Quoted value = 106,
    '918D151': 2416 # Quoted value = 2416
}

MOTOR_MAP = {
    'WHEEL': {
        'motor_model': '919D1481',
        'sr_serial': 'SR0UF7',
        'diameter': 0.1013,
        'type_ids': {
            'LEFT': {'channel': 0, 'rpmoffset': 0},
            'RIGHT': {'channel': 1, 'rpmoffset': -2}
        }
    },
    'ARM': {
        'motor_model': '918D151',
        'sr_serial': 'SR0RF9',
        'diameter': 0.01, # TODO Get actual measurements
        'type_ids': {
            'MAIN': {'channel': 0, 'rpmoffset': 0}
        }
    }
}

class MotorController(object):
    def __init__(self, robot, type, id):
        if type in MOTOR_MAP:
            info = MOTOR_MAP[type]
        else:
            raise TypeError("Unknown motor type %s" % type)
        self.diameter = info['diameter']
        if id not in info['type_ids'].keys():
            raise TypeError("Invalid or no id for motor definition")
        board = robot.motors[info['sr_serial']]
        channel = info['type_ids'][id]['channel']
        self.RPM = MOTOR_RPM[info['motor_model']] + info['type_ids'][id]['rpmoffset']
        self._motor = self._get_channel(board, channel)
        self.opp_dir = 0

    def _get_channel(self, board, channel):
        if not hasattr(board, 'm%d' % channel):
            raise TypeError("Unknown channel %d" % channel)
        return getattr(board, 'm%d' % channel)

    def forward(self, speed):
        if speed == 0: return self.stop()
        self.opp_dir = -1
        self._motor.power = abs(speed)

    def backward(self, speed):
        if speed == 0: return self.stop()
        self.opp_dir = 1
        self._motor.power = -abs(speed)

    def stop(self):
        self._motor.power = self.opp_dir
        self.opp_dir = 0

    def get_circumference(self):
        """Get circumference of motor wheel/rod using pre-defined
        diameter table."""
        return self.diameter * math.pi

    def get_rotations(self, seconds):
        """Return how many rotations would occur in the given seconds
        using pre-defined RPM table."""
        return (self.RPM / 60.0) * seconds

    def calc_distance(self, time, speed):
        """Calculate the expected distance moved in
        t seconds at d% speed."""
        circumference = self.get_circumference()
        revolutions = self.get_rotations(time)
        return circumference * revolutions * (speed / 100.0)

    def calc_wait_time(self, dist, speed):
        """Calculate the delay it takes to travel dist at d% speed."""
        dist, speed = abs(dist), abs(speed)
        return (6000 * dist) / (self.RPM * self.get_circumference() * speed)

    def calc_rpm(self, duration, actual_dist, speed):
        """
        Calculate the true RPM of the motor given the duration of the journey,
        the actual distance traveled and the speed as a percentage.
        The diameter of the circle that drives the movement (i.e wheel) must be
        known.

        Use this in testing to correct the RPM stated above.
        """

        return (6000*actual_dist) / (duration*self.get_circumference()*speed)
