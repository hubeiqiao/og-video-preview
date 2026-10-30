#!/bin/sh
# Assemble the landing page into _site/ from files the repo already has: the page, its own og:video (site/og/out,
# made by the skill itself from the approved still: site/og/build.sh), the film (social/promo.mp4), the eval's cards (eval/out)
# and the element boxes the skill read on each card (site/media/boxes.json).
# Light versions for the page are made here and cached in .cache/: small tile videos for the grid (480 px, 30 fps)
# and a 720p film, so a page full of moving cards stays smooth.
# The og files carry a version in their name (og-v5): bump it in index.html and here when the card changes.
set -e
cd "$(dirname "$0")/.."
OUT=_site
CACHE=.cache/site
rm -rf "$OUT" && mkdir -p "$OUT/og" "$OUT/media/tiles" "$OUT/eval" "$OUT/fonts" "$OUT/media/posters" "$CACHE/tiles" "$CACHE/posters"
cp_() { cp -c "$@" 2>/dev/null || cp "$@"; }  # a clone on APFS: no second copy on disk
newer() { [ ! -s "$2" ] || [ "$1" -nt "$2" ]; }
# Minimal Homebrew ffmpeg omits libwebp; use cwebp when installed. Ubuntu's ffmpeg includes libwebp.
webp() {
  src=$1 dest=$2 quality=$3 width=$4
  if command -v cwebp >/dev/null 2>&1; then
    cwebp -quiet -q "$quality" -resize "$width" 0 "$src" -o "$dest"
  elif [ "$width" -gt 0 ]; then
    ffmpeg -v error -y -i "$src" -vf "scale=$width:-2:flags=lanczos" -c:v libwebp -quality "$quality" "$dest"
  else
    ffmpeg -v error -y -i "$src" -c:v libwebp -quality "$quality" "$dest"
  fi
}

cp_ site/index.html site/textures.js "$OUT/"
cp_ site/og/out/og.jpg "$OUT/og/og-v5.jpg"
cp_ site/og/out/og.mp4 "$OUT/og/og-v5.mp4"
cp_ site/media/boxes.json site/media/sites.json site/media/promo-poster.jpg site/media/joe.webp "$OUT/media/"
cp_ site/fonts/* "$OUT/fonts/"
cp_ eval/out/*.mp4 eval/out/*.jpg eval/results.json "$OUT/eval/"

# Small stills stay images until hover, so 103 tiles need neither full JPEGs nor video decoders.
for f in eval/out/*.jpg; do
  t="$CACHE/posters/$(basename "$f" .jpg).webp"
  if newer "$f" "$t"; then
    webp "$f" "$t" 88 480
  fi
  cp_ "$t" "$OUT/media/posters/"
done
# Same approved live-site stills, stored locally so the first screen has no cross-origin image dependency.
for name in joespeaking hubeiqiao promo-poster; do
  f="site/media/$name.jpg"
  t="$CACHE/$name-v2.webp"
  if newer "$f" "$t"; then
    if [ "$name" = promo-poster ]; then webp "$f" "$t" 85 1280
    else webp "$f" "$t" 92 0; fi
  fi
  cp_ "$t" "$OUT/media/$name.webp"
done

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
python3 site/build_page.py
touch "$OUT/.nojekyll"
echo "built $OUT: $(find "$OUT" -type f | wc -l | tr -d ' ') files, $(du -sh "$OUT" | cut -f1)"
