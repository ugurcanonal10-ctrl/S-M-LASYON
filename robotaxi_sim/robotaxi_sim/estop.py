import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from geometry_msgs.msg import Twist
import sys
import termios
import tty
import threading


class EStop(Node):
    def __init__(self):
        super().__init__('estop_node')

        # --- DURUM MAKİNESİ (FSM) DEĞİŞKENLERİ ---
        self.estop_active = False
        self.gps_lost = False          # Görev 4: GPS kesinti durumu
        self.current_state = "NORMAL"  # Başlangıç durumu

        # Abonelikler ve Yayıncılar
        self.sub = self.create_subscription(Bool, '/estop', self.estop_cb, 10)
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel_raw', self.cmd_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(Bool, '/estop_status', 10)

        # Görev 4: Durum bilgisini diğer düğümlere/arayüze yayınlayacak topic
        self.fsm_text_pub = self.create_publisher(String, '/fsm_status_text', 10)

        # --- OTOMATIK GPS-KAYBI ENTEGRASYONU (Ahmet, Gorev 1 ile baglanti) ---
        # gps_loss_zone paketindeki gps_loss_simulator node'u, arac tunel
        # bolgesine girince/cikinca bu topic'i otomatik True/False yapiyor.
        # Onceki surumde gps_lost SADECE klavyeden 'G' tusuyla degisiyordu -
        # yani gercek demoda arac tunele girdiginde FSM bunu hic gormuyordu,
        # kullanicinin elle G'ye basmasi gerekiyordu (zamanlama hatasina acik,
        # gercekci degil). Simdi iki kaynak da gps_lost'u etkiliyor:
        #   - /gps_loss/active (otomatik, asil demo akisi)
        #   - klavyeden 'G' tusu (manuel override, prova/test icin)
        self.gps_loss_sub = self.create_subscription(
            Bool, '/gps_loss/active', self.gps_loss_cb, 10)

        self.timer = self.create_timer(0.1, self.fsm_loop)

        self.get_logger().info('========================================')
        self.get_logger().info('  Gelişmiş FSM & E-Stop Node Başlatıldı')
        self.get_logger().info('  SPACE tuşu = Acil Durdur / Devam Et')
        self.get_logger().info('  G tuşu     = GPS Sinyalini Kes / Geri Getir (manuel override)')
        self.get_logger().info('  /gps_loss/active topic\'i otomatik dinleniyor (gercek tunel demosu)')
        self.get_logger().info('========================================')

        self.keyboard_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        self.keyboard_thread.start()

    def estop_cb(self, msg):
        self.estop_active = msg.data

    def gps_loss_cb(self, msg):
        # gps_loss_zone node'undan gelen OTOMATIK durum. Bu, klavyeden 'G'
        # ile yapilan manuel degisikligin de UZERINE yazar - yani gercek
        # tunel demosu sirasinda kimsenin G'ye basmasina gerek yok.
        if msg.data != self.gps_lost:
            self.gps_lost = msg.data
            kaynak = "otomatik (gps_loss_zone)"
            durum = "KESILDI" if msg.data else "GERI GELDI"
            self.get_logger().info(f'📡 GPS {durum} [{kaynak}]')

    def cmd_cb(self, msg):
        # Eğer E-Stop aktifse gelen hız komutlarını sıfırla, değilse aynen geçir
        if self.estop_active:
            self.cmd_pub.publish(Twist())
        else:
            self.cmd_pub.publish(msg)

    def fsm_loop(self):
        # --- SONLU DURUM MAKİNESİ (FSM) MANTIĞI ---
        if self.estop_active:
            self.current_state = "ESTOP AKTIF"
            self.cmd_pub.publish(Twist())  # Güvenlik amacıyla hızı kes
        elif self.gps_lost:
            self.current_state = "DEAD RECKONING"
        else:
            self.current_state = "NORMAL"

        # E-Stop durumunu yayınla
        bool_msg = Bool()
        bool_msg.data = self.estop_active
        self.status_pub.publish(bool_msg)

        # Ekran/Takip arayüzü için metin tabanlı durum bilgisini yayınla
        text_msg = String()
        text_msg.data = f"Mod: {self.current_state}"
        self.fsm_text_pub.publish(text_msg)

    def keyboard_listener(self):
        # Linux terminalinden ham (raw) karakter okuma ayarları
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)

                # --- SPACE: MANUEL ACİL DURDURMA ---
                if ch == ' ':
                    self.estop_active = not self.estop_active
                    if self.estop_active:
                        self.get_logger().warn('🚨 KLAVYEDEN ACİL DURDURMA AKTİF!')
                    else:
                        self.get_logger().info('✅ KLAVYEDEN E-STOP DEAKTİF. SÜRÜŞE HAZIR.')

                # --- G TUŞU: GPS KESİNTİSİ / DEAD RECKONING (manuel override) ---
                elif ch == 'g' or ch == 'G':
                    self.gps_lost = not self.gps_lost
                    if self.gps_lost:
                        self.get_logger().error('📡 GPS SINYALİ KESİLDİ! (manuel) Dead Reckoning moduna geçiliyor!')
                    else:
                        self.get_logger().info('📡 GPS SINYALİ GELDİ. (manuel) Normal moda dönülüyor.')

                # --- Q TUŞU: GÜVENLİ ÇIKIŞ ---
                elif ch == 'q' or ch == 'Q':
                    self.get_logger().info('Çıkılıyor...')
                    rclpy.shutdown()
                    break
        finally:
            # Terminal ayarlarını eski orijinal haline geri döndür
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main(args=None):
    rclpy.init(args=args)
    node = EStop()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
