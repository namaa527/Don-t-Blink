import cv2
from hand_tracker import get_tracker

tracker = get_tracker()

camera = cv2.VideoCapture(0)

while True:
    success, frame = camera.read()

    if not success:
        break

    if tracker.update(frame):
        index_tip = tracker.index_tip()
        print("Index tip:", index_tip)

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()