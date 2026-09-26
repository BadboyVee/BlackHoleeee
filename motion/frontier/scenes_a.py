"""Cold open and ASTRA 6."""
import math

import numpy as np
import skia

from engine import gfx as G
from engine.core import (clamp, lerp, anim, snap, whip, out_expo, in_expo, in_cubic, in_quad, out_cubic,
                         out_back, in_out_cubic, spring, W, H, CX, CY, hash01)
from engine.three import Cam, fib_sphere, rot_x, rot_y, rot_z, ring
from .common import (INK, PAPER, WHITE, GREEN, BLUE, CLAY, fill, fit, draw_glyphs, card, kick_env, with_alpha,
                     lab_logo, model_logo)
from .score import G as GR, WORDS, T_DROP_A, T_DROP_B, BREATH

# ---------------------------------------------------------------- cold open

WORD_COLORS = {"LABS.": GREEN, "MINDS.": BLUE, "FRONTIER.": CLAY}
ROLL = [GR.at(2, 3), GR.at(2, 3, 2), GR.at(2, 4), GR.at(2, 4, 1), GR.at(2, 4, 2), GR.at(2, 4, 3)]


def word_font(word, wdth):
    target = 1760 if word == "FRONTIER." else (1500 if len(word) > 4 else 1180)
    base = fit(word, "archivo", target, wght=900, wdth=125)
    return G.Font("archivo", base.size, wght=900, wdth=wdth)


def s_open(c, t):
    fill(c, INK)
    # crosshair and a compass ring that open on the first hit
    u = anim(t, 0.0, 0.55, ease=snap)
    hair = G.P(WHITE, 0.16, stroke=1.2)
    c.drawLine(CX - CX * u, CY, CX + CX * u, CY, hair)
    c.drawLine(CX, CY - CY * u, CX, CY + CY * u, hair)
    for k in range(-12, 13):
        x = CX + k * 80 * u
        c.drawLine(x, CY - 6, x, CY + 6, G.P(WHITE, 0.22 * u, stroke=1.2))

    if t < GR.at(2, 3):
        i = max([k for k, (tw, _) in enumerate(WORDS) if tw <= t] or [0])
        tw, word = WORDS[i]
        du = t - tw
        # the previous word leaves an outline echo that swells and fades
        if i > 0:
            pw = WORDS[i - 1][1]
            e = clamp(du / 0.32)
            f = word_font(pw, 125)
            run = f.shape(pw)
            s = 1 + 0.35 * out_cubic(e)
            with G.xf(c, CX, CY, s=s):
                run.draw(c, -run.width / 2, f.cap / 2, G.P(WHITE, 0.45 * (1 - e), stroke=2.0))
        wd = lerp(72, 125, snap(clamp(du / 0.3)))
        f = word_font(word, wd)
        run = f.shape(word)
        s = lerp(1.16, 1.0, out_expo(clamp(du / 0.22)))
        inv = (i in (0, 4, 5)) and du < 2 / 60
        if inv:
            fill(c, WHITE)
        acc = WORD_COLORS.get(word)
        paints = [G.P(INK if inv else (acc if (acc and gi == len(run.gids) - 1) else WHITE)) for gi in range(len(run.gids))]
        with G.xf(c, CX, CY, s=s):
            draw_glyphs(c, run, -run.width / 2, f.cap / 2, paints)
        return

    # bar 2, beats 3-4: FRONTIER. collapses into the three-lab constellation
    t0 = GR.at(2, 3)
    k = clamp((t - t0) / 0.3)
    if k < 1:
        f = word_font("FRONTIER.", lerp(125, 62, in_expo(k)))
        run = f.shape("FRONTIER.")
        s = lerp(1.0, 0.25, in_expo(k))
        paints = [G.P(CLAY if gi == len(run.gids) - 1 else WHITE, 1 - k * k) for gi in range(len(run.gids))]
        with G.xf(c, CX, CY, s=s):
            draw_glyphs(c, run, -run.width / 2, f.cap / 2, paints)
    t_end = GR.at(3) - BREATH
    if t >= t_end:
        return
    grow = snap(clamp((t - t0 - 0.05) / 0.4))
    implode = in_expo(clamp((t - (t_end - 0.12)) / 0.12))
    R = 300 * grow * (1 + 0.25 * clamp((t - t0) / 0.6)) * (1 - implode)
    rot = -90 + 40 * in_quad(clamp((t - t0) / 0.65))
    labs = [("OPENAI", GREEN), ("GOOGLE DEEPMIND", BLUE), ("ANTHROPIC", CLAY)]
    pts = []
    for n in range(3):
        a = math.radians(rot + n * 120)
        pts.append((CX + R * math.cos(a), CY + R * math.sin(a) * 0.92))
    tri = G.poly(pts, closed=True)
    c.drawPath(tri, G.P(WHITE, 0.55 * (1 - implode), stroke=1.6, effect=G.trim(0, snap(clamp((t - t0 - 0.1) / 0.35)))))
    flash = max([math.exp(-(t - r) / 0.05) for r in ROLL if t >= r] or [0.0])
    f_lab = G.Font("mono", 16, wght=700)
    for n, ((x, y), (name, col)) in enumerate(zip(pts, labs)):
        g = snap(clamp((t - t0 - 0.05 - n * 0.06) / 0.3)) * (1 - implode)
        G.circle(c, x, y, (44 + 18 * flash) * g, G.P(INK))
        G.circle(c, x, y, (44 + 18 * flash) * g, G.P(col, 0.9, stroke=2.0))
        if g > 0.01:
            lab_logo(c, n, x, y, 50 * g * (1 + 0.15 * flash), 1.0, rot=-120 * (1 - g))
        la = clamp((t - t0 - 0.15 - n * 0.06) / 0.2) * (1 - implode)
        if la > 0:
            dx = x - CX
            dy = y - CY
            d = math.hypot(dx, dy) + 1e-6
            lx, ly = x + dx / d * 46, y + dy / d * 46
            G.text(c, G.scramble(name, la, n, t), lx, ly, f_lab, G.P(WHITE, la), align=0.5 - 0.5 * dx / d,
                   tracking=0.16, anchor="cap")


# ---------------------------------------------------------------- ASTRA 6

_rng = np.random.default_rng(6)
STARS = fib_sphere(900) * (1 + 0.035 * _rng.standard_normal((900, 1)))
TW_PH = _rng.random(900) * 6.28
TW_FR = 1.5 + _rng.random(900) * 4
STAR_GREEN = _rng.random(900) < 0.13
_d = np.linalg.norm(STARS[:, None, :] - STARS[None, :, :], axis=2)
np.fill_diagonal(_d, 9)
_pick = _rng.choice(900, 300, replace=False)
LINKS = sorted({(min(a, b), max(a, b)) for a in _pick for b in np.argsort(_d[a])[:2]})
LINK_ORDER = _rng.permutation(len(LINKS))
del _d
RINGS = [(1.42, rot_x(1.2) @ rot_z(0.3)), (1.68, rot_x(0.35) @ rot_z(-0.5)), (1.95, rot_x(1.9) @ rot_y(0.8))]
TUN_N = 650
TUN_A = _rng.random(TUN_N) * 6.283
TUN_R = 0.35 + 2.4 * _rng.random(TUN_N) ** 0.7
TUN_Z = _rng.random(TUN_N) * 40
TUN_G = _rng.random(TUN_N) < 0.2

T_ZOOM = GR.at(4) - 0.36           # zoom through the A starts
T_SPHERE = GR.at(4)
T_WARP = GR.at(5)
T_COLLAPSE = GR.at(5, 4)


def astra_word(t, wdth):
    f = fit("ASTRA", "archivo", 1480, wght=900, wdth=125)
    return G.Font("archivo", f.size, wght=900, wdth=wdth)


def counter_center(font, gid):
    """Centre of the smallest contour of a glyph: the counter of the A."""
    path = font.glyph_path(gid)
    it = skia.Path.Iter(path, False)
    best, cur = None, []
    while True:
        verb, pts = it.next()
        if verb == skia.Path.kDone_Verb:
            break
        if verb == skia.Path.kMove_Verb:
            if cur:
                xs, ys = zip(*cur)
                box = (max(xs) - min(xs)) * (max(ys) - min(ys))
                if best is None or box < best[0]:
                    best = (box, (sum(xs) / len(xs), sum(ys) / len(ys)))
            cur = [(p.x(), p.y()) for p in pts[:1]]
        else:
            cur += [(p.x(), p.y()) for p in pts[1:]]
    if cur:
        xs, ys = zip(*cur)
        box = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if best is None or box < best[0]:
            best = (box, (sum(xs) / len(xs), sum(ys) / len(ys)))
    return best[1]


def star_sphere(c, t, alpha=1.0):
    ang = 0.42 * (t - T_ZOOM) + 0.4
    dist = lerp(4.6, 3.6, out_cubic(clamp((t - T_ZOOM) / 2.0)))
    cam = Cam((dist * math.sin(ang), 0.9, -dist * math.cos(ang)), (0, 0, 0), fov=40, cx=CX + 150)
    x, y, z, vis = cam.project(STARS)
    zn = (z - z.min()) / (z.max() - z.min() + 1e-6)
    tw = 0.62 + 0.38 * np.sin(t * TW_FR + TW_PH)
    s16 = int((t - T_DROP_A) / (GR.spb / 4))
    hot = hash01(np.arange(900), s16) < 0.07
    since = (t - T_DROP_A) % (GR.spb / 4)
    flash = math.exp(-since / 0.05)
    lp = clamp((t - T_SPHERE + 0.2) / 1.2)
    nl = int(len(LINKS) * lp)
    lk = G.P(WHITE, 0.2 * alpha, stroke=1.0)
    for li in LINK_ORDER[:nl]:
        a, b = LINKS[li]
        d = 1 - (zn[a] + zn[b]) / 2
        lk.setAlphaf(0.28 * alpha * d)
        c.drawLine(x[a], y[a], x[b], y[b], lk)
    for R, M in RINGS:
        pts = ring(180, R) @ M.T
        rx, ry, rz, _ = cam.project(pts)
        rzn = (rz - z.min()) / (z.max() - z.min() + 1e-6)
        seg = G.P(WHITE, 0.3, stroke=1.2)
        for i in range(180):
            j = (i + 1) % 180
            seg.setAlphaf(alpha * (0.08 + 0.32 * (1 - rzn[i])))
            c.drawLine(rx[i], ry[i], rx[j], ry[j], seg)
            if i % 10 == 0:
                c.drawLine(rx[i], ry[i], rx[i] + (rx[i] - cam.cx) * 0.03, ry[i] + (ry[i] - cam.cy) * 0.03, seg)
        sa = t * (1.1 / R) + R
        sp = np.array([[R * math.cos(sa), 0, R * math.sin(sa)]]) @ M.T
        sx, sy, sz, _ = cam.project(sp)
        G.circle(c, sx[0], sy[0], 5, G.P(GREEN, alpha))
    # the OpenAI blossom sits at the heart of the system, behind the near stars
    ctr_x, ctr_y, _, _ = cam.project(np.zeros((1, 3)))
    bl = alpha * clamp((t - T_SPHERE + 0.15) / 0.35)
    if bl > 0:
        c.drawCircle(ctr_x[0], ctr_y[0], 230, G.P(GREEN, 1, shader=G.radial_grad(ctr_x[0], ctr_y[0], 230, [GREEN, INK], alphas=[0.35 * bl, 0.0])))
        lab_logo(c, 0, ctr_x[0], ctr_y[0], 200 * (0.8 + 0.2 * snap(bl)), bl, rot=18 * (t - T_SPHERE))
    order = np.argsort(-z)
    p = G.P(WHITE)
    for i in order:
        if not vis[i]:
            continue
        d = 1 - zn[i]
        r = 1.0 + 3.0 * d * d
        a = alpha * (0.2 + 0.8 * d) * tw[i]
        col = GREEN if (STAR_GREEN[i] or hot[i]) else WHITE
        if hot[i]:
            r *= 1 + 1.5 * flash
            a = min(1.0, a + flash)
        p.setColor4f(G.c4(col, a))
        c.drawCircle(x[i], y[i], r, p)


def hyperspace(c, t):
    u = clamp((t - T_WARP) / (T_COLLAPSE - T_WARP))
    travelled = 6 * u + 40 * in_quad(u) ** 1.2
    speed = 6 + 70 * u
    col = clamp((t - T_COLLAPSE) / 0.2)
    focal = 900
    z = (TUN_Z - travelled) % 40 + 0.5
    r = TUN_R * (1 - in_expo(col))
    x = CX + r * np.cos(TUN_A) * focal / z
    y = CY + r * np.sin(TUN_A) * focal / z
    z2 = z + speed * 0.018
    x2 = CX + r * np.cos(TUN_A) * focal / z2
    y2 = CY + r * np.sin(TUN_A) * focal / z2
    p = G.P(WHITE, 1, stroke=1.6, cap="round")
    for i in range(TUN_N):
        a = clamp(1.4 - z[i] / 30)
        if a <= 0.01:
            continue
        p.setColor4f(G.c4(GREEN if TUN_G[i] else WHITE, a))
        p.setStrokeWidth(0.8 + 3.0 * (1 - z[i] / 40))
        c.drawLine(x[i], y[i], x2[i], y2[i], p)
    # a tunnel of words flying at the camera
    f = G.Font("archivo", 220, wght=900, wdth=125)
    run = f.shape("ASTRA")
    for k in range(5):
        zz = (k * 8 - travelled * 0.9) % 40 + 0.8
        s = 3.2 / zz
        a = clamp(1.6 - zz / 14) * clamp(zz / 1.6) * (1 - col)
        if a <= 0.01:
            continue
        with G.xf(c, CX, CY, s=s):
            run.draw(c, -run.width / 2, f.cap / 2, G.P(GREEN if k % 2 else WHITE, a, stroke=2.5 / s))


def s_astra(c, t):
    fill(c, INK)
    ke = kick_env(t)
    if t < T_ZOOM + 0.36:
        # the sphere waits behind the word: the A's counter is a window onto it
        if t > T_ZOOM:
            star_sphere(c, t, clamp((t - T_ZOOM) / 0.2))
        c.drawCircle(CX, CY, 900, G.P(GREEN, 0.10 + 0.06 * ke, shader=G.radial_grad(CX, CY, 900, [GREEN, INK], alphas=[0.5, 0.0])))
        wd = 125 - 7 * ke
        f = astra_word(t, wd)
        run = f.shape("ASTRA")
        x0, base = CX - run.width / 2, CY + f.cap / 2
        z = in_expo(clamp((t - T_ZOOM) / 0.36))
        # the big italic 6, written on, then filled
        f6 = G.Font("fraunces-italic", 1150, wght=600, opsz=144, SOFT=0)
        run6 = f6.shape("6")
        wr = clamp((t - GR.at(3, 3)) / 0.45)
        fl = clamp((t - GR.at(3, 3) - 0.4) / 0.25)
        six_a = 1 - clamp(z * 3)
        if wr > 0 and six_a > 0:
            path = run6.path(0, 0)
            with G.xf(c, 1320 + 30 * (1 - snap(wr)), 1060, rot=-4 * (1 - snap(wr)), s=1 + 0.02 * ke):
                c.drawPath(path, G.P(GREEN, six_a, stroke=4, effect=G.trim(0, snap(wr))))
                if fl > 0:
                    c.drawPath(path, G.P(GREEN, 0.92 * fl * six_a))
        # the zoom: scale about the counter of the first A
        gid0 = run.gids[0]
        cx0, cy0 = counter_center(f, gid0)
        px, py = x0 + run.xs[0] + cx0, base + cy0
        zs = lerp(1.0, 70.0, z)

        def drop(i):
            ti = T_DROP_A + i * GR.spb / 4
            if t < ti - 0.14:
                return (0, 0, 1, 1, 0, 0)
            if t < ti:
                uu = (t - (ti - 0.14)) / 0.14
                return (0, -760 * (1 - uu) ** 2, 0.9, 1.12, 0, 1)
            s = t - ti
            d = math.exp(-s / 0.07) * math.cos(2 * math.pi * s / 0.2)
            spread = 0 if i == 0 else (i - 0) * 260 * z
            return (spread, 0, 1 + 0.14 * d, 1 - 0.24 * d, 0, 1)
        # anchor the zoom on the counter while drifting it to the middle of the frame
        sx_, sy_ = lerp(px, CX, snap(z)), lerp(py, CY, snap(z))
        with G.xf(c, sx_, sy_, s=zs):
            c.translate(-px, -py)
            draw_glyphs(c, run, x0, base, G.P(WHITE), drop)
            la = clamp((t - GR.at(3, 3)) / 0.25) * (1 - clamp(z * 4))
            if la > 0:
                fm = G.Font("mono", 20, wght=720)
                G.text(c, G.scramble("CONTENDER 01 / 03", la, 1, t), x0 + 8, base - f.cap - 44, fm, G.P(GREEN, la), tracking=0.2)
                G.text(c, G.scramble("OPENAI", la, 2, t), x0 + run.width - 8, base + 66, fm, G.P(WHITE, la * 0.8), align=1.0, tracking=0.2)
        return
    if t < T_WARP:
        star_sphere(c, t)
        fm = G.Font("archivo", 64, wght=900, wdth=125)
        card(c, 150, 330, t, T_SPHERE + 0.05, 0, GREEN)
        return
    if t < T_COLLAPSE + 0.25:
        hyperspace(c, t)
        return
    # the last half-beat: one point that splits into two
    u = clamp((t - (T_COLLAPSE + 0.25)) / (T_DROP_B - T_COLLAPSE - 0.25))
    sep = 380 * snap(u)
    for sgn in (-1, 1):
        G.circle(c, CX + sgn * sep, CY, 10 + 26 * u, G.P(WHITE if sgn < 0 else "#c9b8ff"))
        G.circle(c, CX + sgn * sep, CY, 60 + 40 * u, G.P(WHITE, 0.25 * (1 - u), stroke=1.5))
