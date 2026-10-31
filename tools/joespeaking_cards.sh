#!/bin/sh
# One big preview of Joe Speaking's og:videos (one for every social card, made with this skill) for the website:
# twelve cards playing at once in a 4 x 3 grid, site/media/joespeaking-cards.mp4, and its first frame as a poster
# (joespeaking-cards.webp). Usage: sh tools/joespeaking_cards.sh DIR_WITH_<card>.mp4
set -e
SRC=$1
cd "$(dirname "$0")/.."
CARDS="home-en home-ja scoring-en ios-en teachers-ko partners-en mcp-chatgpt-en home-zh-CN celpip-speaking-practice-en ielts-speaking-questions-2026-en newsletter-joe-speaking-1-0-en ios-zh-TW"
args="" chain="" i=0
for c in $CARDS; do
  args="$args -i $SRC/$c.mp4"
  chain="$chain[$i:v]fps=30,scale=480:252:flags=lanczos,setsar=1[v$i];"
  i=$((i + 1))
done
layout="0_0|492_0|984_0|1476_0|0_264|492_264|984_264|1476_264|0_528|492_528|984_528|1476_528"
ffmpeg -v error -y $args -filter_complex "${chain}[v0][v1][v2][v3][v4][v5][v6][v7][v8][v9][v10][v11]xstack=inputs=12:layout=$layout:fill=0x0f0d0b[g]" \
  -map "[g]" -t 4 -c:v libx264 -crf 27 -preset slow -pix_fmt yuv420p -an -movflags +faststart site/media/joespeaking-cards.mp4
ffmpeg -v error -y -i site/media/joespeaking-cards.mp4 -frames:v 1 site/media/joespeaking-cards.png
cwebp -quiet -q 82 site/media/joespeaking-cards.png -o site/media/joespeaking-cards.webp && rm site/media/joespeaking-cards.png
ls -la site/media/joespeaking-cards.mp4 site/media/joespeaking-cards.webp | awk '{print $5, $9}'
