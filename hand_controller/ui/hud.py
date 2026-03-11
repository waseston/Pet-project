"""
ui/hud.py

Draws a clean HUD overlay on the camera feed.
"""

import cv2
import numpy as np
import time
from tracking.gesture_recognizer import GestureResult, GestureRecognizer


_recognizer = GestureRecognizer()


class HUD:
    """
    Stateless overlay renderer.
    Call HUD.draw(frame, ...) each frame.
    """

    # colour palette
    C_WHITE   = (255, 255, 255)
    C_GREEN   = (80, 230, 80)
    C_YELLOW  = (50, 220, 220)
    C_RED     = (60, 60, 240)
    C_CYAN    = (230, 200, 30)
    C_DARK    = (20, 20, 20)
    C_ORANGE  = (30, 140, 240)

    def __init__(self):
        self._fps_times = []
        self._last_fps  = 0.0

    def draw(
        self,
        frame: np.ndarray,
        hands_data: list,
        gesture_results: list,
        mode: str,
        active_action: str = "",
    ):
        h, w, _ = frame.shape

        # ── FPS ──────────────────────────────────────────────────────────
        now = time.time()
        self._fps_times.append(now)
        self._fps_times = [t for t in self._fps_times if now - t < 1.0]
        fps = len(self._fps_times)

        # ── Background strips ─────────────────────────────────────────────
        # Top bar
        cv2.rectangle(frame, (0, 0), (w, 38), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, 0), (w, 38), (50, 50, 50), 1)

        # ── Mode badge ────────────────────────────────────────────────────
        mode_colors = {
            'CURSOR': (60, 180, 60),
            'SCROLL': (200, 140, 30),
            'MEDIA':  (160, 50, 200),
        }
        mc = mode_colors.get(mode, self.C_WHITE)
        cv2.rectangle(frame, (8, 6), (130, 32), mc, -1)
        cv2.putText(frame, f"MODE: {mode}", (14, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.C_WHITE, 1, cv2.LINE_AA)

        # ── FPS ───────────────────────────────────────────────────────────
        cv2.putText(frame, f"FPS {fps:3d}", (w - 90, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.C_YELLOW, 1, cv2.LINE_AA)

        # ── Per-hand info ─────────────────────────────────────────────────
        for i, (hd, gr) in enumerate(zip(hands_data, gesture_results)):
            label   = _recognizer.label(gr)
            fingers = gr.fingers
            pinch   = gr.pinch_distance
            angle   = gr.palm_angle
            vx, vy  = gr.velocity
            speed   = (vx**2 + vy**2) ** 0.5
            side    = hd['handedness']

            panel_x = 8 + i * (w // 2)
            panel_y = h - 115

            # Panel BG
            overlay = frame.copy()
            cv2.rectangle(overlay, (panel_x - 4, panel_y),
                          (panel_x + 220, h - 8), (10, 10, 10), -1)
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

            # Hand side
            cv2.putText(frame, f"{side} hand", (panel_x, panel_y + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.C_CYAN, 1, cv2.LINE_AA)

            # Gesture label
            cv2.putText(frame, label, (panel_x, panel_y + 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.C_GREEN, 2, cv2.LINE_AA)

            # Finger bars
            names = ['T', 'I', 'M', 'R', 'P']
            for fi, (name, state) in enumerate(zip(names, fingers)):
                bx = panel_x + fi * 26
                color = self.C_GREEN if state else (80, 80, 80)
                cv2.rectangle(frame, (bx, panel_y + 44), (bx + 20, panel_y + 62), color, -1)
                cv2.putText(frame, name, (bx + 5, panel_y + 58),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.C_WHITE, 1)

            # Pinch indicator
            pinch_col = self.C_RED if gr.pinch_active else self.C_WHITE
            cv2.putText(frame, f"Pinch: {pinch:.0f}px", (panel_x, panel_y + 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, pinch_col, 1, cv2.LINE_AA)

            # Angle + speed
            cv2.putText(frame, f"Angle: {angle:+.0f}°  Speed: {speed:.1f}",
                        (panel_x, panel_y + 96),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, self.C_YELLOW, 1, cv2.LINE_AA)

        # ── Active action flash ───────────────────────────────────────────
        if active_action:
            cv2.putText(frame, active_action,
                        (w // 2 - 80, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, self.C_ORANGE, 3, cv2.LINE_AA)

        # ── Help hint ─────────────────────────────────────────────────────
        cv2.putText(frame,
                    "Open Palm (1s) = cycle mode  |  Q = quit",
                    (8, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (140, 140, 140), 1, cv2.LINE_AA)

        return frame