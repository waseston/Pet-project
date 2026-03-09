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
        fingers = []

        tips = [4, 8, 12, 16, 20]

        # Большой палец (немного другая логика)
        if landmarks[tips[0]][1] > landmarks[tips[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Остальные пальцы
        for i in range(1, 5):

            if landmarks[tips[i]][2] < landmarks[tips[i] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers



    def process(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        landmarks_list = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                h, w, c = frame.shape

                for id, lm in enumerate(hand_landmarks.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)

                    landmarks_list.append((id, cx, cy))

                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )
        
    

        return frame, landmarks_list,