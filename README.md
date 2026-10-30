# OG Video Preview

![OG Video Preview](social/hero.gif)

An agent skill that turns any approved Open Graph image into a looping `og:video`, so your link previews move, and makes sure the video actually plays in iMessage, Safari and social cards.

> Works with [Claude Code](https://claude.com/claude-code), [OpenAI Codex](https://openai.com/index/codex/), [Cursor](https://cursor.sh) and other agents that support the [Agent Skills](https://agentskills.io) standard.

## Watch it

[16-second promo (MP4)](social/promo.mp4): it opens on the X post that started this (its own og:video playing), then turns an OG image into video in one prompt. Made with Remotion; music "Deep Urban" from Mixkit (free licence); sound effects from [earshot](https://github.com/Leonxlnx/earshot).

## Examples

Every route A example below starts from the approved image alone. The skill read each card, chose every motion and rendered it with no hand tuning. `out/layers-preview.png` in each folder shows what it recognised.

**JoeSpeaking.com homepage card.** The pill pops, the headline rises letter by letter, the report card settles in place, the orb and its arrow rise, the wordmark unfurls from its logo.

![JoeSpeaking.com OG video](examples/joespeaking-home/out/preview.gif)

**hubeiqiao.com home card.** Type rises word by word and letter by letter on a dark vignette, the portrait springs in with a ring.

![hubeiqiao.com OG video](examples/hubeiqiao-home/out/preview.gif)

**hubeiqiao.com/co card.** Type over a photo: the photo stays, the camera breathes, and each line rises back in over a refilled background.

![hubeiqiao.com/co OG video](examples/hubeiqiao-co/out/preview.gif)

**A TON of Demos talk card, from its still.** The same card as the route B example below, animated from the finished JPG instead of the HTML.

![A TON of Demos OG video](examples/ton-of-demos/out/preview.gif)

**Living style.** Nothing leaves: the blobs flow and settle, the title stays readable the whole time.

![Living style OG video](examples/living-blobs/out/preview.gif)

**demo.joespeaking.com talk card**, built as an HTML card (route B).

![demo.joespeaking.com OG video](examples/demo-joespeaking/out/preview.gif)

Rebuild all of them with `bash examples/build-examples.sh`. The engine was also run on the OG images of 60+ well-known sites. Their images belong to the sites, so they are not in this repo: `bash examples/gallery/run.sh` fetches and renders them on your machine.

## How it works

1. **Approve the still.** Get the 1200×630 `og:image` right first.
2. **Turn that exact image into motion.** The skill reads the approved image and works out what each element is: headline, body text, label, logo, pill, icon, avatar, photo, panel, illustration, shape or line. It cuts each one out cleanly over a refilled background, and each kind gets its own physical motion. Type rises word by word out of its own line, marks spin in, pills pop, photos open, panels lift and lines draw, all on one set of easing curves and springs. Frame 0 and the last frame are the approved image, pixel for pixel.
3. **Publish both**, with tags and a server that let link previews play the video.

Two routes:

| Route | Start from | Good for |
|---|---|---|
| A. From the approved image | any PNG/JPG, made anywhere | existing cards, cards from Figma or Canva |
| B. From an HTML card | `template/og.html` | new cards designed in code |

## The part that silently breaks playback

Apple's players request `Range: bytes=0-1` first and only play when the server answers **206 Partial Content**. Cloudflare Workers static assets answer 200 with the whole file, so the preview falls back to the still image. The skill checks for this (`scripts/check_live.sh`) and ships a small Worker that fixes it (`worker/range-worker.js`). It also versions files by name (`home-v3.mp4`) instead of query strings.

## Installation

### Claude Code plugin

```bash
/plugin marketplace add hubeiqiao/og-video-preview
/plugin install og-video-preview@og-video-preview-marketplace
```

### Agent Skills

```bash
npx skills add hubeiqiao/og-video-preview
```

### Manual

```bash
git clone https://github.com/hubeiqiao/og-video-preview.git ~/.claude/skills/og-video-preview
```

Requirements: Python 3 with `playwright` and `Pillow`, Google Chrome, `ffmpeg`.

## Usage

```
Use /og-video-preview to make my og:image move
```
```
Turn public/og/home.jpg into an OG video and wire up the tags
```
```
My og:video only shows a still in iMessage. Find out why.
```

The skill will:
1. Confirm the still is approved (or help design it, with rules for cards strangers can read at thumbnail size)
2. Propose layers and motion roles for the image
3. Render a few preview frames for review, then the full 60 fps loop
4. Check that frame 0 matches the approved image and that the loop has no visible jump
5. Encode the MP4 and JPEG, write the meta tags, and check the live server answers Range requests

## What's inside

```
og-video-preview/
├── SKILL.md                 # workflow, card and motion rules, tags, server requirements
├── template/
│   ├── from-image.html      # route A: animate an approved image from layers.js
│   └── og.html              # route B: configurable HTML card
├── scripts/
│   ├── suggest_layers.py    # propose layer boxes for an image
│   ├── render_frames.py     # Playwright frame capture at 2x
│   ├── check_frame0.py      # frame 0 vs the approved still
│   ├── check_loop.py        # seamless loop check
│   ├── encode.sh            # MP4 + JPEG with size limits
│   └── check_live.sh        # live tags, files and Range check
├── worker/range-worker.js   # Range / 206 support on Cloudflare Workers assets
├── examples/                # JoeSpeaking.com and demo.joespeaking.com
└── social/                  # this repo's own hero, social preview and promo
```

## Credits

Inspired by [Michael Pfister](https://x.com/pfista)'s [post on X](https://x.com/pfista/status/2113288415546638515): "this is your sign to start using og:video on your website".

Built by [Joe Hu](https://x.com/hubeiqiao) while making the link previews for [Joe Speaking](https://joespeaking.com) and a talk at A TON of Demos Ottawa.

## License

MIT
