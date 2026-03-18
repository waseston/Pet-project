from vision.camera import Camera
from vision.renderer import Renderer
from tracking.hand_tracker import HandTracker


class App:
    def __init__(self):
        self.camera = Camera()
        self.tracker = HandTracker()
        self.renderer = Renderer()

    def run(self):
        """Main application loop."""
        try:
            while True:
                frame = self.camera.read()

                landmarks = self.tracker.process(frame)
                fingers = self.tracker.fingers_up(landmarks) if landmarks else []
                hand_landmarks_raw, connections = self.tracker.get_draw_data()

                frame = self.renderer.draw(frame, landmarks, fingers, hand_landmarks_raw, connections)

                self.camera.show(frame)

                if self.camera.should_quit():
                    break

        finally:
            self.camera.release()