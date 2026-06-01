#!/usr/bin/env python3
"""
Blog builder — drop a .txt file in blog/ with this format and push:

    title: Your Post Title
    date:  YYYY-MM-DD
    desc:  One-line blurb for the listing (optional — falls back to first paragraph)

    First paragraph of the post goes here. It gets the larger lead style.

    Second paragraph. Blank line = new paragraph.

    # Section heading  →  <h3>
    `inline code`      →  <code>
    **bold text**      →  <strong>

GitHub Actions runs this script on every push that touches blog/*.txt,
then commits the generated .html files and posts.json back to the repo.
"""
import json
import re
from datetime import datetime
from pathlib import Path

BLOG_DIR = Path("blog")

HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{description}">
    <title>{title} — Dhruv Chopra</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../style.css">
    <link rel="stylesheet" href="post.css">
</head>
<body>

    <nav>
        <a href="../" class="nav-name">Dhruv Chopra</a>
        <button class="nav-toggle" aria-label="Toggle navigation">Menu</button>
        <ul class="nav-links">
            <li><a href="../#about">About</a></li>
            <li><a href="../#blog">Blog</a></li>
            <li><a href="../#research">Research</a></li>
            <li><a href="../#work">Work</a></li>
            <li><a href="../#projects">Projects</a></li>
            <li><a href="../#cv">CV</a></li>
            <li><a href="../#contact">Contact</a></li>
        </ul>
    </nav>

    <main>
        <article>
            <header class="post-header">
                <p class="post-kicker">Blog</p>
                <h1>{title}</h1>
                <p class="post-byline">Dhruv Chopra &middot; <time datetime="{date_iso}">{date_display}</time></p>
            </header>
            <div class="post-body">
{body_html}
                <p class="post-back"><a href="../#blog">&larr; Blog</a></p>
            </div>
        </article>
    </main>

    <script>
        const toggle = document.querySelector('.nav-toggle');
        const links  = document.querySelector('.nav-links');
        toggle.addEventListener('click', () => links.classList.toggle('open'));
    </script>

</body>
</html>
"""


def parse_txt(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    # Split on first blank line to separate frontmatter from body
    parts = re.split(r'\n[ \t]*\n', text, maxsplit=1)
    meta = {}
    body = parts[1].strip() if len(parts) == 2 else ""
    for line in parts[0].splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip().lower()] = val.strip()
    return meta, body


def inline_fmt(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def body_to_html(body: str) -> str:
    blocks = re.split(r'\n{2,}', body)
    out = []
    first = True
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            out.append(f'                <h3>{inline_fmt(block[2:].strip())}</h3>')
        else:
            text = inline_fmt(" ".join(block.splitlines()))
            cls = ' class="lead"' if first else ''
            out.append(f'                <p{cls}>{text}</p>')
            first = False
    return "\n".join(out)


def fmt_date(s: str):
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
        return d.strftime("%b %Y"), s
    except ValueError:
        return s, s


def main():
    posts = []

    for txt in sorted(BLOG_DIR.glob("*.txt")):
        meta, body = parse_txt(txt)
        slug = txt.stem
        title = meta.get("title", slug.replace("-", " ").title())
        date_display, date_iso = fmt_date(meta.get("date", ""))

        if "desc" in meta:
            desc = meta["desc"]
        else:
            first_para = re.split(r'\n{2,}', body)[0] if body else ""
            desc = re.sub(r'[`*#]', '', " ".join(first_para.splitlines()))[:160].strip()

        html = HTML.format(
            title=title,
            description=desc,
            date_iso=date_iso,
            date_display=date_display,
            body_html=body_to_html(body),
        )

        out = BLOG_DIR / f"{slug}.html"
        out.write_text(html, encoding="utf-8")
        print(f"  built  {out}")

        posts.append({
            "slug": slug,
            "title": title,
            "date": meta.get("date", ""),
            "date_display": date_display,
            "desc": desc,
            "url": f"blog/{slug}.html",
        })

    posts.sort(key=lambda p: p["date"], reverse=True)

    manifest = BLOG_DIR / "posts.json"
    manifest.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote  {manifest}  ({len(posts)} post{'s' if len(posts) != 1 else ''})")


if __name__ == "__main__":
    main()
