"""
sim_teknofest.launch.py
------------------------
Asıl yarış pistini (tünel dahil) açan ve GPS-kaybı simülasyon node'unu
otomatik başlatan launch dosyası.

Mevcut sim.launch.py'ye DOKUNULMADI (city.world ile çalışmaya devam
eder) - bu, onun yanına eklenen YENİ bir launch dosyasıdır.

Kullanım:
  colcon build --packages-select robotaxi_sim gps_loss_zone
  source install/setup.bash
  ros2 launch robotaxi_sim sim_teknofest.launch.py

Test:
  ros2 topic list                    # /gazebo/model_states, /gps, /gps/fix görmelisiniz
  ros2 topic echo /gps_loss/status_text
  # Aracı teleop veya cmd_vel ile +x yönünde sürün (kavşak x=20, tünel x=49-61)
  # Tünele girince /gps/fix akışının durduğunu, status_text'in
  # "Mod: DEAD RECKONING" olduğunu görmelisiniz.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    pkg_robotaxi = get_package_share_directory('robotaxi_sim')
    pkg_gps_loss = get_package_share_directory('gps_loss_zone')

    urdf = os.path.join(pkg_robotaxi, 'models', 'robotaxi', 'robotaxi.urdf')
    world = os.path.join(pkg_robotaxi, 'worlds', 'teknofest_pist.world')
    gps_loss_params = os.path.join(pkg_gps_loss, 'config', 'gps_loss_zone.yaml')

    with open(urdf, 'r') as f:
        robot_desc = f.read()

    return LaunchDescription([

        ExecuteProcess(
            cmd=['gazebo', '--verbose', world, '-s', 'libgazebo_ros_factory.so'],
            output='screen'
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_desc}],
            output='screen'
        ),

        # Pistin başında (kavşaktan ve tünelden önce) spawn ediyoruz ki
        # araç kavşağı, sonra tüneli sırasıyla geçebilsin.
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', 'robotaxi', '-topic', 'robot_description',
                       '-x', '-8', '-y', '0', '-z', '0.6'],
            output='screen'
        ),

        Node(
            package='gps_loss_zone',
            executable='gps_loss_simulator',
            name='gps_loss_simulator',
            output='screen',
            parameters=[gps_loss_params],
        ),
    ])
