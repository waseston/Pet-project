import cv2
import mediapipe as mp


class HandTracker:
    def __init__(self, max_hands=5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

    def fingers_up(self, landmarks):
        """Returns a list of 5 values (0 or 1) indicating which fingers are up."""
        fingers = []
        tips = [4, 8, 12, 16, 20]

        # Thumb (horizontal logic)
        if landmarks[tips[0]][1] > landmarks[tips[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Other four fingers (vertical logic)
        for i in range(1, 5):
            if landmarks[tips[i]][2] < landmarks[tips[i] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def process(self, frame):
        """Detects hand landmarks in a frame. Returns landmarks only (no drawing)."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        landmarks_list = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                h, w, _ = frame.shape

                for id, lm in enumerate(hand_landmarks.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    landmarks_list.append((id, cx, cy))

                # Store raw landmarks for drawing later
                self._last_hand_landmarks = results.multi_hand_landmarks
                self._last_connections = self.mp_hands.HAND_CONNECTIONS

        return landmarks_list

    def get_draw_data(self):
        """Returns raw mediapipe landmarks for the renderer to draw."""
        return getattr(self, '_last_hand_landmarks', []), \
               getattr(self, '_last_connections', None)