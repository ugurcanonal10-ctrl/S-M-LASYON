"""
Atlas Takimi - Mission Manager Node
GEOJSON hedef koordinatlarini okur, mesafe hesaplar,
gorev olaylarini FSM'ye bildirir.

Dinledigi topicler:
  /localization/gps_pose -> geometry_msgs/Pose2D

Yayinladigi topicler:
  /mission/event                   -> std_msgs/String
  /localization/distance_to_target -> std_msgs/Float32
"""

import math
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from geometry_msgs.msg import Pose2D

# Ornek GEOJSON yapisi (gercek yarisma gununde dosyadan okunur)
SAMPLE_WAYPOINTS = [
    {'type': 'pickup',  'lat': 0.0, 'lon': 0.0},
    {'type': 'dropoff', 'lat': 0.0, 'lon': 0.0},
    {'type': 'park',    'lat': 0.0, 'lon': 0.0},
]

ARRIVAL_THRESHOLD_M = 1.0   # <=1 m: hedefe ulastirildi
PARK_APPROACH_M     = 5.0   # <=5 m: park arama baslar


class MissionManagerNode(Node):

    def __init__(self):
        super().__init__('mission_manager_node')
        self.get_logger().info('[MissionManager] Baslatildi.')

        self._waypoints = SAMPLE_WAYPOINTS
        self._wp_index = 0
        self._current_pose = None

        self._pub_event = self.create_publisher(
            String, '/mission/event', 10)
        self._pub_dist = self.create_publisher(
            Float32, '/localization/distance_to_target', 10)

        self.create_subscription(
            Pose2D, '/localization/gps_pose', self._cb_pose, 10)

        self.create_timer(0.2, self._timer_cb)  # 5 Hz

    def _cb_pose(self, msg: Pose2D):
        self._current_pose = msg

    def _timer_cb(self):
        if self._current_pose is None:
            return
        if self._wp_index >= len(self._waypoints):
            return

        wp = self._waypoints[self._wp_index]
        dist = self._euclidean(
            self._current_pose.x, self._current_pose.y,
            wp['lat'], wp['lon'])

        # Mesafeyi yayinla
        dist_msg = Float32()
        dist_msg.data = float(dist)
        self._pub_dist.publish(dist_msg)

        # Gorev olayini yayinla
        event_msg = String()
        wp_type = wp['type']

        if wp_type == 'park':
            if dist <= PARK_APPROACH_M:
                event_msg.data = 'park'
                self._pub_event.publish(event_msg)
        else:
            event_msg.data = wp_type  # 'pickup' veya 'dropoff'
            self._pub_event.publish(event_msg)

        # Hedefe ulasildiysa bir sonraki waypoint'e gec
        if dist <= ARRIVAL_THRESHOLD_M:
            self.get_logger().info(
                f'[MissionManager] Hedef {self._wp_index} tamamlandi '
                f'({wp_type}). Siradaki hedefe geciliyor.')
            self._wp_index += 1

    def _euclidean(self, x1, y1, x2, y2) -> float:
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def main(args=None):
    rclpy.init(args=args)
    node = MissionManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
