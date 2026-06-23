import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from .perception import PerceptionPipeline

class RobotaksiPerceptionNode(Node):
    def __init__(self):
        super().__init__('robotaksi_perception_node')
        
        # CvBridge, ROS 2 görüntüsünü OpenCV formatına (bgr8) çevirmek için şart
        self.bridge = CvBridge()
        
        # weights klasörü yerine dosyayı attığımız tam adresi veriyoruz
        model_yolu = "/root/robotaksi_ws/src/S-M-LASYON/atlas_planning/best.pt"
        self.pipeline = PerceptionPipeline(model_path=model_yolu)
        
        # Simülasyondaki ön kamerayı dinleyen asıl Subscriber satırı:
        self.subscription = self.create_subscription(
            Image,
            '/front_camera/image_raw',
            self.camera_callback,
            10
        )
        self.get_logger().info("Robotaksi Algılama Düğümü Başlatıldı. Ön kamera bekleniyor...")

    def camera_callback(self, msg):
        try:
            # ROS 2'den gelen mesajı OpenCV karesine (frame) dönüştür
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Senin perception pipeline fonksiyonunu çalıştır
            output = self.pipeline.process(frame)
            
            # Sonuçları terminale bas
            print(output)
            
            # NOT: Docker içinde cv2.imshow patladığı için o satırları kaldırdım. 
            # Verileri doğrudan yukarıdaki print(output) ile terminalden izleyeceksin.

        except Exception as e:
            self.get_logger().error(f"Görüntü işlenirken hata oluştu: {str(e)}")

def main(args=None):
    rclpy.init(args=args)
    node = RobotaksiPerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
