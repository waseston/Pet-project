import cv2
from vision.camera import Camera
from vision.render import Renderer
from tracking.hand_tracker import HandTracker
from tracking.gesture_controller import GestureController


class App:
    def __init__(self):
        self.camera   = Camera()
        self.tracker  = HandTracker()
        self.renderer = Renderer()

        fw = int(self.camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fh = int(self.camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.gesture_ctrl = GestureController(fw, fh)

        self._last_fingers = None

    def run(self):
        try:
            while True:
                frame    = self.camera.read()
                landmarks = self.tracker.process(frame)
                fingers   = self.tracker.fingers_up(landmarks) if landmarks else []
                hand_landmarks_raw, connections = self.tracker.get_draw_data()

                gesture = ""
                if fingers and landmarks:
                    gesture = self.gesture_ctrl.update(fingers, landmarks)

                frame = self.renderer.draw(
                    frame, landmarks, fingers,
                    hand_landmarks_raw, connections, gesture
                )
                self.camera.show(frame)

                if fingers and fingers != self._last_fingers:
                    labels = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
                    states = ", ".join(
                        f"{l}: {'UP' if s else 'DOWN'}"
                        for l, s in zip(labels, fingers)
                    )
                    print(f"[{gesture}] {states}")
                    self._last_fingers = fingers

                if self.camera.should_quit():
                    break
        finally:
            self.camera.release()