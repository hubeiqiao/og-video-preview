# OG Video Preview

An agent skill that turns an approved Open Graph image into a looping og:video, so link previews move where apps can play video (iMessage, Discord) and every other app shows the matching still. Frame 0 of the video is pixel-identical to the image.

## Install

```bash
/plugin install og-video-preview --marketplace hubeiqiao/og-video-preview
```

Or, for any agent that supports Agent Skills: `npx skills add hubeiqiao/og-video-preview`.

Then ask your agent: "Use /og-video-preview to make my og:image move."

Website: https://hubeiqiao.com/og-video-preview/
Source, examples and the 103-card eval: https://github.com/hubeiqiao/og-video-preview

## What it runs

Everything runs on your machine, on files you give it. The skill contains readable source only: Python and shell scripts, two HTML templates and one Cloudflare Worker example.

- `scripts/suggest_layers.py` and `scripts/make_plate.py` read your image with OpenCV, NumPy and Pillow, and optionally Tesseract (through `pytesseract`) to read type. `suggest_layers.py` runs `make_plate.py` itself.
- `scripts/render_frames.py` serves your working folder on 127.0.0.1 and captures frames with Playwright in your installed Google Chrome.
- `scripts/encode.sh` runs `ffmpeg` and `ffprobe` on those frames.
- `scripts/check_frame0.py` and `scripts/check_loop.py` compare frames locally.
- `scripts/check_live.sh` is the only script that goes online: it uses `curl` to fetch the page URL you pass it and the og:image and og:video files that page names, to check status, type, size and the Range (206) answer. It writes nothing.
- `template/og.html` (the HTML card route) loads two fonts from Google Fonts when it renders.
- `worker/range-worker.js` is an example Cloudflare Worker you can deploy yourself to answer Range requests for `.mp4` files. The skill never deploys anything.

What it writes: `suggest_layers.py` and `make_plate.py` write the plate, cutouts, masks, `layers.js` and a preview into the output folder you name; `render_frames.py` writes PNG frames into the folder you name; `encode.sh` writes `<name>.mp4` and `<name>.jpg`, replacing files of that name; `check_frame0.py` writes `frame0-diff.png` in the current folder when frame 0 does not match. Nothing installs packages, changes settings or sends data anywhere else.

## Requirements

Python 3 with `playwright`, `Pillow`, `opencv-python` and `numpy`; Google Chrome; `ffmpeg` and `ffprobe`. Tesseract is optional.

## License

MIT. See `LICENSE`.
