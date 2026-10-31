#!/bin/sh
# Joe Speaking's og:videos (one for every social card, made with this skill) as light tiles for the website's gallery:
# site/media/js-cards/<card>.mp4 (480 px, 30 fps) and <card>.webp, plus site/media/js-cards.json with the card names.
# Usage: sh tools/joespeaking_cards.sh DIR_WITH_<card>.mp4_AND_<card>.jpg
set -e
SRC=$1
cd "$(dirname "$0")/.."
OUT=site/media/js-cards
mkdir -p "$OUT"
names=""
for f in "$SRC"/*.mp4; do
  n=$(basename "$f" .mp4)
  ffmpeg -v error -y -i "$f" -vf "fps=30,scale=480:-2:flags=lanczos" -c:v libx264 -crf 30 -preset slow -pix_fmt yuv420p -an -movflags +faststart "$OUT/$n.mp4"
  cwebp -quiet -q 85 -resize 480 0 "$SRC/$n.jpg" -o "$OUT/$n.webp"
  names="$names\"$n\","
done
echo "[${names%,}]" > site/media/js-cards.json
echo "$(ls "$OUT"/*.mp4 | wc -l | tr -d ' ') cards, $(du -sh "$OUT" | cut -f1)"
