import cv2
import mediapipe as mp
import numpy as np
import math
from collections import deque


class HandTracker:
    """
    Enhanced hand tracker — Stage 2 + Stage 3.
    Tracks 21 landmarks per hand, computes finger states,
    pinch distance, palm angle, and velocity with EMA smoothing.
    """

    # Landmark indices
    TIPS   = [4, 8, 12, 16, 20]
    KNUCK  = [3, 6, 10, 14, 18]   # one joint below tip (for bend detection)
    WRIST  = 0
    PALM_CENTER = 9               # middle-finger MCP ≈ palm centre

    def __init__(self, max_hands: int = 2, smooth_factor: float = 0.6):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles

        # EMA smoothing buffer: hand_id → {lm_id: deque}
        self._smooth: dict[int, dict[int, deque]] = {}
        self.smooth_factor = smooth_factor          # α for EMA

        # Velocity tracking
        self._prev_palm: dict[int, tuple] = {}      # hand_id → (x, y)
        self._velocities: dict[int, tuple] = {}     # hand_id → (vx, vy)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def process(self, frame: np.ndarray):
        """
        Detect hands, smooth landmarks, draw skeleton.

        Returns
        -------
        frame        : annotated BGR frame
        hands_data   : list of dicts, one per detected hand:
            {
              'landmarks': [(id, x, y), ...],   # smoothed pixel coords
              'fingers':   [0/1, 0/1, 0/1, 0/1, 0/1],
              'pinch':     float,               # px distance index↔thumb
              'palm_angle': float,              # degrees, tilt of palm
              'velocity':  (vx, vy),            # px / frame
              'handedness': 'Left' | 'Right',
            }
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        hands_data = []

        if results.multi_hand_landmarks:
            h, w, _ = frame.shape

            for hand_idx, (hand_lms, handedness) in enumerate(
                zip(results.multi_hand_landmarks,
                    results.multi_handedness)
            ):
                label = handedness.classification[0].label  # 'Left'/'Right'

                # ── Raw pixel coords ──────────────────────────────────────
                raw = {}
                for lm_id, lm in enumerate(hand_lms.landmark):
                    raw[lm_id] = (int(lm.x * w), int(lm.y * h))

                # ── EMA smoothing ─────────────────────────────────────────
                smoothed = self._smooth_landmarks(hand_idx, raw)

                lm_list = [(lm_id, x, y) for lm_id, (x, y) in smoothed.items()]

                # ── Gesture features ──────────────────────────────────────
                fingers    = self._fingers_up(smoothed, label)
                pinch      = self._pinch_distance(smoothed)
                palm_angle = self._palm_angle(smoothed)
                velocity   = self._calc_velocity(hand_idx, smoothed)

                hands_data.append({
                    'landmarks':  lm_list,
                    'fingers':    fingers,
                    'pinch':      pinch,
                    'palm_angle': palm_angle,
                    'velocity':   velocity,
                    'handedness': label,
                })

                # ── Draw skeleton ─────────────────────────────────────────
                # rebuild NormalizedLandmarkList with smoothed coords
                # (just draw original — smoothing is visual-only difference)
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw_styles.get_default_hand_landmarks_style(),
                    self.mp_draw_styles.get_default_hand_connections_style(),
                )

                # Palm-angle indicator
                self._draw_angle_indicator(frame, smoothed, palm_angle)

        return frame, hands_data

    # ------------------------------------------------------------------ #
    #  Feature Extraction                                                  #
    # ------------------------------------------------------------------ #

    def _fingers_up(self, lm: dict, handedness: str) -> list[int]:
        """Return [thumb, index, middle, ring, pinky] — 1=extended, 0=bent."""
        fingers = []

        # Thumb: compare x-axis (flipped for Left hand)
        tip_x  = lm[self.TIPS[0]][0]
        base_x = lm[self.TIPS[0] - 1][0]
        if handedness == 'Right':
            fingers.append(1 if tip_x < base_x else 0)
        else:
            fingers.append(1 if tip_x > base_x else 0)

        # Fingers 1-4: tip y < pip y  (higher on screen = extended)
        for i in range(1, 5):
            tip_y = lm[self.TIPS[i]][1]
            pip_y = lm[self.TIPS[i] - 2][1]
            fingers.append(1 if tip_y < pip_y else 0)

        return fingers

    def _pinch_distance(self, lm: dict) -> float:
        """Euclidean px distance between thumb tip (4) and index tip (8)."""
        x1, y1 = lm[4]
        x2, y2 = lm[8]
        return math.hypot(x2 - x1, y2 - y1)

    def _palm_angle(self, lm: dict) -> float:
        """
        Angle of the palm normal vector (wrist → middle-MCP),
        in degrees from horizontal. Positive = tilted right.
        """
        wx, wy = lm[self.WRIST]
        px, py = lm[self.PALM_CENTER]
        angle = math.degrees(math.atan2(wy - py, px - wx))
        return angle

    def _calc_velocity(self, hand_idx: int, lm: dict) -> tuple[float, float]:
        """Palm velocity in px/frame using EMA."""
        cx, cy = lm[self.PALM_CENTER]
        if hand_idx in self._prev_palm:
            px, py = self._prev_palm[hand_idx]
            raw_vx, raw_vy = cx - px, cy - py
            if hand_idx in self._velocities:
                old_vx, old_vy = self._velocities[hand_idx]
                vx = self.smooth_factor * raw_vx + (1 - self.smooth_factor) * old_vx
                vy = self.smooth_factor * raw_vy + (1 - self.smooth_factor) * old_vy
            else:
                vx, vy = raw_vx, raw_vy
        else:
            vx, vy = 0.0, 0.0

        self._prev_palm[hand_idx] = (cx, cy)
        self._velocities[hand_idx] = (vx, vy)
        return (vx, vy)

    # ------------------------------------------------------------------ #
    #  Smoothing                                                           #
    # ------------------------------------------------------------------ #

    def _smooth_landmarks(self, hand_idx: int, raw: dict) -> dict:
        """
        Apply Exponential Moving Average to each landmark.
        α = smooth_factor  (0 = very smooth, 1 = no smoothing)
        """
        if hand_idx not in self._smooth:
            self._smooth[hand_idx] = {lm_id: deque(maxlen=5) for lm_id in raw}

        smoothed = {}
        buf = self._smooth[hand_idx]

        for lm_id, (x, y) in raw.items():
            if lm_id not in buf:
                buf[lm_id] = deque(maxlen=5)
            buf[lm_id].append((x, y))
            # EMA over deque
            xs = [p[0] for p in buf[lm_id]]
            ys = [p[1] for p in buf[lm_id]]
            sx = int(np.mean(xs))
            sy = int(np.mean(ys))
            smoothed[lm_id] = (sx, sy)

        return smoothed

    # ------------------------------------------------------------------ #
    #  Drawing Helpers                                                     #
    # ------------------------------------------------------------------ #

    def _draw_angle_indicator(self, frame, lm: dict, angle: float):
        """Draw a small arrow showing palm tilt."""
        cx, cy = lm[self.PALM_CENTER]
        length = 40
        end_x = int(cx + length * math.cos(math.radians(angle)))
        end_y = int(cy - length * math.sin(math.radians(angle)))
        cv2.arrowedLine(frame, (cx, cy), (end_x, end_y),
                        (255, 200, 0), 2, tipLength=0.35)