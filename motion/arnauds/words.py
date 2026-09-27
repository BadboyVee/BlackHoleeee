"""Type as picture: the giant words in black, the ring of beads that thinks, and the closing lines."""
import math
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, lerp, snap, whip, out_cubic, in_out_cubic
from .look import F, T, ui, WHITE, INK, SHADOW, glow_blob, draw_cover, ground, VIVID_GOLD, EMERALD
from .score import WORDS, T_FIND, T_DROPS, T_RISE, T_LIME, T_CRAVE, T_ROLL, T_WAIT

GIANT = 420
BASE = 700
OUTLINE = 6          # the black line around the white letters, outside them


# ---------------------------------------------------------------- giant words

def giant_font():
    return F("serif", GIANT)


def word_font(fill):
    """The same serif as the name; the special word leans into italic."""
    return F("serif-italic", GIANT) if fill == "glow" else giant_font()


@lru_cache(maxsize=1)
def giant_layout():
    space = giant_font().width(" ")
    out, x = [], 0.0
    for t0, word, fill in WORDS:
        w = word_font(fill).width(word)
        out.append(dict(t=t0, word=word, fill=fill, x=x, w=w))
        x += w + space
    return out


def _typed(t, t0, word):
    return int(math.ceil(len(word) * clamp((t - t0) / 0.14)))


def giant_cam(t):
    """Camera x (the left edge of the frame in line coordinates): the caret rides at ~70% of the width."""
    lay = giant_layout()
    x = -700.0
    for i, it in enumerate(lay):
        target = it["x"] + it["w"] - 1250
        u = clamp((t - it["t"] + 0.12) / 0.34)
        x = lerp(x, target, whip(u) if i else in_out_cubic(u))
    return x


def typed_part(it, t):
    return it["word"][:_typed(t, it["t"], it["word"])]


def typed_end(it, t):
    part = typed_part(it, t)
    return it["x"] + (word_font(it["fill"]).shape(part).width if part else 0.0)


def word_fill(c, it, x, y, t):
    """A giant word in the serif: white letters, a black line around them and a soft black shadow."""
    part = typed_part(it, t)
    if not part:
        return
    path = word_font(it["fill"]).shape(part).path(x, y)
    with G.xf(c, 0, 18):
        c.drawPath(path, G.P(INK, 0.3, blur=24))
    c.drawPath(path, G.P(INK, 1, stroke=2 * OUTLINE, join="round"))
    c.drawPath(path, G.P(WHITE))


def giant_caret(c, x, top, h):
    """The caret in the words' own style: a white bar lined in black."""
    bw = 12
    c.drawRect(skia.Rect.MakeXYWH(x - bw - OUTLINE, top - OUTLINE, bw + 2 * OUTLINE, h + 2 * OUTLINE), G.P(INK))
    c.drawRect(skia.Rect.MakeXYWH(x - bw, top, bw, h), G.P(WHITE))


def giant(c, t):
    ground(c, t)
    lay = giant_layout()
    cam = giant_cam(t)
    c.save()
    c.translate(-cam, 0)
    alive = [it for it in lay if t >= it["t"]]
    top, h = BASE - giant_font().cap - 40, giant_font().cap + 140
    for it in alive:
        word_fill(c, it, it["x"], BASE, t)
    x = typed_end(alive[-1], t) + 34 if alive else lay[0]["x"] + 10
    giant_caret(c, x, top, h)
    c.restore()


# ---------------------------------------------------------------- beads that think, a coin that answers

RING = (960, 600, 250)          # centre and radius of the bead ring
CHIPS = ["pizza", "sushi", "ramen"]
BEADS = 44
RING_BEADS = (VIVID_GOLD, EMERALD, WHITE)


def field(c, t):
    """The thinking scene and the carousel sit on the film's one ground."""
    ground(c, t)


def bead(c, x, y, r, col, a=1.0):
    c.drawCircle(x, y + r * 0.35, r, G.P(SHADOW, 0.3 * a, blur=r * 0.5))
    c.drawCircle(x, y, r, G.P(col, a, shader=G.radial_grad(x - r * 0.35, y - r * 0.4, r * 1.6,
                                                         [G.mixc(col, "#ffffff", 0.55), col, G.mixc(col, "#000000", 0.45)],
                                                         stops=[0.0, 0.45, 1.0])))
    G.circle(c, x - r * 0.35, y - r * 0.38, r * 0.22, G.P("#ffffff", 0.85 * a))


def doubloon(c, x, y, r, flip, t, a=1.0):
    """A Mardi Gras doubloon: bright gold, ridged, stamped with the A. `flip` is the coin's turn in radians."""
    sx = math.cos(flip)
    face = abs(sx)
    with G.layer(c, alpha=a):
        glow_blob(c, x, y, r * 2.6, VIVID_GOLD, 0.5)
        with G.xf(c, x, y, sx=max(0.04, face), sy=1.0):
            G.circle(c, 0, 0, r, G.P("#c98a00"))
            c.drawCircle(0, 0, r * 0.97, G.P(VIVID_GOLD, 1, shader=G.linear_grad(
                -r, -r, r, r, ["#fff3b0", VIVID_GOLD, "#e0a100", VIVID_GOLD])))
            for k in range(72):
                ang = 2 * math.pi * k / 72
                c.drawLine(math.cos(ang) * r * 0.9, math.sin(ang) * r * 0.9, math.cos(ang) * r * 0.97,
                           math.sin(ang) * r * 0.97, G.P("#b07800", 0.7, stroke=2))
            G.circle(c, 0, 0, r * 0.78, G.P("#a8791a", 0.8, stroke=3))
            if sx > 0:
                T(c, "A", 0, r * 0.3, F("serif", r * 0.95), "#6b4a0c", align=0.5)
                ring = "ARNAUD’S  ·  1918  ·  "
                f = ui(max(10, r * 0.13), 700)
                run = f.shape(ring, 0.25)
                for i, gid, gx, adv in run.glyphs():
                    ang = -math.pi / 2 + 2 * math.pi * (gx + adv / 2) / run.width
                    with G.xf(c, math.cos(ang) * r * 0.86, math.sin(ang) * r * 0.86, rot=math.degrees(ang) + 90):
                        G.glyph(c, f, gid, -adv / 2, f.cap / 2, G.P("#6b4a0c"))
            else:
                T(c, "1918", 0, r * 0.14, ui(r * 0.4, 800), "#6b4a0c", align=0.5)
        # a glint crossing the face
        g = ((t * 0.9) % 1.0)
        if face > 0.3:
            with G.clip_rect(c, x - r * face, y - r, 2 * r * face, 2 * r):
                c.drawLine(x - r + 2 * r * g - 40, y - r, x - r + 2 * r * g + 40, y + r, G.P("#ffffff", 0.35, stroke=26, blur=10))


def finding(c, t, enter=1.0):
    """Finding something special: a ring of gold, green and white beads spins like a loader while the three cravings orbit
    inside it; one by one they are tossed away, and a gold doubloon flips into the middle."""
    field(c, t)
    gone = clamp((t - T_LIME) / 0.35)
    if gone >= 1:
        return
    c.saveLayerAlpha(None, int(255 * (1 - gone)))
    _finding(c, t)
    c.restore()


def _finding(c, t):
    # the label in the giant words' style: white serif lined in black
    f = F("serif", 72)
    dots = int((t - T_FIND) * 6) % 4
    label = "Finding something special"
    path = f.shape(label + "." * dots).path(960 - f.width(label) / 2, 196)
    with G.xf(c, 0, 8):
        c.drawPath(path, G.P(INK, 0.3, blur=10))
    c.drawPath(path, G.P(INK, 1, stroke=4.5, join="round"))
    c.drawPath(path, G.P(WHITE))
    cx, cy, R = RING
    found = clamp((t - T_RISE) / 0.5)
    spin = (t - T_FIND) * 2.6
    head = spin % (2 * math.pi)
    Rr = R * (1 - 0.12 * snap(found))
    for i in range(BEADS):
        ang = 2 * math.pi * i / BEADS + spin * 0.35
        d = (head - (2 * math.pi * i / BEADS)) % (2 * math.pi)
        lit = math.exp(-d * 1.4)                    # a comet of brighter, bigger beads chases round the ring
        col = G.mixc(RING_BEADS[i % 3], WHITE, 0.3 * max(lit, found))
        r = 13 + 6 * lit
        bead(c, cx + Rr * math.cos(ang), cy + Rr * math.sin(ang), r, col)
    # the cravings orbit inside, then get tossed
    for k, (name, td) in enumerate(zip(CHIPS, T_DROPS)):
        ang = -math.pi / 2 + 2 * math.pi * k / 3 - (t - T_FIND) * 1.3
        x, y = cx + 120 * math.cos(ang), cy + 120 * math.sin(ang)
        s, a = 1.0, 1.0
        rot = 0.0
        if t >= td:
            u = clamp((t - td) / 0.5)
            e = out_cubic(u)
            x += math.cos(ang) * 700 * e
            y += math.sin(ang) * 700 * e - 260 * e + 520 * e * e
            rot = 540 * e * (1 if k % 2 else -1)
            s = 1 - 0.4 * e
            a = 1 - u
            if a <= 0:
                continue
        with G.layer(c, alpha=a * clamp((t - T_FIND) / 0.25)):
            with G.xf(c, x, y, s=s, rot=rot):
                c.save()
                clip = skia.Path()
                clip.addCircle(0, 0, 62)
                c.clipPath(clip, skia.ClipOp.kIntersect, True)
                draw_cover(c, name, -64, -64, 128, 128, min_w=300)
                c.restore()
                G.circle(c, 0, 0, 62, G.P("#ffffff", 0.95, stroke=5))
    # the answer
    if t >= T_RISE - 0.05:
        u = clamp((t - T_RISE) / 0.6)
        flip = 5 * math.pi * (1 - out_cubic(u))
        r = 90 + 30 * out_cubic(u)
        doubloon(c, cx, cy - 30 * (1 - u), r, flip, t)
        if u > 0.6:
            v = clamp((u - 0.6) / 0.4)
            for k in range(8):
                ang = k * math.pi / 4 + t
                L = 160 + 120 * v
                px, py = cx + math.cos(ang) * L, cy + math.sin(ang) * L
                pts = G.star_points(4, 16 * (1 - v * 0.4), 4, cx=px, cy=py)
                c.drawPath(G.poly(pts), G.P(RING_BEADS[k % 3], 1 - v * 0.6))


# ---------------------------------------------------------------- closing lines

ROLL = [("pizza", "pizza"), ("sushi", "sushi"), ("ramen", "ramen"), ("something special", None)]
SPECIAL = ui(66, 700)     # the answer, in bold black with a white glow behind it


def crave(c, t):
    """You were craving pizza / sushi / ramen / something special. Now your table is waiting."""
    ground(c, t)
    f = ui(66, 460)
    lead = "You were craving"
    lw = f.width(lead + " ")
    idx = sum(1 for tr in T_ROLL if t >= tr)
    word, chip = ROLL[idx]
    ww = f.width(word) + 92 if chip else SPECIAL.width(word)
    x0 = 960 - (lw + ww) / 2
    rise = snap(clamp((t - T_WAIT) / 0.4))
    y = 520 - 70 * rise
    # the lead, word by word, the way the reference writes it
    x = x0
    for k, wd in enumerate(lead.split(" ")):
        u = clamp((t - T_CRAVE - 0.1 * k) / 0.3)
        T(c, wd, x, y + 14 * (1 - out_cubic(u)), f, INK, a=u)
        x += f.width(wd + " ")
    # the rolling slot
    prev_t = T_ROLL[idx - 1] if idx > 0 else T_CRAVE + 0.25
    u = clamp((t - prev_t) / 0.22)
    with G.clip_rect(c, x - 10, y - 100, 1400, 140):
        if idx > 0 and u < 1:
            pw, pc = ROLL[idx - 1]
            _slot(c, pw, pc, x, y - 110 * out_cubic(u), f, 1 - u, t)
        _slot(c, word, chip, x, y + 110 * (1 - out_cubic(u)), f, u, t)
    if t >= T_WAIT:
        g = ui(66, 460)
        words = "Now your table is waiting.".split(" ")
        total = sum(g.width(w + " ") for w in words) - g.width(" ")
        x = 960 - total / 2
        for k, wd in enumerate(words):
            v = clamp((t - T_WAIT - 0.1 - 0.12 * k) / 0.3)
            gap = 40 * (1 - out_cubic(v))
            T(c, wd, x + gap * k, y + 120, g, INK, a=v)
            x += g.width(wd + " ")


def _slot(c, word, chip, x, y, f, a, t):
    if chip:
        c.save()
        clip = skia.Path()
        clip.addCircle(x + 36, y - 24, 36)
        c.clipPath(clip, skia.ClipOp.kIntersect, True)
        draw_cover(c, chip, x, y - 60, 72, 72, alpha=a, min_w=200)
        c.restore()
        T(c, word, x + 92, y, f, INK, a=a)
    else:
        path = SPECIAL.shape(word).path(x, y)
        c.drawPath(path, G.P(WHITE, 0.8 * a, blur=16))
        c.drawPath(path, G.P(INK, a))
