#!/bin/sh
# Assemble the landing page into _site/ from files the repo already has: the page, its own og:video (site/og/prism/out,
# rendered by the skill from the scene in site/og/prism), the film (social/promo.mp4), the eval's 61 cards (eval/out)
# and the element boxes the skill read on each card (site/media/boxes.json).
# Light versions for the page are made here and cached in .cache/: small tile videos for the grid (480 px, 30 fps)
# and a 720p film, so a page full of moving cards stays smooth.
# The og files carry a version in their name (og-v4): bump it in index.html and here when the card changes.
set -e
cd "$(dirname "$0")/.."
OUT=_site
CACHE=.cache/site
rm -rf "$OUT" && mkdir -p "$OUT/og" "$OUT/media/tiles" "$OUT/eval" "$CACHE/tiles"
cp_() { cp -c "$@" 2>/dev/null || cp "$@"; }  # a clone on APFS: no second copy on disk
newer() { [ ! -f "$2" ] || [ "$1" -nt "$2" ]; }

cp_ site/index.html site/textures.js "$OUT/"
cp_ site/og/prism/out/og.jpg "$OUT/og/og-v4.jpg"
cp_ site/og/prism/out/og.mp4 "$OUT/og/og-v4.mp4"
cp_ site/media/boxes.json site/media/sites.json site/media/promo-poster.jpg "$OUT/media/"
cp_ eval/out/*.mp4 eval/out/*.jpg eval/results.json "$OUT/eval/"

for f in eval/out/*.mp4; do
  t="$CACHE/tiles/$(basename "$f")"
  if newer "$f" "$t"; then
    ffmpeg -v error -y -i "$f" -vf "fps=30,scale=480:-2:flags=lanczos" -c:v libx264 -crf 30 -preset slow -pix_fmt yuv420p -an -movflags +faststart "$t"
  fi
  cp_ "$t" "$OUT/media/tiles/"
done
if newer social/promo.mp4 "$CACHE/film.mp4"; then
  ffmpeg -v error -y -i social/promo.mp4 -vf "scale=1280:-2:flags=lanczos" -c:v libx264 -crf 25 -preset slow -pix_fmt yuv420p \
    -c:a aac -b:a 128k -movflags +faststart "$CACHE/film.mp4"
fi
cp_ "$CACHE/film.mp4" "$OUT/media/film.mp4"
touch "$OUT/.nojekyll"
echo "built $OUT: $(find "$OUT" -type f | wc -l | tr -d ' ') files, $(du -sh "$OUT" | cut -f1)"
