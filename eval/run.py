#!/usr/bin/env python3
"""Eval: run the whole route A pipeline on every card in eval/cards and score it.

For each card: read it (suggest_layers.py), cut it (make_plate.py), render 4 s at 60 fps,
then measure what must hold for every OG video:
  frame0   the first frame equals the card (mean difference, share of local defects)
  seam     the jump from the last frame to the first, against an ordinary frame step
  size     the encoded MP4 and frame-0 JPEG against the 2 MB / 180 KB limits
and record what the engine decided (layers, kinds, style) so changes can be compared.

Writes eval/out/<name>.mp4 and .jpg, eval/results.json, eval/sheet.jpg (a contact sheet)
and the results table in eval/README.md.

Usage: python3 eval/run.py [--only stripe,github] [--jobs 3] [--keep]
"""
import argparse
import concurrent.futures as cf
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def frame0_scores(card, frame):
    ref = Image.open(card).convert("RGB")
    f = Image.open(frame).convert("RGB").resize(ref.size, Image.LANCZOS)
    soft = lambda im: np.asarray(im.filter(ImageFilter.GaussianBlur(1)), np.int16)
    d = np.abs(soft(ref) - soft(f))  # the same measure as scripts/check_frame0.py
    return float(d.mean()), float((d.max(2) > 40).mean() * 100)


def seam_score(frames):
    d = lambda p, q: int(np.abs(np.asarray(Image.open(p).convert("RGB"), np.int16) - np.asarray(Image.open(q).convert("RGB"), np.int16)).max())
    return d(frames[-1], frames[0]), max(d(frames[0], frames[1]), d(frames[-3], frames[-2]))


def one(card, keep, resume):
    name = os.path.splitext(os.path.basename(card))[0]
    done = os.path.join(HERE, "out", name + ".json")
    if resume and os.path.exists(done):
        return json.load(open(done))
    # frames go to a temp folder: thousands of PNGs inside a synced folder slow the whole machine
    work = os.path.join(HERE, "work", name) if keep else os.path.join(tempfile.gettempdir(), "og-eval", name)
    shutil.rmtree(work, ignore_errors=True)
    t0 = time.time()
    log = run([PY, os.path.join(ROOT, "scripts", "suggest_layers.py"), card, work])
    shutil.copy(os.path.join(ROOT, "template", "from-image.html"), work)
    run([PY, os.path.join(ROOT, "scripts", "render_frames.py"), os.path.join(work, "from-image.html"), os.path.join(work, "frames")])
    frames = sorted(glob.glob(os.path.join(work, "frames", "f*.png")))
    mean, local = frame0_scores(os.path.join(work, "card.jpg"), frames[0])
    seam, step = seam_score(frames)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    run(["bash", os.path.join(ROOT, "scripts", "encode.sh"), os.path.join(work, "frames"), os.path.join(HERE, "out", name)])
    src = open(os.path.join(work, "layers.js")).read()
    cfg = json.loads(re.search(r"window\.OG\s*=\s*(\{.*\})\s*;", src, re.S).group(1))
    kinds = {}
    for L in cfg["layers"]:
        kinds[L["kind"]] = kinds.get(L["kind"], 0) + 1
    style = cfg["style"] if cfg["style"] != "auto" else ("living" if cfg["background"] == "detailed" else "rebuild")
    res = {
        "name": name, "layers": len(cfg["layers"]), "kinds": kinds, "background": cfg["background"], "style": style,
        "frame0_mean": round(mean, 3), "frame0_local_pct": round(local, 3), "seam": seam, "step": step,
        "mp4_kb": os.path.getsize(os.path.join(HERE, "out", name + ".mp4")) // 1024,
        "jpg_kb": os.path.getsize(os.path.join(HERE, "out", name + ".jpg")) // 1024,
        "seconds": round(time.time() - t0, 1),
    }
    res["pass"] = (mean <= 2 and local <= 0.05 and seam <= step * 1.5 + 4 and res["mp4_kb"] <= 2048 and res["jpg_kb"] <= 180)
    if not keep:
        shutil.rmtree(work, ignore_errors=True)
    else:
        shutil.rmtree(os.path.join(work, "frames"), ignore_errors=True)
    json.dump(res, open(done, "w"), indent=1)
    return res


def sheet(results):
    tw, th, cols = 300, 158, 4
    rows = (len(results) + cols - 1) // cols
    c = Image.new("RGB", (cols * tw * 3 + cols * 12, rows * (th + 22)), (12, 12, 14))
    d = ImageDraw.Draw(c)
    for i, r in enumerate(results):
        x, y = (i % cols) * (tw * 3 + 12), (i // cols) * (th + 22)
        mp4 = os.path.join(HERE, "out", r["name"] + ".mp4")
        for k, t in enumerate((0.3, 0.7, 1.6)):
            png = os.path.join(HERE, "out", f".{r['name']}-{k}.png")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", mp4, "-frames:v", "1", "-vf", f"scale={tw}:-1", png], check=True)
            c.paste(Image.open(png), (x + k * tw, y + 20))
            os.remove(png)
        d.text((x + 4, y + 4), f"{r['name']}  {r['layers']} layers  {r['style']}  {'pass' if r['pass'] else 'FAIL'}", fill=(220, 220, 220))
    c.save(os.path.join(HERE, "sheet.jpg"), quality=80)


def table(results):
    lines = ["| Card | Layers | Kinds | Style | Frame 0 (mean / local) | Seam / step | MP4 | Pass |", "|---|---|---|---|---|---|---|---|"]
    for r in results:
        kinds = ", ".join(f"{k} {v}" for k, v in sorted(r["kinds"].items(), key=lambda e: -e[1]))
        lines.append(f"| [{r['name']}](out/{r['name']}.mp4) | {r['layers']} | {kinds} | {r['style']} | {r['frame0_mean']} / {r['frame0_local_pct']}% | {r['seam']} / {r['step']} | {r['mp4_kb']} KB | {'yes' if r['pass'] else '**no**'} |")
    passed = sum(r["pass"] for r in results)
    return f"**{passed} of {len(results)} cards pass.**\n\n" + "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated card names")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--keep", action="store_true", help="keep each card's work folder (layers.js and cuts) in eval/work/")
    ap.add_argument("--resume", action="store_true", help="skip cards that already have a result in eval/out/")
    a = ap.parse_args()
    cards = sorted(glob.glob(os.path.join(HERE, "cards", "*.jpg")))
    if a.only:
        cards = [c for c in cards if os.path.splitext(os.path.basename(c))[0] in a.only.split(",")]
    results = []
    def safe(c):
        try:
            return one(c, a.keep, a.resume)
        except subprocess.CalledProcessError as e:  # a failed card is a result, not the end of the run
            name = os.path.splitext(os.path.basename(c))[0]
            err = (e.stderr or e.stdout or "").strip().splitlines()[-1:] or ["failed"]
            return {"name": name, "layers": 0, "kinds": {}, "background": "", "style": "", "frame0_mean": -1, "frame0_local_pct": -1,
                    "seam": -1, "step": -1, "mp4_kb": -1, "jpg_kb": -1, "seconds": 0, "pass": False, "error": err[0]}
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for r in ex.map(safe, cards):
            print(f"{r['name']:<14} {r['layers']:>2} layers  {r['style']:<8} frame0 {r['frame0_mean']:.2f}/{r['frame0_local_pct']:.3f}%  seam {r['seam']}/{r['step']}  {r['mp4_kb']} KB  {'pass' if r['pass'] else 'FAIL'}", flush=True)
            results.append(r)
    if not a.only:
        json.dump(results, open(os.path.join(HERE, "results.json"), "w"), indent=1)
        sheet(results)
        readme = os.path.join(HERE, "README.md")
        text = open(readme).read() if os.path.exists(readme) else ""
        start, end = "<!-- results -->", "<!-- /results -->"
        block = f"{start}\n{table(results)}{end}"
        text = re.sub(re.escape(start) + ".*" + re.escape(end), block, text, flags=re.S) if start in text else text + "\n" + block + "\n"
        open(readme, "w").write(text)
    print(f"{sum(r['pass'] for r in results)} of {len(results)} pass")


if __name__ == "__main__":
    main()
