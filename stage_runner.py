"""Run ONE stage alone (camera + the stage + a simple result text).
Nothing else from the game is used, so each person can test their own stage.
Keys: Q / Esc quit | R restart | W win (debug) | L lose (debug)
"""
import time
import cv2
import config
from stage_base import RUNNING, WIN, LOSE
from ui import draw_text, draw_hud
from debug_input import on_mouse


def run_stage(stage_class):
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.H)
    if not cap.isOpened():
        print("Cannot open the camera. Check config.CAMERA_INDEX.")
        return

    stage = stage_class()
    window = "TEST - " + stage.name
    cv2.namedWindow(window, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(window, on_mouse)

    stage.start()
    result = RUNNING
    start_time = last = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.resize(cv2.flip(frame, 1), (config.W, config.H))
        now = time.time()
        dt, last = now - last, now
        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), 27):
            break
        if key == ord('r'):
            stage = stage_class()
            stage.start()
            result = RUNNING
            start_time = now

        left = max(stage.time_limit - (now - start_time), 0)
        if result == RUNNING:
            result = stage.update(frame, dt)
            if config.DEBUG and key == ord('w'):
                result = WIN
            elif config.DEBUG and key == ord('l'):
                result = LOSE
            if result == RUNNING and left <= 0:
                result = LOSE
        draw_hud(frame, "TEST", stage.name, left)

        if result != RUNNING:
            color = config.GREEN if result == WIN else config.RED
            text = "YOU WIN" if result == WIN else "YOU LOSE"
            draw_text(frame, text, (config.W // 2, config.H // 2), 3, color, 6, center=True)
            draw_text(frame, "R: restart     Q: quit", (config.W // 2, config.H // 2 + 80),
                      1, config.WHITE, 2, center=True)

        cv2.imshow(window, frame)
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
