"""04 ANTHROPIC, 05 MACHINES OF LOVING GRACE, 06 DARIO AMODEI."""
import math
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from engine import logos as LG
from engine.core import (clamp, lerp, snap, whip, out_expo, in_expo, out_cubic, in_out_cubic, W, H, CX, CY, hash01)
from .common import INK, PAPER, PAGE, CLAY, KRAFT, DIM, fill, blur_in, chapter, kick_env
from . import photos as PH
from .score import G as GR, T_ANTH, T_GRACE, T_CENTURY, T_DOMAINS, T_FIN, T_LAST, DURATION

PLATE_DIR = None

# ---------------------------------------------------------------- 04 ANTHROPIC

ODO_T = [T_ANTH + k * GR.spb / 4 for k in range(6)]
LOGO_T = T_ANTH + 0.8
ANTH_TEXT_T = [T_ANTH + 1.0, T_ANTH + 1.35, T_ANTH + 1.65]
CLAUDE_T = GR.at(10)
HQ_T = T_ANTH + 1.3


def odometer(c, t, x, base, f, col):
    """'20' then two digit wheels rolling from 16 to 21, one step per sixteenth."""
    run20 = f.shape("20")
    run20.draw(c, x, base, G.P(col))
    steps = sum(1 for s in ODO_T[1:] if s <= t)
    v = 16 + steps
    since = t - (ODO_T[steps] if steps < len(ODO_T) else ODO_T[-1])
    roll = snap(clamp(since / 0.1)) if steps > 0 else 1.0
    prev = v - 1 if steps > 0 else v
    dx = x + run20.width
    digit_w = f.width("0")
    hgt = f.cap * 1.35
    for place, (a_digit, b_digit) in enumerate(((prev // 10, v // 10), (prev % 10, v % 10))):
        xx = dx + place * digit_w
        mid = xx + digit_w / 2     # digits are centred in fixed slots: Fraunces has no tabular figures
        with G.clip_rect(c, xx - 4, base - f.cap - 30, digit_w + 8, f.cap + 60):
            if a_digit == b_digit:
                G.text(c, str(b_digit), mid, base, f, G.P(col), align=0.5)
            else:
                G.text(c, str(a_digit), mid, base - hgt * roll, f, G.P(col), align=0.5)
                G.text(c, str(b_digit), mid, base + hgt * (1 - roll), f, G.P(col), align=0.5)
    return dx + 2 * digit_w


def s_anthropic(c, t):
    fill(c, CLAY)
    chapter(c, t, T_ANTH, "04", "ANTHROPIC", INK, PAGE)
    f = G.Font("fraunces", 330, wght=450, opsz=144, SOFT=0)
    odometer(c, t, 140, 560, f, INK)
    ff = G.Font("fraunces", 86, wght=420, opsz=96)
    blur_in(c, ff.shape("co-founds Anthropic"), 150, 700, INK, t, ANTH_TEXT_T[0], stagger=0.025)
    fi = G.Font("serif-italic", 52)
    blur_in(c, fi.shape("with Daniela Amodei and colleagues"), 152, 780, INK, t, ANTH_TEXT_T[1], stagger=0.012,
            blur=8)
    ca = snap(clamp((t - ANTH_TEXT_T[2]) / 0.3))
    if ca > 0:
        fm = G.Font("mono", 20, wght=750)
        label = "CO-FOUNDER  &  CEO"
        wl = fm.width(label, 0.26)
        G.rrect(c, 150, 830, (wl + 48) * ca, 52, 26, G.P(INK))
        with G.clip_rect(c, 150, 830, (wl + 48) * ca, 52):
            G.text(c, label, 174, 865, fm, G.P(PAGE), tracking=0.26)
    # the A\ mark draws itself, then fills; with an office photograph it tucks into the photo's corner
    # the card shows the office if there is a photograph of it, otherwise the portrait
    card = "anthropic-hq" if PH.available("anthropic-hq") else ("dario" if PH.available("dario") else None)
    caption = "ANTHROPIC  ·  SAN FRANCISCO" if card == "anthropic-hq" else "DARIO AMODEI  ·  CO-FOUNDER & CEO"
    hx, hy, hw, hh = 1040, 250, 720, 540
    he = snap(clamp((t - HQ_T) / 0.5)) if card else 0.0
    if he > 0:
        c.drawRect(skia.Rect.MakeXYWH(hx + 14, hy + 22, hw, hh), G.P(INK, 0.25, blur=22))
        img = PH.duotone(card, hw, hh, INK, PAGE, 0.3)
        with G.clip_rect(c, hx, hy + hh * (1 - he), hw, hh * he):
            with G.xf(c, hx + hw / 2, hy + hh / 2, s=1.06 - 0.06 * he):
                G.draw_image(c, img, -hw / 2, -hh / 2, hw, hh)
        fm = G.Font("mono", 17, wght=700)
        G.text(c, G.scramble(caption, clamp((t - HQ_T - 0.3) / 0.4), 9, t), hx, hy + hh + 42, fm,
               G.P(INK, he), tracking=0.26)
    lu = clamp((t - LOGO_T) / 0.55)
    if lu > 0:
        lx, ly, ls = lerp(1430, hx + 70, he), lerp(470, hy + 62, he), lerp(420, 64, he)
        p = LG.mark_path("anthropic", lx, ly, ls)
        c.drawPath(p, G.P(PAGE if he > 0.5 else INK, 1, stroke=4 * (1 - he) + 1, effect=G.trim(0, snap(lu))))
        fa = clamp((t - LOGO_T - 0.45) / 0.25)
        if fa > 0:
            c.drawPath(p, G.P(PAGE if he > 0.5 else INK, fa))
    # 2023: an ink panel sweeps in with the Claude spark
    pu = whip(clamp((t - CLAUDE_T + 0.1) / 0.38))
    if pu > 0:
        x = W - (W - 960) * pu
        c.drawRect(skia.Rect.MakeXYWH(x, 0, W - x, H), G.P(INK))
        with G.clip_rect(c, x, 0, W - x, H):
            sp = snap(clamp((t - CLAUDE_T) / 0.6))
            LG.claude(c, 1440, 440, 380 * (0.6 + 0.4 * sp), CLAY, 1.0, sp, rot=25 * (t - CLAUDE_T), t=t)
            fm = G.Font("mono", 20, wght=700)
            G.text(c, G.scramble("2023", clamp((t - CLAUDE_T) / 0.3), 2, t), 1080, 230, fm, G.P(CLAY), tracking=0.3)
            fc = G.Font("fraunces-italic", 150, wght=380, opsz=144, SOFT=100)
            blur_in(c, fc.shape("Claude"), 1210, 830, PAPER, t, CLAUDE_T + 0.25, stagger=0.05)


# ---------------------------------------------------------------- 05 MACHINES OF LOVING GRACE

ESSAY_T = T_GRACE + 0.1
QUOTE_T = T_GRACE + 1.0
RULER_SQUEEZE = T_CENTURY + 0.5
DOMAINS = ["BIOLOGY & HEALTH", "NEUROSCIENCE & MIND", "ECONOMIC DEVELOPMENT", "PEACE & GOVERNANCE", "WORK & MEANING"]
DOMAIN_T = [T_DOMAINS + k * GR.spb / 2 for k in range(5)]
PLATE_N = 150


@lru_cache(maxsize=4)
def plate(idx):
    if not PLATE_DIR:
        return None
    p = os.path.join(PLATE_DIR, f"f{idx:04d}.png")
    if not os.path.exists(p):
        return None
    return G.image_from_rgba(cv2.cvtColor(cv2.imread(p, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGBA))


def city(c, t):
    idx = int(clamp((t - T_GRACE) * 60, 0, PLATE_N - 1)) + 1
    img = plate(idx)
    if img is not None:
        G.draw_image(c, img, 0, 0, W, H)
        return
    fill(c, "#0c0908")      # stand-in until the Blender plate exists
    for i in range(400):
        x = hash01(i, 1) * W
        y = 380 + hash01(i, 2) ** 0.6 * 700
        if hash01(i, 3) < clamp((t - T_GRACE) / 1.5):
            G.circle(c, x, y, 1.5 + 2 * hash01(i, 4), G.P(KRAFT, 0.8))


def s_grace(c, t):
    if t < T_CENTURY:
        city(c, t)
        c.drawRect(skia.Rect.MakeWH(W, 520), G.P(INK, 1, shader=G.linear_grad(0, 0, 0, 520, [INK, INK], alphas=[0.85, 0.0])))
        c.drawRect(skia.Rect.MakeXYWH(0, 640, W, 440), G.P(INK, 1, shader=G.linear_grad(0, 640, 0, H, [INK, INK], alphas=[0.0, 0.9])))
        chapter(c, t, T_GRACE, "05", "MACHINES OF LOVING GRACE", PAPER, KRAFT)
        f = G.Font("fraunces-italic", 128, wght=360, opsz=144, SOFT=100, WONK=1)
        run = f.shape("Machines of Loving Grace")
        blur_in(c, run, CX - run.width / 2, 400, PAPER, t, ESSAY_T, stagger=0.03)
        fm = G.Font("mono", 17, wght=650)
        G.text(c, G.scramble("AN ESSAY BY DARIO AMODEI  ·  OCTOBER 2024", clamp((t - ESSAY_T - 0.5) / 0.4), 5, t),
               CX, 470, fm, G.P(KRAFT), align=0.5, tracking=0.26)
        fq = G.Font("serif-italic", 76)
        q = "“a country of geniuses in a datacenter”"
        rq = fq.shape(q)
        blur_in(c, rq, CX - rq.width / 2, 910, PAPER, t, QUOTE_T, stagger=0.018, blur=10)
        return
    if t < T_DOMAINS:
        fill(c, PAPER)
        chapter(c, t, T_CENTURY, "05", "THE COMPRESSED 21ST CENTURY", INK, CLAY)
        f = G.Font("fraunces-italic", 118, wght=380, opsz=144, SOFT=100)
        run = f.shape("the compressed 21st century")
        blur_in(c, run, CX - run.width / 2, 380, INK, t, T_CENTURY + 0.05, stagger=0.02)
        sq = whip(clamp((t - RULER_SQUEEZE) / 0.55))
        x0, x1 = 160, 1760
        xe = lerp(x1, x0 + (x1 - x0) * 0.1, sq)
        y = 640
        grow = snap(clamp((t - T_CENTURY) / 0.45))
        c.drawLine(x0, y, x0 + (xe - x0) * grow, y, G.P(INK, 1, stroke=2))
        for k in range(101):
            u = k / 100
            if u > grow:
                break
            x = x0 + (xe - x0) * u
            major = k % 10 == 0
            c.drawLine(x, y, x, y - (34 if major else 14), G.P(CLAY if major else INK, 1, stroke=2.2 if major else 1.2))
        fm = G.Font("mono", 18, wght=700)
        a1 = clamp((t - T_CENTURY - 0.25) / 0.3)
        # a bracket that shrinks with the ruler: the span it measures stays labelled
        c.drawLine(x0, y + 44, x0 + (xe - x0) * grow, y + 44, G.P(CLAY if sq > 0.5 else INK, 0.6 * a1, stroke=1.4))
        for xx in (x0, x0 + (xe - x0) * grow):
            c.drawLine(xx, y + 36, xx, y + 52, G.P(CLAY if sq > 0.5 else INK, 0.6 * a1, stroke=1.4))
        if sq > 0:
            c.drawLine(xe, y, x1, y, G.P(INK, 0.14 * sq, stroke=1.2, effect=G.dash(6, 8)))
        left = "50–100 YEARS OF PROGRESS"
        right = "  →  5–10 YEARS"
        wl = fm.width(left, 0.26)
        wr = fm.width(right, 0.26)
        xs = CX - (wl + wr * sq) / 2
        G.text(c, left, xs, y + 110, fm, G.P(INK, a1), tracking=0.26)
        if sq > 0:
            G.text(c, right, xs + wl, y + 110, fm, G.P(CLAY, sq), tracking=0.26)
        return
    # five domains, rising like a sun
    fill(c, INK)
    chapter(c, t, T_DOMAINS, "05", "HOW AI COULD TRANSFORM THE WORLD", PAPER, KRAFT)
    rise = out_cubic(clamp((t - T_DOMAINS) / 1.2))
    sx, sy = CX, lerp(1260, 1080, rise)
    r = 330
    c.drawCircle(sx, sy, 900, G.P(CLAY, 1, shader=G.radial_grad(sx, sy, 900, [CLAY, INK], alphas=[0.5, 0.0])))
    c.drawCircle(sx, sy, r, G.P(CLAY, 1, shader=G.radial_grad(sx, sy - 80, r, ["#f3b58f", CLAY])))
    fl = G.Font("mono", 20, wght=700)
    for k, (name, tk) in enumerate(zip(DOMAINS, DOMAIN_T)):
        u = snap(clamp((t - tk) / 0.35))
        if u <= 0:
            continue
        ang = math.radians(-90 + (k - 2) * 27)
        L0, L1 = r + 30, r + 30 + (330 if k == 2 else 390) * u
        xa, ya = sx + math.cos(ang) * L0, sy + math.sin(ang) * L0
        xb, yb = sx + math.cos(ang) * L1, sy + math.sin(ang) * L1
        c.drawLine(xa, ya, xb, yb, G.P(KRAFT, 0.9, stroke=2.5, cap="round"))
        G.circle(c, xb, yb, 7, G.P(PAPER))
        align = 0.5 if k == 2 else (1.0 if k < 2 else 0.0)
        dx = 0 if k == 2 else (-18 if k < 2 else 18)
        G.text(c, f"0{k + 1}", xb + dx, yb - 52, G.Font("mono", 14, wght=700), G.P(KRAFT, u), align=align, tracking=0.2)
        G.text(c, G.scramble(name, u, k, t), xb + dx, yb - 22, fl, G.P(PAPER, u), align=align, tracking=0.2)
    fi = G.Font("serif-italic", 56)
    run = fi.shape("How AI could transform the world for the better")
    blur_in(c, run, CX - run.width / 2, 290, PAPER, t, T_DOMAINS + 0.1, stagger=0.012, blur=8)


# ---------------------------------------------------------------- 06 DARIO AMODEI

NAME = "Dario Amodei"
NAME_T = [T_FIN + 0.1 + i * GR.spb / 8 for i in range(len(NAME))]
ROLE_T = T_FIN + 1.05
RECAP = ["PHYSICS", "SAFETY", "SCALE", "ANTHROPIC", "LOVING GRACE"]
RECAP_T = [T_FIN + 1.55 + k * GR.spb / 4 for k in range(5)]
TRACE_T = GR.at(15)


def s_finale(c, t):
    fill(c, INK)
    portrait = PH.available("dario")
    wg = lerp(220, 430, snap(clamp((t - T_FIN) / 1.4)))
    sweep = in_out_cubic(clamp((t - T_LAST) / 0.9))
    fr = G.Font("serif-italic", 64 if not portrait else 58)
    fm = G.Font("mono", 17 if not portrait else 13, wght=650)
    if portrait:
        pw = 760
        ph = int(min(760, max(500, pw / (PH.aspect("dario") or 1.0))))
        px, py = 1010, int(570 - ph / 2)
        pe = snap(clamp((t - T_FIN - 0.15) / 0.6))
        if pe > 0:
            img = PH.duotone("dario", pw, ph, "#1f1e1b", PAPER, 0.35)
            drift = 1.07 - 0.05 * clamp((t - T_FIN) / (DURATION - T_FIN))
            with G.clip_rect(c, px, py + ph * (1 - pe), pw, ph * pe):
                with G.xf(c, px + pw / 2, py + ph / 2, s=drift):
                    G.draw_image(c, img, -pw / 2, -ph / 2, pw, ph)
            c.drawRect(skia.Rect.MakeXYWH(px, py, pw, ph), G.P(PAPER, 0.12 * pe, stroke=1.5))
        f = G.Font("fraunces", 200, wght=wg, opsz=144, SOFT=100)
        r1, r2 = f.shape("Dario"), f.shape("Amodei")
        n1 = len(r1.gids)
        tx = 146
        G.light_sweep(c, lambda cc: (blur_in(cc, r1, tx, 470, PAPER, t, T_FIN, starts=NAME_T[:n1], dur=0.5, rise=50, blur=16),
                                     blur_in(cc, r2, tx, 670, PAPER, t, T_FIN, starts=NAME_T[n1 + 1:], dur=0.5, rise=50, blur=16)),
                      tx - 300, tx + max(r1.width, r2.width) + 300, 560, sweep, colors=("#ffd9a8", "#f3b58f"), width=240)
        la = snap(clamp((t - T_FIN - 0.6) / 0.4))
        if la > 0:
            LG.mark(c, "anthropic", tx + 34, 250, 56 * la, G.P(PAPER, 0.85 * la))
        rr = fr.shape("Co-founder & CEO, Anthropic")
        blur_in(c, rr, tx + 4, 764, CLAY, t, ROLE_T, stagger=0.015, blur=8)
        rx, ry = tx + 6, 838
        tr_x0, tr_x1, tr_y, spike_x = tx, 900, 900, (tx + 900) / 2
    else:
        f = G.Font("fraunces", 236, wght=wg, opsz=144, SOFT=100)
        run = f.shape(NAME)
        x = CX - run.width / 2
        G.light_sweep(c, lambda cc: blur_in(cc, run, x, 560, PAPER, t, T_FIN, starts=NAME_T[:len(run.gids)], dur=0.5,
                                            rise=50, blur=16),
                      x - 300, x + run.width + 300, 480, sweep, colors=("#ffd9a8", "#f3b58f"), width=240, strength=1.0)
        la = snap(clamp((t - T_FIN - 0.6) / 0.4))
        if la > 0:
            LG.mark(c, "anthropic", CX, 250, 64 * la, G.P(PAPER, 0.85 * la))
        rr = fr.shape("Co-founder & CEO, Anthropic")
        blur_in(c, rr, CX - rr.width / 2, 668, CLAY, t, ROLE_T, stagger=0.015, blur=8)
        sep_w = fm.width("   ·   ".join(RECAP), 0.26)
        rx, ry = CX - sep_w / 2, 760
        tr_x0, tr_x1, tr_y, spike_x = 300, 1620, 880, CX
    sep = "   ·   " if not portrait else "  ·  "
    xx = rx
    for k, (name, tk) in enumerate(zip(RECAP, RECAP_T)):
        a = clamp((t - tk) / 0.25)
        tr = 0.26 if not portrait else 0.2
        G.text(c, G.scramble(name, a, k, t), xx, ry, fm, G.P(PAPER, 0.75 * a), tracking=tr)
        xx += fm.width(name + sep, tr)
    # the trace from the prologue returns, flat, and fires once on the last chord
    tu = clamp((t - TRACE_T) / 1.9)
    if tu > 0:
        n = 600
        xs = np.linspace(tr_x0, tr_x0 + (tr_x1 - tr_x0) * snap(tu), n)
        ys = tr_y + 1.6 * np.sin(xs * 0.07 + t * 5)
        fire = t - T_LAST
        if fire > -0.01:
            dt = (xs - spike_x) / 800.0
            ys = ys + 120 * (-np.exp(-((dt - 0.0015) / 0.0011) ** 2) + 0.38 * np.exp(-((dt - 0.0055) / 0.0028) ** 2)) * math.exp(-max(fire, 0) / 1.2)
        path = skia.Path()
        path.addPoly([skia.Point(float(a), float(b)) for a, b in zip(xs, ys)], False)
        c.drawPath(path, G.P(PAPER, 0.8, stroke=1.8, join="round"))
        G.circle(c, xs[-1], ys[-1], 5, G.P(CLAY))
        if fire > 0:
            g = math.exp(-fire / 0.25)
            G.circle(c, spike_x, tr_y - 60, 30 + 60 * g, G.P(CLAY, 0.3 * g))
    fa = clamp((t - T_LAST - 0.3) / 0.5)
    if fa > 0:
        fm2 = G.Font("mono", 15, wght=600)
        G.text(c, "A TRIBUTE  ·  EVERY FRAME WRITTEN IN CODE", CX, H - 118, fm2, G.P(PAPER, 0.8 * fa), align=0.5, tracking=0.3)
        fd = G.Font("mono", 11, wght=500)
        note = "FAN-MADE  ·  NOT AFFILIATED WITH OR ENDORSED BY ANTHROPIC"
        cr = PH.credit()
        if cr:
            note = f"PHOTOS: {cr}  ·  " + note
        G.text(c, note, CX, H - 50, fd, G.P(PAPER, 0.45 * fa), align=0.5, tracking=0.2)
    out = clamp((t - (DURATION - 0.9)) / 0.9)
    if out > 0:
        fill(c, "#000000", out)
