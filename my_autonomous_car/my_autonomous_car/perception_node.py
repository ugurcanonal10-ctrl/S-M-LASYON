import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String, Float32
from cv_bridge import CvBridge
from .perception_pipeline import PerceptionPipeline

class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')
        self.bridge = CvBridge()
        self.perception = PerceptionPipeline(model_path="yolov8n.pt")
        
        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        
        self.pub_light = self.create_publisher(String, '/perception/traffic_light', 10)
        self.pub_sign = self.create_publisher(String, '/perception/sign', 10)
        self.pub_lane_error = self.create_publisher(Float32, '/perception/lane_error', 10)
        
        self.get_logger().info("[ALGI] Perception Node Baslatildi...")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            results = self.perception.process(cv_image)
            
            lane_error = Float32()
            lane_error.data = float(results["lane"].get("lane_offset", 0.0))
            self.pub_lane_error.publish(lane_error)
            
            if results["traffic_light"]["state"] != "none":
                light_msg = String()
                light_msg.data = results["traffic_light"]["state"]
                self.pub_light.publish(light_msg)
                
            if len(results["signs"]) > 0:
                sign_msg = String()
                sign_msg.data = results["signs"][0]["class"]
                self.pub_sign.publish(sign_msg)
        except Exception as e:
            self.get_logger().error(f"Algi Hatasi: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

