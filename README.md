# The Economic Ledger

A small blog you build from Markdown. No Node, no frameworks.

## Setup (once)
```bash
pip install -r requirements.txt
```

## Write a post
Create `posts/my-post.md`:
```markdown
---
title: "My post title"
description: "One-sentence summary shown on the home page."
date: 2026-10-05
tags: [inflation, policy]
---

## First section

Your text...
```
Tags with spaces are fine (`"labor market"`). Add `draft: true` to hide a post.

## Build and preview
```bash
python build.py
python -m http.server 8000 -d docs
```
Open http://localhost:8000

## Publish on GitHub Pages
1. Run `python build.py`, then commit and push (the `docs/` folder is included).
2. On GitHub: Settings > Pages > Source: **Deploy from a branch**, Branch: `main`, Folder: `/docs`.

Site name, tagline, and author are at the top of `build.py`. Colors and fonts are in `static/style.css`.
