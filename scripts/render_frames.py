#!/usr/bin/env python3
"""Capture every frame of an OG card page that exposes window.render(t).

Usage: render_frames.py CARD.html OUT_DIR [--fps 60] [--seconds 4] [--scale 2]

Frames are written as OUT_DIR/f0000.png ... at the card size (1200x630 unless
window.OG says otherwise) times --scale. Works for template/og.html and
template/from-image.html.
Prints the right edge of each top-level element so you can check text
does not run into the portrait (keep a gap of 40 px or more).
"""
import argparse
import asyncio
import functools
import http.server
import os
import threading

from playwright.async_api import async_playwright


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--frames", help="comma-separated frame numbers to render only those (previews)")
    ap.add_argument("--root", help="folder to serve (default: the card's folder); use when the card loads files from a parent folder")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    # Serve the card's folder over http: from-image.html reads pixels from a canvas,
    # which Chrome blocks for file:// images.
    root = os.path.abspath(a.root) if a.root else os.path.dirname(os.path.abspath(a.card))
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=root)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    rel = os.path.relpath(os.path.abspath(a.card), root).replace(os.sep, "/")
    card = f"http://127.0.0.1:{server.server_address[1]}/{rel}"
    n = round(a.fps * a.seconds)
    frames = [int(x) for x in a.frames.split(",")] if a.frames else range(n)

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        page = await browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=a.scale)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(card)
        await page.evaluate("document.fonts.ready")
        await page.wait_for_timeout(300)
        if errors:
            raise SystemExit("page error: " + "; ".join(errors))
        await page.wait_for_function("!window.ready || window.readyDone === true", timeout=15000)
        size = await page.evaluate("window.OG ? [OG.width, OG.height] : [1200, 630]")
        await page.set_viewport_size({"width": size[0], "height": size[1]})
        await page.wait_for_timeout(1200)  # let images decode
        edges = await page.evaluate(
            "[...document.querySelectorAll('.el')].map(e => [e.id, Math.round(e.getBoundingClientRect().right)])"
        )
        print("right edges:", ", ".join(f"{i}={r}" for i, r in edges))
        plan = await page.evaluate("window.plan || null")
        if plan:  # what the template chose for each element
            for p_ in plan:
                print(f"  {p_['id']:<14} {p_['kind']:<12} {p_['motion']:<12} {p_['style']:<8} at {p_['at']:<5} {p_['accent']}")
        for i in frames:
            await page.evaluate(f"render({i / a.fps})")
            await page.screenshot(path=os.path.join(a.out, f"f{i:04d}.png"))
        await browser.close()
    server.shutdown()
    if errors:
        raise SystemExit("page error: " + "; ".join(errors))
    print(f"wrote {len(list(frames))} frames to {a.out}")


asyncio.run(main())
