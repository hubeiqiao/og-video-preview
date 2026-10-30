#!/usr/bin/env bash
# Fetch each site's og:image, read it, and render a preview strip, all under examples/gallery/out/
# (ignored by git: those images belong to the sites). Usage: bash examples/gallery/run.sh [site-filter]
set -uo pipefail
PY=${PYTHON:-python3}
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
mkdir -p out
grep -v '^#' sites.txt | grep -i -- "${1:-}" | while read -r url; do
  [ -z "$url" ] && continue
  name=$(echo "$url" | sed -E 's#https?://(www\.)?##; s#/.*##; s#\.[a-z]+$##; s#\.#-#g')
  dir=out/$name
  img=$(curl -sL -m 15 -A "Mozilla/5.0 facebookexternalhit/1.1" "$url" | tr '\n' ' ' \
    | grep -oiE '<meta[^>]+(property|name)="(og:image|twitter:image)"[^>]*>' | head -1 \
    | grep -oiE 'content="[^"]+"' | sed 's/content="//; s/"$//; s/&amp;/\&/g')
  case "$img" in //*) img="https:$img";; /*) img="$url$img";; esac
  [ -z "$img" ] && { echo "$name: no og:image"; continue; }
  mkdir -p "$dir" && curl -sL -m 20 -o "$dir/source" "$img" || continue
  echo "== $name"
  "$PY" "$ROOT/scripts/suggest_layers.py" "$dir/source" "$dir" | grep -v '^plate' || continue
  cp "$ROOT/template/from-image.html" "$dir/"
  "$PY" "$ROOT/scripts/render_frames.py" "$dir/from-image.html" "$dir/frames" --frames 0,18,30,40,52,66,84,110,150,200 --scale 1 | grep -v 'right edges'
  "$PY" "$ROOT/scripts/check_frame0.py" "$dir/card.jpg" "$dir/frames/f0000.png" | tail -1
done
