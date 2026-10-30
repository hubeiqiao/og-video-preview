#!/usr/bin/env python3
"""Data for the website, from the eval: site/media/sites.json (each card's domain and group, from eval/sites.txt and its
comment headers) and, with --boxes, site/media/boxes.json (the elements suggest_layers.py reads on each card, and on
the live cards of joespeaking.com and hubeiqiao.com, for the hero animation). The boxes take a few minutes.

Usage: python3 site/data.py [--boxes]
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "eval"))
from fetch import get, name_of  # noqa: E402  the card names and the polite download fetch.py uses

LIVE = {"joespeaking": "https://joespeaking.com/landing/og/home-en.jpg", "hubeiqiao": "https://hubeiqiao.com/share/og-home.jpg"}


def sites():
    out, group = {}, ""
    for line in open(os.path.join(ROOT, "eval", "sites.txt")):
        line = line.strip()
        if line.startswith("#"):
            m = re.match(r"#\s*(.+?)\s*\(\d{4}-\d\d-\d\d\)\s*$", line)
            if m:
                group = m.group(1)
        elif line.startswith("http"):
            name = name_of(line)
            if os.path.exists(os.path.join(ROOT, "eval", "cards", name + ".jpg")):
                host = urllib.parse.urlparse(line).hostname
                out[name] = {"domain": host[4:] if host.startswith("www.") else host, "group": group}
    return out


def boxes(names):
    py = sys.executable
    tmp = tempfile.mkdtemp(prefix="og-boxes-")
    srcs = {n: os.path.join(ROOT, "eval", "cards", n + ".jpg") for n in names}
    for n, url in LIVE.items():
        p = os.path.join(tmp, n + ".jpg")
        data, _ = get(url)
        open(p, "wb").write(data)
        srcs[n] = p

    def read(item):
        n, src = item
        out = os.path.join(tmp, n)
        subprocess.run([py, os.path.join(ROOT, "scripts", "suggest_layers.py"), src, out], check=True, capture_output=True)
        c = json.loads(re.search(r"window.OG = (.*);", open(os.path.join(out, "layers.js")).read(), re.S).group(1))
        L = [[l["kind"], l["box"]] for l in c["layers"] if l["box"][2] * l["box"][3] >= 900]
        L.sort(key=lambda b: -b[1][2] * b[1][3])
        return n, L[:14]
    with cf.ThreadPoolExecutor(4) as ex:
        return dict(ex.map(read, srcs.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boxes", action="store_true")
    a = ap.parse_args()
    s = sites()
    os.makedirs(os.path.join(ROOT, "site", "media"), exist_ok=True)
    json.dump(s, open(os.path.join(ROOT, "site", "media", "sites.json"), "w"), separators=(",", ":"))
    print(f"sites.json: {len(s)} cards")
    if a.boxes:
        b = boxes(list(s))
        json.dump(b, open(os.path.join(ROOT, "site", "media", "boxes.json"), "w"), separators=(",", ":"))
        print(f"boxes.json: {len(b)} cards")


if __name__ == "__main__":
    main()
