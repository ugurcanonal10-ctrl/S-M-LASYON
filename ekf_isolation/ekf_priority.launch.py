"""
ekf_priority.launch.py
------------------------
Robotaksi yarismasi - Gorev 5 (Ahmet): EKF'nin, agir SLAM/point-cloud
islemden IZOLE calistigini gosteren launch konfigurasyonu.

MIMARI ACIKLAMA (rapor 7.9'a eklenecek paragrafin teknik temeli):

1) SURECSEL IZOLASYON (zaten dogal olarak var):
   robot_localization'in ekf_node ve navsat_transform_node'u, ROS2'de
   her biri AYRI BIR ISLETIM SISTEMI SURECI (process) olarak calisir -
   slam_toolbox ve pointcloud_to_laserscan da kendi ayri surecleridir.
   Yani Python GIL'i veya tek bir process'in thread'leri arasinda
   paylasilan kaynak sorunu YOKTUR: Linux cekirdegi, EKF'nin surecini
   SLAM'in surecinden BAGIMSIZ olarak zamanlar (preemptive multitasking).
   Bu, "ayri thread" gereksiniminin OS seviyesinde zaten karsilandigi
   anlamina gelir.

2) ZAMANLAMA ONCELIGI (bu launch dosyasinin eklediği kisim):
   Surec izolasyonu varsa da, CPU YOGUN bir SLAM scan-matching islemi
   (or. loop closure sirasinda) kisa sureli CPU patlamalari yapip
   zamanlayicinin EKF surecine zaman ayirmasini geciktirebilir - ozellikle
   tek cekirdekli/dusuk cekirdek sayili ortamlarda (konteynerimiz gibi).
   Bunu onlemek icin EKF ve navsat_transform_node, `nice` ile DAHA
   YUKSEK Linux zamanlayici onceligiyle (`-10`, normal 0'dan daha
   yuksek oncelikli) baslatiliyor - SLAM/point-cloud node'lari ise
   varsayilan (0) oncelikte kaliyor. Boylece CPU rekabeti olustugunda
   cekirdek EKF'yi once calistirir, EKF'nin 30Hz (rapor metninde "100Hz"
   hedeflenmisse, ekf.yaml'daki frequency parametresi guncellenmeli)
   dongusu SLAM'in CPU yukunden ETKILENMEZ.

ONEMLI: `nice` ile NEGATIF (yuksek) oncelik vermek root yetkisi ister.
Konteynerde zaten root oldugumuz icin bu calisir; gercek arac
bilgisayarinda (Advantech) cnf/sudoers ayari gerekebilir.

Kullanim:
  ros2 launch ekf_isolation/ekf_priority.launch.py
  (Bunu calistirmadan ONCE Gazebo'nun acik oldugundan emin olun)
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import EnvironmentVariable
import os


def generate_launch_description():
    # localization_pkg kurulu config dosyasinin yolu - workspace'inize
    # gore degistirin (varsayilan: ~/arac_ws).
    ws = os.path.expanduser(os.environ.get('ROS_WS', '~/arac_ws'))
    ekf_config = os.path.join(
        ws, 'install', 'localization_pkg', 'share',
        'localization_pkg', 'config', 'ekf.yaml')

    # nice -n -10: normalden YUKSEK oncelik (Linux'ta nice degeri ne kadar
    # DUSUKSE oncelik o kadar YUKSEKTIR; araligi -20 (en yuksek) ile 19
    # (en dusuk) arasidir). -10 agresif ama guvenli bir secim.
    ekf_node = ExecuteProcess(
        cmd=['nice', '-n', '-10', 'ros2', 'run', 'robot_localization',
             'ekf_node', '--ros-args', '--params-file', ekf_config],
        output='screen',
        name='ekf_node_HIGH_PRIORITY',
    )

    navsat_node = ExecuteProcess(
        cmd=['nice', '-n', '-10', 'ros2', 'run', 'robot_localization',
             'navsat_transform_node', '--ros-args',
             '-r', 'imu/data:=/gazebo_ros_imu/out',
             '-r', 'gps/fix:=/gazebo_ros_gps/out',
             '-p', 'zero_altitude:=true',
             '-p', 'use_sim_time:=true'],
        output='screen',
        name='navsat_transform_node_HIGH_PRIORITY',
    )

    return LaunchDescription([ekf_node, navsat_node])
