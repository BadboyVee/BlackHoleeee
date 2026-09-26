"""INTERFACE: a square UI reel. A camera travels a board of components while Fable 5.1 streams its answer,
the board goes dark with one click, tilts back into an overview of everything the cursor touched, and ships."""
import math
import os
from functools import lru_cache

import numpy as np
import skia

from .score import *   # noqa: F401,F403 - the timing sheet is the vocabulary of this file
from engine import gfx as G   # after the star import: the sheet's musical grid is also called G
from engine import logos as LG
from engine.core import clamp, lerp, snap, whip, out_cubic, in_out_cubic, in_out_sine, spring, noise1, bezier
from engine.render import Film
from . import stream as S
from .ui import (LIGHT, DARK, CLAY, F, T, rr, panel, tag, press_of, pop, icon_play, icon_pause, icon_check,
                 icon_search, icon_arrow_up, toggle, roll_text, roll_number)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")

# ---------------------------------------------------------------- the board (board px; 1 px on screen at zoom 1)
SEG_W = 290
PICK_X0, PICK_Y0, PICK_H = 720 - 1.5 * SEG_W, 278, 104
PICK_CENTERS = [PICK_X0 + SEG_W * (k + 0.5) for k in range(3)]
MODELS = [("Astra 6", "openai"), ("Gemini 3.8", "gemini"), ("Fable 5.1", "claude")]
MCARD = (395, 434, 650, 262)
COMPOSER = (140, 820, 1160, 440)
PLAYER = (1740, 2000, 1160, 900)
SETTINGS = (1870, 3040, 900, 700)
STATS = (3420, 2980, 1000, 720)
PALETTE = (3470, 3860, 900, 540)
METER = (1870, 300, 900, 400)
TIMELINE = (1740, 820, 1160, 540)
ROSTER = (1740, 1480, 1160, 400)
SWATCHES = (3470, 300, 900, 420)
TYPE_CARD = (3470, 860, 900, 520)
QUEUE = (3420, 1500, 1000, 560)
ACTIVITY = (3420, 2180, 1000, 640)
BOARD_MID = (2280, 2340)

SEND_C = (COMPOSER[0] + COMPOSER[2] - 86, COMPOSER[1] + COMPOSER[3] - 82)
VIDEO = (PLAYER[0] + 40, PLAYER[1] + 40, 1080, 607.5)
SCRUB = (PLAYER[0] + 96, PLAYER[0] + PLAYER[2] - 44, PLAYER[1] + 776)
TOGGLE_X = SETTINGS[0] + SETTINGS[2] - 90
ROW_Y = [SETTINGS[1] + 176, SETTINGS[1] + 276, SETTINGS[1] + 376]
SLIDE = (SETTINGS[0] + 60, SETTINGS[0] + SETTINGS[2] - 60, SETTINGS[1] + 560)
SEG3 = (STATS[0] + 50, STATS[1] + 50, 660, 68)
CHART = (STATS[0] + 50, STATS[0] + STATS[2] - 50, STATS[1] + 450, STATS[1] + STATS[3] - 50)

FILM_LEN = 26.4
CHAPTERS = [(0.0, "COLD OPEN"), (3.2, "ASTRA 6"), (8.0, "GEMINI 3.8"), (12.8, "FABLE 5.1"), (17.6, "THE CLASH"),
            (20.8, "FINALE")]


def theme_at(t):
    return LIGHT if t < T_WIPE else DARK


# ---------------------------------------------------------------- camera

D_FOCAL = 1700.0
CAM_WHIP = bezier(0.7, 0.0, 0.2, 1.0)    # softer than the UI's whip: a camera this fast needs its blur to read
SHOT_PICKER = (720, 500, 1.22)
SHOT_COMPOSER = (720, 1046, 1.12)
SHOT_PLAYER = (2320, 2452, 1.10)
SHOT_SETTINGS = (2320, 3392, 1.24)
SHOT_STATS = (3920, 3342, 1.14)
SHOT_OVER_A = (2450, 2250, 0.350, -27.0, 52.0)
SHOT_OVER_B = (2520, 2180, 0.380, -21.0, 55.0)
SHOT_PALETTE = (3920, 4130, 1.22)


def _shot(s):
    return (float(s[0]), float(s[1]), float(s[2]), float(s[3]) if len(s) > 3 else 0.0,
            float(s[4]) if len(s) > 4 else 0.0)


def _mix(a, b, e):
    z = math.exp(lerp(math.log(a[2]), math.log(b[2]), e))     # zoom in log space: an even-feeling zoom
    return (lerp(a[0], b[0], e), lerp(a[1], b[1], e), z, lerp(a[3], b[3], e), lerp(a[4], b[4], e))


def _follow_target(t):
    return S.head_y(t) - 400.0


_FOLLOW_TS = np.arange(T_RESP, T_TO_PLAYER + 0.02, 0.02)
_FOLLOW_CY = np.maximum.accumulate([_follow_target(x) for x in _FOLLOW_TS])


def follow(t):
    """While Fable streams, keep its newest line in the lower third. The camera never scrolls back up,
    not even when the thinking block folds away."""
    cy = float(np.interp(t, _FOLLOW_TS, _FOLLOW_CY))
    return (720.0, max(1130.0, cy), 1.0, 0.0, 0.0)


def _move(t, t0, dur, a, b, ease=CAM_WHIP, roll=0.0):
    u = clamp((t - t0) / dur)
    v = _mix(a, b, ease(u))
    return (v[0], v[1], v[2], v[3] + roll * math.sin(math.pi * u), v[4])


def cam(t):
    """(cx, cy, zoom, rot, tilt) of the camera over the board."""
    pk, cp, pl = _shot(SHOT_PICKER), _shot(SHOT_COMPOSER), _shot(SHOT_PLAYER)
    se, sa, pa = _shot(SHOT_SETTINGS), _shot(SHOT_STATS), _shot(SHOT_PALETTE)
    oa, ob = _shot(SHOT_OVER_A), _shot(SHOT_OVER_B)
    if t < T_TO_COMPOSER:
        u = in_out_sine(clamp(t / T_TO_COMPOSER))
        return (pk[0], pk[1] - 12 * u, pk[2] * (0.985 + 0.03 * u), 0.0, 0.0)
    pk_end = (pk[0], pk[1] - 12, pk[2] * 1.015, 0.0, 0.0)
    if t < 3.8:
        cp_d = (cp[0], cp[1], cp[2] * (1 + 0.02 * clamp((t - 2.4) / 1.4)), 0.0, 0.0)
        return _move(t, T_TO_COMPOSER, 0.38, pk_end, cp_d, roll=2.5)
    cp_end = (cp[0], cp[1], cp[2] * 1.02, 0.0, 0.0)
    if t < T_TO_PLAYER:
        f = follow(t)
        if t < 4.4:
            return _mix(cp_end, f, in_out_cubic(clamp((t - 3.8) / 0.6)))
        return f
    if t < T_TO_SETTINGS:
        pl_d = (pl[0], pl[1] - 10 * clamp((t - 11.0) / 2.2), pl[2] * (1 + 0.025 * clamp((t - 11.0) / 2.2)), 0.0, 0.0)
        return _move(t, T_TO_PLAYER, 0.38, follow(T_TO_PLAYER), pl_d, roll=-3.5)
    pl_end = (pl[0], pl[1] - 10, pl[2] * 1.025, 0.0, 0.0)
    if t < T_TO_STATS:
        return _move(t, T_TO_SETTINGS, 0.36, pl_end, se, roll=3.0)
    if t < T_OVER:
        return _move(t, T_TO_STATS, 0.36, se, sa, roll=-3.0)
    if t < T_OVER + 0.9:
        return _move(t, T_OVER, 0.9, sa, oa, ease=snap)
    if t < T_FLY:
        return _mix(oa, ob, in_out_sine(clamp((t - T_OVER - 0.9) / (T_FLY - T_OVER - 0.9))))
    if t < T_ENTER:
        return _move(t, T_FLY, 0.54, ob, pa)
    e = in_out_sine(clamp((t - T_ENTER) / (DURATION - T_ENTER)))
    return (pa[0], pa[1] + 30 * e, pa[2] * (1 + 0.09 * e), 0.0, 0.0)


def homography(tilt, rot):
    """Plane coordinates (centred on the camera target) to the screen, with the board tilted back by `tilt`."""
    a, b = math.radians(-tilt), math.radians(rot)
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    R = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]]) @ np.array([[cb, -sb, 0], [sb, cb, 0], [0, 0, 1]])
    K = np.array([[D_FOCAL, 0, CX], [0, D_FOCAL, CY], [0, 0, 1.0]])
    Hm = K @ np.column_stack([R[:, 0], R[:, 1], [0, 0, D_FOCAL]])
    Hm /= Hm[2, 2]
    return skia.Matrix.MakeAll(*[float(v) for v in Hm.ravel()])


IMPACTS = [(T_WIPE, 13.0), (T_OVER, 11.0), (T_ENTER, 8.0)]


def shake(t):
    amp = 0.0
    for t0, a in IMPACTS:
        if 0 <= t - t0 < 0.6:
            amp += a * math.exp(-(t - t0) / 0.11)
    return amp * noise1(t * 36, 3.1), amp * noise1(t * 36, 7.7)


def cam_matrix(t):
    cx, cy, z, rot, tilt = cam(t)
    m = homography(tilt, rot)
    m.preScale(z, z)
    m.preTranslate(-cx, -cy)
    sx, sy = shake(t)
    m.postTranslate(sx, sy)
    return m


def to_screen(t, x, y):
    p = cam_matrix(t).mapXY(x, y)
    return p.fX, p.fY


def visible_rect(m):
    """Board-space bounding box of what the camera sees."""
    inv = skia.Matrix()
    if not m.invert(inv):
        return (-1e9, -1e9, 1e9, 1e9)
    pts = [inv.mapXY(x, y) for x in (0, SIZE[0] / 2, SIZE[0]) for y in (0, SIZE[1] / 2, SIZE[1])]
    xs, ys = [p.fX for p in pts], [p.fY for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def seen(vis, r, margin=80):
    x, y, w, h = r
    return not (x + w < vis[0] - margin or x > vis[2] + margin or y + h < vis[1] - margin or y > vis[3] + margin)


# ---------------------------------------------------------------- backdrop and board furniture

def backdrop(c, th):
    c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(th.bg0))
    c.drawCircle(CX, 560, 1250, G.P(th.bg1, 1, shader=G.radial_grad(CX, 560, 1250, [th.bg1, th.bg0])))


def board_grid(c, th, vis, zoom):
    """Dots like a design canvas; they fade to a coarse line grid when the camera pulls back."""
    x0, y0, x1, y1 = max(vis[0], -600), max(vis[1], -600), min(vis[2], 5200), min(vis[3], 5200)
    dot_a = clamp((zoom - 0.5) / 0.3)
    if dot_a > 0:
        step = 44
        xs = np.arange(math.floor(x0 / step) * step, x1 + step, step)
        ys = np.arange(math.floor(y0 / step) * step, y1 + step, step)
        if len(xs) * len(ys) < 60000:
            gx, gy = np.meshgrid(xs, ys)
            pts = [skia.Point(float(a), float(b)) for a, b in zip(gx.ravel(), gy.ravel())]
            p = G.P(th.dot, (0.13 if th.name == "light" else 0.10) * dot_a, stroke=3.4, cap="round")
            c.drawPoints(skia.Canvas.kPoints_PointMode, pts, p)
    line_a = clamp((0.75 - zoom) / 0.3)
    if line_a > 0:
        step = 176
        p = G.P(th.dot, 0.07 * line_a, stroke=2.5)
        for x in np.arange(math.floor(x0 / step) * step, x1 + step, step):
            c.drawLine(float(x), y0, float(x), y1, p)
        for y in np.arange(math.floor(y0 / step) * step, y1 + step, step):
            c.drawLine(x0, float(y), x1, float(y), p)


def frame_label(c, th, num, name, x, y, a=1.0):
    tag(c, th, f"{num}   {name}", x, y - 24, a=a * 0.9)


# ---------------------------------------------------------------- 1 model picker + model card

def pick_pos(t):
    p = PICK_CENTERS[0]
    for k, tc in enumerate(T_PICK):
        if t >= tc:
            p += (PICK_CENTERS[k + 1] - PICK_CENTERS[k]) * spring(t - tc, 2.3, 0.52)
    return p


def picker(c, th, t):
    u = clamp((t - T_PICKER_IN) / 0.4)
    if u <= 0:
        return
    e = snap(u)
    with G.layer(c, alpha=u, blur=14 * (1 - e) if e < 0.97 else 0.0):
        with G.xf(c, 720, PICK_Y0 + PICK_H / 2, s=0.93 + 0.07 * e):
            c.translate(-720, -(PICK_Y0 + PICK_H / 2))
            _picker(c, th, t)


def _picker(c, th, t):
    y0, h = PICK_Y0, PICK_H
    panel(c, th, PICK_X0 - 10, y0 - 10, 3 * SEG_W + 20, h + 20, r=62)
    pos = pick_pos(t)
    vel = (pick_pos(t + 0.008) - pick_pos(t - 0.008)) / 0.016
    stretch = 1 + min(0.45, abs(vel) / 2600)
    for k, tc in enumerate(T_PICK):
        hover = clamp((t - (tc - 0.3)) / 0.15) * (1 - clamp((t - tc) / 0.1))
        if hover > 0:
            c.drawRRect(rr(PICK_CENTERS[k + 1] - 132, y0 + 8, 264, h - 16, 44), G.P(th.soft, hover))
    sw = 264 * stretch
    c.save()
    c.clipRRect(rr(PICK_X0, y0, 3 * SEG_W, h, 52), skia.ClipOp.kIntersect, True)
    c.drawRRect(rr(pos - sw / 2, y0 + 8, sw, h - 16, 44), G.P(th.ink))
    c.restore()
    f = F("inter", 31, wght=600, opsz=32)
    cy = y0 + h / 2
    for k, (label, logo) in enumerate(MODELS):
        cov = clamp(1 - abs(pos - PICK_CENTERS[k]) / 150)
        col = G.mixc(th.ink, th.on_ink, cov)
        lw = f.width(label)
        x = PICK_CENTERS[k] - (lw + 50) / 2
        if logo == "openai":
            LG.mark(c, "openai", x + 17, cy, 34, G.P(col))
        elif logo == "gemini":
            LG.gemini(c, x + 17, cy, 34)
        else:
            spin = 180 * clamp((t - T_PICK[1]) / 0.6) if t >= T_PICK[1] else 0.0
            LG.claude(c, x + 17, cy, 38, CLAY, 1.0, 1.0, rot=spin)
        G.text(c, label, x + 50, cy + 11, f, G.P(col))
    tag(c, th, "3 AVAILABLE", PICK_X0 + 3 * SEG_W, y0 - 34, align=1.0)


def model_card(c, th, t):
    if t < T_CARD:
        return
    s = pop(t, T_CARD, 2.5, 0.5)
    a = clamp((t - T_CARD) / 0.16)
    x, y, w, h = MCARD
    with G.layer(c, alpha=a):
        with G.xf(c, x + w / 2, y, s=0.9 + 0.1 * s):
            c.translate(-(x + w / 2), -y + (1 - s) * -24)
            panel(c, th, x, y, w, h, r=30, lift=0.8)
            LG.claude(c, x + 62, y + 70, 56, CLAY, 1.0, 1.0, rot=40 * s)
            T(c, "Fable 5.1", x + 112, y + 68, F("inter", 36, wght=660, opsz=32), th.ink)
            T(c, "Anthropic  ·  selected", x + 112, y + 102, F("inter", 22, wght=460, opsz=24), th.sub)
            badge = "MAX EFFORT"
            fb = F("mono", 14, wght=700)
            bw = fb.width(badge, 0.2) + 28
            c.drawRRect(rr(x + w - 40 - bw, y + 44, bw, 34, 17), G.P(CLAY, 0.14))
            T(c, badge, x + w - 40 - bw / 2, y + 66, fb, CLAY, align=0.5, tracking=0.2)
            c.drawLine(x + 40, y + 142, x + w - 40, y + 142, G.P(th.line, 1, stroke=1.4))
            fl = F("mono", 14, wght=650)
            fv = F("inter", 27, wght=600, opsz=24)
            for k, (lab, val) in enumerate((("CONTEXT", "1M tokens"), ("THINKING", "extended"), ("OUTPUT", "code + film"))):
                cx = x + 40 + k * 200
                ak = clamp((t - T_CARD - 0.12 - 0.06 * k) / 0.2)
                T(c, lab, cx, y + 186, fl, th.sub, a=ak, tracking=0.22)
                T(c, val, cx, y + 224 + 10 * (1 - snap(ak)), fv, th.ink, a=ak)


# ---------------------------------------------------------------- 2 composer

def composer(c, th, t):
    x, y, w, h = COMPOSER
    focus = clamp((t - (T_TO_COMPOSER + 0.1)) / 0.3)
    panel(c, th, x, y, w, h, r=40, lift=0.6 + 0.4 * focus)
    tag(c, th, "NEW FILM", x + 52, y + 64)
    tag(c, th, "1 OF 3", x + w - 52, y + 64, align=1.0)
    f = F("inter", 44, wght=520, opsz=32)
    total = len(PROMPT[0]) + len(PROMPT[1])
    n = int(total * clamp((t - T_TYPE[0]) / (T_TYPE[1] - T_TYPE[0])))
    if n == 0:
        T(c, "Describe the film…", x + 52, y + 150, f, th.faint)
    l1 = PROMPT[0][:n]
    l2 = PROMPT[1][:max(0, n - len(PROMPT[0]))]
    T(c, l1, x + 52, y + 150, f, th.ink)
    T(c, l2, x + 52, y + 214, f, th.ink)
    line = 1 if n > len(PROMPT[0]) else 0
    cx_ = x + 52 + f.width([l1, l2][line]) + 4
    if t < T_SEND and (int(t * 2.4) % 2 == 0 or T_TYPE[0] <= t < T_TYPE[1] + 0.1):
        c.drawRect(skia.Rect.MakeXYWH(cx_, y + 112 + 64 * line, 3.5, 48), G.P(th.ink))
    fc = F("inter", 24, wght=560, opsz=24)
    chips = [("1920 × 1080", None), ("60 fps", None), ("Fable 5.1", "claude"), ("Effort · max", None)]
    chx = x + 52
    for k, ((label, logo), tc) in enumerate(zip(chips, T_CHIPS)):
        u = pop(t, tc, 2.6, 0.5)
        lw = fc.width(label) + (40 if logo else 0)
        cw = lw + 44
        if u > 0:
            with G.xf(c, chx + cw / 2, SEND_C[1], s=max(0.0, u)):
                c.drawRRect(rr(-cw / 2, -27, cw, 54, 27), G.P(th.soft))
                tx = -cw / 2 + 22
                if logo:
                    LG.claude(c, tx + 12, 0, 26, CLAY)
                    tx += 40
                T(c, label, tx, 9, fc, th.ink)
        chx += cw + 14
    # send: arrow, then a stop square while Fable works, then the arrow again
    pr = press_of(t, [T_SEND])
    busy = S.sending(t)
    ready = n >= total
    with G.xf(c, SEND_C[0], SEND_C[1], s=1 - 0.1 * pr):
        G.circle(c, 0, 0, 34, G.P(G.mixc(th.line, th.ink, 1.0 if ready else 0.0)))
        if busy > 0.5:
            c.drawRRect(rr(-10, -10, 20, 20, 4), G.P(th.on_ink))
            ring = G.arc_path(0, 0, 40, (t - T_SEND) * 400, 90)
            c.drawPath(ring, G.P(CLAY, 1, stroke=4, cap="round"))
        else:
            icon_arrow_up(c, 0, 0, 30, th.on_ink if ready else th.sub)


# ---------------------------------------------------------------- 4 player

@lru_cache(maxsize=4)
def levels(key):
    p = os.path.join(OUT, f"{key}_levels.npz")
    if os.path.exists(p):
        d = np.load(p)
        return d["rms"], d["levels"]
    n = int(60 * 26.4)
    rms = np.abs(np.sin(np.linspace(0, 30, n))) * 0.8 + 0.1
    return rms, np.tile(rms[:, None], (1, 10))


def playhead(t):
    """Seconds into THE FRONTIER that the player shows."""
    if t < T_PLAY:
        return FILM_AT_PLAY
    if t < T_GRAB:
        return FILM_AT_PLAY + (t - T_PLAY)
    p0 = FILM_AT_PLAY + (T_GRAB - T_PLAY)
    if t < T_DROP:
        return lerp(p0, FILM_AT_DROP, in_out_cubic((t - T_GRAB) / (T_DROP - T_GRAB)))
    return min(FILM_LEN - 0.05, FILM_AT_DROP + (t - T_DROP))


def scrub_x(ph):
    x0, x1, _ = SCRUB
    return x0 + (x1 - x0) * ph / FILM_LEN


def chapter(ph):
    name = CHAPTERS[0][1]
    for t0, nm in CHAPTERS:
        if ph >= t0:
            name = nm
    return name


def player(c, th, t):
    x, y, w, h = PLAYER
    panel(c, th, x, y, w, h, r=44, color=G.mixc(th.card, "#000000", 0.0))
    vx, vy, vw, vh = VIDEO
    ph = playhead(t)
    c.save()
    c.clipRRect(rr(vx, vy, vw, vh, 26), skia.ClipOp.kIntersect, True)
    img = S.film_image(S.frame_index(ph))
    if img is not None:
        G.draw_image(c, img, vx, vy, vw, vh)
    else:
        c.drawRect(skia.Rect.MakeXYWH(vx, vy, vw, vh), G.P("#1e1e22"))
    # paused: a scrim and a big play button that is pressed away
    pa = 1 - clamp((t - T_PLAY - 0.05) / 0.3)
    if pa > 0:
        c.drawRect(skia.Rect.MakeXYWH(vx, vy, vw, vh), G.P("#000000", 0.38 * pa))
        pr = press_of(t, [T_PLAY])
        hov = clamp((t - (T_PLAY - 0.2)) / 0.12)
        with G.xf(c, vx + vw / 2, vy + vh / 2, s=(1 + 0.08 * hov - 0.1 * pr) * (1 + 0.3 * (1 - pa))):
            G.circle(c, 0, 0, 58, G.P("#ffffff", 0.94 * pa))
            icon_play(c, 5, 0, 44, "#0e0e10", a=pa)
    # chapter badge
    name = chapter(ph)
    fb = F("mono", 16, wght=700)
    bw = fb.width(name, 0.2) + 34
    c.drawRRect(rr(vx + 24, vy + 24, bw, 40, 20), G.P("#000000", 0.55))
    T(c, name, vx + 24 + bw / 2, vy + 50, fb, "#ffffff", align=0.5, tracking=0.2)
    c.restore()
    c.drawRRect(rr(vx + 0.5, vy + 0.5, vw - 1, vh - 1, 26), G.P("#ffffff", 0.08, stroke=1.2))
    # title row
    T(c, "the-frontier.mp4", vx, vy + vh + 66, F("inter", 34, wght=640, opsz=32), th.ink)
    T(c, "26.4 s  ·  1920 × 1080  ·  60 fps", vx + vw, vy + vh + 64, F("inter", 23, wght=480, opsz=24), th.sub,
      align=1.0)
    # waveform scrubber with chapter ticks
    rms, _ = levels("frontier")
    x0, x1, sy = SCRUB
    n = 84
    prog = ph / FILM_LEN
    for k in range(n):
        v = float(rms[int(k / n * (len(rms) - 1))])
        bh = 6 + 40 * v
        bx = x0 + (x1 - x0) * (k + 0.5) / n
        played = (k + 0.5) / n <= prog
        c.drawRRect(rr(bx - 2.3, sy - bh / 2, 4.6, bh, 2.3), G.P(th.ink if played else th.line))
    fm = F("mono", 13, wght=650)
    for t0, nm in CHAPTERS[1:]:
        cxk = scrub_x(t0)
        c.drawLine(cxk, sy - 38, cxk, sy - 28, G.P(th.sub, 0.8, stroke=1.4))
    # play / pause glyph
    if t < T_PLAY:
        icon_play(c, x0 - 44, sy, 22, th.ink)
    else:
        icon_pause(c, x0 - 46, sy, 22, th.ink)
    held = T_GRAB <= t <= T_DROP + 0.05
    hx = scrub_x(ph)
    G.circle(c, hx, sy, 12 + 4 * held, G.P(th.ink))
    G.circle(c, hx, sy, 5, G.P(th.card))
    if held:
        G.circle(c, hx, sy, 28, G.P(th.ink, 0.14))
        # a preview bubble above the handle while scrubbing
        u = clamp((t - T_GRAB) / 0.12) * (1 - clamp((t - T_DROP) / 0.12))
        if u > 0:
            pw, phh = 200, 112.5
            with G.xf(c, hx, sy - 150, s=0.8 + 0.2 * u):
                c.save()
                c.clipRRect(rr(-pw / 2, -phh / 2, pw, phh, 12), skia.ClipOp.kIntersect, True)
                im = S.film_thumb(S.frame_index(ph), pw, int(phh))
                if im is not None:
                    G.draw_image(c, im, -pw / 2, -phh / 2, pw, phh, alpha=u)
                c.restore()
                c.drawRRect(rr(-pw / 2, -phh / 2, pw, phh, 12), G.P("#ffffff", 0.9 * u, stroke=3))
                T(c, chapter(ph), 0, phh / 2 + 28, fm, th.ink, a=u, align=0.5, tracking=0.2)
    fmt = F("mono", 21, wght=500)
    cur = int(ph)
    T(c, f"0:{cur:02d}", x0, sy + 70, fmt, th.sub, tnum=True)
    T(c, f"-0:{max(0, int(FILM_LEN) - cur):02d}", x1, sy + 70, fmt, th.sub, align=1.0, tnum=True)


# ---------------------------------------------------------------- 5 settings

def slider_value(t):
    if t < T_SLIDE[0]:
        return 0.35
    return lerp(0.35, 1.0, in_out_cubic(clamp((t - T_SLIDE[0]) / (T_SLIDE[1] - T_SLIDE[0]))))


def _switch(t, tc, initially=False):
    if tc is None:
        return 1.0 if initially else 0.0
    return spring(t - tc, 2.8, 0.55) if t >= tc else 0.0


def settings(c, th, t):
    x, y, w, h = SETTINGS
    panel(c, th, x, y, w, h, r=40)
    T(c, "Render settings", x + 50, y + 80, F("inter", 36, wght=640, opsz=32), th.ink)
    tag(c, th, "THE FRONTIER", x + w - 50, y + 74, align=1.0)
    f = F("inter", 31, wght=520, opsz=32)
    fs = F("inter", 22, wght=450, opsz=24)
    rows = [("Motion blur", "12 sub-frames per frame", None, True),
            ("Film grain", "8 textures, one per frame", T_TOG[0], False),
            ("Dark mode", "for the 2 a.m. renders", T_TOG[1], False)]
    for (label, hint, tt, init), yy in zip(rows, ROW_Y):
        T(c, label, x + 50, yy + 2, f, th.ink)
        T(c, hint, x + 50, yy + 34, fs, th.sub)
        toggle(c, th, TOGGLE_X, yy, _switch(t, tt, init))
        c.drawLine(x + 50, yy + 60, x + w - 50, yy + 60, G.P(th.line, 1, stroke=1.4))
    v = slider_value(t)
    names = ["low", "medium", "high", "max"]
    name = names[min(3, int(v * 3.999))]
    T(c, "Effort", x + 50, SLIDE[2] - 44, f, th.ink)
    T(c, name, x + w - 50, SLIDE[2] - 44, F("inter", 31, wght=640, opsz=32), CLAY if name == "max" else th.ink,
      align=1.0)
    t0x, t1x, ty = SLIDE
    c.drawRRect(rr(t0x, ty - 5, t1x - t0x, 10, 5), G.P(th.line))
    kx = lerp(t0x, t1x, v)
    c.drawRRect(rr(t0x, ty - 5, kx - t0x, 10, 5), G.P(th.ink))
    held = T_SLIDE[0] <= t <= T_SLIDE[1]
    c.drawCircle(kx, ty + 2, 19, G.P("#000000", 0.2, blur=3))
    G.circle(c, kx, ty, 19 + 3 * held, G.P("#ffffff" if th.name == "light" else th.ink))
    G.circle(c, kx, ty, 19 + 3 * held, G.P(th.line, 1, stroke=1.5))
    fm = F("mono", 15, wght=600)
    for k, nm in enumerate(names):
        T(c, nm.upper(), lerp(t0x, t1x, k / 3), ty + 50, fm, th.sub, align=[0.0, 0.5, 0.5, 1.0][k], tracking=0.2)


# ---------------------------------------------------------------- 6 stats

FILMS = [dict(name="Frontier", frames=1584, secs="26.4 s", bpm="150 BPM", lufs="−10 LUFS", key="frontier", len=26.4),
         dict(name="Tribute", frames=1968, secs="32.8 s", bpm="120 BPM", lufs="−11 LUFS", key="dario", len=32.8),
         dict(name="Interface", frames=1500, secs="25.0 s", bpm="120 BPM", lufs="−11 LUFS", key="interface", len=25.0)]


@lru_cache(maxsize=4)
def envelope(key, n=90):
    rms, _ = levels(key)
    idx = np.linspace(0, len(rms) - 1, n).astype(int)
    v = np.convolve(rms, np.ones(40) / 40, mode="same")[idx]
    return v / (v.max() + 1e-9)


def stats_sel(t):
    s = 0.0
    for tc in T_SWITCH:
        if t >= tc:
            s += spring(t - tc, 2.4, 0.55)
    return s


def stats(c, th, t):
    x, y, w, h = STATS
    panel(c, th, x, y, w, h, r=44)
    sx, sy, sw, sh = SEG3
    c.drawRRect(rr(sx, sy, sw, sh, sh / 2), G.P(th.soft))
    u = stats_sel(t)
    seg = sw / 3
    selx = sx + 6 + seg * u
    c.drawRRect(rr(selx, sy + 8, seg - 12, sh - 16, (sh - 16) / 2), G.P("#000000", 0.08, blur=6))
    c.drawRRect(rr(selx, sy + 6, seg - 12, sh - 12, (sh - 12) / 2), G.P(th.card if th.name == "light" else "#2a2a30"))
    fseg = F("inter", 25, wght=600, opsz=24)
    for k, film in enumerate(FILMS):
        cov = clamp(1 - abs(u - k))
        T(c, film["name"], sx + seg * (k + 0.5), sy + sh / 2 + 9, fseg, G.mixc(th.sub, th.ink, cov), align=0.5)
    idx = min(2, int(round(u)))
    k0 = 0 if t < T_SWITCH[0] else (1 if t < T_SWITCH[1] else 2)
    kprev = max(0, k0 - 1)
    tsw = T_SWITCH[k0 - 1] if k0 > 0 else -9
    rollu = clamp((t - tsw - 0.05) / 0.6)
    fb = F("inter", 150, wght=640, opsz=32)
    a_s, b_s = f"{FILMS[kprev]['frames']:,}", f"{FILMS[k0]['frames']:,}"
    wnum = roll_number(c, a_s, b_s, rollu if k0 > 0 else 1.0, x + 46, y + 300, fb, th.ink)
    T(c, "frames", x + 46 + wnum + 18, y + 300, F("inter", 34, wght=500, opsz=32), th.sub)
    fv = F("inter", 32, wght=640, opsz=32)
    fl = F("mono", 15, wght=650)
    for j, (key, lab) in enumerate((("secs", "LENGTH"), ("bpm", "TEMPO"), ("lufs", "LOUDNESS"))):
        cx0 = x + 50 + j * 250
        v0, v1 = FILMS[kprev][key], FILMS[k0][key]
        e = snap(clamp((t - tsw - 0.1 - 0.06 * j) / 0.35)) if k0 > 0 else 1.0
        with G.clip_rect(c, cx0 - 4, y + 330, 240, 60):
            if v0 != v1:
                T(c, v0, cx0, y + 372 - 50 * e, fv, th.ink)
            T(c, v1, cx0, y + 372 + (50 * (1 - e) if v0 != v1 else 0), fv, th.ink)
        T(c, lab, cx0, y + 402, fl, th.sub, tracking=0.22)
    cx0, cx1, cy0, cy1 = CHART
    ea, eb = envelope(FILMS[kprev]["key"]), envelope(FILMS[k0]["key"])
    m = snap(rollu) if k0 > 0 else 1.0
    env = ea * (1 - m) + eb * m
    xs = np.linspace(cx0, cx1, len(env))
    ys = cy1 - (cy1 - cy0) * (0.08 + 0.85 * env)
    path = skia.Path()
    path.addPoly([skia.Point(float(a), float(b)) for a, b in zip(xs, ys)], False)
    area = skia.Path(path)
    area.lineTo(cx1, cy1)
    area.lineTo(cx0, cy1)
    area.close()
    accent = th.ink
    c.drawPath(area, G.P(accent, 1, shader=G.linear_grad(0, cy0, 0, cy1, [accent, accent], alphas=[0.12, 0.0])))
    c.drawPath(path, G.P(accent, 1, stroke=3.2, join="round"))
    c.drawLine(cx0, cy1, cx1, cy1, G.P(th.line, 1, stroke=1.5))
    hv = clamp((t - T_HOVER[0]) / 0.15) * (1 - clamp((t - T_HOVER[1]) / 0.15))
    if hv > 0:
        mx = lerp(cx0 + 0.52 * (cx1 - cx0), cx0 + 0.83 * (cx1 - cx0),
                  in_out_cubic(clamp((t - T_HOVER[0]) / (T_HOVER[1] - T_HOVER[0]))))
        k = int(np.clip((mx - cx0) / (cx1 - cx0) * (len(env) - 1), 0, len(env) - 1))
        px, py = xs[k], ys[k]
        c.drawLine(px, cy0, px, cy1, G.P(th.ink, 0.3 * hv, stroke=1.4, effect=G.dash(5, 6)))
        G.circle(c, px, py, 9 * hv, G.P(th.ink))
        G.circle(c, px, py, 5 * hv, G.P(th.card))
        secs = k / (len(env) - 1) * FILMS[k0]["len"]
        label = f"LOUDNESS  ·  0:{int(secs):02d}"
        fm = F("mono", 18, wght=650)
        lw = fm.width(label, 0.16) + 36
        c.drawRRect(rr(px - lw / 2, py - 74, lw, 46, 23), G.P(th.ink, hv))
        T(c, label, px, py - 43, fm, th.on_ink, a=hv, align=0.5, tracking=0.16)


def hover_point(t):
    """Board position of the chart point the cursor rides during the hover."""
    cx0, cx1, cy0, cy1 = CHART
    env = envelope("interface")
    mx = lerp(cx0 + 0.52 * (cx1 - cx0), cx0 + 0.83 * (cx1 - cx0), in_out_cubic(clamp((t - T_HOVER[0]) / (T_HOVER[1] - T_HOVER[0]))))
    k = int(np.clip((mx - cx0) / (cx1 - cx0) * (len(env) - 1), 0, len(env) - 1))
    return float(np.linspace(cx0, cx1, len(env))[k]), float(cy1 - (cy1 - cy0) * (0.08 + 0.85 * env[k]))


# ---------------------------------------------------------------- 8 command palette + end

RESULTS = [("Ship all three films", "⏎"), ("Export ProRes 4444", "⌘E"), ("Open the Blender plates", "⌘B")]


def palette(c, th, t):
    if t >= T_ENTER + 0.12:
        return
    x, y, w, h = PALETTE
    op = pop(t, T_CMDK, 2.6, 0.55) if t >= T_CMDK else 0.0
    if t < T_CMDK:
        # before ⌘K: a quiet placeholder card on the board
        panel(c, th, x, y, w, h, r=36, lift=0.4)
        icon_search(c, x + 60, y + 72, 34, th.faint)
        fp = F("inter", 38, wght=500, opsz=32)
        T(c, "Press", x + 104, y + 86, fp, th.faint)
        kx = x + 104 + fp.width("Press") + 16
        c.drawRRect(rr(kx, y + 50, 72, 46, 11), G.P(th.soft))
        c.drawRRect(rr(kx + 0.5, y + 50.5, 71, 45, 11), G.P(th.line, 1, stroke=1.2))
        T(c, "⌘K", kx + 36, y + 81, F("dejavu-sans-bold", 21), th.sub, align=0.5)
        return
    with G.xf(c, x + w / 2, y + h / 2, s=0.94 + 0.06 * op):
        c.translate(-(x + w / 2), -(y + h / 2))
        panel(c, th, x, y, w, h, r=36, lift=1.2)
        icon_search(c, x + 60, y + 72, 34, th.sub)
        n = sum(1 for k in T_KEYS if k <= t)
        f = F("inter", 38, wght=500, opsz=32)
        if n == 0:
            T(c, "Type a command", x + 104, y + 86, f, th.faint)
        else:
            T(c, "ship"[:n], x + 104, y + 86, f, th.ink)
        cxp = x + 104 + (f.width("ship"[:n]) if n else 0) + 3
        if int(t * 2.4) % 2 == 0 or (T_KEYS[0] <= t < T_KEYS[-1] + 0.2):
            c.drawRect(skia.Rect.MakeXYWH(cxp, y + 52, 3.5, 44), G.P(th.ink))
        c.drawRRect(rr(x + w - 110, y + 50, 64, 42, 10), G.P(th.soft))
        T(c, "⌘K", x + w - 78, y + 79, F("dejavu-sans-bold", 20), th.sub, align=0.5)
        c.drawLine(x, y + 130, x + w, y + 130, G.P(th.line, 1, stroke=1.5))
        fr = F("inter", 31, wght=520, opsz=32)
        fh = F("dejavu-sans-bold", 22)
        press = clamp((t - T_ENTER) / 0.06)
        for k, (label, hint) in enumerate(RESULTS):
            a = clamp((t - T_KEYS[0] - 0.05 - k * 0.06) / 0.2)
            if a <= 0:
                continue
            ry = y + 160 + k * 112
            sel = k == 0 and n >= 2
            if sel:
                c.drawRRect(rr(x + 20, ry, w - 40, 96, 22), G.P(G.mixc(th.soft, th.ink, press), a))
            col = G.mixc(th.ink, th.on_ink, press if sel else 0.0)
            c.drawRRect(rr(x + 44, ry + 24, 48, 48, 12), G.P(th.card if sel else th.soft, a))
            if k == 0:
                icon_play(c, x + 69, ry + 48, 22, th.ink, a=a)
            elif k == 1:
                c.drawRect(skia.Rect.MakeXYWH(x + 57, ry + 38, 24, 20), G.P(th.ink, a, stroke=3))
            else:
                LG.claude(c, x + 68, ry + 48, 28, CLAY, a)
            T(c, label, x + 116, ry + 60 + 12 * (1 - snap(a)), fr, col, a=a)
            T(c, hint, x + w - 50, ry + 58, fh, G.mixc(th.sub, th.on_ink, press if sel else 0.0), a=a, align=1.0)


def end(c, th, t):
    if t < END[0]:
        return
    px, py = PALETTE[0] + PALETTE[2] / 2, PALETTE[1] + PALETTE[3] / 2
    u = whip(clamp((t - END[0]) / 0.36))
    w, h = lerp(PALETTE[2] - 40, 640, u), lerp(96, 112, u)
    cy = lerp(PALETTE[1] + 160 + 48, py - 40, u)
    panel(c, th, px - w / 2, cy - h / 2, w, h, r=h / 2, color=th.ink, lift=0.9)
    ca = snap(clamp((t - END[0] - 0.25) / 0.3))
    if ca > 0:
        ix = px - w / 2 + 64
        c.drawCircle(ix, cy, 26 * ca, G.P(th.on_ink))
        icon_check(c, ix, cy + 1, 27, th.ink, p=ca)
        T(c, "Every frame is code", ix + 50, cy + 12, F("inter", 35, wght=620, opsz=32), th.on_ink, a=ca)
    fl = F("inter", 25, wght=560, opsz=24)
    xs = [-230, 0, 230]
    for k, ((label, logo), tl) in enumerate(zip(MODELS, T_LOGOS)):
        s = pop(t, tl, 2.6, 0.5)
        if s <= 0:
            continue
        lx, ly = px + xs[k], cy + 150
        a = clamp((t - tl) / 0.15)
        with G.xf(c, lx, ly, s=s):
            c.drawRRect(rr(-100, -46, 200, 92, 46), G.P(th.soft, a))
            if logo == "openai":
                LG.mark(c, "openai", -58, 0, 34, G.P(th.ink, a))
            elif logo == "gemini":
                LG.gemini(c, -58, 0, 34, alpha=a)
            else:
                LG.claude(c, -58, 0, 38, CLAY, a)
            T(c, label, -30, 9, fl, th.ink, a=a)
    la = clamp((t - T_CREDIT) / 0.4)
    if la > 0:
        tag(c, th, "THE FRONTIER   ·   DARIO AMODEI   ·   INTERFACE", px, cy + 262, a=la, align=0.5)


# ---------------------------------------------------------------- the rest of the board

def _card_title(c, th, x, y, title, sub=None):
    T(c, title, x + 44, y + 70, F("inter", 32, wght=640, opsz=32), th.ink)
    if sub:
        tag(c, th, sub, x + 44 + F("inter", 32, wght=640, opsz=32).width(title) + 20, y + 66)


def meter(c, th, t):
    x, y, w, h = METER
    panel(c, th, x, y, w, h, r=36, lift=0.5)
    _card_title(c, th, x, y, "Now playing", "INTERFACE.WAV")
    _, lv = levels("interface")
    fi = min(len(lv) - 1, int(t * 60))
    n = lv.shape[1]
    bw = (w - 88 - 12 * (n - 1)) / n
    for k in range(n):
        v = float(lv[fi, k])
        bh = 12 + 190 * v
        c.drawRRect(rr(x + 44 + k * (bw + 12), y + h - 50 - bh, bw, bh, 8), G.P(CLAY if k < 2 else th.ink, 0.9))
    bar = min(12, int(t / 2) + 1)
    T(c, f"BAR {bar:02d} / 12", x + w - 44, y + 66, F("mono", 18, wght=650), th.sub, align=1.0, tracking=0.2)


SCENES = [(0.0, 2.0, "PICK"), (2.0, 3.8, "PROMPT"), (3.8, 10.5, "FABLE 5.1 ANSWERS"), (10.5, 13.2, "PLAY"),
          (13.2, 15.5, "SETTINGS"), (15.5, 18.0, "STATS"), (18.0, 20.9, "OVERVIEW"), (20.9, 25.0, "SHIP")]


def timeline(c, th, t):
    x, y, w, h = TIMELINE
    panel(c, th, x, y, w, h, r=36, lift=0.5)
    _card_title(c, th, x, y, "Timeline", "12 BARS · 120 BPM")
    x0, x1 = x + 44, x + w - 44
    fm = F("mono", 14, wght=600)
    for b in range(13):
        bx = lerp(x0, x1, b / 12)
        c.drawLine(bx, y + 120, bx, y + h - 60, G.P(th.line, 1, stroke=1.2))
        if b < 12:
            T(c, f"{b + 1:02d}", bx + 8, y + 140, fm, th.sub)
    for k, (a, b, name) in enumerate(SCENES):
        ry = y + 170 + (k % 4) * 72
        ax, bx = lerp(x0, x1, a / DURATION), lerp(x0, x1, b / DURATION)
        on = a <= t < b
        c.drawRRect(rr(ax + 2, ry, bx - ax - 4, 56, 14), G.P(th.ink if on else th.soft))
        with G.clip_rect(c, ax + 2, ry, bx - ax - 4, 56):
            T(c, name, ax + 16, ry + 35, F("mono", 15, wght=650), th.on_ink if on else th.sub, tracking=0.12)
    hx = lerp(x0, x1, t / DURATION)
    c.drawLine(hx, y + 110, hx, y + h - 50, G.P(CLAY, 1, stroke=3))
    G.circle(c, hx, y + 110, 8, G.P(CLAY))


def roster(c, th, t):
    x, y, w, h = ROSTER
    panel(c, th, x, y, w, h, r=36, lift=0.5)
    _card_title(c, th, x, y, "Models", "3 AVAILABLE")
    labs = ["OpenAI", "Google DeepMind", "Anthropic"]
    sel = 0 if t < T_PICK[0] else (1 if t < T_PICK[1] else 2)
    for k, ((name, logo), lab) in enumerate(zip(MODELS, labs)):
        ry = y + 130 + k * 84
        if k == sel:
            c.drawRRect(rr(x + 24, ry - 8, w - 48, 76, 20), G.P(th.soft))
        if logo == "openai":
            LG.mark(c, "openai", x + 76, ry + 30, 36, G.P(th.ink))
        elif logo == "gemini":
            LG.gemini(c, x + 76, ry + 30, 36)
        else:
            LG.claude(c, x + 76, ry + 30, 40, CLAY)
        T(c, name, x + 118, ry + 40, F("inter", 29, wght=600, opsz=32), th.ink)
        T(c, lab, x + 380, ry + 40, F("inter", 24, wght=450, opsz=24), th.sub)
        G.circle(c, x + w - 70, ry + 30, 15, G.P(th.ink if k == sel else th.line, 1, stroke=2.5))
        if k == sel:
            G.circle(c, x + w - 70, ry + 30, 8, G.P(th.ink))


def swatches(c, th, t):
    x, y, w, h = SWATCHES
    panel(c, th, x, y, w, h, r=36, lift=0.5)
    _card_title(c, th, x, y, "Tokens", th.name.upper())
    toks = [("bg", th.bg0), ("card", th.card), ("ink", th.ink), ("sub", th.sub), ("line", th.line),
            ("soft", th.soft), ("clay", CLAY), ("code", "#141417")]
    fm = F("mono", 15, wght=600)
    for k, (name, col) in enumerate(toks):
        cx = x + 44 + (k % 4) * 208
        cy = y + 120 + (k // 4) * 140
        c.drawRRect(rr(cx, cy, 70, 70, 18), G.P(col))
        c.drawRRect(rr(cx + 0.5, cy + 0.5, 69, 69, 18), G.P(th.line, 1, stroke=1.2))
        T(c, name, cx + 86, cy + 30, F("inter", 22, wght=600, opsz=24), th.ink)
        T(c, col.upper(), cx + 86, cy + 58, fm, th.sub)


def type_card(c, th, t):
    x, y, w, h = TYPE_CARD
    panel(c, th, x, y, w, h, r=36, lift=0.5)
    _card_title(c, th, x, y, "Type", "3 FAMILIES")
    T(c, "Aa", x + 44, y + 290, F("inter", 190, wght=620, opsz=32), th.ink)
    T(c, "Inter", x + 330, y + 176, F("inter", 34, wght=600, opsz=32), th.ink)
    T(c, "JetBrains Mono", x + 330, y + 238, F("mono", 30, wght=500), th.ink)
    T(c, "ARCHIVO", x + 330, y + 304, F("archivo", 38, wght=800, wdth=125), th.ink)
    T(c, "0123456789 · ∑ fps · ⌘K", x + 44, y + h - 60, F("mono", 24, wght=450), th.sub)


def queue(c, th, t):
    x, y, w, h = QUEUE
    panel(c, th, x, y, w, h, r=36, lift=0.5)
    _card_title(c, th, x, y, "Render queue")
    pf = in_out_cubic(clamp((t - T_PROG[0]) / (T_PROG[1] - T_PROG[0])))
    pt = 0.25 + 0.7 * clamp(t / DURATION)
    pi = clamp((t - T_ENTER) / 2.5)
    rows = [("the-frontier.mp4", pf), ("dario-amodei-tribute.mp4", pt), ("interface.mp4", pi)]
    for k, (name, p) in enumerate(rows):
        ry = y + 140 + k * 128
        T(c, name, x + 44, ry, F("mono", 23, wght=560), th.ink)
        st = "done" if p >= 1 else (f"{int(p * 100)}%" if p > 0 else "queued")
        T(c, st, x + w - 44, ry, F("mono", 21, wght=600), CLAY if 0 < p < 1 else th.sub, align=1.0)
        c.drawRRect(rr(x + 44, ry + 26, w - 88, 10, 5), G.P(th.line))
        if p > 0:
            c.drawRRect(rr(x + 44, ry + 26, max(10, (w - 88) * p), 10, 5), G.P(th.ink if p >= 1 else CLAY))


LOG = [(T_PICK[1], "Fable 5.1 selected"), (T_SEND, "Prompt sent"), (T_THOUGHT, "Thought for 12 s"),
       (T_CODE, "Wrote 4 lines of Python"), (T_DONE, "Rendered the-frontier.mp4"), (T_PLAY, "Playing"),
       (T_WIPE, "Dark mode on"), (T_SWITCH[0], "Stats: Tribute"), (T_SWITCH[1], "Stats: Interface"),
       (T_ENTER, "Shipped")]


def activity(c, th, t):
    x, y, w, h = ACTIVITY
    panel(c, th, x, y, w, h, r=36, lift=0.5)
    _card_title(c, th, x, y, "Activity")
    live = [(tt, s) for tt, s in LOG if tt <= t][-7:]
    fm = F("mono", 18, wght=600)
    fi = F("inter", 24, wght=500, opsz=24)
    for k, (tt, s) in enumerate(reversed(live)):
        ry = y + 140 + k * 68
        a = clamp((t - tt) / 0.2)
        T(c, f"00:{tt:04.1f}", x + 44, ry, fm, th.sub, a=a, tnum=True)
        T(c, s, x + 190, ry, fi, th.ink, a=a)


# ---------------------------------------------------------------- the cursor

CLICKS = [T_PICK[0], T_PICK[1], T_SEND, T_COPY, T_OPEN, T_PLAY, T_GRAB, T_TOG[0], T_TOG[1], T_SLIDE[0],
          T_SWITCH[0], T_SWITCH[1]]
HOLDS = [(T_GRAB, T_DROP), T_SLIDE]


def _seg_center(k):
    sx, sy, sw, sh = SEG3
    return sx + sw / 3 * (k + 0.5), sy + sh / 2


def _cursor_keys():
    """(time, x, y, space): 'b' keys are on the board and follow the camera at that moment."""
    return [
        (0.0, 1270, 1400, "s"),
        (0.66, PICK_CENTERS[1] + 14, PICK_Y0 + 64, "b"), (T_PICK[0], PICK_CENTERS[1] + 14, PICK_Y0 + 64, "b"),
        (1.3, PICK_CENTERS[2] + 20, PICK_Y0 + 64, "b"), (T_PICK[1], PICK_CENTERS[2] + 20, PICK_Y0 + 64, "b"),
        (1.94, 1190, 1150, "s"),
        (2.9, 1250, 1300, "s"), (3.3, 1250, 1300, "s"),
        (3.62, SEND_C[0] + 6, SEND_C[1] + 8, "b"), (T_SEND, SEND_C[0] + 6, SEND_C[1] + 8, "b"),
        (4.3, 1270, 1180, "s"), (8.1, 1250, 1160, "s"),
        (8.46, S.COPY_CENTER[0] + 8, S.COPY_CENTER[1] + 8, "b"), (T_COPY, S.COPY_CENTER[0] + 8, S.COPY_CENTER[1] + 8, "b"),
        (9.1, 1240, 1250, "s"), (10.14, 1240, 1250, "s"),
        (10.42, S.OPEN_CENTER[0] + 8, S.OPEN_CENTER[1] + 8, "b"), (T_OPEN, S.OPEN_CENTER[0] + 8, S.OPEN_CENTER[1] + 8, "b"),
        (10.96, VIDEO[0] + VIDEO[2] / 2 + 10, VIDEO[1] + VIDEO[3] / 2 + 12, "b"),
        (T_PLAY, VIDEO[0] + VIDEO[2] / 2 + 10, VIDEO[1] + VIDEO[3] / 2 + 12, "b"),
        (11.6, 1130, 1210, "s"),
        (12.08, scrub_x(playhead(T_GRAB)) + 4, SCRUB[2] + 6, "b"), (T_GRAB, scrub_x(playhead(T_GRAB)) + 4, SCRUB[2] + 6, "b"),
        (T_DROP, scrub_x(FILM_AT_DROP) + 4, SCRUB[2] + 6, "b"),
        (13.1, 1150, 1180, "s"),
        (13.62, TOGGLE_X + 8, ROW_Y[1] + 10, "b"), (T_TOG[0], TOGGLE_X + 8, ROW_Y[1] + 10, "b"),
        (13.92, TOGGLE_X + 8, ROW_Y[2] + 10, "b"), (T_TOG[1], TOGGLE_X + 8, ROW_Y[2] + 10, "b"),
        (14.58, lerp(SLIDE[0], SLIDE[1], 0.35) + 4, SLIDE[2] + 6, "b"),
        (T_SLIDE[0], lerp(SLIDE[0], SLIDE[1], 0.35) + 4, SLIDE[2] + 6, "b"),
        (T_SLIDE[1], SLIDE[1] + 4, SLIDE[2] + 6, "b"),
        (15.44, 1180, 1200, "s"),
        (15.88, _seg_center(1)[0] + 8, _seg_center(1)[1] + 8, "b"), (T_SWITCH[0], _seg_center(1)[0] + 8, _seg_center(1)[1] + 8, "b"),
        (16.6, _seg_center(2)[0] + 8, _seg_center(2)[1] + 8, "b"), (T_SWITCH[1], _seg_center(2)[0] + 8, _seg_center(2)[1] + 8, "b"),
        (T_HOVER[0], *hover_point(T_HOVER[0]), "b"), (T_HOVER[1], *hover_point(T_HOVER[1]), "b"),
        (18.2, 1300, 1500, "s"), (DURATION, 1300, 1500, "s"),
    ]


@lru_cache(maxsize=1)
def cursor_track():
    out = []
    for tk, x, y, space in _cursor_keys():
        if space == "b":
            x, y = to_screen(tk, x, y)
        out.append((tk, x, y))
    return out


def cursor_pos(t):
    keys = cursor_track()
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            e = in_out_cubic(u)
            d = math.hypot(x1 - x0, y1 - y0)
            arc = math.sin(math.pi * e) * min(60.0, d * 0.12)
            nx, ny = (-(y1 - y0) / d, (x1 - x0) / d) if d > 1e-6 else (0.0, 0.0)
            return x0 + (x1 - x0) * e + nx * arc, y0 + (y1 - y0) * e + ny * arc
    return keys[-1][1], keys[-1][2]


_ARROW = [(0, 0), (0, 31), (7.8, 24), (13, 35.5), (17.6, 33.4), (12.6, 22.4), (23, 22.4)]


def cursor(c, t):
    a = clamp(t / 0.25) * (1 - clamp((t - 18.0) / 0.25))
    if a <= 0:
        return
    th = theme_at(t - 0.05)
    x, y = cursor_pos(t)
    press = press_of(t, CLICKS)
    for h0, h1 in HOLDS:
        if h0 <= t <= h1:
            press = max(press, 0.6)
    for tc in CLICKS:
        u = (t - tc) / 0.45
        if 0 <= u < 1:
            G.circle(c, x, y, 8 + 46 * out_cubic(u), G.P(th.ink, 0.25 * (1 - u) * a, stroke=2.0))
    s = 1.35 * (1 - 0.14 * press)
    path = G.poly([(px * s, py * s) for px, py in _ARROW])
    body, edge = (th.ink, th.on_ink)
    with G.layer(c, alpha=a):
        with G.xf(c, x, y):
            with G.xf(c, 1.5, 4):
                c.drawPath(path, G.P("#000000", 0.28, blur=3))
            c.drawPath(path, G.P(edge, 1, stroke=4.2, join="round"))
            c.drawPath(path, G.P(body))


# ---------------------------------------------------------------- screen-space overlays

def toast(c, th, t):
    t0, t1 = T_TOAST
    if not t0 <= t < t1 + 0.4:
        return
    s = spring(t - t0, 2.2, 0.6)
    out = whip(clamp((t - t1) / 0.36))
    w, h = 640, 96
    x, y = CX - w / 2, lerp(-130, 44, s) - 190 * out
    panel(c, th, x, y, w, h, r=h / 2, lift=1.0)
    G.circle(c, x + 50, y + h / 2, 22, G.P(th.ink))
    icon_check(c, x + 50, y + h / 2 + 1, 22, th.on_ink, p=snap(clamp((t - t0 - 0.12) / 0.3)))
    T(c, "the-frontier.mp4 is ready", x + 90, y + 44, F("inter", 27, wght=620, opsz=32), th.ink)
    T(c, "26.4 s  ·  1080p60  ·  every frame is code", x + 90, y + 74, F("inter", 20, wght=460, opsz=24), th.sub)
    life = 1 - clamp((t - t0) / (t1 - t0))
    c.drawRRect(rr(x + 48, y + h - 5, (w - 96) * life, 3, 1.5), G.P(CLAY, 0.8))


def path_points():
    """Where every click landed, in board coordinates, in order."""
    pts = []
    for tk, x, y, space in _cursor_keys():
        if space == "b" and any(abs(tk - tc) < 1e-6 for tc in CLICKS):
            pts.append((x, y))
    return pts


def click_path(c, th, t):
    """Overview: the cursor's journey drawn across the board, click by click."""
    if t < T_PATH[0] - 0.1:
        return
    pts = path_points()
    p = in_out_cubic(clamp((t - T_PATH[0]) / (T_PATH[1] - T_PATH[0])))
    path = skia.Path()
    path.moveTo(*pts[0])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        path.quadTo(mx - dy * 0.18, my + dx * 0.18, x1, y1)
    fade = 1 - clamp((t - (T_FLY + 0.1)) / 0.3)
    if fade <= 0:
        return
    with G.layer(c, alpha=fade):
        c.drawPath(path, G.P(CLAY, 0.45, stroke=22, cap="round", effect=G.trim(0, p), blur=10))
        c.drawPath(path, G.P(CLAY, 1, stroke=7, cap="round", effect=G.compose(G.dash(26, 18), G.trim(0, p))))
        meas = skia.PathMeasure(path, False)
        total = meas.getLength()
        # arc length at each click, to pop its marker when the line arrives
        acc, lens = 0.0, [0.0]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            acc += math.hypot(x1 - x0, y1 - y0)
            lens.append(acc)
        fm = F("mono", 46, wght=750)
        for k, (x, y) in enumerate(pts):
            reach = lens[k] / max(lens[-1], 1)
            s = spring(p - reach, 12.0, 0.5) if p >= reach else 0.0
            if s <= 0:
                continue
            with G.xf(c, x, y, s=s):
                G.circle(c, 0, 0, 96, G.P(CLAY, 0.25, blur=30))
                G.circle(c, 0, 0, 60, G.P(CLAY))
                T(c, f"{k + 1:02d}", 0, 16, fm, "#0e0e10", align=0.5)
        del meas, total


def counters(c, th, t):
    if not T_OVER + 0.3 <= t < T_FLY + 0.3:
        return
    a = clamp((t - T_OVER - 0.3) / 0.3) * (1 - clamp((t - T_FLY) / 0.25))
    words = len(S.PROSE_TOK) + sum(len(x.split()) for x in S.THINKING) + 20
    keys = len(PROMPT[0]) + len(PROMPT[1]) + 6
    stats_ = [("CLICKS", len(CLICKS)), ("KEYSTROKES", keys), ("WORDS STREAMED", words), ("FRAMES", 1500)]
    fb = F("archivo", 64, wght=800, wdth=112)
    fl = F("mono", 15, wght=650)
    with G.layer(c, alpha=a):
        T(c, "INTERFACE", 64, 120, F("archivo", 88, wght=850, wdth=125), th.ink)
        tag(c, th, "ONE BOARD  ·  FOURTEEN COMPONENTS  ·  ONE CURSOR", 68, 164)
        for k, (lab, val) in enumerate(stats_):
            x = 64 + k * 340
            u = clamp((t - T_OVER - 0.45 - 0.12 * k) / 0.7)
            v = int(round(val * out_cubic(u)))
            T(c, f"{v:,}", x, SIZE[1] - 92, fb, th.ink, tnum=True)
            T(c, lab, x + 4, SIZE[1] - 56, fl, th.sub, tracking=0.24)


# ---------------------------------------------------------------- the film

COMPONENTS = [("01", "MODEL PICKER", (PICK_X0 - 10, PICK_Y0 - 10, 3 * SEG_W + 20, PICK_H + 20), picker),
              (None, None, MCARD, model_card),
              ("02", "COMPOSER", COMPOSER, composer),
              ("03", "FABLE 5.1  ·  ANSWER", (S.RX, S.RY, S.RW, S.CARD_H), S.answer),
              ("04", "PLAYER", PLAYER, player),
              ("05", "SETTINGS", SETTINGS, settings),
              ("06", "STATS", STATS, stats),
              ("07", "COMMAND", PALETTE, palette),
              ("08", "NOW PLAYING", METER, meter),
              ("09", "TIMELINE", TIMELINE, timeline),
              ("10", "MODELS", ROSTER, roster),
              ("11", "TOKENS", SWATCHES, swatches),
              ("12", "TYPE", TYPE_CARD, type_card),
              ("13", "RENDER QUEUE", QUEUE, queue),
              ("14", "ACTIVITY", ACTIVITY, activity)]


LABEL_AT = {"01": T_PICKER_IN, "03": T_RESP}


def world(c, th, t):
    """Everything but the cursor, in one theme."""
    backdrop(c, th)
    m = cam_matrix(t)
    zoom = cam(t)[2]
    vis = visible_rect(m)

    def board(cc):
        cc.save()
        cc.concat(m)
        board_grid(cc, th, vis, zoom)
        for num, name, rect, fn in COMPONENTS:
            if not seen(vis, rect):
                continue
            if num:
                la = clamp((t - LABEL_AT.get(num, 0.0)) / 0.3)
                if la > 0:
                    frame_label(cc, th, num, name, rect[0], rect[1], a=la)
            fn(cc, th, t)
        end(cc, th, t)
        click_path(cc, th, t)
        cc.restore()

    # as the board settles into the overview, a light sweep glints across it
    u = (t - (T_OVER + 0.35)) / 1.4
    if 0 < u < 1:
        G.light_sweep(c, board, -400, SIZE[0] + 400, CY, in_out_sine(u), colors=("#ffffff",), width=150,
                      angle=28.0, strength=0.3)
    else:
        board(c)
    toast(c, th, t)
    counters(c, th, t)


def wipe_center():
    return to_screen(T_WIPE, TOGGLE_X, ROW_Y[2])


class Interface(Film):
    duration = DURATION
    size = SIZE

    def bg(self, t):
        return G.rgb(theme_at(t).bg0)

    def draw(self, c, t):
        u = (t - T_WIPE) / WIPE_LEN
        if u < 0:
            world(c, LIGHT, t)
        elif u >= 1:
            world(c, DARK, t)
        else:
            world(c, LIGHT, t)
            wx, wy = wipe_center()
            far = max(math.hypot(wx - px, wy - py) for px in (0, SIZE[0]) for py in (0, SIZE[1]))
            r = (far + 40) * snap(u) + 1
            c.save()
            c.clipPath(skia.Path.Circle(wx, wy, r), skia.ClipOp.kIntersect, True)
            world(c, DARK, t)
            c.restore()
            G.circle(c, wx, wy, r, G.P(CLAY, 0.9 * (1 - u), stroke=10 * (1 - u) + 2))
            G.circle(c, wx, wy, r, G.P(CLAY, 0.5 * (1 - u), stroke=30, blur=18))
        fade = clamp((t - T_FADE[0]) / (T_FADE[1] - T_FADE[0]))
        if fade > 0:
            c.drawRect(skia.Rect.MakeWH(*SIZE), G.P(DARK.bg0, fade))
        cursor(c, t)
        d = G.mixc(DARK.sub, DARK.bg0, fade)
        if t >= END[0] + 0.8:
            la = clamp((t - END[0] - 0.8) / 0.4)
            T(c, "FAN-MADE · NOT AFFILIATED WITH OPENAI, GOOGLE OR ANTHROPIC", CX, SIZE[1] - 56,
              F("mono", 13, wght=500), d, a=0.8 * la, align=0.5, tracking=0.2)

    def mb(self, t):
        for w0 in WHIPS:
            if w0 - 0.02 <= t <= w0 + 0.58:
                return 16
        if T_OVER - 0.02 <= t <= T_OVER + 0.7:
            return 14
        return 6

    def fx(self, t):
        dark = t >= T_WIPE + 0.3
        fx = {"grain": 0.02 if dark else 0.012, "vignette": 0.2 if dark else 0.07}
        if dark:
            fx.update(bloom=0.32, bloom_th=0.72, bloom_r=1.2)
        k = t - T_WIPE
        if 0 <= k < 0.5:
            fx["chroma"] = 5.0 * math.exp(-k / 0.1)
            fx["flash"] = 0.18 * math.exp(-k / 0.08)
        k = t - T_OVER
        if 0 <= k < 0.6:
            fx["zoom_blur"] = 0.12 * math.exp(-k / 0.12)
            fx["flash"] = 0.12 * math.exp(-k / 0.08)
        k = t - T_ENTER
        if 0 <= k < 0.5:
            fx["flash"] = 0.14 * math.exp(-k / 0.08)
        return fx
