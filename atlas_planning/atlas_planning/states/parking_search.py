"""
Park Yeri Arama State
- Park bolgesine girilir, uygun bos yer aranir
- Yer bulununca Park Manuvrasina gec
- Bulunamazsa dongu (ayni state'te kal)
"""

from .base_state import BaseState, StateID


class ParkingSearchState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.PARKING_SEARCH, logger)
        self._spot_found = False

    def on_enter(self):
        super().on_enter()
        self._spot_found = False
        if self.logger:
            self.logger.info('[ParkingSearch] Park yeri aranıyor.')

    def execute(self, context: dict):
        if context.get('parking_spot_available'):
            self._spot_found = True

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        if self._spot_found:
            return StateID.PARKING_MANEUVER

        return None  # Dongu: ayni state'te kal
