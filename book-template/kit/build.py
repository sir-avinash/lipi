#!/usr/bin/env python3
"""Build a static book site from Markdown chapters.

    python tools/build.py            # build every chapter into docs/
    python tools/build.py --only 3 --out /tmp/draft
                                     # draft build of chapter 3 alone; references
                                     # to other chapters print a warning

Pipeline: pandoc (+ filter.lua) -> KaTeX at build time -> HTML template.
Config lives in book.toml at the repository root.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
OUT = ROOT / "docs"
PANDOC_FORMAT = "markdown+fenced_divs+bracketed_spans+footnotes+pipe_tables+smart+implicit_figures"


def fail(msg: str) -> None:
    sys.exit(f"build failed: {msg}")


def split_front_matter(text: str) -> tuple[dict, str]:
    text = text.lstrip("\ufeff")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, text[m.end():]


def pandoc(body: str, env: dict) -> str:
    proc = subprocess.run(
        ["pandoc", "-f", PANDOC_FORMAT, "-t", "html5", "--katex", "--wrap=none",
         "--no-highlight", "--lua-filter", str(TOOLS / "filter.lua")],
        input=body, capture_output=True, text=True, env={**os.environ, **env},
    )
    if proc.returncode != 0 or "BOOKERR" in proc.stderr:
        fail(proc.stderr.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.stdout


def render_math(fragment: str, macros_path: Path, tmp: Path) -> str:
    src, dst = tmp / "in.html", tmp / "out.html"
    src.write_text(fragment, encoding="utf-8")
    proc = subprocess.run(
        ["node", str(TOOLS / "render_math.mjs"), str(src), str(dst), str(macros_path)],
        capture_output=True, text=True, cwd=TOOLS,
    )
    if proc.returncode != 0:
        fail(proc.stderr.strip())
    return dst.read_text(encoding="utf-8")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def inline_md(text: str, macros_path: Path, tmp: Path) -> str:
    """Render a one-line Markdown string (titles, summaries) to inline HTML."""
    proc = subprocess.run(
        ["pandoc", "-f", PANDOC_FORMAT, "-t", "html5", "--katex", "--wrap=none"],
        input=text, capture_output=True, text=True,
    )
    out = render_math(proc.stdout, macros_path, tmp).strip()
    return re.sub(r"^<p>|</p>$", "", out)


def nav_html(cfg: dict, chapters: list[dict], current: dict | None) -> str:
    parts = []
    for part in cfg["part"]:
        items = []
        for ch in part["chapter"]:
            built = next((c for c in chapters if c["num"] == ch["num"]), None)
            if built is None:
                items.append(f'<li class="planned"><span class="n">{ch["num"]}</span>{esc(ch["title"])}</li>')
                continue
            cls = ' class="current"' if current is built else ""
            sub = ""
            if current is built:
                secs = "".join(
                    f'<li><a href="#{s["id"]}"><span class="n">{s["num"]}</span>{esc(s["title"])}</a></li>'
                    for s in built["sections"])
                sub = f'<ol class="secs">{secs}</ol>'
            items.append(
                f'<li{cls}><a href="{built["file"]}"><span class="n">{built["num"]}</span>'
                f'{built["nav_title"]}</a>{sub}</li>')
        parts.append(f'<div class="part">{esc(part["title"])}</div><ol>{"".join(items)}</ol>')
    return "".join(parts)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400..700;1,400..700&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/katex/katex.min.css">
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="{body_class}">
<details class="mobile-nav"><summary>{book_title}</summary><nav>{nav}</nav></details>
<aside class="sidebar">
<a class="brand" href="index.html">{book_title}</a>
<nav>{nav}</nav>
<a class="print-link" href="book.pdf" download>Download the book as PDF</a>
<a class="print-link minor" href="book.html">Read as a single page</a>
</aside>
<main>
{main}
</main>
</body>
</html>
"""


def chapter_main(ch: dict, prev: dict | None, nxt: dict | None, cfg: dict) -> str:
    links = []
    if ch.get("notebook"):
        url = f'https://colab.research.google.com/github/{cfg["repo"]}/blob/{cfg.get("branch", "main")}/{ch["notebook"]}'
        links.append(f'<a href="{url}">Notebook (Colab)</a>')
    if ch.get("verify"):
        url = f'https://github.com/{cfg["repo"]}/blob/{cfg.get("branch", "main")}/{ch["verify"]}'
        links.append(f'<a href="{url}">Verification script</a>')
    if ch.get("skill"):
        url = f'https://github.com/{cfg["repo"]}/blob/{cfg.get("branch", "main")}/{ch["skill"]}'
        links.append(f'<a href="{url}">Skill</a>')
    assets = f'<p class="assets">{" · ".join(links)}</p>' if links else ""
    foot = '<nav class="pager">'
    foot += f'<a class="prev" href="{prev["file"]}"><span>Previous</span>{prev["num"]}. {prev["title_html"]}</a>' if prev else "<span></span>"
    foot += f'<a class="next" href="{nxt["file"]}"><span>Next</span>{nxt["num"]}. {nxt["title_html"]}</a>' if nxt else "<span></span>"
    foot += "</nav>"
    return (
        f'<div class="running-head">{ch["num"]}. {esc(ch["nav_plain"])}</div>'
        f'<article class="chapter" id="{ch["id"]}">'
        f'<header class="chapter-head"><div class="chapter-num">{ch["kind"]} {ch["num"]}</div>'
        f'<h1>{ch["title_html"]}</h1>{assets}{ch.get("epigraph_html", "")}</header>'
        f'{ch["body"]}</article>{foot}')


def main() -> None:
    cfg = tomllib.loads((ROOT / "book.toml").read_text(encoding="utf-8"))
    if "branch" not in cfg:
        # Link notebooks, scripts and skills on the branch being built, so the links are never dead.
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        cfg["branch"] = os.environ.get("BOOK_BRANCH") or (head if head and head != "HEAD" else "main")
    tmp = Path(tempfile.mkdtemp(prefix="bookbuild-"))
    macros_path = tmp / "macros.json"
    macros_path.write_text(json.dumps(cfg.get("macros", {})), encoding="utf-8")

    global OUT
    if "--out" in sys.argv:
        OUT = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
    only = None
    if "--only" in sys.argv:
        only = {int(n) for n in sys.argv[sys.argv.index("--only") + 1].split(",")}
        os.environ["BOOK_LENIENT"] = "1"
    chapters = []
    planned: dict[str, dict] = {}
    for part in cfg["part"]:
        for ch in part["chapter"]:
            if "file" not in ch:
                continue
            if only and isinstance(ch["num"], int) and ch["num"] not in only:
                if ch.get("id"):  # left out of a partial build: name it, do not link it
                    planned[ch["id"]] = {"text": f'Chapter\u00a0{ch["num"]}', "file": "", "planned": True}
                continue
            if not (ROOT / ch["file"]).exists():
                print(f'note: {ch["file"]} not written yet; listed as planned', file=sys.stderr)
                if ch.get("id"):
                    planned[ch["id"]] = {"text": f'Chapter\u00a0{ch["num"]}', "file": "", "planned": True}
                continue
            meta, body = split_front_matter((ROOT / ch["file"]).read_text(encoding="utf-8"))
            num = ch["num"]
            appendix = not isinstance(num, int)
            if not appendix:
                skill_dirs = sorted((ROOT / "skills").glob(f"ch{num:02d}-*/SKILL.md"))
                if skill_dirs and "skill" not in meta:
                    meta["skill"] = str(skill_dirs[0].relative_to(ROOT))
            chapters.append({
                **meta, "num": num, "src": body,
                "file": f"app{num}.html" if appendix else f"ch{num:02d}.html",
                "kind": "Appendix" if appendix else "Chapter",
                "id": meta.get("id", f"ch-{num}"), "part": part["title"],
                "title": meta.get("title") or fail(f'{ch["file"]}: missing title'),
            })

    # Pass 1: collect labels from every chapter.
    labels: dict[str, dict] = {}
    for ch in chapters:
        path = tmp / f'{ch["file"]}.labels.json'
        pandoc(ch["src"], {"BOOK_CHAPTER": str(ch["num"]), "BOOK_FILE": ch["file"], "BOOK_COLLECT": str(path)})
        got = json.loads(path.read_text(encoding="utf-8"))
        ch["sections"] = got["sections"] or []
        for key, val in (got["labels"] or {}).items():
            if key in labels:
                fail(f'label "{key}" defined in both {labels[key]["file"]} and {ch["file"]}')
            labels[key] = val
        labels[ch["id"]] = {"text": f'{ch["kind"]} {ch["num"]}', "file": ch["file"]}

    for key, val in planned.items():
        labels.setdefault(key, val)
    labels_path = tmp / "labels.json"
    labels_path.write_text(json.dumps(labels), encoding="utf-8")

    # Pass 2: render.
    for single in (False, True):
        for ch in chapters:
            frag = pandoc(ch["src"], {
                "BOOK_CHAPTER": str(ch["num"]), "BOOK_FILE": ch["file"],
                "BOOK_LABELS": str(labels_path), "BOOK_SINGLE": "1" if single else "0"})
            ch["body_single" if single else "body"] = render_math(frag, macros_path, tmp)
    for ch in chapters:
        ch["title_html"] = inline_md(ch["title"], macros_path, tmp)
        ch["nav_plain"] = ch.get("short", re.sub(r"[$\\{}]", "", ch["title"]))
        ch["nav_title"] = inline_md(ch.get("short", ch["title"]), macros_path, tmp)
        if ch.get("epigraph"):
            source = f'<footer>{inline_md(ch["epigraph_source"], macros_path, tmp)}</footer>' if ch.get("epigraph_source") else ""
            ch["epigraph_html"] = f'<blockquote class="epigraph"><p>{inline_md(ch["epigraph"], macros_path, tmp)}</p>{source}</blockquote>'

    kept_pdf = None
    if OUT.exists():
        if "--no-pdf" in sys.argv and (OUT / "book.pdf").exists():
            kept_pdf = tmp / "book.pdf.kept"
            shutil.copy(OUT / "book.pdf", kept_pdf)
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    (OUT / ".nojekyll").write_text("")
    shutil.copy(TOOLS / "style.css", OUT / "assets" / "style.css")
    katex_dist = TOOLS / "node_modules" / "katex" / "dist"
    (OUT / "assets" / "katex" / "fonts").mkdir(parents=True)
    shutil.copy(katex_dist / "katex.min.css", OUT / "assets" / "katex")
    for font in (katex_dist / "fonts").glob("*.woff2"):
        shutil.copy(font, OUT / "assets" / "katex" / "fonts")
    if (ROOT / "figures").exists():
        (OUT / "figures").mkdir()
        for pattern in ("*.svg", "*.png", "*.gif"):
            for fig in (ROOT / "figures").glob(pattern):
                shutil.copy(fig, OUT / "figures")

    book_title = esc(cfg["title"])
    for i, ch in enumerate(chapters):
        prev = chapters[i - 1] if i else None
        nxt = chapters[i + 1] if i + 1 < len(chapters) else None
        page = PAGE.format(
            title=f'{ch["num"]}. {esc(ch["nav_plain"])} | {book_title}', book_title=book_title,
            body_class="chapter-page", nav=nav_html(cfg, chapters, ch),
            main=chapter_main(ch, prev, nxt, cfg))
        (OUT / ch["file"]).write_text(page, encoding="utf-8")

    # Landing page.
    intro_meta, intro_src = split_front_matter((ROOT / cfg.get("index", "chapters/index.md")).read_text(encoding="utf-8"))
    intro = render_math(pandoc(intro_src, {"BOOK_CHAPTER": "0", "BOOK_FILE": "index.html", "BOOK_LABELS": str(labels_path)}), macros_path, tmp)
    toc = []
    for part in cfg["part"]:
        rows = []
        for ch in part["chapter"]:
            built = next((c for c in chapters if c["num"] == ch["num"]), None)
            if built:
                summary = f'<p>{inline_md(built["summary"], macros_path, tmp)}</p>' if built.get("summary") else ""
                rows.append(f'<li><a href="{built["file"]}"><span class="n">{built["num"]}</span>{built["title_html"]}</a>{summary}</li>')
            else:
                rows.append(f'<li class="planned"><span class="n">{ch["num"]}</span>{esc(ch["title"])}<em>planned</em></li>')
        toc.append(f'<h3>{esc(part["title"])}</h3><ol class="toc">{"".join(rows)}</ol>')
    landing = (
        f'<article class="landing"><header class="chapter-head"><h1>{book_title}</h1>'
        f'<p class="subtitle">{esc(cfg.get("subtitle", ""))}</p>'
        f'<p class="assets"><a href="book.pdf" download>Download the book as PDF</a> · '
        f'<a href="book.html">Read as a single page</a> · '
        f'<a href="https://github.com/{cfg["repo"]}">Source on GitHub</a></p></header>'
        f'{intro}<h2 id="contents">Contents</h2>{"".join(toc)}</article>')
    (OUT / "index.html").write_text(PAGE.format(
        title=book_title, book_title=book_title, body_class="landing-page",
        nav=nav_html(cfg, chapters, None), main=landing), encoding="utf-8")

    # Single-page edition for printing to PDF.
    whole = "".join(
        f'<article class="chapter" id="{ch["id"]}"><header class="chapter-head">'
        f'<div class="chapter-num">{ch["kind"]} {ch["num"]}</div><h1>{ch["title_html"]}</h1>{ch.get("epigraph_html", "")}</header>'
        f'{ch["body_single"]}</article>' for ch in chapters)
    (OUT / "book.html").write_text(PAGE.format(
        title=book_title, book_title=book_title, body_class="single-page",
        nav=nav_html(cfg, chapters, None),
        main=f'<header class="chapter-head book-title"><h1>{book_title}</h1></header>{whole}'), encoding="utf-8")

    # Every referenced figure must exist.
    missing = set()
    for page in OUT.glob("*.html"):
        for src in re.findall(r'<img src="([^"]+)"', page.read_text(encoding="utf-8")):
            if not src.startswith("http") and not (OUT / src).exists():
                missing.add(src)
    if missing:
        fail("missing figures: " + ", ".join(sorted(missing)))

    # PDF edition, printed from the single-page edition.
    if kept_pdf is not None:
        shutil.copy(kept_pdf, OUT / "book.pdf")
    if "--no-pdf" not in sys.argv:
        proc = subprocess.run(["node", str(TOOLS / "make_pdf.cjs"), str(OUT / "book.html"), str(OUT / "book.pdf")],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            fail("PDF: " + proc.stderr.strip() + " (install Playwright, or pass --no-pdf)")

    shutil.rmtree(tmp)
    print(f"built {len(chapters)} chapters, {len(labels)} labels -> {OUT}/")


if __name__ == "__main__":
    main()
