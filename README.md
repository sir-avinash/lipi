# Lipi

Reusable skills and kits for writing mathematical textbooks: how the book is built, how its figures are drawn, and how its chapters are written. The visual language follows Keenan Crane's *Discrete Differential Geometry* and *Illustrating Geometry*.

## Skills

| Skill | Use it to | Ships with |
| :-- | :-- | :-- |
| [`book-template`](book-template/SKILL.md) | Build a book as a static site from Markdown: build-time math, automatic numbering and cross-references, callouts, sidenotes, print edition, executable notebooks, per-chapter verification. | `kit/`: `build.py`, `filter.lua`, `render_math.mjs`, `style.css`, `make_notebook.py`, example config, authoring template |
| [`beautiful-diagrams`](beautiful-diagrams/SKILL.md) | Draw figures from real 3D geometry with a strict stroke hierarchy, matte pastel shading, computed hidden lines and haloed labels. | `figkit.py`, `fonts/` |
| [`engaging-exposition`](engaging-exposition/SKILL.md) | Write chapters that are absorbing to read: puzzles, thought experiments, concrete before general, checked examples. | |

## Using them in a book

```bash
cp -r lipi/book-template/kit/. mybook/tools/
```

```bash
cp -r lipi/beautiful-diagrams/figkit.py lipi/beautiful-diagrams/fonts mybook/tools/
```

Then follow the quick start in `book-template/SKILL.md`. The kits are the source of truth: fix a bug here, then copy it into the book.
