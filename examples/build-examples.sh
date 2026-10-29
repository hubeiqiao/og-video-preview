#!/usr/bin/env bash
# Rebuild both examples end to end. Run from the repo root.
set -euo pipefail
PY=${PYTHON:-python3}   # set PYTHON if your playwright lives in another interpreter
cd "$(dirname "$0")/.."

gif() { # small looping preview for the README
  ffmpeg -v error -y -i "$1" -vf "fps=20,scale=600:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=sierra2_4a" -loop 0 "$2"
}

# Route A: JoeSpeaking.com's approved homepage card, animated from the image alone
ex=examples/joespeaking-home
"$PY" scripts/render_frames.py $ex/from-image.html $ex/frames
"$PY" scripts/check_frame0.py $ex/card.jpg $ex/frames/f0000.png
"$PY" scripts/check_loop.py $ex/frames
bash scripts/encode.sh $ex/frames $ex/out/home-v1
gif $ex/out/home-v1.mp4 $ex/out/preview.gif

# Route B: the demo.joespeaking.com talk card, built as HTML
ex=examples/demo-joespeaking
"$PY" scripts/render_frames.py $ex/og.html $ex/frames
"$PY" scripts/check_loop.py $ex/frames
bash scripts/encode.sh $ex/frames $ex/out/demo-v1
gif $ex/out/demo-v1.mp4 $ex/out/preview.gif
