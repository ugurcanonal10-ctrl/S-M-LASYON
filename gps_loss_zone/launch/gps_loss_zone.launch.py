"""
gps_loss_simulator'i tek başına test etmek için launch dosyası.
Gerçek demoda bu node'u, Yasemin'in ana lokalizasyon launch dosyasına
EKLEYIN (aşağıdaki entegrasyon notuna bakın) - ayrı ayrı çalıştırmayın.

Kullanım:
  ros2 launch gps_loss_zone gps_loss_zone.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('gps_loss_zone')
    params_file = os.path.join(pkg_share, 'config', 'gps_loss_zone.yaml')

    gps_loss_node = Node(
        package='gps_loss_zone',
        executable='gps_loss_simulator',
        name='gps_loss_simulator',
        output='screen',
        parameters=[params_file],
    )

    return LaunchDescription([gps_loss_node])
