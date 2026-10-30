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
        if kind != "avatar" and L.get("cut") != "rect" and sub.sum():
            # a soft shadow or glow belongs to its element: faint difference from the background, close by, owned by nobody else
            halo = cv2.dilate(m, np.ones((25, 25), np.uint8)) > 0
            f_ = faint[y0:y1, x0:x1]
            halo &= (f_ > 9) & (f_ < 90) & ((own == 0) | (own == L.get("mask", -1)))
            m = np.maximum(m, cv2.dilate(halo.astype(np.uint8), np.ones((5, 5), np.uint8)))
            # on the plain background, refill from the background model; on a panel or a picture, from the neighbours
            ring = cv2.dilate(m, np.ones((9, 9), np.uint8)) - m
            rx = img[y0:y1, x0:x1][ring > 0]
            if kind in TEXT_KINDS and cfg.get("background") == "detailed":
                thin[y0:y1, x0:x1] |= m  # type on a picture: refill with its texture
            elif len(rx) and (dist(rx, B[y0:y1, x0:x1][ring > 0]) < 30).mean() > 0.75:
                wide[y0:y1, x0:x1] |= m
            elif kind in TEXT_KINDS and not flat:
                thin[y0:y1, x0:x1] |= m
        if "mask" in L:  # never carry another layer's glyphs: tight leading would duplicate them
            others = cv2.dilate(((own > 0) & (own != L["mask"])).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            m[others] = 0
        cut[y0:y1, x0:x1] |= m
        own_cut.append((L.get("id", f"layer{len(own_cut) + 1}"), x0, y0, x1, y1, m))
        glyph[y0:y1, x0:x1] |= sub if sub.sum() else m

    hole = cv2.dilate(cut, np.ones((3, 3), np.uint8)) > 0
    plate = pushpull(img, ~hole)
    if not flat and thin.any():  # over photos and gradients, keep texture behind type
        tex = cv2.inpaint(img, (cv2.dilate(thin, np.ones((3, 3), np.uint8)) * 255).astype(np.uint8), 7, cv2.INPAINT_TELEA)
        t = cv2.dilate(thin, np.ones((3, 3), np.uint8)) > 0
        plate[t] = tex[t]
    w_ = wide > 0
    plate[w_] = B[w_]  # a large hole filled from its neighbours smears them in; the background model does not
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
    for lid, x0, y0, x1, y1, m in own_cut:
        one = np.zeros((H, W), np.uint8)
        one[y0:y1, x0:x1] = m
        rgba = cutout(one)
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
    print(f"plate, layers and glyphs written ({int(hole.sum())} px refilled)")


if __name__ == "__main__":
    main()
