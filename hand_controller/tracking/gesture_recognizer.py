import math
from dataclasses import dataclass
from enum import Enum, auto


class Gesture(Enum):
    NONE          = auto()
    FIST          = auto()   # all fingers closed
    OPEN_PALM     = auto()   # all fingers open
    POINTING      = auto()   # only index up
    PEACE         = auto()   # index + middle up
    THREE         = auto()   # index + middle + ring
    FOUR          = auto()   # all except thumb
    THUMBS_UP     = auto()   # only thumb up
    THUMBS_DOWN   = auto()   # thumb down (detected by angle)
    PINCH         = auto()   # thumb+index close together
    OK            = auto()   # pinch + other fingers up
    CALL_ME       = auto()   # thumb + pinky up
    ROCK          = auto()   # index + pinky up (horns)


PINCH_THRESHOLD = 40         # px — below this = pinch active
OPEN_THRESHOLD  = 0.75       # fraction of frame height — finger "long"


@dataclass
class GestureResult:
    gesture: Gesture
    confidence: float          # 0.0 – 1.0  (rough heuristic)
    pinch_active: bool
    pinch_distance: float
    fingers: list              # [thumb, index, middle, ring, pinky]
    palm_angle: float
    velocity: tuple            # (vx, vy) px/frame


class GestureRecognizer:
    """
    Rule-based gesture classifier.
    Input: one hand's data dict from HandTracker.process().
    Output: GestureResult.
    """

    def recognize(self, hand_data: dict) -> GestureResult:
        fingers  = hand_data['fingers']          # [0/1 × 5]
        pinch    = hand_data['pinch']
        angle    = hand_data['palm_angle']
        velocity = hand_data['velocity']

        pinch_active = pinch < PINCH_THRESHOLD

        gesture, confidence = self._classify(fingers, pinch_active, angle)

        return GestureResult(
            gesture=gesture,
            confidence=confidence,
            pinch_active=pinch_active,
            pinch_distance=pinch,
            fingers=fingers,
            palm_angle=angle,
            velocity=velocity,
        )

    # ------------------------------------------------------------------ #
    #  Classification rules                                                #
    # ------------------------------------------------------------------ #

    def _classify(self, f: list, pinch: bool, angle: float):
        """
        f = [thumb, index, middle, ring, pinky]
        Returns (Gesture, confidence).
        """
        total = sum(f)

        # ── Pinch family ──────────────────────────────────────────────
        if pinch and f[1] == 0:                          # strict pinch
            if total == 1:                               # only thumb up
                return Gesture.PINCH, 0.9
            if f[2] == 1 and f[3] == 1 and f[4] == 1:   # pinch + 3 fingers = OK
                return Gesture.OK, 0.85

        # ── All fingers ───────────────────────────────────────────────
        if total == 0:
            return Gesture.FIST, 0.95

        if total == 5:
            return Gesture.OPEN_PALM, 0.95

        # ── Single fingers ────────────────────────────────────────────
        if f == [0, 1, 0, 0, 0]:
            return Gesture.POINTING, 0.93

        if f == [1, 0, 0, 0, 0]:
            # Thumb direction determines up/down
            if -30 < angle < 60:
                return Gesture.THUMBS_UP, 0.88
            elif angle < -60 or angle > 120:
                return Gesture.THUMBS_DOWN, 0.75
            return Gesture.THUMBS_UP, 0.70

        # ── Two fingers ───────────────────────────────────────────────
        if f == [0, 1, 1, 0, 0]:
            return Gesture.PEACE, 0.92

        if f == [1, 0, 0, 0, 1]:
            return Gesture.CALL_ME, 0.88

        if f == [0, 1, 0, 0, 1]:
            return Gesture.ROCK, 0.88

        # ── Three/Four fingers ────────────────────────────────────────
        if f == [0, 1, 1, 1, 0]:
            return Gesture.THREE, 0.88

        if f == [0, 1, 1, 1, 1]:
            return Gesture.FOUR, 0.88

        return Gesture.NONE, 0.0

    def label(self, result: GestureResult) -> str:
        """Human-readable one-liner for overlay text."""
        names = {
            Gesture.NONE:       "—",
            Gesture.FIST:       "✊ Fist",
            Gesture.OPEN_PALM:  "✋ Open Palm",
            Gesture.POINTING:   "☝ Pointing",
            Gesture.PEACE:      "✌ Peace",
            Gesture.THREE:      "3️  Three",
            Gesture.FOUR:       "4️  Four",
            Gesture.THUMBS_UP:  "👍 Thumbs Up",
            Gesture.THUMBS_DOWN:"👎 Thumbs Down",
            Gesture.PINCH:      "🤌 Pinch",
            Gesture.OK:         "👌 OK",
            Gesture.CALL_ME:    "🤙 Call Me",
            Gesture.ROCK:       "🤘 Rock",
        }
        return names.get(result.gesture, "?")