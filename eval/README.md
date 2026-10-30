# Eval: 61 real OG images

The skill should work on any approved OG image, not only on cards made for it. This folder is its test: the Open Graph images of 61 well-known sites, each put through the whole route A pipeline with no hand tuning, and scored.

![Contact sheet](sheet.jpg)

```bash
python3 eval/run.py              # all cards, 3 at a time: out/*.mp4, results.json, sheet.jpg, the table below
python3 eval/run.py --only stripe,github --keep   # a few cards, keeping their layers.js, cuts and frames in eval/work/
```

What is measured on every card:

| Check | Pass when |
|---|---|
| Frame 0 | it equals the card: mean difference ≤ 2, and local defects (a gap between letters, a missing edge) on ≤ 0.05 % of pixels |
| Seam | the jump from the last frame to the first is no bigger than an ordinary frame step |
| Size | MP4 ≤ 2 MB, frame-0 JPEG ≤ 180 KB |

`results.json` also records what the engine decided for each card (how many layers, which kinds, rebuild or living), so a change to the engine can be compared card by card. Re-run after any change to `scripts/` or `template/from-image.html` and read the diff of `results.json` and `sheet.jpg`.

The images in `cards/` were fetched from each site's `og:image` on 2026-10-29 (`sites.txt` lists the pages) and cover-cropped to 1200×630. They belong to their owners and are here only as test inputs; they are not covered by this repository's MIT licence.

<!-- results -->
**61 of 61 cards pass.**

| Card | Layers | Kinds | Style | Frame 0 (mean / local) | Seam / step | MP4 | Pass |
|---|---|---|---|---|---|---|---|
| [anthropic](out/anthropic.mp4) | 1 | headline 1 | rebuild | 0.221 / 0.0% | 0 / 2 | 64 KB | yes |
| [arc](out/arc.mp4) | 2 | illustration 1, headline 1 | rebuild | 0.349 / 0.0% | 0 / 1 | 133 KB | yes |
| [astro](out/astro.mp4) | 13 | illustration 8, headline 2, logo 1, text 1, pill 1 | rebuild | 1.588 / 0.0% | 0 / 3 | 735 KB | yes |
| [bolt](out/bolt.mp4) | 1 | headline 1 | rebuild | 0.507 / 0.0% | 0 / 2 | 256 KB | yes |
| [bun](out/bun.mp4) | 5 | headline 3, logo 1, label 1 | rebuild | 0.906 / 0.0% | 0 / 2 | 274 KB | yes |
| [cal](out/cal.mp4) | 18 | pill 9, label 4, icon 2, text 1, headline 1, illustration 1 | rebuild | 0.996 / 0.0% | 1 / 1 | 244 KB | yes |
| [calendly](out/calendly.mp4) | 14 | label 5, shape 4, illustration 2, logo 1, headline 1, icon 1 | rebuild | 0.988 / 0.0% | 1 / 3 | 563 KB | yes |
| [clerk](out/clerk.mp4) | 7 | stroke 2, headline 2, logo 1, text 1, shape 1 | rebuild | 0.639 / 0.0% | 0 / 1 | 181 KB | yes |
| [cursor](out/cursor.mp4) | 2 | logo 1, headline 1 | rebuild | 0.201 / 0.0% | 0 / 1 | 62 KB | yes |
| [deno](out/deno.mp4) | 5 | text 4, headline 1 | rebuild | 0.576 / 0.0% | 0 / 1 | 213 KB | yes |
| [discord](out/discord.mp4) | 18 | icon 15, headline 1, logo 1, illustration 1 | rebuild | 0.936 / 0.0% | 0 / 3 | 638 KB | yes |
| [dropbox](out/dropbox.mp4) | 2 | shape 2 | rebuild | 0.113 / 0.0% | 1 / 1 | 157 KB | yes |
| [dub](out/dub.mp4) | 18 | icon 5, label 4, shape 2, text 2, stroke 2, illustration 1, headline 1, avatar 1 | rebuild | 1.169 / 0.0% | 0 / 1 | 299 KB | yes |
| [excalidraw](out/excalidraw.mp4) | 14 | icon 8, shape 2, logo 1, headline 1, text 1, label 1 | rebuild | 0.589 / 0.0% | 0 / 1 | 277 KB | yes |
| [figma](out/figma.mp4) | 7 | headline 3, icon 2, stroke 1, illustration 1 | rebuild | 1.334 / 0.0% | 1 / 2 | 427 KB | yes |
| [fly](out/fly.mp4) | 9 | icon 4, headline 3, avatar 1, text 1 | rebuild | 1.37 / 0.0% | 0 / 3 | 706 KB | yes |
| [framer](out/framer.mp4) | 18 | headline 6, label 4, shape 3, illustration 2, icon 2, stroke 1 | living | 1.685 / 0.0% | 0 / 3 | 976 KB | yes |
| [ghost](out/ghost.mp4) | 18 | icon 14, illustration 3, avatar 1 | rebuild | 0.823 / 0.0% | 1 / 2 | 416 KB | yes |
| [github](out/github.mp4) | 10 | shape 4, illustration 3, headline 2, icon 1 | rebuild | 0.639 / 0.0% | 1 / 2 | 236 KB | yes |
| [granola](out/granola.mp4) | 8 | icon 4, headline 4 | rebuild | 1.297 / 0.0% | 0 / 2 | 749 KB | yes |
| [gumroad](out/gumroad.mp4) | 6 | illustration 5, headline 1 | rebuild | 1.082 / 0.0% | 0 / 2 | 652 KB | yes |
| [huggingface](out/huggingface.mp4) | 3 | headline 2, illustration 1 | rebuild | 0.502 / 0.0% | 0 / 2 | 206 KB | yes |
| [intercom](out/intercom.mp4) | 5 | headline 3, photo 1, text 1 | rebuild | 1.37 / 0.0% | 15 / 12 | 288 KB | yes |
| [linear](out/linear.mp4) | 2 | logo 1, headline 1 | rebuild | 0.181 / 0.0% | 0 / 2 | 181 KB | yes |
| [loom](out/loom.mp4) | 17 | icon 6, illustration 4, headline 3, stroke 2, shape 1, label 1 | rebuild | 0.822 / 0.0% | 1 / 3 | 407 KB | yes |
| [mailchimp](out/mailchimp.mp4) | 3 | headline 2, logo 1 | rebuild | 0.41 / 0.0% | 0 / 2 | 180 KB | yes |
| [mintlify](out/mintlify.mp4) | 4 | shape 3, headline 1 | rebuild | 0.187 / 0.0% | 0 / 1 | 81 KB | yes |
| [miro](out/miro.mp4) | 1 | shape 1 | rebuild | 0.157 / 0.0% | 1 / 1 | 186 KB | yes |
| [mobbin](out/mobbin.mp4) | 18 | icon 8, headline 4, illustration 2, shape 1, pill 1, avatar 1, label 1 | rebuild | 1.145 / 0.0% | 0 / 2 | 468 KB | yes |
| [netlify](out/netlify.mp4) | 13 | icon 6, avatar 3, headline 2, text 1, shape 1 | rebuild | 0.718 / 0.0% | 0 / 3 | 508 KB | yes |
| [nextjs](out/nextjs.mp4) | 2 | headline 1, text 1 | rebuild | 0.129 / 0.0% | 0 / 2 | 39 KB | yes |
| [notion](out/notion.mp4) | 14 | stroke 3, icon 3, text 2, headline 2, shape 2, logo 1, illustration 1 | rebuild | 1.215 / 0.0% | 0 / 1 | 409 KB | yes |
| [obsidian](out/obsidian.mp4) | 5 | illustration 2, stroke 1, headline 1, text 1 | rebuild | 0.391 / 0.0% | 1 / 2 | 231 KB | yes |
| [perplexity](out/perplexity.mp4) | 3 | icon 1, headline 1, text 1 | rebuild | 0.322 / 0.0% | 0 / 1 | 123 KB | yes |
| [pitch](out/pitch.mp4) | 2 | logo 1, headline 1 | rebuild | 0.16 / 0.0% | 0 / 1 | 256 KB | yes |
| [planetscale](out/planetscale.mp4) | 18 | logo 5, text 4, label 4, shape 3, headline 1, icon 1 | rebuild | 1.056 / 0.0% | 0 / 2 | 318 KB | yes |
| [posthog](out/posthog.mp4) | 9 | icon 3, illustration 2, stroke 1, logo 1, headline 1, pill 1 | rebuild | 0.733 / 0.0% | 1 / 2 | 588 KB | yes |
| [railway](out/railway.mp4) | 18 | icon 7, illustration 4, headline 3, logo 1, text 1, label 1, shape 1 | rebuild | 0.781 / 0.0% | 2 / 2 | 401 KB | yes |
| [raycast](out/raycast.mp4) | 17 | icon 8, label 5, logo 1, text 1, headline 1, illustration 1 | rebuild | 1.03 / 0.0% | 0 / 1 | 276 KB | yes |
| [replit](out/replit.mp4) | 11 | shape 3, icon 3, illustration 2, headline 2, label 1 | rebuild | 0.488 / 0.0% | 1 / 2 | 510 KB | yes |
| [resend](out/resend.mp4) | 18 | shape 4, label 4, stroke 3, illustration 3, icon 2, headline 1, pill 1 | rebuild | 0.684 / 0.0% | 1 / 2 | 279 KB | yes |
| [retool](out/retool.mp4) | 6 | text 2, headline 2, label 1, shape 1 | living | 1.399 / 0.0% | 0 / 2 | 694 KB | yes |
| [rive](out/rive.mp4) | 17 | stroke 4, text 2, headline 2, logo 2, label 2, icon 2, illustration 2, shape 1 | rebuild | 0.988 / 0.0% | 1 / 2 | 251 KB | yes |
| [sentry](out/sentry.mp4) | 18 | label 6, stroke 4, illustration 3, pill 2, shape 1, icon 1, text 1 | living | 0.664 / 0.0% | 1 / 2 | 519 KB | yes |
| [shopify](out/shopify.mp4) | 8 | icon 5, headline 1, stroke 1, shape 1 | rebuild | 1.151 / 0.0% | 0 / 2 | 235 KB | yes |
| [slack](out/slack.mp4) | 3 | logo 1, headline 1, text 1 | rebuild | 0.22 / 0.0% | 0 / 1 | 87 KB | yes |
| [spline](out/spline.mp4) | 3 | illustration 2, label 1 | rebuild | 0.189 / 0.0% | 0 / 1 | 108 KB | yes |
| [spotify](out/spotify.mp4) | 18 | icon 7, illustration 5, stroke 2, label 2, shape 2 | rebuild | 1.597 / 0.0% | 0 / 3 | 888 KB | yes |
| [stripe](out/stripe.mp4) | 3 | shape 2, headline 1 | rebuild | 0.574 / 0.0% | 0 / 1 | 549 KB | yes |
| [supabase](out/supabase.mp4) | 4 | headline 2, logo 1, text 1 | rebuild | 0.414 / 0.0% | 0 / 1 | 134 KB | yes |
| [superhuman](out/superhuman.mp4) | 10 | logo 2, illustration 2, icon 2, label 2, avatar 1, text 1 | rebuild | 1.051 / 0.0% | 0 / 1 | 860 KB | yes |
| [tailwindcss](out/tailwindcss.mp4) | 18 | icon 8, shape 3, label 2, headline 2, illustration 2, logo 1 | rebuild | 1.175 / 0.0% | 1 / 1 | 450 KB | yes |
| [tldraw](out/tldraw.mp4) | 2 | logo 1, headline 1 | rebuild | 0.28 / 0.0% | 0 / 1 | 116 KB | yes |
| [typeform](out/typeform.mp4) | 1 | headline 1 | rebuild | 0.165 / 0.0% | 0 / 2 | 54 KB | yes |
| [v0](out/v0.mp4) | 2 | headline 2 | rebuild | 0.283 / 0.0% | 0 / 2 | 67 KB | yes |
| [vercel](out/vercel.mp4) | 1 | illustration 1 | rebuild | 0.085 / 0.0% | 1 / 1 | 78 KB | yes |
| [vite](out/vite.mp4) | 8 | headline 3, illustration 2, label 1, logo 1, stroke 1 | living | 0.528 / 0.0% | 0 / 2 | 1226 KB | yes |
| [warp](out/warp.mp4) | 7 | icon 3, shape 2, illustration 1, panel 1 | rebuild | 1.169 / 0.0% | 1 / 1 | 269 KB | yes |
| [webflow](out/webflow.mp4) | 18 | illustration 6, icon 5, label 4, logo 1, headline 1, stroke 1 | rebuild | 1.579 / 0.0% | 1 / 3 | 835 KB | yes |
| [zapier](out/zapier.mp4) | 18 | label 8, headline 6, icon 2, illustration 1, logo 1 | living | 1.023 / 0.0% | 0 / 3 | 354 KB | yes |
| [zed](out/zed.mp4) | 18 | label 8, illustration 6, logo 1, text 1, headline 1, stroke 1 | rebuild | 1.655 / 0.0% | 0 / 2 | 796 KB | yes |
<!-- /results -->
