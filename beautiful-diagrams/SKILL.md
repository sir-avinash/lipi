---
name: beautiful-diagrams
description: Create publication-grade mathematical and geometric diagrams in Keenan Crane's visual style, computed from real 3D geometry with a strict stroke hierarchy, pastel matte shading, soft shadows and haloed labels. Includes figkit.py, a matplotlib kit that implements the rules. Use when drawing any geometric, mathematical, robotics or technical figure, or a data plot that must match such figures.
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

- **Match the document font:** Use `Linux Libertine` / `EB Garamond` / `Source Serif 4` (italic for math symbols like $f$, $M$, $T_p M$) and `Linux Biolinum` / `Source Sans 3` for clean text callouts and axis annotations. Export the text as outlines unless the SVG is inlined in a page that loads those fonts.
- **One role per colour, held across the whole document:** ink for structure, indigo for the main object or the good path, terracotta for the contrast, error or failure, teal for a third role.
- **Local placement ("Too far, Too close, Just Right"):** Keep labels roughly `4px` to `8px` from their target vertex, edge, or vector tip. Never touch or overlap the stroke, and never drift so far that association is ambiguous.
- **Optical centering:** Center labels inside regions or at arrow midpoints visually, accounting for ascenders, descenders, and subscripts.
- **White-halo occlusion clearance:** Whenever a label crosses a line or sits over a shaded region, add a background-matching halo (`#fdfcf8` for warm paper or `#ffffff` for white) so lines break cleanly around the text without erasing underlying geometry.
  - **SVG:** `paint-order: stroke fill; stroke: #fdfcf8; stroke-width: 4px; stroke-linejoin: round;`
  - **Matplotlib:** `path_effects=[pe.withStroke(linewidth=3.8, foreground="#fdfcf8")]`

## 5. Python Implementation: `figkit.py`

`figkit.py` in this directory implements the rules above on top of `matplotlib`. Copy it, with `fonts/`, into the project's `tools/` directory. Do not use `mpl_toolkits.mplot3d`: its depth sorting is wrong for intersecting objects and it cannot produce the stroke tiers.

```python
from figkit import Scene, INDIGO, TERRACOTTA, great_circle, geodesic, unit

s = Scene(width=6.4, height=3.6, azim=-32, elev=20)   # an explicit orthographic camera
s.shadow((0, 0, -1.1), 1.0)                            # soft cast shadow on the ground
s.sphere((0, 0, 0), 1.0)                               # matte shading + vector silhouette
s.sphere_curve(great_circle((0, 0, 1)))                # solid in front, dashed behind
q = unit([0.8, -0.6, 0.12])
s.tangent_plane(1.002 * q, size=0.4)
s.arrow(q, q + 0.36 * unit([0, 0, 1]), color=INDIGO)
s.label(q, r"$q$", dx=9, dy=-10)                       # offset in points, paper halo
s.save("figures/ch01-example.svg")
```

What the kit provides:

| Call | What it does |
| :-- | :-- |
| `Scene(azim, elev)` | Orthographic camera. `project`, `depth`, `point_visible`. Limits are fitted to what was drawn. |
| `sphere` | Analytic normals, Lambert shading rendered to an embedded raster, exact circular silhouette as a vector stroke. Optional transparency for showing an interior. |
| `sphere_curve` | Splits a curve on a sphere into front and back by the sign of its depth. Front is solid, back is dashed and faded. |
| `ribbons` | Space curves that pass over and under each other (rings, linkages, knots). Pieces are depth-sorted and drawn over a paper understroke so the nearer strand visibly breaks the farther one. |
| `patch`, `tangent_plane` | Flat translucent polygons from 3D corners. |
| `arrow`, `frame`, `dot` | Vectors with filled heads sized in scene units, triads, markers (hollow for hidden points). |
| `label`, `text2d`, `pad_to` | Labels in outlined text with a paper-coloured halo. `pad_to` grows the canvas for wide labels. |
| `shadow` | Soft radial shadow, squashed by the camera elevation. |
| `new_plot`, `style_axes`, `halo` | Data plots in the same palette, weights and fonts. |
| `rot`, `hat`, `unit`, `great_circle`, `small_circle`, `geodesic` | Geometry helpers. |

### Rules the kit encodes, and why

- **Text is exported as outlines** (`svg.fonttype = "path"`). An SVG placed with `<img>` cannot load web fonts, so live text falls back to a default face and the figure no longer matches the page. Outlines look the same in every browser and in print. Use live text (`"none"`) only for SVG inlined into a page that is guaranteed to have the fonts.
- **The document's fonts are bundled** (`fonts/`, EB Garamond and Source Sans 3, both SIL OFL) and wired into mathtext, so `$T_qS^2$` in a label matches the prose. Words that are not mathematics use the sans face at 9 to 10 pt.
- **Shading is raster, lines are vector.** A sphere shaded with thousands of polygons makes a huge SVG with visible seams. One small embedded image under vector strokes is smaller and cleaner.
- **Visibility is computed.** On a sphere, a point faces the camera when `(p - center) . view >= 0`. For curves in space, sort short pieces by depth.
- **Output is deterministic** (fixed hash salt, no date), so regenerated figures do not churn version control.

### Composing a scene

1. Decide the one question the figure answers. Write the caption first.
2. Choose the camera so that nothing important is edge-on or on the silhouette. For a plane, keep the view direction within about 60° of its normal. For a point on a sphere, keep it well inside the front hemisphere.
3. Place geometry, then vectors, then labels. Offset labels with `dx`, `dy` in points.
4. Keep postfix `^\wedge`, `\mathcal` and a bare `\delta` out of labels: mathtext draws them badly in a text face. Use `\mathrm{\delta}` or words.
5. For a wide label near the edge, call `Scene.pad_to(points)` so the canvas grows to hold it.
6. **Render and look.** Rasterise the SVG and inspect it at the size it will be printed. Check for: labels on top of strokes, labels clipped at the edge, planes seen edge-on, arrows hidden under surfaces, two objects overlapping by accident, a hidden line drawn solid.
7. Fix and repeat. The first render is never right.

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
