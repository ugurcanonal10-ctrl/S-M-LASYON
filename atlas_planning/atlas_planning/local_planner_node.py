"""
Atlas Takimi - Local Planner Node (DWA)
Dynamic Window Approach ile engel kacinma hesaplar.
Dinledigi topicler:
  /perception/obstacles -> std_msgs/String  (JSON: [{"x":1.2,"y":0.3}, ...])
  /planning/current_vel -> std_msgs/Float32 (m/s)
Yayinladigi topicler:
  /planning/dwa_result  -> std_msgs/String  ('cleared' / 'failed')
  /planning/dwa_cmd_vel -> geometry_msgs/Twist
"""
import json
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32
from geometry_msgs.msg import Twist

# --- Araç kısıtları ---
MAX_SPEED      = 2.0    # m/s
MIN_SPEED      = 0.0
MAX_YAWRATE    = 1.0    # rad/s
MAX_ACCEL      = 1.0    # m/s²
MAX_DYAWRATE   = 2.0    # rad/s²
DT             = 0.1    # simülasyon adımı (s)
PREDICT_TIME   = 2.0    # kaç saniyelik yol simüle edilsin
ROBOT_RADIUS   = 0.5    # çarpışma yarıçapı (m)

# --- Hız örnekleme adımları ---
V_SAMPLES      = 5
YAW_SAMPLES    = 11

# --- Hedef (araç koordinatında, daima düz ileri) ---
GOAL_X = 3.0
GOAL_Y = 0.0


class LocalPlannerNode(Node):
    def __init__(self):
        super().__init__('local_planner_node')
        self.get_logger().info('[LocalPlanner] DWA node baslatildi.')

        self._obstacles = []
        self._current_vel = 0.0

        self._pub_result = self.create_publisher(
            String, '/planning/dwa_result', 10)
        self._pub_cmd = self.create_publisher(
            Twist, '/planning/dwa_cmd_vel', 10)

        self.create_subscription(
            String, '/perception/obstacles', self._cb_obstacles, 10)
        self.create_subscription(
            Float32, '/planning/current_vel', self._cb_vel, 10)

        self.create_timer(0.1, self._timer_cb)  # 10 Hz

    def _cb_obstacles(self, msg: String):
        try:
            self._obstacles = json.loads(msg.data)
        except Exception:
            self._obstacles = []

    def _cb_vel(self, msg: Float32):
        self._current_vel = msg.data

    def _timer_cb(self):
        best_v, best_w = self._dwa_control()

        if best_v is None:
            # Güvenli yol bulunamadı
            result = String()
            result.data = 'failed'
            self._pub_result.publish(result)
            self.get_logger().warn('[LocalPlanner] Guclu yol bulunamadi!')
            return

        # Hız komutu yayınla
        cmd = Twist()
        cmd.linear.x = best_v
        cmd.angular.z = best_w
        self._pub_cmd.publish(cmd)

        # Engel temizlendi mi?
        if best_v > 0.1 and abs(best_w) < 0.8:
            result = String()
            result.data = 'cleared'
            self._pub_result.publish(result)

    def _dwa_control(self):
        """
        Dynamic Window Approach ana fonksiyonu.
        En iyi (v, w) çiftini döndürür.
        """
        dw = self._dynamic_window()
        best_score = -float('inf')
        best_v, best_w = None, None

        v_min, v_max, w_min, w_max = dw

        v_step = (v_max - v_min) / max(V_SAMPLES - 1, 1)
        w_step = (w_max - w_min) / max(YAW_SAMPLES - 1, 1)

        v = v_min
        while v <= v_max + 1e-6:
            w = w_min
            while w <= w_max + 1e-6:
                traj = self._simulate(v, w)
                if self._check_collision(traj):
                    w += w_step
                    continue
                score = self._score(traj, v)
                if score > best_score:
                    best_score = score
                    best_v = v
                    best_w = w
                w += w_step
            v += v_step

        return best_v, best_w

    def _dynamic_window(self):
        """
        Aracın fiziksel kısıtlarına göre erişilebilir hız penceresini hesapla.
        """
        v_min = max(MIN_SPEED, self._current_vel - MAX_ACCEL * DT)
        v_max = min(MAX_SPEED, self._current_vel + MAX_ACCEL * DT)
        w_min = -MAX_YAWRATE
        w_max =  MAX_YAWRATE
        return v_min, v_max, w_min, w_max

    def _simulate(self, v, w):
        """
        (v, w) ile PREDICT_TIME kadar yolu simüle et.
        Araç koordinatında başlar: x=0, y=0, yaw=0
        """
        x, y, yaw = 0.0, 0.0, 0.0
        traj = [(x, y)]
        t = 0.0
        while t < PREDICT_TIME:
            x   += v * math.cos(yaw) * DT
            y   += v * math.sin(yaw) * DT
            yaw += w * DT
            traj.append((x, y))
            t += DT
        return traj

    def _check_collision(self, traj):
        """
        Simüle edilen yolda herhangi bir engele çarpma var mı?
        """
        for (tx, ty) in traj:
            for obs in self._obstacles:
                ox, oy = obs.get('x', 0), obs.get('y', 0)
                dist = math.hypot(tx - ox, ty - oy)
                if dist < ROBOT_RADIUS:
                    return True
        return False

    def _score(self, traj, v):
        """
        Yolu puanla:
          - Hedefe yakınlık (yüksek puan = iyi)
          - Hız (yüksek puan = iyi)
        """
        end_x, end_y = traj[-1]
        goal_dist = math.hypot(GOAL_X - end_x, GOAL_Y - end_y)
        goal_score  = 1.0 / (goal_dist + 1e-6)
        speed_score = v / MAX_SPEED
        return goal_score + 0.5 * speed_score


def main(args=None):
    rclpy.init(args=args)
    node = LocalPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
