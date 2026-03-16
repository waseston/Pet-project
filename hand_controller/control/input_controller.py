"""
control/input_controller.py
Cross-platform abstraction for mouse / keyboard emulation.

Usage
-----
from control.input_controller import InputController
ctrl = InputController()
ctrl.move_cursor(x, y)
ctrl.click()
ctrl.scroll(dy)
"""

import platform
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    try:
        import evdev  # noqa: F401  (Linux only — silences Pylance on Windows)
    except ImportError:
        pass

_OS = platform.system()   # 'Windows' | 'Linux' | 'Darwin'


# ────────────────────────────────────────────────────────────────────────────
#  Backend implementations
# ────────────────────────────────────────────────────────────────────────────

class _PyAutoGUIBackend:
    """Works on Windows, macOS, and most Linux (X11) distros."""

    def __init__(self):
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0          # no artificial delay
        self._pg = pyautogui
        w, h = pyautogui.size()
        self.screen_w = w
        self.screen_h = h

    def move(self, x: int, y: int):
        self._pg.moveTo(x, y, duration=0)

    def click(self, btn: str = 'left'):
        self._pg.click(button=btn)

    def press(self, btn: str = 'left'):
        self._pg.mouseDown(button=btn)

    def release(self, btn: str = 'left'):
        self._pg.mouseUp(button=btn)

    def scroll(self, dy: int):
        self._pg.scroll(dy)

    def key_press(self, key: str):
        self._pg.press(key)


class _EvdevBackend:
    """Linux-only, works on Wayland too (needs write access to /dev/uinput)."""

    def __init__(self):
        import evdev
        from evdev import UInput, ecodes as e
        cap = {
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
            e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
        }
        self._ui = UInput(cap, name='gesture-mouse')
        import subprocess
        res = subprocess.check_output(['xrandr']).decode()
        # naive: grab first 'connected primary ...' resolution
        self.screen_w, self.screen_h = 1920, 1080
        self._e = e
        self._cur_x = 0
        self._cur_y = 0

    def move(self, x: int, y: int):
        dx = x - self._cur_x
        dy = y - self._cur_y
        self._ui.write(self._e.EV_REL, self._e.REL_X, dx)
        self._ui.write(self._e.EV_REL, self._e.REL_Y, dy)
        self._ui.syn()
        self._cur_x = x
        self._cur_y = y

    def click(self, btn: str = 'left'):
        code = {'left': self._e.BTN_LEFT,
                'right': self._e.BTN_RIGHT,
                'middle': self._e.BTN_MIDDLE}[btn]
        self._ui.write(self._e.EV_KEY, code, 1)
        self._ui.write(self._e.EV_KEY, code, 0)
        self._ui.syn()

    def press(self, btn: str = 'left'):
        code = {'left': self._e.BTN_LEFT, 'right': self._e.BTN_RIGHT}[btn]
        self._ui.write(self._e.EV_KEY, code, 1)
        self._ui.syn()

    def release(self, btn: str = 'left'):
        code = {'left': self._e.BTN_LEFT, 'right': self._e.BTN_RIGHT}[btn]
        self._ui.write(self._e.EV_KEY, code, 0)
        self._ui.syn()

    def scroll(self, dy: int):
        self._ui.write(self._e.EV_REL, self._e.REL_WHEEL, dy)
        self._ui.syn()

    def key_press(self, _key: str):
        pass   # not implemented for evdev backend


class _NullBackend:
    """Fallback — logs actions without performing them."""
    screen_w, screen_h = 1920, 1080

    def move(self, x, y): pass
    def click(self, btn='left'): print(f"[NullBackend] click {btn}")
    def press(self, btn='left'): print(f"[NullBackend] press {btn}")
    def release(self, btn='left'): print(f"[NullBackend] release {btn}")
    def scroll(self, dy): print(f"[NullBackend] scroll {dy}")
    def key_press(self, key): print(f"[NullBackend] key {key}")


# ────────────────────────────────────────────────────────────────────────────
#  Public controller
# ────────────────────────────────────────────────────────────────────────────

class InputController:
    """
    Platform-independent cursor + click controller.

    Parameters
    ----------
    backend   : 'auto' | 'pyautogui' | 'evdev' | 'null'
    cam_w, cam_h     : camera frame resolution
    dead_zone : fraction of cam frame treated as dead zone at edges
    smoothing : EMA α for cursor movement (0=frozen, 1=raw)
    """

    def __init__(
        self,
        backend: str = 'auto',
        cam_w: int = 640,
        cam_h: int = 480,
        dead_zone: float = 0.1,
        smoothing: float = 0.25,
    ):
        self._backend = self._init_backend(backend)
        self.cam_w = cam_w
        self.cam_h = cam_h
        self.dead_zone = dead_zone
        self.smoothing = smoothing

        self._sx = self._backend.screen_w // 2
        self._sy = self._backend.screen_h // 2
        self._dragging = False

    # ── public ───────────────────────────────────────────────────────────

    @property
    def screen_size(self):
        return self._backend.screen_w, self._backend.screen_h

    def move_cursor(self, cam_x: int, cam_y: int):
        """Map a camera pixel → screen pixel and move cursor there."""
        tx, ty = self._cam_to_screen(cam_x, cam_y)
        # EMA smooth
        self._sx = int(self.smoothing * tx + (1 - self.smoothing) * self._sx)
        self._sy = int(self.smoothing * ty + (1 - self.smoothing) * self._sy)
        self._backend.move(self._sx, self._sy)

    def click(self, btn: str = 'left'):
        self._backend.click(btn)

    def start_drag(self):
        if not self._dragging:
            self._backend.press('left')
            self._dragging = True

    def stop_drag(self):
        if self._dragging:
            self._backend.release('left')
            self._dragging = False

    def scroll(self, dy: int):
        """dy > 0 = scroll up, dy < 0 = scroll down."""
        self._backend.scroll(dy)

    def key_press(self, key: str):
        self._backend.key_press(key)

    # ── coordinate mapping ────────────────────────────────────────────────

    def _cam_to_screen(self, cx: int, cy: int) -> tuple[int, int]:
        dz = self.dead_zone
        # remap [dz·W, (1-dz)·W] → [0, screen_w]
        fx = (cx / self.cam_w - dz) / (1 - 2 * dz)
        fy = (cy / self.cam_h - dz) / (1 - 2 * dz)
        fx = max(0.0, min(1.0, fx))
        fy = max(0.0, min(1.0, fy))
        # mirror x (camera is flipped)
        fx = 1.0 - fx
        sw, sh = self._backend.screen_w, self._backend.screen_h
        return int(fx * sw), int(fy * sh)

    # ── backend factory ───────────────────────────────────────────────────

    @staticmethod
    def _init_backend(name: str):
        if name == 'null':
            return _NullBackend()

        if name == 'evdev' or (name == 'auto' and _OS == 'Linux'):
            try:
                b = _EvdevBackend()
                print("[InputController] Using evdev backend")
                return b
            except Exception as e:
                print(f"[InputController] evdev failed ({e}), falling back")

        try:
            b = _PyAutoGUIBackend()
            print("[InputController] Using pyautogui backend")
            return b
        except Exception as e:
            print(f"[InputController] pyautogui failed ({e}), using null backend")
            return _NullBackend()