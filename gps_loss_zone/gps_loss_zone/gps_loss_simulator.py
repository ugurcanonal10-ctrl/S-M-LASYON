#!/usr/bin/env python3
"""
gps_loss_simulator
-------------------
Robotaksi yarismasi - konumlandirma alt sistemi (Ahmet, Gorev 1).

Bu node, aracin Gazebo icindeki GERCEK (ground-truth) konumunu
/gazebo/model_states uzerinden izler. Arac, worlds/teknofest_pist.world
icinde ZATEN VAR OLAN "tunel" yapisinin kapladigi dikdortgen bolgeye
(x:[49,61], y:[-4.3,4.3]) girdiginde, GPS plugin'inden gelen ham
NavSatFix mesajlarini:

  - mode == "drop"    -> hic yayinlamaz (toplam sinyal kaybi, navsat_transform_node
                          guncelleme alamaz -> robot_localization sadece odom/IMU ile
                          dead reckoning yapmaya baslar)
  - mode == "degrade" -> STATUS_NO_FIX + cok yuksek kovaryansla yayinlar
                          (kismi bozulma senaryosu icin)

Bolge disinda mesajlar oldugu gibi (pass-through) yayinlanir.

Ayrica asagidaki topic'leri yayinlar (Gorev 4 FSM ve RViz text overlay
bunlari dogrudan kullanabilir):
  /gps_loss/active       (std_msgs/Bool)   - bolgede mi degil mi
  /gps_loss/status_text  (std_msgs/String) - "Mod: DEAD RECKONING" / "Mod: NORMAL"

Topoloji (repodaki GERCEK topic adlariyla):
  [URDF: gazebo_ros_gps_sensor] --/gps (NavSatFix, zaten var, DEGISTIRMEYIN)-->
      [gps_loss_simulator] --/gps/fix-->
          [navsat_transform_node (Yasemin'in EKF kurulumu, henuz repoya eklenmedi)]

ONEMLI: /gazebo/model_states topic'inin var olmasi icin world dosyasina
gazebo_ros_state plugin'i eklenmis olmali (bkz. README - bu repo'da
şu an YOK, eklenmesi gerekiyor).
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from gazebo_msgs.msg import ModelStates
from std_msgs.msg import Bool, String


class GpsLossSimulator(Node):

    def __init__(self):
        super().__init__('gps_loss_simulator')

        # ---------------- Parametreler ----------------
        # NOT: Bu varsayilanlar S-M-LASYON/robotaxi_sim reposundaki gercek
        # URDF/world degerleriyle eslesecek sekilde ayarlandi (model adi,
        # GPS plugin topic'i, worlds/teknofest_pist.world icindeki mevcut
        # tunel koordinatlari). config/gps_loss_zone.yaml dosyasi bunlari
        # zaten parametre olarak da veriyor; burasi sadece yaml verilmeden
        # calistirilirsa diye guvenli bir fallback.
        self.declare_parameter('model_name', 'robotaxi')
        self.declare_parameter('model_states_topic', '/gazebo/model_states')
        self.declare_parameter('raw_gps_topic', '/gps')
        self.declare_parameter('out_gps_topic', '/gps/fix')
        self.declare_parameter('mode', 'drop')            # 'drop' | 'degrade'
        self.declare_parameter('degraded_covariance', 9999.0)

        # worlds/teknofest_pist.world icindeki MEVCUT tunel ile AYNI:
        # tunel_giris x=49, tunel_cikis x=61, tunel_sol/sag y=+-4.3
        self.declare_parameter('zone_x_min', 49.0)
        self.declare_parameter('zone_x_max', 61.0)
        self.declare_parameter('zone_y_min', -4.3)
        self.declare_parameter('zone_y_max', 4.3)

        # Tunele gercekten girmeden test edebilmek icin manuel anahtar:
        # ros2 param set /gps_loss_simulator force_loss true
        self.declare_parameter('force_loss', False)

        self.model_name = self.get_parameter('model_name').value
        self.mode = self.get_parameter('mode').value
        self.degraded_cov = float(self.get_parameter('degraded_covariance').value)

        model_states_topic = self.get_parameter('model_states_topic').value
        raw_gps_topic = self.get_parameter('raw_gps_topic').value
        out_gps_topic = self.get_parameter('out_gps_topic').value

        self.in_zone = False
        self.zone_enter_stamp = None

        # ---------------- Sub / Pub ----------------
        self.sub_states = self.create_subscription(
            ModelStates, model_states_topic, self.on_model_states, 10)

        self.sub_gps = self.create_subscription(
            NavSatFix, raw_gps_topic, self.on_gps, 10)

        self.pub_gps = self.create_publisher(NavSatFix, out_gps_topic, 10)
        self.pub_zone_active = self.create_publisher(Bool, '/gps_loss/active', 10)
        self.pub_zone_text = self.create_publisher(String, '/gps_loss/status_text', 10)

        self.get_logger().info(
            "gps_loss_simulator baslatildi | mod=%s | model=%s | raw=%s -> out=%s" %
            (self.mode, self.model_name, raw_gps_topic, out_gps_topic))
        self._log_zone()

    def _log_zone(self):
        x0, x1, y0, y1 = self._zone()
        self.get_logger().info(
            "GPS-kaybi bolgesi: x[%.1f, %.1f]  y[%.1f, %.1f]" % (x0, x1, y0, y1))

    def _zone(self):
        return (
            self.get_parameter('zone_x_min').value,
            self.get_parameter('zone_x_max').value,
            self.get_parameter('zone_y_min').value,
            self.get_parameter('zone_y_max').value,
        )

    # ------------------------------------------------------------------
    def on_model_states(self, msg: ModelStates):
        if self.model_name not in msg.name:
            # Henuz spawn olmamis olabilir; sessizce gec.
            return
        idx = msg.name.index(self.model_name)
        x = msg.pose[idx].position.x
        y = msg.pose[idx].position.y

        x_min, x_max, y_min, y_max = self._zone()
        geometric_in_zone = (x_min <= x <= x_max) and (y_min <= y <= y_max)
        force = bool(self.get_parameter('force_loss').value)
        now_in_zone = geometric_in_zone or force

        if now_in_zone and not self.in_zone:
            self.zone_enter_stamp = self.get_clock().now()
            self.get_logger().warn(
                "GPS SINYALI KESILDI (x=%.2f, y=%.2f) -> dead reckoning baslıyor" % (x, y))
        elif (not now_in_zone) and self.in_zone:
            if self.zone_enter_stamp is not None:
                dt = (self.get_clock().now() - self.zone_enter_stamp).nanoseconds / 1e9
            else:
                dt = float('nan')
            self.get_logger().info(
                "GPS SINYALI GERI GELDI (kayip suresi: %.1f sn)" % dt)

        self.in_zone = now_in_zone

        active_msg = Bool()
        active_msg.data = self.in_zone
        self.pub_zone_active.publish(active_msg)

        text_msg = String()
        text_msg.data = "Mod: DEAD RECKONING (GPS YOK)" if self.in_zone else "Mod: NORMAL (GPS VAR)"
        self.pub_zone_text.publish(text_msg)

    # ------------------------------------------------------------------
    def on_gps(self, msg: NavSatFix):
        if not self.in_zone:
            self.pub_gps.publish(msg)
            return

        if self.mode == 'drop':
            # Mesaji yutuyoruz: navsat_transform_node hicbir guncelleme almaz.
            return

        # mode == 'degrade': mesaji bozarak yayinla
        msg.status.status = NavSatStatus.STATUS_NO_FIX
        msg.position_covariance = [
            self.degraded_cov, 0.0, 0.0,
            0.0, self.degraded_cov, 0.0,
            0.0, 0.0, self.degraded_cov,
        ]
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self.pub_gps.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = GpsLossSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
