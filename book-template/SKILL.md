---
name: book-template
description: Build and style mathematical textbooks and static GitHub Pages sites (docs/index.html) in Keenan Crane's Discrete Differential Geometry style with warm off-white paper, wide-margin Tufte layout, Libertine/Source Sans typography, theorem callout boxes, MathJax 3, and Mermaid.js.
---

# Mathematical Book & Static Web Textbook Template

Use this skill when designing, formatting, or building a mathematical/technical textbook or static GitHub Pages book (`docs/index.html`) inspired by Keenan Crane's *Discrete Differential Geometry: An Applied Introduction*.

## 1. Page Layout, Measure, & Color Surface

- **Warm off-white paper for screen:** Set the default viewport background to `#fdfcf8` with deep charcoal ink `#1e1e1e` (never harsh `#000000` on `#ffffff` on screen) to give the calm, glare-free feel of archival textbook paper.
- **Crisp print mode:** Inside `@media print`, switch background to `#ffffff`, ink to `#000000`, hide navigation sidebars/topbars, and add `break-inside: avoid` on callout boxes, figures, and display equations.
- **Comfortable reading measure:** Constrain the main prose column to `64ch` (`~680px` to `720px`) with generous vertical rhythm (`1.62` line-height).
- **Wide margins & Tufte-style marginalia:** On wide viewports (`>= 1180px`), pair the `680px` prose column with a `240px` right margin track (`gap: 3rem`) for sidenotes, small schematic figures, and short historical/geometric remarks. On narrower screens (`< 1180px`), collapse margin notes cleanly inline as subtle indented blocks.
- **Running chapter headers:** Display uppercase tracked sans-serif running heads (e.g., `2.2. ANATOMY OF A SIMPLICIAL COMPLEX`) at the top of each section/page in muted slate `#646873` (`0.75rem`, `letter-spacing: 0.08em`).

## 2. Font Pairing & Typographic Hierarchy

Load Google Fonts (or local WOFF2) for classic academic serif prose paired with crisp humanist sans-serif headers and clean monospace code.

- **Prose & Display Math:** `'Linux Libertine O', 'EB Garamond', 'Source Serif 4', Georgia, serif` at `1.08rem` (`17.5px`), `line-height: 1.65`.
- **Headings, Callout Labels, & Nav UI:** `'Linux Biolinum O', 'Source Sans 3', system-ui, -apple-system, sans-serif`.
- **Code & Algorithms:** `'JetBrains Mono', 'Fira Code', ui-monospace, monospace` at `0.88em` with subtle `#f4f1e8` background and `1px solid #e5e0d0` border for code blocks.

Google Fonts families to include: `EB Garamond` (400..700, normal & italic), `Source Sans 3` (400, 600, 700), and `JetBrains Mono` (400, 500).

## 3. Theorem, Definition, Remark, & Exercise Boxes

Follow Crane's DDG convention: clear uppercase/small-caps sans-serif headers, subtle left border accents, and generous internal padding (`1rem 1.25rem`).

| Environment | Left Border Accent | Background Tint | Body Style |
| :--- | :--- | :--- | :--- |
| **Definition / Theorem / Proposition** | `3.5px solid #1b1f8a` | `#f4f6fb` | Roman or light italic statement; bold header `THEOREM 3.1` |
| **Example / Exercise** | `3.5px solid #2a6f73` | `#f3f8f8` | Normal roman text; numbered `EXAMPLE 1`, `EXERCISE 2.1` |
| **Remark / Note / Disclaimer** | `3.5px solid #b07322` | `#fbf7ef` | Normal roman text; subtle amber label `REMARK` |
| **Coding Exercise** | `3.5px solid #4a4e58` | `#f5f3ec` | Normal roman + monospace method names `CODING 1` |

### Proofs & Equation Numbering

- **Proofs:** Begin with italic *Proof.* (no heavy box), end with a right-aligned QED square (`\square` or CSS `float: right` `□`).
- **Equation numbering:** Use AMS-style right-aligned numbers `(2.1)` via `\tag{2.1}` or `\label{eq:name}` + `\eqref{eq:name}`. Wrap display math containers in `overflow-x: auto` so wide matrices never break mobile layout.

## 4. Static GitHub Pages (`docs/index.html`) Architecture

Structure the site so it deploys directly from `/docs` on GitHub Pages (or via Jekyll `docs/_config.yml` + `docs/index.md`):

```text
docs/
  _config.yml         # Optional Jekyll config (kramdown + mathjax)
  index.md            # Landing page or SPA shell
  styles.css          # Paper palette (#fdfcf8), Tufte grid, callout boxes, print rules
  mathjax_config.js   # MathJax 3 configuration with AMS tags
  diagrams.js         # Keenan-Crane-style inline SVG figures
  app.js              # Chapter navigation, callout decoration, Mermaid & MathJax init
  book_data.js        # Bundled chapter markdown sections
```

### MathJax 3 Configuration (`mathjax_config.js`)

Load this configuration before `mathjax@3/es5/tex-mml-chtml.js` so inline `$...$`, display `$$...$$`, and explicit `\tag{}` / `\eqref{}` work reliably across chapters:

```javascript
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    tags: 'ams',
    processEscapes: true
  },
  options: {
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
  }
};
```

### Mermaid.js Schematics Configuration (`app.js`)

Theme Mermaid (`mermaid@11`) diagrams to match the `#fdfcf8` paper and `#1b1f8a` indigo ink:

```javascript
mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  themeVariables: {
    background: '#fdfcf8',
    primaryColor: '#f4f6fb',
    primaryTextColor: '#1e242b',
    primaryBorderColor: '#1b1f8a',
    lineColor: '#2b2b2b',
    secondaryColor: '#fbf7ef',
    tertiaryColor: '#f3f8f8',
    fontFamily: '"Source Sans 3", system-ui, sans-serif'
  }
});
```

### Core CSS Skeleton (`docs/styles.css`)

```css
:root {
  --paper: #fdfcf8;
  --ink: #1e242b;
  --muted: #525d6a;
  --accent: #1b1f8a;
  --border: #e3dfd4;
  --font-serif: 'EB Garamond', 'Linux Libertine O', Georgia, serif;
  --font-sans: 'Source Sans 3', 'Linux Biolinum O', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;
}

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-serif);
  font-size: 18.5px;
  line-height: 1.65;
}

.main {
  max-width: 68ch;
  margin: 0 auto;
  padding: 2.25rem 3.5rem 5rem;
}

.callout {
  margin: 1.5rem 0;
  padding: 0.95rem 1.25rem;
  border-radius: 3px;
  border-left: 3.5px solid var(--accent);
  background: #f4f6fb;
}

.callout.example { border-left-color: #2a6f73; background: #f3f8f8; }
.callout.remark  { border-left-color: #b07322; background: #fbf7ef; }
.callout.coding  { border-left-color: #4a4e58; background: #f5f3ec; }

.mjx-container[display="true"] { overflow-x: auto; padding: 0.4rem 0; }

@media print {
  body { background: #ffffff; color: #000000; font-size: 11pt; }
  .sidebar, .asset-bar, .chapter-nav-footer { display: none !important; }
  .callout, .kc-figure, .mermaid { break-inside: avoid; }
}
```

### Responsive Chapter Navigation Checklist

- **Collapsible sidebar TOC:** List chapters and section anchors; highlight the active chapter.
- **Footer prev/next links:** Place Previous / Next chapter navigation buttons at the bottom of every chapter.
- **Dynamic MathJax re-typesetting:** Call `await MathJax.typesetPromise([container])` and `await mermaid.run({ nodes: container.querySelectorAll('.mermaid') })` after rendering each chapter.

## Primary References

- Keenan Crane, *Discrete Differential Geometry: An Applied Introduction* (PDF): https://www.cs.cmu.edu/~kmcrane/Projects/DDG/paper.pdf
- Keenan Crane, *Discrete Differential Geometry* Course Page: https://www.cs.cmu.edu/~kmcrane/Projects/DDG/
