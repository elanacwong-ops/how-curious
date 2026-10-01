#!/usr/bin/env python3
"""Builds the blog: reads Markdown from posts/ and pages/, writes HTML to docs/.

Usage:  python build.py
Links are relative, so the site works at any address (GitHub Pages project
site, user site, or a local preview) with no configuration.
"""
import re
import shutil
from datetime import date, datetime
from html import escape
from pathlib import Path

import markdown
import yaml

# ---- Edit these ----------------------------------------------------------
SITE_TITLE = "How Curious"
TAGLINE = "Curiosities about recent economic developments and hot topics in the media."
AUTHOR = "Elana Wong"
# --------------------------------------------------------------------------

ROOT = Path(__file__).parent
OUT = ROOT / "docs"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def load(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)


def to_html(body):
    return markdown.markdown(body, extensions=["extra", "toc", "smarty"])


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def fmt(d):
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def write(rel, html):
    path = OUT / rel / "index.html" if rel else OUT / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def layout(title, body, root, description=""):
    full_title = f"{title} | {SITE_TITLE}" if title else SITE_TITLE
    desc = escape(description or TAGLINE, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(full_title)}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{root}">{escape(SITE_TITLE)}</a>
  <nav>
    <a href="{root}">Posts</a>
    <a href="{root}topics/">Topics</a>
    <a href="{root}about/">About</a>
  </nav>
</header>
<main>
{body}
</main>
<footer class="site-footer">&copy; {date.today().year} {escape(AUTHOR)}</footer>
</body>
</html>
"""


def tag_links(tags, root):
    return "".join(
        f'<a class="tag" href="{root}topics/{slugify(t)}/">{escape(str(t).replace("-", " "))}</a>'
        for t in tags
    )


def ledger(posts, root):
    rows = "".join(
        f"""<li>
  <time datetime="{p['date'].isoformat()}">{fmt(p['date'])}</time>
  <div>
    <a class="entry-title" href="{root}posts/{p['slug']}/">{escape(p['title'])}</a>
    <p>{escape(p['description'])}</p>
  </div>
</li>"""
        for p in posts
    )
    return f'<ol class="ledger">{rows}</ol>'


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(ROOT / "static" / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").touch()

    # Load posts
    posts = []
    for f in sorted((ROOT / "posts").glob("*.md")):
        meta, body = load(f)
        if meta.get("draft"):
            continue
        words = len(re.findall(r"\w+", body))
        posts.append({
            "slug": meta.get("slug") or f.stem,
            "title": meta.get("title", f.stem),
            "description": meta.get("description", ""),
            "date": as_date(meta.get("date", date.today())),
            "tags": meta.get("tags", []) or [],
            "minutes": max(1, round(words / 220)),
            "html": to_html(body),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)

    # Post pages
    for p in posts:
        root = "../../"
        body = f"""<article>
<header class="post-head">
  <h1>{escape(p['title'])}</h1>
  <p class="byline">By {escape(AUTHOR)} on <time datetime="{p['date'].isoformat()}">{fmt(p['date'])}</time>, {p['minutes']} min read</p>
  <p class="tags">{tag_links(p['tags'], root)}</p>
</header>
<div class="prose">
{p['html']}
</div>
</article>"""
        write(f"posts/{p['slug']}", layout(p["title"], body, root, p["description"]))

    # Home
    intro = f'<section class="intro"><h1>{escape(SITE_TITLE)}</h1><p>{escape(TAGLINE)}</p></section>'
    write("", layout("", intro + ledger(posts, "./"), "./"))

    # Topics
    by_tag = {}
    for p in posts:
        for t in p["tags"]:
            by_tag.setdefault(slugify(t), {"name": str(t).replace("-", " "), "posts": []})["posts"].append(p)

    items = "".join(
        f'<li><a href="{s}/">{escape(v["name"])}</a> <span>{len(v["posts"])}</span></li>'
        for s, v in sorted(by_tag.items())
    )
    write("topics", layout("Topics", f'<h1 class="page-title">Topics</h1><ul class="topic-list">{items}</ul>', "../"))
    for s, v in by_tag.items():
        body = f'<h1 class="page-title">{escape(v["name"])}</h1>' + ledger(v["posts"], "../../")
        write(f"topics/{s}", layout(v["name"], body, "../../"))

    # Static pages (pages/about.md -> /about/)
    for f in (ROOT / "pages").glob("*.md"):
        meta, body = load(f)
        title = meta.get("title", f.stem.title())
        html = f'<h1 class="page-title">{escape(title)}</h1><div class="prose">{to_html(body)}</div>'
        write(f.stem, layout(title, html, "../"))

    # 404
    (OUT / "404.html").write_text(
        layout("Not found", '<h1 class="page-title">Page not found</h1><p><a href="/">Go to the home page</a></p>', "/"),
        encoding="utf-8",
    )
    print(f"Built {len(posts)} post(s) into {OUT}")


if __name__ == "__main__":
    main()
