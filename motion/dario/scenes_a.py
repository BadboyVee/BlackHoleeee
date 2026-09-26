"""Prologue, 01 PHYSICS, 02 SAFETY, 03 SCALE."""
import math

import numpy as np
import skia

from engine import gfx as G
from engine.core import (clamp, lerp, snap, whip, out_expo, in_expo, out_cubic, in_out_cubic, out_back,
                         W, H, CX, CY, hash01)
from engine.three import Cam
from .common import INK, PAPER, PAGE, CLAY, KRAFT, DIM, fill, blur_in, chapter, kick_env, spike_wave
from .score import G as GR, SPIKES, T_PHYS, T_SAFE, T_SCALE, T_ANTH

# ---------------------------------------------------------------- prologue: it started with neurons

WORD_TIMES = [0.45, 1.2]
COLLAPSE_T = T_PHYS - 0.45
_rng = np.random.default_rng(3)
TRACE_SPIKES = [np.array(SPIKES)]
for k in range(1, 9):
    extra = np.sort(_rng.uniform(0.2, GR.at(2), 7))
    shifted = np.array(SPIKES) + _rng.normal(0, 0.006, len(SPIKES))
    keep = (_rng.random(len(SPIKES)) < 0.5) | (shifted > GR.at(2))
    TRACE_SPIKES.append(np.sort(np.concatenate([shifted[keep], extra])))


def trace(c, t, k, y0, x0, x1, amp, alpha, squeeze=0.0):
    n = 900
    taus = np.linspace(t - 2.0, t, n)
    base = (3.0 * np.sin(taus * 41 + k * 1.7) + 2.2 * np.sin(taus * 97 + k * 0.6) + 1.4 * np.sin(taus * 173 + k * 2.9))
    y = base.copy()
    for ts in TRACE_SPIKES[k]:
        if t - 2.0 - 0.02 < ts < t:
            dt = taus - ts
            m = (dt > -0.004) & (dt < 0.02)
            y[m] += amp * (-np.exp(-((dt[m] - 0.0015) / 0.0011) ** 2) + 0.38 * np.exp(-((dt[m] - 0.0055) / 0.0028) ** 2))
    xs = np.linspace(x0, x1, n)
    xs = CX + (xs - CX) * (1 - squeeze)
    ys = CY + (y0 + y - CY) * (1 - squeeze)
    path = skia.Path()
    path.addPoly([skia.Point(float(a), float(b)) for a, b in zip(xs, ys)], False)
    c.drawPath(path, G.P(PAPER, alpha, stroke=1.6, join="round"))
    return xs[-1], ys[-1]


def s_prologue(c, t):
    fill(c, INK)
    sq = in_expo(clamp((t - COLLAPSE_T) / 0.4))
    spread = snap(clamp((t - GR.at(2)) / 0.6))
    n = 1 + int(8 * spread + 0.999) if spread > 0 else 1
    ytr = 690
    for k in range(n):
        off = (k - 0) * 0
        if k > 0:
            side = 1 if k % 2 else -1
            off = side * ((k + 1) // 2) * 46 * spread
        a = 0.95 if k == 0 else 0.45 * spread
        hx, hy = trace(c, t, k, ytr + off, 150, 1770, 150 if k == 0 else 70, a * (1 - sq * 0.5), sq)
        if k == 0:
            last = max([s for s in SPIKES if s <= t] or [-9])
            glow = math.exp(-(t - last) / 0.08)
            G.circle(c, hx, hy, 5 + 7 * glow, G.P(CLAY))
            G.circle(c, hx, hy, 18 + 26 * glow, G.P(CLAY, 0.25 * glow))
    la = clamp(t / 0.4) * (1 - sq)
    fm = G.Font("mono", 15, wght=600)
    G.text(c, "CH 01  ·  20 KHZ  ·  50 µV/DIV  ·  PRINCETON, NJ", 150, ytr - 190, fm, G.P(PAPER, 0.55 * la), tracking=0.2)
    c.drawLine(150, ytr - 170, 150 + 1620 * snap(la), ytr - 170, G.P(PAPER, 0.15 * la, stroke=1))
    # the line
    f = G.Font("fraunces-italic", 150, wght=340, opsz=144, SOFT=100, WONK=1)
    line = "It started with neurons."
    run = f.shape(line)
    split = len("It started ")
    starts = [WORD_TIMES[0] + i * 0.045 if i < split else WORD_TIMES[1] + (i - split) * 0.045 for i in range(len(run.gids))]
    up = 60 * in_expo(clamp((t - COLLAPSE_T + 0.1) / 0.4))
    a = 1 - clamp((t - COLLAPSE_T) / 0.3)
    if a > 0:
        x = CX - run.width / 2
        with G.xf(c, 0, -up):
            for i, gid, gx, adv in run.glyphs():
                col = CLAY if i >= len("It started with ") else PAPER
                u = clamp((t - starts[i]) / 0.45)
                if u <= 0:
                    continue
                e = snap(u)
                sig = 14 * (1 - e)
                p = G.P(col, a * min(1, u * 1.6))
                if sig > 0.4:
                    with G.layer(c, blur=sig):
                        G.glyph(c, f, gid, x + gx, 420 + 40 * (1 - e), p)
                else:
                    G.glyph(c, f, gid, x + gx, 420 + 40 * (1 - e), p)


# ---------------------------------------------------------------- 01 PHYSICS

PHYS_ENTRY = [T_PHYS + 0.35, T_PHYS + 1.1]
N_NEU = 40
_r2 = np.random.default_rng(11)
RASTER = []
_beats = [T_PHYS + b * GR.spb for b in range(-4, 12)]
for i in range(N_NEU):
    ts = list(np.cumsum(_r2.exponential(1 / 3.2, 60)) + T_PHYS - 3.0)
    sync = [b + _r2.normal(0, 0.006) for b in _beats if _r2.random() < 0.62]
    RASTER.append((np.array(ts), np.array(sync)))


def raster(c, t, x0, y0, w, h, alpha):
    win = 2.4
    c.drawRect(skia.Rect.MakeXYWH(x0, y0, w, h), G.P(PAPER, 0.18 * alpha, stroke=1.2))
    for b in _beats:
        if t - win < b < t:
            x = x0 + w * (1 - (t - b) / win)
            c.drawLine(x, y0, x, y0 + h, G.P(CLAY, 0.18 * alpha, stroke=1.2))
    rowh = h / N_NEU
    tick = G.P(PAPER, 0.8 * alpha, stroke=1.6)
    hot = G.P(CLAY, alpha, stroke=2.2)
    for i, (ts, sync) in enumerate(RASTER):
        y = y0 + (i + 0.5) * rowh
        for arr, p in ((ts, tick), (sync, hot)):
            m = (arr > t - win) & (arr < t)
            for s in arr[m]:
                x = x0 + w * (1 - (t - s) / win)
                c.drawLine(x, y - rowh * 0.36, x, y + rowh * 0.36, p)
    fm = G.Font("mono", 14, wght=600)
    G.text(c, "NEURON", x0 - 18, y0 + 6, fm, G.P(PAPER, 0.5 * alpha), align=1.0, tracking=0.2, anchor="top")
    G.text(c, "TIME  →", x0 + w, y0 + h + 30, fm, G.P(PAPER, 0.5 * alpha), align=1.0, tracking=0.2)
    G.text(c, "40 CELLS  ·  SYNCHRONY ON THE BEAT", x0, y0 + h + 30, fm, G.P(CLAY, 0.8 * alpha), tracking=0.2)


def s_physics(c, t):
    fill(c, INK)
    chapter(c, t, T_PHYS, "01", "PHYSICS", PAPER, CLAY)
    rows = [("Stanford", "B.S.  ·  PHYSICS"), ("Princeton", "PH.D.  ·  NEURAL CIRCUITS")]
    f = G.Font("fraunces", 124, wght=380, opsz=144, SOFT=50)
    fm = G.Font("mono", 20, wght=650)
    for k, (school, deg) in enumerate(rows):
        t0 = PHYS_ENTRY[k]
        if t < t0 - 0.1:
            continue
        y = 470 + k * 250
        ln = snap(clamp((t - t0 + 0.1) / 0.5))
        c.drawLine(150, y - 130, 150 + 720 * ln, y - 130, G.P(PAPER, 0.25, stroke=1.2))
        G.text(c, f"0{k + 1}", 150, y - 100, G.Font("mono", 14, wght=700), G.P(CLAY, ln), tracking=0.2)
        blur_in(c, f.shape(school), 146, y, PAPER, t, t0, stagger=0.035)
        G.text(c, G.scramble(deg, clamp((t - t0 - 0.2) / 0.4), k, t), 152, y + 56, fm, G.P(PAPER, 0.85), tracking=0.24)
    ra = snap(clamp((t - T_PHYS - 0.2) / 0.5))
    raster(c, t, 1010, 300 + 40 * (1 - ra), 760, 470, ra)


# ---------------------------------------------------------------- 02 SAFETY

PAPER_TITLE = "Concrete Problems in AI Safety"
SAFE_TYPE0 = T_SAFE + 0.3
SAFE_TYPE_DUR = 0.7
SAFE_HILITE = T_SAFE + 1.15
PROBLEMS = ["Avoiding negative side effects", "Avoiding reward hacking", "Scalable oversight", "Safe exploration",
            "Robustness to distributional shift"]
PROBLEMS_T = [T_SAFE + 1.35 + k * 0.25 for k in range(5)]
SAFE_CARD2 = GR.at(6, 2)
AUTH1 = ["DARIO AMODEI", "CHRIS OLAH", "JACOB STEINHARDT", "PAUL CHRISTIANO", "JOHN SCHULMAN", "DAN MANÉ"]
AUTH2 = "P. CHRISTIANO  ·  J. LEIKE  ·  T. BROWN  ·  M. MARTIC  ·  S. LEGG  ·  D. AMODEI"


def page(c, x, y, w, h, rot=0.0):
    with G.xf(c, x + w / 2, y + h / 2, rot=rot):
        c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 10, -h / 2 + 18, w, h), G.P(INK, 0.16, blur=18))
        c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), G.P(PAGE))


def s_safety(c, t):
    fill(c, PAPER)
    chapter(c, t, T_SAFE, "02", "SAFETY", INK, CLAY)
    x, y, w, h = 150, 270, 860, 560
    u = snap(clamp((t - T_SAFE) / 0.4))
    c.save()
    c.translate(0, 120 * (1 - u))
    page(c, x, y, w, h)
    fm = G.Font("mono", 15, wght=650)
    G.text(c, "2016  ·  PAPER", x + 56, y + 70, fm, G.P(CLAY), tracking=0.24)
    G.text(c, "01 / 02", x + w - 56, y + 70, fm, G.P(INK, 0.5), align=1.0, tracking=0.24)
    ft = G.Font("fraunces", 66, wght=520, opsz=72)
    nch = int(len(PAPER_TITLE) * clamp((t - SAFE_TYPE0) / SAFE_TYPE_DUR))
    typed = PAPER_TITLE[:nch]
    l1, l2 = "Concrete Problems", " in AI Safety"
    G.text(c, typed[:len(l1)], x + 56, y + 170, ft, G.P(INK))
    if nch > len(l1):
        G.text(c, typed[len(l1):].lstrip(), x + 56, y + 250, ft, G.P(INK))
    fa = G.Font("mono", 17, wght=560)
    au = clamp((t - SAFE_TYPE0 - SAFE_TYPE_DUR) / 0.3)
    lines = ["  ·  ".join(AUTH1[:3]), "  ·  ".join(AUTH1[3:])]
    hl = snap(clamp((t - SAFE_HILITE) / 0.28))
    if hl > 0:
        wn = fa.width(AUTH1[0], 0.12)
        c.drawRect(skia.Rect.MakeXYWH(x + 50, y + 318, (wn + 14) * hl, 34), G.P(CLAY, 0.9))
    for k, ln in enumerate(lines):
        G.text(c, G.scramble(ln, au, k, t), x + 56, y + 342 + k * 38, fa, G.P(INK, 0.85), tracking=0.12)
    for k in range(5):
        wl = (0.55 + 0.4 * hash01(k, 5)) * (w - 112) * snap(clamp((t - SAFE_TYPE0 - 0.4 - k * 0.05) / 0.4))
        c.drawRoundRect(skia.Rect.MakeXYWH(x + 56, y + 440 + k * 22, wl, 8), 4, 4, G.P(INK, 0.1))
    c.restore()
    # the five problems
    fh = G.Font("mono", 15, wght=700)
    lx, ly = 1110, 330
    ha = clamp((t - PROBLEMS_T[0] + 0.3) / 0.3)
    G.text(c, G.scramble("FIVE CONCRETE PROBLEMS", ha, 7, t), lx, ly, fh, G.P(CLAY, ha), tracking=0.26)
    fl = G.Font("fraunces", 38, wght=450, opsz=48)
    for k, (item, tk) in enumerate(zip(PROBLEMS, PROBLEMS_T)):
        a = clamp((t - tk) / 0.25)
        if a <= 0:
            continue
        yy = ly + 70 + k * 84
        box = skia.Rect.MakeXYWH(lx, yy - 30, 34, 34)
        c.drawRect(box, G.P(INK, a, stroke=2.0))
        tick = G.poly([(lx + 7, yy - 13), (lx + 15, yy - 5), (lx + 29, yy - 24)], closed=False)
        c.drawPath(tick, G.P(CLAY, 1, stroke=4.5, cap="round", join="round", effect=G.trim(0, snap(clamp((t - tk - 0.08) / 0.2)))))
        G.text(c, item, lx + 58 + 20 * (1 - snap(a)), yy, fl, G.P(INK, a))
    # the second paper lands on the stack
    u2 = clamp((t - SAFE_CARD2) / 0.45)
    if u2 > 0:
        e = snap(u2)
        cx2, cy2 = lerp(2300, 190 + w / 2 - 20, e), 330 + h / 2 + 30
        with G.xf(c, cx2, cy2, rot=lerp(8, -2.2, e)):
            c.translate(-w / 2, -h / 2)
            page(c, 0, 0, w, h)
            G.text(c, "2017  ·  PAPER", 56, 70, fm, G.P(CLAY), tracking=0.24)
            G.text(c, "02 / 02", w - 56, 70, fm, G.P(INK, 0.5), align=1.0, tracking=0.24)
            ft2 = G.Font("fraunces", 58, wght=520, opsz=72)
            G.text(c, "Deep Reinforcement Learning", 56, 170, ft2, G.P(INK))
            G.text(c, "from Human Preferences", 56, 240, ft2, G.P(INK))
            G.text(c, AUTH2, 56, 320, G.Font("mono", 15, wght=560), G.P(INK, 0.8), tracking=0.08)
            fi = G.Font("serif-italic", 44)
            ga = clamp((t - SAFE_CARD2 - 0.5) / 0.35)
            G.text(c, "early groundwork for RLHF", 56, 420, fi, G.P(CLAY, ga))


# ---------------------------------------------------------------- 03 SCALE

NET_STEPS = [T_SCALE + k * GR.spb for k in range(4)]
PLOT_T0 = GR.at(8)
N_POINTS = 20
POINT_T = [PLOT_T0 + 0.15 + k * GR.spb / 8 for k in range(N_POINTS)]
FIT_T = PLOT_T0 + 1.05
_r3 = np.random.default_rng(23)
LAYER_X = np.linspace(-2.4, 2.4, 5)
_PTS = {}


def layer_nodes(width):
    if width not in _PTS:
        side = int(math.ceil(math.sqrt(width)))
        pts = []
        for i in range(width):
            a, b = divmod(i, side)
            pts.append(((a - (width - 1) // side / 2) * 0.42, (b - (side - 1) / 2) * 0.42))
        _PTS[width] = np.array(pts)
    return _PTS[width]


def network(c, t, cx):
    steps = sum(1 for s in NET_STEPS if s <= t)
    width = 3 * 2 ** max(0, steps - 1)
    prev = max(3, width // 2)
    since = t - (NET_STEPS[steps - 1] if steps else T_SCALE)
    grow = snap(clamp(since / 0.3))
    ang = 0.5 * (t - T_SCALE) - 0.6
    cam = Cam((7.0 * math.sin(ang), 1.6, -7.0 * math.cos(ang)), (0, 0, 0), fov=40, cx=cx, cy=CY + 40)
    layers = []
    for li, lx in enumerate(LAYER_X):
        cur = layer_nodes(width)
        if steps > 1 and grow < 1:
            par = layer_nodes(prev)
            src = par[np.arange(width) // 2 % len(par)]
            yz = src + (cur - src) * grow
        else:
            yz = cur
        P = np.stack([np.full(len(yz), lx), yz[:, 0], yz[:, 1]], 1)
        layers.append(cam.project(P))
    zs = np.concatenate([L[2] for L in layers])
    zmin, zmax = zs.min(), zs.max()
    edge = G.P(PAPER, 0.1, stroke=1.0)
    ea = 0.22 / math.sqrt(width / 3)
    for a, b in zip(layers, layers[1:]):
        ax, ay, az, _ = a
        bx, by, bz, _ = b
        for i in range(len(ax)):
            for j in range(len(bx)):
                d = 1 - ((az[i] + bz[j]) / 2 - zmin) / (zmax - zmin + 1e-6)
                edge.setAlphaf(ea * (0.3 + 0.7 * d))
                c.drawLine(ax[i], ay[i], bx[j], by[j], edge)
    node = G.P(PAPER)
    for x, y, z, _ in layers:
        for i in range(len(x)):
            d = 1 - (z[i] - zmin) / (zmax - zmin + 1e-6)
            new = steps > 1 and i >= prev
            node.setColor4f(G.c4(KRAFT if new and grow < 1 else PAPER, 0.45 + 0.55 * d))
            c.drawCircle(x[i], y[i], (3.5 + 5 * d) * (0.6 + 0.4 * (grow if new else 1)), node)
    return width


def plot(c, t, x0, y0, w, h):
    ax = snap(clamp((t - PLOT_T0) / 0.4))
    axis = G.poly([(x0, y0), (x0, y0 + h), (x0 + w, y0 + h)], closed=False)
    c.drawPath(axis, G.P(PAPER, 0.8, stroke=2.0, effect=G.trim(0, ax)))
    fm = G.Font("mono", 14, wght=600)
    for k in range(9):
        xx = x0 + w * k / 8
        c.drawLine(xx, y0 + h, xx, y0 + h + 10 * ax, G.P(PAPER, 0.5 * ax, stroke=1.2))
        yy = y0 + h * k / 8
        c.drawLine(x0 - 10 * ax, yy, x0, yy, G.P(PAPER, 0.5 * ax, stroke=1.2))
        c.drawLine(x0, yy, x0 + w, yy, G.P(PAPER, 0.05 * ax, stroke=1.0))
    G.text(c, "COMPUTE  (LOG)  →", x0 + w, y0 + h + 44, fm, G.P(PAPER, 0.6 * ax), align=1.0, tracking=0.22)
    with G.xf(c, x0 - 40, y0, rot=-90):
        G.text(c, "LOSS  (LOG)  →", -h, 0, fm, G.P(PAPER, 0.6 * ax), tracking=0.22)

    # loss falls as compute grows: a straight line, downhill, on log-log axes
    def lx(u):
        return x0 + w * (0.06 + 0.8 * u)

    def line_y(u):
        return y0 + h * (0.1 + 0.72 * u)
    for k, tk in enumerate(POINT_T):
        a = clamp((t - tk) / 0.12)
        if a <= 0:
            continue
        u = (k + 0.5) / N_POINTS
        px = lx(u)
        py = line_y(u) + (hash01(k, 3) - 0.5) * 34
        pop = 1 + 0.8 * math.exp(-(t - tk) / 0.08)
        G.circle(c, px, py, 7 * pop * a, G.P(KRAFT, a))
        G.circle(c, px, py, 16 * pop * a, G.P(KRAFT, 0.25 * a, stroke=1.2))
    fu = snap(clamp((t - FIT_T) / 0.5))
    if fu > 0:
        p0 = (lx(-0.05), line_y(-0.05))
        p1 = (lx(1.05), line_y(1.05))
        c.drawPath(G.poly([p0, p1], closed=False), G.P(CLAY, 1, stroke=4, cap="round", effect=G.trim(0, fu)))
        ex = snap(clamp((t - FIT_T - 0.45) / 0.5))
        if ex > 0:
            q1 = (lx(1.2), line_y(1.2))
            c.drawPath(G.poly([p1, q1], closed=False), G.P(CLAY, 0.8 * ex, stroke=3, effect=skia.PathEffect.MakeCompose(G.dash(14, 10), G.trim(0, ex))))
        fa = clamp((t - FIT_T - 0.3) / 0.4)
        f1 = G.Font("fraunces-italic", 76, wght=420, opsz=144)
        fs = G.Font("dejavu-serif-italic", 62)
        f2 = G.Font("fraunces-italic", 40, wght=420, opsz=48)
        tx, ty = x0 + w * 0.6, y0 + h * 0.2
        r1 = G.text(c, "L", tx, ty, f1, G.P(PAPER, fa))
        r2 = G.text(c, "∝", tx + r1.width + 18, ty - 2, fs, G.P(PAPER, fa))
        r3 = G.text(c, "C", tx + r1.width + r2.width + 36, ty, f1, G.P(PAPER, fa))
        G.text(c, "−0.050", tx + r1.width + r2.width + r3.width + 44, ty - 38, f2, G.P(CLAY, fa))


def s_scale(c, t):
    fill(c, INK)
    chapter(c, t, T_SCALE, "03", "SCALE", PAPER, KRAFT)
    if t < PLOT_T0:
        width = network(c, t, CX + 300)
        f = G.Font("fraunces-italic", 230, wght=360, opsz=144, SOFT=100)
        blur_in(c, f.shape("Scale."), 140, 610, PAPER, t, T_SCALE + 0.1, stagger=0.05)
        fm = G.Font("mono", 20, wght=650)
        G.text(c, G.scramble("OPENAI  ·  VP OF RESEARCH", clamp((t - T_SCALE - 0.5) / 0.4), 3, t), 150, 700, fm,
               G.P(KRAFT), tracking=0.24)
        fw = G.Font("mono", 64, wght=300)
        G.text(c, f"×{width:02d}", 150, 840, fw, G.P(PAPER, 0.8), tracking=0.05)
        return
    plot(c, t, 330, 270, 1260, 560)
    ca = clamp((t - FIT_T - 0.2) / 0.4)
    if ca > 0:
        fm = G.Font("mono", 17, wght=650)
        G.text(c, G.scramble("CO-AUTHOR  ·  GPT-2 (2019)  ·  GPT-3 (2020)  ·  SCALING LAWS (2020)", ca, 4, t), CX, 930,
               fm, G.P(PAPER, 0.85), align=0.5, tracking=0.2)
