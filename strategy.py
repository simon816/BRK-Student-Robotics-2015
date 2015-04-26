"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import logging

from event_bus import EventBus

class StrategyRegistry:

    reg = {}

    @staticmethod
    def get(name):
        return StrategyRegistry.reg[name]

    @staticmethod
    def set(name, strat):
        StrategyRegistry.reg[name] = strat


class Strategy:
    def get_states(self):
        return {'MAIN': lambda:None}

    def set_game_util(self, game):
        self.sm = game.sm
        self.bot = game.robot
        self.log = logging.getLogger('Robot.Strategy')
        self.corner = game.corner
        self.corners = game.corners
        self._game = game



class Strategy1(Strategy):

    def get_states(self):
        return {
            'MAIN': self.start,
            'DROP_OWN_FLAG': self.drop_against_barrier,
            'STEAL': self.steal_flag,
            'GO_BACK': self.back_to_zone
        }

    def flag_touch(self):
        pass

    def start(self):
        EventBus.GLOBAL.unregister('bump', self._game.handle_bump)
        EventBus.GLOBAL.register('flag_plate_touch', self.flag_touch)
        self.left_corner = (self.corner + 1) % 4
        self.right_corner = (self.corner - 1) % 4
        own_marker = self.bot.camera.get_markers(sleep=False).filter(
            lambda m: m.info.marker_type == 'flag').get_closest()
        self.own_marker_code = own_marker.info.code \
            if own_marker is not None else -1
        self.bot.wheels.forward(2, 60)
        self.bot.arm.down()
        self.bot.wheels.left(60, 60)
        self.bot.wheels.forward(1.5, 60)
        self.sm.set_state('DROP_OWN_FLAG')

    def drop_against_barrier(self):
        self.bot.arm.up()
        self.bot.wheels.backward(0.5, 60)
        EventBus.GLOBAL.register('bump', self._game.handle_bump)
        self.bot.wheels.left(90, 60)
        close_wall = self.bot.camera.get_markers().filter(
            lambda m: m.info.marker_type == 'arena').get_closest()
        if close_wall is not None:
            self.bot.wheels.forward(close_wall.dist - 0.4, 60)
        else:
            self.bot.wheels.forward(1.2, 60)
        self.bot.wheels.right(60, 60)
        self.bot.wheels.forward(1.3, 60)
        self.back_out_if_bumping()
        self.sm.set_state('STEAL', [self.corners[self.left_corner]])

    def steal_flag(self, arena_markers):
        result = self.bot.find_flag(arena_markers, 60)
        if result['result'] == 'navigating':
            if result['nav_success']:
                if self.bot.flag_sens.read():
                    self.sm.set_state('GO_BACK')
                else:
                    self.log.info("Navigated to marker, not touching")
                    self.bot.wheels.forward(0.5, 60)
                    if self.bot.flag_sens.read():
                        self.sm.set_state('GO_BACK')
                    else:
                        self.log.warn("Flag not touching, turn a bit")
                        if 'flag' in result:
                            deg = result['flag'].rot_y
                        else:
                            deg = 7
                        if deg < 0:
                            self.bot.wheels.left(deg * 1.5, 50, pivot='wheel')
                        else:
                            self.bot.wheels.right(deg * 1.5, 50, pivot='wheel')
                        self.sm.set_state('GO_BACK')
            else:
                self.log.info("Navigation failed")
                self.bot.wheels.right(15, 60)
                self.steal_flag(arena_markers)
        else:
            self.log.info("Not navigating")
            self.bot.wheels.right(10, 30)
            self.bot.wheels.forward(0.3, 60)
            self.back_out_if_bumping()
            self.steal_flag(None)

    def back_to_zone(self):
        arm_wait = self.bot.arm.down(async=True)
        c_pivot_wait = self.bot.camera.look_behind(async=True)
        arm_wait()
        c_pivot_wait()
        self.bot.wheels.backward(1, 80)
        walls = self.corners[self.corner]
        markers = self.bot.camera.get_markers().filter(
            lambda m: m.info.code in walls)
        if markers.is_empty:
            self.log.info("No home walls found")
            self.bot.wheels.left(20, 60)
            self.bot.wheels.backward(1, 60)
            self.back_out_if_bumping()
            self.back_to_zone()
        else:
            target_wall = markers.get_closest()
            if target_wall.rot_y < 0:
                self.bot.wheels.right(target_wall.rot_y, 60)
            else:
                self.bot.wheels.left(target_wall.rot_y, 60)
            #self.bot.face_marker(target_wall, 60)
            self.bot.wheels.backward(target_wall.dist - 0.5, 60)
            new_m_wall = self.bot.camera.get_markers().filter(
                lambda m: m.info.code == target_wall.info.code).get_closest()
            if new_m_wall is None:
                self.bot.wheels.left(20, 50)
                self.bot.wheels.backward(0.3, 60)
                self.back_to_zone()
                return
            self.bot.arm.up()
            c_pivot_wait = self.bot.camera.look_forward(async=True)
            self.bot.wheels.right(60, 60)
            c_pivot_wait()
            self.bot.wheels.forward(2, 60)
            self.back_out_if_bumping()
            self.sm.set_state('STEAL', [self.corners[self.right_corner]])

    def back_out_if_bumping(self):
        if self.bot.is_bumping():
            self.log.info("Bumped, go back")
            self.bot.wheels.backward(0.4, 60)
            self.bot.wheels.right(30, 60)

class TestMode(Strategy):
    def get_states(self):
        return {
            'MAIN': self.test
        }

    def test(self):
        self.bot.wheels.forward(1, 70)

StrategyRegistry.set('STRAT_1', Strategy1())
StrategyRegistry.set('TESTS', TestMode())
