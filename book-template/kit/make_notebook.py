#!/usr/bin/env python3
"""Turn a percent-format script into a notebook, and run it to prove it works.

    python tools/make_notebook.py notebooks/src/ch01.py notebooks/ch01_name.ipynb

Cells are separated by lines starting with `# %%`. A cell that starts with
`# %% [markdown]` is Markdown; its lines are comments with the leading `# `
stripped. The notebook is executed top to bottom and saved with its outputs.
"""
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
cells, kind, buf = [], None, []


def flush():
    if kind is None:
        return
    text = "\n".join(buf).strip("\n")
    if kind == "markdown":
        text = "\n".join(line[2:] if line.startswith("# ") else line.lstrip("#") for line in text.splitlines())
        cells.append(nbformat.v4.new_markdown_cell(text))
    elif text:
        cells.append(nbformat.v4.new_code_cell(text))


for line in src.read_text(encoding="utf-8").splitlines():
    if line.startswith("# %%"):
        flush()
        kind, buf = ("markdown" if "[markdown]" in line else "code"), []
    else:
        if kind is None:
            kind = "code"
        buf.append(line)
flush()

nb = nbformat.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
})
if "--no-run" not in sys.argv:
    NotebookClient(nb, timeout=600, kernel_name="python3").execute()
nbformat.write(nb, dst)
print(f"wrote {dst} ({len(cells)} cells{'' if '--no-run' in sys.argv else ', executed'})")
