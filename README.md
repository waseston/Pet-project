# Gesture Control Interface using Computer Vision

A computer vision project that enables interaction with a computer using hand gestures captured from a webcam.

The system detects and tracks hand landmarks in real time and serves as a foundation for gesture-based control interfaces.

## Features

- Real-time hand detection
- Hand landmark tracking
- Multi-hand support
- Visual feedback using landmarks

## Technologies

- Python 3.12.XX
- OpenCV
- MediaPipe

## Installation

Clone the repository:

```bash
git clone https://github.com/waseston/gesture-control-interface.git
cd gesture-control-interface

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

gesture-control-interface
│
├── main.py
├── tracking
│   └── hand_tracker.py
└── README.md

```