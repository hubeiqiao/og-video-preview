#!/usr/bin/env python3
"""The README's before-and-after GIFs: the approved og:image on the left, the og:video the skill made on the right.

  social/hero.gif           this project's own og:video (a still in, a video out), for the top of the README
  social/showcase.gif       nine famous sites' og:videos playing at once, right under it
  social/pairs/<name>.gif   one card per GIF, for Examples
  social/eval-pairs.gif     six eval cards in one grid, for Evaluation

The layout (labels, stills, arrows) is captured once from a small HTML page through scripts/render_frames.py; ffmpeg
then plays each og:video into its card's slot (a headless browser does not repaint a seeked <video> reliably).
Re-run after the eval or the examples change.

Usage: python3 tools/readme_gifs.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, ".cache", "readme-gifs")
PY = sys.executable

def best(n):  # a card the reading step was run on shows that version
    return f"eval/out/{n}-read.mp4" if os.path.exists(os.path.join(ROOT, "eval", "out", f"{n}-read.mp4")) else f"eval/out/{n}.mp4"


EXAMPLES = [(n, f"eval/out/{n}.jpg", best(n), d) for n, d in [  # name, still, video, caption
    ("ycombinator", "ycombinator.com"), ("x", "x.ai"), ("shopify", "shopify.com"),
    ("slack", "slack.com"), ("pitch", "pitch.com"), ("notion", "notion.com"),
    ("lovable", "lovable.dev"), ("chatbase", "chatbase.co")]]
EVAL = ["openai", "stripe", "cal", "github", "raycast", "cloudflare"]
SHOWCASE = ["ycombinator", "x", "shopify", "stripe", "openai", "notion", "slack", "pitch", "elevenlabs"]


def showcase(out):
    """The og:videos the skill made for nine famous sites, playing together in a 3 x 3 grid."""
    cw, ch, g = 400, 210, 12
    args, chain = [], ""
    for k, n in enumerate(SHOWCASE):
        args += ["-i", os.path.join(ROOT, best(n))]
        chain += f"[{k}:v]fps=15,scale={cw}:{ch}:flags=lanczos,setsar=1[v{k}];"
    layout = "|".join(f"{(k % 3) * (cw + g)}_{(k // 3) * (ch + g)}" for k in range(len(SHOWCASE)))
    clip_ = os.path.join(WORK, "showcase.mp4")
    os.makedirs(WORK, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex",
                    chain + "".join(f"[v{k}]" for k in range(len(SHOWCASE))) + f"xstack=inputs={len(SHOWCASE)}:layout={layout}:fill=0x0f0d0b[g]",
                    "-map", "[g]", "-t", "4", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv444p", clip_], check=True)
    gif([clip_], out, width=880)

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@400..700&family=Fragment+Mono&display=block" rel="stylesheet">
<script>window.OG = {{ width: {W}, height: {H} }};</script>
<style>
* {{ margin:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; overflow:hidden; background:oklch(0.145 0.006 60); }}
body {{ font-family:'Familjen Grotesk', sans-serif; color:oklch(0.97 0.004 60); -webkit-font-smoothing:antialiased; position:relative; }}
.card {{ position:absolute; border-radius:{R}px; overflow:hidden; box-shadow:0 0 0 1px oklch(1 0 0 / 0.1), 0 10px 30px oklch(0 0 0 / 0.35); }}
.card img, .card video {{ width:100%; height:100%; display:block; object-fit:cover; }}
.tag {{ position:absolute; font-family:'Fragment Mono', monospace; font-size:{F}px; color:oklch(0.72 0.01 60); }}
.tag b {{ color:oklch(0.82 0.15 78); font-weight:400; }}
.site {{ position:absolute; font-family:'Fragment Mono', monospace; font-size:{F}px; color:oklch(0.82 0.008 60); }}
svg {{ position:absolute; }}
</style></head><body>
{BODY}
<script>
const vids = [...document.querySelectorAll('video')], imgs = [...document.querySelectorAll('img')];
const loaded = el => new Promise(r => (el.tagName === 'VIDEO' ? el.readyState >= 2 : el.complete) ? r()
  : el.addEventListener(el.tagName === 'VIDEO' ? 'loadeddata' : 'load', r, {{ once: true }}));
window.render = async function (t) {{
  await Promise.all(vids.map(v => new Promise(r => {{
    const u = Math.min(t % 4, v.duration - 0.001);
    if (Math.abs(v.currentTime - u) < 1e-3) return r();
    v.addEventListener('seeked', () => r(), {{ once: true }}); v.currentTime = u;
  }})));
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
}};
window.ready = Promise.all([document.fonts.ready, ...vids.map(loaded), ...imgs.map(loaded)]).then(() => window.render(0)).then(() => {{ window.readyDone = true; }});
</script></body></html>"""

ARROW = '<svg style="left:{x}px;top:{y}px" width="{w}" height="24" viewBox="0 0 {w} 24" fill="none"><path d="M3 12 H{a} M{b} 3 L{c} 12 L{b} 21" stroke="oklch(0.82 0.15 78)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def pair(x, y, cw, still, video, site, f, labels):
    ch = round(cw * 630 / 1200)
    gap = 56
    out = []
    if labels:
        out.append(f'<div class="tag" style="left:{x}px;top:{y - f - 12}px"><b>before</b> og:image</div>')
        out.append(f'<div class="tag" style="left:{x + cw + gap}px;top:{y - f - 12}px"><b>after</b> og:video</div>')
    out.append(f'<div class="card" style="left:{x}px;top:{y}px;width:{cw}px;height:{ch}px"><img src="../../{still}"></div>')
    out.append(ARROW.format(x=x + cw + 10, y=y + ch // 2 - 12, w=gap - 20, a=gap - 26, b=gap - 34, c=gap - 23))
    out.append(f'<div class="card" style="left:{x + cw + gap}px;top:{y}px;width:{cw}px;height:{ch}px"><img src="../../{still}"></div>')
    out.append(f'<div class="site" style="left:{x}px;top:{y + ch + 10}px">{site}</div>')
    return "\n".join(out), ch, (video, x + cw + gap, y, cw, ch)


def clip(name, W, H, body, slots, width, R=10):
    """The layout as a still, with every og:video played into its slot: a 4 s MP4 at `width` px, 15 fps."""
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    html = os.path.join(WORK, name + ".html")
    open(html, "w").write(PAGE.format(W=W, H=H, R=R, F=15, BODY=body))
    frames = os.path.join(WORK, name)
    subprocess.run([PY, os.path.join(ROOT, "scripts", "render_frames.py"), html, frames, "--root", ROOT, "--frames", "0"],
                   check=True, capture_output=True)
    bg = os.path.join(frames, "f0000.png")
    k = Image.open(bg).width / W  # the capture's own scale (2x)
    args, chain, last = ["-loop", "1", "-t", "4", "-i", bg], [], "0:v"
    for j, (video, x, y, cw, ch) in enumerate(slots):
        mw, mh = round(cw * k), round(ch * k)
        mask = os.path.join(WORK, f"{name}-mask{j}.png")
        m = Image.new("L", (mw, mh), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, mw - 1, mh - 1], radius=round(R * k), fill=255)
        m.save(mask)
        args += ["-i", os.path.join(ROOT, video), "-loop", "1", "-i", mask]
        vi, mi = 1 + 2 * j, 2 + 2 * j
        chain.append(f"[{vi}:v]fps=15,scale={mw}:{mh}:flags=lanczos,format=rgba[v{j}];[{mi}:v]format=gray[m{j}];[v{j}][m{j}]alphamerge[a{j}];"
                     f"[{last}][a{j}]overlay={round(x * k)}:{round(y * k)}:shortest=1[o{j}]")
        last = f"o{j}"
    out = os.path.join(WORK, name + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(chain) + f";[{last}]scale={width}:-2:flags=lanczos,fps=15[f]",
                    "-map", "[f]", "-t", "4", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv444p", out], check=True)
    return out


def gif(clips, out, width=None):
    """One GIF from one or more clips played in turn, with one palette."""
    src = clips[0]
    if len(clips) > 1:
        lst = os.path.join(WORK, os.path.basename(out) + ".txt")
        open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
        src = os.path.join(WORK, os.path.basename(out) + ".mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", src], check=True)
    pal = out + ".pal.png"
    pre = f"fps=15,scale={width}:-1:flags=lanczos," if width else ""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", pre + "palettegen=stats_mode=diff", pal], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", pal, "-lavfi", f"[0:v]{pre}null[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    "-loop", "0", out], check=True)
    os.remove(pal)
    print(f"{os.path.relpath(out, ROOT)}  {os.path.getsize(out) // 1024} KB")


def main():
    os.makedirs(os.path.join(ROOT, "social", "pairs"), exist_ok=True)
    for name, still, video, site in EXAMPLES:
        body, ch, slot = pair(24, 40, 360, still, video, site, 15, True)
        gif([clip(name, 24 * 2 + 360 * 2 + 56, 40 + ch + 40, body, [slot], 560)], os.path.join(ROOT, "social", "pairs", name + ".gif"))
    # the hero: the project's own og:video (site/og/build.sh), which says it all: a still in, a video out
    gif([os.path.join(ROOT, "site", "og", "out", "og.mp4")], os.path.join(ROOT, "social", "hero.gif"), width=880)
    showcase(os.path.join(ROOT, "social", "showcase.gif"))
    # the eval grid: two pairs a row, three rows
    cw, gapx, x0, y0, rowh = 250, 60, 24, 44, 0
    parts, slots = [], []
    for k, n in enumerate(EVAL):
        site = json.load(open(os.path.join(ROOT, "site", "media", "sites.json"))).get(n, {}).get("domain", n)
        col, row = k % 2, k // 2
        x = x0 + col * (2 * cw + 56 + gapx)
        body, ch, slot = pair(x, y0 + row * (round(cw * 630 / 1200) + 52), cw, f"eval/out/{n}.jpg", best(n), site, 15, row == 0)
        parts.append(body); slots.append(slot)
        rowh = ch
    W = x0 * 2 + 2 * (2 * cw + 56) + gapx
    H = y0 + 3 * (rowh + 52) - 10
    gif([clip("eval-pairs", W, H, "\n".join(parts), slots, 900)], os.path.join(ROOT, "social", "eval-pairs.gif"))


if __name__ == "__main__":
    main()
