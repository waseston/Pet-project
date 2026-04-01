import cv2
import mediapipe as mp

# Цвет и метка для каждого жеста
_GESTURE_STYLE = {
    "open_palm": ((0, 200, 0),   "MOVE"),
    "pinch":     ((0, 180, 255), "CLICK"),
    "fist":      ((0, 80, 255),  "DRAG"),
    "stop":      ((180, 0, 255), "STOP"),
    "PAUSED":    ((80, 80, 80),  "PAUSED"),
    "ACTIVE":    ((0, 255, 180), "ACTIVE"),
    "unknown":   ((60, 60, 60),  "---"),
}


class Renderer:
    def __init__(self):
        self.mp_draw = mp.solutions.drawing_utils

    def draw(self, frame, landmarks, fingers,
             hand_landmarks_raw=None, connections=None, gesture: str = ""):

        # Hand skeleton
        if hand_landmarks_raw and connections:
            for hand_lm in hand_landmarks_raw:
                self.mp_draw.draw_landmarks(frame, hand_lm, connections)

        # Index fingertip dot + coords
        for lm in landmarks:
            id, x, y = lm
            if id == 8:
                cv2.circle(frame, (x, y), 10, (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, f"{x},{y}", (x, y - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Gesture overlay (top-left pill)
        if gesture:
            color, label = _GESTURE_STYLE.get(gesture, ((60, 60, 60), gesture.upper()))
            cv2.rectangle(frame, (8, 8), (200, 48), (20, 20, 20), -1)
            cv2.rectangle(frame, (8, 8), (200, 48), color, 2)
            cv2.putText(frame, label, (18, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

        return frame