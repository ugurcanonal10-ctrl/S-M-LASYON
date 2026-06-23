import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

import cv2
import json

from perception import PerceptionPipeline


class PerceptionNode:

    def __init__(self):

        #  perception engine
        self.pipeline = PerceptionPipeline()

        #  ROS init
        self.bridge = CvBridge()

        #  subscriber (camera)
        rospy.Subscriber(
            "/camera/image_raw",
            Image,
            self.image_callback,
            queue_size=1
        )

        #  publishers
        self.pub = rospy.Publisher(
            "/perception_output",
            String,
            queue_size=10
        )

        self.emergency_pub = rospy.Publisher(
            "/emergency_stop",
            String,
            queue_size=10
        )

        self.speed_pub = rospy.Publisher(
            "/speed_cmd",
            String,
            queue_size=10
        )

        rospy.loginfo(" Perception Node Started")

    def image_callback(self, msg):

        #  ROS → OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")

        #  run perception
        output = self.pipeline.process(frame)

        #  convert to JSON string
        output_str = json.dumps(output)

        #  publish full perception
        self.pub.publish(output_str)

        #  emergency topic
        self.emergency_pub.publish(str(output["emergency_stop"]))

        #  speed topic
        self.speed_pub.publish(str(output["speed"]))

        #  debug
        rospy.loginfo_throttle(1, output)


if __name__ == "__main__":

    rospy.init_node("perception_node")

    node = PerceptionNode()

    rospy.spin()