"""
build.py — turn /src/*.md + /templates/* + config.json into a static site.

usage: python3 build.py
output: index.html, feed.xml, posts/*.html in the repo root
"""

import re
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
POSTS_SRC = ROOT / "src"
TEMPLATES = ROOT / "templates"
OUT = ROOT
OUT_POSTS = OUT / "posts"


def md_to_html(md: str) -> str:
    lines = md.split("\n")
    out = []
    i = 0
    in_para = []

    def flush_para():
        if in_para:
            text = " ".join(in_para)
            out.append(f"<p>{inline(text)}</p>")
            in_para.clear()

    while i < len(lines):
        line = lines[i]

        # code block
        if line.startswith("```"):
            flush_para()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code = "\n".join(buf)
            code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            out.append(f"<pre><code>{code}</code></pre>")
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # blockquote
        if line.startswith(">"):
            flush_para()
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
            continue

        # blank line ends a paragraph
        if line.strip() == "":
            flush_para()
            i += 1
            continue

        # accumulate paragraph text
        in_para.append(line.strip())
        i += 1

    flush_para()
    return "\n  ".join(out)


def inline(text: str) -> str:
    # links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # bold then italic (order matters)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text

def parse_post(path: Path):
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise ValueError(f"{path} missing frontmatter")
    _, fm, body = raw.split("---", 2)

    meta = {}
    for line in fm.strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()

    return {
        "title": meta["title"],
        "date": meta["date"],          # "YYYY-MM-DD"
        "summary": meta.get("summary", ""),
        "slug": path.stem,             # e.g. "2026-04-28-hello"
        "body_html": md_to_html(body.strip()),
    }

def main():
    cfg = json.loads((ROOT / "config.json").read_text())

    posts = sorted(
        [parse_post(p) for p in POSTS_SRC.glob("*.md")],
        key=lambda p: p["date"],
        reverse=True,
    )

    # post pages
    post_tpl = (TEMPLATES / "post.html").read_text()
    OUT_POSTS.mkdir(exist_ok=True)
    for p in posts:
        html = post_tpl.format(
            language=cfg["language"],
            site_title=cfg["title"],
            post_title=p["title"],
            post_summary=p["summary"],
            post_date=p["date"],
            post_body=p["body_html"],
            email=cfg["email"],
        )
        (OUT_POSTS / f"{p['slug']}.html").write_text(html)

    # index
    list_html = "\n".join(
        f'    <li><span class="date">{p["date"]}</span>'
        f'<a href="posts/{p["slug"]}.html">{p["title"]}</a></li>'
        for p in posts
    )
    index_tpl = (TEMPLATES / "index.html").read_text()
    (OUT / "index.html").write_text(index_tpl.format(
        language=cfg["language"],
        title=cfg["title"],
        tagline=cfg["tagline"],
        description=cfg["description"],
        github=cfg["github"],
        email=cfg["email"],
        post_list=list_html,
    ))

    # feed
    items = []
    for p in posts:
        pub = datetime.strptime(p["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        pub_822 = pub.strftime("%a, %d %b %Y %H:%M:%S +0000")
        url = f'{cfg["url"]}/posts/{p["slug"]}.html'
        items.append(f"""    <item>
      <title>{p["title"]}</title>
      <link>{url}</link>
      <guid>{url}</guid>
      <pubDate>{pub_822}</pubDate>
      <description>{p["summary"]}</description>
    </item>""")

    feed = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
        <channel>
            <title>{cfg["title"]}</title>
            <link>{cfg["url"]}/</link>
            <description>{cfg["description"]}</description>
            <language>{cfg["language"]}</language>
            <atom:link href="{cfg["url"]}/feed.xml" rel="self" type="application/rss+xml" />
        {chr(10).join(items)}
        </channel>
        </rss>
        """
    (OUT / "feed.xml").write_text(feed)

    print(f"built {len(posts)} posts → index.html, feed.xml, posts/*.html")

if __name__ == "__main__":
    main()
