#!/bin/sh
# The landing page's own og:video, made with the skill's route B (an HTML card, card.html): a still og:image on the
# left, an arrow, and on the right the og:video the skill made from that same image (joespeaking.com's card), playing.
# The right card plays the real video frame by frame, so the loop closes where the video's own loop does.
# Output: site/og/out/og.mp4 and og.jpg (frame 0, the still).
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
SKILL=../..
W=work
rm -rf "$W" && mkdir -p "$W/frames" out && rm -f out/layers-preview.png
cp ../media/joespeaking.jpg "$W/still.jpg"
# the video's 4 s loop at 30 fps: card frame t shows video frame t
ffmpeg -v error -y -i ../media/joespeaking-og.mp4 -vf "fps=30,scale=940:494:flags=lanczos" -q:v 2 -start_number 0 "$W/frames/f%04d.jpg"
echo "window.FRAMES = $(ls "$W/frames" | wc -l | tr -d ' ');" > "$W/frames.js"
# 30 fps, one card frame per video frame (at 60 the loop check would measure a normal step between two copies)
"$PY" "$SKILL/scripts/render_frames.py" card.html "$W/out" --root .. --fps 30 --seconds 4
"$PY" "$SKILL/scripts/check_loop.py" "$W/out"
bash "$SKILL/scripts/encode.sh" "$W/out" out/og 30
rm -rf "$W"
