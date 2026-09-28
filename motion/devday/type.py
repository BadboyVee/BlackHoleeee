"""Type built the way the teaser builds it: a glyph's points arrive first, its outline joins them up, then it
fills. The points are the ones a type designer draws (corners and extremes), taken from the font's own outlines.
Between two lines the points fly from one to the other, which is how every title in the list turns into the next."""
import math
from functools import lru_cache

import numpy as np
import skia

from engine import gfx as G
from engine.core import clamp, hash01
from .look import F


# ---------------------------------------------------------------- the nodes of an outline

def nodes(path, corner_deg=28.0, axis_tol=0.08):
    """On-curve points at corners and at horizontal or vertical extremes, the way a type designer places them."""
    contours, cur = [], []
    it = skia.Path.Iter(path, False)
    while True:
        verb, pts = it.next()
        if verb == skia.Path.kDone_Verb:
            break
        if verb == skia.Path.kMove_Verb:
            if cur:
                contours.append(cur)
            cur = []
        elif verb == skia.Path.kClose_Verb:
            if cur:
                contours.append(cur)
            cur = []
        else:
            cur.append((verb, [(p.x(), p.y()) for p in pts]))
    if cur:
        contours.append(cur)
    out = []
    cos_c = math.cos(math.radians(corner_deg))
    for segs in contours:
        n = len(segs)
        for i, (verb, pts) in enumerate(segs):
            nverb, npts = segs[(i + 1) % n]
            tin = (pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])
            tout = (npts[1][0] - npts[0][0], npts[1][1] - npts[0][1])
            li, lo = math.hypot(*tin), math.hypot(*tout)
            if li < 1e-6 or lo < 1e-6:
                continue
            corner = (tin[0] * tout[0] + tin[1] * tout[1]) / (li * lo) < cos_c
            flat = abs(tin[1]) / li < axis_tol and abs(tout[1]) / lo < axis_tol
            upright = abs(tin[0]) / li < axis_tol and abs(tout[0]) / lo < axis_tol
            curved = verb != skia.Path.kLine_Verb or nverb != skia.Path.kLine_Verb
            if corner or ((flat or upright) and curved):
                out.append(pts[-1])
    if len(out) < 2:                      # a shape with no corners or extremes: take a few points round it
        m = skia.PathMeasure(path, True)
        L = m.getLength()
        if L > 0:
            for k in range(4):
                ok, pos, _ = m.getPosTan(L * k / 4)
                if ok:
                    out.append((pos.x(), pos.y()))
    return out


class Glyph:
    __slots__ = ("path", "pts", "col", "cx", "rank")

    def __init__(self, path, pts, col, cx):
        self.path, self.pts, self.col, self.cx, self.rank = path, pts, col, cx, 0.0


class Word:
    """A line of type laid out once: each glyph's outline in frame space, its colour and its nodes.
    parts is [(text, colour), ...]; gaps adds space after a part (the teaser sets its brackets apart)."""

    def __init__(self, parts, size, x, y, align=0.5, fam="gsans", axes=(), gaps=(), tracking=0.0):
        font = F(fam, size, **dict(axes))
        gaps = dict(gaps)
        runs = [font.shape(s, tracking) for s, _ in parts]
        total = sum(r.width for r in runs) + sum(gaps.values())
        x0 = x - total * align
        self.size, self.font, self.x0, self.x1, self.y = size, font, x0, x0 + total, y
        self.glyphs = []
        cx = x0
        for i, ((s, col), run) in enumerate(zip(parts, runs)):
            for _, gid, gx, adv in run.glyphs():
                gp = font.glyph_path(gid)
                if gp is None or gp.countVerbs() == 0:
                    continue
                p = skia.Path(gp)
                p.offset(cx + gx, y)
                self.glyphs.append(Glyph(p, np.array(nodes(p), float), col, cx + gx + adv / 2))
            cx += run.width + gaps.get(i, 0.0)
        span = max(self.x1 - self.x0, 1.0)
        for g in self.glyphs:
            g.rank = clamp((g.cx - self.x0) / span)
        self.pts = np.concatenate([g.pts for g in self.glyphs]) if self.glyphs else np.zeros((0, 2))
        self.owner = np.concatenate([np.full(len(g.pts), i) for i, g in enumerate(self.glyphs)]) \
            if self.glyphs else np.zeros(0, int)
        self.rank = np.array([self.glyphs[i].rank for i in self.owner]) if self.glyphs else np.zeros(0)

    @property
    def dot_r(self):
        return max(2.2, 0.048 * self.size)

    @property
    def line_w(self):
        return max(1.3, 0.0095 * self.size)

    def bounds(self):
        b = skia.Rect.MakeEmpty()
        for g in self.glyphs:
            b.join(g.path.getBounds())
        return b


@lru_cache(maxsize=256)
def word(parts, size, x, y, align=0.5, fam="gsans", axes=(), gaps=(), tracking=0.0):
    return Word(parts, size, x, y, align, fam, axes, gaps, tracking)


# ---------------------------------------------------------------- building a line

class Build:
    """When each glyph of a word gets its points, its outline, its fill, and when it gives them back.
    t_in is when the first glyph's points land; spread is how long the sweep takes from the first glyph to the
    last. t_out (optional) is when the fill starts giving way to points again, sweeping the same way."""

    def __init__(self, t_in, spread=0.3, outline=0.07, fill=0.17, dots_off=0.3, t_out=None, spread_out=None,
                 hold_dots=False, fill_spread=None, pop=0.05):
        self.t_in, self.spread, self.outline, self.fill, self.dots_off = t_in, spread, outline, fill, dots_off
        self.t_out = t_out
        self.spread_out = spread if spread_out is None else spread_out
        self.fill_spread = spread if fill_spread is None else fill_spread
        self.hold_dots = hold_dots
        self.pop = pop

    def glyph(self, rank, t):
        """(dots, outline, fill) strengths of a glyph at this rank."""
        tau = t - (self.t_in + self.spread * rank)
        if tau < 0:
            return 0.0, 0.0, 0.0
        tf = t - (self.t_in + self.fill_spread * rank)       # the fill may sweep more slowly than the points
        dots = clamp(tau / self.pop) if self.pop > 0 else 1.0
        if not self.hold_dots:
            dots *= 1 - clamp((tf - self.dots_off) / 0.1)
        outline = clamp((tau - self.outline) / 0.04) * (1 - clamp((tf - self.fill - 0.05) / 0.06))
        fill = clamp((tf - self.fill) / 0.05)
        if self.t_out is not None:
            to = t - (self.t_out + self.spread_out * rank)
            if to >= 0:
                k = clamp(to / 0.04)
                fill *= 1 - k
                outline *= 1 - k
                dots = max(dots, k)
        return dots, outline, fill


def draw_word(c, w, t, build, dot_col, a=1.0, dots=True, fill_col=None, dot_scale=1.0, first=0, last=None):
    """Draw a word at time t under a Build. With dots=False the points are left to a Flight. Glyphs outside
    first..last are already built and simply drawn filled."""
    if a <= 0:
        return
    lw, dr = w.line_w, w.dot_r * dot_scale
    for gi, g in enumerate(w.glyphs):
        if gi < first or (last is not None and gi >= last):
            c.drawPath(g.path, G.P(fill_col or g.col, a))
            continue
        d, o, f = build.glyph(g.rank, t)
        col = fill_col or g.col
        if f > 0:
            c.drawPath(g.path, G.P(col, f * a))
        if o > 0:
            c.drawPath(g.path, G.P(col, o * a, stroke=lw))
        if dots and d > 0 and len(g.pts):
            p = G.P(dot_col, a)
            r = dr * (0.35 + 0.65 * d) if d < 1 else dr
            if d < 1:
                p.setAlphaf(clamp(a * (0.3 + 0.7 * d)))
            for x, y in g.pts:
                c.drawCircle(x, y, r, p)


def draw_filled(c, w, a=1.0, col=None):
    if a <= 0:
        return
    for g in w.glyphs:
        c.drawPath(g.path, G.P(col or g.col, a))


# ---------------------------------------------------------------- points in flight

def _out_cubic(u):
    return 1 - (1 - u) ** 3


class Flight:
    """Points flying from src to dst, each on its own clock, swelling on the way like the teaser's."""

    def __init__(self, src, dst, t0, dur, col0, col1=None, r0=4.0, r1=None, swell=0.9, bend=0.0, seed=0,
                 fade_in=0.0):
        self.src = np.asarray(src, float).reshape(-1, 2)
        self.dst = np.asarray(dst, float).reshape(-1, 2)
        n = len(self.src)
        self.t0 = np.broadcast_to(np.asarray(t0, float), (n,)).copy()
        self.dur = np.broadcast_to(np.asarray(dur, float), (n,)).copy()
        self.c0 = np.array(G.rgb(col0))
        self.c1 = np.array(G.rgb(col1 or col0))
        self.r0 = np.broadcast_to(np.asarray(r0, float), (n,)).copy()
        self.r1 = np.broadcast_to(np.asarray(r1 if r1 is not None else r0, float), (n,)).copy()
        self.swell = np.broadcast_to(np.asarray(swell, float), (n,)).copy()
        d = self.dst - self.src
        perp = np.stack([-d[:, 1], d[:, 0]], 1)
        side = np.where(hash01(np.arange(n), seed) < 0.5, -1.0, 1.0)
        self.perp = perp * (bend * side * (0.4 + 0.6 * hash01(np.arange(n), seed + 3)))[:, None]
        self.fade_in = fade_in

    def state(self, t):
        u = np.clip((t - self.t0) / np.maximum(self.dur, 1e-6), 0.0, 1.0)
        e = _out_cubic(u)
        s = np.sin(np.pi * u)
        pos = self.src + (self.dst - self.src) * e[:, None] + self.perp * s[:, None]
        r = (self.r0 + (self.r1 - self.r0) * e) * (1 + self.swell * s)
        return u, e, pos, r

    def draw(self, c, t, a=1.0, only_moving=False, waiting=False):
        """waiting=True also draws the points that have not left yet, where they wait."""
        if a <= 0:
            return
        u, e, pos, r = self.state(t)
        live = np.ones(len(u), bool) if waiting else t >= self.t0 - (self.fade_in if self.fade_in else 0)
        if only_moving:
            live &= u < 1
        p = skia.Paint(AntiAlias=True)
        for i in np.nonzero(live)[0]:
            k = e[i]
            col = self.c0 + (self.c1 - self.c0) * k
            al = a
            if self.fade_in and t < self.t0[i] + self.fade_in:
                al *= clamp((t - self.t0[i] + self.fade_in) / self.fade_in)
            p.setColor4f(skia.Color4f(col[0], col[1], col[2], clamp(al)))
            c.drawCircle(float(pos[i, 0]), float(pos[i, 1]), float(max(r[i], 0.0)), p)


def pair_index(src_pts, dst_pts):
    """Match two point sets left to right, so every source point goes somewhere and every target gets one;
    the indices into each."""
    a = np.asarray(src_pts, float).reshape(-1, 2)
    b = np.asarray(dst_pts, float).reshape(-1, 2)
    if len(a) == 0 or len(b) == 0:
        return np.zeros(0, int), np.zeros(0, int)
    ia = np.argsort(a[:, 0] + 0.001 * a[:, 1], kind="stable")
    ib = np.argsort(b[:, 0] + 0.001 * b[:, 1], kind="stable")
    m = max(len(a), len(b))
    k = np.arange(m)
    return ia[k * len(a) // m], ib[k * len(b) // m]


def pair(src_pts, dst_pts):
    a = np.asarray(src_pts, float).reshape(-1, 2)
    b = np.asarray(dst_pts, float).reshape(-1, 2)
    i, j = pair_index(a, b)
    return a[i], b[j]
