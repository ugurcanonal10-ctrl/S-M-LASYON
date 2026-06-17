"""
Statik Engel State
- DWA algoritmasi ile engel etrafinda guvenli rota hesapla
- Gecilirse Serit Takibi, gecileemezse Acil Durdurma
"""

from .base_state import BaseState, StateID


class StaticObstacleState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.STATIC_OBSTACLE, logger)
        self._cleared = False
        self._failed = False

    def on_enter(self):
        super().on_enter()
        self._cleared = False
        self._failed = False
        if self.logger:
            self.logger.info('[StaticObstacle] DWA baslatiliyor.')

    def execute(self, context: dict):
        # DWA sonucu local_planner_node'dan gelir
        dwa_result = context.get('dwa_result', '')
        if dwa_result == 'cleared':
            self._cleared = True
        elif dwa_result == 'failed':
            self._failed = True

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        if self._cleared:
            return StateID.LANE_FOLLOW

        if self._failed:
            return StateID.EMERGENCY_STOP

        return None
