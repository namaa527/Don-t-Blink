# DON'T BLINK

Install:  pip install -r requirements.txt   (run everything from this folder)

## Work on YOUR stage alone (no menu, no other stages)
    python run_stage1.py     # Don't Move   -> edit stages/stage1_dont_move.py
    python run_stage2.py     # Trace        -> edit stages/stage2_trace.py
    python run_stage3.py     # Lock & Fire  -> edit stages/stage3_lock_fire.py
Keys: Q/Esc quit | R restart | W win (debug) | L lose (debug)
No hand tracker yet? Use the mouse:  from debug_input import mouse
(mouse["x"], mouse["y"], mouse["down"])

## Full game (later, when stages are merged)
    python main.py
Keys: SPACE start | R retry | M menu | Q/Esc quit

Only edit your own stage file. Tune shared numbers in config.py (ask first).
