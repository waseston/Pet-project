from vision.camera import Camera
from vision.renderer import Renderer
from tracking.hand_tracker import HandTracker

class App:
    def __init__(self):
        self.camera = Camera()
        self.tracker = HandTracker()
        self.renderer = Renderer()

    def run(self):
        while True:
            frame = self.camera.read()
            frame, landmarks = self.tracker.process(frame)
            fingers = self.tracker.fingers_up(landmarks) if landmarks else []
            self.renderer.draw(frame, landmarks, fingers)
            if self.camera.should_quit():
                break
        self.camera.release()