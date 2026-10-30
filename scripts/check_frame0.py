#!/usr/bin/env python3
"""Check that the animation's first frame matches the approved still.

Usage: check_frame0.py APPROVED.jpg FRAMES_DIR/f0000.png
The frame is scaled to the approved image's size before comparing. Two tests:
the mean difference (the whole card), and local defects (a gap between letters,
a missing edge), which a low mean can hide. Both images are softened slightly
first, so resampling a 2x capture does not count as a defect.
"""
import sys

import numpy as np
from PIL import Image, ImageChops, ImageFilter

ref = Image.open(sys.argv[1]).convert("RGB")
frame = Image.open(sys.argv[2]).convert("RGB").resize(ref.size, Image.LANCZOS)
diff = ImageChops.difference(ref, frame)
soft = lambda im: np.asarray(im.filter(ImageFilter.GaussianBlur(1)), dtype=np.int16)
d = np.abs(soft(ref) - soft(frame))
mean = float(d.mean())  # softened too: film grain does not survive a 2x capture, and nobody can see it go
local = d.max(2) > 40
share = local.mean() * 100
print(f"mean difference {mean:.2f} (0 = identical; under 2 is invisible), local defects {share:.3f}% of pixels (limit 0.05%)")
if mean > 2 or share > 0.05:
    diff.point(lambda v: min(255, v * 4)).save("frame0-diff.png")
    sys.exit("frame 0 does not match the approved image; see frame0-diff.png")
