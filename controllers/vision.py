"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import math

from sr.robot.vision import (MARKER_ARENA,
                       MARKER_ROBOT,
                       MARKER_FLAG)

DEFAULT_RESOLUTION = (960, 720)

# TODO
CAMERA_HEIGHT = 0.5 # Height in meters for the elevation above the ground

class VisionController(object):
    def __init__(self, robot):
        self.res = DEFAULT_RESOLUTION
        self._see = robot.see
        self._stats = {
            'cam_init': [],
            'capture': [],
            'img_scan': []
        }

    def find_markers(self):
        markers, timings = self._see(self.res, True)
        self._record_timings(timings)
        return markers

    def _record_timings(self, times):
        self._stats['cam_init'].append(times['cam'])
        self._stats['capture'].append(times['yuyv'])
        self._stats['img_scan'].append(times['find_markers'])

    def print_stat(self):
        timesvars = [[]] * 3
        timesvars[0] = self._stats['cam_init']
        timesvars[1] = self._stats['capture']
        timesvars[2] = self._stats['img_scan']
        averages = []
        for times in timesvars:
            avg = 0
            for time in times:
                avg += time
            avg /= float(len(times))
            averages.append(avg)
        print "It took %f seconds for camera to initialize" % averages[0]
        print "It took %f seconds to capture the image" % averages[1]
        print "It took %f seconds to scan for libkoki markers" % averages[2]

    def change_resolution(self, new_res):
        if type(new_res) == tuple and len(new_res) == 2:
            if type(new_res[0]) == int and type(new_res[1]) == int:
                self.res = new_res
                return True
        return False

class MarkerHelper:
    # A marker helper class
    def __init__(self, marker):
        self.marker = marker

    def get_center_height(self):
        height = self.marker.info.size / 2
        if self.marker.info.marker_type == MARKER_ARENA:
            # Figure 4: The markers are placed 50mm above the floor.
            height += 0.05
        elif self.marker.info.marker_type == MARKER_FLAG:
            # Section 3.5.3: ground clearance of 10mm.
            height += 0.01
        elif self.marker.info.marker_type == MARKER_ROBOT:
            # A robot has a max height of 0.5m, best guess is to assume the
            # badge is half that height
            height += 0.25
        return height

    @property
    def horizontal_dist(self):
        square = (self.marker.dist ** 2) - (self.vertical_height ** 2)
        if square < 0: return 0
        return math.sqrt(square)

    @property
    def vertical_height(self):
        # Returns the height of the marker from the camera
        return CAMERA_HEIGHT - self.get_center_height()

    def __str__(self):
        return "MarkerHelper(rotation=%.2f, distance=%.2f, orientation=%s)" % (
            self.marker.rot_y, self.horizontal_dist, self.marker.orientaton)

    def __repr__(self):
        return repr(self.marker)

