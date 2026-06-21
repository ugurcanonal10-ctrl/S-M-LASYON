from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    pkg_share = get_package_share_directory('localization_pkg')
    config = os.path.join(pkg_share, 'config', 'ekf_local.yaml')

    return LaunchDescription([

        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[config],
            remappings=[
                ('odometry/filtered', '/odometry/filtered')
            ]
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom',
            output='screen',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        ),
    ])
