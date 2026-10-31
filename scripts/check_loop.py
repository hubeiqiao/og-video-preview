#!/usr/bin/env python3
"""Check that the loop is seamless: the jump from the last frame back to the
first should be no bigger than an ordinary frame-to-frame step (with a little slack).
Also check that the video moves at all: a loop of identical frames is seamless too.

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


def motion(frames):  # the most any sampled frame differs from frame 0, on a small grey copy (mean level difference)
    small = lambda p: Image.open(p).convert("L").resize((240, 126))
    f0 = small(frames[0])
    return max(sum(ImageChops.difference(f0, small(p)).getdata()) / (240 * 126) for p in frames[:: max(1, len(frames) // 24)])


moved = motion(frames)
print(f"motion {moved:.2f}")
if moved < 0.2:
    sys.exit("the video does not move: every frame is the card. Give the card a reading, or let the camera breathe")
