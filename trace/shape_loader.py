"""Loads a dalgona picture and turns its engraved outline into a list of points.
Pictures live in  assest/traces/  (jpg or png). Drop a new picture there and it is used.
"""
import os
import random
import cv2
import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = ("assest", "assets")       # your folder is spelled "assest"
EXTENSIONS = (".jpg", ".jpeg", ".png")
POINTS = 300                         # how many points the outline is made of


# ---------- finding and loading the pictures ----------
def traces_folder():
    for name in FOLDERS:
        folder = os.path.join(_ROOT, name, "traces")
        if os.path.isdir(folder):
            return folder
    raise FileNotFoundError("Put the pictures in  assest/traces/")


def list_shapes():
    folder = traces_folder()
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(EXTENSIONS))
    return {os.path.splitext(f)[0]: os.path.join(folder, f) for f in files}


def choose_shape():
    shapes = list_shapes()
    name = random.choice(list(shapes.keys()))
    return name, shapes[name]


def load_shape():
    name, path = choose_shape()
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError("Cannot read " + path)
    return name, image


# ---------- extracting the outline ----------
def find_cookie(image):
    """The cookie is the orange (saturated) area. The background is grey."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = cv2.GaussianBlur(hsv[:, :, 1], (0, 0), 5)
    _, binary = cv2.threshold(sat, 60, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    biggest = max(contours, key=cv2.contourArea)
    mask = np.zeros(image.shape[:2], np.uint8)
    cv2.drawContours(mask, [biggest], -1, 255, -1)
    return mask, cv2.boundingRect(biggest)          # mask, (x, y, w, h)


def find_groove(image, cookie_mask, box):
    """The engraved line is a thin darker groove. Black-hat finds thin dark lines."""
    size = min(box[2], box[3])
    k = int(0.06 * size)
    inner = cv2.erode(cookie_mask,
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    gray = cv2.GaussianBlur(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (0, 0), 2)
    kk = max(15, int(0.025 * size) | 1)
    hat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk)))
    hat = cv2.bitwise_and(hat, hat, mask=inner)
    _, groove = cv2.threshold(hat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return groove


def outline_points(groove, box):
    """Close small gaps, then take the longest outer contour = the shape."""
    size = min(box[2], box[3])
    k = int(0.03 * size) | 1
    closed = cv2.morphologyEx(groove, cv2.MORPH_CLOSE,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None
    contour = max(contours, key=lambda c: cv2.arcLength(c, True))
    return contour.reshape(-1, 2).astype(float)


def resample(points, n):
    """n points equally spaced along the closed outline."""
    pts = np.vstack([points, points[:1]])
    seg = np.hypot(*np.diff(pts, axis=0).T)
    dist = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.linspace(0, dist[-1], n, endpoint=False)
    return np.stack([np.interp(t, dist, pts[:, 0]), np.interp(t, dist, pts[:, 1])], axis=1)


def analyze_shape(image, points=POINTS):
    cookie_mask, box = find_cookie(image)
    groove = find_groove(image, cookie_mask, box)
    raw = outline_points(groove, box)
    if raw is None or len(raw) < 20:
        raise ValueError("Could not find the outline in this picture")
    path = resample(raw, points)
    start = int(np.argmin(path[:, 1]))              # start from the top-most point
    path = np.roll(path, -start, axis=0)
    return {"path": path, "cookie_mask": cookie_mask, "box": box}


def get_shape_path(image):
    """Same name as before: returns the outline as a list of (x, y) in IMAGE pixels."""
    return analyze_shape(image)["path"].tolist()


# ---------- placing it on the game screen ----------
def fit_to_screen(image, info, screen_w, screen_h, size=520, top=60):
    """Returns (path on screen, cookie picture, cookie mask, top-left corner).
    The path and the picture use the SAME scale and offset, so they always match."""
    x, y, w, h = info["box"]
    scale = size / max(w, h)
    ox = screen_w / 2 - w * scale / 2
    oy = top + (screen_h - top) / 2 - h * scale / 2
    path = (info["path"] - [x, y]) * scale + [ox, oy]
    sprite = cv2.resize(image[y:y + h, x:x + w], None, fx=scale, fy=scale,
                        interpolation=cv2.INTER_AREA)
    mask = cv2.resize(info["cookie_mask"][y:y + h, x:x + w],
                      (sprite.shape[1], sprite.shape[0]))
    return path, sprite, mask, (int(round(ox)), int(round(oy)))
