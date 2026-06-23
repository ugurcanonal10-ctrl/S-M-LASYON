import cv2
import numpy as np


class LaneDetector:
    def __init__(self):
        self.prev_center = None

    def process(self, frame):

        h, w = frame.shape[:2]

        #  ROI (lower half)
        roi_y = int(h * 0.6)
        roi = frame[roi_y:h, :]

        if roi.size == 0:
            return {
                "lane_center": float(w / 2),
                "lane_offset": 0.0,
                "lane_angle": 0.0
            }

        #  HSV conversion
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        #  lane color masks
        white = cv2.inRange(hsv, (0, 0, 200), (180, 40, 255))
        yellow = cv2.inRange(hsv, (15, 80, 80), (40, 255, 255))

        mask = cv2.bitwise_or(white, yellow)

        #  noise reduction
        blur = cv2.GaussianBlur(mask, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=40,
            minLineLength=40,
            maxLineGap=120
        )

        left, right = [], []

        #  line filtering
        if lines is not None:

            for l in lines:

                x1, y1, x2, y2 = l[0]

                # avoid division error
                if x2 - x1 == 0:
                    continue

                slope = (y2 - y1) / (x2 - x1)

                # remove horizontal noise
                if abs(slope) < 0.4:
                    continue

                mid = (x1 + x2) / 2

                if slope < 0:
                    left.append(mid)
                else:
                    right.append(mid)

        #  lane center estimation
        if left and right:
            center = (np.mean(left) + np.mean(right)) / 2
        elif left:
            center = np.mean(left)
        elif right:
            center = np.mean(right)
        else:
            center = self.prev_center if self.prev_center is not None else w / 2

        #  smoothing (low-pass filter)
        if self.prev_center is not None:
            center = 0.7 * self.prev_center + 0.3 * center

        self.prev_center = center

        #  normalize offset safely
        offset = (center - w / 2) / w
        offset = max(-1.0, min(1.0, offset))   # 🔥 safety clamp

        angle = offset * 45

        return {
            "lane_center": float(center),
            "lane_offset": float(offset),
            "lane_angle": float(angle)
        }