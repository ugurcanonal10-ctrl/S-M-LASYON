import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Float32, Bool

class AutonomousController(Node):
    def __init__(self):
        super().__init__('autonomous_controller')
        
        # --- DONANIMA (VEYA SİMÜLASYONA) GİDEN SÜRÜŞ KOMUTLARI ---
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # --- ATLAS PLANLAMA (FSM & DWA & HIZ) ABONELİKLERİ ---
        self.create_subscription(String, '/planning/behavior_command', self._cb_behavior, 10)
        self.create_subscription(Float32, '/planning/velocity_profile', self._cb_velocity, 10)
        self.create_subscription(Twist, '/planning/dwa_cmd_vel', self._cb_dwa, 10)
        self.create_subscription(Bool, '/safety/emergency', self._cb_emergency, 10)
        
        # --- ALGI (PERCEPTION) ABONELİĞİ ---
        # Şerit takip algoritmasını yazanlar, hatayı bu topic'e (Float32) publish etmeli
        self.create_subscription(Float32, '/perception/lane_error', self._cb_lane_error, 10)
        
        # --- KONTROL DEĞİŞKENLERİ ---
        self.behavior = 'LANE_FOLLOW'
        self.target_speed = 0.0
        self.dwa_cmd = Twist()
        self.emergency = False
        
        # --- ŞERİT PID AYARLARI ---
        self.kp = 1.2    # Virajlara karşı direksiyon tepkisi
        self.kd = 0.05   # Oskilasyon (Zikzak) sönümleyici 
        self.dt = 0.033  # Döngü süresi (1/30 saniye)
        self.lane_error = 0.0
        self.last_error = 0.0
        
        # Saniyede 30 defa motorlara güç basacak döngü
        self.timer = self.create_timer(self.dt, self.control_loop)
        
        self.get_logger().info("--- ATLAS KONTROLCÜSÜ AKTİF: ALGI TAKIMINDAN ŞERİT HATASI BEKLENİYOR ---")

    # ------------------------------------------------------------------ #
    #  PLANLAMA VE ALGI TAKIMINDAN GELEN VERİLERİN OKUNMASI              #
    # ------------------------------------------------------------------ #
    def _cb_behavior(self, msg: String):
        self.behavior = msg.data.upper()

    def _cb_velocity(self, msg: Float32):
        self.target_speed = msg.data

    def _cb_dwa(self, msg: Twist):
        self.dwa_cmd = msg

    def _cb_emergency(self, msg: Bool):
        self.emergency = msg.data
        if self.emergency:
            self.get_logger().fatal("UMS ACİL DURUM: FRENLER KİLİTLENDİ!")

    def _cb_lane_error(self, msg: Float32):
        # Kamerayı işleyen diğer düğümden gelen saf hata verisi
        self.lane_error = msg.data

    # ------------------------------------------------------------------ #
    #  ANA SÜRÜŞ DÖNGÜSÜ (KAS SİSTEMİ)                                   #
    # ------------------------------------------------------------------ #
    def control_loop(self):
        msg = Twist()
        
        # 1. GÜVENLİK DUVARI (HARD STOP)
        if self.emergency or self.behavior == 'EMERGENCY_STOP':
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.publisher_.publish(msg)
            return
            
        # 2. ENGELDEN KAÇMA VEYA PARK MANEVRASI (DWA ALGORİTMASI)
        if self.behavior in ['STATIC_OBSTACLE', 'DYNAMIC_OBSTACLE', 'PARKING_MANEUVER']:
            # Kontrolü Planlama takımının DWA algoritmasına bırakıyoruz
            msg.linear.x = self.dwa_cmd.linear.x
            msg.angular.z = self.dwa_cmd.angular.z
            
        # 3. DURMA DURUMLARI (Kırmızı Işık, Yolcu İndir/Bindir, Görev Sonu)
        elif self.behavior in ['RED_LIGHT', 'PASSENGER_PICKUP', 'PASSENGER_DROPOFF', 'MISSION_COMPLETE']:
            msg.linear.x = 0.0
            msg.angular.z = 0.0 # Direksiyonu düzle
            
        # 4. NORMAL ŞERİT TAKİBİ VE SEYİR (PID KONTROL)
        else:
            # Hız profili doğrudan Velocity Planner'dan gelir
            msg.linear.x = self.target_speed
            
            # PID Direksiyon Hesaplaması (Zamana Göre Doğru Türev)
            turev = (self.lane_error - self.last_error) / self.dt
            steering = (self.kp * self.lane_error) + (self.kd * turev)
            self.last_error = self.lane_error
            
            # Direksiyon polaritesi eksi ile tersine çevrildi ve limitleri artırıldı
            msg.angular.z = max(min(-steering, 1.5), -1.5)

        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = AutonomousController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
