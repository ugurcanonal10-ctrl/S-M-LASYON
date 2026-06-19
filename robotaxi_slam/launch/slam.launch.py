"""
slam.launch.py
---------------
Velodyne VLP-16 point cloud -> 2D laser dilimi -> slam_toolbox -> RViz
zincirini başlatır.

NOT: slam_toolbox'ın paket-içi online_async_launch.py'si (slam_toolbox
2.4.1, Foxy) `slam_params_file` argumanini desteklemiyor - launch_arguments
ile verilen ozel config sessizce yok sayilip her zaman kendi varsayilan
config'ini kullaniyordu (test sirasinda `ps aux` ile dogrulandi). Bu yuzden
slam_toolbox node'unu BURADA DOGRUDAN baslatiyoruz, paketin kendi launch
dosyasini include etmiyoruz - bu sekilde kendi parametre dosyamiz
GARANTI yukleniyor.

Bu launch dosyası robotaxi_sim'in Gazebo simülasyonunu AÇMAZ — onu
zaten açık varsayar (önce `ros2 launch robotaxi_sim sim_teknofest.launch.py`
ile sahneyi açın, sonra bu launch'ı ayrı bir terminalde çalıştırın).

Kullanım:
  # Terminal 1
  ros2 launch robotaxi_sim sim_teknofest.launch.py

  # Terminal 2
  ros2 launch robotaxi_slam slam.launch.py

  # Terminal 3 - aracı sürün (haritanın oluşması için hareket gerekir)
  ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.5}, angular: {z: 0.2}}" -r 10

RViz'de "Map" display'i, araç ilerledikçe canlı güncellenen haritayı
gösterir.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_slam = get_package_share_directory('robotaxi_slam')

    p2l_params = os.path.join(pkg_slam, 'config', 'pointcloud_to_laserscan.yaml')
    slam_params = os.path.join(pkg_slam, 'config', 'slam_toolbox_params.yaml')
    rviz_config = os.path.join(pkg_slam, 'rviz', 'slam_view.rviz')

    # 1) 3D point cloud (/velodyne_points) -> 2D LaserScan (/scan)
    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        parameters=[p2l_params],
        remappings=[
            ('cloud_in', '/velodyne_points'),
            ('scan', '/scan'),
        ],
    )

    # 2) slam_toolbox (online async - gercek zamanli haritalama)
    #    Dogrudan Node olarak baslatiliyor (bkz. yukaridaki NOT).
    #    use_sim_time verilmiyor cunku bu world /clock yayinlamiyor
    #    (libgazebo_ros_init.so yuklenmedigi icin) - sistemdeki diger
    #    tum node'lar gibi gercek (wall-clock) zaman kullaniyoruz.
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params],
    )

    # 3) RViz - harita + scan + point cloud + TF agacini ayni ekranda goster
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
    )

    return LaunchDescription([
        pointcloud_to_laserscan_node,
        slam_toolbox_node,
        rviz_node,
    ])
