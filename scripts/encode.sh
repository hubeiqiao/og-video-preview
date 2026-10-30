#!/usr/bin/env bash
# Encode captured frames into the OG video and its matching still.
# Usage: encode.sh FRAMES_DIR OUT_BASENAME [FPS]
#   writes OUT_BASENAME.mp4 (H.264, yuv420p, silent, faststart, 1200x630)
#   and OUT_BASENAME.jpg (frame 0, 4:4:4 chroma)
# Version by filename (page-v3), never by query string.
set -euo pipefail
FRAMES=$1; OUT=$2; FPS=${3:-60}
mkdir -p "$(dirname "$OUT")"

# busy, grainy cards compress worse: raise CRF step by step until the MP4 fits 2 MB
size() { stat -f%z "$1" 2>/dev/null || stat -c%s "$1"; }
for CRF in 19 22 25 28; do
  ffmpeg -v error -y -framerate "$FPS" -i "$FRAMES/f%04d.png" \
    -vf "scale=1200:630:flags=lanczos,format=yuv420p" \
    -c:v libx264 -preset slow -crf "$CRF" -movflags +faststart -an "$OUT.mp4"
  [ "$(size "$OUT.mp4")" -le 2097152 ] && break
done
for Q in 3 5 7 9; do
  ffmpeg -v error -y -i "$FRAMES/f0000.png" -vf "scale=1200:630:flags=lanczos,format=yuvj444p" \
    -q:v "$Q" -frames:v 1 "$OUT.jpg"
  [ "$(size "$OUT.jpg")" -le 184320 ] && break
done
mp4=$(size "$OUT.mp4"); jpg=$(size "$OUT.jpg")
echo "$OUT.mp4  $((mp4 / 1024)) KB  (limit 2048 KB, CRF $CRF)"
echo "$OUT.jpg  $((jpg / 1024)) KB  (limit 180 KB, q $Q)"
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,pix_fmt,r_frame_rate -of compact "$OUT.mp4"
[ "$mp4" -le 2097152 ] || { echo "MP4 over 2 MB even at CRF 28: shorten the loop or calm the background" >&2; exit 1; }
[ "$jpg" -le 184320 ] || { echo "JPEG over 180 KB: lower quality" >&2; exit 1; }
