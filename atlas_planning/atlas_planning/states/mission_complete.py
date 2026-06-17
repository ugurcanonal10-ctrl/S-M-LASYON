"""
Gorev Tamamlandi State
- Park basariyla yapildi
- Son state: hicbir yere gecis yok
"""

from .base_state import BaseState, StateID


class MissionCompleteState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.MISSION_COMPLETE, logger)

    def on_enter(self):
        super().on_enter()
        if self.logger:
            self.logger.info('[MISSION] Gorev basariyla tamamlandi!')

    def execute(self, context: dict):
        pass

    def check_transitions(self, context: dict):
        return None  # Son state, gecis yok
