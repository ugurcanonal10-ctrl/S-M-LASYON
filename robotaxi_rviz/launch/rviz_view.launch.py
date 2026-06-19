"""
rviz_view.launch.py
--------------------
Robotaksi yarismasi - Gorev 3 (Ahmet): ground truth / EKF / ham GPS
path'lerini farkli renklerde, kovaryans elipsleriyle ve TF agaciyla
(map->odom->base_link) gosteren RViz konfigurasyonu.

ONEMLI - PLACEHOLDER TF UYARISI:
Yasemin'in mevcut EKF kurulumu (localization_pkg) TEK bir yerel EKF
(world_frame: odom), yani sadece odom->base_link TF'i yayinliyor.
Orijinal plandaki ikinci/global EKF (map->odom) HENUZ KURULMADI.
Bu launch dosyasi, RViz'de "map" frame'inin gorunup TF agacinin tam
calismasi icin GECICI bir static_transform_publisher (map->odom,
kimlik donusumu) ekliyor. Bu GERCEK bir global lokalizasyon DEGILDIR -
sadece gorsellestirme altyapisinin simdiden hazir olmasi icindir.
Yasemin'in global EKF'si eklendiginde bu static_transform_publisher
SATIRI SILINMELI ve map->odom TF'i o EKF'den gelmeli.

On kosul - bu launch'tan ONCE asagidakiler ayri terminallerde acik olmali:
  ros2 launch robotaxi_sim sim_teknofest.launch.py
  ros2 launch localization_pkg localization.launch.py

Kullanim:
  ros2 launch robotaxi_rviz rviz_view.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_rviz = get_package_share_directory('robotaxi_rviz')
    rviz_config = os.path.join(pkg_rviz, 'rviz', 'localization_view.rviz')

    # GECICI placeholder - bkz. yukaridaki UYARI. Foxy'de static_transform_publisher
    # pozisyonel syntax kullanir: x y z yaw pitch roll parent_frame child_frame
    map_to_odom_placeholder = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_PLACEHOLDER',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
    )

    ground_truth_node = Node(
        package='robotaxi_rviz',
        executable='ground_truth_odom_publisher',
        name='ground_truth_odom_publisher',
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_localization',
        output='screen',
        arguments=['-d', rviz_config],
    )

    return LaunchDescription([
        map_to_odom_placeholder,
        ground_truth_node,
        rviz_node,
    ])
