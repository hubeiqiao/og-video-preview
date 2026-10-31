#!/usr/bin/env python3
"""Build the clean plate and the cutouts for template/from-image.html.

Reads OUT/card.jpg and OUT/layers.js (and OUT/cut-mask.png from suggest_layers.py).
Writes:
  plate.png   the card with every layer removed and the background filled in
  layers.png  the card with alpha 1 over each layer's pixels, feathering to 0 just
              outside (where plate and card are identical), so layers over plate
              reproduce the card exactly and only the element moves, never a box
              of background around it
  glyphs.png  white, alpha = each layer's own pixels: a mask for light sweeps

Cut per layer: type keeps only its glyphs; avatars cut a disc; every other kind
cuts its filled outline. A layer you added by hand (no "mask" from suggest_layers.py)
is cut as a rectangle, or a disc with "cut": "disc". To change what an element is
made of, re-run suggest_layers.py rather than editing boxes.

Usage: make_plate.py OUT_DIR
"""
import json
import os
import re
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suggest_layers import background, dist, fill_holes, pushpull  # noqa: E402

TEXT_KINDS = {"headline", "text", "label"}


def read_config(d):
    src = open(os.path.join(d, "layers.js")).read()
    body = re.search(r"window\.OG\s*=\s*(\{.*\})\s*;", src, re.S).group(1)
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', body)  # bare keys
    body = re.sub(r",(\s*[}\]])", r"\1", body)  # trailing commas
    return json.loads(body)


def main():
    d = sys.argv[1]
    cfg = read_config(d)
    img = cv2.cvtColor(cv2.imread(os.path.join(d, cfg["image"])), cv2.COLOR_BGR2RGB)
    H, W = img.shape[:2]
    marked = os.path.join(d, "cut-mask.png")
    owner = cv2.imread(marked, cv2.IMREAD_GRAYSCALE) if os.path.exists(marked) else np.zeros((H, W), np.uint8)
    flat = json.load(open(os.path.join(d, "cut.json")))["flat"] if os.path.exists(os.path.join(d, "cut.json")) else False

    cut = np.zeros((H, W), np.uint8)    # what each layer carries
    glyph = np.zeros((H, W), np.uint8)  # tight pixels, for sheens
    thin = np.zeros((H, W), np.uint8)   # glyph cuts: inpaint these with texture
    wide = np.zeros((H, W), np.uint8)   # shapes sitting on the background: refill with the background model
    own_cut = []                        # each layer's own cut, for its own cutout image
    clean_fill = set()                  # layers whose hole is refilled from the plain background model
    B, _ = background(img, 40)
    # the background away from every element (a flat edge can still hide a vignette or a gradient),
    # so soft shadows and glows are not part of it
    near = cv2.dilate((owner > 0).astype(np.uint8), np.ones((45, 45), np.uint8))
    # on a flat card, only pixels of the card's own colour: a scribble or a sticker left in the plate would tint the
    # model and leave faint ghosts of every element that leaves
    base = (near == 0) & (dist(img, B) < 30) if flat else near == 0
    if base.mean() > 0.05:
        B = pushpull(img, base)
    faint = dist(img, B)
    for L in cfg["layers"]:
        x, y, w, h = L["box"]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        own = owner[y0:y1, x0:x1]
        # only this layer's own pixels; a layer added by hand has none, so it is cut as a rectangle (or a disc)
        sub = (own == L["mask"]).astype(np.uint8) if "mask" in L else np.zeros_like(own)
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        kind = L.get("kind", "")
        if L.get("cut") == "disc" or kind == "avatar":
            cv2.ellipse(m, ((x1 - x0) // 2, (y1 - y0) // 2), ((x1 - x0) // 2, (y1 - y0) // 2), 0, 0, 360, 1, -1)
        elif L.get("cut") == "rect" or sub.sum() == 0:
            m[:] = 1
        elif kind in TEXT_KINDS:
            # faint strokes too: inside its own line, anything clearly off the line's surroundings is type
            box_img = img[y0:y1, x0:x1]
            ring = np.concatenate([box_img[:2].reshape(-1, 3), box_img[-2:].reshape(-1, 3), box_img[:, :2].reshape(-1, 3), box_img[:, -2:].reshape(-1, 3)])
            faint_ink = (dist(box_img, np.median(ring, 0)) > 22) & ((own == 0) | (own == L.get("mask", -1)))
            sub = np.maximum(sub, faint_ink.astype(np.uint8))
            # antialiasing and JPEG ringing go too; on a gradient or picture also a soft shadow or glow
            k = 7 if flat else 13
            m = cv2.dilate(sub, np.ones((k, k), np.uint8))
        else:
            m = cv2.dilate(fill_holes(sub), np.ones((11, 11), np.uint8))  # soft edges, shadows, chroma bleed
        rect = L.get("cut") == "rect"
        if kind != "avatar" and (sub.sum() or rect):
            # a soft shadow or glow belongs to its element: faint difference from the background, close by, owned by nobody
            # else; a window's drop shadow reaches further, and left in the plate it is a ghost of the window once it leaves
            halo = cv2.dilate(m, np.ones((41, 41) if rect else (25, 25), np.uint8)) > 0
            f_ = faint[y0:y1, x0:x1]
            halo &= (f_ > 9) & (f_ < 90) & ((own == 0) | (own == L.get("mask", -1)))
            # where the background model is off (a gradient it does not follow), everything around reads as "faint":
            # type has no glow to carry there, and a halo would be a box of background travelling with the words
            around = (cv2.dilate(m, np.ones((15, 15), np.uint8)) > 0) & ~(m > 0)
            if kind in TEXT_KINDS and around.any() and np.median(f_[around]) > 8:
                halo[:] = False
            m = np.maximum(m, cv2.dilate(halo.astype(np.uint8), np.ones((5, 5), np.uint8)))
            # on the plain background, refill from the background model; on a panel or a picture, from the neighbours
            ring = cv2.dilate(m, np.ones((9, 9), np.uint8)) - m
            rx = img[y0:y1, x0:x1][ring > 0]
            if kind in TEXT_KINDS and cfg.get("background") == "detailed":
                thin[y0:y1, x0:x1] |= m  # type on a picture: refill with its texture
            elif len(rx) and (dist(rx, B[y0:y1, x0:x1][ring > 0]) < 30).mean() > 0.75:
                wide[y0:y1, x0:x1] |= m
                clean_fill.add(L.get("id"))
            elif kind in TEXT_KINDS and not flat:
                thin[y0:y1, x0:x1] |= m
        if "mask" in L:  # never carry another layer's glyphs: tight leading would duplicate them
            others = cv2.dilate(((own > 0) & (own != L["mask"])).astype(np.uint8), np.ones((3, 3) if kind in TEXT_KINDS else (7, 7), np.uint8)) > 0  # a picture never carries the soft rim of type over it
            m[others] = 0
        cut[y0:y1, x0:x1] |= m
        own_cut.append((L.get("id", f"layer{len(own_cut) + 1}"), x0, y0, x1, y1, m, L.get("cut") == "ink"))
        glyph[y0:y1, x0:x1] |= sub if sub.sum() else m

    hole = cv2.dilate(cut, np.ones((3, 3), np.uint8)) > 0
    plate = pushpull(img, ~hole)
    if not flat and thin.any():  # over photos and gradients, keep texture behind type
        tex = cv2.inpaint(img, (cv2.dilate(thin, np.ones((3, 3), np.uint8)) * 255).astype(np.uint8), 7, cv2.INPAINT_TELEA)
        t = cv2.dilate(thin, np.ones((3, 3), np.uint8)) > 0
        plate[t] = tex[t]
    w_ = wide > 0
    smooth_fill = plate.copy()  # the refill from the surroundings, before the background model replaces it
    plate[w_] = B[w_]  # a large hole filled from its neighbours smears them in; the background model does not
    # an element on a flat surface of its own (type on a notepad, a mark on a card inside the card): the background
    # model is the whole card's, so there it is the wrong colour; the surface's own colour, just around it, is right
    for lid, x0, y0, x1, y1, m, _ in own_cut:
        if lid not in clean_fill:
            continue
        full = np.zeros((H, W), np.uint8); full[y0:y1, x0:x1] = m
        ring = (cv2.dilate(full, np.ones((11, 11), np.uint8)) > 0) & ~(cv2.dilate(cut, np.ones((3, 3), np.uint8)) > 0)
        if ring.sum() > 60 and img[ring].astype(np.float32).std(0).max() < 6:
            plate[(cv2.dilate(full, np.ones((3, 3), np.uint8)) > 0)] = np.median(img[ring], 0)
    # text typed into an input: behind it is the input's own flat fill, the median just around the text
    for lid, x0, y0, x1, y1, m, _ in own_cut:
        L = next((L for L in cfg["layers"] if L.get("id") == lid), {})
        if L.get("role") != "typing":
            continue
        full = np.zeros((H, W), np.uint8); full[y0:y1, x0:x1] = m
        ring = (cv2.dilate(full, np.ones((9, 9), np.uint8)) > 0) & ~(full > 0)
        plate[(full > 0) | (cv2.dilate(full, np.ones((3, 3), np.uint8)) > 0)] = np.median(img[ring], 0)
    # a list that scrolls (a reading's "list" region): behind it is only the card and its highlight bar, so its column is
    # rebuilt from them, not refilled line by line (a refill would smear the bar's colour down the column)
    for R in cfg.get("regions") or []:
        if R.get("role") != "list":
            continue
        x, y, w, h = R["box"]
        # the card behind a list is a gradient down the column: each row's median across it, which its letters cannot move
        col = img[y:y + h, x:x + w].astype(np.float32)
        light = col.mean() > 128  # letters darker than a light card (or lighter than a dark one) never reach this percentile
        rows = np.percentile(col, 88 if light else 12, axis=1)
        rows = cv2.GaussianBlur(rows[:, None, :], (1, 0), sigmaX=0.1, sigmaY=6)[:, 0, :]
        plate[y:y + h, x:x + w] = rows[:, None, :]
        hole[y:y + h, x:x + w] = True  # all of the column is rebuilt, not only where a line was
        if R.get("bar"):
            bx, by, bw, bh = R["bar"]
            bar = img[by:by + bh, bx:bx + bw].astype(np.float32)
            bar_c = np.median(img[by + 4:by + bh - 4, bx + 4:bx + 14].reshape(-1, 3), 0)
            lum_ = lambda a: a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            text = lum_(bar) < lum_(bar_c[None, None, :].astype(np.float32)) - 10  # its own text, darker than the bar
            text = cv2.dilate(text.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            plate[by:by + bh, bx:bx + bw] = np.where(text[..., None], bar_c, bar)
    clean = os.path.join(d, "plate-clean.png")
    if cfg.get("cleanPlate") and os.path.exists(clean):  # a clean background from an image-edit tool beats any refill
        cp = cv2.cvtColor(cv2.imread(clean), cv2.COLOR_BGR2RGB)
        plate = cv2.resize(cp, (W, H), interpolation=cv2.INTER_AREA).astype(plate.dtype)
    plate = np.where(hole[..., None], plate, img).clip(0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(d, "plate.png"), cv2.cvtColor(plate, cv2.COLOR_RGB2BGR))

    def cutout(m):  # alpha 1 over the cut and its refilled rim, a soft edge outside where plate and card agree
        a_ = cv2.GaussianBlur(cv2.dilate(m, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.5)
        a_ = np.maximum(a_, (cv2.dilate(m, np.ones((3, 3), np.uint8)) > 0).astype(np.float32))
        return cv2.cvtColor(np.dstack([img, (a_ * 255).clip(0, 255).astype(np.uint8)]), cv2.COLOR_RGBA2BGRA)
    cv2.imwrite(os.path.join(d, "layers.png"), cutout(cut))
    # one image per layer with only its own pixels, so boxes may overlap (tight leading, a pill in a line)
    # each image is cropped to its own pixels (a full-card image per layer costs the browser too much
    # memory); cuts/cuts.js records where each crop sits on the card
    os.makedirs(os.path.join(d, "cuts"), exist_ok=True)
    where = {}
    def ink_cutout(m):
        # its ink alone: coverage from how far each pixel is from what lies behind it (the refilled plate), in the
        # line's own ink colour, so it can pass over a highlight bar or the bare card without a box of either
        near = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
        d = dist(img, plate)
        lm = img.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        ink = img[near & (d > 30) & (lm <= np.percentile(lm[near & (d > 30)], 25))] if (near & (d > 30)).any() else img[near]
        tone = np.median(ink.reshape(-1, 3), 0) if len(ink) else np.zeros(3)  # the darkest of its ink, never the bar behind it
        back = np.median(plate[near].reshape(-1, 3), 0)
        full = max(20.0, float(dist(tone[None, :], back[None, :])[0]))
        a_ = np.clip((d - 8) / (full - 8), 0, 1) * near  # coverage, above the refill's own noise
        # one neutral ink: the template sets each row's lightness with opacity, so no colour from behind can travel with it
        dark = lm[near].mean() > (np.array([0.2126, 0.7152, 0.0722]) @ tone)
        rgb = np.full(img.shape, 28 if dark else 240, np.uint8)
        return cv2.cvtColor(np.dstack([rgb, (a_ * 255).astype(np.uint8)]), cv2.COLOR_RGBA2BGRA)

    jobs = []
    for lid, x0, y0, x1, y1, m, inky in own_cut:
        one = np.zeros((H, W), np.uint8)
        one[y0:y1, x0:x1] = m
        jobs.append((lid, one, cutout(one)))
        if inky:  # a list line also gets its ink alone, worn while it moves (at rest it wears its exact cut)
            jobs.append((lid + "-ink", one, ink_cutout(one)))
    for lid, one, rgba in jobs:
        ys, xs = np.nonzero(rgba[..., 3])
        if not len(ys):
            continue
        cx, cy, cx1, cy1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        cv2.imwrite(os.path.join(d, "cuts", f"{lid}.png"), rgba[cy:cy1, cx:cx1], [cv2.IMWRITE_PNG_COMPRESSION, 9])
        where[lid] = [cx, cy, cx1 - cx, cy1 - cy]
    with open(os.path.join(d, "cuts", "cuts.js"), "w") as fh:
        fh.write("window.CUTS = " + json.dumps(where) + ";\n")

    ga = cv2.GaussianBlur(glyph.astype(np.float32), (0, 0), 0.7)
    white = np.full((H, W, 3), 255, np.uint8)
    cv2.imwrite(os.path.join(d, "glyphs.png"), np.dstack([white, (ga * 255).clip(0, 255).astype(np.uint8)]))
    # where an element is lighter than the background behind it: a picture that stays in place takes its light sweep
    # through these parts only (the paper of a print, the glint on an object), never through its cut's soft edge
    lum = lambda a: a.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    lit = np.clip((lum(img) - lum(plate)) / 60, 0, 1) * (cv2.dilate(cut, np.ones((3, 3), np.uint8)) > 0)
    lit = cv2.GaussianBlur(lit, (0, 0), 1.0)
    cv2.imwrite(os.path.join(d, "light.png"), np.dstack([white, (lit * 255).clip(0, 255).astype(np.uint8)]))
    # an element whose hole cannot be refilled cleanly (grain, a photo, a pattern around it: the refill is a smooth
    # patch that shows the moment the element leaves) moves in place instead, and never leaves
    if not cfg.get("cleanPlate"):  # a flat card can still carry a grid, a map or a pattern
        hp = lambda a: np.abs(a.astype(np.float32) - cv2.GaussianBlur(a.astype(np.float32), (0, 0), 2)).mean(2)
        hp_img, hp_plate = hp(img), hp(plate)
        edges = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), 60, 140) > 0  # structure: grid lines, a map, stripes
        by_id = {L.get("id"): L for L in cfg["layers"]}
        poor = []
        for lid, x0, y0, x1, y1, m, _ in own_cut:
            L = by_id.get(lid)
            if L is None or L.get("role") in ("window", "panel", "float", "typing", "button", "listline", "scribble") or L.get("settle") or m.sum() < 300:
                continue
            full = np.zeros((H, W), np.uint8); full[y0:y1, x0:x1] = m
            inner = (full > 0) & hole
            ring = (cv2.dilate(full, np.ones((19, 19), np.uint8)) > 0) & ~(cv2.dilate(cut, np.ones((5, 5), np.uint8)) > 0)
            if ring.sum() < 80 or inner.sum() < 80:
                continue
            grain, smooth = hp_img[ring].mean(), hp_plate[inner].mean()
            busy = img[ring].astype(np.float32).std(0).mean()  # a picture around it: whatever is filled in is a guess
            if os.environ.get("PLATE_DEBUG"): print(lid, round(float(grain), 2), round(float(smooth), 2), round(float(busy), 1), int(ring.sum()), int(inner.sum()))
            lines_ = edges[ring].mean()  # a refill cannot continue lines that run under the element
            # the refill's colour at its edge against the card just outside: a step there is a visible patch
            inner_ = (full > 0) & hole & ~(cv2.erode(full, np.ones((9, 9), np.uint8)) > 0)
            outer_ = (cv2.dilate(full, np.ones((9, 9), np.uint8)) > 0) & ~(full > 0) & ~(cv2.dilate(cut, np.ones((3, 3), np.uint8)) > 0)
            step_ = float(np.abs(np.median(plate[inner_], 0).astype(float) - np.median(img[outer_], 0).astype(float)).max()) if inner_.sum() > 40 and outer_.sum() > 40 else 0
            if os.environ.get("PLATE_DEBUG"): print("  edges", round(float(lines_), 3), "step", round(step_, 1))
            # refilled from its neighbours (a panel, a poster, a photo around it): that refill is a smear, so it stays
            smear = lid not in clean_fill
            # the card's model and the surroundings' own refill disagree here (a gradient the model does not follow, or
            # something near that a refill would pull in): neither can be trusted, so it stays
            unsure = lid in clean_fill and float(np.abs(B[inner].astype(float) - smooth_fill[inner].astype(float)).mean()) > 4
            if unsure and plate[inner].astype(float).std() > 0:
                smear = True
            if smear or (grain > 1.2 and smooth < 0.4 * grain) or busy > 26 or lines_ > 0.05 or step_ > 10:
                L["settle"] = True
                poor.append(f"{lid} ({'smeared refill, ' if smear else ''}grain {grain:.1f} vs {smooth:.1f}, spread {busy:.0f})")
        # what lies on something that stays (a heading in an app window that holds still) stays with it: leaving, it
        # would expose the window under it, and the window cannot follow
        holders = [L for L in cfg["layers"] if L.get("settle") and L.get("kind") not in ("headline", "text", "label")]
        for L in cfg["layers"]:
            if L.get("settle") or L.get("role"):
                continue
            lx, ly, lw, lh = L["box"]
            cx_, cy_ = lx + lw / 2, ly + lh / 2
            def over(M):  # its centre on it, or a tenth of it over it (a word running onto a window)
                mx, my, mw, mh = M["box"]
                ov = max(0, min(lx + lw, mx + mw) - max(lx, mx)) * max(0, min(ly + lh, my + mh) - max(ly, my))
                return (mx <= cx_ <= mx + mw and my <= cy_ <= my + mh and mw * mh > lw * lh) or ov > 0.1 * lw * lh
            if any(M is not L and over(M) for M in holders):
                L["settle"] = True
                poor.append(f"{L.get('id')} (on something that stays)")
        # type is one block: if one line has to stay, they all do (half a paragraph leaving reads as broken)
        TEXTISH = {"headline", "text", "label"}
        if any(by_id.get(p_.split(" ")[0], {}).get("kind") in TEXTISH for p_ in poor):
            for L in cfg["layers"]:
                if L.get("kind") in TEXTISH and not L.get("role") and not L.get("settle"):
                    L["settle"] = True
                    poor.append(f"{L.get('id')} (with the rest of the type)")
        if poor:
            src = open(os.path.join(d, "layers.js")).read()
            i, j = src.index("{"), src.rindex("}") + 1
            try:
                body = json.loads(src[i:j])
            except ValueError:  # layers.js edited by hand into plain JS: it keeps what it says
                body = None
            if body is not None:
                for L in body["layers"]:
                    if by_id.get(L.get("id"), {}).get("settle"):
                        L["settle"] = True
                open(os.path.join(d, "layers.js"), "w").write(src[:i] + json.dumps(body, indent=1) + src[j:])
                print("stays in place (its hole would show): " + ", ".join(poor))
    print(f"plate, layers and glyphs written ({int(hole.sum())} px refilled)")


if __name__ == "__main__":
    main()
