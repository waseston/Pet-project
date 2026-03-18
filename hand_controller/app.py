from vision.camera import Camera
from vision.renderer import Renderer
from tracking.hand_tracker import HandTracker


class App:
    def __init__(self):
        self.camera = Camera()
        self.tracker = HandTracker()
        self.renderer = Renderer()
        self._last_fingers = None          # ← track previous state

    def run(self):
        try:
            while True:
                frame = self.camera.read()
                landmarks = self.tracker.process(frame)
                fingers = self.tracker.fingers_up(landmarks) if landmarks else []
                hand_landmarks_raw, connections = self.tracker.get_draw_data()
                frame = self.renderer.draw(frame, landmarks, fingers, hand_landmarks_raw, connections)
                self.camera.show(frame)

                # Only print when finger state changes
                if fingers and fingers != self._last_fingers:
                    labels = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
                    states = ", ".join(
                        f"{l}: {'UP' if s else 'DOWN'}"
                        for l, s in zip(labels, fingers)
                    )
                    print(f"Fingers → {states}")
                    self._last_fingers = fingers

                if self.camera.should_quit():
                    break
        finally:
            self.camera.release()