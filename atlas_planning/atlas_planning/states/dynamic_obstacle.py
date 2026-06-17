"""
Dinamik Engel State
- Hareketli nesneyi bekle, etrafından gec ya da hizini dusur
- Engel gecinece Serit Takibi'ne don
"""

from .base_state import BaseState, StateID


class DynamicObstacleState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.DYNAMIC_OBSTACLE, logger)
        self._cleared = False

    def on_enter(self):
        super().on_enter()
        self._cleared = False
        if self.logger:
            self.logger.info('[DynamicObstacle] Dinamik engel bekleniyor.')

    def execute(self, context: dict):
        if context.get('obstacle_type') != 'dynamic':
            self._cleared = True

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        if self._cleared:
            return StateID.LANE_FOLLOW

        return None
