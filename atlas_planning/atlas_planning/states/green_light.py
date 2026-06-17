"""
Yesil Isik State
- Isik yesile donunce 5 saniye icinde harekete gec
- Kavsak gecilince Serit Takibi'ne don
"""

import time
from .base_state import BaseState, StateID

GREEN_TIMEOUT_SEC = 5.0


class GreenLightState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.GREEN_LIGHT, logger)
        self._enter_time = None

    def on_enter(self):
        super().on_enter()
        self._enter_time = time.time()

    def execute(self, context: dict):
        pass  # Hareket baslat

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        elapsed = time.time() - self._enter_time if self._enter_time else 0
        if elapsed >= GREEN_TIMEOUT_SEC or context.get('intersection_cleared'):
            return StateID.LANE_FOLLOW

        return None
