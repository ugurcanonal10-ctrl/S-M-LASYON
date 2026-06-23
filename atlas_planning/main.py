import cv2
from perception import PerceptionPipeline

pipeline = PerceptionPipeline("weights/best.pt")

cap = cv2.VideoCapture("robodeneme4.mp4")  # 0 = webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break

    output = pipeline.process(frame)

    print(output)

    cv2.imshow("Robotaksi Perception", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()