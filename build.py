#!/usr/bin/env python3
"""Build the static site from data/posts.json.

Writes index.html, people.html, posts/*.html, search-data.js and grid
thumbnails in media/thumb/ (only the missing ones). Requires Pillow.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from html import escape
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
SITE = "Jonah's 1000 Picture Books"
IMG_SIZE = 900    # every media/*.webp is 900x900
THUMB_SIZE = 300  # grid cells are ~140px wide, so this covers 2x displays
# hashtags on more than this share of posts are boilerplate (#book, #kidlit...)
# and are left out of the search index
BOILERPLATE_SHARE = 0.25


def load():
    return json.loads((ROOT / 'data' / 'posts.json').read_text())


def slug(n):
    return f'{n:04d}'


def long_date(iso):
    d = date.fromisoformat(iso)
    return f'{d:%B} {d.day}, {d.year}'


def short_date(iso):
    d = date.fromisoformat(iso)
    return f'{d:%b} {d.day}, {d.year}'


# --- people ---------------------------------------------------------------

def split_people(credit):
    """'Terry Fan, Eric Fan, and Devin Fan' -> three names, but keep pairs
    sharing a surname ('Leo and Diane Dillon') together as one credit."""
    if '(' in credit:
        return [credit]
    chunks = [c for c in re.split(r',\s*(?:and\s+)?|\s+and\s+', credit) if c]
    names = []
    for c in chunks:
        if names and ' ' not in names[-1]:
            names[-1] += ' and ' + c
        else:
            names.append(c)
    return names


def person_id(name):
    ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', ascii_name.lower()).strip('-')


def sort_key(name):
    base = re.sub(r'\s*\(.*?\)', '', name)
    base = re.sub(r',?\s+(Jr|Sr)\.?$', '', base)
    last = base.split()[-1]
    fold = lambda s: unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return (re.sub(r'[^a-z]', '', fold(last)), fold(name))


def credits(p):
    """[(role, name), ...] in byline order."""
    out = []
    for role in ('author', 'illustrator'):
        if role in p:
            out += [(role, name) for name in split_people(p[role])]
    return out


def linked_names(credit, prefix):
    """Escape a credit string, linking each person to the people page."""
    out, pos = '', 0
    for name in split_people(credit):
        i = credit.index(name, pos)
        out += escape(credit[pos:i])
        out += f'<a href="{prefix}people.html#{person_id(name)}">{escape(name)}</a>'
        pos = i + len(name)
    return out + escape(credit[pos:])


# --- post pages -----------------------------------------------------------

def page_title(p):
    if 'title' not in p:
        return f'#{p["n"]} &mdash; {p["date"]} &mdash; {SITE}'
    bits = [escape(p['title'])]
    if 'author' in p:
        bits.append(escape(p['author']))
    bits += [f'#{p["n"]}', SITE]
    return ' &mdash; '.join(bits)


def nav(p, total):
    prev = (f'<a href="{slug(p["n"] - 1)}.html" rel="prev">&larr; previous</a>'
            if p['n'] > 1 else '<span></span>')
    nxt = (f'<a href="{slug(p["n"] + 1)}.html" rel="next">next &rarr;</a>'
           if p['n'] < total else '<span></span>')
    home = f'<a href="../index.html#p{slug(p["n"])}" class="home">index</a>'
    return f'<nav>{prev} {home} {nxt}</nav>'


def book_block(p):
    if 'title' not in p:
        return ''
    out = f'<div class="book"><h2>{escape(p["title"])}</h2>\n'
    byline = []
    if 'author' in p:
        byline.append('by ' + linked_names(p['author'], '../'))
    if 'illustrator' in p:
        byline.append('illustrated by ' + linked_names(p['illustrator'], '../'))
    if byline:
        out += f'<p class="byline">{" &middot; ".join(byline)}</p>\n'
    out += (f'<p class="buy">ISBN {p["isbn"]} &middot; '
            f'<a href="{escape(p["bookshop"])}" rel="noopener">Find on Bookshop.org</a></p></div>')
    return out


def render_post(p, total):
    imgs = '\n'.join(f'<img src="../media/{i}.webp" width="{IMG_SIZE}" height="{IMG_SIZE}" '
                     f'alt="" loading="lazy">' for i in p['images'])
    n = nav(p, total)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title(p)}</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="layout">
<div class="images">
{imgs}
</div>
<div class="text">
{n}
<p class="meta">#{p["n"]} of {total} &middot; <time datetime="{p["date"]}">{long_date(p["date"])}</time></p>
{book_block(p)}
<p class="caption">{escape(p["caption"])}</p>
{n}
</div>
</div>
<script src="../post.js"></script>
</body>
</html>
'''


# --- index ----------------------------------------------------------------

def thumb(image_id):
    return f'media/thumb/{image_id}.webp'


def plain_byline(p):
    bits = []
    if 'author' in p:
        bits.append(p['author'])
    if 'illustrator' in p and p.get('illustrator') != p.get('author'):
        bits.append(('illus. ' if bits else 'illustrated by ') + p['illustrator'])
    return ' · '.join(bits)


def render_cell(p):
    label = ''
    if 'title' in p:
        label += f'<span class="t">{escape(p["title"])}</span>'
    if plain_byline(p):
        label += f'<span class="b">{escape(plain_byline(p))}</span>'
    label += f'<span class="d">#{p["n"]} · {short_date(p["date"])}</span>'
    return (f'<a href="posts/{slug(p["n"])}.html" id="p{slug(p["n"])}">'
            f'<img src="{thumb(p["images"][0])}" width="{THUMB_SIZE}" height="{THUMB_SIZE}" '
            f'alt="" loading="lazy"><span class="label">{label}</span></a>')


def render_index(posts):
    cells = '\n'.join(render_cell(p) for p in posts)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
<h1><a href="index.html">{SITE}</a></h1>
<p>1000 days. 1000 books. An archive of @jonahdragan on Instagram, July 2020 &ndash; April 2023.</p>
<p><a href="people.html">Browse by author &amp; illustrator</a></p>
<div class="search"><input id="q" type="search" placeholder="Search titles, authors, captions&hellip;" autocomplete="off"></div>
<div class="views" role="group" aria-label="Layout">
<button type="button" data-view="grid" aria-pressed="true">Grid</button>
<button type="button" data-view="list" aria-pressed="false">List</button>
</div>
<p id="count"></p>
</header>
<div class="grid">
{cells}
</div>
<footer>{len(posts)} posts &middot; built from an Instagram export</footer>
<script src="search.js"></script>
</body>
</html>
'''


# --- people page ----------------------------------------------------------

def render_people(posts):
    people = defaultdict(list)  # name -> [(post, roles)]
    for p in posts:
        roles = defaultdict(list)
        for role, name in credits(p):
            roles[name].append(role)
        for name, r in roles.items():
            people[name].append((p, r))

    by_letter = defaultdict(list)
    for name in sorted(people, key=sort_key):
        by_letter[sort_key(name)[0][:1].upper() or '#'].append(name)

    role_label = {('author',): 'author', ('illustrator',): 'illustrator',
                  ('author', 'illustrator'): 'author &amp; illustrator'}
    sections = []
    for letter, names in by_letter.items():
        entries = []
        for name in names:
            books = '\n'.join(
                f'<li><a href="posts/{slug(p["n"])}.html">'
                f'<img src="{thumb(p["images"][0])}" width="{THUMB_SIZE}" height="{THUMB_SIZE}" '
                f'alt="" loading="lazy"><span class="t">{escape(p["title"])}</span>'
                f'<span class="d">#{p["n"]} · {role_label[tuple(dict.fromkeys(r))]}</span></a></li>'
                for p, r in people[name])
            count = len(people[name])
            entries.append(
                f'<section class="person" id="{person_id(name)}">\n'
                f'<h3>{escape(name)} <span class="count">{count} book{"s" if count > 1 else ""}</span></h3>\n'
                f'<ul>\n{books}\n</ul>\n</section>')
        sections.append(f'<h2 id="letter-{letter}">{letter}</h2>\n' + '\n'.join(entries))

    letters = ' '.join(f'<a href="#letter-{l}">{l}</a>' for l in by_letter)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Authors &amp; Illustrators &mdash; {SITE}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
<h1><a href="index.html">{SITE}</a></h1>
<p>{len(people)} authors &amp; illustrators, A&ndash;Z by surname.</p>
<p class="letters">{letters}</p>
</header>
<main class="people">
{chr(10).join(sections)}
</main>
<footer><a href="index.html">&larr; back to the index</a></footer>
</body>
</html>
'''


# --- search index ---------------------------------------------------------

def search_entries(posts):
    tags = Counter()
    for p in posts:
        tags.update(set(re.findall(r'#\w+', p['caption'])))
    boilerplate = {t for t, c in tags.items() if c > BOILERPLATE_SHARE * len(posts)}

    entries = []
    for p in posts:
        prose = re.sub(r'#\w+', '', p['caption'])
        fields = [p.get(k) for k in ('title', 'author', 'illustrator', 'isbn')] + [prose]
        text = ' '.join(' '.join(filter(None, fields)).split()).lower()
        # keep topical hashtags as plain words, unless already in the text
        extra = []
        for t in dict.fromkeys(re.findall(r'#\w+', p['caption'])):
            word = t[1:].lower()
            if t not in boilerplate and word not in text and word not in extra:
                extra.append(word)
        entries.append(compact(' '.join([text] + extra)))
    return entries


def compact(text):
    """Search ANDs whitespace-free substrings, so only the set of words
    matters: drop repeats and any word contained in a longer one."""
    words = sorted(set(text.split()), key=len, reverse=True)
    kept = []
    for w in words:
        if not any(w in k for k in kept):
            kept.append(w)
    order = {w: i for i, w in enumerate(text.split())}
    return ' '.join(sorted(kept, key=order.get))


# --- thumbnails -----------------------------------------------------------

def make_thumbs(posts):
    out_dir = ROOT / 'media' / 'thumb'
    out_dir.mkdir(exist_ok=True)
    made = 0
    for p in posts:
        dest = out_dir / f'{p["images"][0]}.webp'
        if dest.exists():
            continue
        with Image.open(ROOT / 'media' / f'{p["images"][0]}.webp') as im:
            im.convert('RGB').resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS).save(
                dest, 'WEBP', quality=72, method=6)
        made += 1
    return made


def main():
    posts = load()
    total = len(posts)
    made = make_thumbs(posts)
    for p in posts:
        (ROOT / 'posts' / f'{slug(p["n"])}.html').write_text(render_post(p, total))
    (ROOT / 'index.html').write_text(render_index(posts))
    (ROOT / 'people.html').write_text(render_people(posts))
    index = json.dumps(search_entries(posts), ensure_ascii=False)
    (ROOT / 'search-data.js').write_text(f'window.SEARCH_INDEX = {index};\n')
    print(f'built {total} posts, {made} new thumbnails')


if __name__ == '__main__':
    main()
