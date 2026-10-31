# Eval: 103 real OG images

The skill should work on any approved OG image, not only on cards made for it. This folder is its test: the Open Graph images of 103 well-known sites (developer tools and products, venture capital firms, AI companies and technology companies), each put through the whole route A pipeline with no hand tuning, and scored.

![Contact sheet](sheet.jpg)

```bash
python3 eval/fetch.py            # download the og:image of every site in sites.txt that is not in cards/ yet
python3 eval/run.py              # all cards, 3 at a time: out/*.mp4, results.json, sheet.jpg, the table below
python3 eval/run.py --only stripe,github --keep   # a few cards, keeping their layers.js, plate and cuts in eval/work/
```

What is measured on every card:

| Check | Pass when |
|---|---|
| Frame 0 | it equals the card: mean difference ≤ 2, and local defects (a gap between letters, a missing edge) on ≤ 0.05 % of pixels |
| Seam | the jump from the last frame to the first is at most 1.5 ordinary frame steps (plus 4 levels of slack) |
| Size | MP4 ≤ 2 MB, frame-0 JPEG ≤ 180 KB |

`results.json` also records what the engine decided for each card (how many layers, which kinds, rebuild or living), so a change to the engine can be compared card by card. Re-run after any change to `scripts/` or `template/from-image.html` and read the diff of `results.json` and `sheet.jpg`.

The images in `cards/` were fetched from each site's `og:image` by `fetch.py` (`sites.txt` lists the pages, in groups with the date each group was fetched: 2026-10-29 and 2026-10-30) and cover-cropped to 1200×630. Sites with no og:image, a square logo instead of a link card, or a server that refuses the request are skipped. They belong to their owners and are here only as test inputs; they are not covered by this repository's MIT licence.

<!-- results -->
**103 of 103 cards pass.**

| Card | Layers | Kinds | Style | Frame 0 (mean / local) | Seam / step | MP4 | Pass |
|---|---|---|---|---|---|---|---|
| [a16z](out/a16z.mp4) | 4 | text 2, headline 1, icon 1 | living | 0.524 / 0.0% | 0 / 2 | 1263 KB | yes |
| [accel](out/accel.mp4) | 3 | illustration 3 | rebuild | 0.163 / 0.0% | 1 / 4 | 316 KB | yes |
| [amd](out/amd.mp4) | 18 | label 11, illustration 2, icon 2, shape 1, text 1, stroke 1 | living | 0.413 / 0.0% | 0 / 2 | 1053 KB | yes |
| [anthropic](out/anthropic.mp4) | 1 | headline 1 | rebuild | 0.07 / 0.0% | 1 / 3 | 92 KB | yes |
| [apple](out/apple.mp4) | 1 | shape 1 | rebuild | 0.007 / 0.0% | 0 / 1 | 41 KB | yes |
| [arc](out/arc.mp4) | 2 | illustration 1, headline 1 | rebuild | 0.131 / 0.0% | 53 / 52 | 262 KB | yes |
| [astro](out/astro.mp4) | 13 | illustration 8, headline 2, logo 1, text 1, pill 1 | rebuild | 0.397 / 0.0% | 0 / 3 | 742 KB | yes |
| [bolt](out/bolt.mp4) | 1 | headline 1 | rebuild | 0.17 / 0.0% | 0 / 2 | 260 KB | yes |
| [bun](out/bun.mp4) | 7 | label 3, avatar 1, shape 1, illustration 1, headline 1 | rebuild | 0.325 / 0.0% | 0 / 1 | 312 KB | yes |
| [bvp](out/bvp.mp4) | 3 | stroke 1, shape 1, icon 1 | living | 0.433 / 0.0% | 0 / 1 | 1128 KB | yes |
| [cal](out/cal.mp4) | 18 | label 7, icon 6, illustration 3, text 1, headline 1 | rebuild | 0.271 / 0.0% | 1 / 1 | 261 KB | yes |
| [calendly](out/calendly.mp4) | 18 | label 5, shape 4, illustration 4, icon 3, logo 1, headline 1 | rebuild | 0.28 / 0.0% | 1 / 3 | 576 KB | yes |
| [canva](out/canva.mp4) | 10 | illustration 6, icon 3, stroke 1 | rebuild | 0.273 / 0.0% | 0 / 2 | 591 KB | yes |
| [clerk](out/clerk.mp4) | 11 | label 4, stroke 3, headline 2, logo 1, text 1 | rebuild | 0.238 / 0.0% | 0 / 1 | 195 KB | yes |
| [cloudflare](out/cloudflare.mp4) | 0 |  | living | 0.358 / 0.0% | 0 / 1 | 1095 KB | yes |
| [coatue](out/coatue.mp4) | 1 | headline 1 | rebuild | 0.088 / 0.0% | 1 / 2 | 108 KB | yes |
| [cognition](out/cognition.mp4) | 8 | illustration 3, stroke 2, label 1, panel 1, headline 1 | rebuild | 0.272 / 0.0% | 1 / 1 | 501 KB | yes |
| [cohere](out/cohere.mp4) | 18 | label 7, stroke 6, icon 2, logo 1, headline 1, illustration 1 | living | 0.399 / 0.0% | 0 / 2 | 1740 KB | yes |
| [conviction](out/conviction.mp4) | 1 | shape 1 | rebuild | 0.195 / 0.0% | 114 / 131 | 803 KB | yes |
| [cursor](out/cursor.mp4) | 2 | logo 1, headline 1 | rebuild | 0.064 / 0.0% | 39 / 38 | 122 KB | yes |
| [deno](out/deno.mp4) | 9 | headline 7, text 1, illustration 1 | rebuild | 0.191 / 0.0% | 0 / 1 | 255 KB | yes |
| [discord](out/discord.mp4) | 18 | icon 11, label 2, text 2, headline 1, logo 1, illustration 1 | rebuild | 0.273 / 0.0% | 0 / 3 | 678 KB | yes |
| [dropbox](out/dropbox.mp4) | 2 | shape 2 | rebuild | 0.039 / 0.0% | 0 / 2 | 173 KB | yes |
| [dub](out/dub.mp4) | 18 | icon 4, label 4, stroke 3, headline 2, illustration 2, shape 1, avatar 1, pill 1 | rebuild | 0.327 / 0.0% | 0 / 2 | 285 KB | yes |
| [duolingo](out/duolingo.mp4) | 8 | shape 5, illustration 1, icon 1, avatar 1 | rebuild | 0.092 / 0.0% | 0 / 1 | 162 KB | yes |
| [elevenlabs](out/elevenlabs.mp4) | 16 | label 15, headline 1 | rebuild | 0.211 / 0.0% | 0 / 0 | 336 KB | yes |
| [excalidraw](out/excalidraw.mp4) | 18 | icon 8, label 5, shape 2, logo 1, headline 1, text 1 | rebuild | 0.174 / 0.0% | 0 / 1 | 285 KB | yes |
| [figma](out/figma.mp4) | 7 | headline 3, icon 2, stroke 1, illustration 1 | rebuild | 0.298 / 0.0% | 1 / 2 | 425 KB | yes |
| [fly](out/fly.mp4) | 9 | icon 4, headline 3, avatar 1, text 1 | rebuild | 0.372 / 0.0% | 0 / 3 | 714 KB | yes |
| [framer](out/framer.mp4) | 16 | icon 5, stroke 4, illustration 3, shape 3, headline 1 | living | 0.497 / 0.0% | 0 / 2 | 893 KB | yes |
| [generalcatalyst](out/generalcatalyst.mp4) | 1 | shape 1 | living | 0.233 / 0.0% | 0 / 1 | 594 KB | yes |
| [ghost](out/ghost.mp4) | 18 | icon 14, illustration 2, avatar 1, shape 1 | rebuild | 0.24 / 0.0% | 1 / 1 | 385 KB | yes |
| [github](out/github.mp4) | 10 | shape 4, illustration 3, headline 2, icon 1 | rebuild | 0.236 / 0.0% | 1 / 2 | 237 KB | yes |
| [glean](out/glean.mp4) | 18 | label 8, shape 5, icon 2, illustration 1, stroke 1, text 1 | rebuild | 0.152 / 0.0% | 0 / 1 | 388 KB | yes |
| [granola](out/granola.mp4) | 8 | icon 4, headline 4 | rebuild | 0.504 / 0.0% | 0 / 2 | 747 KB | yes |
| [greylock](out/greylock.mp4) | 18 | shape 8, label 5, headline 3, text 2 | rebuild | 0.186 / 0.0% | 1 / 1 | 263 KB | yes |
| [groq](out/groq.mp4) | 5 | headline 4, icon 1 | living | 0.133 / 0.0% | 0 / 2 | 247 KB | yes |
| [gumroad](out/gumroad.mp4) | 6 | illustration 5, headline 1 | rebuild | 0.413 / 0.0% | 0 / 2 | 646 KB | yes |
| [gv](out/gv.mp4) | 1 | shape 1 | rebuild | 0.049 / 0.0% | 58 / 62 | 344 KB | yes |
| [harvey](out/harvey.mp4) | 1 | headline 1 | rebuild | 0.053 / 0.0% | 1 / 3 | 75 KB | yes |
| [huggingface](out/huggingface.mp4) | 3 | headline 2, illustration 1 | rebuild | 0.165 / 0.0% | 1 / 3 | 345 KB | yes |
| [ibm](out/ibm.mp4) | 18 | pill 17, headline 1 | rebuild | 0.164 / 0.0% | 0 / 1 | 142 KB | yes |
| [ideogram](out/ideogram.mp4) | 9 | shape 6, label 2, headline 1 | living | 0.39 / 0.0% | 0 / 2 | 1271 KB | yes |
| [indexventures](out/indexventures.mp4) | 6 | pill 5, illustration 1 | rebuild | 0.064 / 0.0% | 1 / 1 | 53 KB | yes |
| [insightpartners](out/insightpartners.mp4) | 2 | headline 1, text 1 | rebuild | 0.045 / 0.0% | 0 / 1 | 89 KB | yes |
| [intercom](out/intercom.mp4) | 13 | headline 7, icon 2, panel 1, illustration 1, photo 1, text 1 | rebuild | 0.416 / 0.0% | 38 / 37 | 494 KB | yes |
| [kleinerperkins](out/kleinerperkins.mp4) | 3 | headline 2, panel 1 | rebuild | 0.145 / 0.0% | 1 / 4 | 156 KB | yes |
| [linear](out/linear.mp4) | 2 | logo 1, headline 1 | rebuild | 0.078 / 0.0% | 47 / 47 | 233 KB | yes |
| [loom](out/loom.mp4) | 18 | icon 7, illustration 4, headline 3, stroke 2, label 1, shape 1 | rebuild | 0.265 / 0.0% | 1 / 3 | 416 KB | yes |
| [lovable](out/lovable.mp4) | 2 | illustration 1, avatar 1 | living | 0.313 / 0.0% | 1 / 2 | 632 KB | yes |
| [lsvp](out/lsvp.mp4) | 10 | stroke 7, headline 2, icon 1 | rebuild | 0.07 / 0.0% | 0 / 1 | 83 KB | yes |
| [mailchimp](out/mailchimp.mp4) | 3 | headline 2, logo 1 | rebuild | 0.133 / 0.0% | 2 / 4 | 235 KB | yes |
| [mintlify](out/mintlify.mp4) | 5 | stroke 3, icon 2 | rebuild | 0.077 / 0.0% | 0 / 1 | 41 KB | yes |
| [miro](out/miro.mp4) | 1 | shape 1 | rebuild | 0.048 / 0.0% | 1 / 2 | 212 KB | yes |
| [mistral](out/mistral.mp4) | 6 | stroke 2, logo 1, text 1, headline 1, illustration 1 | rebuild | 0.169 / 0.0% | 1 / 2 | 306 KB | yes |
| [mobbin](out/mobbin.mp4) | 18 | icon 9, headline 4, illustration 2, shape 1, pill 1, avatar 1 | rebuild | 0.316 / 0.0% | 0 / 2 | 479 KB | yes |
| [netlify](out/netlify.mp4) | 17 | icon 7, avatar 5, headline 2, text 1, illustration 1, shape 1 | rebuild | 0.273 / 0.0% | 1 / 3 | 525 KB | yes |
| [nextjs](out/nextjs.mp4) | 2 | headline 1, icon 1 | rebuild | 0.049 / 0.0% | 46 / 46 | 85 KB | yes |
| [nfx](out/nfx.mp4) | 1 | shape 1 | rebuild | 0.084 / 0.0% | 64 / 63 | 642 KB | yes |
| [notion](out/notion.mp4) | 16 | stroke 3, icon 3, headline 2, illustration 2, shape 2, label 2, logo 1, text 1 | rebuild | 0.376 / 0.0% | 0 / 1 | 410 KB | yes |
| [obsidian](out/obsidian.mp4) | 9 | label 3, illustration 2, text 2, stroke 1, headline 1 | rebuild | 0.159 / 0.0% | 1 / 1 | 188 KB | yes |
| [openai](out/openai.mp4) | 17 | icon 8, shape 5, headline 2, illustration 2 | rebuild | 0.452 / 0.0% | 1 / 2 | 671 KB | yes |
| [perplexity](out/perplexity.mp4) | 3 | icon 1, headline 1, illustration 1 | rebuild | 0.119 / 0.0% | 1 / 2 | 246 KB | yes |
| [pika](out/pika.mp4) | 6 | shape 4, icon 1, headline 1 | living | 0.256 / 0.0% | 0 / 1 | 665 KB | yes |
| [pinterest](out/pinterest.mp4) | 18 | illustration 9, shape 3, icon 3, label 2, stroke 1 | rebuild | 0.432 / 0.0% | 0 / 2 | 947 KB | yes |
| [pitch](out/pitch.mp4) | 2 | logo 1, headline 1 | rebuild | 0.07 / 0.0% | 40 / 39 | 342 KB | yes |
| [planetscale](out/planetscale.mp4) | 18 | text 10, label 6, headline 1, illustration 1 | rebuild | 0.374 / 0.0% | 0 / 2 | 355 KB | yes |
| [posthog](out/posthog.mp4) | 9 | icon 3, illustration 2, headline 2, stroke 1, pill 1 | rebuild | 0.32 / 0.0% | 0 / 2 | 593 KB | yes |
| [railway](out/railway.mp4) | 18 | icon 6, illustration 4, headline 3, label 2, logo 1, text 1, stroke 1 | rebuild | 0.239 / 0.0% | 1 / 2 | 357 KB | yes |
| [raycast](out/raycast.mp4) | 18 | icon 10, logo 2, headline 2, illustration 2, text 1, label 1 | rebuild | 0.284 / 0.0% | 0 / 1 | 250 KB | yes |
| [replit](out/replit.mp4) | 18 | label 9, illustration 3, shape 2, icon 2, headline 1, text 1 | rebuild | 0.236 / 0.0% | 1 / 2 | 547 KB | yes |
| [resend](out/resend.mp4) | 18 | label 7, illustration 5, shape 3, icon 2, pill 1 | rebuild | 0.197 / 0.0% | 0 / 2 | 320 KB | yes |
| [retool](out/retool.mp4) | 6 | label 4, text 1, shape 1 | living | 0.377 / 0.0% | 0 / 2 | 682 KB | yes |
| [rive](out/rive.mp4) | 18 | stroke 7, icon 4, headline 3, label 2, logo 1, illustration 1 | rebuild | 0.323 / 0.0% | 1 / 1 | 179 KB | yes |
| [runwayml](out/runwayml.mp4) | 2 | headline 1, text 1 | rebuild | 0.148 / 0.0% | 0 / 2 | 322 KB | yes |
| [salesforce](out/salesforce.mp4) | 5 | icon 4, shape 1 | rebuild | 0.048 / 0.0% | 1 / 2 | 183 KB | yes |
| [scale](out/scale.mp4) | 4 | text 2, logo 1, headline 1 | rebuild | 0.178 / 0.0% | 0 / 1 | 154 KB | yes |
| [sentry](out/sentry.mp4) | 18 | illustration 7, label 3, icon 3, stroke 3, shape 1, pill 1 | living | 0.259 / 0.0% | 1 / 2 | 544 KB | yes |
| [sequoiacap](out/sequoiacap.mp4) | 6 | stroke 2, shape 2, illustration 1, panel 1 | living | 0.641 / 0.0% | 1 / 2 | 1572 KB | yes |
| [shopify](out/shopify.mp4) | 6 | icon 4, headline 1, stroke 1 | rebuild | 0.275 / 0.0% | 0 / 11 | 453 KB | yes |
| [slack](out/slack.mp4) | 3 | logo 1, headline 1, illustration 1 | rebuild | 0.084 / 0.0% | 1 / 2 | 140 KB | yes |
| [spline](out/spline.mp4) | 4 | label 2, illustration 1, stroke 1 | rebuild | 0.07 / 0.0% | 0 / 1 | 98 KB | yes |
| [spotify](out/spotify.mp4) | 18 | illustration 5, icon 5, label 3, photo 3, stroke 1, shape 1 | rebuild | 0.398 / 0.0% | 27 / 26 | 883 KB | yes |
| [stability](out/stability.mp4) | 6 | label 1, text 1, shape 1, pill 1, headline 1, icon 1 | living | 0.416 / 0.0% | 0 / 2 | 1026 KB | yes |
| [stripe](out/stripe.mp4) | 3 | shape 2, headline 1 | rebuild | 0.24 / 0.0% | 0 / 1 | 548 KB | yes |
| [suno](out/suno.mp4) | 2 | headline 2 | rebuild | 0.402 / 0.0% | 0 / 2 | 970 KB | yes |
| [supabase](out/supabase.mp4) | 3 | headline 2, illustration 1 | rebuild | 0.142 / 0.0% | 1 / 3 | 226 KB | yes |
| [superhuman](out/superhuman.mp4) | 17 | label 8, illustration 3, icon 3, logo 2, avatar 1 | rebuild | 0.378 / 0.0% | 0 / 2 | 722 KB | yes |
| [tailwindcss](out/tailwindcss.mp4) | 18 | icon 11, shape 3, illustration 2, label 1, headline 1 | rebuild | 0.268 / 0.0% | 1 / 1 | 470 KB | yes |
| [thrivecap](out/thrivecap.mp4) | 1 | stroke 1 | rebuild | 0.026 / 0.0% | 1 / 1 | 51 KB | yes |
| [tldraw](out/tldraw.mp4) | 6 | shape 5, panel 1 | rebuild | 0.109 / 0.0% | 0 / 2 | 120 KB | yes |
| [together](out/together.mp4) | 7 | shape 2, label 2, headline 2, illustration 1 | rebuild | 0.151 / 0.0% | 0 / 1 | 199 KB | yes |
| [typeform](out/typeform.mp4) | 1 | headline 1 | rebuild | 0.052 / 0.0% | 1 / 3 | 78 KB | yes |
| [v0](out/v0.mp4) | 2 | headline 1, illustration 1 | rebuild | 0.116 / 0.0% | 174 / 173 | 421 KB | yes |
| [vercel](out/vercel.mp4) | 1 | illustration 1 | rebuild | 0.046 / 0.0% | 1 / 1 | 174 KB | yes |
| [vite](out/vite.mp4) | 13 | label 9, illustration 1, logo 1, text 1, stroke 1 | living | 0.526 / 0.0% | 0 / 2 | 1245 KB | yes |
| [warp](out/warp.mp4) | 7 | icon 3, shape 2, illustration 1, panel 1 | rebuild | 0.222 / 0.0% | 1 / 1 | 283 KB | yes |
| [webflow](out/webflow.mp4) | 18 | illustration 6, label 4, icon 2, stroke 2, text 2, logo 1, headline 1 | rebuild | 0.354 / 0.0% | 1 / 3 | 926 KB | yes |
| [windsurf](out/windsurf.mp4) | 18 | illustration 9, label 3, icon 3, shape 2, headline 1 | living | 0.467 / 0.0% | 0 / 3 | 1201 KB | yes |
| [x](out/x.mp4) | 1 | shape 1 | rebuild | 0.027 / 0.0% | 52 / 53 | 205 KB | yes |
| [ycombinator](out/ycombinator.mp4) | 18 | avatar 15, headline 2, illustration 1 | rebuild | 0.354 / 0.0% | 0 / 2 | 414 KB | yes |
| [zapier](out/zapier.mp4) | 8 | icon 4, headline 2, illustration 1, text 1 | living | 0.313 / 0.0% | 0 / 2 | 339 KB | yes |
| [zed](out/zed.mp4) | 18 | illustration 9, stroke 4, label 3, icon 1, headline 1 | rebuild | 0.379 / 0.0% | 0 / 3 | 836 KB | yes |
<!-- /results -->

## With the reading step

The table above is the skill with no help: it reads every card on its own. The skill's workflow starts with a reading step, where the agent looks at the card, says what it shows and writes a short plan (`eval/scenes/<name>.json`): which parts are whole units and what each one is, for example a window, a button, a scribble, a list, a ring of avatars or a row of logos. Cards whose automatic reading missed what they show are run again with their plan, as `out/<name>-read.mp4`:

<!-- read -->
**7 of 7 cards pass.**

| Card | Layers | Kinds | Style | Frame 0 (mean / local) | Seam / step | MP4 | Pass |
|---|---|---|---|---|---|---|---|
| [a16z-read](out/a16z-read.mp4) | 4 | text 2, headline 1, photo 1 | living | 0.53 / 0.0% | 1 / 3 | 1162 KB | yes |
| [cloudflare-read](out/cloudflare-read.mp4) | 2 | logo 1, pill 1 | living | 0.358 / 0.0% | 0 / 2 | 1119 KB | yes |
| [deno-read](out/deno-read.mp4) | 11 | text 10, headline 1 | rebuild | 0.478 / 0.011% | 0 / 0 | 352 KB | yes |
| [ghost-read](out/ghost-read.mp4) | 0 |  | rebuild | 0.236 / 0.0% | 239 / 243 | 796 KB | yes |
| [openai-read](out/openai-read.mp4) | 17 | icon 5, shape 4, illustration 3, stroke 3, headline 2 | rebuild | 0.455 / 0.0% | 0 / 2 | 676 KB | yes |
| [webflow-read](out/webflow-read.mp4) | 9 | panel 7, logo 1, label 1 | rebuild | 0.368 / 0.0% | 0 / 2 | 1026 KB | yes |
| [ycombinator-read](out/ycombinator-read.mp4) | 3 | headline 2, icon 1 | rebuild | 0.353 / 0.0% | 237 / 234 | 730 KB | yes |
<!-- /read -->
