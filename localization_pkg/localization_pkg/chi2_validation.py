import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import numpy as np
import math

class Chi2Validation(Node):
    def __init__(self):
        super().__init__('chi2_validation')

        self.ekf_x = None
        self.ekf_y = None
        self.chi2_threshold = 7.815  # 3 serbestlik derecesi, %95 güven
        self.rejected = 0
        self.accepted = 0

        # Sahte GPS sıçraması enjekte eden publisher
        self.gps_pub = self.create_publisher(
            Odometry, '/odometry/gps_injected', 10)
        self.status_pub = self.create_publisher(
            String, '/localization/chi2_status', 10)

        self.create_subscription(
            Odometry, '/odometry/filtered', self.ekf_cb, 10)

        self.create_timer(1.0, self.inject_and_validate)
        self.inject_outlier = False
        self.cycle = 0

        self.get_logger().info('Chi2 Doğrulama Node başlatıldı')
        self.get_logger().info(f'Chi2 eşik değeri: {self.chi2_threshold}')

    def ekf_cb(self, msg):
        self.ekf_x = msg.pose.pose.position.x
        self.ekf_y = msg.pose.pose.position.y

    def inject_and_validate(self):
        if self.ekf_x is None:
            return

        self.cycle += 1

        # Her 5 saniyede bir aykırı sıçrama enjekte et
        if self.cycle % 10 < 5:
            self.inject_outlier = False
            # Normal gürültü
            noise_x = np.random.normal(0, 0.03)
            noise_y = np.random.normal(0, 0.03)
        else:
            self.inject_outlier = True
            # Büyük sahte sıçrama (2 metre)
            noise_x = np.random.normal(2.0, 0.1)
            noise_y = np.random.normal(2.0, 0.1)

        gps_x = self.ekf_x + noise_x
        gps_y = self.ekf_y + noise_y

        # Chi2 testi
        innovation_x = gps_x - self.ekf_x
        innovation_y = gps_y - self.ekf_y
        chi2 = innovation_x**2 / 0.09 + innovation_y**2 / 0.09

        status = String()
        if chi2 > self.chi2_threshold:
            self.rejected += 1
            status.data = 'REDDEDİLDİ'
            self.get_logger().warn(
                f'AYKIRI GPS REDDEDİLDİ | Chi2: {chi2:.2f} > {self.chi2_threshold} | '
                f'Toplam red: {self.rejected}')
        else:
            self.accepted += 1
            status.data = 'KABUL EDİLDİ'
            self.get_logger().info(
                f'GPS kabul edildi | Chi2: {chi2:.2f} < {self.chi2_threshold} | '
                f'Toplam kabul: {self.accepted}')

        self.status_pub.publish(status)

def main(args=None):
    rclpy.init(args=args)
    node = Chi2Validation()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
