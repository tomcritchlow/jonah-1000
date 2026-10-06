#!/usr/bin/env python3
"""One-off: recover structured post data from the generated HTML archive.

The original build ran off an Instagram export that isn't in this repo.
This script reads posts/*.html and writes data/posts.json, which build.py
then treats as the source of truth.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def field(pattern, text):
    m = re.search(pattern, text, re.S)
    return html.unescape(m.group(1)) if m else None


def main():
    posts = []
    for path in sorted((ROOT / 'posts').glob('*.html')):
        page = path.read_text()
        n = int(path.stem)
        post = {
            'n': n,
            'date': field(r'<time datetime="([^"]+)"', page),
            'images': re.findall(r'<img src="\.\./media/([^"]+)\.webp"', page),
            'caption': field(r'<p class="caption">(.*?)</p>\n<nav>', page),
        }
        if '<div class="book">' in page:
            post['title'] = field(r'<h2>(.*?)</h2>', page)
            byline = field(r'<p class="byline">(.*?)</p>', page) or ''
            byline = re.sub(r'<[^>]+>', '', byline)  # names may be linked
            parts = byline.split(' · ')
            for part in parts:
                if part.startswith('by '):
                    post['author'] = part[3:]
                elif part.startswith('illustrated by '):
                    post['illustrator'] = part[len('illustrated by '):]
            post['isbn'] = field(r'ISBN (\w+)', page)
            post['bookshop'] = field(r'<p class="buy">.*?<a href="([^"]+)"', page)
        posts.append(post)
    out = ROOT / 'data' / 'posts.json'
    out.write_text(json.dumps(posts, ensure_ascii=False, indent=1) + '\n')
    print(f'wrote {len(posts)} posts to {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
