#!/usr/bin/env bash
# Rebuild every example end to end. Run from anywhere; outputs land in examples/<name>/out/.
# Route A examples start from the approved image alone: nothing is hand-tuned.
set -euo pipefail
PY=${PYTHON:-python3}   # set PYTHON if your playwright lives in another interpreter
cd "$(dirname "$0")/.."

gif() { # small looping preview for the README
  ffmpeg -v error -y -i "$1" -vf "fps=15,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=sierra2_4a" -loop 0 "$2"
}

route_a() { # name, then any suggest_layers.py options
  local name=$1; shift
  local ex=examples/$name work=examples/$name/work
  rm -rf "$work"
  "$PY" scripts/suggest_layers.py "$ex"/source.* "$work" "$@"
  cp template/from-image.html "$work"/
  "$PY" scripts/render_frames.py "$work/from-image.html" "$work/frames"
  "$PY" scripts/check_frame0.py "$work/card.jpg" "$work/frames/f0000.png"
  "$PY" scripts/check_loop.py "$work/frames"
  mkdir -p "$ex/out"
  bash scripts/encode.sh "$work/frames" "$ex/out/$name"
  gif "$ex/out/$name.mp4" "$ex/out/preview.gif"
  cp "$work/layers-preview.png" "$ex/out/"
  rm -rf "$work/frames"
}

route_a og-video-preview
route_a joespeaking-home
route_a living-blobs --style living

# Route B: the demo.joespeaking.com talk card, built as HTML
ex=examples/demo-joespeaking
"$PY" scripts/render_frames.py $ex/og.html $ex/frames
"$PY" scripts/check_loop.py $ex/frames
bash scripts/encode.sh $ex/frames $ex/out/demo-v1
gif $ex/out/demo-v1.mp4 $ex/out/preview.gif
rm -rf $ex/frames
