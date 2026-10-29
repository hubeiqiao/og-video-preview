#!/usr/bin/env python3
"""Suggest animation layers for an approved OG image.

Finds the background colour (the most common edge colour), marks every pixel
that differs from it, groups nearby marked pixels into boxes, and writes a
starter layers.js for template/from-image.html. Review the boxes, merge or split
them, and give each one a role before rendering.

Works best on flat or softly graded backgrounds. For busy photographic
backgrounds, draw the boxes by hand and use plate "blur" or a clean plate image.

Usage: suggest_layers.py CARD.jpg OUT_DIR [--gap 14] [--min 900] [--tol 38]
Writes OUT_DIR/layers.js and OUT_DIR/layers-preview.png (boxes drawn on the card).
"""
import argparse
import json
import os
from collections import Counter, deque

from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("card")
ap.add_argument("out")
ap.add_argument("--gap", type=int, default=14, help="pixels between parts that still belong to one layer")
ap.add_argument("--min", type=int, default=900, help="smallest box area to keep, in pixels")
ap.add_argument("--tol", type=int, default=38, help="colour distance from the background that counts as content")
a = ap.parse_args()

im = Image.open(a.card).convert("RGB")
W, H = im.size
px = im.load()
edge = [px[x, 0] for x in range(W)] + [px[x, H - 1] for x in range(W)] + [px[0, y] for y in range(H)] + [px[W - 1, y] for y in range(H)]
bg = Counter((r // 8 * 8, g // 8 * 8, b // 8 * 8) for r, g, b in edge).most_common(1)[0][0]

# work on a coarse grid: one cell per `step` pixels, marked if any pixel differs from the background
step = max(2, a.gap // 2)
gw, gh = (W + step - 1) // step, (H + step - 1) // step
grid = [[False] * gw for _ in range(gh)]
for y in range(0, H, 2):
    for x in range(0, W, 2):
        r, g, b = px[x, y]
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > a.tol:
            grid[y // step][x // step] = True

seen = [[False] * gw for _ in range(gh)]
boxes = []
for gy in range(gh):
    for gx in range(gw):
        if not grid[gy][gx] or seen[gy][gx]:
            continue
        q = deque([(gx, gy)]); seen[gy][gx] = True
        x0 = x1 = gx; y0 = y1 = gy
        while q:
            cx, cy = q.popleft()
            x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < gw and 0 <= ny < gh and grid[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True; q.append((nx, ny))
        bx, by = max(0, x0 * step - 4), max(0, y0 * step - 4)
        bw, bh = min(W, (x1 + 1) * step + 4) - bx, min(H, (y1 + 1) * step + 4) - by
        if bw * bh >= a.min and bw * bh < W * H * 0.9:
            boxes.append([bx, by, bw, bh])

# words of one text line come out as separate boxes; join boxes that share a line
def same_line(p, q):
    ov = min(p[1] + p[3], q[1] + q[3]) - max(p[1], q[1])
    gap = max(p[0], q[0]) - min(p[0] + p[2], q[0] + q[2])
    return ov > 0.5 * min(p[3], q[3]) and gap < 3 * a.gap and max(p[3], q[3]) < 2.2 * min(p[3], q[3])


merged = True
while merged:
    merged = False
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if same_line(boxes[i], boxes[j]):
                p, q = boxes[i], boxes[j]
                x0, y0 = min(p[0], q[0]), min(p[1], q[1])
                x1, y1 = max(p[0] + p[2], q[0] + q[2]), max(p[1] + p[3], q[1] + q[3])
                boxes[i] = [x0, y0, x1 - x0, y1 - y0]
                del boxes[j]
                merged = True
                break
        if merged:
            break

boxes.sort(key=lambda b: (b[1] // 40, b[0]))
layers = [{"id": f"layer{i + 1}", "box": b, "role": "rise"} for i, b in enumerate(boxes)]
os.makedirs(a.out, exist_ok=True)
config = {"image": os.path.basename(a.card), "width": W, "height": H, "loop": 4.0,
          "plate": {"mode": "fill"}, "layers": layers}
with open(os.path.join(a.out, "layers.js"), "w") as f:
    f.write("// Roles: rise | pop | spin | stamp | wipe | slide | fade. Order = entrance order.\n")
    f.write("window.OG = " + json.dumps(config, indent=2) + ";\n")

prev = im.copy(); d = ImageDraw.Draw(prev)
for i, (x, y, w, h) in enumerate(boxes):
    d.rectangle([x, y, x + w, y + h], outline=(255, 0, 80), width=3)
    d.text((x + 6, y + 4), f"layer{i + 1}", fill=(255, 0, 80))
prev.save(os.path.join(a.out, "layers-preview.png"))
print(f"background {bg}, {len(boxes)} layers -> {a.out}/layers.js")
for l in layers:
    print(" ", l["id"], l["box"])
