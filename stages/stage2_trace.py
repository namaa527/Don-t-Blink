import math
import random
import cv2
import numpy as np
import config
import audio
from stage_base import Stage, RUNNING, WIN, LOSE
from ui import draw_text
from debug_input import mouse            # used only if there is no hand tracker
from trace.path_tracker import PathTracker
from trace.shape_loader import load_shape, analyze_shape, fit_to_screen

try:
    from hand_tracker import get_tracker
except Exception:                         # mediapipe missing -> mouse mode
    get_tracker = None

# ---- settings (tune these) ----
SHAPE_SIZE = 520          # size of the cookie on screen (pixels)
MARK_TOL = 22             # finger closer than this to the line = that part is traced
FAIL_TOL = 45             # finger farther than this from the line = "off the line"
OFF_PATH_SECONDS = 1.0    # how long you may stay off the line before the cookie breaks
WIN_PROGRESS = 90         # % of the outline you must trace
SMOOTHING = 0.5           # 0..1  (higher = follows the finger faster, but shakier)
BREAK_SECONDS = 1.0       # how long the "cookie breaks" animation lasts
CRACKS = 8                # number of cracks

# sound files (put them in assest/sounds/ - all optional)
MUSIC = "halloween.mp3"      # loops during the stage
SND_START = "start.mp3"        # when the trace begins
SND_WARNING = "warning.mp3"    # the moment you leave the line
SND_CRACK = "crack.mp3"         # the moment the cookie breaks
SND_GAMEOVER = "gameover.mp3"  # when the break animation ends (Game Over screen follows)
SND_WIN = "win.mp3"            # you win


class TraceStage(Stage):
    name = "Trace"
    description = "Follow the line with your fingertip. Don't leave it."
    time_limit = 30

    def start(self):
        self.shape_name, image = load_shape()
        info = analyze_shape(image)
        path, self.sprite, self.sprite_mask, self.corner = fit_to_screen(
            image, info, config.W, config.H, size=SHAPE_SIZE)
        self.pts = [(int(x), int(y)) for x, y in path]
        self.tracker = PathTracker(path, MARK_TOL, FAIL_TOL)

        # the cookie as a full-screen mask (cracks are drawn only inside it)
        ox, oy = self.corner
        h, w = self.sprite.shape[:2]
        self.cookie_full_mask = np.zeros((config.H, config.W), np.uint8)
        self.cookie_full_mask[oy:oy + h, ox:ox + w] = self.sprite_mask

        self.hand = None
        if get_tracker is not None:
            try:
                self.hand = get_tracker()
            except Exception as e:
                print("Hand tracker not available, using the mouse:", e)

        self.finger = None        # smoothed fingertip
        self.armed = False        # becomes True when the finger first touches the line
        self.off_time = 0.0
        self.t = 0.0
        self.breaking = False     # True while the cookie-break animation plays
        self.break_t = 0.0
        self.cracks = []
        audio.play_music(MUSIC)

    # ---- where is the fingertip? ----
    def read_finger(self, frame):
        if self.hand is not None:
            if self.hand.update(frame):
                return self.hand.index_tip()
            return None
        return (mouse["x"], mouse["y"])

    # ---- winning ----
    def win(self):
        audio.stop_music()
        audio.play(SND_WIN)
        return WIN

    # ---- losing = the cookie breaks, THEN the game shows Game Over ----
    def start_break(self, finger=None):
        if finger is not None:                       # break where you left the line
            d = np.hypot(self.tracker.path[:, 0] - finger[0], self.tracker.path[:, 1] - finger[1])
            origin = self.pts[int(d.argmin())]
        else:                                        # time is up: break anywhere on the line
            origin = self.pts[random.randrange(len(self.pts))]
        self.cracks = []
        for _ in range(CRACKS):
            angle = random.uniform(0, 2 * math.pi)
            x, y = origin
            points = [(int(x), int(y))]
            for _ in range(10):
                angle += random.uniform(-0.5, 0.5)           # jagged
                step = random.uniform(25, 55)
                x += math.cos(angle) * step
                y += math.sin(angle) * step
                points.append((int(x), int(y)))
            self.cracks.append(points)
        self.breaking = True
        self.break_t = 0.0
        audio.stop_music()
        audio.play(SND_CRACK)

    def draw_break(self, frame):
        p = min(self.break_t / BREAK_SECONDS, 1.0)
        layer = np.zeros((config.H, config.W), np.uint8)             # cracks grow with time
        for points in self.cracks:
            k = max(2, int(len(points) * p) + 1)
            cv2.polylines(layer, [np.array(points[:k], np.int32)], False, 255, 6)
        layer = cv2.bitwise_and(layer, self.cookie_full_mask)        # only on the cookie
        frame[layer > 0] = config.BLACK

        a = 0.5 * (1 - p)                                            # red flash that fades
        flash = np.full(frame.shape, config.RED, np.uint8)
        frame[:] = cv2.addWeighted(frame, 1 - a, flash, a, 0)

        m = np.float32([[1, 0, random.randint(-8, 8)], [0, 1, random.randint(-8, 8)]])
        frame[:] = cv2.warpAffine(frame, m, (config.W, config.H))    # shake

        draw_text(frame, "YOU BROKE IT", (config.W // 2, 100), 1.6, config.RED, 4, center=True)

    # ---- drawing ----
    def draw_scene(self, frame):
        frame[:] = cv2.convertScaleAbs(frame, alpha=0.35)          # dim the camera
        ox, oy = self.corner
        h, w = self.sprite.shape[:2]
        region = frame[oy:oy + h, ox:ox + w]
        region[self.sprite_mask > 0] = self.sprite[self.sprite_mask > 0]

        n = len(self.pts)
        cv2.polylines(frame, [np.array(self.pts, np.int32)], True, config.GRAY, 3)
        v = self.tracker.visited
        for i in range(n):                                          # traced part in red
            j = (i + 1) % n
            if v[i] and v[j]:
                cv2.line(frame, self.pts[i], self.pts[j], config.RED, 7)
        cv2.circle(frame, self.pts[0], 13, config.GREEN, -1)
        draw_text(frame, "START", (self.pts[0][0] + 18, self.pts[0][1] - 8), 0.7, config.GREEN, 2)

    def update(self, frame, dt):
        # the break animation plays, then we return LOSE (the game shows Game Over)
        if self.breaking:
            self.break_t += dt
            self.draw_scene(frame)
            self.draw_break(frame)
            if self.break_t >= BREAK_SECONDS:
                audio.play(SND_GAMEOVER)
                return LOSE
            return RUNNING

        self.t += dt
        if self.t >= self.time_limit - BREAK_SECONDS - 0.5:   # time is up
            self.start_break()
            return RUNNING

        raw = self.read_finger(frame)
        if raw is not None:
            if self.finger is None:
                self.finger = raw
            else:
                a = SMOOTHING
                self.finger = (int(a * raw[0] + (1 - a) * self.finger[0]),
                               int(a * raw[1] + (1 - a) * self.finger[1]))
        else:
            self.finger = None

        self.draw_scene(frame)

        if self.finger is None:
            draw_text(frame, "NO HAND", (config.W // 2, 100), 1.2, config.GRAY, 3, center=True)
        else:
            self.tracker.update(self.finger)
            if not self.armed and self.tracker.touching():
                self.armed = True                                   # the trace begins
                audio.play(SND_START)

            if self.armed:
                if self.tracker.on_path:
                    self.off_time = 0.0
                else:
                    if self.off_time == 0.0:                        # just left the line
                        audio.play(SND_WARNING)
                    self.off_time += dt
            color = config.WHITE if self.tracker.on_path or not self.armed else config.RED
            cv2.circle(frame, self.finger, 12, color, -1)
            cv2.circle(frame, self.finger, 16, config.RED, 2)

        progress = self.tracker.get_progress()
        draw_text(frame, f"TRACED {int(progress)}%  (need {WIN_PROGRESS}%)", (40, 105), 0.9, config.WHITE, 2)
        if not self.armed:
            draw_text(frame, "Touch the line to begin", (config.W // 2, config.H - 40),
                      0.9, config.GRAY, 2, center=True)
        else:                                                       # warning bar: off the line
            bar = int(config.W * min(self.off_time / OFF_PATH_SECONDS, 1.0))
            cv2.rectangle(frame, (0, 62), (bar, 70), config.RED, -1)

        if self.off_time >= OFF_PATH_SECONDS:
            self.start_break(self.finger)
            return RUNNING
        if progress >= WIN_PROGRESS:
            return self.win()
        return RUNNING                