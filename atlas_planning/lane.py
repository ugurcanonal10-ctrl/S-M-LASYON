import cv2
import numpy as np

class LaneDetector:
    def __init__(self):
        self.prev_center = None

    def process(self, frame):
        h, w = frame.shape[:2]

        roi_y = int(h * 0.6)
        roi = frame[roi_y:h, :]

        if roi.size == 0:
            return {"lane_center": w/2, "lane_offset": 0.0, "lane_angle": 0.0}

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        white = cv2.inRange(hsv, (0, 0, 200), (180, 40, 255))
        yellow = cv2.inRange(hsv, (15, 80, 80), (40, 255, 255))
        mask = white + yellow

        blur = cv2.GaussianBlur(mask, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        lines = cv2.HoughLinesP(
            edges, 1, np.pi/180,
            threshold=40,
            minLineLength=40,
            maxLineGap=120
        )

        left, right = [], []

        if lines is not None:
            for l in lines:
                x1, y1, x2, y2 = l[0]
                if x2 - x1 == 0:
                    continue

                slope = (y2 - y1) / (x2 - x1)

                if abs(slope) < 0.4:
                    continue

                mid = (x1 + x2) / 2

                if slope < 0:
                    left.append(mid)
                else:
                    right.append(mid)

        if left and right:
            center = (np.mean(left) + np.mean(right)) / 2
        else:
            center = self.prev_center if self.prev_center else w/2

        if self.prev_center is not None:
            center = 0.7 * self.prev_center + 0.3 * center

        self.prev_center = center

        offset = (center - w/2) / w
        angle = offset * 45

        return {
            "lane_center": float(center),
            "lane_offset": float(offset),
            "lane_angle": float(angle)
        }