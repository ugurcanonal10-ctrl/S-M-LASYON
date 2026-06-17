"""
Atlas Takimi - Behavior Monitor Node
UMS-1/UMS-2 sinyallerini izler, acil durdurma yayinlar.

Dinledigi topicler:
  /ums/signal  -> std_msgs/String  ('UMS1' / 'UMS2')

Yayinladigi topicler:
  /safety/emergency -> std_msgs/Bool
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool


class BehaviorMonitorNode(Node):

    def __init__(self):
        super().__init__('behavior_monitor_node')
        self.get_logger().info('[BehaviorMonitor] Baslatildi.')

        self._pub_emergency = self.create_publisher(
            Bool, '/safety/emergency', 10)

        self.create_subscription(
            String, '/ums/signal', self._cb_ums, 10)

    def _cb_ums(self, msg: String):
        signal = msg.data.strip().upper()
        if signal == 'UMS1':
            self.get_logger().error('[BehaviorMonitor] UMS-1 alindi! '
                                    'Acil durdurma yayinlaniyor.')
            out = Bool()
            out.data = True
            self._pub_emergency.publish(out)
        elif signal == 'UMS2':
            self.get_logger().info('[BehaviorMonitor] UMS-2 (Go) alindi.')


def main(args=None):
    rclpy.init(args=args)
    node = BehaviorMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
