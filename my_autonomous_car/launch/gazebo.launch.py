import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_name = 'my_autonomous_car'

    # 1. Yeni Pist Dosyamızın Tam Yolu
    world_file_path = os.path.join(get_package_share_directory(pkg_name), 'worlds', 'track.world')

    # 2. Araç Tasarım Dosyamızın Yolu
    xacro_file = os.path.join(get_package_share_directory(pkg_name), 'urdf', 'car.urdf.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    # Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw}]
    )

    # Gazebo'yu BİZİM DÜNYAMIZLA başlat
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
        launch_arguments={'world': world_file_path}.items()
    )

    # Aracı Gazebo'ya Ekle
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'autonomous_car',
                                   '-z', '0.1'], # Aracın asfalta saplanmaması için hafif yukarıdan bırakıyoruz
                        output='screen')

    return LaunchDescription([
        gazebo,
        node_robot_state_publisher,
        spawn_entity
    ])


