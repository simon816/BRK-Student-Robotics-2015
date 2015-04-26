"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import logging
import math

from controllers.ruggeduino import RuggeduinoController
from systems.vision import VisionSystem
from systems.movement import MovementSystem
from systems.mech import MechSystem
from threads import RobotThreads

class Robot:

    WHEEL_SPAN = 0.4

    def __init__(self, srBot):
        self.log = logging.getLogger('Robot')
        self.log.info("Initializing")
        try:
            self.camera = VisionSystem(srBot)
            self.wheels = MovementSystem(srBot)
            self.arm = MechSystem(srBot)
        except:
            self.log.critical("Critical error when setting-up systems")
            raise
        self.log.debug("Setup switch sources")
        for source in ['ARM_SW', 'F_SENS_PL', 'BUMP_FR', 'BUMP_FL', 'BUMP_FM']:
            RuggeduinoController(srBot, type='sources', id=source).write(False)
        self._configure_bump_sensors(srBot)
        self.flag_sens = RuggeduinoController(srBot, type='flag_sensor',
                                              id='PLATE')
        self.threads = RobotThreads(self)
        self.running = True
        self.threads.run()
        self.log.info("Done")

    def _configure_bump_sensors(self, srBot):
        fl = RuggeduinoController(srBot, type='bump', id='FL')
        fr = RuggeduinoController(srBot, type='bump', id='FR')
        fm = RuggeduinoController(srBot, type='bump', id='FM')
        self.bump = {
            'front': {
                'left': fl,
                'right': fr,
                'middle': fm
            },
            'back': {},
            'left': {
                'front': fl
            },
            'right': {
                'front': fr
            },
            '__all__': [fl, fr, fm]
        }

    def is_bumping(self):
        for sensor in self.bump['__all__']:
            if sensor.read():
                return sensor
        return False

    def stop(self):
        self.log.info("Stopping all communications")
        self.running = False

    def goto_marker(self, marker, speed, assumed_close=0.6, filter_func=None):
        """Attempts to go to the given marker.
        assumed_close is a number that defines the maximum distance a marker can
        be before assuming the robot is too close to see the marker.
        filter_func is a callable that is applied to the markers found,
        see MarkerCollection#filter. If None, it will match markers with the
        same code.
        Note: Because this assumes the camera can't see a marker closer than
        assumed_close, the method may never exit if assumed_close is too small.
        Returns True on success, False if it could not go to the marker."""
        self.log.debug("going to marker %s %.1f%% assuming %.1f is close",
                       marker, speed, assumed_close)
        if filter_func is None:
            filter_func = lambda m: m.info.code == marker.info.code
        if not callable(filter_func):
            raise TypeError("Filter function must be callable")
        mhelper = VisionSystem.get_helper_for(marker)
        h_dist = mhelper.horizontal_dist
        travel_dist = h_dist / 2.0
        if marker.rot_y < 0:
            self.wheels.left(marker.rot_y, speed)
        else:
            self.wheels.right(marker.rot_y, speed)
        self.wheels.forward(travel_dist, speed)
        new_marker = self.camera.get_markers().filter(filter_func).get_closest()
        if new_marker is None:
            if travel_dist < assumed_close:
                # OK, we are close enough to the target marker.
                # Go forwards the remaining half distance
                self.log.debug("Assuming the remaining distance is close, %.2f",
                               travel_dist)
                self.wheels.forward(travel_dist, speed)
                return True
            self.log.debug("Lost marker and it's not assumed to be close, %.2f",
                           travel_dist)
            return False
        return self.goto_marker(new_marker, speed, assumed_close, filter_func)

    def face_marker(self, marker, speed):
        """Faces the given marker."""
        self.log.debug("Facing marker %s at %.1f%%", marker, speed)
        if marker.rot_y < 0:
            self.wheels.left(marker.rot_y, speed)
        else:
            self.wheels.right(marker.rot_y, speed)
        return
        m_orient = abs(marker.orientation.rot_y)
        if m_orient < 0:
            self.log.debug("Going left then right")
            turn_1 = self.wheels.left
            turn_2 = self.wheels.right
        else:
            self.log.debug("Going right then left")
            turn_1 = self.wheels.right
            turn_2 = self.wheels.left
        deg1 = abs(marker.rot_y)
        deg2 = m_orient * 0.5
        dist = (0.5 * marker.dist) / abs(math.cos(math.radians(m_orient)))
        turn_1(deg1, speed)
        self.wheels.forward(dist, speed)
        turn_2(deg2, speed)

    def navigate_to_marker(self, marker, speed, comparator=None):
        """TODO: Revise this method and write docstring"""
        self.log.debug("navigating to marker")
        self.face_marker(marker, speed) # face the marker
        markers = self.camera.get_markers() # rescan for the marker
        new_markers = markers.filter(lambda m: m.info.code == marker.info.code)
        if new_markers.is_empty:
            self.log.warning("Could not find marker after facing")
            return False
        self.log.debug("Found marker, continuing")
        marker = new_markers.get_closest()
        if self.goto_marker(marker, speed, filter_func=comparator):
            return True
        markers = self.camera.get_markers() # rescan for the marker
        new_markers = markers.filter(lambda m: m.info.code == marker.info.code)
        if new_markers.is_empty:
            self.log.warning("Could not find marker after trying to go to it")
            return False
        self.log.debug("Found marker again, continuing")
        marker = new_markers.get_closest()
        return self.navigate_to_marker(marker, speed, comparator)

    def find_flag(self, wall_boundary, speed):
        self.log.debug("Finding flag within the bounds %s", wall_boundary)
        turned180 = False
        result = {'result': None}
        while True:
            markers = self.camera.get_markers()
            flags = markers.filter(lambda m: m.info.marker_type == 'flag')
            walls = markers.filter(lambda m: m.info.marker_type == 'arena')
            if wall_boundary is not None:
                walls = walls.filter(lambda m: m.info.code in wall_boundary)
            if walls.is_empty:
                self.log.info("No walls found")
                #if turned180:
                #    result['result'] = 'lost'
                #    break
                self.wheels.right(20, speed / 1.5)
                if self.is_bumping():
                    self.log.info("Bumped, reverse")
                    self.wheels.backward(0.3, 60)
                    self.wheels.left(30, speed)
                #self.wheels.right(180, speed)
                #turned180 = True
                continue
            if flags.is_empty or flags.get_closest().dist > 4:
                w_marker = walls.get_closest_rotation(180) # get_closest()
                if w_marker is not None and w_marker.dist < 2:
                    self.log.info("Wall far")
                    self.wheels.right(20, speed / 1.5)
                    if self.is_bumping():
                        self.log.info("Bumped, reverse")
                        self.wheels.backward(0.7, speed)
                        self.wheels.left(30, speed)
                    continue
                if w_marker is not None:
                    dist = w_marker.dist / 3
                    self.log.info("No flags nearby, heading closer %.2f", w_marker.rot_y)
                    self.face_marker(w_marker, speed)
                    self.log.info("driving %.2fm", dist)
                    self.wheels.forward(dist, speed)
                    if self.is_bumping():
                        self.wheels.backward(0.5, speed)
                        self.wheels.left(20, speed)
                else:
                    self.log.info("Turn right 20")
                    self.wheels.right(20, speed / 1.5)
                    if self.is_bumping():
                        self.log.info("Bumped, reverse")
                        self.wheels.backward(0.7, speed)
                        self.wheels.left(30, speed)
                continue
            flag = flags.get_closest()
            self.log.info("Seen flag %s", flag)
            nav_success = self.navigate_to_marker(flag, speed)
            result['result'] = 'navigating'
            result['nav_success'] = nav_success
            result['flag_code'] = flag.info.code
            result['flag'] = flag
            break
        return result
