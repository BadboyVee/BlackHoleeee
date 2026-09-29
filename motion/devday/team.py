"""DevDay 2026, the drop: the OpenAI team, as a hierarchy. The white line's points fly up into the OpenAI mark;
from it the chart grows on the beat: Sam Altman at the top, then a bar to Mark Chen, Greg Brockman and Thibault
Sottiaux below, each in a ring of the teaser's colours with their name and role built from points. The photographs
are the user's (photos/devday/, not in the repository); anyone without one yet is shown by initials."""
import os
from functools import lru_cache

import cv2
import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_back, in_back, in_out_sine
from .look import gsm, WHITE, DIM, PURPLE, ORANGE, GREEN, BLUE, MONO
from .type import Word, word, mark_glyph, draw_word, Build
from .launches import Station, StartStation, draw_chain
from .intro import LINE, LINE_BUILD
from .score import T_TEAM, T_WORLD, CX

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "..", "photos", "devday")

# key, name, role, centre, radius, ring colour, when it pops (s after the drop)
TEAM = [
    ("altman", "Sam Altman", "CEO", (960, 338), 124, PURPLE, 0.25),
    ("chen", "Mark Chen", "Chief Research Officer", (420, 752), 104, BLUE, 1.00),
    ("brockman", "Greg Brockman", "President", (960, 752), 104, GREEN, 1.25),
    ("sottiaux", "Thibault Sottiaux", "Codex lead", (1500, 752), 104, ORANGE, 1.50),
]
# the square to crop from each photograph (x0, y0, x1, y1); without one, a head-and-shoulders square from the top
CROP = {"altman": (176, 2, 360, 186), "chen": (0, 0, 400, 400), "sottiaux": (80, 10, 520, 450),
        "brockman": (37, 20, 517, 500)}
BAR_Y = 614
OUT = T_WORLD - 0.36               # the chart starts to fold away


# ---------------------------------------------------------------- the photographs

def _photo_path(key):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = os.path.join(PHOTOS, key + ext)
        if os.path.exists(p):
            return p
    return None


@lru_cache(maxsize=None)
def portrait_image(key, px):
    path = _photo_path(key)
    if path is None:
        return None
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    if key in CROP:
        x0, y0, x1, y1 = CROP[key]
    else:
        side = min(w, h) if h <= w else int(w * 0.92)
        x0 = (w - side) // 2
        y0 = 0 if h <= w else int(h * 0.03)
        x1, y1 = x0 + side, min(h, y0 + side)
    sq = img[max(0, y0):y1, max(0, x0):x1]
    sq = cv2.resize(sq, (px, px), interpolation=cv2.INTER_AREA)
    rgba = cv2.cvtColor(sq, cv2.COLOR_BGR2RGBA)
    return G.image_from_rgba(rgba)


def portrait(c, key, name, x, y, r, s, ring, a=1.0):
    """A photograph in a ring of colour; initials on a dark disc until there is one."""
    R = r * s
    if R <= 0.5 or a <= 0:
        return
    c.drawCircle(x, y, R + 9, G.P(ring, a))
    c.drawCircle(x, y, R + 3, G.P("#000000", a))
    img = portrait_image(key, int(2 * r))
    if img is not None:
        c.save()
        clip = skia.Path()
        clip.addCircle(x, y, R)
        c.clipPath(clip, doAntiAlias=True)
        G.draw_image(c, img, x - R, y - R, 2 * R, 2 * R, a)
        c.restore()
    else:
        c.drawCircle(x, y, R, G.P("#1d1d1f", a))
        initials = "".join(p[0] for p in name.split()[:2])
        G.text(c, initials, x, y, gsm(R * 0.62), G.P(ring, a), align=0.5, anchor="cap")


# ---------------------------------------------------------------- the chart

LOGO = Word.of([mark_glyph("openai", CX, 128, 92, WHITE)], 92, 128)
_LINE = StartStation(LINE, LINE_BUILD, ORANGE)
CHAIN = [_LINE, Station(T_TEAM, LOGO, GREEN, _LINE, lead=0.22, fly=0.28)]
CHAIN[1].build = Build(CHAIN[1].land, spread=0.0, outline=0.03, fill=0.12, dots_off=0.2, pop=0.0, t_out=OUT + 0.12,
                       vanish=0.12)


def _labels():
    out = []
    for j, (key, name, role, (x, y), r, col, t0) in enumerate(TEAM):
        big = j == 0
        wn = word(((name, WHITE),), 52 if big else 42, x, y + r + (74 if big else 64), axes=(("wght", 560),))
        wr = word(((role.upper(), DIM),), 22 if big else 19, x, y + r + (112 if big else 98), fam=MONO,
                  axes=(("wght", 500),), tracking=0.12)
        t_out = OUT + 0.02 * (3 - j)
        bn = Build(T_TEAM + t0 + 0.1, spread=0.25, outline=0.03, fill=0.1, dots_off=0.18, t_out=t_out, vanish=0.12)
        br = Build(T_TEAM + t0 + 0.2, spread=0.25, outline=0.03, fill=0.1, dots_off=0.18, t_out=t_out, vanish=0.12)
        out.append((wn, bn, wr, br, col))
    return out


LABELS = _labels()


def lines(c, t):
    """The chart's lines: down from the mark to Sam Altman, then down to a bar and down again to the others."""
    k = t - T_TEAM
    fold = clamp((t - OUT) / 0.3)
    a = 0.55 * (1 - fold)
    if a <= 0:
        return
    p = G.P(WHITE, a, stroke=3, cap="round")
    top = TEAM[0]
    x0, y0 = top[3]
    u = clamp((k - 0.12) / 0.14)
    if u > 0:
        c.drawLine(x0, 180, x0, lerp(180, y0 - top[4] - 14, u), p)
    u = clamp((k - 0.78) / 0.14)
    if u > 0:
        yb = y0 + top[4] + 126
        c.drawLine(x0, yb, x0, lerp(yb, BAR_Y, u), p)
    u = in_out_sine(clamp((k - 0.9) / 0.2))
    if u > 0:
        xs = [m[3][0] for m in TEAM[1:]]
        c.drawLine(lerp(x0, min(xs), u), BAR_Y, lerp(x0, max(xs), u), BAR_Y, p)
        for key, name, role, (x, y), r, col, t0 in TEAM[1:]:
            v = clamp((k - t0 + 0.06) / 0.1)
            if v > 0:
                c.drawLine(x, BAR_Y, x, lerp(BAR_Y, y - r - 14, v), p)


def team(c, t):
    push = 1 + 0.035 * in_out_sine(clamp((t - T_TEAM - 2.0) / 1.6))
    with G.xf(c, CX, 540, s=push):
        c.translate(-CX, -540)
        lines(c, t)
        draw_chain(c, t, CHAIN, until=T_WORLD)
        for j, (key, name, role, (x, y), r, col, t0) in enumerate(TEAM):
            u = clamp((t - T_TEAM - t0) / 0.3)
            s = out_back(u, 2.0) if u < 1 else 1.0
            gone = clamp((t - (OUT + 0.06 * (3 - j))) / 0.22)
            s *= 1 - in_back(gone, 2.0) if gone > 0 else 1.0
            if u > 0 and u < 1:
                v = u
                c.drawCircle(x, y, r + 12 + 90 * v, G.P(col, 0.7 * (1 - v), stroke=5 * (1 - v) + 1))
            portrait(c, key, name, x, y, r, max(s, 0.0), col)
            wn, bn, wr, br, _ = LABELS[j]
            draw_word(c, wn, t, bn, col)
            draw_word(c, wr, t, br, col)
