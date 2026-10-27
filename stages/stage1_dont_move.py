import cv2
import math
import os
import random
import time
import pygame
import config
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from stage_base import Stage, RUNNING, WIN, LOSE
from ui import draw_text

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# نقاط الجسم المستخدمة: كتفين، مرفقين، معصمين، وركين، وأنف
KEYPOINTS = [0, 11, 12, 13, 14, 15, 16, 23, 24]
L_SHOULDER, R_SHOULDER = 11, 12

CALIBRATION_SECONDS = 1.0
GRACE_AFTER_RED = 0.5
MOVE_THRESHOLD = 0.15
FRAMES_TO_LOSE = 2
MIN_VISIBILITY = 0.5
LIGHT_CHANGES_TO_WIN = 5     # عدد تبديلات الضوء قبل الفوز

MODEL_NAME = "pose_landmarker_lite.task"
GREEN_SOUND_FILE = "green_light-2.mp3"


class DontMoveStage(Stage):
    name = "Don't Move"
    description = "Green: move.  Red: freeze."
    time_limit = 60

    def start(self):
        model_path = os.path.join(base_dir, MODEL_NAME)
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.3,
            min_pose_presence_confidence=0.3,
            min_tracking_confidence=0.3,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

        # صوت الضوء الأخضر
        self.green_sound = None
        try:
            pygame.mixer.pre_init(44100, -16, 2, 2048)
            pygame.mixer.init()
            self.green_sound = pygame.mixer.Sound(
                os.path.join(base_dir, GREEN_SOUND_FILE)
            )
        except Exception as e:
            print("Green light sound error:", e)

        now = time.time()
        self.calib_start = now
        self.state_start_time = now
        self.is_green_light = True
        self.light_duration = random.uniform(2, 5)
        self.calibration_done = False
        self.last_timestamp_ms = 0

        self.ref_pose = None
        self.over_count = 0
        self.times = 0

        self._update_sound()   # المرحلة بتبدأ بأخضر، فالصوت بيشتغل

    # ---------------- الصوت ----------------
    def _update_sound(self):
        """بتنادى عند كل تبديل للضوء: أخضر = شغّل، أحمر = وقّف."""
        if not self.green_sound:
            return
        if self.is_green_light:
            self.green_sound.play(loops=-1)
        else:
            self.green_sound.stop()

    def stop(self):
        if self.green_sound:
            self.green_sound.stop()

    # ---------------- دوال مساعدة ----------------
    def _next_timestamp(self):
        ts = int(time.time() * 1000)
        if ts <= self.last_timestamp_ms:
            ts = self.last_timestamp_ms + 1
        self.last_timestamp_ms = ts
        return ts

    def _get_points(self, landmarks, w, h):
        pts = {}
        for i in KEYPOINTS:
            lm = landmarks[i]
            if lm.visibility is not None and lm.visibility >= MIN_VISIBILITY:
                pts[i] = (lm.x * w, lm.y * h)
        return pts

    def _movement(self, ref, cur):
        if L_SHOULDER not in ref or R_SHOULDER not in ref:
            return 0.0
        scale = math.dist(ref[L_SHOULDER], ref[R_SHOULDER])
        if scale < 1:
            return 0.0
        common = [i for i in ref if i in cur]
        if len(common) < 3:
            return 0.0
        total = sum(math.dist(ref[i], cur[i]) for i in common)
        return (total / len(common)) / scale

    # ---------------- التحديث كل فريم ----------------
    def update(self, frame, dt):
        now = time.time()
        h, w = frame.shape[:2]

        # تبديل الضوء (والصوت معه)
        if now - self.state_start_time > self.light_duration:
            self.is_green_light = not self.is_green_light
            self.state_start_time = now
            self.light_duration = random.uniform(2, 5)
            self.ref_pose = None
            self.over_count = 0
            self.times += 1
            self._update_sound()

        if self.times > LIGHT_CHANGES_TO_WIN:
            self.stop()
            return WIN

        if not self.calibration_done and now - self.calib_start > CALIBRATION_SECONDS:
            self.calibration_done = True

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect_for_video(mp_image, self._next_timestamp())

        player_found = bool(result.pose_landmarks)

        if player_found:
            pts = self._get_points(result.pose_landmarks[0], w, h)
            color = config.GREEN if self.is_green_light else config.RED

            for (x, y) in pts.values():
                cv2.circle(frame, (int(x), int(y)), 5, color, -1)

            if self.calibration_done and not self.is_green_light:
                red_time = now - self.state_start_time
                if red_time > GRACE_AFTER_RED:
                    if self.ref_pose is None:
                        self.ref_pose = pts
                    else:
                        movement = self._movement(self.ref_pose, pts)
                        if movement > MOVE_THRESHOLD:
                            self.over_count += 1
                        else:
                            self.over_count = 0
                        if self.over_count >= FRAMES_TO_LOSE:
                            self.stop()
                            return LOSE
        else:
            self.over_count = 0

        if not player_found:
            draw_text(frame, "NO BODY DETECTED", (w // 2, h // 2), 1, config.RED, 2)
        else:
            light_text = "GREEN - MOVE" if self.is_green_light else "RED - FREEZE"
            draw_text(frame, light_text, (50, 100), 1,
                      config.GREEN if self.is_green_light else config.RED, 2)

        draw_text(frame, "PLACEHOLDER Stage 1", (40, h - 40), 0.9, config.GRAY, 2)

        return RUNNING

