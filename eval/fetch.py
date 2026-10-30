#!/usr/bin/env python3
"""Fetch the og:image of every site in eval/sites.txt into eval/cards/<name>.jpg (cover-cropped to 1200x630).

The card name is the site's main label (www.anthropic.com -> anthropic, deepmind.google -> deepmind). Cards that already
exist are kept. A site is skipped, with the reason printed, when it has no og:image or twitter:image, the image will not
download, or it is not a link card (narrower than 1.3:1 or under 600 px wide: a square logo is not what a preview shows).

Usage: python3 eval/fetch.py [--only name,name]
"""
import argparse
import html
import io
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def name_of(url):
    host = urllib.parse.urlparse(url).hostname or ""
    parts = [p for p in host.split(".") if p not in ("www",)]
    return parts[-2] if len(parts) >= 2 else parts[0]


def get(url, limit=8_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(limit), r.geturl()


def og_image(page, base):
    text = page.decode("utf-8", "ignore")
    for prop in ("og:image", "og:image:url", "og:image:secure_url", "twitter:image", "twitter:image:src"):
        for tag in re.findall(r"<meta\b[^>]*>", text, re.I):
            if re.search(r'(property|name)\s*=\s*["\']' + re.escape(prop) + r'["\']', tag, re.I):
                m = re.search(r'content\s*=\s*["\']([^"\']+)["\']', tag, re.I)
                if m:
                    return urllib.parse.urljoin(base, html.unescape(m.group(1).strip()))
    return None


def cover(im, w=1200, h=630):
    im = im.convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated card names")
    a = ap.parse_args()
    urls = [l.strip() for l in open(os.path.join(HERE, "sites.txt")) if l.strip().startswith("http")]
    os.makedirs(os.path.join(HERE, "cards"), exist_ok=True)
    got, skipped = [], []
    for url in urls:
        name = name_of(url)
        if a.only and name not in a.only.split(","):
            continue
        out = os.path.join(HERE, "cards", name + ".jpg")
        if os.path.exists(out):
            continue
        try:
            page, final = get(url, 2_000_000)
            src = og_image(page, final)
            if not src:
                skipped.append((name, "no og:image")); continue
            data, _ = get(src)
            im = Image.open(io.BytesIO(data))
            if im.width < 600 or im.width / im.height < 1.3:
                skipped.append((name, f"not a link card ({im.width}x{im.height})")); continue
            cover(im).save(out, quality=92)
            got.append(name)
            print(f"{name:<16} {im.width}x{im.height}  {src[:90]}", flush=True)
        except Exception as e:
            skipped.append((name, str(e)[:80]))
        time.sleep(0.5)  # polite: one site at a time
    print(f"\nfetched {len(got)}; skipped {len(skipped)}")
    for n, why in skipped:
        print(f"  skipped {n}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
