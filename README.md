# Jonah's 1000 Picture Books

Static archive of [@jonahdragan](https://www.instagram.com/jonahdragan/)'s
Instagram project: 1,000 picture book reviews in 1,000 days, July 2020 –
April 2023.

**Browse it here: https://tomcritchlow.com/jonah-1000/**

Originally generated from an Instagram data export — 1,001 posts and
9,314 images (resized to 900px WebP) — with an image-grid index, an
author & illustrator index, and client-side search.

## Building

`data/posts.json` is the source of truth for every post (date, images,
caption, book metadata). To rebuild the site after editing it:

    pip install Pillow
    python3 build.py

This regenerates `index.html`, `people.html`, `posts/*.html` and
`search-data.js`, and creates any missing 300px grid thumbnails in
`media/thumb/`. The hand-written files are `style.css`, `search.js` and
`post.js`.

`tools/extract.py` is how `data/posts.json` was first recovered from the
generated HTML; it shouldn't need running again.
