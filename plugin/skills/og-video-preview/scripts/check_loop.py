#!/usr/bin/env python3
"""Check that the loop is seamless: the jump from the last frame back to the
first should be no bigger than an ordinary frame-to-frame step (with a little slack).

Usage: check_loop.py FRAMES_DIR
"""
import glob
import os
import sys

from PIL import Image, ImageChops

frames = sorted(glob.glob(os.path.join(sys.argv[1], "f*.png")))
if len(frames) < 3:
    sys.exit("need the full frame set")


def diff(a, b):
    d = ImageChops.difference(Image.open(a).convert("RGB"), Image.open(b).convert("RGB"))
    return max(hi for _, hi in d.getextrema())


seam = diff(frames[-1], frames[0])
# reference steps never involve the last frame, so a bad last frame cannot raise its own bar
step = max(diff(frames[0], frames[1]), diff(frames[-3], frames[-2]))
print(f"seam {seam}  normal step {step}")
if seam > step * 1.5 + 4:
    sys.exit("visible jump at the loop point: make ambient motion periodic in the loop length and let frame 0 be the settled card")
print("loop is seamless")
