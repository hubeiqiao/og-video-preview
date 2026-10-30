---
name: og-video-preview
description: Turn any approved Open Graph image into a looping og:video so link previews move, and make it actually play where previews can play video (iMessage, Discord, Telegram) while every other app shows the matching still. Works from the finished image alone: it reads what each element is (headline, logo, pill, photo, panel, shape, line and more), cuts it out cleanly and gives each kind its own physical motion, with frame 0 pixel-identical to the image. Or from an HTML card. Covers what to animate, motion presets, Playwright frame capture, ffmpeg encoding, seamless-loop and frame-0 checks, the meta tags, and the server requirements (HTTP Range / 206, clean .mp4 URLs, versioned filenames). Use when someone asks for an OG video, animated link preview, animated share card or og:video, wants an existing og:image to move, or has an og:video that only shows a still.
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
| **B. From an HTML card** | You are designing the card in code and want to change its text later without a new image | `template/og.html` |

Requirements: Python 3 with `playwright`, `Pillow`, `opencv-python` and `numpy`; Chrome installed (Playwright uses `channel="chrome"`); `ffmpeg` and `ffprobe`. Optional: Tesseract and `pytesseract`, which find type on photos and 3D scenes and screen out texture that only looks like text.

## Route A: from the approved image

```bash
SKILL=~/.claude/skills/og-video-preview   # the folder this SKILL.md is in
mkdir -p og && cp $SKILL/template/from-image.html og/
python3 $SKILL/scripts/suggest_layers.py approved.png og      # card.jpg, layers.js, plate.png, layers.png, glyphs.png, layers-preview.png
python3 $SKILL/scripts/render_frames.py og/from-image.html og/frames --frames 0,20,40,60,90,150   # preview; prints the motion plan
python3 $SKILL/scripts/check_frame0.py og/card.jpg og/frames/f0000.png
python3 $SKILL/scripts/render_frames.py og/from-image.html og/frames                 # all frames
python3 $SKILL/scripts/check_loop.py og/frames
bash    $SKILL/scripts/encode.sh og/frames public/og/home-v1 # home-v1.mp4 + home-v1.jpg
```

Requires `opencv-python` and `numpy` besides Playwright and Pillow. Any size or ratio works: the card is cover-cropped to 1200×630 first.

### 1. Read the card: what is each element?

`suggest_layers.py` models the background (a flat colour, or a smooth estimate under a gradient or photo), marks everything that stands out, groups it into elements, and decides what each one **is** from how it looks. Three cases are handled before that:
- a big surface (a window, a card on a backdrop) becomes background and is searched again for the elements on it;
- a full-card picture or scene (a 3D render, a photo, a dense illustration) stays in the plate, and only the type on it becomes layers: Tesseract reads where the lines are, and every glyph pixel goes to the nearest read line;
- grids and hairline patterns stay in the background.

| Kind | How it is recognised |
|---|---|
| `headline` | text lines whose cap height is near the largest on the card |
| `text` | other text lines (one colour, many glyphs of regular height) |
| `label` | small text: kickers, URLs, captions |
| `logo` | a mark at the start of, or just left of, a text line: taller than its letters, another colour, or solid |
| `pill` | a solid bar, wider than tall, with content in it: tags, buttons |
| `icon` | a small graphic with inner detail: emoji, mascots, app icons |
| `avatar` | a round element with photo detail |
| `photo` | a solid rectangle with many colours |
| `panel` | a large solid surface: screenshots, UI cards, sticky notes |
| `illustration` | a larger multicolour graphic |
| `shape` | a one-colour form: dots, squares, blobs, triangles |
| `stroke` | thin and long: lines, arrows, underlines, squiggles |

Text is split into lines, lines into words, and a one-word headline into letters. Look at `layers-preview.png` (each box is labelled with its id; the underline marks its parts). If an element is read wrongly, change its `kind` in `layers.js`; that needs no new cut. A box you add by hand is cut as a rectangle (or a disc with `"cut": "disc"`); run `make_plate.py og` after adding or removing boxes. To change which pixels an element owns, re-run `suggest_layers.py` instead.

### 2. Cut it so only the element moves

`make_plate.py` writes:
- `plate.png`: the card with every element removed and the background refilled (smooth fill for shapes, texture-preserving inpaint behind type on photos and gradients).
- `layers.png`: the card with alpha 1 over each element and a soft edge just outside it. Where the alpha is partial, plate and card are identical, so the layers over the plate reproduce the card exactly. Type keeps only its glyphs: no box of background travels with a word.
- `cuts/<id>.png`: the same, one image per layer with only that layer's pixels, so boxes may overlap (tight leading, a pill inside a line) without a line carrying pieces of its neighbour.
- `glyphs.png`: each element's own pixels, a mask for light sweeps.
- `light.png`: where an element is lighter than the refilled background behind it, the mask for the light that runs through a picture that stays in place.

A soft shadow or glow travels with its element: faint pixels around it that differ from the background model are part of its cut.

**A clean background lets everything move.** A refill is never perfect behind a large visual on a picture, which is why such visuals settle in place. When an image-edit tool is available (any model that can edit an image from a reference), ask it for the approved image with every element removed: the background alone, same colour, light and texture, no ghost outlines (check it at 3x where the elements were). Pass it to the analyzer:

```bash
python3 $SKILL/scripts/suggest_layers.py og.jpg og --plate og-clean.png
```

`make_plate.py` then fills every hole from it, nothing has to settle, and the style becomes `flow`. For a visual-led card (an illustration, a scene of separate objects), this is what makes it lively; design such a card with its objects apart from each other, so each can move on its own.

### 3. Motion comes from the kind

Each kind has an entrance, an exit, an idle movement and an accent, built on the house tokens of physical-motion-design: `cubic-bezier(0.22, 1, 0.36, 1)` (smooth) for entrances, `cubic-bezier(0.35, 1.55, 0.65, 1)` (spring) only for pops, damped springs for anything with weight, and exits that are the smooth curve reversed (softer and shorter than entrances).

| Kind | Enters | Leaves | Lives | Accent |
|---|---|---|---|---|
| `headline` | words (or letters) rise out of the line's own mask, staggered, on a spring | sinks back into the mask | stays still | the card's choice: a light sweep through the glyphs, the letters hopping in turn, or a star opening on the last line; camera punch when the last line lands |
| `text` | fade + 14 px rise + 3 px blur clearing, 0.42 s smooth | fade, drop, blur | | sweep if it has an accent colour |
| `label` | wipes on left to right with a short slide | fade | | |
| `logo` | scales up from 35 % with a spin, on a spring | shrinks and turns away | gentle bob and tilt | the card's choice of one turn: flat, over in 3D like a coin, a swing that settles, or a pop with a star and a ring |
| wordmark | unfurls out of its logo, left to right | | | sweep |
| `pill` | pops on the spring curve (overshoot) | shrinks | a small pulse (living) | a sweep, or a light circling it |
| `icon` | springs up from 30 % with a small turn | shrinks | bob and tilt | the same turn as the card's logo; in a crowd of more than three, small icons only pop in turn |
| `avatar` | springs up from 50 % with a turn | shrinks and turns | float | ring ripple |
| `photo` | opens from the middle (clip) while settling from 110 % | fade, slight shrink | slow push-in and drift | |
| `panel` | lifts 42 px with a scale from 94 % and a clearing blur | fade, drop | float | glancing reflection |
| `illustration` | rises with a squash on landing | fade, drop | sway and bob | |
| `shape` (small) | pops from 0, rippling outward from the headline | shrinks to 0 | twinkle | |
| `shape` (large) | grows from 80 % out of a blur | fade | decorative blobs (large, or bleeding off the card) flow like liquid, then settle; a centred mark stays crisp | |
| `stroke` | draws at a pen's even pace along its long axis; an arrow (its two barbs found on the skeleton) draws from its tail to its head | undraws | redraws (living) | |

**Visuals that cannot leave cleanly settle instead.** A photo, panel, illustration or avatar that sits on something other than the plain background (a photo inside a UI, a poster in a stack), or covers a fifth of the card, never exposes the plate: it leans toward the viewer (scale 103.5 % with a light blur) during the exit and springs back when its turn comes. Light then runs through its own lit parts (`light.png`: where it is brighter than the background behind it), so a print, a glint or a pale object comes alive without the soft edge of its cut showing. Shapes on the background leave and come back, and their holes are refilled from the background model, not smeared from their neighbours.

**Accents differ from card to card.** Not every card gets the same light sweep: each card picks, from its own layout, one accent for its headlines, one turn for its marks and one for its pills, and every element of a kind shares it, so a card stays coherent and two cards rarely match. The same card always gets the same video. Set them in `layers.js` with `fx` (`{"headline": "sheen|hop|glint", "mark": "spin|flip|wobble|pop", "pill": "sheen|orbit", "texture": "ripple|wind|swirl"}`), or per layer with `fx` and `turn`.

**Textures move as one surface.** A fine line pattern over the card (a wave grid, contour lines, a guilloche) is found as many thin, faint, colourless pieces spread across the card; they stay in the plate instead of flying apart as separate shapes (`texture` in `layers.js`), and the plate itself is warped in place: rings spreading from the headline (`ripple`), a wave passing across (`wind`) or a slow turn around the headline (`swirl`). The pattern stays calm right behind the type, and the warp is exactly zero at the loop point. Of the 103 eval cards, only ElevenLabs has one.

**Camera.** On a graded or pictorial background the whole card breathes: a slow push-in of about 2 % that returns to 1 at the loop point, so background and layers move together and nothing slides against what is behind it. The headline's landing adds a short, damped punch.

**Choreography** is automatic: elements enter in reading order (rows top to bottom, left to right), visuals arrive with the words rather than after them, small decorations ripple outward from the headline, a wordmark follows its logo, and the whole entrance is compressed to land by about 2 s of the 4 s loop. `render_frames.py` prints the plan (kind, motion, start time, accents) before capturing.

**Style** (`style` in `layers.js`):
- `rebuild` (default): a quick staggered exit in the first 0.34 s, then everything re-enters.
- `flow` (default with `--plate`): nothing leaves, and every visual keeps moving through the whole loop, each on its own path: drift, a 3D tilt and a slow turn, nearer (bigger) visuals moving further, so the card has depth. Type stays still and readable. Every move is a sine of the loop, so frame 0 is the card and the loop closes on it.
- `living` (default when the type sits on a photo or a 3D scene, where no refill behind it looks clean): nothing leaves. Type stays still and readable while light sweeps through it, the camera breathes, decorative blobs flow, a logo turns once, lines redraw. Jed Bridges' og:video cards are the model: the title stays readable the whole time while one or two things move.

**Energy** (`energy`): `calm` (smaller moves, no overshoot, no accents), `lively` (default), `bold` (more overshoot, plus a flare across the card, drifting glows and sparks off the last headline word).

**Overrides per layer**: `kind`, `motion` (use another kind's motion), `at` (start time in seconds), `idle` (how much it moves while it lives: 0 keeps it still, 1 is the default, up to 2; in a card that shows a change, keep the before still and let the after move). Top level: `fx` (above), `accent` ("r,g,b" for sweeps, stars and rings; otherwise the first saturated text colour, and white type without one gets no sweep), `loop`.

Every extra (idle, sweeps, rings, glows, punch, liquid edges, the breathing of a graded background) is exactly zero at t = 0 and t = loop, so the loop closes on the approved card.

Tested on the OG images of 103 well-known sites in the repository's [`eval/`](https://github.com/hubeiqiao/og-video-preview/tree/main/eval) (developer tools, venture capital firms, AI companies and technology companies) (`python3 eval/run.py` renders and scores all of them; run it after any change to the engine). Where a reading is wrong it is usually one of: a text line containing a pill or avatars, a dense UI screenshot (many small parts), stylised capitals Tesseract cannot read. Fix those with `kind` in `layers.js`.

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

1. **Fast and physical.** Land everything within about 2 s of a 4 s loop. Springs for anything with weight, the spring curve only for pops, the smooth curve for everything else. Slow fades read as "not moving".
2. **Motion follows the element.** Type rises out of its own line, marks spin in, pills pop, photos open, panels lift, lines draw. Never one preset for everything.
3. **One hero moment.** One camera punch when the headline lands, one light sweep per element at most. Accents should not compete.
4. **60 fps, 4 s.** Smooth on retina screens, still a few hundred KB.
5. **Frame 0 is the settled card**, identical to the still, and the loop closes on it: every idle, accent and camera move is zero at t = 0 and t = loop.
6. **Nothing reveals a hole.** What cannot be refilled cleanly moves in place instead of leaving.
7. **Deterministic frames.** No CSS transitions or requestAnimationFrame; pages expose `window.render(t)` and the capture script calls it for each frame.

## Encoding

`scripts/encode.sh`:
- H.264, `yuv420p`, **no audio track**, `+faststart`, 1200×630, CRF 19 (raised to 22, 25, then 28 until the MP4 fits 2 MB), Lanczos downscale from 2× captures.
- MP4 **≤ 2 MB** (a 4 s card is usually 300–700 KB). JPEG from frame 0 **< 180 KB**.

Checks that must pass:
- `check_frame0.py`: frame 0 matches the approved still: mean difference under 2, and no local defects (a gap between letters, a missing edge) on more than 0.05 % of pixels.
- `check_loop.py`: the jump from the last frame to the first is no bigger than 1.5 normal frame steps (plus 4 levels of slack).

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

## Where og:video plays (checked 2026-10-30)

Most apps read only `og:image`. **Where video is not supported, the app simply shows your `og:image`, the approved still, exactly as it did before you added og:video; nothing breaks.** The video is a bonus where it plays, which is why frame 0 must be that same image: the still and the moving card always agree.

| App | What it shows | Conditions and source |
|---|---|---|
| iMessage | **Plays**: autoplays muted and loops | Direct MP4 link; the page under 1 MB, icon + image + video under 10 MB; with autoplay off or Reduce Motion, the still with a play button. Apple [TN3156](https://developer.apple.com/documentation/technotes/tn3156-create-rich-previews-for-messages). Needs HTTP Range (206), see below |
| Discord | **Plays**: inline player with a play button, no autoplay | MP4, WebM or MOV over https; `og:image` is required and becomes the first frame; the whole fetch must finish within 10 s, at most 50 MB; previews cached about 30 min. Discord's docs also ask for `og:type` `video.other` or `twitter:card` `player`; a device test (checkmyog, 24 Oct 2026) played a plain `website` page too. [Discord link previews](https://docs.discord.com/developers/link-previews/overview) |
| Telegram | **Plays**: as a looping GIF | Our test on 30 Oct 2026 played the og:video as a looping GIF in the link preview. An earlier device test on 24 Oct 2026 saw only the still ([checkmyog](https://github.com/twidtwid/checkmyog)), so clients may differ: test yours |
| Slack | Still | Classic unfurls read Open Graph and show `og:image`; inline video only for sites Slack handles itself or an app unfurl. [Slack unfurling](https://docs.slack.dev/messaging/unfurling-links-in-messages/) |
| X, Facebook, LinkedIn, WhatsApp, Signal, Bluesky, Mastodon, Matrix / Element | Still | Each reads `og:image`; none plays `og:video` in a link card (X's large card needs `twitter:card` `summary_large_image`). The viral og:video clips on X were iMessage screen recordings |

Sources were read on 2026-10-30; the per-app device tests are from [checkmyog](https://github.com/twidtwid/checkmyog) (MIT), whose support table cites each one.

## After publishing

- `scripts/check_live.sh <page-url>` reads the page's tags and checks both files: absolute https URLs, a 200 answer with a non-empty body of the right type (image, video/mp4), and the 206 answer to a Range request. It warns about query strings and an MP4 over 2 MB, and exits non-zero on any failure.
- iMessage caches a preview per URL on the sender's device; retest with a URL it has never seen (`?t=2`).
- LinkedIn Post Inspector, and the X and Facebook card tools, refresh their caches.
- Platforms decide for themselves whether to animate (see the table above). Report "eligible and verified over HTTP" until someone has seen it move on a device.

## Files

| File | What |
|---|---|
| `template/from-image.html` | Route A: the motion engine; turns `layers.js` (elements and kinds) into motion |
| `template/og.html` | Route B: configurable HTML card with the full motion set |
| `scripts/suggest_layers.py` | Reads an approved image: finds and classifies its elements, splits type into lines, words and letters |
| `scripts/make_plate.py` | Clean plate, element cutouts and glyph masks (re-run after editing boxes) |
| `scripts/render_frames.py` | Captures frames at 2× through a local server; prints element edges |
| `scripts/check_frame0.py` | Frame 0 against the approved still |
| `scripts/check_loop.py` | Seam against a normal frame step |
| `scripts/encode.sh` | Frames to MP4 and frame-0 JPEG, with size limits |
| `scripts/check_live.sh` | Live tags, files, https and Range check |
| `worker/range-worker.js` | Cloudflare Worker adding Range / 206 for `.mp4` |
| [`examples/`](https://github.com/hubeiqiao/og-video-preview/tree/main/examples) | Worked examples (route A, living style, route B) with inputs and outputs |
| [`eval/`](https://github.com/hubeiqiao/og-video-preview/tree/main/eval) | 103 real OG images, `fetch.py` that downloads them, the runner that renders and scores them, and the results |
