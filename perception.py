from ultralytics import YOLO
import cv2
from lane import LaneDetector
from pathlib import Path


class PerceptionPipeline:
    def __init__(self, model_path=None):

        #  project root (cross-platform)
        BASE_DIR = Path(__file__).resolve().parent.parent

        if model_path is None:
            model_path = BASE_DIR / "models" / "best.pt"

        #  YOLO model
        self.model = YOLO(str(model_path))

        #  lane detector
        self.lane = LaneDetector()

        #  class sets (must match YOLO training labels)
        self.SIGN_CLASSES = {
            "stop", "parking", "yield", "no_entry",
            "speed_limit_20", "speed_limit_30", "speed_limit_50",
            "pedestrian_crossing"
        }

        self.OBSTACLE_CLASSES = {"person", "car", "bicycle"}

        self.LIGHT_CLASSES = {"traffic_light", "traffic light"}

        #  temporal safety memory
        self.emergency_counter = 0

    def process(self, frame):
        """
        INPUT: BGR image (numpy array)
        OUTPUT: dict (ROS-ready perception output)
        """

        h, w = frame.shape[:2]

        # -------------------------
        # LANE DETECTION
        # -------------------------
        lane = self.lane.process(frame)
        lane_offset = lane.get("lane_offset", 0.0)

        # -------------------------
        #  YOLO INFERENCE
        # -------------------------
        results = self.model(frame)[0]

        signs = []
        pedestrians = []
        traffic_light = {"state": "none"}

        emergency = False
        speed = 1.0

        # -------------------------
        #  DETECTION LOOP
        # -------------------------
        for box in results.boxes:

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if conf < 0.45:
                continue

            # normalize class name
            name = self.model.names[cls].lower().replace(" ", "_")

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # -------------------------
            #  TRAFFIC LIGHT
            # -------------------------
            if name in self.LIGHT_CLASSES:

                roi = frame[y1:y2, x1:x2]

                if roi.size > 0:
                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    mean = gray.mean()

                    if mean < 80:
                        state = "red"
                    elif mean < 150:
                        state = "yellow"
                    else:
                        state = "green"

                    traffic_light = {"state": state}

                    if state == "red":
                        emergency = True

            # -------------------------
            #  OBSTACLES
            # -------------------------
            elif name in self.OBSTACLE_CLASSES:

                pedestrians.append({
                    "bbox": (x1, y1, x2, y2),
                    "class": name,
                    "conf": conf
                })

                # close obstacle safety rule
                if y2 > h * 0.6:
                    emergency = True

            # -------------------------
            #  TRAFFIC SIGNS
            # -------------------------
            elif name in self.SIGN_CLASSES:

                signs.append(name)

                if name == "stop":
                    emergency = True

                elif name == "speed_limit_20":
                    speed = min(speed, 0.2)

                elif name == "speed_limit_30":
                    speed = min(speed, 0.3)

                elif name == "speed_limit_50":
                    speed = min(speed, 0.5)

        # -------------------------
        #  LANE INFLUENCE (SAFETY CLAMPED)
        # -------------------------
        speed = min(speed, 1.0 - abs(lane_offset))
        speed = max(0.0, speed)

        # -------------------------
        #  EMERGENCY MEMORY LOGIC
        # -------------------------
        if emergency:
            self.emergency_counter = 5
        else:
            self.emergency_counter = max(0, self.emergency_counter - 1)

        # -------------------------
        #  FINAL OUTPUT (ROS STANDARD)
        # -------------------------
        return {
            "lane": {
                "offset": float(lane_offset),
                "angle": float(lane.get("lane_angle", 0.0))
            },
            "traffic_signs": signs,
            "traffic_light": traffic_light,
            "obstacles": pedestrians,
            "emergency_stop": self.emergency_counter > 0,
            "speed": float(speed)
        }