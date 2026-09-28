"""AGI WEEK motion kit: masked kinetic type with a live weight morph, brand-mark mask reveals, particle bursts,
shockwaves, speed lines, trim-path strokes, card glints and 3D tilts."""
import math
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, out_back, spring, hash01
from . import marks as M
from .look import F, WHITE


# ---------------------------------------------------------------- type

def vfont(fam, size, w):
    """A variable face at a weight quantised to 25, so a morph reuses a handful of cached instances."""
    w = max(100, min(900, int(round(w / 25.0)) * 25))
    if fam == "inter":
        return F("inter", size, wght=w, opsz=32)
    if fam == "fraunces":
        return F("fraunces", size, wght=w, opsz=144, SOFT=0, WONK=0)
    if fam == "fraunces-italic":
        return F("fraunces-italic", size, wght=w, opsz=144, SOFT=0, WONK=1)
    return F(fam, size, wght=w)


def mask_rise(c, text, x, y, size, col, t, t0, fam="inter", w0=200, w1=800, stagger=0.028, dur=0.6, align=0.0,
              a=1.0, tr0=0.08, tr1=-0.01, shader=None, rise=1.08, glow=None):
    """Kinetic type. Each letter rises out from behind its own baseline mask on an expo ease while its weight grows
    from w0 to w1, and the whole word's tracking closes from tr0 to tr1. Returns the width at rest."""
    final = vfont(fam, size, w1)
    run = final.shape(text, tr1)
    n = max(1, len(run.gids))
    total = dur + stagger * (n - 1)
    g = out_expo(clamp((t - t0) / total))
    extra = (tr0 - tr1) * size * (1 - g)                 # the extra letter-spacing still to close
    width = run.width + extra * (n - 1)
    x0 = x - width * align
    top = y - size * 1.05
    bottom = y + size * 0.3
    if t < t0:
        return run.width
    with G.clip_rect(c, x0 - size, top, width + 2 * size, bottom - top):
        for i, gid, gx, adv in run.glyphs():
            u = clamp((t - t0 - stagger * i) / dur)
            if u <= 0:
                continue
            e = out_expo(u)
            wt = lerp(w0, w1, out_cubic(u))
            f = vfont(fam, size, wt)
            gxx = x0 + gx + extra * i
            gy = y + size * rise * (1 - e)
            if glow is not None:
                G.glyph(c, f, gid, gxx, gy, G.P(glow[0], glow[1] * a * u, blur=size * 0.12))
            p = G.P(col, a)
            if shader is not None:
                p.setShader(shader)
                p.setAlphaf(a)
            G.glyph(c, f, gid, gxx, gy, p)
    return run.width


def words_rise(c, words, x, y, size, col, t, fam="inter", w0=250, w1=700, align=0.0, a=1.0, gap=None):
    """A line of words, each with its own start time [(t0, word)], each rising out of its mask."""
    f = vfont(fam, size, w1)
    sp = gap if gap is not None else f.width(" ")
    total = sum(f.width(w) for _, w in words) + sp * (len(words) - 1)
    cx = x - total * align
    for t0, w in words:
        mask_rise(c, w, cx, y, size, col, t, t0, fam=fam, w0=w0, w1=w1, stagger=0.02, dur=0.45, a=a, tr0=0.04)
        cx += f.width(w) + sp


def typewriter(text, t, t0, cps=28.0):
    n = int(max(0.0, t - t0) * cps)
    return text[:n]


# ---------------------------------------------------------------- mask reveals

@lru_cache(maxsize=None)
def _mark_path(name):
    p = M._path(name)
    b = p.getBounds()
    return p, b.centerX(), b.centerY(), max(b.width(), b.height())


def mark_path(name, cx, cy, size, rot=0.0):
    p, bx, by, bs = _mark_path(name)
    m = skia.Matrix()
    m.setTranslate(-bx, -by)
    m.postScale(size / bs, size / bs)
    if rot:
        m.postRotate(rot)
    m.postTranslate(cx, cy)
    out = skia.Path(p)
    out.transform(m)
    return out


def reveal_through(c, name, cx, cy, u, draw_fn, t, rot=0.0, max_size=6400, edge=WHITE):
    """The next scene opens inside a brand mark that grows from nothing to past the frame, turning as it goes."""
    if u <= 0:
        return
    size = max_size * (u ** 2.2)
    path = mark_path(name, cx, cy, max(1.0, size), rot)
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    draw_fn(c, t)
    c.restore()
    # marks have holes and thin arms; the last stretch hands over to the whole scene so nothing is left uncovered
    fill = clamp((u - 0.72) / 0.28)
    if fill > 0:
        with G.layer(c, alpha=fill):
            draw_fn(c, t)
    if u < 1:
        a = math.sin(math.pi * u)
        c.drawPath(path, G.P(edge, 0.9 * a, stroke=3 + 5 * a))
        c.drawPath(path, G.P(edge, 0.35 * a, stroke=24, blur=18))


def blinds(c, u, draw_fn, t, n=9, vertical=False):
    """Venetian blinds: strips of the next scene open one after another."""
    if u <= 0:
        return
    p = skia.Path()
    for k in range(n):
        v = clamp(u * 1.6 - k * 0.6 / n)
        v = out_cubic(v)
        if v <= 0:
            continue
        if vertical:
            w = 1920 / n
            p.addRect(skia.Rect.MakeXYWH(k * w, 0, w * v + 1, 1080))
        else:
            h = 1080 / n
            p.addRect(skia.Rect.MakeXYWH(0, k * h + h * (1 - v) / 2, 1920, h * v + 1))
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    draw_fn(c, t)
    c.restore()


# ---------------------------------------------------------------- particles and energy

def burst(c, x, y, t, t0, n=28, cols=(WHITE,), speed=900.0, life=0.9, size=5.0, seed=0, gravity=500.0,
          streak=0.035):
    """Sparks thrown out from a point: each flies, slows, falls and fades, drawn as a short streak."""
    k = t - t0
    if k < 0 or k > life * 1.3:
        return
    for i in range(n):
        ang = 2 * math.pi * float(hash01(i, seed * 3 + 1)) + 0.3 * float(hash01(i, seed + 7))
        sp = speed * (0.35 + 0.65 * float(hash01(i, seed * 5 + 2)))
        lf = life * (0.55 + 0.45 * float(hash01(i, seed * 7 + 3)))
        if k > lf:
            continue
        drag = 3.2
        d = sp * (1 - math.exp(-drag * k)) / drag
        vx, vy = math.cos(ang), math.sin(ang)
        px = x + vx * d
        py = y + vy * d + 0.5 * gravity * k * k
        v = sp * math.exp(-drag * k)
        tail = v * streak
        a = (1 - k / lf) ** 1.5
        col = cols[i % len(cols)]
        c.drawLine(px, py, px - vx * tail, py - vy * tail - gravity * k * streak,
                   G.P(col, a, stroke=size * (0.5 + 0.5 * float(hash01(i, seed + 11))), cap="round"))


def shockwave(c, x, y, t, t0, col=WHITE, r0=30.0, r1=900.0, dur=0.6, width=10.0, a=1.0):
    k = (t - t0) / dur
    if not 0 <= k < 1:
        return
    e = out_expo(k)
    r = lerp(r0, r1, e)
    c.drawCircle(x, y, r, G.P(col, a * (1 - k) ** 1.4, stroke=width * (1 - k) + 1))
    c.drawCircle(x, y, r, G.P(col, a * 0.35 * (1 - k), stroke=width * 3, blur=16))


def speed_lines(c, cx, cy, amt, t, col=WHITE, n=70, seed=4):
    """Radial streaks rushing out from the centre, for pushes and drops."""
    if amt <= 0.01:
        return
    for i in range(n):
        ang = 2 * math.pi * float(hash01(i, seed))
        ph = (float(hash01(i, seed + 1)) + t * (1.6 + 1.4 * float(hash01(i, seed + 2)))) % 1.0
        r0 = 200 + 1300 * ph * ph
        L = (80 + 420 * ph) * amt
        x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0 * 0.7
        x1, y1 = cx + math.cos(ang) * (r0 + L), cy + math.sin(ang) * (r0 + L) * 0.7
        c.drawLine(x0, y0, x1, y1, G.P(col, amt * 0.55 * math.sin(math.pi * ph), stroke=1.5 + 2 * ph, cap="round"))


def glint(c, rrect, t, t0, dur=0.7, a=0.55, width=160.0):
    """A specular band of light crossing a card once, clipped to it."""
    k = (t - t0) / dur
    if not 0 <= k < 1:
        return
    r = rrect.rect()
    x = lerp(r.left() - width * 2, r.right() + width * 2, out_cubic(k))
    c.save()
    c.clipRRect(rrect, skia.ClipOp.kIntersect, True)
    sh = G.linear_grad(x - width, r.top(), x + width, r.bottom(), [WHITE, WHITE, WHITE], alphas=[0.0, a, 0.0])
    c.drawRect(r, G.P(WHITE, 1, shader=sh))
    c.restore()


def draw_line(c, x0, y0, x1, y1, t, t0, col, width=3.0, dur=0.45, a=1.0):
    """A line that draws itself on from its start."""
    u = out_expo(clamp((t - t0) / dur))
    if u <= 0:
        return
    c.drawLine(x0, y0, lerp(x0, x1, u), lerp(y0, y1, u), G.P(col, a, stroke=width, cap="round"))


def trim_stroke(c, path, u, col, width, a=1.0, cap="round"):
    """A path stroked up to u of its length (After Effects' Trim Paths)."""
    if u <= 0:
        return
    p = G.P(col, a, stroke=width, cap=cap, join="round")
    eff = G.trim(0.0, u)
    if eff is not None and u < 1:
        p.setPathEffect(eff)
    c.drawPath(path, p)


# ---------------------------------------------------------------- space

def tilt(c, cx, cy, rx=0.0, ry=0.0, rz=0.0, D=1700.0):
    """Tilt what follows like a card in 3D around the screen point (cx, cy)."""
    if abs(rx) < 0.01 and abs(ry) < 0.01 and abs(rz) < 0.01:
        return
    c.concat(G.perspective(cx, cy, rx=rx, ry=ry, rz=rz, D=D))


def swing_in(t, t0, freq=2.1, damp=0.55):
    """0 -> 1 on a spring, for panels swinging into place."""
    return spring(t - t0, freq, damp) if t >= t0 else 0.0


def float_y(t, phase=0.0, amp=6.0, speed=1.3):
    return amp * math.sin(t * speed + phase)


def overshoot(u, s=1.7):
    return out_back(clamp(u), s)


# ---------------------------------------------------------------- founders

def founder(c, key, x, y, size, t, t0, ring=WHITE, text_col=WHITE, sub_col=None, side="right", rect_h=None, a=1.0):
    """A founder's portrait opens: the mask grows from its centre on an expo ease while the photo inside eases back
    from a slow push (Ken Burns), a ring draws itself round, then the name rises out of its mask."""
    from .look import FOUNDERS, portrait_image, rr, ui
    if t < t0 or a <= 0:
        return
    f = FOUNDERS[key]
    u = out_expo(clamp((t - t0) / 0.7))
    kb = lerp(1.22, 1.0, out_cubic(clamp((t - t0) / 1.6)))
    img = portrait_image(key, int(size * 2.4))
    circle = "circle" in f
    w = size
    h = size if circle else (rect_h or size * 0.66)
    with G.layer(c, alpha=a):
        # the shadow grows with the mask
        if circle:
            c.drawCircle(x, y + 14, w / 2 * u, G.P("#000000", 0.35 * u, blur=22))
        else:
            c.drawRRect(rr(x - w / 2 * u, y - h / 2 * u + 14, w * u, h * u, 28), G.P("#000000", 0.3 * u, blur=24))
        c.save()
        clip = skia.Path()
        if circle:
            clip.addCircle(x, y, max(0.5, w / 2 * u))
        else:
            clip.addRRect(rr(x - w / 2 * u, y - h / 2 * u, w * u, h * u, 28 * u + 1))
        c.clipPath(clip, skia.ClipOp.kIntersect, True)
        if img is not None:
            iw = w * kb
            ih = iw * img.height() / img.width()
            G.draw_image(c, img, x - iw / 2, y - ih / 2 if not circle else y - iw / 2, iw, ih)
        c.restore()
        # the ring draws itself on, then a pulse of light runs off it
        v = clamp((t - t0 - 0.15) / 0.6)
        ring_path = skia.Path()
        if circle:
            ring_path.addArc(skia.Rect.MakeXYWH(x - w / 2 - 7, y - w / 2 - 7, w + 14, w + 14), -90, 359.9)
        else:
            ring_path.addRRect(rr(x - w / 2 - 6, y - h / 2 - 6, w + 12, h + 12, 32))
        trim_stroke(c, ring_path, out_cubic(v), ring, 4)
        k = (t - t0 - 0.75) / 0.6
        if 0 <= k < 1:
            c.drawPath(ring_path, G.P(ring, 0.5 * (1 - k), stroke=4 + 26 * k, blur=10 * k + 2))
    # the caption
    if circle:
        half = size / 2 + 36
        tx = x + half if side == "right" else x - half
        al = 0.0 if side == "right" else 1.0
        ty = y + 2
    else:
        tx, al, ty = x - size / 2, 0.0, y + h / 2 + 60
    mask_rise(c, f["name"], tx, ty, 34, text_col, t, t0 + 0.3, w0=300, w1=680, stagger=0.012, dur=0.45, align=al,
              a=a, tr0=0.05)
    r = clamp((t - t0 - 0.55) / 0.4)
    if r > 0:
        fr = ui(22, 500)
        from .look import T
        T(c, f["role"], tx, ty + 38 + 10 * (1 - out_cubic(r)), fr, sub_col or text_col, a=a * r * 0.75, align=al,
          tracking=0.02)
        lw = fr.width(f["role"], 0.02)
        x0 = tx if al == 0 else tx - lw
        draw_line(c, x0, ty + 56, x0 + min(90.0, lw), ty + 56, t, t0 + 0.6, ring, 2.5, a=a * 0.9)
