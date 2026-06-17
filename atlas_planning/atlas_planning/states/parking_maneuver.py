"""
Park Manuvrasi State
- Dik park yapilir, tekerlekler serit disina tasmaZ
- Maksimum 3 dakika
- Park tamamlaninca Gorev Tamamlandi
"""

import time
from .base_state import BaseState, StateID

MAX_PARK_DURATION_SEC = 180.0  # 3 dakika


class ParkingManeuverState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.PARKING_MANEUVER, logger)
        self._enter_time = None
        self._park_complete = False

    def on_enter(self):
        super().on_enter()
        self._enter_time = time.time()
        self._park_complete = False
        if self.logger:
            self.logger.info('[ParkingManeuver] Park manuvrasi basliyor. '
                             'Limit: 3 dk')

    def execute(self, context: dict):
        if context.get('parking_complete'):
            self._park_complete = True

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        elapsed = time.time() - self._enter_time if self._enter_time else 0

        if self._park_complete:
            return StateID.MISSION_COMPLETE

        if elapsed >= MAX_PARK_DURATION_SEC:
            if self.logger:
                self.logger.warn('[ParkingManeuver] Sure asimi! Acil durma.')
            return StateID.EMERGENCY_STOP

        return None
