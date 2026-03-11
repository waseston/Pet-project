# Gesture Control Interface using Computer Vision

A computer vision project that enables interaction with a computer using hand gestures captured from a webcam.

The system detects and tracks hand landmarks in real time and serves as a foundation for gesture-based control interfaces.

## Features

- Real-time hand detection
- Hand landmark tracking
- Multi-hand support
- Visual feedback using landmarks

## Technologies

- Python 3.12.10
- OpenCV
- MediaPipe

## Installation

Clone the repository:

```bash
git clone https://github.com/waseston/Pet-project.git

cd hand_controler

```

## Install dependencies

```python

pip install opencv-python mediapipe

```

## Usage

Run the main script:

```pyhon

python main.py

```
The webcam will open and the system will start detecting hands.

## Project Structure

```bash

hand_controller
│
├── tracking
│   └── hand_tracker.py
├── vision
│   └── camera.py
├── main.py
└── README.md

```

# Gesture Control Interface

Vision-based input controller — Stages 2 → 4 of the roadmap.

```
gesture_control/
├── main.py                        ← entry point
├── requirements.txt
├── tracking/
│   ├── hand_tracker.py            ← Stage 2 + 3: MediaPipe + EMA smoothing
│   └── gesture_recognizer.py      ← Stage 3: rule-based classifier
├── control/
│   ├── input_controller.py        ← Stage 4: cross-platform OS input
│   └── gesture_mapper.py          ← Stage 4: gesture → action router
├── ui/
│   └── hud.py                     ← live overlay: FPS, fingers, mode
└── utils/
    └── camera.py                  ← camera abstraction
```

---

## Install

```bash
pip install -r requirements.txt
```

> **Linux / Wayland**: if `pyautogui` doesn't work, install `evdev` and run as root or add your user to the `input` group.

---

## Run

```bash
cd gesture_control
python main.py
```

---

## Modes

| Key | Mode    | How it works                                         |
|-----|---------|------------------------------------------------------|
| `1` | CURSOR  | Index finger tip moves cursor. Pinch = click. Peace = right-click. |
| `2` | SCROLL  | Move hand up/down to scroll.                         |
| `3` | MEDIA   | 👍 play/pause, 👎 stop, ☝ next, ✌ prev, ✊ mute     |

**Switch in-gesture**: hold Open Palm for ~1 s to cycle modes.

---

## Gestures recognised

| Gesture    | Fingers up             |
|------------|------------------------|
| Fist       | none                   |
| Open Palm  | all 5                  |
| Pointing   | index only             |
| Peace      | index + middle         |
| Three      | index + middle + ring  |
| Four       | all except thumb       |
| Thumbs Up  | thumb only, palm up    |
| Thumbs Down| thumb only, palm down  |
| Pinch      | thumb+index close      |
| OK         | pinch + 3 fingers      |
| Call Me    | thumb + pinky          |
| Rock       | index + pinky          |

---

## Architecture notes

### EMA smoothing (hand_tracker.py)
Each landmark coordinate runs through a 5-frame moving average, removing jitter without adding visible lag.

### Coordinate mapping (input_controller.py)
Camera space → screen space transform:
1. Dead-zone crop (default 10% edges) eliminates border instability.
2. X-axis mirror (camera is flipped).
3. EMA on final screen coords (α = 0.25) for smooth cursor feel.

### Cross-platform input
`InputController` auto-detects the OS:
- **Linux X11/Wayland**: tries `evdev` (uinput) first, falls back to `pyautogui`
- **Windows / macOS**: uses `pyautogui`
- **No display / testing**: `NullBackend` logs actions to stdout

### Stage 5 extension points
- Add `control/profiles/` with JSON bindings per app (Blender, browser, etc.)
- Add virtual joystick axes via `vgamepad` (Windows) or `uinput` (Linux)
- Replace rule-based recognizer with a small MLP trained on your own gestures

---

## Tuning

| Parameter | Location | Effect |
|-----------|----------|--------|
| `smooth_factor` | `HandTracker.__init__` | Landmark smoothing (0=max, 1=raw) |
| `smoothing` | `InputController.__init__` | Cursor EMA (0=frozen, 1=raw) |
| `dead_zone` | `InputController.__init__` | Edge exclusion fraction |
| `cooldown` | `GestureMapper.__init__` | Min seconds between clicks |
| `PINCH_THRESHOLD` | `gesture_recognizer.py` | px distance for pinch detection |