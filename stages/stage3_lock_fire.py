import os
import random
import time

import cv2
import numpy as np
import pygame
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import config
from stage_base import Stage, RUNNING, WIN, LOSE
from ui import draw_text

# مجلد المشروع (جنب main.py)، فوق مجلد stages
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset(name):
    return os.path.join(ROOT, name)


HAND_MODEL = "hand_landmarker.task"
MUSIC_FILE = "brvhrtz-action-loop-e-90-bpm-brvhrtz-233462.mp3"
SHOOT_FILE = "sovetsky_rastov72-geweher-98-sound-effect-383799.mp3"
HIT_FILE = "u_68csiaifb5-bulletimpact3-442719.mp3"

ACTIVE_TARGETS = 3
MAX_TARGETS = 8
WIN_SCORE = 6
TARGET_RADIUS = 55
COLORS = [
    (0, 0, 255),
    (0, 215, 255),
    (255, 0, 0),
    (50, 50, 50),
]


class LockFireStage(Stage):
    name = "Lock & Fire"
    description = "Point your index finger, move it down then up to shoot."
    time_limit = 30

    # ---------------- بداية المرحلة ----------------
    def start(self):
        base_options = python.BaseOptions(model_asset_path=asset(HAND_MODEL))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.hand_landmarker = vision.HandLandmarker.create_from_options(options)
        self.last_timestamp_ms = 0

        # الصوت
        self.shoot_sound = None
        self.hit_sound = None
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(asset(MUSIC_FILE))
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print("Background music error:", e)
        try:
            self.shoot_sound = pygame.mixer.Sound(asset(SHOOT_FILE))
        except Exception as e:
            print("Shoot sound error:", e)
        try:
            self.hit_sound = pygame.mixer.Sound(asset(HIT_FILE))
        except Exception as e:
            print("Hit sound error:", e)

        # حالة اللعبة
        self.score = 0
        self.spawned = 0
        self.targets = []
        self.initialized = False      # بنعمل الأهداف بأول update (لما نعرف حجم الفريم)
        self.game_start = time.time()

        self.shoot_cooldown = 0
        self.show_bang = False
        self.prev_y = 0
        self.motion_state = "IDLE"

    # لو game.py بينادي stop() لما تخلص المرحلة، بيوقف الموسيقى
    def stop(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    # ---------------- دوال مساعدة ----------------
    def _next_timestamp(self):
        ts = int(time.time() * 1000)
        if ts <= self.last_timestamp_ms:
            ts = self.last_timestamp_ms + 1
        self.last_timestamp_ms = ts
        return ts

    def _spawn_target(self, w, h):
        self.targets.append({
            "x": random.randint(int(w * 0.2), int(w * 0.8)),
            "y": random.randint(int(h * 0.2), int(h * 0.6)),
            "dx": random.choice([-4, -3, 3, 4]),
            "dy": random.choice([-4, -3, 3, 4]),
            "radius": TARGET_RADIUS,
            "active": True,
            "color": random.choice(COLORS),
        })
        self.spawned += 1

    def _move_targets(self, w, h):
        for t in self.targets:
            if not t["active"]:
                continue
            t["x"] += t["dx"]
            t["y"] += t["dy"]

            if t["x"] - t["radius"] < 50 or t["x"] + t["radius"] > w - 50:
                t["dx"] *= -1
            if t["y"] - t["radius"] < 50 or t["y"] + t["radius"] > h - 100:
                t["dy"] *= -1

            if random.random() < 0.02:
                t["dx"] = max(-5, min(5, t["dx"] + random.choice([-1, 1])))
                t["dy"] = max(-5, min(5, t["dy"] + random.choice([-1, 1])))

    def _is_pointing(self, lm):
        """السبابة مفرودة وباقي الأصابع مطويّة."""
        index_extended = lm[8][1] < lm[5][1] - 15
        others_folded = (
                lm[12][1] > lm[9][1] and
                lm[16][1] > lm[13][1] and
                lm[20][1] > lm[17][1]
        )
        return index_extended and others_folded

    def _shoot(self, tip, w, h):
        self.show_bang = True
        self.shoot_cooldown = 15
        if self.shoot_sound:
            self.shoot_sound.play()

        for t in self.targets:
            if not t["active"]:
                continue
            dist = np.hypot(tip[0] - t["x"], tip[1] - t["y"])
            if dist < t["radius"] + 30:
                t["active"] = False
                self.score += 1
                if self.hit_sound:
                    self.hit_sound.play()
                if self.spawned < MAX_TARGETS:
                    self._spawn_target(w, h)
                break

    # ---------------- التحديث كل فريم ----------------
    def update(self, frame, dt):
        h, w = frame.shape[:2]

        if not self.initialized:
            for _ in range(ACTIVE_TARGETS):
                self._spawn_target(w, h)
            self.initialized = True

        elapsed = time.time() - self.game_start
        time_left = max(0, int(self.time_limit - elapsed))

        # الفوز والخسارة
        if self.score >= WIN_SCORE:
            self.stop()
            return WIN
        if time_left == 0:
            self.stop()
            return LOSE

        self._move_targets(w, h)

        # كشف اليد
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.hand_landmarker.detect_for_video(mp_image, self._next_timestamp())

        pointing = False
        if result.hand_landmarks:
            lm = [(int(p.x * w), int(p.y * h)) for p in result.hand_landmarks[0]]

            if self._is_pointing(lm):
                pointing = True
                tip = lm[8]
                current_y = tip[1]

                if self.prev_y != 0:
                    y_diff = current_y - self.prev_y
                    if y_diff > 5 :
                        self.motion_state = "DOWN"
                    elif y_diff < -5 and self.motion_state == "DOWN" \
                            and self.shoot_cooldown == 0:
                        self.motion_state = "IDLE"
                        self._shoot(tip, w, h)
                self.prev_y = current_y

                cv2.circle(frame, tip, 18, (0, 255, 255), 2)
                cv2.circle(frame, tip, 6, (0, 0, 255), -1)

        if not pointing:
            self.prev_y = 0
            self.motion_state = "IDLE"

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.shoot_cooldown < 8:
            self.show_bang = False

        # رسم الأهداف
        for t in self.targets:
            if not t["active"]:
                continue
            tx, ty, r, col = t["x"], t["y"], t["radius"], t["color"]
            cv2.line(frame, (tx - r - 15, ty), (tx + r + 15, ty), col, 3)
            cv2.line(frame, (tx, ty - r - 15), (tx, ty + r + 15), col, 3)
            cv2.circle(frame, (tx, ty), r, col, 3)
            cv2.circle(frame, (tx, ty), int(r * 0.55), col, 2)
            cv2.circle(frame, (tx, ty), 7, col, -1)

        if self.show_bang:
            draw_text(frame, "BANG!", (w // 2 - 120, 180), 2.5, (0, 255, 255), 5)

        # الواجهة
        draw_text(frame, f"Score: {self.score}/{WIN_SCORE}", (40, 60), 1.1, config.GREEN, 3)
        draw_text(frame, f"Time: {time_left}s", (40, 120), 1.2, (0, 165, 255), 3)

        return RUNNING