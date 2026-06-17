"""
Serit Takibi State
Polinom regresyon ile serit eğrisini hesaplar,
direksiyon ve hız komutu üretir.
"""
import numpy as np
from .base_state import BaseState, StateID

class LaneFollowState(BaseState):
    def __init__(self, logger=None):
        super().__init__(StateID.LANE_FOLLOW, logger)
        self._steering = 0.0
        self._speed = 2.0

    def on_enter(self):
        super().on_enter()
        self._steering = 0.0
        self._speed = 2.0
        if self.logger:
            self.logger.info('[LaneFollow] Serit takibi baslatildi.')

    def execute(self, context: dict):
        lane_points = context.get('lane_points', [])

        if len(lane_points) < 3:
            # Yeterli serit noktası yoksa düz git
            self._steering = 0.0
            self._speed = 1.0
            return

        # Noktaları x ve y dizilerine ayır
        xs = np.array([p[0] for p in lane_points], dtype=float)
        ys = np.array([p[1] for p in lane_points], dtype=float)

        # 2. derece polinom fit: y = ax² + bx + c
        coeffs = np.polyfit(xs, ys, deg=2)

        # Aracın önündeki noktada eğriye bak (x=1.0 metre ileri)
        lookahead_x = 1.0
        predicted_y = np.polyval(coeffs, lookahead_x)

        # Direksiyon açısı: saptama miktarına göre orantılı
        # predicted_y pozitifse sola, negatifse sağa
        steering_gain = 0.5
        self._steering = float(-predicted_y * steering_gain)
        self._steering = max(-1.0, min(1.0, self._steering))  # [-1, 1] sınırla

        self._speed = 2.0

        if self.logger:
            self.logger.info(
                f'[LaneFollow] steering={self._steering:.3f} '
                f'speed={self._speed:.1f}'
            )

    def check_transitions(self, context: dict):
        if context.get('emergency'):
            return StateID.EMERGENCY_STOP
        if context.get('traffic_light') == 'red':
            return StateID.RED_LIGHT
        if context.get('sign_detected'):
            return StateID.SIGN_RESPONSE
        if context.get('obstacle_type') == 'static':
            return StateID.STATIC_OBSTACLE
        if context.get('obstacle_type') == 'dynamic':
            return StateID.DYNAMIC_OBSTACLE
        mission = context.get('mission_event', '').strip()
        dist = context.get('distance_to_target', 999)
        if mission in ('', 'none'):
            return None
        if mission == 'pickup' and dist <= 1.0:
            return StateID.PASSENGER_PICKUP
        if mission == 'dropoff' and dist <= 1.0:
            return StateID.PASSENGER_DROPOFF
        if mission == 'park' and dist <= 5.0:
            return StateID.PARKING_SEARCH
        return None
