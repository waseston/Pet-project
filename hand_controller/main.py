"""
main.py — Gesture Control Interface
====================================
Runs the full pipeline:
  Camera → HandTracker → GestureRecognizer → GestureMapper → OS Input

Controls
--------
  Q          quit
  1/2/3      switch mode manually (CURSOR / SCROLL / MEDIA)
  Open Palm  hold ~1 s  →  cycle mode
"""

import sys
import os
import cv2

# Add the directory containing main.py to sys.path
# so that utils/, tracking/, control/, ui/ are all importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vision.camera              import Camera
from tracking.hand_tracker      import HandTracker
from tracking.gesture_recognizer import GestureRecognizer
from control.input_controller   import InputController
from control.gesture_mapper     import GestureMapper
from ui.hud                     import HUD


def main():
    # ── Init ─────────────────────────────────────────────────────────────
    cam        = Camera(camera_id=0, width=1280, height=720, fps=30)
    tracker    = HandTracker(max_hands=2, smooth_factor=0.6)
    recognizer = GestureRecognizer()
    controller = InputController(
        backend='auto',
        cam_w=cam.width,
        cam_h=cam.height,
        dead_zone=0.10,
        smoothing=0.25,
    )
    mapper = GestureMapper(controller, cooldown=0.35)
    hud    = HUD()

    cv2.namedWindow("Gesture Control", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Gesture Control", 1280, 720)

    print("=== Gesture Control Interface ===")
    print("  Q — quit")
    print("  1 / 2 / 3 — switch mode")
    print("  Open Palm (1s) — cycle mode in-gesture")
    print("=================================")

    while True:
        frame = cam.read()
        if frame is None:
            print("[WARN] dropped frame")
            continue

        # ── Process ───────────────────────────────────────────────────────
        frame, hands_data = tracker.process(frame)

        gesture_results = []
        for hd in hands_data:
            gr = recognizer.recognize(hd)
            gesture_results.append(gr)
            mapper.process(hd, gr, hd['landmarks'])

        # ── HUD ───────────────────────────────────────────────────────────
        frame = hud.draw(frame, hands_data, gesture_results, mapper.mode)

        cv2.imshow("Gesture Control", frame)

        # ── Key handling ──────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            mapper._mode_idx = 0
        elif key == ord('2'):
            mapper._mode_idx = 1
        elif key == ord('3'):
            mapper._mode_idx = 2

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()