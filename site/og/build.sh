#!/bin/sh
# The landing page's own og:video, made by the skill itself from the approved still (route A):
#   source.jpg  the approved og:image (a still photo goes into a machine and comes out as moving video cards)
#   plate.png   the same image with every object removed, from an image-edit tool (suggest_layers.py --plate)
# Each object's idle is set by where it sits: the grey still on the left barely moves, the machine a little, the video
# cards on the right the most, so the card itself says "a still in, a video out". Output: site/og/out/og.mp4 and og.jpg.
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
SKILL=../..
W=work
rm -rf "$W" && mkdir -p out
"$PY" "$SKILL/scripts/suggest_layers.py" source.jpg "$W" --plate plate.png --energy bold
"$PY" - "$W/layers.js" <<'PYEOF'
import json, sys
p = sys.argv[1]; head, body = open(p).read().split("window.OG = ", 1)
c = json.loads(body.rstrip().rstrip(";"))
for l in c["layers"]:
    cx = (l["box"][0] + l["box"][2] / 2) / c["width"]
    l["idle"] = 0.12 if cx < 0.2 else 0.35 if cx < 0.45 else 1.0 if cx < 0.75 else 1.5
open(p, "w").write(head + "window.OG = " + json.dumps(c, indent=1) + ";\n")
PYEOF
cp "$SKILL/template/from-image.html" "$W/"
"$PY" "$SKILL/scripts/render_frames.py" "$W/from-image.html" "$W/frames"
"$PY" "$SKILL/scripts/check_frame0.py" "$W/card.jpg" "$W/frames/f0000.png"
"$PY" "$SKILL/scripts/check_loop.py" "$W/frames"
bash "$SKILL/scripts/encode.sh" "$W/frames" out/og
cp "$W/layers-preview.png" out/
rm -rf "$W"
