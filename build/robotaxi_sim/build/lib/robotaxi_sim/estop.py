import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
import sys
import termios
import tty
import threading

class EStop(Node):
    def __init__(self):
        super().__init__('estop_node')
        self.estop_active = False

        # E-Stop topic dinle (harici buton/yazılım için)
        self.sub = self.create_subscription(Bool, '/estop', self.estop_cb, 10)

        # cmd_vel filtrele
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel_raw', self.cmd_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # E-Stop durumu yayınla
        self.status_pub = self.create_publisher(Bool, '/estop_status', 10)

        # Her 0.1 saniyede durum yayınla
        self.timer = self.create_timer(0.1, self.publish_status)

        self.get_logger().info('========================================')
        self.get_logger().info('  E-Stop Node Başlatıldı')
        self.get_logger().info('  SPACE tuşu = Acil Durdur / Devam Et')
        self.get_logger().info('  /estop topic = True/False ile de kontrol')
        self.get_logger().info('========================================')

        # Klavye thread'i
        self.keyboard_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        self.keyboard_thread.start()

    def estop_cb(self, msg):
        self.estop_active = msg.data
        if self.estop_active:
            self.get_logger().warn('🚨 ACİL DURUM AKTİF! Araç durduruluyor!')
            self.cmd_pub.publish(Twist())
        else:
            self.get_logger().info('✅ E-Stop deaktif. Normal operasyon.')

    def cmd_cb(self, msg):
        if not self.estop_active:
            self.cmd_pub.publish(msg)
        else:
            self.cmd_pub.publish(Twist())

    def publish_status(self):
        msg = Bool()
        msg.data = self.estop_active
        self.status_pub.publish(msg)
        if self.estop_active:
            self.cmd_pub.publish(Twist())  # Sürekli durdur

    def keyboard_listener(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch == ' ':
                    self.estop_active = not self.estop_active
                    if self.estop_active:
                        self.get_logger().warn('🚨 SPACE ile ACİL DURDURMA AKTİF!')
                    else:
                        self.get_logger().info('✅ SPACE ile E-Stop deaktif.')
                elif ch == 'q':
                    self.get_logger().info('Çıkılıyor...')
                    rclpy.shutdown()
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main(args=None):
    rclpy.init(args=args)
    node = EStop()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
