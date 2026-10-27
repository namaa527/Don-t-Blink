import time
import cv2
import config
from ui import blank, draw_text, draw_hud
from stage_base import RUNNING, WIN, LOSE
from stages.stage1_dont_move import DontMoveStage
from stages.stage2_trace import TraceStage
from stages.stage3_lock_fire import LockFireStage

STAGE_CLASSES = [DontMoveStage, TraceStage, LockFireStage]
INTRO_SECONDS = 3


class Game:
    def __init__(self):
        self.state = "MENU"          # MENU, INTRO, PLAYING, GAME_OVER, WIN
        self.stage_idx = 0
        self.stage = None
        self.state_start = time.time()

    def set_state(self, state):
        self.state = state
        self.state_start = time.time()

    def start_intro(self, idx):
        self.stage_idx = idx
        self.stage = STAGE_CLASSES[idx]()
        self.set_state("INTRO")

    def run(self):
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.H)
        if not cap.isOpened():
            print("Cannot open the camera. Check config.CAMERA_INDEX.")
            return
        cv2.namedWindow(config.WINDOW, cv2.WINDOW_NORMAL)
        if config.FULLSCREEN:
            cv2.setWindowProperty(config.WINDOW, cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN)
        last = time.time()
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
            cv2.imshow(config.WINDOW, self.tick(frame, dt, key))
            if cv2.getWindowProperty(config.WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
        cap.release()
        cv2.destroyAllWindows()

    def tick(self, frame, dt, key):
        cx, cy = config.W // 2, config.H // 2
        elapsed = time.time() - self.state_start

        if self.state == "MENU":
            out = blank()
            draw_text(out, "DON'T BLINK", (cx, cy - 60), 3, config.RED, 6, center=True)
            draw_text(out, "THE SYSTEM IS WATCHING", (cx, cy + 10), 0.9, config.GRAY, 2, center=True)
            draw_text(out, "Press SPACE to start", (cx, cy + 110), 1, config.WHITE, 2, center=True)
            if key == 32:
                self.start_intro(0)
            return out

        if self.state == "INTRO":
            out = blank()
            draw_text(out, f"STAGE {self.stage_idx + 1}", (cx, cy - 70), 2, config.RED, 4, center=True)
            draw_text(out, self.stage.name, (cx, cy), 1.6, config.WHITE, 3, center=True)
            draw_text(out, self.stage.description, (cx, cy + 70), 0.9, config.GRAY, 2, center=True)
            if elapsed >= INTRO_SECONDS:
                self.stage.start()
                self.set_state("PLAYING")
            return out

        if self.state == "PLAYING":
            result = self.stage.update(frame, dt)
            if config.DEBUG:
                if key == ord('w'):
                    result = WIN
                elif key == ord('l'):
                    result = LOSE
            left = self.stage.time_limit - elapsed
            if result == RUNNING and left <= 0:
                result = LOSE
            draw_hud(frame, self.stage_idx + 1, self.stage.name, max(left, 0))
            if result == WIN:
                if self.stage_idx + 1 < len(STAGE_CLASSES):
                    self.start_intro(self.stage_idx + 1)
                else:
                    self.set_state("WIN")
            elif result == LOSE:
                self.set_state("GAME_OVER")
            return frame

        if self.state == "GAME_OVER":
            out = blank()
            draw_text(out, "GAME OVER", (cx, cy - 20), 3, config.RED, 6, center=True)
            draw_text(out, "R: retry stage     M: menu", (cx, cy + 80), 1, config.WHITE, 2, center=True)
            if key == ord('r'):
                self.start_intro(self.stage_idx)
            elif key == ord('m'):
                self.set_state("MENU")
            return out

        out = blank()  # WIN
        draw_text(out, "YOU SURVIVED", (cx, cy - 20), 3, config.GREEN, 6, center=True)
        draw_text(out, "M: menu", (cx, cy + 80), 1, config.WHITE, 2, center=True)
        if key == ord('m'):
            self.set_state("MENU")
        return out
