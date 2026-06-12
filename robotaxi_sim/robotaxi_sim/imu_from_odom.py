import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
import math

class ImuFromOdom(Node):
    def __init__(self):
        super().__init__('imu_from_odom')

        self.prev_vx = 0.0
        self.prev_vy = 0.0
        self.prev_wz = 0.0
        self.prev_time = None

        self.sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.pub = self.create_publisher(Imu, '/imu/data', 10)

        self.get_logger().info('IMU emülatör başlatıldı → /imu/data')

    def odom_cb(self, msg):
        now = self.get_clock().now()

        imu_msg = Imu()
        imu_msg.header.stamp = msg.header.stamp
        imu_msg.header.frame_id = 'imu_link'

        # Orientation — doğrudan odometriden al
        imu_msg.orientation = msg.pose.pose.orientation

        # Angular velocity
        imu_msg.angular_velocity.x = 0.0
        imu_msg.angular_velocity.y = 0.0
        imu_msg.angular_velocity.z = msg.twist.twist.angular.z

        # Linear acceleration — hız türevi
        if self.prev_time is not None:
            dt = (now - self.prev_time).nanoseconds / 1e9
            if dt > 0:
                ax = (msg.twist.twist.linear.x - self.prev_vx) / dt
                ay = (msg.twist.twist.linear.y - self.prev_vy) / dt
            else:
                ax, ay = 0.0, 0.0
        else:
            ax, ay = 0.0, 0.0

        imu_msg.linear_acceleration.x = ax
        imu_msg.linear_acceleration.y = ay
        imu_msg.linear_acceleration.z = 9.81  # yerçekimi

        # Covariance
        imu_msg.orientation_covariance[0] = 0.01
        imu_msg.orientation_covariance[4] = 0.01
        imu_msg.orientation_covariance[8] = 0.01
        imu_msg.angular_velocity_covariance[0] = 0.01
        imu_msg.angular_velocity_covariance[4] = 0.01
        imu_msg.angular_velocity_covariance[8] = 0.01
        imu_msg.linear_acceleration_covariance[0] = 0.1
        imu_msg.linear_acceleration_covariance[4] = 0.1
        imu_msg.linear_acceleration_covariance[8] = 0.1

        self.pub.publish(imu_msg)

        self.prev_vx = msg.twist.twist.linear.x
        self.prev_vy = msg.twist.twist.linear.y
        self.prev_wz = msg.twist.twist.angular.z
        self.prev_time = now


def main(args=None):
    rclpy.init(args=args)
    node = ImuFromOdom()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
