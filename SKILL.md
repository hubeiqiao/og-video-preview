---
name: og-video-preview
description: Turn any approved Open Graph image into a looping og:video so link previews move, and make it actually play in iMessage, Safari, Slack and social cards. Works from the finished image alone (cuts it into layers, frame 0 stays pixel-identical) or from an HTML card. Covers what to animate, motion presets, Playwright frame capture, ffmpeg encoding, seamless-loop and frame-0 checks, the meta tags, and the server requirements (HTTP Range / 206, clean .mp4 URLs, versioned filenames). Use when someone asks for an OG video, animated link preview, animated share card or og:video, wants an existing og:image to move, or has an og:video that only shows a still.
---

# OG video preview

An OG video is a short, silent, looping MP4 that link previews can play in place of the share image. The workflow is always the same:

1. **Approve the still first.** The person signs off on the 1200×630 `og:image`. Nothing moves until the picture is right.
2. **Turn that exact image into motion.** Frame 0 of the video is the approved image, pixel for pixel, so the still and the video can never disagree.
3. **Publish both**, with tags and a server setup that let clients actually play the video.

Two routes for step 2:

| Route | Use when | Start from |
|---|---|---|
| **A. From the approved image** (default) | You have the final PNG/JPG, made anywhere (Figma, Canva, a generator, a screenshot) | `template/from-image.html` + `scripts/suggest_layers.py` |
| **B. From an HTML card** | You are designing the card in code, or want word-by-word text motion | `template/og.html` |

Requirements: Python 3 with `playwright` and `Pillow`, Chrome installed (Playwright uses `channel="chrome"`), `ffmpeg` and `ffprobe`.

## Route A: from the approved image

```bash
SKILL=~/.claude/skills/og-video-preview
mkdir -p og && cp approved.jpg og/card.jpg && cp $SKILL/template/from-image.html og/
python3 $SKILL/scripts/suggest_layers.py og/card.jpg og        # writes og/layers.js + og/layers-preview.png
# edit og/layers.js: one layer per thing that should move, each with a role (see below)
python3 $SKILL/scripts/render_frames.py og/from-image.html og/frames --frames 0,30,50,70,100   # preview
python3 $SKILL/scripts/check_frame0.py og/card.jpg og/frames/f0000.png
python3 $SKILL/scripts/render_frames.py og/from-image.html og/frames                 # all frames
python3 $SKILL/scripts/check_loop.py og/frames
bash    $SKILL/scripts/encode.sh og/frames public/og/home-v1 # home-v1.mp4 + home-v1.jpg
```

How it works: every layer is a rectangle cut from the approved image itself and placed back exactly where it was, so at rest the page *is* the image. Underneath sits a **plate**, the same image with those rectangles removed, so layers can leave and come back.

**Choosing layers.** `suggest_layers.py` finds everything that differs from the background colour and joins words on one line. Its output is a starting point: look at `layers-preview.png`, then
- split the headline into one layer per line (each line rises on its own),
- separate a visual from the arrow or line that touches it,
- keep boxes from overlapping, and leave a few pixels of background around each one,
- order layers in the order they should enter.

**Roles** (`role` in `layers.js`):

| Role | Motion | Good for |
|---|---|---|
| `rise` | springs up out of its own box | headline lines, subtitles |
| `pop` | scales up from 30% with a spring | badges, pills, labels |
| `spin` | spins and springs in, then floats | portraits, orbs, logos as heroes |
| `stamp` | slams down from 160% with a tilt and a flash, then floats | screenshots, report cards, stickers |
| `wipe` | revealed left to right | arrows, underlines, charts, lines |
| `slide` | slides in from the left | brand row, footer |
| `fade` | soft fade up | anything quiet |

Optional per layer: `at` (start time in seconds); top level: `stagger` (default 0.13 s), `loop` (default 4 s).

**Plate** (`plate.mode` in `layers.js`):
- `fill` (default): each box is filled with the average colour of a thin ring around it. Clean on flat or gently graded backgrounds.
- `blur`: a heavily blurred copy of the card. For photos and busy gradients; text ghosts show only while layers are away.
- `image` with `src`: a clean background exported from the design tool. Best result for complex backgrounds.

## Route B: from an HTML card

```bash
mkdir -p og && cp $SKILL/template/og.html og/ && cp portrait.png og/ && cp icon.png og/
# edit CONFIG at the top of og/og.html (kicker, title lines, highlight line, subtitle, portrait, name, brand, colours)
python3 $SKILL/scripts/render_frames.py og/og.html og/frames
```

The template rebuilds the card each loop: staggered exit, title words rising out of masks, a portrait that spins in with a ring shockwave, the subtitle springing up with a flash on its last phrase, the brand row sliding in, a light sweep across the highlighted line, then a hold with drifting glows. `render_frames.py` prints each element's right edge; keep text 40 px or more clear of the portrait.

## What makes a good card (decide before approving the still)

Each rule came from a real review.

1. **Everything continues the title.** Ask of each element: what does it have to do with the title? Metrics ("100+ versions", "3,000+ users"), release numbers ("1.0 → 1.1") and insider terms read as noise to a stranger. A short line that finishes the title's thought beats any stat.
2. **Write for someone who knows nothing about you.** No jargon and no scores whose scale the viewer cannot know.
3. **Readable at 300×157.** Look at every frame at that size. Nothing under ~24 px on the 1200×630 canvas; URLs, QR codes and small mono dates do not survive.
4. **Design a card, not a screenshot.** One title, one supporting line, one visual anchor, one brand mark.
5. **Short and rhythmic beats complete.** Two parallel phrases ("Built for me. Shared with you.") beat three explanatory lines.
6. **Punctuation is design.** A display title often looks better without a trailing period; match the page.
7. **Portraits in circles get scaled ~115%** so no transparent rim shows.

## Motion rules

1. **Fast and physical.** Land everything within ~2 s of a 4 s loop, with damped springs and overshoot. Slow fades read as "not moving".
2. **60 fps, 4 s.** Smooth on retina screens, still a few hundred KB.
3. **Frame 0 is the settled card**, identical to the still. The loop opens with a quick staggered exit (layers streak away with blur in ~0.3 s), rebuilds, then holds.
4. **Ambient motion in the hold** (drifting glows, a floating visual) uses periodic functions of `2πt/T`, so the last frame flows into the first.
5. **Masked text exits as a block.** Sliding a masked word sideways clips it.
6. **Deterministic frames.** No CSS transitions or requestAnimationFrame; pages expose `window.render(t)` and the capture script calls it for each frame.

## Encoding

`scripts/encode.sh`:
- H.264, `yuv420p`, **no audio track**, `+faststart`, 1200×630, CRF 19, Lanczos downscale from 2× captures.
- MP4 **≤ 2 MB** (a 4 s card is usually 300–700 KB). JPEG from frame 0 **< 180 KB**.

Checks that must pass:
- `check_frame0.py`: frame 0 matches the approved still (mean difference under 2).
- `check_loop.py`: the jump from the last frame to the first is no bigger than a normal frame step.

## Meta tags

```html
<meta property="og:image" content="https://example.com/og/home-v3.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Plain sentence describing the card">
<meta property="og:video" content="https://example.com/og/home-v3.mp4">
<meta property="og:video:secure_url" content="https://example.com/og/home-v3.mp4">
<meta property="og:video:type" content="video/mp4">
<meta property="og:video:width" content="1200">
<meta property="og:video:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.com/og/home-v3.jpg">
<meta name="twitter:image:alt" content="Plain sentence describing the card">
```

- Absolute HTTPS URLs.
- **Version by filename (`home-v3.mp4`), never by query string (`home.mp4?v=3`).** Matching the clean URL style of a site whose preview already played was part of the fix.
- New filename on every re-render so crawlers fetch the new file.

## Server: the part that silently breaks playback

Apple's players (iMessage previews, Safari `<video>`) first ask for `Range: bytes=0-1` and only play when the server answers **`206 Partial Content`** with `Accept-Ranges: bytes`. A server that answers `200` with the whole file gets a still image in iMessage, and inline video may not play on iPhone.

```bash
curl -s -o /dev/null -H "Range: bytes=0-1" -w "%{http_code}\n" https://example.com/og/home-v3.mp4   # must be 206
```

- Vercel, R2 custom domains and most CDNs return 206 already.
- **Cloudflare Workers static assets return 200.** Use `worker/range-worker.js` and route only `.mp4` through it:

```jsonc
{
  "main": "range-worker.js",
  "assets": { "directory": "public", "binding": "ASSETS", "run_worker_first": ["/*.mp4", "/**/*.mp4"] }
}
```

  Without `run_worker_first`, asset paths never reach the worker. Keep the worker file out of the public folder. Test with `wrangler dev`: Range → 206, full GET → 200 with `Accept-Ranges`, out-of-range → 416, other pages unchanged.

## After publishing

- `scripts/check_live.sh <page-url>` reads the page's tags and checks both files: status, type, size, https, query strings and the 206 answer. It exits non-zero on any failure.
- iMessage caches a preview per URL on the sender's device; retest with a URL it has never seen (`?t=2`).
- LinkedIn Post Inspector, and the X and Facebook card tools, refresh their caches.
- Platforms decide for themselves whether to animate. Report "eligible and verified over HTTP" until someone has seen it move on a device.

## Files

| File | What |
|---|---|
| `template/from-image.html` | Route A: animates an approved image from `layers.js` (layers, roles, plate) |
| `template/og.html` | Route B: configurable HTML card with the full motion set |
| `scripts/suggest_layers.py` | Proposes layer boxes for an approved image and draws them on a preview |
| `scripts/render_frames.py` | Captures frames at 2× through a local server; prints element edges |
| `scripts/check_frame0.py` | Frame 0 against the approved still |
| `scripts/check_loop.py` | Seam against a normal frame step |
| `scripts/encode.sh` | Frames to MP4 and frame-0 JPEG, with size limits |
| `scripts/check_live.sh` | Live tags, files, https and Range check |
| `worker/range-worker.js` | Cloudflare Worker adding Range / 206 for `.mp4` |
| `examples/` | JoeSpeaking.com (route A) and demo.joespeaking.com (route B), with inputs and outputs |
