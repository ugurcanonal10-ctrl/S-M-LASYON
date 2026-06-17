"""
Atlas Takimi - Velocity Planner Node
Yamuk (trapezoidal) hiz profili uretir.
FSM'den gelen behavior_command'a gore hedef hiz belirler.

Dinledigi topicler:
  /planning/behavior_command       -> std_msgs/String
  /localization/distance_to_target -> std_msgs/Float32

Yayinladigi topicler:
  /planning/velocity_profile -> std_msgs/Float32  (m/s)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32

# Hiz sabitleri (m/s)
CRUISE_SPEED     = 2.0
APPROACH_SPEED   = 0.5
STOP_SPEED       = 0.0

# Yavas hiz bolgesi mesafesi (m)
SLOWDOWN_DIST    = 5.0


class VelocityPlannerNode(Node):

    def __init__(self):
        super().__init__('velocity_planner_node')
        self.get_logger().info('[VelocityPlanner] Baslatildi.')

        self._behavior = 'LANE_FOLLOW'
        self._dist_to_target = 999.0

        self._pub_vel = self.create_publisher(
            Float32, '/planning/velocity_profile', 10)

        self.create_subscription(
            String, '/planning/behavior_command',
            self._cb_behavior, 10)
        self.create_subscription(
            Float32, '/localization/distance_to_target',
            self._cb_distance, 10)

        self.create_timer(0.05, self._timer_cb)  # 20 Hz

    def _cb_behavior(self, msg: String):
        self._behavior = msg.data.upper()

    def _cb_distance(self, msg: Float32):
        self._dist_to_target = msg.data

    def _timer_cb(self):
        speed = self._compute_speed()
        out = Float32()
        out.data = float(speed)
        self._pub_vel.publish(out)

    def _compute_speed(self) -> float:
        """Yamuk hiz profili hesapla."""
        # Acil/son state'ler: her zaman dur
        if self._behavior in ('EMERGENCY_STOP', 'MISSION_COMPLETE',
                               'RED_LIGHT'):
            return STOP_SPEED

        # Yolcu alma/indirme: dur ve bekle
        if self._behavior in ('PASSENGER_PICKUP', 'PASSENGER_DROPOFF'):
            return STOP_SPEED

        # Park manuvrasi: yavas
        if self._behavior == 'PARKING_MANEUVER':
            return APPROACH_SPEED

        # Hedefe yaklasim: hizi dusur (trapezoidal profil)
        if self._dist_to_target <= SLOWDOWN_DIST:
            # Lineer azaltma: CRUISE -> APPROACH
            ratio = self._dist_to_target / SLOWDOWN_DIST
            return APPROACH_SPEED + (CRUISE_SPEED - APPROACH_SPEED) * ratio

        # Normal suruş
        return CRUISE_SPEED


def main(args=None):
    rclpy.init(args=args)
    node = VelocityPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
