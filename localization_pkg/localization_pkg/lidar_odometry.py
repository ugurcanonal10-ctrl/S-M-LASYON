import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import Odometry
import numpy as np
from kiss_icp.kiss_icp import KissICP
from kiss_icp.config import KISSConfig

class LidarOdometryNode(Node):
    def __init__(self):
        super().__init__('lidar_odometry_node')
        
        self.get_logger().info('LiDAR Odometry Node başlatıldı')
        
        # KISS-ICP
        config = KISSConfig()
        config.data.max_range = 100.0
        config.data.min_range = 1.0
        config.mapping.voxel_size = 1.0
        self.kiss_icp = KissICP(config=config)
        
        # LiDAR verisini dinle
        self.lidar_sub = self.create_subscription(
            PointCloud2,
            '/velodyne_points',
            self.lidar_callback,
            10
        )
        
        # Odometry yayınla
        self.odom_pub = self.create_publisher(
            Odometry,
            '/localization/lidar_odom',
            10
        )
        
        self.get_logger().info('VLP-16 verisi bekleniyor...')

    def lidar_callback(self, msg):
        points = self.pointcloud2_to_array(msg)
        
        if points is None or len(points) == 0:
            return
        
        # KISS-ICP ile pozisyon hesapla
        self.kiss_icp.register_frame(points)
        pose = self.kiss_icp.poses[-1]
        
        # Odometry mesajı
        odom_msg = Odometry()
        odom_msg.header.stamp = msg.header.stamp
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_link'
        
        odom_msg.pose.pose.position.x = float(pose[0, 3])
        odom_msg.pose.pose.position.y = float(pose[1, 3])
        odom_msg.pose.pose.position.z = float(pose[2, 3])
        
        self.odom_pub.publish(odom_msg)
        self.get_logger().info(
            f'Konum: x={pose[0,3]:.2f} y={pose[1,3]:.2f}'
        )

    def pointcloud2_to_array(self, msg):
        import struct
        points = []
        point_step = msg.point_step
        data = msg.data
        
        for i in range(0, len(data), point_step):
            x = struct.unpack_from('f', data, i)[0]
            y = struct.unpack_from('f', data, i + 4)[0]
            z = struct.unpack_from('f', data, i + 8)[0]
            
            if not (np.isnan(x) or np.isnan(y) or np.isnan(z)):
                points.append([x, y, z])
                
        return np.array(points, dtype=np.float64)

def main(args=None):
    rclpy.init(args=args)
    node = LidarOdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
