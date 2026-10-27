Stage 2 (Trace) - what changed
1) trace/shape_loader.py   : finds the engraved outline (not the cookie shadow), relative paths, any picture in assest/traces/
2) trace/path_tracker.py   : coverage based progress + "off the line" detection (no test code on import)
3) stages/stage2_trace.py  : the full stage
4) hand_tracker.py         : merged version (has thumb_closed for stage 3, index_tip returns None without a hand)
Copy these files over the same ones in your project, then:  python run_stage2.py
