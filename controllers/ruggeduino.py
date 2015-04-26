"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

from sr.robot.ruggeduino import (INPUT,
                                OUTPUT,
                                INPUT_PULLUP)

PIN_TYPES = {  # mode, signal_type {digital or analogue}
     'ARM_SWITCH': (INPUT_PULLUP, 'digital'),
     'FLAG_SENSOR': (INPUT_PULLUP, 'digital'),
     'BUMP': (INPUT_PULLUP, 'digital'),
     'SOURCES': (OUTPUT, 'digital')
}

_SERIAL_MAIN = '75230313833351311051'

PIN_MAP = {  # type: (board_serial, identifier: pin_no)
    'ARM_SWITCH': (_SERIAL_MAIN, {
        'SW1': 2
    }),
    'BUMP': (_SERIAL_MAIN, {
        'FL': 8,
        'FR': 6,
        'FM': 4
    }),
    'FLAG_SENSOR': (_SERIAL_MAIN, {
        'PLATE': 10
    }),
    'SOURCES': (_SERIAL_MAIN, {
        'ARM_SW': 3,
        'F_SENS_PL': 11,
        'BUMP_FR': 7,
        'BUMP_FL': 9,
        'BUMP_FM': 5
    })
}

class RuggeduinoController:
    def __init__(self, robot, type, id):
        type = type.upper()
        if type in PIN_MAP:
            map = PIN_MAP[type]
        else:
            raise TypeError("Unknown ruggeduino type %s" % type)

        if id not in map[1].keys():
            raise TypeError("Invalid or no id for ruggeduino definition")
        pin = map[1][id]

        ruggeduino = robot.ruggeduinos[map[0]]
        if not ruggeduino._is_srduino():
            raise TypeError("Must be an SR ruggeduino")

        info = PIN_TYPES[type]
        if pin in (0, 1) and info[1] == 'digital':
            raise IndexError("Cannot use pin %d as it is reserved internally" %
                             pin)
        if info[1] not in ('analogue', 'digital'):
            raise TypeError("Unknown signal type %r" % info[1])

        ruggeduino.pin_mode(pin, info[0])
        name = 'write' if info[0] == OUTPUT else 'read'
        self.is_output = name == 'write'
        self.is_input = not self.is_output
        function = '%s_%s' % (info[1], name)
        if function == 'analogue_write':
            raise NotImplementedError("Writing to analogue output not possible")
        method = getattr(ruggeduino, function)
        invert = info[0] == INPUT_PULLUP and info[1] == 'digital'
        self._ruggeduino = (method, pin, invert)
        def toString():
            return  "Ruggeduino(%s.%s)" % (type, id)
        self.__str__ = toString
        self.__repr__ = self.__str__

    def _run(self, *args):
        value = self._ruggeduino[0](*(self._ruggeduino[1],) + args)
        if self._ruggeduino[2]: value = not value
        return value

    def read(self):
        """Returns the value of the pin, float for analogue - the voltage,
        and boolean for digital - True for high and False for low."""
        if not self.is_input:
            raise TypeError("Trying to read a non-input pin")
        return self._run()

    def write(self, value):
        """Write a value to the pin,
        boolean only - True for high and False for low."""
        if not self.is_output:
            raise TypeError("Trying to write to a non-output pin")
        return self._run(value)
