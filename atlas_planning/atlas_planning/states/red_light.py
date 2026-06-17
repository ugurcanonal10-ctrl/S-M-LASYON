"""
Kirmizi Isik State
- Sartnameye gore 0-5 m araliginda dur (60 puan)
- Erken durma: 20 puan, isik gecme: -30 puan
"""

from .base_state import BaseState, StateID


class RedLightState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.RED_LIGHT, logger)

    def on_enter(self):
        super().on_enter()
        if self.logger:
            self.logger.info('[RedLight] Dur komutu gonderiliyor.')

    def execute(self, context: dict):
        # Yamuk hiz profili ile 0-5 m araliginda dur
        # velocity_planner_node bu komutu islenir
        pass

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        if context.get('traffic_light') == 'green':
            return StateID.GREEN_LIGHT

        return None
