"""
control/gesture_mapper.py

Maps GestureResult → OS input actions.
Handles cooldowns, drag state, and mode switching.
"""

import time
from tracking.gesture_recognizer import Gesture, GestureResult
from control.input_controller import InputController


class GestureMapper:
    """
    Stateful mapper: consumes a GestureResult each frame,
    decides what OS action to perform.

    Modes
    -----
    CURSOR  – index finger controls mouse, pinch = click
    SCROLL  – peace sign controls scroll wheel
    MEDIA   – thumb gestures control media keys
    """

    MODES = ['CURSOR', 'SCROLL', 'MEDIA']

    def __init__(self, controller: InputController, cooldown: float = 0.4):
        self.ctrl = controller
        self.cooldown = cooldown          # seconds between click actions
        self._last_action_time: dict = {}
        self._mode_idx = 0
        self._prev_gesture = Gesture.NONE
        self._pinch_was_active = False
        self._scroll_accum = 0.0

    # ── public ───────────────────────────────────────────────────────────

    @property
    def mode(self) -> str:
        return self.MODES[self._mode_idx]

    def process(self, hand_data: dict, result: GestureResult, lm: list):
        """
        Call once per frame per hand.

        Parameters
        ----------
        hand_data : raw dict from HandTracker
        result    : GestureResult from GestureRecognizer
        lm        : landmark list [(id,x,y), ...]
        """
        g = result.gesture

        # ── Mode switch: OPEN_PALM held for 1 s → cycle mode ─────────────
        if g == Gesture.OPEN_PALM:
            if self._can_act('mode_switch', debounce=1.0):
                self._mode_idx = (self._mode_idx + 1) % len(self.MODES)
                print(f"[GestureMapper] Mode → {self.mode}")
                self._mark('mode_switch')

        # ── Dispatch by mode ─────────────────────────────────────────────
        if self.mode == 'CURSOR':
            self._cursor_mode(result, lm)
        elif self.mode == 'SCROLL':
            self._scroll_mode(result)
        elif self.mode == 'MEDIA':
            self._media_mode(result)

        self._prev_gesture = g

    # ── Modes ─────────────────────────────────────────────────────────────

    def _cursor_mode(self, result: GestureResult, lm: list):
        g = result.gesture

        # Move cursor with index finger tip (id=8)
        if g in (Gesture.POINTING, Gesture.PINCH, Gesture.NONE):
            index_lm = next(((x, y) for id_, x, y in lm if id_ == 8), None)
            if index_lm:
                self.ctrl.move_cursor(*index_lm)

        # Pinch → left click (on rising edge only)
        if result.pinch_active and not self._pinch_was_active:
            if self._can_act('click', self.cooldown):
                self.ctrl.click('left')
                self._mark('click')

        # Pinch + move = drag
        if result.pinch_active:
            index_lm = next(((x, y) for id_, x, y in lm if id_ == 8), None)
            if index_lm:
                self.ctrl.start_drag()
                self.ctrl.move_cursor(*index_lm)
        else:
            self.ctrl.stop_drag()

        # Two-finger peace → right-click
        if g == Gesture.PEACE and self._prev_gesture != Gesture.PEACE:
            if self._can_act('right_click', self.cooldown):
                self.ctrl.click('right')
                self._mark('right_click')

        self._pinch_was_active = result.pinch_active

    def _scroll_mode(self, result: GestureResult):
        vx, vy = result.velocity
        # vertical velocity → scroll wheel
        SCROLL_SENSITIVITY = 0.15
        self._scroll_accum += -vy * SCROLL_SENSITIVITY
        if abs(self._scroll_accum) >= 1.0:
            ticks = int(self._scroll_accum)
            self.ctrl.scroll(ticks)
            self._scroll_accum -= ticks

    def _media_mode(self, result: GestureResult):
        g = result.gesture
        if g == self._prev_gesture:
            return           # only on new gesture
        mapping = {
            Gesture.THUMBS_UP:   'playpause',
            Gesture.THUMBS_DOWN: 'stop',
            Gesture.POINTING:    'nexttrack',
            Gesture.PEACE:       'prevtrack',
            Gesture.FIST:        'volumemute',
        }
        key = mapping.get(g)
        if key and self._can_act(f'media_{key}', self.cooldown):
            self.ctrl.key_press(key)
            self._mark(f'media_{key}')

    # ── Helpers ───────────────────────────────────────────────────────────

    def _can_act(self, action_id: str, debounce: float) -> bool:
        last = self._last_action_time.get(action_id, 0)
        return (time.time() - last) >= debounce

    def _mark(self, action_id: str):
        self._last_action_time[action_id] = time.time()