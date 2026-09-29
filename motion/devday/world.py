"""DevDay 2026: developers from 78 countries. A crowd of exactly 78 of the teaser's faces (thirteen across, six
deep) pops in on the right, one after another, while the number beside them counts up with them; when the last
one lands, the 78 flashes its points. The crowd looks over at it, bobs with the beat, cheers when the bass comes
back, and folds away into points as the 78 flies into the first launch's title."""
import math

from engine import gfx as G
from engine.core import clamp, out_back, in_back, hash01
from .look import WHITE, DIM, ORANGE, PURPLE, GREY, GREEN, BLUE, DARK, MONO, DISPLAY, F, SANS
from .faces import face
from .type import word, draw_word, Build
from .score import T_WORLD, T_LIST

COLS, ROWS = 13, 6
AREA = (830.0, 250.0, 1000.0, 580.0)           # where the crowd stands, on the right
T_COUNT0 = T_WORLD + 0.12                      # the first face pops in...
T_DONE = T_WORLD + 1.48                        # ...and the 78th
T_PULSE = T_WORLD + 2.76                       # the bass comes back: they cheer
T_SHUT = T_LIST - 0.38                         # they fold away

LABEL = word((("DEVELOPERS FROM", DIM),), 32, 150, 318, align=0.0, fam=MONO, axes=(("wght", 500),), tracking=0.14)
W78 = word((("78", WHITE),), 440, 132, 690, align=0.0, axes=DISPLAY)
COUNTRIES = word((("countries", WHITE),), 108, 146, 806, align=0.0)
B_LABEL = Build(T_WORLD + 0.1, spread=0.3, outline=0.03, fill=0.1, dots_off=0.18, t_out=T_SHUT, vanish=0.14)
B78 = Build(T_DONE, spread=0.0, outline=0.0, fill=0.0, dots_off=0.26, pop=0.05)
B_COUNTRIES = Build(T_DONE + 0.05, spread=0.3, outline=0.03, fill=0.1, dots_off=0.18, t_out=T_SHUT + 0.04,
                    vanish=0.14)

EYES = [("o", "o"), ("^", "^"), ("*", "*"), ("-", "-"), ("+", "+"), (">", "<"), ("n", "n")]
COLOURS = [PURPLE, ORANGE, GREY, GREEN, BLUE, PURPLE, ORANGE, GREEN, BLUE, DARK]


def _crowd():
    """Seventy-eight faces: where each stands, how big, its colour and eyes, and when it pops in."""
    x0, y0, w, h = AREA
    cw, ch = w / COLS, h / ROWS
    people = []
    for row in range(ROWS):
        for col in range(COLS):
            n = row * COLS + col
            x = x0 + cw * (col + 0.5 + (0.25 if row % 2 else -0.25)) + (hash01(n, 1) - 0.5) * 10
            y = y0 + ch * (row + 0.5) + (hash01(n, 2) - 0.5) * 12
            r = 30 + 7 * hash01(n, 3)
            col_ = COLOURS[int(hash01(n, 4) * len(COLOURS)) % len(COLOURS)]
            eyes = EYES[int(hash01(n, 5) * len(EYES)) % len(EYES)]
            order = col + 0.6 * row + 2.2 * hash01(n, 6)
            people.append([x, y, r, col_, eyes, order, n])
    people.sort(key=lambda p: p[5])
    for k, p in enumerate(people):
        p[5] = T_COUNT0 + (T_DONE - T_COUNT0) * k / (len(people) - 1)
    return people


CROWD = _crowd()


def crowd(c, t):
    for x, y, r, col, eyes, t0, n in CROWD:
        u = clamp((t - t0) / 0.18)
        if u <= 0:
            continue
        s = out_back(u, 2.4) if u < 1 else 1.0
        gone = clamp((t - (T_SHUT + 0.2 * (x - AREA[0]) / AREA[2])) / 0.16)
        if gone > 0:
            s *= 1 - in_back(gone, 2.0)
        if s <= 0.01:
            continue
        ph = hash01(n, 7)
        bob = 3 * math.sin(2 * math.pi * (2 * (t - T_WORLD) + ph))
        wave = clamp((t - T_PULSE - 0.18 * (x - AREA[0]) / AREA[2]) / 0.22)
        hop = -34 * math.sin(math.pi * wave) if 0 < wave < 1 else 0.0
        cheer = t >= T_PULSE + 0.18 * (x - AREA[0]) / AREA[2]
        face(c, x, y + bob + hop, r * s, col, ("^", "^") if cheer else eyes,
             yaw=0.0 if cheer else -0.3 - 0.15 * ph, pitch=0.06, roll=10 * (ph - 0.5))


def counter(c, t):
    """The number counting up with the crowd, until the 78th lands."""
    if t < T_COUNT0 or t >= T_DONE:
        return
    n = sum(1 for p in CROWD if t >= p[5])
    G.text(c, f"{max(1, min(n, 78))}", W78.x0, W78.y, F(SANS, 440, wght=600), G.P(WHITE))


def world(c, t, with_78=True):
    crowd(c, t)
    draw_word(c, LABEL, t, B_LABEL, ORANGE)
    if with_78:
        counter(c, t)
        draw_word(c, W78, t, B78, ORANGE)
    draw_word(c, COUNTRIES, t, B_COUNTRIES, ORANGE)
