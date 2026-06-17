"""
Yolcu Indirme State - v2
"""

import time
from .base_state import BaseState, StateID

WAIT_DURATION_SEC = 17.0


class PassengerDropoffState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.PASSENGER_DROPOFF, logger)
        self._enter_time = None
        self._done = False

    def on_enter(self):
        super().on_enter()
        self._enter_time = time.time()
        self._done = False
        if self.logger:
            self.logger.info(f'[Dropoff] Bekleniyor: {WAIT_DURATION_SEC}s')

    def on_exit(self):
        super().on_exit()
        self._done = False

    def execute(self, context: dict):
        elapsed = time.time() - self._enter_time if self._enter_time else 0
        if elapsed >= WAIT_DURATION_SEC:
            self._done = True

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        if self._done:
            return StateID.LANE_FOLLOW

        return None
