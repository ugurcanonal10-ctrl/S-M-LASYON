"""
Acil Durdurma State
- UMS-1 sinyali veya kritik hata ile tetiklenir
- Arac 2 metre icinde durur
- Son state: hicbir yere gecis yok
"""

from .base_state import BaseState, StateID


class EmergencyStopState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.EMERGENCY_STOP, logger)

    def on_enter(self):
        super().on_enter()
        if self.logger:
            self.logger.error('[EMERGENCY] ACİL DURDURMA! '
                              'Arac 2m icinde duruyor.')

    def execute(self, context: dict):
        pass  # Dur komutu behavior_monitor_node uzerinden gonder

    def check_transitions(self, context: dict):
        return None  # Son state, gecis yok
