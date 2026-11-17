---
name: beautiful-diagrams
description: Create publication-grade mathematical and geometric diagrams in Keenan Crane's visual style using 3D-first projection, strict stroke hierarchy, muted pastel shading with soft cast shadows, white-halo labels, and clean Python/matplotlib or inline SVG implementations.
---

# Beautiful Diagrams (Keenan Crane & SIGGRAPH Style)

Use this skill whenever generating geometric, mathematical, robotics, or technical illustrations in Python (`matplotlib` / SVG / PDF) or inline HTML `<svg>`. The rules synthesize Keenan Crane's *Illustrating Geometry*, the *Penrose* diagramming framework, and SIGGRAPH's *Explanatory Paper Figures with Illustrator and Blender*.

## 1. Core Philosophy: Geometry First

- **Never fake 3D perspective:** "Really do it in 3D. Faking it never works" (Crane). Human eyes immediately spot slightly wrong ellipses, foreshortening, or tangent planes. Always compute 2D coordinates from actual 3D geometry (meshes, parametric surfaces, curves) using an explicit orthographic or perspective camera projection.
- **Separate structure from style:** Following *Penrose*, define mathematical objects and spatial relationships (containment, tangency, orthogonality, layer order, disjointness) separately from visual attributes (stroke weights, fills, fonts).
- **Vector first, raster only for matte shading:** Export SVG for web textbooks and PDF for LaTeX so figures remain infinitely zoomable. When using 3D Cycles/Blender renders for smooth matte surfaces, composite crisp vector strokes, arrows, and labels on top.
- **Iterate from insight:** Every figure must answer one clear question. Start with a rough layout, verify that occluded and front features read unambiguously, then refine line weights and label clearance.

## 2. Line Hierarchy & Stroke Discipline

Every curve in a figure belongs to a strict visual tier. Use rounded caps and joins (`stroke-linecap="round"`, `stroke-linejoin="round"`) on all geometric strokes.

| Line Class | Weight (SVG px / pt) | Style & Opacity | Purpose |
| :--- | :--- | :--- | :--- |
| **Silhouette / Boundary** | `2.2` to `2.8` | Solid `#1a1a1a`, 100% | Outer contour of a 3D surface or domain boundary |
| **Primary Vector / Arrow** | `1.8` to `2.2` | Solid `#1b1f8a` or `#1a1a1a` | Tangent vectors, normals, flows, emphasized paths |
| **Interior / Combinatorial** | `0.8` to `1.2` | Solid `#2b2b2b`, 65% to 85% | Mesh edges, geodesics, coordinate grids, level sets |
| **Hidden / Occluded** | `0.7` to `1.0` | Dashed (`4 3` or `3.5 3`), 45% to 65% | Back-facing edges, occluded curve segments, construction lines |

### Silhouette & Tapered Ink Rules

- **Always draw the silhouette:** Extract edges shared by one front-facing triangle and one back-facing triangle (plus open boundary edges) and stroke them in the thickest tier.
- **Tapered / variable-weight strokes:** For hand-inked elegance, vary stroke width slightly along curved silhouettes (thicker on the shadow side or foreground, thinner on highlights or receding arcs) by rendering variable-width ribbon polygons or segmented polylines in Python/SVG.
- **True hidden-line testing:** Determine visibility via z-buffer or ray-mesh occlusion in 3D before drawing. Never guess which segment is behind a surface.

## 3. Palette, Shading, & Soft Cast Shadows

Keep surface fills light, matte, and low-saturation so dark ink strokes and mathematical labels remain dominant.

### Signature Palette

- **Ink & Accents:** Primary ink `#1a1a1a`; Crane signature deep indigo `#1b1f8a`; warm terracotta accent `#c85a32`; muted teal `#2a6f73`.
- **Cool Surface Pastels:** Ice blue `#d8e4f0` to `#9fb9d8`; soft periwinkle `#c7d0e8`; pale slate `#e2e8f0`.
- **Warm Surface Pastels:** Warm paper/sand `#f6efe2`; soft peach `#f2c6a0`; muted ochre `#e8c56b`.
- **Occluded / Interior Regions:** Use a cooler, desaturated tint at `20%` to `35%` opacity so back faces recede behind front faces without visual noise.

### Lighting & Soft Cast Shadows

- **Two-light studio rule:** Place a primary area light behind and slightly above the camera for clear form reading, and a softer secondary fill light from the side to lift harsh shadows. High roughness (matte look) prevents distracting specular hotspots.
- **Cheat the light when needed:** Use separate light directions for surface shading versus ground cast shadows if doing so clarifies 3D depth.
- **Soft cast shadows:** Project the 3D geometry onto a ground plane and fill with a subtle linear or radial gradient using `#1b1f8a` or `#2c3248` at `18%` to `25%` opacity fading smoothly to `0%` opacity. Never use harsh, opaque drop shadows.

## 4. Labeling & Typography

- **Match the document font:** Use `Linux Libertine` / `EB Garamond` / `Source Serif 4` (italic for math symbols like $f$, $M$, $T_p M$) and `Linux Biolinum` / `Source Sans 3` for clean text callouts and axis annotations.
- **Local placement ("Too far, Too close, Just Right"):** Keep labels roughly `4px` to `8px` from their target vertex, edge, or vector tip. Never touch or overlap the stroke, and never drift so far that association is ambiguous.
- **Optical centering:** Center labels inside regions or at arrow midpoints visually, accounting for ascenders, descenders, and subscripts.
- **White-halo occlusion clearance:** Whenever a label crosses a line or sits over a shaded region, add a background-matching halo (`#fdfcf8` for warm paper or `#ffffff` for white) so lines break cleanly around the text without erasing underlying geometry.
  - **SVG:** `paint-order: stroke fill; stroke: #fdfcf8; stroke-width: 4px; stroke-linejoin: round;`
  - **Matplotlib:** `path_effects=[pe.withStroke(linewidth=3.8, foreground="#fdfcf8")]`

## 5. Python (`matplotlib`) Implementation Pattern

Use explicit 3D camera projection and painter's sorting in 2D `Axes` rather than `mpl_toolkits.mplot3d` defaults, which distort depth sorting and lack clean SVG layering.

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.collections import PolyCollection, LineCollection

plt.rcParams.update({
    "svg.fonttype": "none",          # Keep text editable/selectable in SVG
    "font.family": "serif",
    "mathtext.fontset": "stix",
})

def project_ortho(pts, azim_deg=-35, elev_deg=24):
    az, el = np.radians(azim_deg), np.radians(elev_deg)
    Rz = np.array([[np.cos(az), -np.sin(az), 0],
                   [np.sin(az),  np.cos(az), 0],
                   [0, 0, 1]])
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(el), -np.sin(el)],
                   [0, np.sin(el),  np.cos(el)]])
    R = Rx @ Rz
    p_cam = pts @ R.T
    return p_cam[:, :2], p_cam[:, 2]  # (xy_2d, depth_z)

def add_halo_label(ax, x, y, text, color="#1a1a1a", bg="#fdfcf8", size=11):
    ax.text(
        x, y, text, color=color, fontsize=size,
        ha="center", va="center", zorder=50,
        path_effects=[pe.withStroke(linewidth=4.0, foreground=bg)],
    )
```

### Painter's Order & Silhouette Extraction Checklist

1. Project all vertices `(xy, z) = project_ortho(V)` and compute per-triangle mean depth `z_tri`.
2. Sort triangles back-to-front (`np.argsort(z_tri)`) and compute Lambertian shading `max(0.15, dot(n, light_dir))` blended into the pastel base color.
3. Draw ground cast shadow polygons at `zorder=1` (`alpha=0.18`, `#1b1f8a` or `#2c3248`).
4. Draw occluded/hidden dashed curves at `zorder=5` (`linestyle=(0, (4, 3))`, `linewidth=0.9`, `alpha=0.55`).
5. Draw sorted surface `PolyCollection` at `zorder=10` with subtle edge strokes (`linewidth=0.3`, matching fill or faint `#4a5568` at `alpha=0.25`).
6. Extract silhouette edges (where adjacent triangles have opposite `dot(n, view_dir)` signs) and draw at `zorder=20` (`linewidth=2.3`, `capstyle="round"`).
7. Draw primary vectors/arrows (`zorder=30`) and white-halo labels (`zorder=50`).

## 6. Clean Inline SVG Pattern (Web Textbooks)

Structure inline `<svg>` elements in strict back-to-front `<g>` layers with reusable `<defs>` for gradients, markers, and halo styles.

```html
<svg viewBox="0 0 640 360" class="diagram" role="img" aria-label="Tangent space on manifold">
  <defs>
    <radialGradient id="cast-shadow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1b1f8a" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#1b1f8a" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="surface-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e3ecf6"/>
      <stop offset="100%" stop-color="#aec6e0"/>
    </linearGradient>
    <marker id="arrow-ink" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#1b1f8a"/>
    </marker>
    <style>
      .silhouette { fill: none; stroke: #1a1a1a; stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; }
      .contour    { fill: none; stroke: #2b2b2b; stroke-width: 1.0; stroke-opacity: 0.7; stroke-linecap: round; }
      .hidden     { fill: none; stroke: #2b2b2b; stroke-width: 0.9; stroke-opacity: 0.5; stroke-dasharray: 4 3; stroke-linecap: round; }
      .vec        { fill: none; stroke: #1b1f8a; stroke-width: 2.0; stroke-linecap: round; marker-end: url(#arrow-ink); }
      .lbl        { font-family: "Linux Libertine O", "EB Garamond", Georgia, serif; font-style: italic; font-size: 16px; fill: #1a1a1a;
                    paint-order: stroke fill; stroke: #fdfcf8; stroke-width: 4px; stroke-linejoin: round; }
    </style>
  </defs>
  <g id="layer-shadow">
    <ellipse cx="320" cy="300" rx="170" ry="34" fill="url(#cast-shadow)"/>
  </g>
  <g id="layer-hidden"><!-- dashed back-facing curves --></g>
  <g id="layer-surface"><!-- pastel shaded fills --></g>
  <g id="layer-contours"><!-- interior grid / geodesics --></g>
  <g id="layer-silhouette"><!-- thick outer silhouettes --></g>
  <g id="layer-annotations"><!-- vectors and .lbl elements --></g>
</svg>
```

## Primary References

- Keenan Crane, *Illustrating Geometry*: https://www.cs.cmu.edu/~kmcrane/IllustratingGeometry.pdf
- Katherine Ye et al. (Keenan Crane), *Penrose: From Mathematical Notation to Beautiful Diagrams* (SIGGRAPH 2020): https://penrose.cs.cmu.edu/siggraph20
- Ruben Wiersma, *Explanatory paper figures with Illustrator and Blender* (RCDC@SIGGRAPH): https://research.siggraph.org/blog/guides/explanatory-paper-figures-with-illustrator-and-blender/
