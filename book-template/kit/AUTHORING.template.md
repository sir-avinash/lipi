# Authoring guide

Pick one finished chapter as the reference for voice, structure and markup, and name it here. This file states the rules it follows. The `engaging-exposition` skill explains the reasoning behind the writing rules.

## Who we write for

State the reader in two sentences: what they know, what they do not, and when new ideas are introduced.

## How a chapter is built

1. **Open with a puzzle.** A concrete question the reader thinks they can answer, and cannot. No roadmap paragraph, no learning objectives, no thesis statement.
2. **Concrete before general.** The circle before the sphere, the sphere before the manifold. A picture or a number before the definition. State the theorem only after the reader could have guessed it.
3. **Thought experiments carry the hard ideas.** Use a `thought` block for anything a reader can do in their head or with their hands. At least two per chapter.
4. **Worked examples have real numbers.** Every number quoted in the text is produced by `verify/chNN.py`.
5. **Each section ends by creating the need for the next one.** A question, an unexplained piece, a failure of what was just built.
6. **Be honest about limits.** Say what a result does not give you. Use a `warning` block for traps that cost people flight hardware.
7. **Close with exercises and sources.** 5 to 8 exercises that ask for a derivation, an experiment or a counterexample. Then "Notes and sources": who did what, in two or three sentences, and a reference list.

Target length is 3000 to 4500 words. Cut anything that does not help the reader understand or do something.

## Prose rules

- Short sentences. One idea each. If a sentence has three clauses, split it.
- No em-dashes. Use a full stop, a colon or parentheses.
- Plain verbs. Never "leverage", "delve", "crucial", "pivotal", "robust framework", "it is worth noting", "in this chapter we will".
- Do not announce what you are about to say. Say it.
- Address the reader as "you". Use "we" for shared derivation steps.
- Define a term once, in bold, at first use. Do not rename it later.
- British or American spelling is fine. Be consistent within a chapter.
- No claims you have not checked. No invented quotes, numbers or citations. Cite only works you can identify precisely. If a source PDF is available, check the claim against it.
- Never mention how the book was produced, which tools generated it, or what any layout was modelled on.

## Markup

Chapters are Pandoc Markdown. No level-1 headings: the title comes from the front matter.

```markdown
---
title: The manifolds robots live on
short: Manifolds
id: ch-manifolds
summary: One sentence for the contents page.
notebook: notebooks/ch02_name.ipynb
verify: verify/ch02.py
---

Opening puzzle, straight in.

## Section title {#sec2-name}

::: {.definition #def2-name name="Short title"}
Body. Display math goes on its own lines.
:::
```

Block types: `definition`, `theorem`, `proposition`, `lemma`, `corollary` share one counter. `example`, `exercise`, `thought` each have their own. `remark`, `warning` and `proof` are unnumbered. `name="..."` is optional and may contain inline math.

Numbering and cross-references are automatic.

| Thing | How to label it | How to refer to it | Renders as |
| :-- | :-- | :-- | :-- |
| Equation | `\label{eq2-name}` inside `$$...$$` | `[](#eq2-name)` | (2.4) |
| Block | `#thm2-name` in the div attributes | `[](#thm2-name)` | Theorem 2.3 |
| Figure | `![Caption.](figures/ch02-name.svg){#fig2-name}` | `[](#fig2-name)` | Figure 2.1 |
| Section | `{#sec2-name}` on the heading | `[](#sec2-name)` | Section 2.2 |
| Table | wrap in `::: {.table #tbl2-name}` | `[](#tbl2-name)` | Table 2.1 |
| Chapter | `id:` in front matter | `[](#ch-manifolds)` | Chapter 2 |

Rules that keep the build green:

- Prefix every label with the chapter number (`eq2-`, `thm2-`, `fig2-`, `sec2-`). Labels are global.
- Only label equations you refer to. Unlabelled equations are unnumbered.
- A figure is an image alone in its paragraph, with a caption that says what to look at.
- Sidenotes are footnotes: `^[Short aside.]`. Keep them to one or two sentences.
- Unnumbered closing sections: `## Exercises {#sec2-exercises .unnumbered}` and `## Notes and sources {#sec2-notes .unnumbered}`.
- Math is KaTeX. A LaTeX error fails the build. Use `\begin{bmatrix}`, `\begin{aligned}`, `\tfrac`, `\operatorname`. One `\label` per display.
- Shared macros are in `book.toml`. List them here.

List the chapter ids here so authors can cite chapters that are not written yet.

## Notation

Fixed for the whole book. Do not introduce alternatives. Fill this table in before the second chapter is written: every symbol that appears in more than one chapter, with its convention (frames, signs, units).

| Object | Symbol and convention |
| :-- | :-- |
| ... | ... |

## Figures

Each chapter has one script, `figures/src/chNN.py`, with one function per figure, writing `figures/chNN-name.svg`. Use `tools/figkit.py`. Read its docstrings and the reference chapter's figure script before drawing. The `beautiful-diagrams` skill has the full rules.

- **Compute, never fake.** Every point is the projection of real 3D geometry through `Scene`. Hidden parts are found by the kit (`sphere_curve`, `point_visible`, `ribbons`).
- **One question per figure.** If the caption needs "and also", make two figures.
- **Stroke tiers.** Silhouette thickest, vectors next, construction lines thin, hidden lines dashed. Use the kit's constants.
- **Palette.** Ink for structure. Indigo for the main object or the "good" path. Terracotta for the contrasting object, error or failure. Teal for a third role. Pastel fills only.
- **Labels sit next to what they name**, with the halo the kit applies. Math in labels uses `$...$`. Words use `fontfamily="Source Sans 3"` at size 9 to 10.
- **Look at every figure** before you keep it. Rasterise it and check for overlaps, clipped text, edge-on planes and labels that landed on a line.
- Aim for 4 to 6 figures per chapter. At least half should be geometric scenes, the rest data plots produced by simulation.

## Verification

`verify/chNN.py` checks the chapter. Shared helpers live in `verify/common.py`.

- Every identity stated in the chapter gets a numerical check at random points.
- Every derivative formula is checked against finite differences.
- Every derived model is derived a second time by an independent route (a symbolic library, a second formulation, a conservation law) and compared numerically.
- Every number quoted in the text is computed there and stored with `ck.record(...)`.
- The script must exit 0. If a claim in an earlier draft fails, the text changes, not the check.

## Notebooks and skills

Each chapter has a notebook and a skill.

- **Notebook.** Source in `notebooks/src/chNN.py` (percent format, `# %%` and `# %% [markdown]` cells). Build and execute with `python tools/make_notebook.py notebooks/src/chNN.py notebooks/chNN_name.ipynb`. It must run top to bottom on a clean Colab runtime: install anything beyond NumPy, SciPy and Matplotlib in its first cell. It lets the reader reproduce the chapter's examples and start the exercises.
- **Skill.** `skills/chNN-name/SKILL.md` with valid front matter (`name`, `description`). It is a procedure a researcher or an agent follows to apply the chapter to their own system: when to use it, the steps, the checks that must pass, the failure modes. Formulas in a skill must match the chapter exactly. No narrative.

## Build

```bash
python figures/src/ch03.py
python verify/ch03.py
python tools/build.py --only 3 --out /tmp/draft-ch3
python tools/build.py
```

The full build fails on any broken reference, duplicate label, missing figure or LaTeX error.
