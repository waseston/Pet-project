from tracking.hand_tracker import HandTracker
import cv2


def main():
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()

    cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Hand Tracking", 960, 540)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, landmarks = tracker.process(frame)

        if landmarks:
            fingers = tracker.fingers_up(landmarks)
            print("Fingers:", fingers)
            
            for lm in landmarks:
                id, x, y = lm

                if id == 8:  # указательный палец
                    cv2.circle(frame, (x, y), 10, (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, f"Index: {x},{y}", (x, y-20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (0,255,0), 2)

        cv2.imshow("Hand Tracking", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()