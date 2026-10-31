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
| [a16z](out/a16z.mp4) | 3 | text 2, headline 1 | living | 0.523 / 0.0% | 0 / 2 | 1258 KB | yes |
| [accel](out/accel.mp4) | 3 | illustration 3 | rebuild | 0.163 / 0.0% | 1 / 4 | 315 KB | yes |
| [amd](out/amd.mp4) | 13 | label 10, stroke 2, text 1 | living | 0.412 / 0.0% | 0 / 2 | 1107 KB | yes |
| [anthropic](out/anthropic.mp4) | 1 | headline 1 | rebuild | 0.07 / 0.0% | 1 / 3 | 95 KB | yes |
| [apple](out/apple.mp4) | 1 | shape 1 | rebuild | 0.007 / 0.0% | 0 / 1 | 40 KB | yes |
| [arc](out/arc.mp4) | 2 | illustration 1, headline 1 | rebuild | 0.131 / 0.0% | 53 / 52 | 175 KB | yes |
| [astro](out/astro.mp4) | 12 | illustration 8, headline 2, text 1, pill 1 | rebuild | 0.397 / 0.0% | 0 / 2 | 718 KB | yes |
| [bolt](out/bolt.mp4) | 1 | headline 1 | rebuild | 0.17 / 0.0% | 0 / 1 | 254 KB | yes |
| [bun](out/bun.mp4) | 7 | label 3, avatar 1, shape 1, illustration 1, headline 1 | rebuild | 0.325 / 0.0% | 0 / 1 | 293 KB | yes |
| [bvp](out/bvp.mp4) | 1 | icon 1 | living | 0.432 / 0.0% | 0 / 1 | 1126 KB | yes |
| [cal](out/cal.mp4) | 14 | label 5, icon 3, shape 3, text 1, headline 1, illustration 1 | living | 0.272 / 0.0% | 1 / 1 | 77 KB | yes |
| [calendly](out/calendly.mp4) | 13 | label 4, illustration 4, icon 3, logo 1, headline 1 | rebuild | 0.28 / 0.0% | 1 / 2 | 564 KB | yes |
| [canva](out/canva.mp4) | 9 | illustration 6, icon 2, stroke 1 | rebuild | 0.273 / 0.0% | 0 / 2 | 585 KB | yes |
| [clerk](out/clerk.mp4) | 6 | stroke 2, headline 2, logo 1, text 1 | living | 0.238 / 0.0% | 0 / 0 | 56 KB | yes |
| [cloudflare](out/cloudflare.mp4) | 0 |  | living | 0.358 / 0.0% | 0 / 1 | 1085 KB | yes |
| [coatue](out/coatue.mp4) | 1 | headline 1 | rebuild | 0.088 / 0.0% | 1 / 2 | 105 KB | yes |
| [cognition](out/cognition.mp4) | 7 | illustration 3, stroke 1, label 1, panel 1, headline 1 | rebuild | 0.272 / 0.0% | 1 / 1 | 490 KB | yes |
| [cohere](out/cohere.mp4) | 18 | stroke 8, label 4, icon 3, headline 1, logo 1, illustration 1 | living | 0.399 / 0.0% | 0 / 2 | 1757 KB | yes |
| [conviction](out/conviction.mp4) | 1 | shape 1 | rebuild | 0.195 / 0.0% | 114 / 131 | 427 KB | yes |
| [cursor](out/cursor.mp4) | 2 | logo 1, headline 1 | rebuild | 0.064 / 0.0% | 38 / 38 | 78 KB | yes |
| [deno](out/deno.mp4) | 9 | headline 7, text 1, illustration 1 | rebuild | 0.191 / 0.0% | 0 / 1 | 231 KB | yes |
| [discord](out/discord.mp4) | 18 | icon 10, label 2, headline 1, shape 1, logo 1, text 1, stroke 1, illustration 1 | living | 0.274 / 0.0% | 0 / 2 | 838 KB | yes |
| [dropbox](out/dropbox.mp4) | 2 | shape 2 | rebuild | 0.038 / 0.0% | 1 / 2 | 121 KB | yes |
| [dub](out/dub.mp4) | 18 | icon 10, headline 2, illustration 2, label 2, stroke 2 | living | 0.325 / 0.0% | 0 / 0 | 82 KB | yes |
| [duolingo](out/duolingo.mp4) | 8 | shape 5, illustration 1, icon 1, avatar 1 | rebuild | 0.091 / 0.0% | 0 / 1 | 151 KB | yes |
| [elevenlabs](out/elevenlabs.mp4) | 7 | label 6, headline 1 | living | 0.21 / 0.0% | 0 / 0 | 262 KB | yes |
| [excalidraw](out/excalidraw.mp4) | 16 | label 6, icon 5, shape 2, logo 1, headline 1, text 1 | rebuild | 0.174 / 0.0% | 0 / 1 | 257 KB | yes |
| [figma](out/figma.mp4) | 7 | headline 3, icon 2, stroke 1, illustration 1 | rebuild | 0.298 / 0.0% | 1 / 2 | 400 KB | yes |
| [fly](out/fly.mp4) | 9 | icon 4, headline 3, avatar 1, text 1 | rebuild | 0.372 / 0.0% | 0 / 3 | 703 KB | yes |
| [framer](out/framer.mp4) | 11 | stroke 3, icon 3, illustration 3, headline 1, shape 1 | living | 0.497 / 0.0% | 0 / 3 | 887 KB | yes |
| [generalcatalyst](out/generalcatalyst.mp4) | 0 |  | living | 0.233 / 0.0% | 0 / 1 | 583 KB | yes |
| [ghost](out/ghost.mp4) | 18 | icon 14, illustration 2, avatar 1, shape 1 | rebuild | 0.24 / 0.0% | 0 / 1 | 385 KB | yes |
| [github](out/github.mp4) | 10 | shape 4, illustration 3, headline 2, icon 1 | rebuild | 0.236 / 0.0% | 1 / 2 | 227 KB | yes |
| [glean](out/glean.mp4) | 11 | label 6, icon 2, shape 1, illustration 1, text 1 | living | 0.151 / 0.0% | 0 / 1 | 356 KB | yes |
| [granola](out/granola.mp4) | 8 | icon 4, headline 4 | rebuild | 0.504 / 0.0% | 0 / 2 | 773 KB | yes |
| [greylock](out/greylock.mp4) | 11 | label 5, headline 3, text 2, shape 1 | rebuild | 0.184 / 0.0% | 0 / 1 | 183 KB | yes |
| [groq](out/groq.mp4) | 4 | headline 3, icon 1 | living | 0.133 / 0.0% | 0 / 2 | 249 KB | yes |
| [gumroad](out/gumroad.mp4) | 6 | illustration 5, headline 1 | rebuild | 0.413 / 0.0% | 0 / 2 | 643 KB | yes |
| [gv](out/gv.mp4) | 1 | shape 1 | rebuild | 0.049 / 0.0% | 58 / 61 | 155 KB | yes |
| [harvey](out/harvey.mp4) | 1 | headline 1 | rebuild | 0.053 / 0.0% | 1 / 3 | 72 KB | yes |
| [huggingface](out/huggingface.mp4) | 3 | headline 2, illustration 1 | rebuild | 0.165 / 0.0% | 1 / 3 | 343 KB | yes |
| [ibm](out/ibm.mp4) | 2 | illustration 1, headline 1 | rebuild | 0.165 / 0.0% | 2 / 4 | 214 KB | yes |
| [ideogram](out/ideogram.mp4) | 5 | shape 2, label 2, headline 1 | living | 0.391 / 0.0% | 0 / 1 | 1260 KB | yes |
| [indexventures](out/indexventures.mp4) | 1 | illustration 1 | living | 0.064 / 0.0% | 1 / 0 | 14 KB | yes |
| [insightpartners](out/insightpartners.mp4) | 2 | headline 1, text 1 | rebuild | 0.045 / 0.0% | 0 / 1 | 89 KB | yes |
| [intercom](out/intercom.mp4) | 9 | headline 2, text 2, icon 2, panel 1, illustration 1, photo 1 | rebuild | 0.416 / 0.0% | 30 / 29 | 448 KB | yes |
| [kleinerperkins](out/kleinerperkins.mp4) | 3 | headline 2, panel 1 | rebuild | 0.145 / 0.0% | 1 / 4 | 147 KB | yes |
| [linear](out/linear.mp4) | 1 | headline 1 | rebuild | 0.078 / 0.0% | 0 / 2 | 189 KB | yes |
| [loom](out/loom.mp4) | 17 | icon 7, illustration 4, headline 3, stroke 1, label 1, shape 1 | rebuild | 0.263 / 0.0% | 1 / 3 | 417 KB | yes |
| [lovable](out/lovable.mp4) | 1 | illustration 1 | living | 0.313 / 0.0% | 0 / 2 | 636 KB | yes |
| [lsvp](out/lsvp.mp4) | 3 | headline 2, icon 1 | living | 0.07 / 0.0% | 0 / 0 | 26 KB | yes |
| [mailchimp](out/mailchimp.mp4) | 3 | headline 2, logo 1 | rebuild | 0.133 / 0.0% | 2 / 4 | 226 KB | yes |
| [mintlify](out/mintlify.mp4) | 1 | icon 1 | rebuild | 0.077 / 0.0% | 1 / 2 | 129 KB | yes |
| [miro](out/miro.mp4) | 1 | shape 1 | rebuild | 0.048 / 0.0% | 1 / 2 | 126 KB | yes |
| [mistral](out/mistral.mp4) | 6 | stroke 2, logo 1, text 1, headline 1, illustration 1 | rebuild | 0.169 / 0.0% | 1 / 2 | 293 KB | yes |
| [mobbin](out/mobbin.mp4) | 16 | icon 7, headline 4, illustration 2, shape 1, pill 1, avatar 1 | rebuild | 0.316 / 0.0% | 0 / 2 | 426 KB | yes |
| [netlify](out/netlify.mp4) | 16 | icon 6, avatar 5, headline 2, text 1, illustration 1, shape 1 | rebuild | 0.272 / 0.0% | 1 / 3 | 518 KB | yes |
| [nextjs](out/nextjs.mp4) | 2 | headline 1, icon 1 | rebuild | 0.049 / 0.0% | 46 / 45 | 45 KB | yes |
| [nfx](out/nfx.mp4) | 1 | shape 1 | rebuild | 0.085 / 0.0% | 64 / 63 | 428 KB | yes |
| [notion](out/notion.mp4) | 10 | headline 2, illustration 2, stroke 2, label 2, text 1, icon 1 | rebuild | 0.376 / 0.0% | 0 / 3 | 414 KB | yes |
| [obsidian](out/obsidian.mp4) | 5 | label 2, illustration 1, headline 1, text 1 | rebuild | 0.158 / 0.0% | 1 / 1 | 157 KB | yes |
| [openai](out/openai.mp4) | 15 | icon 7, shape 4, headline 2, illustration 2 | rebuild | 0.45 / 0.0% | 1 / 2 | 662 KB | yes |
| [perplexity](out/perplexity.mp4) | 3 | icon 1, headline 1, illustration 1 | rebuild | 0.119 / 0.0% | 1 / 2 | 244 KB | yes |
| [pika](out/pika.mp4) | 1 | headline 1 | living | 0.256 / 0.0% | 0 / 1 | 646 KB | yes |
| [pinterest](out/pinterest.mp4) | 12 | illustration 8, label 2, icon 1, shape 1 | rebuild | 0.43 / 0.0% | 1 / 2 | 939 KB | yes |
| [pitch](out/pitch.mp4) | 1 | headline 1 | rebuild | 0.07 / 0.0% | 0 / 2 | 260 KB | yes |
| [planetscale](out/planetscale.mp4) | 18 | text 10, label 6, headline 1, illustration 1 | rebuild | 0.374 / 0.0% | 0 / 2 | 372 KB | yes |
| [posthog](out/posthog.mp4) | 8 | icon 3, headline 2, stroke 1, illustration 1, pill 1 | rebuild | 0.32 / 0.0% | 0 / 2 | 574 KB | yes |
| [railway](out/railway.mp4) | 17 | icon 7, label 4, headline 3, text 1, logo 1, illustration 1 | rebuild | 0.241 / 0.0% | 1 / 2 | 346 KB | yes |
| [raycast](out/raycast.mp4) | 18 | icon 12, illustration 2, logo 1, text 1, headline 1, label 1 | rebuild | 0.284 / 0.0% | 0 / 1 | 270 KB | yes |
| [replit](out/replit.mp4) | 17 | label 9, illustration 3, icon 2, shape 1, headline 1, text 1 | rebuild | 0.236 / 0.0% | 1 / 2 | 524 KB | yes |
| [resend](out/resend.mp4) | 10 | label 5, illustration 4, shape 1 | living | 0.197 / 0.0% | 0 / 0 | 58 KB | yes |
| [retool](out/retool.mp4) | 5 | label 4, text 1 | living | 0.377 / 0.0% | 0 / 2 | 681 KB | yes |
| [rive](out/rive.mp4) | 18 | stroke 7, icon 4, headline 3, label 2, logo 1, illustration 1 | rebuild | 0.323 / 0.0% | 0 / 0 | 206 KB | yes |
| [runwayml](out/runwayml.mp4) | 2 | headline 1, text 1 | rebuild | 0.148 / 0.0% | 0 / 2 | 322 KB | yes |
| [salesforce](out/salesforce.mp4) | 1 | logo 1 | rebuild | 0.048 / 0.0% | 44 / 43 | 159 KB | yes |
| [scale](out/scale.mp4) | 3 | text 2, headline 1 | rebuild | 0.178 / 0.0% | 1 / 3 | 310 KB | yes |
| [sentry](out/sentry.mp4) | 6 | label 3, icon 1, logo 1, stroke 1 | living | 0.26 / 0.0% | 1 / 2 | 610 KB | yes |
| [sequoiacap](out/sequoiacap.mp4) | 3 | stroke 1, illustration 1, panel 1 | living | 0.641 / 0.0% | 1 / 3 | 1449 KB | yes |
| [shopify](out/shopify.mp4) | 5 | icon 4, headline 1 | rebuild | 0.275 / 0.0% | 0 / 11 | 441 KB | yes |
| [slack](out/slack.mp4) | 3 | logo 1, headline 1, illustration 1 | rebuild | 0.084 / 0.0% | 1 / 2 | 139 KB | yes |
| [spline](out/spline.mp4) | 4 | label 2, illustration 1, stroke 1 | rebuild | 0.071 / 0.0% | 0 / 1 | 94 KB | yes |
| [spotify](out/spotify.mp4) | 11 | icon 6, illustration 2, stroke 1, label 1, shape 1 | living | 0.398 / 0.0% | 1 / 2 | 1077 KB | yes |
| [stability](out/stability.mp4) | 4 | label 1, text 1, pill 1, headline 1 | living | 0.417 / 0.0% | 0 / 2 | 1019 KB | yes |
| [stripe](out/stripe.mp4) | 1 | headline 1 | rebuild | 0.24 / 0.0% | 0 / 1 | 528 KB | yes |
| [suno](out/suno.mp4) | 2 | headline 2 | rebuild | 0.402 / 0.0% | 0 / 1 | 967 KB | yes |
| [supabase](out/supabase.mp4) | 3 | headline 2, illustration 1 | rebuild | 0.142 / 0.0% | 1 / 3 | 234 KB | yes |
| [superhuman](out/superhuman.mp4) | 14 | label 8, icon 3, illustration 2, avatar 1 | rebuild | 0.378 / 0.0% | 0 / 2 | 746 KB | yes |
| [tailwindcss](out/tailwindcss.mp4) | 13 | icon 7, label 1, stroke 1, illustration 1, logo 1, headline 1, shape 1 | living | 0.269 / 0.0% | 0 / 0 | 164 KB | yes |
| [thrivecap](out/thrivecap.mp4) | 1 | stroke 1 | rebuild | 0.026 / 0.0% | 1 / 1 | 51 KB | yes |
| [tldraw](out/tldraw.mp4) | 2 | panel 1, logo 1 | rebuild | 0.108 / 0.0% | 0 / 1 | 172 KB | yes |
| [together](out/together.mp4) | 4 | headline 2, illustration 1, label 1 | rebuild | 0.151 / 0.0% | 0 / 1 | 210 KB | yes |
| [typeform](out/typeform.mp4) | 1 | headline 1 | rebuild | 0.052 / 0.0% | 1 / 3 | 80 KB | yes |
| [v0](out/v0.mp4) | 2 | headline 1, illustration 1 | rebuild | 0.116 / 0.0% | 174 / 173 | 253 KB | yes |
| [vercel](out/vercel.mp4) | 1 | illustration 1 | rebuild | 0.046 / 0.0% | 1 / 1 | 173 KB | yes |
| [vite](out/vite.mp4) | 11 | label 8, illustration 1, text 1, stroke 1 | living | 0.526 / 0.0% | 0 / 2 | 1213 KB | yes |
| [warp](out/warp.mp4) | 7 | icon 3, shape 2, illustration 1, panel 1 | rebuild | 0.22 / 0.0% | 0 / 1 | 268 KB | yes |
| [webflow](out/webflow.mp4) | 18 | icon 5, illustration 4, label 3, stroke 3, logo 1, headline 1, text 1 | living | 0.355 / 0.0% | 1 / 2 | 1241 KB | yes |
| [windsurf](out/windsurf.mp4) | 18 | illustration 9, icon 3, label 3, shape 2, headline 1 | living | 0.467 / 0.0% | 0 / 2 | 1622 KB | yes |
| [x](out/x.mp4) | 1 | shape 1 | rebuild | 0.027 / 0.0% | 52 / 53 | 124 KB | yes |
| [ycombinator](out/ycombinator.mp4) | 18 | avatar 15, headline 2, illustration 1 | rebuild | 0.354 / 0.0% | 0 / 2 | 394 KB | yes |
| [zapier](out/zapier.mp4) | 3 | headline 2, text 1 | living | 0.313 / 0.0% | 0 / 2 | 337 KB | yes |
| [zed](out/zed.mp4) | 16 | illustration 6, stroke 4, icon 2, label 2, headline 1, logo 1 | living | 0.381 / 0.0% | 1 / 2 | 1286 KB | yes |
<!-- /results -->

## With the reading step

The table above is the skill with no help: it reads every card on its own. The skill's workflow starts with a reading step, where the agent looks at the card, says what it shows and writes a short plan (`eval/scenes/<name>.json`): which parts are whole units and what each one is, for example a window, a button, a scribble, a list, a ring of avatars or a row of logos. Cards whose automatic reading missed what they show are run again with their plan, as `out/<name>-read.mp4`:

<!-- read -->
**11 of 11 cards pass.**

| Card | Layers | Kinds | Style | Frame 0 (mean / local) | Seam / step | MP4 | Pass |
|---|---|---|---|---|---|---|---|
| [a16z-read](out/a16z-read.mp4) | 4 | text 2, headline 1, photo 1 | living | 0.53 / 0.0% | 1 / 3 | 1161 KB | yes |
| [cloudflare-read](out/cloudflare-read.mp4) | 2 | logo 1, pill 1 | living | 0.358 / 0.0% | 1 / 2 | 992 KB | yes |
| [deno-read](out/deno-read.mp4) | 11 | text 10, headline 1 | rebuild | 0.478 / 0.011% | 0 / 0 | 351 KB | yes |
| [fly-read](out/fly-read.mp4) | 10 | icon 4, headline 3, avatar 1, text 1, pill 1 | rebuild | 0.373 / 0.0% | 0 / 3 | 723 KB | yes |
| [ghost-read](out/ghost-read.mp4) | 0 |  | rebuild | 0.236 / 0.0% | 240 / 243 | 736 KB | yes |
| [lovable-read](out/lovable-read.mp4) | 1 | illustration 1 | living | 0.313 / 0.0% | 0 / 2 | 706 KB | yes |
| [netlify-read](out/netlify-read.mp4) | 16 | icon 8, avatar 3, headline 2, text 1, illustration 1, shape 1 | rebuild | 0.272 / 0.0% | 1 / 3 | 521 KB | yes |
| [openai-read](out/openai-read.mp4) | 18 | illustration 7, shape 3, icon 3, stroke 3, headline 2 | rebuild | 0.456 / 0.0% | 158 / 172 | 731 KB | yes |
| [warp-read](out/warp-read.mp4) | 14 | illustration 10, icon 2, shape 2 | rebuild | 0.221 / 0.0% | 157 / 173 | 465 KB | yes |
| [webflow-read](out/webflow-read.mp4) | 8 | panel 7, logo 1 | living | 0.368 / 0.0% | 1 / 2 | 893 KB | yes |
| [ycombinator-read](out/ycombinator-read.mp4) | 3 | headline 2, icon 1 | rebuild | 0.353 / 0.0% | 237 / 234 | 744 KB | yes |
<!-- /read -->
