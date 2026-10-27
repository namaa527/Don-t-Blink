"""Mouse state for testing a stage without a hand tracker.

In your stage:
    from debug_input import mouse
    mouse["x"], mouse["y"]   -> mouse position (use it like the fingertip)
    mouse["down"]            -> True while the left button is held (use it like pinch / fire)
Only filled when you run the stage alone with run_stageN.py
"""
import cv2

mouse = {"x": 0, "y": 0, "down": False}


def on_mouse(event, x, y, flags, param):
    mouse["x"], mouse["y"] = x, y
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse["down"] = True
    elif event == cv2.EVENT_LBUTTONUP:
        mouse["down"] = False
