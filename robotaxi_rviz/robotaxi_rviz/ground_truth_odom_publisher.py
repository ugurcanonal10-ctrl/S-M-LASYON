#!/usr/bin/env python3
"""
ground_truth_odom_publisher
----------------------------
Robotaksi yarismasi - Gorev 3 (Ahmet, RViz konfigurasyonu icin yardimci).

Gazebo'nun /gazebo/model_states topic'i (gazebo_msgs/ModelStates) RViz'de
dogrudan bir "path" olarak gosterilemez - RViz'in boyle bir display tipi
yok. Bu node, o array icinden 'robotaxi' modelinin pozunu/hizini cekip
nav_msgs/Odometry olarak /ground_truth/odom uzerinde yeniden yayinlar,
boylece RViz'in yerlesik "Odometry" display'i (path/trail + ok + istenirse
kovaryans elipsi) ile gosterilebilir hale gelir.

Kovaryans: ground truth oldugu icin (gercek simulasyon konumu, olcum
hatasi yok) sifira yakin/kucuk sabit degerler atiyoruz - EKF ve GPS
path'leriyle gorsel karsilastirmada "hata yok" referansi olarak hizmet
eder.

NOT: Bu node'un /gazebo/model_states'i gorebilmesi icin world dosyasinda
gazebo_ros_state plugin'inin yuklu olmasi sart - bu zaten Gorev 1'de
(teknofest_pist.world) eklendi.
"""
import rclpy
from rclpy.node import Node
from gazebo_msgs.msg import ModelStates
from nav_msgs.msg import Odometry


class GroundTruthOdomPublisher(Node):

    def __init__(self):
        super().__init__('ground_truth_odom_publisher')

        self.declare_parameter('model_name', 'robotaxi')
        self.declare_parameter('model_states_topic', '/gazebo/model_states')
        self.declare_parameter('out_topic', '/ground_truth/odom')
        # PLACEHOLDER frame: gercek global EKF (map->odom) gelene kadar
        # 'map' ve 'odom' ayni yerde varsayiliyor (bkz. rviz_view.launch.py
        # icindeki static_transform_publisher notu).
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('child_frame_id', 'base_link')

        self.model_name = self.get_parameter('model_name').value
        self.frame_id = self.get_parameter('frame_id').value
        self.child_frame_id = self.get_parameter('child_frame_id').value

        model_states_topic = self.get_parameter('model_states_topic').value
        out_topic = self.get_parameter('out_topic').value

        self.sub = self.create_subscription(
            ModelStates, model_states_topic, self.on_model_states, 10)
        self.pub = self.create_publisher(Odometry, out_topic, 10)

        self.get_logger().info(
            f"ground_truth_odom_publisher baslatildi | model={self.model_name} "
            f"| {model_states_topic} -> {out_topic}")

    def on_model_states(self, msg: ModelStates):
        if self.model_name not in msg.name:
            return
        idx = msg.name.index(self.model_name)

        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id

        odom.pose.pose = msg.pose[idx]
        odom.twist.twist = msg.twist[idx]

        # Ground truth -> hata yok varsayimi (kucuk sabit kovaryans,
        # RViz'in kovaryans elipsi cizebilmesi icin sifir olmasin)
        small = 1e-4
        odom.pose.covariance[0] = small
        odom.pose.covariance[7] = small
        odom.pose.covariance[35] = small  # yaw

        self.pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = GroundTruthOdomPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
