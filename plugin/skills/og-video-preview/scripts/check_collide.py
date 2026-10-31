#!/usr/bin/env python3
"""Check that no two elements touch while they move: over the loop, the closest approach between every pair of
elements (each layer's own outline pushed through the transform the template applies, and what the reading left in
the plate), flagging pairs that come within --touch px when they were apart in the approved card. On a rebuild card
only the part of the loop after everything has landed counts; entrances are allowed to cross.

With --fix, the moving element of each touching pair is calmed (its idle lowered 15 % at a time, recorded in
layers.js as "fixed") until nothing touches; re-render afterwards. Learned from Joe Speaking's 74 cards, where a
floating orb kept brushing the arrow beside it.

Usage: check_collide.py OUT_DIR [--fix] [--touch 3] [--step 2]
"""
import argparse
import asyncio
import functools
import http.server
import json
import os
import threading

import cv2
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

JS = r"""
async ([sets, step]) => {
  await window.ready;
  const fps = 60, n = Math.round((OG.loop || 4) * fps);
  const moving = {};
  layers.forEach(l => { if (!TEXT.has(l.kind)) moving[l.id] = l; });
  // a rebuild card is checked once everything has landed; a living or flowing card the whole loop
  const from = layers.every(l => l.anchored) ? 0 : Math.max(0, ...layers.map(l => l.land || 0)) + 0.4;
  const place = id => {
    const l = moving[id];
    if (!l) return sets[id];
    const el = l.parts[0], cs = getComputedStyle(el);
    if (cs.transform === 'none') return sets[id];
    const M = new DOMMatrix(cs.transform), left = parseFloat(el.style.left), top = parseFloat(el.style.top);
    const [ox, oy] = cs.transformOrigin.split(' ').map(parseFloat);
    return sets[id].map(([x, y]) => { const p = M.transformPoint(new DOMPoint(x - left - ox, y - top - oy, 0, 1)); return [p.x / p.w + left + ox, p.y / p.w + top + oy]; });
  };
  const dmin = (a, b) => { let m = 1e9; for (const p of a) for (const q of b) { const d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2; if (d < m) m = d; } return Math.sqrt(m); };
  const ids = Object.keys(sets), out = {};
  for (let f = 0; f < n; f += step) {
    if (f && f / fps < from) continue;
    render(f / fps);
    const P = {}; ids.forEach(id => P[id] = place(id));
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
      const a = ids[i], b = ids[j];
      if (!moving[a] && !moving[b]) continue;
      const d = dmin(P[a], P[b]), k = a + '|' + b;
      out[k] = out[k] || { f0: null, min: 1e9, at: 0 };
      if (f === 0) out[k].f0 = d;
      else if (d < out[k].min) { out[k].min = d; out[k].at = f; }
    }
  }
  render(0);
  return out;
}
"""
TEXT = {"headline", "text", "label"}


def outline(sel, n=260):
    cs, _ = cv2.findContours(sel.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    p = np.concatenate([c.reshape(-1, 2) for c in cs]) if cs else np.zeros((0, 2))
    if len(p) > n:
        p = p[np.linspace(0, len(p) - 1, n).astype(int)]
    return p.tolist()


def config(d):
    src = open(os.path.join(d, "layers.js")).read()
    i, j = src.index("{"), src.rindex("}") + 1
    return src[:i], json.loads(src[i:j]), src[j:]


async def probe(d, touch, step):
    own = np.array(Image.open(os.path.join(d, "cut-mask.png")))
    _, cfg, _ = config(d)
    sets = {L["id"]: outline(own == L["mask"]) for L in cfg["layers"] if "mask" in L}
    # what the reading left in the plate (a wordmark, a sticker): it stays where it is, and nothing may run into it
    card = np.array(Image.open(os.path.join(d, cfg["image"])).convert("RGB")).astype(int)
    paper = np.array([int(cfg.get("paper", "#000000")[k:k + 2], 16) for k in (1, 3, 5)])
    rest = (np.abs(card - paper).sum(2) > 60) & (own == 0)
    rest = cv2.morphologyEx(rest.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0
    if rest.sum() > 50 and not cfg.get("cleanPlate"):
        sets["plate"] = outline(cv2.dilate(rest.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0, 400)
    handler = functools.partial(type("Q", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *x: None}), directory=d)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    page = next(f for f in ("from-image.html", "index.html") if os.path.exists(os.path.join(d, f)))
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": cfg["width"], "height": cfg["height"]})
        await pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/{page}")
        await pg.wait_for_function("window.readyDone === true", timeout=60000)
        res = await pg.evaluate(JS, [sets, step])
        await b.close()
    srv.shutdown()
    hits = [k for k, v in res.items() if v["min"] < touch and (v["f0"] if v["f0"] is not None else 1e9) >= touch]
    return res, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--touch", type=float, default=3)
    ap.add_argument("--step", type=int, default=2)
    a = ap.parse_args()
    d = os.path.abspath(a.out)
    for it in range(9):
        res, hits = asyncio.run(probe(d, a.touch, a.step))
        if not hits or not a.fix or it == 8:
            break
        head, cfg, tail = config(d)
        by = {L["id"]: L for L in cfg["layers"]}
        done = set()
        for pair in hits:
            cand = [by[x] for x in pair.split("|") if x in by and by[x]["kind"] not in TEXT | {"stroke"}]
            if not cand:
                continue
            L = max(cand, key=lambda L: L.get("idle", 1))
            if L["id"] in done:
                continue
            old = L.get("idle", 1)
            L["idle"] = round(old * 0.85, 3)
            L["fixed"] = f"idle {L['idle']} (was {old}): touched {[x for x in pair.split('|') if x != L['id']][0]}"
            done.add(L["id"])
            print(f"calmed {L['id']}: idle {old} -> {L['idle']}")
        if not done:
            break
        open(os.path.join(d, "layers.js"), "w").write(head + json.dumps(cfg, indent=1) + tail)
    for k, v in sorted(res.items(), key=lambda kv: kv[1]["min"]):
        if v["min"] < 30:
            print(f"  {'TOUCH' if k in hits else 'ok   '} {k:<30} apart {v['f0'] if v['f0'] is not None else 0:6.1f}  closest {v['min']:6.1f} at frame {v['at']}")
    print(f"touching pairs: {len(hits)}")
    raise SystemExit(1 if hits else 0)


if __name__ == "__main__":
    main()
