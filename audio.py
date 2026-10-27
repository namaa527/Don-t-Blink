"""Tiny shared sound helper (any stage can use it).
Put the sound files in  assest/sounds/  (mp3 or wav).
A missing file or a missing pygame never crashes the game: it just stays silent.

    import audio
    audio.play("fail.mp3")                  # short sound effect
    audio.play_music("trace_music.mp3")     # looping music
    audio.stop_music()
"""
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
FOLDERS = ("assest/traces", "assets")        # your folder is spelled "assest"

_ready = None
_cache = {}


def _find(name):
    for folder in FOLDERS:
        path = os.path.join(_ROOT, folder, "sounds", name)
        if os.path.exists(path):
            return path
    return None


def _init():
    global _ready
    if _ready is None:
        try:
            import pygame
            pygame.mixer.init()
            _ready = True
        except Exception as e:
            print("No sound:", e)
            _ready = False
    return _ready


def play(name, volume=1.0):
    if not _init():
        return
    import pygame
    try:
        if name not in _cache:
            path = _find(name)
            _cache[name] = pygame.mixer.Sound(path) if path else None
        sound = _cache[name]
        if sound:
            sound.set_volume(volume)
            sound.play()
    except Exception as e:
        print("Sound error:", e)


def play_music(name, volume=0.4):
    if not _init():
        print("Audio is not ready")
        return
    import pygame
    try:
        path = _find(name)
        print ("Trying to play music from ",path)
        if path:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)  
        else :
            print("Music file not found")
                       # -1 = loop
    except Exception as e:
        print("Music error:", e)


def stop_music():
    if _ready:
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass