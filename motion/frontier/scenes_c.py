"""THE CLASH and the finale."""
import math
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from engine.core import (clamp, lerp, anim, snap, whip, out_expo, in_expo, out_cubic, in_out_cubic,
                         W, H, CX, CY, hash01)
from .common import (INK, PAPER, WHITE, GREEN, BLUE, VIOLET, CLAY, BOOK, CONTENDERS, fill, fit,
                     draw_glyphs, kick_env, with_alpha, lab_logo, model_logo)
from engine import logos as LG
from .score import G as GR, KICKS, T_DROP_A, T_DROP_B, T_DROP_C, T_CLASH, T_BUILD, T_FINALE, T_LAST, BREATH, DURATION

PLATE_DIR = None
PANELS = [(INK, GREEN, WHITE), (BLUE, WHITE, VIOLET), (PAPER, CLAY, BOOK)]


def accent_at(t):
    if T_DROP_A <= t < T_DROP_B:
        return GREEN
    if T_DROP_B <= t < T_DROP_C:
        return VIOLET
    if T_DROP_C <= t < T_CLASH:
        return CLAY
    return None


# ---------------------------------------------------------------- the clash: a triptych on the beat

def weights(t):
    b = (t - T_CLASH) / GR.spb
    targets = [[3.2, 1, 1], [1, 3.2, 1], [1, 1, 3.2], [1, 1, 1]]
    i = max(0, min(3, int(b)))
    prev = targets[i - 1] if i > 0 else [1, 1, 1]
    e = whip(clamp((b - i) / 0.32))
    w = [lerp(prev[k], targets[i][k], e) for k in range(3)]
    s = sum(w)
    return [W * v / s for v in w]


def motif(c, k, x, y, col, t):
    if k == 0:
        LG.mark(c, "openai", x, y, 92, G.P(col), rot=40 * t)
    elif k == 1:
        LG.gemini(c, x, y, 100, 1.0, rot=0, colors=["#ffffff", "#e3dcff", "#ffffff"])
    else:
        LG.claude(c, x, y, 104, col, 1.0, 1.0, rot=-30 * t, t=t)


def vertical_name(c, text, cx, cy, width, col, max_len=640):
    size = min(max(width * 0.95, 60), 360)
    f125 = G.Font("archivo", size, wght=900, wdth=125)
    f62 = G.Font("archivo", size, wght=900, wdth=62)
    w125, w62 = f125.width(text), f62.width(text)
    if w125 <= max_len:
        wd = 125
    elif w62 <= max_len:
        wd = 62 + 63 * (max_len - w62) / (w125 - w62)
    else:
        wd = 62
        size *= max_len / w62
    f = G.Font("archivo", size, wght=900, wdth=wd)
    run = f.shape(text)
    with G.xf(c, cx, cy, rot=-90):
        run.draw(c, -run.width / 2, f.cap / 2, G.P(col))


def triptych(c, t):
    fill(c, PAPER)      # the panels whip in over the page FABLE left behind
    ws = weights(t)
    x = 0.0
    for k in range(3):
        bg, col, sub = PANELS[k]
        w = ws[k]
        u = whip(clamp((t - T_CLASH + 0.06 - k * 0.04) / 0.22))
        dy = (1 - u) * H * (-1 if k % 2 == 0 else 1)
        with G.clip_rect(c, x, 0, w + 0.5, H):
            c.save()
            c.translate(0, dy)
            c.drawRect(skia.Rect.MakeXYWH(x, 0, w + 1, H), G.P(bg))
            k_ = CONTENDERS[k]
            vertical_name(c, k_["name"], x + w / 2, CY + 10, w, col)
            fv = G.Font("fraunces-italic", 96, wght=500, opsz=144, SOFT=50)
            G.text(c, k_["ver"], x + w / 2, H - 150, fv, G.P(sub), align=0.5)
            motif(c, k, x + w / 2, 160, col, t)
            fm = G.Font("mono", 14, wght=700)
            if w > 300:
                G.text(c, k_["lab"], x + w / 2, H - 110, fm, G.P(sub, 0.8), align=0.5, tracking=0.2)
            c.restore()
        x += w
    for xx in (ws[0], ws[0] + ws[1]):
        c.drawLine(xx, 0, xx, H, G.P(INK, 0.4, stroke=2))


BUILD_KICKS = [k for k in KICKS if T_BUILD <= k < T_FINALE - BREATH]
STROBE = [(INK, WHITE), (BLUE, WHITE), (PAPER, INK), (INK, GREEN), (CLAY, INK), (BLUE, WHITE),
          (PAPER, BLUE), (INK, WHITE), (GREEN, INK), (INK, CLAY), (WHITE, INK)]


def build_state(t):
    n = sum(1 for k in BUILD_KICKS if k <= t)
    return n, STROBE[(n - 1) % len(STROBE)] if n > 0 else STROBE[0]


def build_ink(t):
    n, (bg, fg) = build_state(t)
    return fg


def strobe_title(c, t):
    n, (bg, fg) = build_state(t)
    fill(c, bg)
    last = BUILD_KICKS[n - 1] if n else T_BUILD
    shake = math.exp(-(t - last) / 0.06) * 10
    sx = (hash01(n, 3) - 0.5) * 2 * shake
    sy = (hash01(n, 7) - 0.5) * 2 * shake
    f = fit("THE FRONTIER", "archivo", 1720, wght=900, wdth=125)
    run = f.shape("THE FRONTIER")
    shown = [i for i, ch in enumerate("THE FRONTIER") if ch != " "]

    def fn(i):
        if i not in shown[:n]:
            return (0, 0, 1, 1, 0, 0)
        j = shown.index(i)
        if j == n - 1:
            e = out_expo(clamp((t - last) / 0.09))
            return (0, 0, lerp(1.45, 1, e), lerp(1.45, 1, e), 0, 1)
        return (0, 0, 1, 1, 0, 1)
    with G.xf(c, sx, sy):
        draw_glyphs(c, run, CX - run.width / 2, CY + f.cap / 2, G.P(fg), fn)
        fm = G.Font("mono", 18, wght=700)
        G.text(c, f"{n:02d} / 11", CX, CY + f.cap / 2 + 70, fm, G.P(fg, 0.7), align=0.5, tracking=0.3)


def s_clash(c, t):
    if t < T_BUILD:
        triptych(c, t)
    elif t < T_FINALE - BREATH:
        strobe_title(c, t)
    else:
        fill(c, "#000000")


# ---------------------------------------------------------------- finale

PLATE_N = 150
SLAB_X = [0.2198 * W, 0.5 * W, 0.7771 * W]


@lru_cache(maxsize=4)
def plate(idx):
    if not PLATE_DIR:
        return None
    p = os.path.join(PLATE_DIR, f"f{idx:04d}.png")
    if not os.path.exists(p):
        return None
    img = cv2.cvtColor(cv2.imread(p, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGBA)
    return G.image_from_rgba(img)


def fallback_plate(c, t):
    fill(c, "#050506")
    for k, col in enumerate((GREEN, BLUE, CLAY)):
        x = SLAB_X[k]
        rise = snap(clamp((t - T_FINALE - k * 0.1) / 0.42))
        top = lerp(900, 250, rise)
        c.drawRect(skia.Rect.MakeLTRB(x - 125, top, x + 125, 860), G.P("#0c0c0e"))
        c.drawRect(skia.Rect.MakeLTRB(x - 3, top + 30, x + 3, 840), G.P(col))


def s_finale(c, t):
    idx = int(clamp((t - T_FINALE) * 60, 0, PLATE_N - 1)) + 1
    img = plate(idx)
    push = 1 + 0.035 * in_out_cubic(clamp((t - T_FINALE - 2.4) / 3.2))
    with G.xf(c, CX, CY, s=push):
        c.translate(-CX, -CY)
        if img is not None:
            G.draw_image(c, img, 0, 0, W, H)
        else:
            fallback_plate(c, t)
    # colour haze behind each slab, pumping with the kick
    ke = kick_env(t)
    for k, col in enumerate((GREEN, BLUE, CLAY)):
        x = SLAB_X[k]
        r = 520
        c.drawCircle(x, 520, r, G.P(col, 1, blend=G.SCREEN,
                                     shader=G.radial_grad(x, 520, r, [col, "#000000"], alphas=[0.16 + 0.1 * ke, 0.0])))
    # shockwaves on the impact and on the last hit
    for t0, strength in ((T_FINALE, 1.0), (T_LAST, 0.6)):
        u = clamp((t - t0) / 0.8)
        if 0 < u < 1:
            r = 1700 * out_expo(u)
            G.circle(c, CX, CY, r, G.P(WHITE, strength * (1 - u) * 0.9, stroke=2 + 60 * (1 - u) ** 2))
    # title
    tt = T_FINALE + 0.25
    if t >= tt:
        tr = lerp(0.42, 0.02, snap(clamp((t - tt) / 1.3)))
        f = fit("THE FRONTIER", "archivo", 1180, wght=900, wdth=125)
        run = f.shape("THE FRONTIER", tr)

        def fn(i):
            a = clamp((t - (tt + i * 0.045)) / 0.2)
            return (0, 18 * (1 - snap(a)), 1, 1, 0, a)
        sweep = clamp((t - T_LAST) / 0.7)
        G.light_sweep(c, lambda cc: draw_glyphs(cc, run, CX - run.width / 2, 150 + f.cap / 2, G.P(WHITE), fn),
                      CX - run.width / 2 - 300, CX + run.width / 2 + 300, 150, in_out_cubic(sweep),
                      colors=(GREEN, "#8fa0ff", CLAY), width=300, strength=1.0)
        sa = clamp((t - tt - 0.8) / 0.4)
        if sa > 0:
            fm = G.Font("mono", 17, wght=600)
            G.text(c, G.scramble("THREE LABS  ·  THREE MINDS  ·  ONE FRONTIER", sa, 9, t), CX, 150 + f.cap / 2 + 56,
                   fm, G.P(WHITE, 0.75 * sa), align=0.5, tracking=0.32)
    # contender labels under each slab
    for k in range(3):
        ta = GR.at(15) + k * GR.spb / 2
        a = clamp((t - ta) / 0.3)
        if a <= 0:
            continue
        kk = CONTENDERS[k]
        x = SLAB_X[k]
        lab_logo(c, k, x, 855 - 10 * (1 - snap(a)), 46, a)
        fn_ = G.Font("archivo", 34, wght=900, wdth=118)
        fv = G.Font("fraunces-italic", 38, wght=500, opsz=144, SOFT=50)
        run = fn_.shape(kk["name"])
        vrun = fv.shape(kk["ver"])
        total = run.width + 10 + vrun.width
        x0 = x - total / 2
        yy = 925 + 14 * (1 - snap(a))
        run.draw(c, x0, yy, G.P(WHITE, a))
        vrun.draw(c, x0 + run.width + 10, yy + 2, G.P(kk["color"] if k != 1 else "#6f82ff", a))
        fm = G.Font("mono", 14, wght=600)
        G.text(c, G.scramble(kk["lab"], a, k, t), x, yy + 30, fm, G.P(WHITE, 0.6 * a), align=0.5, tracking=0.24)
    fa = clamp((t - T_LAST - 0.1) / 0.4)
    if fa > 0:
        fm = G.Font("mono", 15, wght=600)
        G.text(c, "EVERY FRAME WRITTEN IN CODE", CX, H - 76, fm, G.P(WHITE, 0.8 * fa), align=0.5, tracking=0.3)
        fd = G.Font("mono", 11, wght=500)
        G.text(c, "FAN-MADE  ·  NOT AFFILIATED WITH OPENAI, GOOGLE OR ANTHROPIC  ·  MARKS BELONG TO THEIR OWNERS",
               CX, H - 50, fd, G.P(WHITE, 0.45 * fa), align=0.5, tracking=0.2)
    out = clamp((t - (DURATION - 0.75)) / 0.75)
    if out > 0:
        fill(c, "#000000", out)
