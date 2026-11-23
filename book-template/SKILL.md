---
name: book-template
description: Build a mathematical textbook as a static site from Markdown chapters, with build-time math rendering, automatic numbering and cross-references, theorem and example callouts, sidenotes, a print edition, executable notebooks and per-chapter verification. Use when starting, restructuring or restyling a technical book, lecture notes or a long-form mathematical document that deploys to GitHub Pages.
---

# Book template

A kit for technical books in the spirit of Keenan Crane's *Discrete Differential Geometry*: warm paper, a narrow measure, wide margins for notes, quiet callouts, figures that carry the argument. The kit lives in `kit/`. Copy it into the book's `tools/` directory and write a `book.toml`.

## Principles

1. **Source is plain Markdown that reads well raw.** Never store chapters as exported documents or as strings inside JavaScript. If a chapter cannot be diffed, it cannot be maintained.
2. **The build must be able to fail.** A broken reference, a duplicate label, a missing figure or a LaTeX error stops the build. A book that renders "something" from broken input accumulates broken input.
3. **Numbers are assigned by the build, never typed.** Authors write labels. Equation, theorem, figure, table and section numbers and all references to them are generated.
4. **Math is rendered at build time.** The page ships static HTML and CSS. No client-side typesetting, no flash of raw TeX, no dependence on a CDN at read time, and errors surface during the build.
5. **No client-side application.** One HTML file per chapter. Navigation is links. The site works with JavaScript disabled and prints cleanly.
6. **Every claim is backed by something that runs.** Each chapter has a verification script and a notebook. See "Verification and notebooks".

## Quick start

```text
book/
  book.toml            title, parts, chapters, shared macros   (see kit/book.example.toml)
  AUTHORING.md         voice, markup, notation                 (start from kit/AUTHORING.template.md)
  chapters/index.md    landing-page text
  chapters/ch01_*.md   chapter sources
  figures/src/ch01.py  writes figures/ch01-*.svg               (see the beautiful-diagrams skill)
  verify/ch01.py       numerical checks; must exit 0
  notebooks/src/ch01.py
  tools/               copy of kit/  (+ figkit.py and fonts/ from beautiful-diagrams)
  docs/                build output, served by GitHub Pages
```

```bash
npm install --prefix tools
```

```bash
python tools/build.py
```

```bash
python tools/build.py --only 3 --out /tmp/draft
```

Requirements: Python 3.11+, Pandoc 3.1+, Node.js, and Playwright with Chromium for the PDF. `--only` builds a subset and downgrades references to other chapters from errors to warnings. `--out` writes somewhere other than `docs/`, which matters when several writers build at once.

## What the kit contains

| File | Role |
| :-- | :-- |
| `build.py` | Reads `book.toml`, runs two Pandoc passes per chapter (collect labels, then render), renders math, wraps pages in the template, writes `index.html`, `chNN.html`, appendices (`appA.html`), `book.html` (single page) and `book.pdf`. Each chapter header links to its notebook, verification script and skill. Writes `.nojekyll`. |
| `filter.lua` | Pandoc Lua filter: numbers sections, callouts, figures, tables and labelled equations; resolves `[](#label)` references across chapters; turns footnotes into sidenotes; adds run-in callout headers and proof QED marks. |
| `render_math.mjs` | Renders every math span with KaTeX on the server. Exits non-zero on a LaTeX error and prints the offending source. |
| `style.css` | Paper palette, type scale, layout grid, callouts, sidenotes, tables, print rules. |
| `make_pdf.cjs` | Prints the single-page edition to `book.pdf` with headless Chromium (Playwright). The site links to it as a download. `--no-pdf` skips it. |
| `check_terms.py` | Enforces one vocabulary and one notation. Reads `terms.toml` and scans chapters, figure scripts, notebook sources and skills for banned variants. |
| `make_notebook.py` | Converts a percent-format `.py` into an `.ipynb` and executes it, so a notebook that does not run cannot be committed. |
| `book.example.toml`, `terms.example.toml` | Example configuration and example terminology rules. |
| `AUTHORING.template.md` | Rules for authors: markup, labels, figures, verification. Add the book's notation table. |

## Author-facing markup

```markdown
---
title: The manifolds robots live on
short: Manifolds
id: ch-manifolds
summary: One sentence for the contents page.
notebook: notebooks/ch02_name.ipynb
verify: verify/ch02.py
---

## Section title {#sec2-name}

::: {.theorem #thm2-name name="Short title"}
Statement, with $inline$ math and
$$ display math \label{eq2-name} $$
:::

See [](#thm2-name) and equation [](#eq2-name). ^[A sidenote.]

![Caption that says what to look at.](figures/ch02-name.svg){#fig2-name}
```

- Callout classes: `definition`, `theorem`, `proposition`, `lemma`, `corollary` (one shared counter); `example`, `exercise`, `thought`, `algorithm` (own counters); `remark`, `warning`, `proof` (unnumbered).
- An empty link `[](#label)` becomes "Theorem 2.3", "(2.4)", "Figure 2.1", "Section 2.2", "Table 2.1" or "Chapter 2", and points to the right file.
- Only labelled equations are numbered.
- Tables are numbered by wrapping them in `::: {.table #tbl2-name}`.
- Remarks and warnings can be referenced too: `[the pitfall](#warn2-name)`.
- A chapter entry in `book.toml` whose `num` is a string (`"A"`) is an appendix.
- A reference carries its own name. Write `[](#ch-x)`, not `Chapter [](#ch-x)`.
- No math in section headings: they also appear in the sidebar.
- Inside math, degrees are `^\circ`.
- Code listings stay under 85 characters per line.
- No level-1 headings in chapters. The title comes from front matter.
- Shared TeX macros go in `[macros]` in `book.toml`.

## Design specification

Keep these unless the book has a reason to differ. They are implemented in `kit/style.css`.

- **Surface.** Paper `#fdfcf8`, ink `#1e242b`, muted `#646873`, rule `#e3dfd4`. Never pure black on pure white on screen. Print switches to white and black.
- **Measure.** About 41rem (65 to 70 characters) at 18.5px, line height 1.62. Do not hyphenate: at this measure a ragged right edge reads better than broken words.
- **Margins.** A 15rem right margin holds sidenotes on wide screens. Below 1280px sidenotes fold inline as indented blocks.
- **Type.** EB Garamond for prose, Source Sans 3 for headings, labels, captions and navigation, JetBrains Mono for code. Old-style numerals in prose, lining numerals in labels and tables.
- **Callouts.** A 3.5px left rule and a faint tint, with a small-caps sans label run into the first line. Indigo `#1b1f8a` on `#f4f6fb` for definitions and theorems. Teal `#2a6f73` on `#f3f8f8` for examples and exercises. Terracotta `#c85a32` on `#fcf4ef` for thought experiments. Amber `#b07322` on `#fbf7ef` for remarks and warnings. Proofs are unboxed: italic "Proof." and a right-aligned square.
- **Navigation.** A fixed sidebar lists parts and chapters, expands the current chapter's sections, and greys out planned chapters. On narrow screens it becomes a `<details>` element. A running head and previous/next links frame each chapter.
- **Print.** `book.html` holds every chapter. Print rules hide navigation, start each chapter on a new page and keep callouts, figures and display math from splitting.

## Verification and notebooks

A textbook is trusted for its equations. Treat them as code.

- `verify/chNN.py` checks every identity at random points, every derivative against finite differences, and every derived model against an independent derivation (a symbolic library, a second formulation, a conservation law). It also computes every number the text quotes and writes them to a JSON file. The text is edited to match the script, not the reverse.
- When a draft claim fails its check, change the claim. Record what changed.
- `notebooks/src/chNN.py` is the notebook source in percent format. `make_notebook.py` builds and executes it. A notebook must run on a clean runtime, so it installs its own extras in the first cell and does not import from the repository.

## One vocabulary, enforced

Readers notice every inconsistency. A symbol that changes between the prose, a figure label and a notebook cell costs more trust than a typo.

- Keep one **notation and glossary appendix** as the source of truth: conventions, symbol tables that link to the defining equation, an alphabetical glossary, and a short "we write X, not Y" table.
- Encode each decision as a rule in `terms.toml` and run `check_terms.py`. It covers chapter text, figure scripts, notebook sources and skills, inside or outside math as the rule says.
- Add a symbol or term to the appendix and the rules before using it.
- Cite a work identically everywhere: same author format, same venue string, same link. Link every reference to its DOI, arXiv page or repository, and confirm each link before adding it.
- When chapters are written in parallel, finish with one consistency pass by a single editor who reads everything, writes the appendix from what the chapters actually use, and fixes all files until the checker passes and every verification script still succeeds.

## Working with several writers

Chapters can be written in parallel by people or agents if these hold:

- One shared authoring guide with a fixed notation table, and one finished chapter as the reference.
- Each writer owns a disjoint set of files (chapter, figure script, verify script, notebook, skill) and never edits `tools/` or `book.toml`.
- Labels carry a chapter prefix (`eq3-`, `thm3-`), because labels are global.
- A writer may reference another chapter only by chapter id until that chapter's labels exist. A final pass adds the finer cross-references.
- Writers build with `--only N --out <private dir>`.
- Each writer reports the claims they corrected and the labels they defined.

## Pitfalls this template exists to prevent

- **Exported documents as source.** Word-processor exports lose `\\`, braces and table structure silently.
- **Client-side math and a single-page app.** They hide LaTeX errors until someone reads the page, and break printing, linking and search.
- **Hand-typed numbers.** "Eq. (2.4)" typed by hand is wrong the first time a paragraph moves.
- **A build that deletes its output directory while another build runs.** Use `--out`.
- **A byte-order mark at the top of a chapter.** It breaks front-matter parsing. The build strips it.
- **SVG figures with live text.** Embedded as images they cannot load web fonts, so labels fall back to a default face. Export text as outlines (see beautiful-diagrams).

## References

- Keenan Crane, *Discrete Differential Geometry: An Applied Introduction*: https://www.cs.cmu.edu/~kmcrane/Projects/DDG/paper.pdf
- Tufte CSS, for the sidenote layout: https://edwardtufte.github.io/tufte-css/
