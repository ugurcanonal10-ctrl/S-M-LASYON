from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    
    config = os.path.join(
        get_package_share_directory('localization_pkg'),
        'config',
        'ekf.yaml'
    )

    return LaunchDescription([
        
        # EKF Node - GPS + IMU birleştirir
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[config]
        ),

        # GPS'i odometry formatına çevirir
        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            name='navsat_transform_node',
            output='screen',
            parameters=[{
                'magnetic_declination_radians': 0.0,
                'yaw_offset': 0.0,
                'zero_altitude': True,
                # bkz. config/ekf.yaml'daki ayni notu - /clock olmadan
                # navsat_transform_node de TF_OLD_DATA aliyordu.
                'use_sim_time': True,
            }],
            remappings=[
                ('imu/data', '/gazebo_ros_imu/out'),
                ('gps/fix', '/gazebo_ros_gps/out'),
                # ESKI: ('odometry/filtered', '/localization/pose') -> KALDIRILDI.
                # EKF varsayilan olarak /odometry/filtered'a yaziyor (yukaridaki
                # ekf_filter_node Node'unda remap YOK), ama bu satir
                # navsat_transform_node'u '/localization/pose'u dinlemeye
                # zorluyordu - boyle bir topic hicbir zaman var olmadi, yani
                # navsat_transform GPS donguyu kapatmak icin gereken filtrelenmis
                # odometriyi ASLA goremiyordu. Kaldirilinca navsat_transform_node
                # varsayilan '/odometry/filtered'i dinleyip EKF'nin gercek
                # ciktisini alacak. (Ahmet, Gorev 3 debug sureci)
            ]
        ),
    ])
