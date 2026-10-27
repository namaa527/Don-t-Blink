"""Hand tracking shared by stage 2 (trace) and stage 3 (lock & fire).
Needs the model file  hand_landmarker.task  in the project folder (next to main.py).

Usage:
    tracker = get_tracker()
    if tracker.update(frame):            # frame = camera image (BGR)
        x, y = tracker.index_tip()       # pixels
        closed = tracker.thumb_closed()  # True while the thumb is folded in
"""
import math
import os
import cv2
import mediapipe as mp

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

# MediaPipe landmark numbers
WRIST, THUMB_TIP, INDEX_BASE, INDEX_TIP, MIDDLE_BASE = 0, 4, 5, 8, 9


class HandTracker:
    def __init__(self, model_path=MODEL_PATH):
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_hands=1,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.lm = None
        self.w = self.h = 1
        self.ratio = 1.0          # last thumb ratio (shown on screen for tuning)
        self._closed = False

    def update(self, frame):
        """Call once per frame. Returns True if a hand was found."""
        self.h, self.w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     # MediaPipe wants RGB
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.landmarker.detect(image)
        self.lm = result.hand_landmarks[0] if result.hand_landmarks else None
        if self.lm is None:
            self._closed = False
        return self.lm is not None

    def point(self, i):
        """Any of the 21 hand points, in pixels."""
        p = self.lm[i]
        return int(p.x * self.w), int(p.y * self.h)

    def index_tip(self):
        if self.lm is None:
            return None
        return self.point(INDEX_TIP)

    def thumb_tip(self):
        if self.lm is None:
            return None
        return self.point(THUMB_TIP)

    def thumb_closed(self, target=INDEX_BASE, close_t=0.30, open_t=0.40):
        """Thumb tip close to the 'target' point = closed (fire).
        target = INDEX_BASE (gun style) or INDEX_TIP (pinch style).
        The distance is divided by the hand size, so it works at any distance.
        Two thresholds (close_t < open_t) stop the flicker near the border."""
        if self.lm is None:
            return False
        size = math.dist(self.point(WRIST), self.point(MIDDLE_BASE)) or 1
        self.ratio = math.dist(self.point(THUMB_TIP), self.point(target)) / size
        if self.ratio < close_t:
            self._closed = True
        elif self.ratio > open_t:
            self._closed = False
        return self._closed


_tracker = None


def get_tracker():
    """One shared tracker for the whole game (loading the model takes time)."""
    global _tracker
    if _tracker is None:
        _tracker = HandTracker()
    return _tracker
