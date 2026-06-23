import cv2
import sys
from perception import PerceptionPipeline


def main():

    pipeline = PerceptionPipeline()

    #  default: webcam
    source = 0

    #  optional: video path
    if len(sys.argv) > 1:
        source = sys.argv[1]

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print("❌ Kamera / video açılamadı!")
        return

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        output = pipeline.process(frame)

        #  debug output
        print(output)

        #  visualization
        cv2.imshow("Robotaksi Perception", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()