import cv2
import mediapipe as mp


class Renderer:
    def __init__(self):
        self.mp_draw = mp.solutions.drawing_utils

    def draw(self, frame, landmarks, fingers, hand_landmarks_raw=None, connections=None):
        """
        Draws all visual elements onto the frame.
        - Skeleton connections via mediapipe raw landmarks
        - Highlighted index fingertip with coordinates
        - Finger state overlay (up/down)
        """
        # Draw hand skeleton
        if hand_landmarks_raw and connections:
            for hand_lm in hand_landmarks_raw:
                self.mp_draw.draw_landmarks(frame, hand_lm, connections)

        # Draw index fingertip highlight and coordinates
        for lm in landmarks:
            id, x, y = lm
            if id == 8:  # Index fingertip
                cv2.circle(frame, (x, y), 10, (0, 255, 0), cv2.FILLED)
                cv2.putText(
                    frame, f"Index: {x},{y}",
                    (x, y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2
                )

        # Draw finger states in top-left corner
        if fingers:
            labels = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
            for i, (label, state) in enumerate(zip(labels, fingers)):
                color = (0, 255, 0) if state else (0, 0, 255)
                text = f"{label}: {'UP' if state else 'DOWN'}"
                cv2.putText(
                    frame, text,
                    (10, 30 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, color, 2
                )

        return frame