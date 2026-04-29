# diegoquezadac.github.io

Static blog. ~200 lines of Python, no dependencies.

## layout

```
build.py        # generator
config.json     # site metadata
style.css       # styles
templates/      # index.html, post.html (str.format placeholders)
src/*.md        # source posts
posts/*.html    # generated (committed for GitHub Pages)
index.html      # generated
feed.xml        # generated RSS
sitemap.xml     # generated, for search engines
```

## new post

Create `src/YYYY-MM-DD-slug.md`:

```
---
title: hello, world
date: 2026-04-28
summary: first post.
draft: true        # optional — skips the post during build
---

body in markdown.
```

Supported markdown: headings, paragraphs, links, inline/block code, blockquotes, lists (`-`, `*`, `1.`), **bold**, *italic*. No images — add them to `md_to_html` in `build.py` if needed.

## build

```
python3 build.py
```

Writes `index.html`, `feed.xml`, `sitemap.xml`, and `posts/*.html` in place. Commit and push — GitHub Pages serves from the repo root (`.nojekyll` disables Jekyll).

## config

Edit `config.json`. Fields are referenced by name in the templates and feed; renaming a key means updating both.
