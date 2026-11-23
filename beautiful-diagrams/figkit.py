"""Figure kit: geometry-first diagrams with a fixed visual grammar.

Every 2D coordinate comes from an explicit orthographic camera applied to real
3D geometry. Visibility on spheres is computed, never guessed. Text is written
as outlines so a figure looks identical in any browser and in print.


    from figkit import Scene
    s = Scene(width=6.4, height=3.6, azim=-35, elev=22)
    s.shadow((0, 0, -1.0), 1.0)
    s.sphere((0, 0, 0), 1.0)
    s.sphere_curve(great_circle((0, 0, 1)))
    s.arrow((0, 0, 1), (0.6, 0, 1), color=INDIGO)
    s.label((0.6, 0, 1), r"$\\omega$", dx=8, dy=4)
    s.save("figures/ch01-example.svg")
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import to_rgb
from matplotlib.patches import Circle, Polygon

# ---- palette (lipi/beautiful-diagrams, section 3) ----
INK = "#1a1a1a"
INDIGO = "#1b1f8a"
TERRACOTTA = "#c85a32"
TEAL = "#2a6f73"
OCHRE = "#b8891f"
MUTED = "#646873"
PAPER = "#fdfcf8"
ICE = "#c9d6ea"
PERIWINKLE = "#c7d0e8"
SAND = "#f1e6d0"
PEACH = "#f2c6a0"

# ---- stroke tiers in points (lipi/beautiful-diagrams, section 2) ----
LW_SILHOUETTE = 1.7
LW_VECTOR = 1.5
LW_CONTOUR = 0.8
LW_HIDDEN = 0.7
DASH = (0, (3.5, 3))

Z_SHADOW, Z_SURFACE, Z_HIDDEN, Z_CONTOUR, Z_SILHOUETTE, Z_VECTOR, Z_LABEL = 1, 10, 12, 14, 20, 30, 50

_FONT_DIR = Path(__file__).resolve().parent / "fonts"
for _f in _FONT_DIR.glob("*.ttf"):
    font_manager.fontManager.addfont(str(_f))

plt.rcParams.update({
    "svg.fonttype": "path",
    "svg.hashsalt": "book",
    "font.family": "EB Garamond",
    "font.size": 11,
    "mathtext.fontset": "custom",
    "mathtext.rm": "EB Garamond",
    "mathtext.it": "EB Garamond:italic",
    "mathtext.bf": "EB Garamond:bold",
    "mathtext.cal": "EB Garamond:italic",
    "mathtext.fallback": "stix",
    "axes.unicode_minus": False,
})


# ---------------------------------------------------------------- geometry
def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def hat(v):
    x, y, z = v
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], float)


def rot(axis, angle):
    """Rotation matrix exp(angle * hat(axis)) by Rodrigues' formula."""
    K = hat(unit(axis))
    return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K


def great_circle(normal, n=240):
    """Points of the unit great circle perpendicular to `normal`."""
    nrm = unit(normal)
    a = unit(np.cross(nrm, [0.3, 0.5, 0.81]))
    b = np.cross(nrm, a)
    t = np.linspace(0, 2 * np.pi, n)
    return np.outer(np.cos(t), a) + np.outer(np.sin(t), b)


def small_circle(axis, polar, n=240):
    """Circle of constant polar angle about `axis` on the unit sphere."""
    nrm = unit(axis)
    return np.cos(polar) * nrm + np.sin(polar) * great_circle(nrm, n)


def geodesic(p, q, n=80, long_way=False):
    """Great-circle arc between unit vectors p and q."""
    p, q = unit(p), unit(q)
    ang = np.arccos(np.clip(p @ q, -1, 1))
    axis = unit(np.cross(p, q))
    if long_way:
        ang = ang - 2 * np.pi
    return np.array([rot(axis, t) @ p for t in np.linspace(0, ang, n)])


# ------------------------------------------------------------------- scene
class Scene:
    """An orthographic camera plus a 2D canvas that obeys the stroke tiers."""

    def __init__(self, width=6.4, height=3.6, azim=-35.0, elev=22.0,
                 xlim=None, ylim=None, light=(-0.45, -0.35, 0.82)):
        az, el = np.radians(azim), np.radians(elev)
        self.view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        self.right = np.array([-np.sin(az), np.cos(az), 0.0])
        self.up = np.cross(self.view, self.right)
        self.light_cam = unit(light)  # in camera axes: right, up, toward viewer
        self.fig = plt.figure(figsize=(width, height))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self._lims = (xlim, ylim)
        self._pts = []

    # -- projection
    def project(self, p):
        p = np.atleast_2d(np.asarray(p, float))
        xy = np.stack([p @ self.right, p @ self.up], axis=1)
        self._pts.append(xy)
        return xy

    def depth(self, p):
        return np.atleast_2d(np.asarray(p, float)) @ self.view

    # -- surfaces
    def sphere(self, center=(0, 0, 0), radius=1.0, color=PERIWINKLE, res=420, outline=True, alpha=1.0):
        """Matte shaded sphere: analytic normals, raster shading, vector silhouette."""
        c = self.project(center)[0]
        g = np.linspace(-1, 1, res)
        X, Y = np.meshgrid(g, -g)
        r2 = X**2 + Y**2
        Zc = np.sqrt(np.clip(1 - r2, 0, 1))
        lam = np.clip(X * self.light_cam[0] + Y * self.light_cam[1] + Zc * self.light_cam[2], 0, 1)
        shade = 0.42 + 0.58 * lam
        base = np.array(to_rgb(color))
        dark = base * np.array([0.60, 0.64, 0.80])
        light = 1 - (1 - base) * 0.30
        img = np.zeros((res, res, 4))
        img[..., :3] = dark + (light - dark) * shade[..., None]
        edge = np.clip((1 - np.sqrt(r2)) * res / 2, 0, 1)
        img[..., 3] = edge * alpha
        self.ax.imshow(img, extent=[c[0] - radius, c[0] + radius, c[1] - radius, c[1] + radius],
                       zorder=Z_SURFACE, interpolation="bilinear")
        if outline:
            self.ax.add_patch(Circle(c, radius, fill=False, ec=INK, lw=LW_SILHOUETTE, zorder=Z_SILHOUETTE))
        self._pts.append(np.array([c - radius, c + radius]))

    def shadow(self, center, radius, strength=0.22, squash=None):
        """Soft cast shadow of a blob of the given radius on a horizontal plane."""
        c = self.project(center)[0]
        squash = abs(self.view[2]) if squash is None else squash
        g = np.linspace(-1, 1, 200)
        X, Y = np.meshgrid(g, g)
        fall = np.clip(1 - np.sqrt(X**2 + Y**2), 0, 1) ** 1.6
        img = np.zeros((200, 200, 4))
        img[..., :3] = to_rgb("#2c3248")
        img[..., 3] = strength * fall
        rx, ry = radius * 1.25, radius * 1.25 * max(squash, 0.18)
        self.ax.imshow(img, extent=[c[0] - rx, c[0] + rx, c[1] - ry, c[1] + ry],
                       zorder=Z_SHADOW, interpolation="bilinear")
        self._pts.append(np.array([[c[0] - rx, c[1] - ry], [c[0] + rx, c[1] + ry]]))

    def patch(self, corners, color=SAND, alpha=0.75, edge=INK, lw=LW_CONTOUR, zorder=Z_CONTOUR - 1):
        """Flat polygon (a tangent plane, a face) from 3D corners."""
        xy = self.project(corners)
        self.ax.add_patch(Polygon(xy, closed=True, fc=color, alpha=alpha, ec="none", zorder=zorder))
        self.ax.add_patch(Polygon(xy, closed=True, fill=False, ec=edge, lw=lw, alpha=0.8,
                                  zorder=zorder + 0.1, joinstyle="round"))

    def tangent_plane(self, point, size=0.55, center=(0, 0, 0), spin=0.0, **kw):
        """Square patch tangent to a sphere at `point`. Returns its in-plane axes."""
        n = unit(np.asarray(point, float) - np.asarray(center, float))
        a = unit(np.cross(n, [0.0, 0.0, 1.0])) if abs(n[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
        a = rot(n, spin) @ a
        b = np.cross(n, a)
        p = np.asarray(point, float)
        self.patch([p + size * (a + b), p + size * (-a + b), p + size * (-a - b), p + size * (a - b)], **kw)
        return a, b

    # -- curves
    def curve(self, pts, color=INK, lw=LW_CONTOUR, hidden=False, alpha=None, zorder=None, **kw):
        xy = self.project(pts)
        style = dict(color=color, lw=LW_HIDDEN if hidden else lw, solid_capstyle="round",
                     dash_capstyle="round", solid_joinstyle="round",
                     alpha=(0.55 if hidden else 0.9) if alpha is None else alpha,
                     zorder=(Z_HIDDEN if hidden else Z_CONTOUR) if zorder is None else zorder)
        if hidden:
            style["linestyle"] = DASH
        style.update(kw)
        self.ax.plot(xy[:, 0], xy[:, 1], **style)

    def sphere_curve(self, pts, center=(0, 0, 0), color=INK, lw=LW_CONTOUR, show_hidden=True, zorder=None, **kw):
        """Curve on a sphere: solid where it faces the camera, dashed where it does not."""
        pts = np.asarray(pts, float)
        front = (pts - np.asarray(center, float)) @ self.view >= 0
        start = 0
        for i in range(1, len(pts) + 1):
            if i == len(pts) or front[i] != front[start]:
                seg = pts[max(start - 1, 0):min(i + 1, len(pts))] if front[start] else pts[start:i]
                if len(seg) > 1:
                    if front[start]:
                        self.curve(seg, color=color, lw=lw, zorder=zorder, **kw)
                    elif show_hidden:
                        self.curve(seg, color=color, hidden=True)
                start = i

    def ribbons(self, curves, gap=2.6, zorder=Z_CONTOUR):
        """Space curves that pass over and under each other (rings, knots, linkages).

        `curves` is a list of (points, color, linewidth). Every curve is cut into
        short pieces, all pieces are sorted by depth, and each is drawn over a
        paper-coloured understroke, so nearer strands visibly break farther ones.
        """
        pieces = []
        for pts, color, lw in curves:
            pts = np.asarray(pts, float)
            xy = self.project(pts)
            dep = pts @ self.view
            for i in range(len(pts) - 1):
                pieces.append((0.5 * (dep[i] + dep[i + 1]), xy[i:i + 2], color, lw))
        pieces.sort(key=lambda piece: piece[0])
        for k, (_, seg, color, lw) in enumerate(pieces):
            z = zorder + 5e-4 * k
            self.ax.plot(seg[:, 0], seg[:, 1], color=PAPER, lw=lw + gap, solid_capstyle="butt", zorder=z)
            self.ax.plot(seg[:, 0], seg[:, 1], color=color, lw=lw, solid_capstyle="round", zorder=z + 2e-4)

    def point_visible(self, p, center=(0, 0, 0)):
        return float((np.asarray(p, float) - np.asarray(center, float)) @ self.view) >= 0

    # -- marks
    def arrow(self, p0, p1, color=INDIGO, lw=LW_VECTOR, head=0.11, zorder=Z_VECTOR, alpha=1.0, dashed=False):
        """Arrow between 3D points. The head is a filled triangle sized in scene units."""
        a, b = self.project([p0, p1])
        d = b - a
        length = np.hypot(*d)
        if length < 1e-9:
            return
        d = d / length
        head = min(head, 0.6 * length)
        base = b - head * d
        nrm = np.array([-d[1], d[0]]) * head * 0.36
        self.ax.plot([a[0], base[0]], [a[1], base[1]], color=color, lw=lw, solid_capstyle="round",
                     zorder=zorder, alpha=alpha, linestyle=DASH if dashed else "-")
        self.ax.add_patch(Polygon([b, base + nrm, base - nrm], closed=True, fc=color, ec=color,
                                  lw=0.4, zorder=zorder, alpha=alpha, joinstyle="round"))

    def dot(self, p, color=INK, size=4.2, zorder=Z_VECTOR + 1, hollow=False):
        xy = self.project(p)[0]
        self.ax.plot([xy[0]], [xy[1]], "o", ms=size, mfc=PAPER if hollow else color, mec=color,
                     mew=1.0, zorder=zorder)

    def frame(self, origin, R, length=0.5, colors=(TERRACOTTA, TEAL, INDIGO), labels=None, lw=LW_VECTOR, **kw):
        """Right-handed triad: columns of R drawn from `origin`."""
        o = np.asarray(origin, float)
        R = np.asarray(R, float)
        for i in range(3):
            tip = o + length * R[:, i]
            self.arrow(o, tip, color=colors[i], lw=lw, **kw)
            if labels:
                self.label(o + (length + 0.12) * R[:, i], labels[i], color=colors[i])

    def label(self, p, text, dx=0, dy=0, color=INK, size=11, ha="center", va="center", halo=PAPER, **kw):
        """Label at a 3D point, offset in points, with a paper-coloured halo."""
        xy = self.project(p)[0]
        self.ax.annotate(text, xy, xytext=(dx, dy), textcoords="offset points", color=color,
                         fontsize=size, ha=ha, va=va, zorder=Z_LABEL,
                         path_effects=[pe.withStroke(linewidth=3.2, foreground=halo)], **kw)

    def text2d(self, x, y, text, **kw):
        """Label at canvas coordinates (same units as projected points)."""
        style = dict(fontsize=11, ha="center", va="center", color=INK, zorder=Z_LABEL,
                     path_effects=[pe.withStroke(linewidth=3.2, foreground=PAPER)])
        style.update(kw)
        self.ax.text(x, y, text, **style)
        self._pts.append(np.array([[x - 0.75, y - 0.15], [x + 0.75, y + 0.15]]))

    def pad_to(self, points):
        """Grow the canvas to include these 3D points (room for wide labels)."""
        self.project(points)

    # -- output
    def finalize(self, pad=0.12):
        """Fix the canvas limits. Called by save() and by animate()."""
        xlim, ylim = self._lims
        if xlim is None or ylim is None:
            allpts = np.vstack(self._pts)
            lo, hi = allpts.min(axis=0) - pad, allpts.max(axis=0) + pad
            xlim = xlim or (lo[0], hi[0])
            ylim = ylim or (lo[1], hi[1])
        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(*ylim)
        return self.fig

    def save(self, path, pad=0.12):
        xlim, ylim = self._lims
        if xlim is None or ylim is None:
            allpts = np.vstack(self._pts)
            lo, hi = allpts.min(axis=0) - pad, allpts.max(axis=0) + pad
            xlim = xlim or (lo[0], hi[0])
            ylim = ylim or (lo[1], hi[1])
        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(*ylim)
        save(self.fig, path)


# ------------------------------------------------------------------- plots
def new_plot(width=6.4, height=3.0, ncols=1, nrows=1, **kw):
    """Axes for data plots in the same visual language as the 3D scenes."""
    fig, axes = plt.subplots(nrows, ncols, figsize=(width, height), **kw)
    for ax in np.atleast_1d(axes).ravel():
        style_axes(ax)
    return fig, axes


def style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK, width=0.8, length=3, labelsize=9)
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontfamily("Source Sans 3")
    ax.set_facecolor("none")


def halo(linewidth=3.2, color=PAPER):
    return [pe.withStroke(linewidth=linewidth, foreground=color)]


def save(fig, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", transparent=True, dpi=220, metadata={"Date": None})
    plt.close(fig)
    print(f"wrote {path}")


# -------------------------------------------------------------- animation
def _render(obj, width_px):
    """Rasterise a Scene or a Figure to an RGBA image of the given pixel width."""
    import io

    from PIL import Image

    fig = obj.finalize() if isinstance(obj, Scene) else obj
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, dpi=width_px / fig.get_figwidth())
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def animate(make_frame, gif_path, strip_path, n=72, fps=12, width_px=640,
            stills=(0.0, 0.34, 0.67, 1.0), hold=1.2, strip_px=560, strip_cols=None, colors=128):
    """One piece of code, two assets: a looping GIF for the web and a filmstrip for print.

    `make_frame(t)` builds and returns a Scene (or a matplotlib Figure) for
    t in [0, 1]. It must not save or close it. Give every frame the SAME canvas:
    pass fixed `xlim` and `ylim` to Scene, or the picture will jitter.

    The GIF plays the n frames at `fps` and holds the last one for `hold`
    seconds. The strip tiles the frames at the times in `stills` on a transparent
    background, for the PDF and for readers who turn motion off. Wide frames read
    better in a grid: set `strip_cols=2`.
    A frame that should carry a caption ("step 2: turn about z") draws it itself.
    """
    from PIL import Image

    gif_path, strip_path = Path(gif_path), Path(strip_path)
    gif_path.parent.mkdir(parents=True, exist_ok=True)
    paper = Image.new("RGBA", (1, 1), PAPER)

    frames = []
    for i in range(n):
        img = _render(make_frame(i / (n - 1)), width_px)
        flat = Image.new("RGBA", img.size, paper.getpixel((0, 0)))
        flat.alpha_composite(img)
        frames.append(flat.convert("RGB"))
    # One palette for the whole loop, taken from a montage of sampled frames, so colours do not flicker.
    sample = frames[:: max(1, n // 8)]
    # Accent colours cover few pixels, so a median cut would drop them. Give each a swatch.
    accents = [INK, INDIGO, TERRACOTTA, TEAL, OCHRE, MUTED, PAPER]
    swatch = sample[0].height // 2
    montage = Image.new("RGB", (sample[0].width, sample[0].height * len(sample) + swatch * len(accents)))
    for k, fr in enumerate(sample):
        montage.paste(fr, (0, k * fr.height))
    for k, col in enumerate(accents):
        montage.paste(Image.new("RGB", (sample[0].width, swatch), col), (0, sample[0].height * len(sample) + k * swatch))
    palette = montage.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    quantized = [fr.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG) for fr in frames]
    durations = [int(1000 / fps)] * n
    durations[-1] = int(1000 * hold)
    quantized[0].save(gif_path, save_all=True, append_images=quantized[1:], duration=durations,
                      loop=0, optimize=True, disposal=1)

    panels = [_render(make_frame(t), strip_px) for t in stills]
    gap = strip_px // 28
    cols = strip_cols or len(panels)
    rows = -(-len(panels) // cols)
    w, h = panels[0].size
    strip = Image.new("RGBA", (cols * w + gap * (cols - 1), rows * h + gap * (rows - 1)), (0, 0, 0, 0))
    for k, p in enumerate(panels):
        strip.alpha_composite(p, ((k % cols) * (w + gap), (k // cols) * (h + gap)))
    strip.save(strip_path, optimize=True)
    print(f"wrote {gif_path} ({gif_path.stat().st_size / 1e6:.1f} MB, {n} frames) and {strip_path}")


def ease(t):
    """Smooth start and stop for a motion parameter in [0, 1]."""
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def phase(t, start, end):
    """Progress of a sub-interval [start, end] of the timeline, clipped to [0, 1]."""
    return float(np.clip((t - start) / (end - start), 0.0, 1.0))


def quadrotor(scene, x, R, arm=0.5, color=INK, lw=1.9, dashed=False, zorder=34):
    """A quadrotor drawn from its real pose, the same way in every chapter.

    Two arms along the body axes R e_1 and R e_2, and four rotor rings of radius
    0.36 arm in the plane of the arms. `dashed=True` draws a desired pose.
    """
    x, R = np.asarray(x, float), np.asarray(R, float)
    kw = dict(color=color, alpha=1.0, zorder=zorder)
    if dashed:
        kw["linestyle"] = DASH
    th = np.linspace(0, 2 * np.pi, 48)
    for d in (R[:, 0], R[:, 1]):
        scene.curve(np.array([x - arm * d, x + arm * d]), lw=lw, **kw)
    for d in (R[:, 0], -R[:, 0], R[:, 1], -R[:, 1]):
        c = x + arm * d + 0.04 * arm * R[:, 2]
        ring = c + 0.36 * arm * (np.outer(np.cos(th), R[:, 0]) + np.outer(np.sin(th), R[:, 1]))
        scene.curve(ring, lw=0.55 * lw, **kw)
