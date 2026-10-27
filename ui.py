import cv2
import numpy as np
import config


def blank(color=config.BLACK):
    return np.full((config.H, config.W, 3), color, np.uint8)


def draw_text(img, text, pos, scale=1.0, color=config.WHITE, thickness=2, center=False):
    font = cv2.FONT_HERSHEY_SIMPLEX
    if center:
        (w, h), _ = cv2.getTextSize(text, font, scale, thickness)
        pos = (pos[0] - w // 2, pos[1] + h // 2)
    cv2.putText(img, text, pos, font, scale, color, thickness, cv2.LINE_AA)


def draw_hud(img, stage_no, name, seconds_left):
    cv2.rectangle(img, (0, 0), (config.W, 60), config.BLACK, -1)
    draw_text(img, f"STAGE {stage_no}  -  {name}", (20, 40), 0.9, config.WHITE, 2)
    s = int(seconds_left)
    color = config.RED if s < 10 else config.WHITE
    draw_text(img, f"{s // 60:02d}:{s % 60:02d}", (config.W - 120, 42), 1.1, color, 3)
