from ultralytics import YOLO
import cv2
from lane import LaneDetector

class PerceptionPipeline:
    def __init__(self, model_path="weights/best.pt"):
        self.model = YOLO(model_path)
        self.lane = LaneDetector()

        self.SIGN_CLASSES = {
            "stop", "parking", "yield", "no_entry",
            "speed_limit_20", "speed_limit_30", "speed_limit_50",
            "pedestrian_crossing"
        }

        self.OBSTACLE_CLASSES = {"person", "car", "bicycle"}

        self.LIGHT_CLASSES = {"traffic_light"}

        self.emergency_counter = 0

    def process(self, frame):
        h, w = frame.shape[:2]

        lane = self.lane.process(frame)
        results = self.model(frame)[0]

        signs = []
        pedestrians = []
        traffic_light = {"state": "none"}

        emergency = False
        speed = 1.0

        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if conf < 0.45:
                continue

            name = self.model.names[cls].lower()
            x1, y1, x2, y2 = map(int, box.xyxy[0])

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

            elif name in self.OBSTACLE_CLASSES:
                pedestrians.append({"bbox": (x1,y1,x2,y2)})
                if y2 > h*0.6:
                    emergency = True

            elif name in self.SIGN_CLASSES:
                signs.append(name)

                if name == "stop":
                    emergency = True
                elif "speed_limit_20" == name:
                    speed = 0.2
                elif "speed_limit_30" == name:
                    speed = 0.3

        # lane influence
        speed = min(speed, 1.0 - abs(lane["lane_offset"]))

        if emergency:
            self.emergency_counter = 5
        else:
            self.emergency_counter = max(0, self.emergency_counter - 1)

        return {
            "lane": lane,
            "signs": signs,
            "traffic_light": traffic_light,
            "pedestrians": pedestrians,
            "emergency_stop": self.emergency_counter > 0,
            "speed": speed
        }