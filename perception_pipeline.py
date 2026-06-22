PERCEPTION PIPELINE                                                                                             from lane import LaneDetector
from ultralytics import YOLO
import cv2
import numpy as np


class PerceptionPipeline:
    def __init__(self, model_path="best.pt"):
        self.lane = LaneDetector()
        self.model = YOLO(model_path)

        # deterministic class sets
        self.SIGN_CLASSES = {"stop", "dur", "park_yeri"}
        self.OBSTACLE_CLASSES = {"person", "dinamik_engel", "koni", "bicycle", "car"}

        # flexible traffic light names
        self.LIGHT_NAMES = {"traffic_light", "trafik_isigi", "trafficlight"}

        # HARD STOP memory (hysteresis)
        self.emergency_counter = 0

    def process(self, frame):
        h, w = frame.shape[:2]

        # ==================================================
        # LANE DETECTION
        # ==================================================
        lane = self.lane.process(frame)

        lane_angle = lane.get("lane_angle", 0.0)
        lane_offset = abs(lane.get("lane_offset", 0.0))

        # ==================================================
        # YOLO INFERENCE
        # ==================================================
        results = self.model(frame)[0]

        signs = []
        pedestrians = []
        traffic_light = {"state": "none"}

        # HARD & SOFT CONTROL OUTPUTS
        emergency_stop = False
        speed_limit = 1.0

        # ==================================================
        # OBJECT PROCESSING
        # ==================================================
        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if conf < 0.45:
                continue

            name = self.model.names[cls].lower()

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # safety clamp
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)

            if x2 <= x1 or y2 <= y1:
                continue

            # ==================================================
            # TRAFFIC LIGHT (HARD STOP)
            # ==================================================
            if any(light in name for light in self.LIGHT_NAMES):

                roi = frame[y1:y2, x1:x2]

                if roi.size > 0:
                    state = self._light_state_v1(roi)

                    traffic_light = {
                        "state": state,
                        "bbox": (x1, y1, x2, y2),
                        "conf": conf
                    }

                    # HARD STOP condition
                    if state == "red" and y2 > h * 0.30:
                        emergency_stop = True

            # ==================================================
            # OBSTACLES (HARD STOP)
            # ==================================================
            elif name in self.OBSTACLE_CLASSES:

                pedestrians.append({
                    "bbox": (x1, y1, x2, y2),
                    "conf": conf
                })

                width = x2 - x1

                if (
                    y2 > h * 0.60 and
                    conf > 0.50 and
                    width > w * 0.05
                ):
                    emergency_stop = True

            # ==================================================
            # TRAFFIC SIGNS (HARD STOP)
            # ==================================================
            elif name in self.SIGN_CLASSES:

                signs.append({
                    "class": name,
                    "conf": conf,
                    "bbox": (x1, y1, x2, y2)
                })

                if name in {"stop", "dur"} and y2 > h * 0.60:
                    emergency_stop = True

        # ==================================================
        # SOFT CONTROL (LANE RISK → SPEED ONLY)
        # ==================================================
        lane_risk = False

        if abs(lane_angle) > 35:
            lane_risk = True
            speed_limit = 0.4

        if lane_offset > 0.35:
            lane_risk = True
            speed_limit = min(speed_limit, 0.5)

        # ==================================================
        # HARD STOP HYSTERESIS (FIXED - NO LOCK BUG)
        # ==================================================
        if emergency_stop:
            self.emergency_counter = 5
        else:
            if self.emergency_counter > 0:
                self.emergency_counter -= 1

        final_emergency = self.emergency_counter > 0

        # ==================================================
        # FINAL OUTPUT
        # ==================================================
        return {
            "lane": lane,
            "signs": signs,
            "traffic_light": traffic_light,

            # HARD CONTROL
            "emergency_stop": final_emergency,

            # SOFT CONTROL
            "speed_limit": speed_limit
        }

    # ==================================================
    # HSV TRAFFIC LIGHT DETECTION (ROBUST VERSION)
    # ==================================================
    def _light_state_v1(self, roi):
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        red1 = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
        red2 = cv2.inRange(hsv, (160, 100, 100), (180, 255, 255))
        red = cv2.countNonZero(red1 + red2)

        yellow = cv2.countNonZero(cv2.inRange(hsv, (15, 100, 100), (35, 255, 255)))
        green = cv2.countNonZero(cv2.inRange(hsv, (40, 70, 70), (90, 255, 255)))

        if red > yellow and red > green and red > 10:
            return "red"
        elif yellow > green and yellow > 10:
            return "yellow"
        elif green > 10:
            return "green"

        return "unknown"
