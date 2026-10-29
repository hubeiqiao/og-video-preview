#!/usr/bin/env python3
"""Check that the animation's first frame matches the approved still.

Usage: check_frame0.py APPROVED.jpg FRAMES_DIR/f0000.png
The frame is scaled to the approved image's size before comparing.
"""
import sys

from PIL import Image, ImageChops, ImageStat

ref = Image.open(sys.argv[1]).convert("RGB")
frame = Image.open(sys.argv[2]).convert("RGB").resize(ref.size, Image.LANCZOS)
diff = ImageChops.difference(ref, frame)
mean = sum(ImageStat.Stat(diff).mean) / 3
print(f"mean difference {mean:.2f} (0 = identical; under 2 is invisible)")
if mean > 2:
    diff.point(lambda v: min(255, v * 4)).save("frame0-diff.png")
    sys.exit("frame 0 does not match the approved image; see frame0-diff.png")
