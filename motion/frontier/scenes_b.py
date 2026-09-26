"""GEMINI 3.8 and FABLE 5.1."""
import math

import numpy as np
import skia

from engine import gfx as G
from engine.core import (clamp, lerp, anim, snap, whip, out_expo, in_expo, in_cubic, in_quad, out_cubic,
                         in_out_cubic, out_back, W, H, CX, CY, hash01)
from engine.three import Cam
from .common import (INK, PAPER, WHITE, GREEN, BLUE, VIOLET, CLAY, BOOK, fill, fit, draw_glyphs, card,
                     kick_env, with_alpha, lab_logo, model_logo)
from engine import logos as LG
from .score import G as GR, T_DROP_B, T_DROP_C, T_CLASH

# ---------------------------------------------------------------- GEMINI 3.8

T_HELIX = GR.at(7)
T_SPLIT = GR.at(8)
T_WIPE = GR.at(8, 4)


def orbit(t, which):
    th = (t - T_DROP_B) * 2 * math.pi / (2 * GR.spb) + (math.pi if which == 0 else 0.0)
    R = 380
    z = math.sin(th)
    return CX + R * math.cos(th), CY + 0.28 * R * math.sin(th), z


def twins(c, t, front):
    for which, col in ((0, WHITE), (1, VIOLET)):
        x, y, z = orbit(t, which)
        if (z >= 0) != front:
            continue
        for k in range(14, 0, -1):
            tt = t - k * 0.022
            if tt < T_DROP_B - 0.3:
                continue
            x0, y0, _ = orbit(tt, which)
            x1, y1, _ = orbit(tt + 0.022, which)
            c.drawLine(x0, y0, x1, y1, G.P(col, 0.5 * (1 - k / 14), stroke=26 * (1 - k / 14) * (1 + 0.3 * z), cap="round"))
        r = 34 * (1 + 0.35 * z)
        G.circle(c, x, y, r, G.P(col))


def text_on_circle(c, s, cx, cy, r, a0, font, paint, spacing=1.0):
    run = font.shape(s)
    for i, gid, gx, adv in run.glyphs():
        a = a0 + (gx + adv / 2) / r * spacing
        c.save()
        c.translate(cx + r * math.cos(a), cy + r * math.sin(a))
        c.rotate(math.degrees(a) + 90)
        G.glyph(c, font, gid, -adv / 2, font.cap / 2, paint)
        c.restore()


_hx = np.linspace(-6.2, 6.2, 124)


def helix(c, t):
    ph = (t - T_HELIX) * 2.8
    grow = snap(clamp((t - T_HELIX + 0.05) / 0.55))
    x = _hx * grow
    k = 1.2
    A = np.stack([x, 0.95 * np.cos(k * x + ph), 0.95 * np.sin(k * x + ph)], 1)
    Bp = np.stack([x, 0.95 * np.cos(k * x + ph + math.pi), 0.95 * np.sin(k * x + ph + math.pi)], 1)
    cam = Cam((-3.6 + 0.8 * (t - T_HELIX), 1.3, -4.6), (0.9, 0, 0), fov=50, cy=CY - 90)
    ax, ay, az, _ = cam.project(A)
    bx, by, bz, _ = cam.project(Bp)
    zmin, zmax = min(az.min(), bz.min()), max(az.max(), bz.max())
    rung = G.P(WHITE, 0.3, stroke=1.4)
    for i in range(0, len(x), 3):
        d = 1 - ((az[i] + bz[i]) / 2 - zmin) / (zmax - zmin + 1e-6)
        rung.setAlphaf(0.12 + 0.4 * d)
        c.drawLine(ax[i], ay[i], bx[i], by[i], rung)
        G.circle(c, (ax[i] + bx[i]) / 2, (ay[i] + by[i]) / 2, 2.5, G.P(WHITE, 0.3 + 0.5 * d))
    pts = [(az[i], ax[i], ay[i], WHITE) for i in range(len(x))] + [(bz[i], bx[i], by[i], VIOLET) for i in range(len(x))]
    pts.sort(key=lambda p: -p[0])
    p = G.P(WHITE)
    beat = (t - T_DROP_B) / GR.spb
    for z, px, py, col in pts:
        d = 1 - (z - zmin) / (zmax - zmin + 1e-6)
        p.setColor4f(G.c4(col, 0.35 + 0.65 * d))
        c.drawCircle(px, py, 2.5 + 7.5 * d * d, p)


def s_gemini(c, t):
    fill(c, BLUE)
    c.drawCircle(CX, CY, 1100, G.P(INK, 1, shader=G.radial_grad(CX, CY, 1100, [BLUE, "#1a2699"], alphas=[0.0, 0.55])))
    ke = kick_env(t)
    if t < T_HELIX:
        twins(c, t, front=False)
        u = clamp((t - T_DROP_B) / (2 * GR.spb))
        e = whip(u)
        f = fit("GEMINI", "archivo", 1250, wght=900, wdth=112)
        run = f.shape("GEMINI")
        x0, base = CX - run.width / 2 - 90, CY + f.cap / 2
        off = 14 * snap(clamp((t - T_DROP_B - 2 * GR.spb) / 0.3)) * (1 + 0.6 * ke)
        run.draw(c, x0 + 1500 * (1 - e) + off, base + off, G.P(VIOLET, 0.9, stroke=2.5))
        run.draw(c, x0 - 1500 * (1 - e), base, G.P(WHITE))
        a3 = clamp((t - GR.at(6, 3, 2)) / 0.25)
        if a3 > 0:
            f3 = G.Font("fraunces-italic", 300, wght=450, opsz=144, SOFT=60)
            G.text(c, "3.8", x0 + run.width + 30, base + 50 * (1 - snap(a3)) + 8, f3, G.P(WHITE, a3))
        la = clamp((t - GR.at(6, 3)) / 0.3)
        if la > 0:
            fm = G.Font("mono", 20, wght=720)
            G.text(c, G.scramble("CONTENDER 02 / 03", la, 3, t), x0 + 6, base - f.cap - 44, fm, G.P(WHITE, la), tracking=0.2)
            G.text(c, G.scramble("GOOGLE DEEPMIND", la, 4, t), x0 + run.width, base + 62, fm, G.P(VIOLET, la), align=1.0, tracking=0.2)
        twins(c, t, front=True)
        return
    if t < T_SPLIT:
        sp = snap(clamp((t - T_HELIX) / 0.5))
        LG.gemini(c, 1500, 330, 330 * sp, 0.95 * sp, rot=30 * (t - T_HELIX))
        helix(c, t)
        with G.layer(c):
            card(c, 150, 660, t, T_HELIX + 0.05, 1, VIOLET, ink=WHITE)
        return
    if t < T_WIPE + 0.4:
        u = t - T_SPLIT
        beat = int(u / GR.spb)
        sw = beat % 2 == 1
        top_bg, bot_bg = (WHITE, BLUE) if sw else (BLUE, WHITE)
        c.drawRect(skia.Rect.MakeXYWH(0, 0, W, CY), G.P(top_bg))
        c.drawRect(skia.Rect.MakeXYWH(0, CY, W, CY), G.P(bot_bg))
        f = G.Font("archivo", 250, wght=900, wdth=125 - 10 * ke)
        word = f.shape("GEMINI")
        step = word.width + 90
        for row, (y, speed, col) in enumerate(((CY / 2, -1100, bot_bg), (CY * 1.5, 1100, top_bg))):
            ofs = (u * speed) % step - step
            k = 0
            x = ofs - step
            while x < W + step:
                outline = (k + row + (1 if sw else 0)) % 2 == 0
                word.draw(c, x, y + f.cap / 2, G.P(col, 1, stroke=3.0) if outline else G.P(col))
                x += step
                k += 1
        rr = 150 + 8 * ke
        G.circle(c, CX, CY, rr, G.P(WHITE))
        G.circle(c, CX, CY, rr + 16, G.P(INK, 0.9, stroke=2.0))
        spin = 90 * snap(clamp((u % GR.spb) / 0.25)) + 90 * beat
        LG.gemini(c, CX, CY, 190 * (1 + 0.1 * ke), 1.0, rot=spin)
        fr = G.Font("mono", 17, wght=700)
        text_on_circle(c, "GEMINI 3.8 · GOOGLE DEEPMIND · LONDON · EST. 2010 · ", CX, CY, rr + 44,
                       u * 1.4, fr, G.P(top_bg if False else INK))
        # ruled lines wipe to paper on the last beat
        if t >= T_WIPE:
            for k in range(10):
                bu = whip(clamp((t - T_WIPE - k * 0.018) / 0.24))
                if bu <= 0:
                    continue
                y = k * H / 10
                x = W * (1 - bu)
                c.drawRect(skia.Rect.MakeXYWH(x, y, W - x, H / 10 + 1), G.P(PAPER))
                c.drawLine(x, y + H / 10, W, y + H / 10, G.P(BOOK, 0.25, stroke=1.5))


# ---------------------------------------------------------------- FABLE 5.1

T_TYPE = GR.at(9, 3)
T_BOOK = GR.at(10)
T_RIBBON = GR.at(11)
FLAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
STORY = "Once, three minds set out to find the edge of the map."
TW, TH, GAP = 236, 320, 22


def flap_tiles(c, t, y0, x0=None):
    total = 5 * TW + 4 * GAP
    x0 = CX - total / 2 if x0 is None else x0
    f = G.Font("archivo", 272, wght=900, wdth=100)
    per = 0.05
    for i, final in enumerate("FABLE"):
        lock = T_DROP_C + GR.spb / 4 * (i + 1)
        x = x0 + i * (TW + GAP)
        settle = 0.0
        if t >= lock:
            cur = nxt = final
            fl = 1.0
            settle = math.exp(-(t - lock) / 0.06) * math.cos((t - lock) * 40)
        else:
            k = (t - T_DROP_C) / per + i * 3
            ki = int(k)
            fl = k - ki
            cur = FLAP[(ki * 7 + i * 11) % 26]
            nxt = FLAP[((ki + 1) * 7 + i * 11) % 26]
        with G.xf(c, x + TW / 2, y0 + TH / 2, sy=1 + 0.04 * settle):
            c.translate(-TW / 2, -TH / 2)
            G.rrect(c, 0, 0, TW, TH, 16, G.P(BOOK))

            def half(ch, top, sy=1.0, shade=0.0):
                with G.clip_rect(c, 0, 0 if top else TH / 2, TW, TH / 2):
                    c.save()
                    c.translate(0, TH / 2)
                    c.scale(1, sy)
                    c.translate(0, -TH / 2)
                    if shade:
                        G.rrect(c, 0, 0, TW, TH, 16, G.P(BOOK))
                    G.text(c, ch, TW / 2, TH / 2, f, G.P(PAPER, 1 - shade), align=0.5, anchor="cap")
                    c.restore()
            if t >= lock:
                half(cur, True)
                half(cur, False)
            else:
                half(nxt, True)
                half(cur, False)
                if fl < 0.5:
                    half(cur, True, sy=math.cos(math.pi * fl), shade=0.5 * fl)
                else:
                    half(nxt, False, sy=-math.cos(math.pi * fl), shade=0.5 * (1 - fl))
            c.drawLine(0, TH / 2, TW, TH / 2, G.P(PAPER, 1, stroke=4))
            G.circle(c, 0, TH / 2, 7, G.P(PAPER))
            G.circle(c, TW, TH / 2, 7, G.P(PAPER))
    return x0, total


# book geometry, in page widths
PW, PH, STK = 1.0, 1.36, 0.05
_lr = np.random.default_rng(51)
LINES = [(z, 0.35 + 0.6 * _lr.random()) for z in np.linspace(-PH / 2 + 0.16, PH / 2 - 0.2, 14)]
FLIPS = [T_BOOK + k * GR.spb for k in range(4)]


def page_curve(th, n=12):
    kap = -1.3 * math.sin(th)
    s = np.linspace(0, PW, n)
    if abs(kap) < 1e-4:
        return s * math.cos(th), s * math.sin(th) + STK, th + 0 * s
    x = (np.sin(th + kap * s) - math.sin(th)) / kap
    y = (math.cos(th) - np.cos(th + kap * s)) / kap + STK
    return x, y, th + kap * s


def book(c, t):
    ang = 0.35 * math.sin(0.5 * (t - T_BOOK)) - 0.15
    cam = Cam((1.7 * math.sin(ang), 1.85, -1.7 * math.cos(ang) - 0.2), (0, 0, 0.06), fov=42, cx=CX - 230, cy=CY + 40)
    rise = snap(clamp((t - T_BOOK) / 0.4))
    c.save()
    c.translate(0, 160 * (1 - rise))

    def proj(P):
        x, y, _, _ = cam.project(np.asarray(P, float))
        return list(zip(x, y))
    m = 0.05
    cover = proj([(-PW - m, 0, -PH / 2 - m), (PW + m, 0, -PH / 2 - m), (PW + m, 0, PH / 2 + m), (-PW - m, 0, PH / 2 + m)])
    c.drawPath(G.poly(cover), G.P(CLAY))
    for sgn in (-1, 1):
        for k in range(6, -1, -1):
            yy = STK * k / 6
            pg = proj([(0, yy, -PH / 2), (sgn * PW, yy, -PH / 2), (sgn * PW, yy, PH / 2), (0, yy, PH / 2)])
            c.drawPath(G.poly(pg), G.P(PAPER if k == 6 else "#e2ddd2"))
            c.drawPath(G.poly(pg), G.P(BOOK, 0.35 if k == 6 else 0.12, stroke=1.0))
        for z, ln in LINES:
            a = proj([(sgn * 0.12, STK, z), (sgn * (0.12 + ln * (PW - 0.24)), STK, z)])
            c.drawLine(a[0][0], a[0][1], a[1][0], a[1][1], G.P(BOOK, 0.4, stroke=2.0, cap="round"))
    flips = []
    for tf in FLIPS:
        u = clamp((t - tf) / 0.8)
        if u > 0:
            flips.append(math.pi * in_out_cubic(u))
    L = np.array([-0.4, 1.0, -0.5]) / np.linalg.norm([-0.4, 1.0, -0.5])
    for th in sorted(flips, reverse=True):
        x, y, phi = page_curve(th)
        bot = proj(np.stack([x, y, np.full_like(x, -PH / 2)], 1))
        top = proj(np.stack([x, y, np.full_like(x, PH / 2)], 1))
        pm = phi[len(phi) // 2]
        nrm = np.array([-math.sin(pm), math.cos(pm), 0.0])
        shade = 0.74 + 0.26 * abs(float(nrm @ L))
        col = tuple(v * shade for v in G.rgb(PAPER))
        path = G.poly(bot + top[::-1])
        c.drawPath(path, G.P(col))
        c.drawPath(path, G.P(BOOK, 0.45, stroke=1.2))
        if th < math.pi / 2:
            for z, ln in LINES:
                ss = np.linspace(0.12, 0.12 + ln * (PW - 0.24), 6)
                xs = np.interp(ss, np.linspace(0, PW, len(x)), x)
                ys = np.interp(ss, np.linspace(0, PW, len(y)), y)
                pts = proj(np.stack([xs, ys, np.full_like(xs, z)], 1))
                c.drawPath(G.poly(pts, closed=False), G.P(BOOK, 0.35, stroke=2.0, cap="round"))
    c.restore()


RIB_TEXT = (STORY + "  ") * 2
_rib = np.arange(len(RIB_TEXT))


def ribbon(c, t, front):
    u = t - T_RIBBON
    implode = in_expo(clamp((t - (T_CLASH - 0.4)) / 0.4))
    rot = u * 0.9 + 3.0 * implode ** 2
    R = 2.05 * (1 - implode)
    a = -_rib * (2 * math.pi / len(_rib)) + rot
    y = 0.5 * np.sin(a) * (1 - implode)
    P = np.stack([R * np.cos(a), y, R * np.sin(a)], 1)
    cam = Cam((0, 0.55, -5.4), (0, 0.05, 0), fov=40)
    px, py, pz, _ = cam.project(P)
    f = G.Font("serif-italic", 60)
    for i in np.argsort(-pz):
        z = P[i, 2]
        if (z < 0) != front:
            continue
        ch = RIB_TEXT[i % len(RIB_TEXT)]
        if ch == " ":
            continue
        s = 5.2 / pz[i]
        sx = math.sin(a[i])
        alpha = (0.95 if z < 0 else 0.3) * clamp((t - T_RIBBON - i * 0.004) / 0.2)
        with G.xf(c, px[i], py[i], sx=s * max(0.12, abs(sx)) * (1 if sx >= 0 else -1), sy=s):
            G.text(c, ch, 0, 0, f, G.P(BOOK, alpha), align=0.5, anchor="x")


def s_fable(c, t):
    fill(c, PAPER)
    ke = kick_env(t)
    if t < T_BOOK:
        y0 = CY - TH / 2 - 70
        f5 = G.Font("fraunces-italic", 330, wght=520, opsz=144, SOFT=40)
        run5 = f5.shape("5.1")
        group = 5 * TW + 4 * GAP + 26 + run5.width
        x0, total = flap_tiles(c, t, y0, CX - group / 2)
        wr = clamp((t - (T_DROP_C + 0.45)) / 0.4)
        if wr > 0:
            path = run5.path(0, 0)
            with G.xf(c, x0 + total + 26, y0 + TH - 6):
                c.drawPath(path, G.P(CLAY, 1, stroke=3.5, effect=G.trim(0, snap(wr))))
                fa = clamp((wr - 0.8) / 0.2)
                if fa > 0:
                    c.drawPath(path, G.P(CLAY, fa))
        la = clamp((t - (T_DROP_C + 0.35)) / 0.3)
        if la > 0:
            fm = G.Font("mono", 20, wght=720)
            G.text(c, G.scramble("CONTENDER 03 / 03", la, 5, t), x0 + 4, y0 - 38, fm, G.P(CLAY, la), tracking=0.2)
            G.text(c, G.scramble("ANTHROPIC", la, 6, t), x0 + group, y0 - 38, fm, G.P(BOOK, la), align=1.0, tracking=0.2)
        c.drawLine(x0, y0 + TH + 34, x0 + total * snap(clamp((t - T_DROP_C - 0.2) / 0.5)), y0 + TH + 34, G.P(CLAY, 1, stroke=5))
        if t >= T_TYPE:
            ft = G.Font("serif-italic", 58)
            full = ft.shape(STORY)
            n = int(len(STORY) * clamp((t - T_TYPE - 0.02) / 0.62))
            xs = CX - full.width / 2
            yb = y0 + TH + 128
            G.text(c, STORY[:n], xs, yb, ft, G.P(BOOK))
            cx_ = xs + (ft.shape(STORY[:n]).width if n else 0) + 30
            LG.claude(c, cx_, yb - 18, 44, CLAY, 1.0, 1.0, rot=(t - T_TYPE) * 220)
        return
    if t < T_RIBBON:
        book(c, t)
        card(c, 1190, 300, t, T_BOOK + 0.05, 2, CLAY, ink=BOOK)
        return
    ribbon(c, t, front=False)
    implode = in_expo(clamp((t - (T_CLASH - 0.4)) / 0.4))
    f = fit("FABLE", "archivo", 1120, wght=900, wdth=125)
    f = G.Font("archivo", f.size, wght=900, wdth=125 - 8 * ke)
    run = f.shape("FABLE")
    s = lerp(0.9, 1.0, out_cubic(clamp((t - T_RIBBON) / 1.2))) * (1 - 0.8 * implode)
    with G.xf(c, CX, CY, s=s):
        run.draw(c, -run.width / 2 + 110, f.cap / 2, G.P(CLAY))
        sp = snap(clamp((t - T_RIBBON) / 0.45))
        LG.claude(c, -run.width / 2 - 70, 0, f.cap * 1.25, CLAY, 1.0, sp, rot=(t - T_RIBBON) * 40, t=t)
    ribbon(c, t, front=True)
