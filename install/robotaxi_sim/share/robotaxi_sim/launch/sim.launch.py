import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    pkg = get_package_share_directory('robotaxi_sim')
    urdf = os.path.join(pkg, 'models', 'robotaxi', 'robotaxi.urdf')
    world = os.path.join(pkg, 'worlds', 'city.world')

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

        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=['-entity', 'robotaxi', '-topic', 'robot_description',
                       '-x', '0', '-y', '0', '-z', '0.6'],
            output='screen'
        ),
    ])
