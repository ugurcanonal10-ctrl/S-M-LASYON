import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from std_msgs.msg import String
import time

class GpsDropout(Node):
    def __init__(self):
        super().__init__('gps_dropout')
        self.gps_active = True
        self.dropout_duration = 10.0
        self.cycle_duration = 20.0

        self.sub = self.create_subscription(
            NavSatFix, '/gazebo_ros_gps/out', self.gps_cb, 10)
        self.pub = self.create_publisher(
            NavSatFix, '/gps/fix', 10)
        self.status_pub = self.create_publisher(
            String, '/localization/gps_status', 10)

        self.create_timer(1.0, self.update_status)
        self.start_time = time.time()
        self.get_logger().info('GPS Dropout Node başlatıldı')

    def update_status(self):
        elapsed = (time.time() - self.start_time) % self.cycle_duration
        if elapsed < self.dropout_duration:
            if self.gps_active:
                self.gps_active = False
                self.get_logger().warn(
                    'GPS KESİLDİ - Dead Reckoning modu aktif')
        else:
            if not self.gps_active:
                self.gps_active = True
                self.get_logger().info(
                    'GPS GERİ DÖNDÜ - Normal mod')
        status = String()
        status.data = 'NORMAL' if self.gps_active else 'DEAD_RECKONING'
        self.status_pub.publish(status)

    def gps_cb(self, msg):
        if self.gps_active:
            self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = GpsDropout()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
