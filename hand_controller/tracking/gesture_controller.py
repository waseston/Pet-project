import math
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class GestureController:
    PINCH_RATIO = 0.28   # dist(thumb, index) / hand_size
    SMOOTH_WIN  = 6      # moving-average window for cursor

    def __init__(self, frame_w: int, frame_h: int):
        self.fw, self.fh = frame_w, frame_h
        self.sw, self.sh = pyautogui.size()

        self.enabled   = True
        self.dragging  = False
        self._pinching = False       # edge-detection: click fires once
        self._stop_arm = False       # edge-detection: toggle fires once
        self._hist: list[tuple[int,int]] = []

    # ── public API ────────────────────────────────────────────────────────

    def update(self, fingers: list[int], landmarks: list[tuple]) -> str:
        """
        Call every frame with current finger states + landmarks.
        Returns gesture label string (for the overlay).
        """
        gesture = self._classify(fingers, landmarks)

        # Stop-toggle: fires on leading edge only
        if gesture == "stop":
            if not self._stop_arm:
                self.enabled = not self.enabled
                self._stop_arm = True
            self._release_drag()
            return "PAUSED" if not self.enabled else "ACTIVE"
        else:
            self._stop_arm = False

        if not self.enabled:
            self._release_drag()
            return "PAUSED"

        # Gesture actions
        if gesture == "open_palm":
            self._release_drag()
            self._move_cursor(landmarks)

        elif gesture == "fist":
            self._release_drag()   # safety: resolve any pinch first
            self._start_drag()

        elif gesture == "pinch":
            self._release_drag()
            if not self._pinching:   # click on leading edge only
                pyautogui.click()
                self._pinching = True

        else:
            self._release_drag()

        if gesture != "pinch":
            self._pinching = False

        return gesture

    # ── private ───────────────────────────────────────────────────────────

    def _classify(self, fingers: list[int], landmarks: list[tuple]) -> str:
        if fingers == [1, 0, 0, 0, 1]:
            return "stop"
        if self._is_pinch(landmarks):
            return "pinch"
        if fingers == [1, 1, 1, 1, 1]:
            return "open_palm"
        if fingers == [0, 0, 0, 0, 0]:
            return "fist"
        return "unknown"

    def _is_pinch(self, landmarks: list[tuple]) -> bool:
        lm = {i: (x, y) for i, x, y in landmarks}
        if not {0, 4, 8, 12}.issubset(lm):
            return False
        dist      = math.dist(lm[4], lm[8])
        hand_size = math.dist(lm[0], lm[12])
        return hand_size > 0 and (dist / hand_size) < self.PINCH_RATIO

    def _move_cursor(self, landmarks: list[tuple]):
        """Smooth cursor movement driven by index fingertip (id=8)."""
        lm = {i: (x, y) for i, x, y in landmarks}
        if 8 not in lm:
            return
        x, y = lm[8]
        sx = int((1 - x / self.fw) * self.sw)
        sy = int(y / self.fh * self.sh)

        self._hist.append((sx, sy))
        if len(self._hist) > self.SMOOTH_WIN:
            self._hist.pop(0)

        ax = int(sum(p[0] for p in self._hist) / len(self._hist))
        ay = int(sum(p[1] for p in self._hist) / len(self._hist))
        pyautogui.moveTo(ax, ay)

    def _start_drag(self):
        if not self.dragging:
            pyautogui.mouseDown()
            self.dragging = True

    def _release_drag(self):
        if self.dragging:
            pyautogui.mouseUp()
            self.dragging = False