"""
    This file is part of Team BRK '404 (Robot Not Found)', licensed under the
    MIT License. A copy of the MIT License can be found in LICENSE.txt
"""

import logging

from state_utils import StateMachine, StateInterrupt
from event_bus import EventBus
from strategy import StrategyRegistry

class PlayGame:
    def __init__(self, robot, corner):
        self.log = logging.getLogger('Robot.Logic')
        self.robot = robot
        self.corner = corner
        self.corners = [
            range(0, 4) + range(24, 28),
            range(3, 11),
            range(11, 18),
            range(18, 25)
        ]
        self.startup()

    def AdjDir(self, Dir):
        if self.corner in [0, 2]:
            return Dir
        self.log.info("Adjusted direction (from %s)", str(Dir))
        return Left if Dir is Right else Right

    def startup(self):
        strategy = StrategyRegistry.get('STRAT_1')
        self.sm = StateMachine(strategy.get_states())
        self.sm.bus.register('change', self.state_changed)
        self.sm.bus.register('error', self.state_error)
        self.sm.bus.register('finish', self.state_finished)
        self.sm.bus.register('interrupt', self.state_interrupted)
        EventBus.GLOBAL.register('markers', self.handle_markers)
        EventBus.GLOBAL.register('bump', self.handle_bump)
        EventBus.GLOBAL.register('__bus_error__', self.handle_bus_error)
        self.sm.bus.register('__bus_error__', self.handle_bus_error)
        self.reset()
        strategy.set_game_util(self)
        for state in self.sm.next_state():
            self.sm.change_state(state)

    def set_state(self, state, *args):
        self.sm.set_state(state, args)

    def state_changed(self, payload):
        fromstate, tostate = payload
        self.log.info("State Changed from %s to %s", fromstate, tostate)

    def state_error(self, payload):
        state, errors = payload
        self.log.error(str(state) + " encountered errors")
        for e in errors:
            self.log.exception(e['exception'])

    def state_finished(self, state):
        self.log.info(str(state) + " finished")

    def state_interrupted(self, payload):
        state, ex = payload
        self.log.info("%s was interrupted, %s", state, ex)

    def reset(self):
        self.sm.set_state("MAIN")

    def handle_bus_error(self, payload):
        channel, handler, exception = payload
        if isinstance(exception, StateInterrupt):
            raise exception
        self.log.error("Error occured when handling the channel '%s'" \
                       + " in the handler %s", channel, handler)
        self.log.exception(exception)

    def handle_markers(self, markers):
        self.log.debug("Handling marker scan")
        currstate = self.sm.get_active_state().name
        obsticles = markers \
            .filter(lambda m: m.info.marker_type in ['robot', 'arena']) \
            .filter(lambda m: m.dist < 0.4)
        if obsticles.is_empty:
            return
        nearest_obsticle = obsticles.get_closest()
        def on_interrupt(payload):
            self.sm.bus.unregister('interrupt', on_interrupt)
            self.log.info("Move away")
            self.robot.wheels.backward(0.9, 50)
            self.robot.wheels.right(10, 50)
        self.sm.bus.register('interrupt', on_interrupt)
        self.log.info("Obsticle found, %s", nearest_obsticle)
        raise StateInterrupt('stop', 'operation.stop')

    def handle_bump(self, sensors):
        self.log.warn("Bumped on sensors %s", sensors)
        self.robot.wheels.backward(0.7, 60)
        self.robot.wheels.left(30, 60)
