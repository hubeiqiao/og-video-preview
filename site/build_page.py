#!/usr/bin/env python3
"""Render crawlable page data and discovery files from the checked-in eval and docs.

Standard library only, so Pages needs no additional Python dependencies.
"""
import hashlib
import html
import json
import os
import re
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '_site'
BASE = os.environ.get('SITE_BASE', 'https://hubeiqiao.com/og-video-preview/')  # where the page is served
REPO = 'https://github.com/hubeiqiao/og-video-preview'
INSTALL = 'npx skills add hubeiqiao/og-video-preview'
DESCRIPTION = 'An open-source agent skill that turns any approved og:image into a looping og:video, so link previews move.'


def png(size):
    """Rasterize the existing amber circle mark, including alpha, without dependencies."""
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            inside = sum(((x + dx / 4 - size / 2) ** 2 + (y + dy / 4 - size / 2) ** 2) < (size * 6 / 16) ** 2
                         for dx in (0.5, 1.5, 2.5, 3.5) for dy in (0.5, 1.5, 2.5, 3.5))
            rows.extend((246, 185, 59, round(255 * inside / 16)))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', size, size, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def main():
    sites = json.loads((ROOT / 'site/media/sites.json').read_text())
    results = json.loads((ROOT / 'eval/results.json').read_text())
    by_name = {r['name']: r for r in results}
    result_order = {r['name']: i for i, r in enumerate(results)}
    # sites.json order is the canonical no-JS reading order; all rendered evals must be present.
    assert by_name.keys() <= sites.keys(), 'An eval result is missing from sites.json'
    names = [n for n in sites if n in by_name]
    passed = sum(bool(r['pass']) for r in results)
    layers = sum(r['layers'] for r in results)
    stats = f'{passed} of {len(results)} pass the checks · {layers} elements read · frame 0 equals the image on every card'
    tiles = []
    for name in names:
        domain = html.escape(sites[name]['domain'], quote=True)
        safe_name = html.escape(name, quote=True)
        tiles.append(f'<button class="tile" data-name="{safe_name}" data-index="{result_order[name]}" data-domain="{domain}" aria-label="Open the og:video of {domain}">'
                     f'<div class="media"><img data-src="media/posters/{safe_name}.webp" alt="" width="1200" height="630" loading="lazy" decoding="async"><noscript><img src="media/posters/{safe_name}.webp" alt="" loading="lazy" style="position:absolute;inset:0"></noscript></div>'
                     f'<span><i class="sr-only">{safe_name}: </i>{domain}</span></button>')
    # the questions people ask, from README.md and SKILL.md (site/faq.json); eval numbers filled in from the results
    faq = [{'q': f['q'], 'a': f['a'].format(sites=len(names), passed=passed)} for f in json.loads((ROOT / 'site/faq.json').read_text())]
    def answer(a):  # a date never breaks across lines
        return re.sub(r'(\d{4})-(\d\d)-(\d\d)', r'<span class="nw">\1-\2-\3</span>', html.escape(a))
    faq_html = '\n'.join(f'<details><summary><span>{html.escape(f["q"])}</span></summary><p>{answer(f["a"])}</p></details>' for f in faq)
    page = (ROOT / 'site/index.html').read_text().replace('{{BASE}}', BASE)
    page = page.replace('<!-- faq -->', faq_html)
    page = page.replace('<!-- eval-grid -->', '<div class="grid">' + '\n'.join(tiles) + '</div>')
    page = page.replace('Real sites. <span', f'{len(names)} real sites. <span')
    page = page.replace("Each card made by the skill from the site's own og:image.", stats)
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'SoftwareApplication', '@id': BASE + '#software', 'name': 'OG Video Preview',
         'url': BASE, 'description': DESCRIPTION, 'applicationCategory': 'DeveloperApplication',
         'operatingSystem': 'Requires Python 3, Google Chrome, ffmpeg and ffprobe',
         'license': 'https://opensource.org/license/mit/', 'codeRepository': REPO,
         'offers': {'@type': 'Offer', 'price': 0},
         'author': {'@id': 'https://hubeiqiao.com/#joe'}},
        {'@type': 'Person', '@id': 'https://hubeiqiao.com/#joe', 'name': 'Joe Hu', 'url': 'https://hubeiqiao.com',
         'sameAs': ['https://x.com/hubeiqiao', 'https://github.com/hubeiqiao']},
        {'@type': 'SoftwareSourceCode', '@id': BASE + '#code', 'name': 'og-video-preview', 'codeRepository': REPO,
         'programmingLanguage': ['Python', 'JavaScript'], 'license': 'https://opensource.org/license/mit/',
         'author': {'@id': 'https://hubeiqiao.com/#joe'}, 'targetProduct': {'@id': BASE + '#software'}},
        {'@type': 'FAQPage', '@id': BASE + '#faq', 'mainEntity': [{'@type': 'Question', 'name': f['q'],
         'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in faq]},
        {'@type': 'WebSite', '@id': BASE + '#website', 'url': BASE, 'name': 'OG Video Preview',
         'description': DESCRIPTION, 'about': {'@id': BASE + '#software'}}]}
    page = page.replace('<!-- structured-data -->', '<script type="application/ld+json">' + json.dumps(graph, separators=(',', ':')) + '</script>')
    # Content hashes invalidate the texture bundle and the hero's element boxes when they change, without query-string
    # caching tricks (the host's service worker keeps any .js or .json it has seen, with no revalidation).
    for name in ('textures.js', 'media/boxes.json'):
        src = OUT / name
        versioned = src.with_name(src.stem + '-' + hashlib.sha256(src.read_bytes()).hexdigest()[:12] + src.suffix)
        src.rename(versioned)
        ref = versioned.relative_to(OUT).as_posix()
        assert f"'{name}'" in page, name
        page = page.replace(f"'{name}'", f"'{ref}'")
    (OUT / 'index.html').write_text(page)
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n')
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{BASE}</loc></url><url><loc>{BASE}index.md</loc></url></urlset>\n')
    (OUT / 'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="#f6b93b"/></svg>\n')
    for size in (16, 32, 192, 512):
        (OUT / f'favicon-{size}.png').write_bytes(png(size))
    (OUT / 'apple-touch-icon.png').write_bytes(png(180))
    (OUT / 'site.webmanifest').write_text(json.dumps({
        'name': 'OG Video Preview', 'short_name': 'OG Video Preview', 'id': BASE,
        'start_url': BASE, 'scope': BASE, 'display': 'browser',
        'background_color': '#0b0a09', 'theme_color': '#0b0a09',
        'icons': [{'src': f'favicon-{n}.png', 'sizes': f'{n}x{n}', 'type': 'image/png'} for n in (192, 512)]}, indent=2) + '\n')
    # These paragraphs summarize README.md and SKILL.md, with eval numbers computed above.
    summary = f'''# OG Video Preview

> {DESCRIPTION}

An agent skill for Claude Code, OpenAI Codex, Cursor and agents supporting Agent Skills. Built by Joe Hu. MIT licensed; eval images belong to their owners.

## Install

```sh
{INSTALL}
```

## How it works

The skill reads and classifies elements in an approved image, cuts them over a refilled background, and gives each kind its own motion. It renders a seamless 4-second loop at 60 fps and checks frame-0 identity, the loop seam and file-size budgets. It writes Open Graph tags and checks HTTP Range support (206). It can also render an HTML card.

## Where og:video plays

The README and skill reference record support checked on 2026-10-30: iMessage autoplays muted and loops; Discord uses an inline player with a play button. Telegram played it as a looping GIF in our test on 2026-10-30. Slack, X, Facebook, LinkedIn, WhatsApp, Signal, Bluesky, Mastodon and Matrix show the still. See the skill reference for conditions and sources.

## Evaluation

{len(results)} real OG images, {passed} passing results, {layers} elements read, with no hand tuning. Checks: frame-0 mean difference <= 2 and local defects <= 0.05%; seam at most 1.5 normal frame steps; MP4 <= 2 MB and JPEG <= 180 KB. Results describe the checked-in eval, not a guarantee for every input.

## FAQ

''' + '\n\n'.join(f'### {f["q"]}\n\n{f["a"]}' for f in faq) + f'''

## Links

- [Landing page]({BASE})
- [Repository and README]({REPO})
- [Skill reference]({REPO}/blob/main/SKILL.md)
- [Eval results]({BASE}eval/results.json)
- [Full page in Markdown]({BASE}index.md)
- [MIT license]({REPO}/blob/main/LICENSE)
'''
    (OUT / 'llms.txt').write_text(summary)
    markdown = f'''# Make your link previews move.

```sh
{INSTALL}
```

[20-second film]({BASE}media/film.mp4)

## Live on real sites

- [joespeaking.com](https://joespeaking.com)
- [hubeiqiao.com](https://hubeiqiao.com)

## {len(names)} real sites. Zero hand-tuning.

{stats}

''' + '\n'.join(f'- [{name} ({sites[name]["domain"]})](https://{sites[name]["domain"]}) · [og:video]({BASE}eval/{name}.mp4)' for name in names) + f'''

## One command. Any og:image.

```sh
{INSTALL}
```

[GitHub]({REPO}) · [Inspired by @pfista](https://x.com/pfista/status/2113288415546638515) · [Built by Joe Hu](https://hubeiqiao.com) · [MIT]({REPO}/blob/main/LICENSE)

---

''' + summary
    (OUT / 'index.md').write_text(markdown)
    (OUT / 'llms-full.txt').write_text(markdown)
    assert '\u2014' not in summary + markdown, 'No em dashes in generated copy'


if __name__ == '__main__':
    main()
