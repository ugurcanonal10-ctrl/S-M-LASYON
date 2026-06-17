"""
Tabela Tepkisi State
- YOLO'dan gelen tabela tipine gore kural uygula
- Kural uygulaninca Serit Takibi'ne don
"""

from .base_state import BaseState, StateID


class SignResponseState(BaseState):

    def __init__(self, logger=None):
        super().__init__(StateID.SIGN_RESPONSE, logger)
        self._rule_applied = False

    def on_enter(self):
        super().on_enter()
        self._rule_applied = False

    def execute(self, context: dict):
        sign_type = context.get('sign_type', '')
        if sign_type and not self._rule_applied:
            if self.logger:
                self.logger.info(f'[Sign] Kural uygulaniyor: {sign_type}')
            self._rule_applied = True

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP

        if self._rule_applied:
            return StateID.LANE_FOLLOW

        return None
