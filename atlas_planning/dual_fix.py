import torch
import cv2

# MODELS
sign_model = torch.hub.load('ultralytics/yolov5', 'custom',
                            path='runs/train/robotaksi_final2/weights/best.pt')
coco_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

cap = cv2.VideoCapture("robodeneme4.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # inference
    results1 = sign_model(frame)
    results2 = coco_model(frame)

    frame = results1.render()[0]
    frame = results2.render()[0]

    cv2.imshow("DUAL MODEL", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()