"""INTERFACE building blocks: two themes, cached fonts, cards, icons and controls."""
import math
from dataclasses import dataclass
from functools import lru_cache

import skia

from engine import gfx as G
from engine.core import clamp, lerp, spring

CLAY = "#d97757"


@dataclass(frozen=True)
class Theme:
    name: str
    bg0: str        # backdrop, edges
    bg1: str        # backdrop, centre glow
    card: str
    ink: str        # text and primary buttons
    on_ink: str     # text on a primary button
    sub: str        # secondary text
    faint: str      # placeholders
    line: str       # hairlines, tracks
    soft: str       # chips, hovers, secondary fills
    dot: str        # the board's dot grid
    shadow: float   # drop-shadow strength
    rim: float      # hairline around cards (dark mode needs one, shadows vanish on black)


LIGHT = Theme("light", bg0="#e6e5e1", bg1="#f6f5f2", card="#ffffff", ink="#0e0e10", on_ink="#ffffff",
              sub="#7a7872", faint="#b3b0a9", line="#e4e2dd", soft="#f1f0ec", dot="#0e0e10", shadow=1.0, rim=0.0)
DARK = Theme("dark", bg0="#08080a", bg1="#15151a", card="#17171b", ink="#f2f1ed", on_ink="#0e0e10",
             sub="#8e8c86", faint="#56554f", line="#2b2b31", soft="#222227", dot="#f2f1ed", shadow=2.4, rim=0.09)

# code colours, on the code block's own dark ground in both themes
CODE_BG = "#141417"
CODE_BAR = "#1c1c20"
SYN = dict(plain="#e7e5df", kw="#e0875f", fn="#8ab4f8", num="#e5c07b", com="#6f6e76", pun="#a9a7a1")


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def T(c, s, x, y, font, col, a=1.0, align=0.0, tracking=0.0, tnum=False):
    return G.text(c, s, x, y, font, G.P(col, a), align=align, tracking=tracking,
                  features={"tnum": True} if tnum else None)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def panel(c, th, x, y, w, h, r=32, color=None, a=1.0, lift=1.0):
    """A card: soft drop shadow, a contact shadow, the face, and a hairline in dark mode."""
    color = color or th.card
    if lift > 0 and a > 0:
        c.drawRRect(rr(x, y + 18 * lift, w, h, r), G.P("#000000", min(1.0, 0.10 * th.shadow) * a * lift, blur=26 * lift))
        c.drawRRect(rr(x, y + 2, w, h, r), G.P("#000000", min(1.0, 0.06 * th.shadow) * a, blur=3))
    c.drawRRect(rr(x, y, w, h, r), G.P(color, a))
    if th.rim > 0:
        c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, r), G.P("#ffffff", th.rim * a, stroke=1.2))


def tag(c, th, s, x, y, a=1.0, align=0.0):
    """Mono caps label, the board's frame names and small headings."""
    T(c, s, x, y, F("mono", 16, wght=650), th.sub, a=a, align=align, tracking=0.24)


def press_of(t, times, tau=0.07):
    p = 0.0
    for tc in times:
        if t >= tc:
            p = max(p, math.exp(-(t - tc) / tau))
    return p


def pop(t, t0, freq=2.6, damping=0.5):
    """0 before t0, then a spring that overshoots to 1."""
    return spring(t - t0, freq, damping) if t >= t0 else 0.0


# ---------------------------------------------------------------- icons

def icon_play(c, x, y, s, col, a=1.0):
    c.drawPath(G.poly([(x - s * 0.35, y - s * 0.5), (x + s * 0.55, y), (x - s * 0.35, y + s * 0.5)]), G.P(col, a))


def icon_pause(c, x, y, s, col, a=1.0):
    for dx in (-0.28, 0.28):
        c.drawRRect(rr(x + dx * s - s * 0.13, y - s * 0.46, s * 0.26, s * 0.92, s * 0.06), G.P(col, a))


def icon_check(c, x, y, s, col, p=1.0, width=None, a=1.0):
    path = G.poly([(x - s * 0.42, y + s * 0.02), (x - s * 0.12, y + s * 0.32), (x + s * 0.45, y - s * 0.3)], closed=False)
    c.drawPath(path, G.P(col, a, stroke=width or s * 0.16, cap="round", join="round", effect=G.trim(0, p)))


def icon_search(c, x, y, s, col):
    G.circle(c, x - s * 0.1, y - s * 0.1, s * 0.34, G.P(col, 1, stroke=s * 0.11))
    c.drawLine(x + s * 0.15, y + s * 0.15, x + s * 0.45, y + s * 0.45, G.P(col, 1, stroke=s * 0.11, cap="round"))


def icon_arrow_up(c, x, y, s, col, a=1.0):
    p = G.P(col, a, stroke=s * 0.14, cap="round", join="round")
    c.drawLine(x, y + s * 0.42, x, y - s * 0.4, p)
    c.drawPath(G.poly([(x - s * 0.36, y - s * 0.04), (x, y - s * 0.42), (x + s * 0.36, y - s * 0.04)], closed=False), p)


def icon_chevron(c, x, y, s, col, rot=0.0, a=1.0):
    with G.xf(c, x, y, rot=rot):
        c.drawPath(G.poly([(-s * 0.4, -s * 0.2), (0, s * 0.2), (s * 0.4, -s * 0.2)], closed=False),
                   G.P(col, a, stroke=s * 0.16, cap="round", join="round"))


def icon_film(c, x, y, s, col, a=1.0):
    c.drawRRect(rr(x - s * 0.5, y - s * 0.36, s, s * 0.72, s * 0.12), G.P(col, a, stroke=s * 0.1))
    for k in range(3):
        for sy in (-0.24, 0.24):
            c.drawRect(skia.Rect.MakeXYWH(x - s * 0.34 + k * s * 0.28, y + sy * s - s * 0.04, s * 0.12, s * 0.08), G.P(col, a))


def icon_copy(c, x, y, s, col, a=1.0):
    c.drawRRect(rr(x - s * 0.3, y - s * 0.4, s * 0.62, s * 0.7, s * 0.1), G.P(col, a, stroke=s * 0.1))
    c.drawRRect(rr(x - s * 0.08, y - s * 0.18, s * 0.62, s * 0.7, s * 0.1), G.P(col, a, stroke=s * 0.1))


# ---------------------------------------------------------------- controls

def toggle(c, th, x, y, s):
    """A switch; s is the knob position 0 -> 1 (a spring value may overshoot)."""
    w, h = 92, 52
    bg = G.mixc(th.line, th.ink, clamp(s))
    c.drawRRect(rr(x - w / 2, y - h / 2, w, h, h / 2), G.P(bg))
    kx = lerp(x - w / 2 + h / 2, x + w / 2 - h / 2, s)
    c.drawCircle(kx, y + 1.5, 21, G.P("#000000", 0.18, blur=2.5))
    knob = "#ffffff" if th.name == "light" else G.mixc("#3a3a40", th.on_ink, clamp(s))
    G.circle(c, kx, y, 21, G.P(knob))


def roll_text(c, a_str, b_str, u, x, y, font, col, a=1.0, align=0.0, h=None):
    """a_str rolls up and out while b_str rolls in from below."""
    h = h or font.size * 1.3
    e = u if u <= 0 or u >= 1 else 1 - (1 - u) ** 3
    if e < 1:
        T(c, a_str, x, y - h * e, font, col, a=a * (1 - e), align=align)
    if e > 0:
        T(c, b_str, x, y + h * (1 - e), font, col, a=a * e, align=align)


def roll_number(c, a_str, b_str, u, x, y, font, col, stagger=0.06, a=1.0):
    """Digits roll from a_str to b_str; each changed digit slides up out of a clip."""
    run = font.shape(b_str, features={"tnum": True})
    runa = font.shape(a_str, features={"tnum": True})
    hgt = font.cap * 1.5
    for i, (gid, gx, adv) in enumerate(zip(run.gids, run.xs, run.adv)):
        ca = a_str[i] if i < len(a_str) else " "
        cb = b_str[i]
        e = clamp((u - i * stagger) / 0.5)
        e = 1 - (1 - e) ** 3
        with G.clip_rect(c, x + gx - 4, y - font.cap - 30, adv + 8, font.cap + 60):
            if ca == cb or e >= 1 or i >= len(runa.gids):
                G.glyph(c, font, gid, x + gx, y, G.P(col, a))
            else:
                G.glyph(c, font, runa.gids[i], x + gx, y - hgt * e, G.P(col, a))
                G.glyph(c, font, gid, x + gx, y + hgt * (1 - e), G.P(col, a))
    return run.width
