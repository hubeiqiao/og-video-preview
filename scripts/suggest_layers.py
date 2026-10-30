#!/usr/bin/env python3
"""Read an approved OG image and propose its animation layers, one per element,
each with a kind the template turns into motion.

1. Normalises the card to 1200x630 (cover crop): OUT/card.jpg
2. Models the background (a flat colour, or a smooth estimate of a gradient or photo)
   and marks every pixel that stands out from it.
3. Groups marked pixels into elements. A large surface (a window, a big card) is
   treated as backdrop and searched again for the elements on it.
4. Classifies each element from what it looks like:
     headline, text, label    type, by size on the card
     logo                     the mark at the start of a wordmark (split from the words)
     pill                     a solid rounded shape with content: tags, buttons
     icon                     a small graphic with detail: logos, emoji, mascots
     avatar                   a round photo
     photo                    a rectangular photo or render
     panel                    a large flat surface: screenshot, UI card, sticky note
     illustration             a larger multicolour graphic
     shape                    a solid one-colour form: dots, squares, blobs, triangles
     stroke                   a line, arrow, underline or squiggle
5. Splits text into words (short headlines into letters) for word-by-word motion.
6. Writes OUT/layers.js and OUT/layers-preview.png, then runs make_plate.py
   (plate.png, layers.png, glyphs.png).

Review layers-preview.png. To correct an element, change its `kind` in layers.js;
after moving or adding boxes, re-run make_plate.py.

Usage: suggest_layers.py CARD OUT_DIR [--style auto|rebuild|living] [--energy calm|lively|bold] [--tol 40] [--max 18]
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

W, H = 1200, 630
KINDS = ["headline", "text", "label", "logo", "pill", "icon", "avatar", "photo",
         "panel", "illustration", "shape", "stroke"]
TEXT_KINDS = {"headline", "text", "label"}


def load_card(path):
    im = Image.open(path).convert("RGB")
    # cover crop in the source's own pixels first, then scale: no huge intermediate for odd ratios
    cw, ch = (im.width, round(im.width * H / W)) if im.width / im.height < W / H else (round(im.height * W / H), im.height)
    left, top = (im.width - cw) // 2, (im.height - ch) // 2
    return np.array(im.crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS))


def pushpull(img, known):
    """Fill unknown pixels smoothly from the known ones (a mask-weighted image pyramid)."""
    c = img.astype(np.float32) * known[..., None]
    w = known.astype(np.float32)
    pyr = []
    while min(c.shape[:2]) > 2:
        pyr.append((c, w))
        size = (max(1, c.shape[1] // 2), max(1, c.shape[0] // 2))
        c = cv2.resize(c, size, interpolation=cv2.INTER_AREA)
        w = cv2.resize(w, size, interpolation=cv2.INTER_AREA)
    est = c / np.maximum(w, 1e-6)[..., None]
    for c, w in reversed(pyr):
        up = cv2.resize(est, (c.shape[1], c.shape[0]), interpolation=cv2.INTER_LINEAR)
        k = np.clip(w * 4, 0, 1)[..., None]  # trust cells that are mostly known
        est = k * (c / np.maximum(w, 1e-6)[..., None]) + (1 - k) * up
    return est


def mode_colour(pixels):
    q = pixels.reshape(-1, 3).astype(int) // 8
    keys, counts = np.unique(q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2], return_counts=True)
    k = keys[counts.argmax()]
    flat = pixels.reshape(-1, 3)
    inbin = (q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]) == k
    return flat[inbin].mean(0), counts.max() / len(q)  # the mean of the modal bin, not its centre


def dist(a, b):
    return np.abs(a.astype(np.float32) - np.asarray(b, np.float32)).sum(-1)


def background(img, tol):
    """Return (background estimate, is_flat)."""
    h, w = img.shape[:2]
    border = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]])
    mode, _ = mode_colour(border)
    if (dist(border, mode) < tol).mean() > 0.6:
        return np.broadcast_to(mode, img.shape).astype(np.float32), True
    # not flat: first guess from a wide median, then refill everything that stands out
    small = cv2.resize(img, (max(8, w // 8), max(8, h // 8)), interpolation=cv2.INTER_AREA)
    B = cv2.resize(cv2.medianBlur(small, 15), (w, h), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    for _ in range(2):
        fg = cv2.dilate((dist(img, B) > tol).astype(np.uint8), np.ones((9, 9), np.uint8))
        B = pushpull(img, fg == 0)
    return B, False


def despeckle(m):
    """Remove single-pixel specks. A 2x2 opening with explicit anchors, so the mask does not shift by a pixel."""
    k = np.ones((2, 2), np.uint8)
    return cv2.dilate(cv2.erode(m, k, anchor=(0, 0)), k, anchor=(1, 1))


def foreground(img, B, tol):
    d = dist(img, B)
    # a glow or soft gradient is background: whatever the plain background reaches without crossing an edge
    grey = cv2.cvtColor(np.ascontiguousarray(img.astype(np.uint8)), cv2.COLOR_RGB2GRAY).astype(np.float32)
    soft = np.hypot(cv2.Sobel(grey, cv2.CV_32F, 1, 0), cv2.Sobel(grey, cv2.CV_32F, 0, 1)) < 10
    seed = d <= tol
    n, lab = cv2.connectedComponents((seed | soft).astype(np.uint8), connectivity=4)
    reached = np.zeros(n, bool)
    reached[np.unique(lab[seed])] = True
    reached[0] = False
    return despeckle(((d > tol) & ~reached[lab]).astype(np.uint8))


def group(m, gx=13, gy=4, min_area=260):
    """Connected groups of marked pixels; words on one line join, lines stay apart."""
    d = cv2.dilate(m, np.ones((2 * gy + 1, 2 * gx + 1), np.uint8))
    _, lab, stats, _ = cv2.connectedComponentsWithStats(d, connectivity=8)
    items = []
    for i, (x, y, w, h, _) in enumerate(stats):
        if i == 0:
            continue
        sub = m[y:y + h, x:x + w] * (lab[y:y + h, x:x + w] == i)  # the marked pixels of this group only
        if sub.sum() < 40:
            continue
        ys, xs = np.nonzero(sub)
        b = [x + xs.min(), y + ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1]
        if b[2] * b[3] >= min_area:
            items.append((b, sub[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8)))
    return items


def merge_items(items):
    """merge_boxes for (box, own mask) pairs. Each piece joins exactly one group, so a small element
    that sits inside a large web's box is never also part of the web. Words of one line join; solid
    pieces side by side (cards in a row) do not."""
    groups = [([list(b)], [k]) for k, (b, _) in enumerate(items)]
    bbox = lambda bs: [min(b[0] for b in bs), min(b[1] for b in bs),
                       max(b[0] + b[2] for b in bs) - min(b[0] for b in bs), max(b[1] + b[3] for b in bs) - min(b[1] for b in bs)]
    fill = lambda g: sum(items[k][1].sum() for k in g[1]) / max(1, sum(items[k][0][2] * items[k][0][3] for k in g[1]))

    def touch(p, q, solid):
        ix = min(p[0] + p[2], q[0] + q[2]) - max(p[0], q[0])
        iy = min(p[1] + p[3], q[1] + q[3]) - max(p[1], q[1])
        small, big = sorted([p[2] * p[3], q[2] * q[3]])
        if ix > 0 and iy > 0 and ix * iy > 0.3 * small and big < 8 * small:
            return True
        hp, hq = p[3], q[3]
        return (not solid and iy > 0.6 * min(hp, hq) and max(hp, hq) < 1.6 * min(hp, hq) and -ix < 0.9 * min(hp, hq))

    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if touch(bbox(groups[i][0]), bbox(groups[j][0]), fill(groups[i]) > 0.6 and fill(groups[j]) > 0.6):
                    groups[i] = (groups[i][0] + groups[j][0], groups[i][1] + groups[j][1])
                    del groups[j]
                    changed = True
                    break
            if changed:
                break
    out = []
    for bs, ks in groups:
        x, y, w, h = bbox(bs)
        mk = np.zeros((h, w), np.uint8)
        for k in ks:
            (bx, by, bw, bh), sub = items[k]
            mk[by - y:by - y + bh, bx - x:bx - x + bw] |= sub
        out.append(([x, y, w, h], mk))
    return out


def drop_textures(m):
    """Grids, rules and hairline patterns span the card at low density: they stay in the plate."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    H0, W0 = m.shape
    out = m.copy()
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if (w > 0.5 * W0 or h > 0.5 * H0) and area < 0.08 * w * h:
            out[lab == i] = 0
    return out


def merge_boxes(boxes, gap):
    """Join boxes that overlap a lot, and the words of one line."""
    def touch(p, q):
        ix = min(p[0] + p[2], q[0] + q[2]) - max(p[0], q[0])
        iy = min(p[1] + p[3], q[1] + q[3]) - max(p[1], q[1])
        small, big = sorted([p[2] * p[3], q[2] * q[3]])
        if ix > 0 and iy > 0 and ix * iy > 0.3 * small and big < 8 * small:
            return True  # pieces of one thing; a small element inside a large web's box stays separate
        # same line: similar height, mostly side by side, a word gap apart
        hp, hq = p[3], q[3]
        if iy > 0.6 * min(hp, hq) and max(hp, hq) < 1.6 * min(hp, hq) and -ix < 0.9 * min(hp, hq):
            return True
        return False
    boxes = [list(b) for b in boxes]
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if touch(boxes[i], boxes[j]):
                    p, q = boxes[i], boxes[j]
                    x0, y0 = min(p[0], q[0]), min(p[1], q[1])
                    x1, y1 = max(p[0] + p[2], q[0] + q[2]), max(p[1] + p[3], q[1] + q[3])
                    boxes[i] = [x0, y0, x1 - x0, y1 - y0]
                    del boxes[j]
                    changed = True
                    break
            if changed:
                break
    return boxes


def fill_holes(m):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(m, np.uint8)
    cv2.drawContours(out, cs, -1, 1, -1)
    return out


def bands(m):
    """Runs of rows that contain marked pixels: text lines."""
    rows = m.sum(1) > 0
    out, start = [], None
    for i, r in enumerate(list(rows) + [False]):
        if r and start is None:
            start = i
        elif not r and start is not None:
            out.append([start, i])
            start = None
    return out


def dotted(bs, m):
    """Lines of a text layer (m: its own pixels, cropped to its box): on a line with no ascenders the dots over
    i and j float as their own short band of small round blobs, and belong to the line below."""
    out, k = [list(b) for b in bs], 0
    while k + 1 < len(out):
        (a0, a1), (b0, b1) = out[k], out[k + 1]
        g = b1 - b0
        if a1 - a0 < 0.3 * g and b0 - a1 < 0.4 * g:
            _, _, st, _ = cv2.connectedComponentsWithStats(m[a0:a1].astype(np.uint8), connectivity=8)
            _, _, body, _ = cv2.connectedComponentsWithStats(m[b0:b1].astype(np.uint8), connectivity=8)
            st, body = st[1:], body[1:]
            st = st[st[:, 4] >= max(6, 0.004 * g * g)]  # paper grain and JPEG specks are not dots
            # each dot sits over a stem about as narrow as itself (the i or the j), not over a wide letter: a third of the
            # way down the line, the run of ink under the dot's centre is short (tight tracking can join the letters)
            row = m[b0 + max(1, int(0.33 * g))] > 0
            def stem(d):
                c = int(d[0] + d[2] / 2)
                if c >= len(row) or not row[c]:
                    return False
                l, r = c, c
                while l > 0 and row[l - 1]: l -= 1
                while r + 1 < len(row) and row[r + 1]: r += 1
                return r - l + 1 <= 2 * d[2]
            if len(st) and (st[:, 2:4] <= 0.35 * g).all() and (st[:, 2:4] >= 0.1 * g).all() \
                    and ((st[:, 2] / st[:, 3] > 0.5) & (st[:, 2] / st[:, 3] < 2)).all() and all(stem(d) for d in st):
                out[k:k + 2] = [[a0, b1]]
                continue
        k += 1
    return out


def columns(m, min_gap):
    """Split a line into parts at column gaps of at least min_gap pixels."""
    cols = m.sum(0) > 0
    parts, start, gap, end = [], None, 0, 0
    for i, c in enumerate(list(cols) + [False] * (min_gap + 1)):
        if c:
            if start is None:
                start = i
            gap, end = 0, i + 1
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                parts.append([start, end - start])
                start = None
    return parts


def features(img, m, box):
    x, y, w, h = box
    crop, mm = img[y:y + h, x:x + w], m[y:y + h, x:x + w]
    filled = fill_holes(mm)
    _, _, st, _ = cv2.connectedComponentsWithStats(mm, connectivity=8)
    comps = st[1:][st[1:, 4] >= 6]
    if len(comps):
        comps = comps[comps[:, 4] >= 0.03 * comps[:, 4].max()]  # specks are not glyphs
    pix = crop[mm > 0]
    dom = mode_colour(pix)[0] if len(pix) else np.zeros(3)
    mono = (dist(pix, dom) < 60).mean() if len(pix) else 0
    hsv = cv2.cvtColor(dom.reshape(1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2HSV)[0, 0]
    inner = crop[filled > 0]
    ell = np.zeros_like(mm)
    cv2.ellipse(ell, (w // 2, h // 2), (max(1, w // 2), max(1, h // 2)), 0, 0, 360, 1, -1)
    union = ((ell > 0) | (filled > 0)).sum()
    q = inner.astype(int) // 32
    ncol = len(np.unique(q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2])) if len(inner) else 0
    return {
        "fill": float(mm.mean()), "solid": float(filled.mean()), "ncc": int(len(comps)),
        "comp_h": float(np.median(comps[:, 3])) if len(comps) else 0.0,
        "mono": float(mono), "ncol": int(ncol),
        "inner_std": float(inner.std()) if len(inner) else 0.0,
        "fg_std": float(pix.std()) if len(pix) else 0.0,
        "ellipse": float(((ell > 0) & (filled > 0)).sum() / max(1, union)),
        "tone": "#%02x%02x%02x" % tuple(int(v) for v in dom), "tone_rgb": [int(v) for v in dom],
        "sat": float(hsv[1]) / 255, "val": float(hsv[2]) / 255,
        "bands": bands(mm), "comps": comps,
    }


def thin(m):
    """Zhang-Suen thinning: a one-pixel skeleton of a mask."""
    s = np.pad((m > 0).astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p = [np.roll(np.roll(s, -dy, 0), -dx, 1) for dy, dx in
                 ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))]  # P2..P9, clockwise
            b = sum(p)
            a = sum(((p[i] == 0) & (p[(i + 1) % 8] == 1)) for i in range(8))
            if step == 0:
                c = (p[0] * p[2] * p[4] == 0) & (p[2] * p[4] * p[6] == 0)
            else:
                c = (p[0] * p[2] * p[6] == 0) & (p[0] * p[4] * p[6] == 0)
            kill = (s == 1) & (b >= 2) & (b <= 6) & (a == 1) & c
            if kill.any():
                s[kill] = 0
                changed = True
        if not changed:
            return s[1:-1, 1:-1]


def arrow_dir(m):
    """Direction from an arrow's tail to its head, as a unit vector, or None for a line without a head.
    On the skeleton, the head's two barbs end close together; the tail is the endpoint far from the others."""
    sk = thin(m)
    nb = sum(np.roll(np.roll(sk, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - sk
    ys, xs = np.nonzero((sk == 1) & (nb == 1))
    if len(xs) != 3:
        return None
    size = max(m.shape)
    e = np.stack([xs, ys], 1).astype(float)
    d = np.hypot(*(e[:, None] - e[None]).transpose(2, 0, 1))
    i, j = np.unravel_index(np.argmin(d + np.eye(3) * 1e9), d.shape)
    tail = 3 - i - j
    if d[i, j] > 0.25 * size or min(d[tail, i], d[tail, j]) < 0.5 * size:
        return None  # no clear head
    v = (e[i] + e[j]) / 2 - e[tail]
    n = float(np.hypot(*v))
    return [round(float(v[0]) / n, 3), round(float(v[1]) / n, 3)]


def textlike(f, box):
    w = box[2]
    if f["ncc"] < 2 or f["fill"] > 0.62 or not f["bands"] or f["mono"] < (0.4 if f["ncc"] >= 8 else 0.55):
        return False
    hs = f["comps"][:, 3]
    regular = ((hs > 0.35 * f["comp_h"]) & (hs < 2.2 * f["comp_h"])).mean() > 0.7
    line_h = max(b[1] - b[0] for b in f["bands"])
    return regular and line_h < 170 and w > 1.2 * line_h


def classify(f, box):
    x, y, w, h = box
    area = w * h / (W * H)
    aspect = w / h
    if min(w, h) <= 10 or (max(aspect, 1 / aspect) >= 6 and f["solid"] < 0.4 and f["ncc"] <= 3):
        return "stroke", "thin and long"
    if f["ncc"] <= 2 and f["fill"] < 0.18 and f["mono"] > 0.6 and max(w, h) > 80 and f["solid"] < 0.5:  # thin: edges are a big share
        return "stroke", "one drawn line or curve"
    if 0.78 <= aspect <= 1.28 and f["ellipse"] > 0.86 and min(w, h) >= 48:
        if f["ncol"] > 18 or f["inner_std"] > 34:
            return "avatar", "round, with photo detail"
        return "shape", "round, one colour"
    if textlike(f, box):
        return "text", f"{f['ncc']} glyphs in one colour"
    if f["solid"] > 0.82 and aspect >= 1.8 and h <= 96 and f["inner_std"] > 14:
        return "pill", "solid rounded bar with content"
    if f["solid"] > 0.86 and (area >= 0.035 or f["ncol"] > 60 and f["inner_std"] > 40):
        if f["ncol"] > 60 and f["inner_std"] > 40 and f["ncc"] <= 12:
            return "photo", "solid rectangle, many colours"
        if area >= 0.035:
            return "panel", "large solid surface"
    single = f["mono"] > 0.85 or (f["ncol"] <= 10 and f["inner_std"] < 30)
    if max(w, h) <= 150:
        if single and f["solid"] - f["fill"] < 0.08:
            return "shape", "small, one colour"
        return "icon", "small graphic with detail"
    if single:
        return "shape", "one-colour form"
    return "illustration", "multicolour graphic"


def ocr_lines(crop):
    """Text lines in a picture, from Tesseract when it is installed (None when it is not)."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        return None
    words = []
    grey = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    for g in (grey, 255 - grey):  # dark type on light and light type on dark
        try:
            d = pytesseract.image_to_data(Image.fromarray(g), config="--psm 11", output_type=pytesseract.Output.DICT)
        except Exception:  # missing language data and the like: carry on without reading
            return None
        for i, t in enumerate(d["text"]):
            t = t.strip()
            if float(d["conf"][i]) >= 62 and len(t) >= 2 and sum(c.isalnum() for c in t) >= 2 and d["height"][i] >= 9:
                words.append([d["left"][i], d["top"][i], d["width"][i], d["height"][i]])
    lines = []
    for wd in sorted(words, key=lambda b: (b[1] + b[3] / 2, b[0])):
        for L in lines:
            if abs((L[1] + L[3] / 2) - (wd[1] + wd[3] / 2)) < 0.4 * max(L[3], wd[3]) and wd[0] - (L[0] + L[2]) < 1.2 * max(L[3], wd[3]) and L[0] - (wd[0] + wd[2]) < 1.2 * max(L[3], wd[3]):
                x0, y0 = min(L[0], wd[0]), min(L[1], wd[1])
                L[:] = [x0, y0, max(L[0] + L[2], wd[0] + wd[2]) - x0, max(L[1] + L[3], wd[1] + wd[3]) - y0]
                break
        else:
            lines.append(list(wd))
    return lines


def detect(img, B, tol, offset, depth, backdrops, m=None, gaps=(13, 4), region=None):
    if m is None:
        m = drop_textures(foreground(img, B, tol))
    if region is not None:
        m = m & region  # only what lies on this surface
    oh, ow = img.shape[:2]
    out = []
    for b, own in merge_items(group(m, *gaps)):
        x, y, w, h = b
        if (w > 0.92 * ow and h < 6) or (h > 0.92 * oh and w < 6):
            continue  # ruled lines and grids belong to the background
        dense = own.mean()
        if w * h > 0.35 * W * H and depth == 0:  # smaller cards (a report, a poster) move as one piece
            crop = img[y:y + h, x:x + w]
            surface, _ = mode_colour(crop)
            own_surface = dist(surface, np.median(B[y:y + h, x:x + w].reshape(-1, 3), 0)) > tol
            if own_surface and (dist(crop, surface) < tol).mean() > 0.45:
                # a window or big card: its surface becomes background too, and what lies on it is searched again
                Bc = B[y:y + h, x:x + w]
                Bc = np.where((dist(crop, surface) < tol)[..., None], surface.astype(np.float32), Bc)
                inner = cv2.erode(fill_holes(own), np.ones((5, 5), np.uint8))
                found = detect(crop, Bc, tol, (offset[0] + x, offset[1] + y), 1, backdrops, region=inner)
                if found:
                    backdrops.append([x + offset[0], y + offset[1], w, h])
                    out += found
                    continue
                # nothing on it: it is an element itself (a big blob, a plain card)
        if w * h > 0.22 * W * H and gaps[0] > 2:
            # a big group may be separate elements that happen to sit close: group them again with tighter gaps
            out += detect(img[y:y + h, x:x + w], B[y:y + h, x:x + w], tol, (offset[0] + x, offset[1] + y), depth,
                          backdrops, m=own.copy(), gaps=(5, 2) if gaps[0] > 5 else (2, 1))
            continue
        if w * h > 0.22 * W * H and dense < 0.3:
            continue  # one sparse connected web across the card (grass, a frame, a pattern): it stays in the plate
        if w * h > 0.35 * W * H and dense >= 0.3:
            # a full-card image or scene: it stays in the plate, and only the crisp things on it
            # (type, logos, buttons) become layers, found by their contrast with their surroundings
            crop = np.ascontiguousarray(img[y:y + h, x:x + w])
            med = cv2.medianBlur(crop, 31)
            backdrops.append([x + offset[0], y + offset[1], w, h, "scene"])
            lines = ocr_lines(crop) or []
            # glyphs near each read line, against that line's own surroundings
            M = np.zeros((h, w), np.uint8)
            for bx, by, bw, bh in lines:
                lx, ly = max(0, bx - int(0.15 * bh)), max(0, by - int(0.3 * bh))
                lx1, ly1 = min(w, bx + bw + int(0.15 * bh)), min(h, by + int(1.3 * bh))
                region = crop[ly:ly1, lx:lx1]
                ring = np.concatenate([region[:2].reshape(-1, 3), region[-2:].reshape(-1, 3), region[:, :2].reshape(-1, 3), region[:, -2:].reshape(-1, 3)])
                M[ly:ly1, lx:lx1] |= (dist(region, np.median(ring, 0)) > 1.2 * tol).astype(np.uint8)
            # every glyph pixel belongs to the read line whose middle is nearest, so tight leading cannot mix lines
            own = [np.zeros((h, w), np.uint8) for _ in lines]
            ys, xs = np.nonzero(M)
            if len(lines) and len(ys):
                cost = np.stack([np.abs(ys - (by + bh / 2)) + np.where((xs >= bx - bh) & (xs <= bx + bw + bh), 0, 1e6)
                                 for bx, by, bw, bh in lines])
                best = cost.argmin(0)
                for k, (bx, by, bw, bh) in enumerate(lines):
                    sel = (best == k) & (cost[k] < bh)
                    own[k][ys[sel], xs[sel]] = 1
            for o in own:
                if o.sum() < 20:
                    continue
                ys, xs = np.nonzero(o)
                bx, by, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
                out.append(([bx + x + offset[0], by + y + offset[1], bx1 - bx, by1 - by], o[by:by1, bx:bx1], "ocr"))
            continue
        out.append(([x + offset[0], y + offset[1], w, h], own, False))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card")
    ap.add_argument("out")
    ap.add_argument("--tol", type=int, default=40, help="colour distance from the background that counts as content")
    ap.add_argument("--max", type=int, default=18, help="most layers to keep; the smallest extras stay in the plate")
    ap.add_argument("--style", default="auto", choices=["auto", "rebuild", "living"])
    ap.add_argument("--energy", default="lively", choices=["calm", "lively", "bold"])
    a = ap.parse_args()
    a.max = min(a.max, 250)  # the owner map is 8-bit

    img = load_card(a.card)
    os.makedirs(a.out, exist_ok=True)
    Image.fromarray(img).save(os.path.join(a.out, "card.jpg"), quality=95)
    B, flat = background(img, a.tol)
    backdrops = []
    found = detect(img, B, a.tol if flat else int(a.tol * 1.4), (0, 0), 0, backdrops)

    # pieces that lie on one line Tesseract read are one line of type, however the grouping split them
    read = ocr_lines(img)
    marked = foreground(img, B, a.tol if flat else int(a.tol * 1.4))
    for rx, ry, rw, rh in read or []:
        lx0, ly0, lx1, ly1 = rx - rh, ry - rh // 2, rx + rw + rh, ry + rh + rh // 2  # Tesseract may miss an end letter
        on = [k for k, ((x, y, w, h), _, loose) in enumerate(found)
              if loose != "ocr" and h < 2 * rh and lx0 <= x + w / 2 <= lx1 and ly0 <= y + h / 2 <= ly1]
        if not on:
            continue
        # the line's own pixels: its pieces, plus free marked pixels inside the read box (a letter that touched
        # a frame line and went to the background with it)
        mk = np.zeros((H, W), np.uint8)
        for k in on:
            (x, y, w, h), sub, _ = found[k]
            mk[y:y + h, x:x + w] |= sub
        taken = np.zeros((H, W), bool)
        for k, ((x, y, w, h), sub, _) in enumerate(found):
            if k not in on:
                taken[y:y + h, x:x + w] |= sub > 0
        tx0, ty0 = max(0, rx - rh // 4), max(0, ry - rh // 8)  # tight vertically: a frame line nearby must not join
        tx1, ty1 = min(W, rx + rw + rh), min(H, ry + rh + rh // 8)
        mk[ty0:ty1, tx0:tx1] |= (marked[ty0:ty1, tx0:tx1] > 0) & ~taken[ty0:ty1, tx0:tx1]
        ys, xs = np.nonzero(mk)
        b_ = [xs.min(), ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1]
        found = [f_ for k, f_ in enumerate(found) if k not in on] + [(b_, mk[b_[1]:b_[1] + b_[3], b_[0]:b_[0] + b_[2]], False)]

    full = np.zeros((H, W), np.uint8)
    for (x, y, w, h), sub, _ in found:
        full[y:y + h, x:x + w] |= sub

    def own_full(box, sub):  # a layer's own pixels, card-sized
        o = np.zeros((H, W), np.uint8)
        x, y, w, h = box
        o[y:y + h, x:x + w] = sub[:h, :w]
        return o

    layers = []
    for box, sub, loose in found:
        own = own_full(box, sub)
        f = features(img, own, box)
        kind, why = ("text", "a text line Tesseract read") if loose == "ocr" else classify(f, box)
        if loose and kind not in {"text", "pill"}:
            continue  # on a scene, only type and marks move; the rest is part of the picture
        layers.append({"box": box, "kind": kind, "why": why, "f": f, "own": own, "scene": loose == "ocr"})

    # what Tesseract can read is text, even in two colours or with a logo beside it
    inked = None
    if read:
        inked = np.zeros((H, W), bool)  # where read words are, a little padded for ascenders and tails
        for rx, ry, rw, rh in read:
            inked[max(0, ry - rh // 3):ry + rh + rh // 3, max(0, rx - rh // 4):rx + rw + rh // 4] = True
        for L in layers:
            if L["kind"] in {"illustration", "shape", "icon"} and L["own"].sum():
                # most of its pixels are read words (a two-colour headline, a logo with its name): it is text
                share = inked[L["own"] > 0].mean()
                if share > 0.7:
                    L["kind"], L["why"] = "text", "text Tesseract read"
                elif share > 0.35:
                    L["named"] = True  # partly read: maybe a logo with its name, tried as a lockup below

    # the dots over i and j on a line with no ascenders are a group of their own: they belong to the line below
    for D in list(layers):
        x, y, w, h = D["box"]
        cs = D["f"]["comps"]
        if not len(cs) or D["kind"] not in {"text", "shape", "icon"}:
            continue
        for T in layers:
            if T is D or T["kind"] != "text" or not T["f"]["comp_h"]:
                continue
            tx, ty, tw, th = T["box"]
            g = T["f"]["comp_h"]  # the line's glyph height: a dot is a small fraction of a letter, not of the block
            tops = [ty + b0 for b0, _ in T["f"]["bands"]]  # any line of a block, not only its first
            if (any(-2 <= t - (y + h) <= 0.5 * g for t in tops) and h <= 0.45 * g and tx - 0.1 * g <= x and x + w <= tx + tw + 0.1 * g
                    and (cs[:, 2] <= 0.45 * g).all() and (cs[:, 3] <= 0.45 * g).all()):
                T["own"] = T["own"] | D["own"]
                ys, xs = np.nonzero(T["own"])
                T["box"] = [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)]
                T["f"] = features(img, T["own"], T["box"])
                layers.remove(D)
                break

    # text: one layer per line; a mark at the start of a line becomes its own logo layer
    split = []
    for L in layers:
        lockup = (L["kind"] in {"illustration", "shape"} and (L["f"]["mono"] > 0.75 or L.get("named"))
                  and L["box"][2] > 2.2 * L["box"][3] and len(L["f"]["bands"]) == 1)
        if L["kind"] != "text" and not lockup:
            split.append(L)
            continue
        x, y, w, h = L["box"]
        for b0, b1 in dotted(L["f"]["bands"], L["own"][y:y + h, x:x + w]):
            if b1 - b0 < 6:
                continue
            xs = np.nonzero(L["own"][y + b0:y + b1, x:x + w].sum(0))[0]
            lb = [x + xs.min(), y + b0, xs.max() - xs.min() + 1, b1 - b0]
            lown = np.zeros((H, W), np.uint8)
            lown[lb[1]:lb[1] + lb[3], lb[0]:lb[0] + lb[2]] = L["own"][lb[1]:lb[1] + lb[3], lb[0]:lb[0] + lb[2]]
            lf = features(img, lown, lb)
            sub = lown[lb[1]:lb[1] + lb[3], lb[0]:lb[0] + lb[2]]
            parts = columns(sub, max(4, int(0.22 * lb[3])))
            if len(parts) >= 2 and not L.get("scene"):  # type read off a picture is text all the way
                (p0, pw), rest = parts[0], parts[1:]
                rows = np.nonzero(sub[:, p0:p0 + pw].sum(1))[0]
                mark = [lb[0] + p0, lb[1] + rows.min(), pw, rows.max() - rows.min() + 1]
                mm = sub[rows.min():rows.max() + 1, p0:p0 + pw] > 0
                rs, re_ = rest[0][0], rest[-1][0] + rest[-1][1]
                rmask = sub[:, rs:re_] > 0
                rrows = np.nonzero(rmask.sum(1))[0]
                tall = rrows.max() - rrows.min() + 1  # ascender to descender of the words
                mpix = img[mark[1]:mark[1] + mark[3], mark[0]:mark[0] + mark[2]][mm]
                rpix = img[lb[1]:lb[1] + lb[3], lb[0] + rs:lb[0] + re_][rmask]
                odd = (mark[3] >= 1.2 * tall or dist(mpix.mean(0), rpix.mean(0)) > 90
                       or (mm.mean() > 0.55 and mark[3] >= 1.05 * tall))
                rb_ = [lb[0] + rs, lb[1], re_ - rs, lb[3]]
                rown = np.zeros((H, W), np.uint8)
                rown[rb_[1]:rb_[1] + rb_[3], rb_[0]:rb_[0] + rb_[2]] = lown[rb_[1]:rb_[1] + rb_[3], rb_[0]:rb_[0] + rb_[2]]
                rf = features(img, rown, rb_)
                # a word in another colour ("is moving."), not a mark: glyphs side by side, no taller than the words,
                # and (when Tesseract is there) read as words. Either alone also fits some logos (Tailwind, Supabase).
                word = len(columns(mm.astype(np.uint8), 2)) >= 2 and mark[3] <= 1.1 * tall
                if word and inked is not None:
                    word = inked[mark[1]:mark[1] + mark[3], mark[0]:mark[0] + mark[2]][mm].mean() > 0.6
                if (odd and not word and 0.5 < mark[2] / mark[3] < 1.9 and re_ - rs > 1.5 * mark[2]
                        and (not lockup or textlike(rf, rb_))):
                    mown = np.zeros((H, W), np.uint8)
                    mown[mark[1]:mark[1] + mark[3], mark[0]:mark[0] + mark[2]] = lown[mark[1]:mark[1] + mark[3], mark[0]:mark[0] + mark[2]]
                    split.append({"box": mark, "kind": "logo", "why": "mark at the start of a wordmark", "f": lf, "own": mown})
                    lb, lf, lown = rb_, rf, rown
                    lf["wordmark"] = True
                    lockup = False
            if lockup:  # no mark and no text found: it stays one graphic
                split.append(L)
                break
            split.append({"box": lb, "kind": "text", "why": L["why"], "f": lf, "own": lown})
    layers = split

    # a small graphic just left of a text line, about as tall, is that line's logo mark
    for L in layers:
        if L["kind"] not in {"icon", "avatar", "shape"}:
            continue
        x, y, w, h = L["box"]
        for T in layers:
            if T["kind"] != "text":
                continue
            tx, ty, tw, th = T["box"]
            gap = tx - (x + w)
            if 0 <= gap < 1.3 * th and 0.7 * th <= h <= 2.4 * th and abs((y + h / 2) - (ty + th / 2)) < 0.35 * h:
                L["kind"], L["why"] = "logo", "mark beside a wordmark"
                T["f"]["wordmark"] = True

    # type sizes are relative to the card: the biggest lines are the headline
    texts = [L for L in layers if L["kind"] == "text"]
    for L in texts:  # cap height: tall glyphs of the line, so an inline pill or avatar does not count
        hs = L["f"]["comps"][:, 3] if len(L["f"]["comps"]) else np.array([L["box"][3]])
        L["cap"] = float(min(np.percentile(hs, 80) * 1.25, L["box"][3]))
    if texts:
        top = max(L["cap"] for L in texts)
        for L in texts:
            h = L["cap"]
            if (h >= 0.72 * top and (h >= 44 or len(texts) == 1)) or h >= 64:
                L["kind"] = "headline"
            elif h < 24:
                L["kind"] = "label"

    # "text" under headline size that Tesseract cannot read is texture (eyelashes, fabric, UI noise): it stays in the plate
    if read is not None:
        def confirmed(L):
            x, y, w, h = L["box"]
            return sum(max(0, min(x + w, r[0] + r[2]) - max(x, r[0])) * max(0, min(y + h, r[1] + r[3]) - max(y, r[1])) for r in read) > 0.4 * w * h
        layers = [L for L in layers if not (L["kind"] in TEXT_KINDS and L["box"][3] < 44 and not confirmed(L))]
        texts = [L for L in layers if L["kind"] in TEXT_KINDS]

    # lines of one block read as one: a line between headline lines of the same size is headline too
    for _ in range(2):
        for L in texts:
            for M in texts:
                if L is M or M["kind"] != "headline" or L["kind"] == "headline":
                    continue
                near = abs(L["box"][1] - (M["box"][1] + M["box"][3])) < 0.8 * M["box"][3] or abs(M["box"][1] - (L["box"][1] + L["box"][3])) < 0.8 * M["box"][3]
                if near and L["cap"] > 0.7 * M["cap"]:
                    L["kind"] = "headline"

    # lines of one paragraph (same left edge, same line height, stacked) share one kind: the larger of theirs
    rank = {"label": 0, "text": 1, "headline": 2}
    for _ in range(2):
        for L in texts:
            for M in texts:
                if L is M or L["kind"] not in rank or M["kind"] not in rank:
                    continue
                lx, ly, lw, lh = L["box"]; mx, my, mw, mh = M["box"]
                stacked = 0 <= my - (ly + lh) < 0.8 * lh
                if stacked and abs(lx - mx) <= 6 and max(lh, mh) < 1.3 * min(lh, mh):
                    top_kind = max(L["kind"], M["kind"], key=rank.get)
                    L["kind"] = M["kind"] = top_kind

    # keep the biggest elements when there are too many; small leftovers stay in the plate
    if len(layers) > a.max:
        layers.sort(key=lambda L: -(L["box"][2] * L["box"][3]) * (3 if L["kind"] in TEXT_KINDS else 1))
        layers = layers[:a.max]

    # reading order: rows top to bottom, left to right inside a row
    layers.sort(key=lambda L: (round((L["box"][1] + L["box"][3] / 2) / 70), L["box"][0]))

    out_layers, counts = [], {}
    for L in layers:
        k = L["kind"]
        counts[k] = counts.get(k, 0) + 1
        x, y, w, h = [int(v) for v in L["box"]]
        item = {"id": f"{k}{counts[k]}", "kind": k, "box": [x, y, w, h]}
        if k in TEXT_KINDS:
            sub = L["own"][y:y + h, x:x + w]
            words = columns(sub, max(4, int(0.22 * h)))
            if k == "headline" and len(words) == 1 and w / h < 9:
                letters = columns(sub, 1)
                if 2 <= len(letters) <= 16:
                    item["letters"] = True
                    words = letters
            if len(words) > 1:
                item["parts"] = [[int(p), int(q)] for p, q in words]
        f = L["f"]
        if k == "stroke":
            d = arrow_dir(L["own"][y:y + h, x:x + w])
            if d:
                item["dir"] = d  # an arrow draws from its tail to its head
        if f.get("wordmark"):
            item["wordmark"] = True
        item["ink"] = f["tone"]
        if k in TEXT_KINDS | {"pill", "shape", "logo"} and f["sat"] > 0.45 and f["val"] > 0.45:
            item["tone"] = f["tone"]  # an accent colour: sheen and glows pick it up
        if k in {"photo", "panel", "illustration", "avatar"}:
            ring = np.concatenate([img[max(0, y - 9):max(0, y - 4), x:x + w].reshape(-1, 3), img[y + h + 4:y + h + 9, x:x + w].reshape(-1, 3),
                                   img[y:y + h, max(0, x - 9):max(0, x - 4)].reshape(-1, 3), img[y:y + h, x + w + 4:x + w + 9].reshape(-1, 3)])
            rb = np.concatenate([B[max(0, y - 9):max(0, y - 4), x:x + w].reshape(-1, 3), B[y + h + 4:y + h + 9, x:x + w].reshape(-1, 3),
                                 B[y:y + h, max(0, x - 9):max(0, x - 4)].reshape(-1, 3), B[y:y + h, x + w + 4:x + w + 9].reshape(-1, 3)])
            on_bg = (dist(ring, rb) < a.tol * 1.4).mean() if len(ring) else 1
            if w * h > 0.2 * W * H or on_bg < 0.75:
                item["settle"] = True  # its hole could not be filled cleanly: it moves in place
        item["why"] = L["why"]
        out_layers.append(item)

    # each marked pixel belongs to exactly one layer: the element it was found in
    owner = np.zeros((H, W), np.uint8)
    for n, (L, src) in enumerate(zip(out_layers, layers), 1):
        owner[(src["own"] > 0) & (owner == 0)] = n
        L["mask"] = n
    Image.fromarray(owner).save(os.path.join(a.out, "cut-mask.png"))

    config = {
        "image": "card.jpg", "layerImage": "layers.png", "cuts": "cuts/", "glyphs": "glyphs.png",
        "width": W, "height": H, "loop": 4.0,
        "style": a.style, "energy": a.energy,
        # type on a large picture: refills behind it never look clean, so the card lives in place
        "background": "detailed" if any(len(b) > 4 and b[2] * b[3] > 0.45 * W * H for b in backdrops) else "flat" if flat else "graded",
        "plate": {"mode": "image", "src": "plate.png"},
        "layers": out_layers,
    }
    with open(os.path.join(a.out, "layers.js"), "w") as fh:
        fh.write("// Written by suggest_layers.py. Each layer's motion comes from its kind:\n")
        fh.write("// " + " | ".join(KINDS) + "\n")
        fh.write("// style: auto | rebuild | living    energy: calm | lively | bold\n")
        fh.write("window.OG = " + json.dumps(config, indent=1) + ";\n")
    with open(os.path.join(a.out, "cut.json"), "w") as fh:
        json.dump({"flat": flat}, fh)

    prev = Image.fromarray(img).convert("RGB")
    d = ImageDraw.Draw(prev)
    for b in backdrops:
        d.rectangle([b[0], b[1], b[0] + b[2], b[1] + b[3]], outline=(128, 128, 128), width=1)
        if len(b) > 4:
            d.text((b[0] + 6, b[1] + 4), "scene (stays in the plate)", fill=(128, 128, 128))
    colours = {"headline": (255, 40, 90), "text": (255, 140, 0), "label": (230, 200, 0), "logo": (0, 200, 255),
               "pill": (170, 80, 255), "icon": (0, 200, 120), "avatar": (255, 80, 200), "photo": (40, 120, 255),
               "panel": (60, 60, 255), "illustration": (0, 170, 170), "shape": (120, 220, 0), "stroke": (255, 255, 255)}
    for L in out_layers:
        x, y, w, h = L["box"]
        c = colours[L["kind"]]
        d.rectangle([x, y, x + w, y + h], outline=c, width=3)
        for px, pw in L.get("parts", []):
            d.line([x + px, y + h + 3, x + px + pw, y + h + 3], fill=c, width=2)
        d.rectangle([x, y - 15, x + 8 + 7 * len(L["id"]), y], fill=c)
        d.text((x + 4, y - 14), L["id"], fill=(0, 0, 0))
    prev.save(os.path.join(a.out, "layers-preview.png"))

    print(f"background {'flat' if flat else 'graded'}, {len(out_layers)} layers, {len(backdrops)} backdrop(s) -> {a.out}/layers.js")
    for L in out_layers:
        extra = f"  {len(L['parts'])} {'letters' if L.get('letters') else 'words'}" if "parts" in L else ""
        print(f"  {L['id']:<14} {L['kind']:<12} {str(L['box']):<22} {L['why']}{extra}")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_plate.py"), a.out], check=True)


if __name__ == "__main__":
    main()
