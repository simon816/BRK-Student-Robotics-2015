"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import logging
import math
import time
import threading

from controllers.vision import VisionController, MarkerHelper
from controllers.servo import ServoController
from event_bus import EventBus

class MarkerCollection:
    EMPTY = None

    def __init__(self, markers):
        self._markers = markers
        self.is_empty = len(markers) == 0

    def get_closest(self):
        """Gets the closest marker in this collection by distance."""
        return self._target_dist(lambda a, b: a < b)

    def get_farthest(self):
        """Gets the farthest marker in this collection by distance."""
        return self._target_dist(lambda a, b: a > b)

    def _target_dist(self, comp_func):
        if self.is_empty:
            return None
        target = self._markers[0]
        for marker in self._markers:
            if comp_func(marker.dist, target.dist):
                target = marker
        return target

    def get_closest_rotation(self, degree=0):
        """Gets the marker closest to the given degree in this collection."""
        if self.is_empty:
            return None
        getrad = lambda d: math.radians(abs(d - 180))
        while degree > 180:
            degree = degree - 360
        target = getrad(degree)
        closest = (math.pi, self._markers[0])
        for marker in self._markers:
            diff = abs(target - getrad(marker.rot_y))
            if diff < closest[0]:
                closest = (diff, marker)
        return closest[1]

    def filter(self, func):
        """Gets the collection of markers that match the given filter.
        The func parameter must be callable and return a boolean."""
        if not callable(func):
            raise TypeError("Filter parameter must be callable")
        if self.is_empty:
            return self
        markers = filter(func, self._markers)
        if len(markers) == 0:
            return MarkerCollection.EMPTY
        return MarkerCollection(markers)

    def __str__(self):
        if self.is_empty:
            return "MarkerCollection.EMPTY"
        def format_marker(marker):
            return ("Marker(code=%d, type=%s, dist=%f rot_y=%f " \
                    + "orientation(rot_y=%f))") % (marker.info.code,
                                                  marker.info.marker_type,
                                                  marker.dist, marker.rot_y,
                                                  marker.orientation.rot_y)
        return str(map(format_marker, self._markers))

MarkerCollection.EMPTY = MarkerCollection([])

class VisionSystem:
    def __init__(self, srBot):
        self.log = logging.getLogger('Robot.Vision')
        self.log.debug("Setup vision and servo controller")
        try:
            self.camera = VisionController(srBot)
            self.pivot = ServoController(srBot, type='CAMERA_PIVOT')
        except Exception as e:
            self.log.exception(e)
            raise e
        self._forward = False
        self.look_forward()

    def get_markers(self, sleep=True):
        """Gets a collection of markers that the robot can currently see."""
        if sleep:
            time.sleep(0.5)
        markers = self.camera.find_markers()
        if len(markers) == 0:
            collection = MarkerCollection.EMPTY
        else:
            collection = MarkerCollection(markers)
        self.log.debug("Found markers: %s", collection)
        EventBus.GLOBAL.post('markers', collection)
        return collection

    def look_forward(self, async=False):
        """Rotates the camera to look forwards, if not already."""
        self.log.debug("Look forward")
        if self._forward:
            self.log.debug("Already looking forwards")
            return lambda: None
        return self._do(True, async)

    def look_behind(self, async=False):
        """Rotates the camera to look backward, if not already."""
        self.log.debug("Look behind")
        if not self._forward:
            self.log.debug("Already looking behind")
            return lambda: None
        return self._do(False, async)

    def _do(self, forward, async):
        angle = self.pivot.MAX if forward else self.pivot.MIN
        def run():
            self.pivot.set_angle(angle)
            time.sleep(0.5) # TODO get minimum time
            self._forward = forward
        if not async:
            run()
            return lambda: None
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        return thread.join

    def is_forward(self):
        """Gets whether the camera is facing forwards."""
        return self._forward

    @staticmethod
    def get_helper_for(marker):
        """Gets the helper object for the given marker object."""
        if isinstance(marker, MarkerHelper):
            return marker
        return MarkerHelper(marker)
