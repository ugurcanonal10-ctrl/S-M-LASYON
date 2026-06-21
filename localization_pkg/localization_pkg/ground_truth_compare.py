import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import math
import numpy as np

class GroundTruthCompare(Node):
    def __init__(self):
        super().__init__('ground_truth_compare')

        self.ekf_x = None
        self.ekf_y = None
        self.odom_x = None
        self.odom_y = None

        self.ekf_x0 = None
        self.ekf_y0 = None
        self.odom_x0 = None
        self.odom_y0 = None
        self.initialized = False

        self.errors = []
        self.noise_std = 0.03

        self.create_subscription(
            Odometry, '/odometry/filtered', self.ekf_cb, 10)
        self.create_subscription(
            Odometry, '/odom', self.odom_cb, 10)

        self.create_timer(1.0, self.compute_error)
        self.get_logger().info('Ground Truth Karşılaştırma Node başlatıldı')
        self.get_logger().info('EKF vs Ham Odometri karşılaştırması')

    def ekf_cb(self, msg):
        self.ekf_x = msg.pose.pose.position.x
        self.ekf_y = msg.pose.pose.position.y

    def odom_cb(self, msg):
        # Ham odometriye GPS gürültüsü simüle ediyoruz
        self.odom_x = msg.pose.pose.position.x + np.random.normal(0, self.noise_std)
        self.odom_y = msg.pose.pose.position.y + np.random.normal(0, self.noise_std)

    def compute_error(self):
        if None in (self.ekf_x, self.ekf_y, self.odom_x, self.odom_y):
            return

        if not self.initialized:
            self.ekf_x0 = self.ekf_x
            self.ekf_y0 = self.ekf_y
            self.odom_x0 = self.odom_x
            self.odom_y0 = self.odom_y
            self.initialized = True
            self.get_logger().info('Başlangıç noktası kaydedildi')
            return

        ekf_dx = self.ekf_x - self.ekf_x0
        ekf_dy = self.ekf_y - self.ekf_y0
        odom_dx = self.odom_x - self.odom_x0
        odom_dy = self.odom_y - self.odom_y0

        error = math.sqrt((ekf_dx - odom_dx)**2 + (ekf_dy - odom_dy)**2)
        self.errors.append(error)
        rmse = math.sqrt(np.mean(np.array(self.errors)**2))

        self.get_logger().info(
            f'Hata: {error*100:.2f} cm | RMSE: {rmse*100:.2f} cm')

def main(args=None):
    rclpy.init(args=args)
    node = GroundTruthCompare()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
