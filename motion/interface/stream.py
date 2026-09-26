"""Fable 5.1's answer, streamed: it thinks, writes a plan, lists the beats, writes the code and renders the film.

Everything here is laid out once at import (word wrap, block positions, when each token lands), so a frame
only has to decide how far along each piece is.
"""
import math
import os
from functools import lru_cache

import cv2
import numpy as np
import skia

from engine import gfx as G
from engine import logos as LG
from engine.core import clamp, lerp, snap, in_out_cubic, hash01
from .score import (T_RESP, T_THINK, T_THINK_LINES, T_THOUGHT, T_PROSE, T_LIST, T_CODE, T_CODE_LINES, T_COPY,
                    T_TOOL, T_PROG, T_DONE, T_OPEN, T_SEND)
from .ui import F, T, rr, panel, pop, press_of, icon_check, icon_film, icon_copy, icon_play, icon_chevron, CLAY, \
    CODE_BG, CODE_BAR, SYN

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(HERE, "..", "out", "player_frames")
FRAMES_FPS = 30

# the answer card, in board coordinates
RX, RY, RW = 140, 1360, 1160
PAD = 56
IW = RW - 2 * PAD
HDR = 100

THINKING = ["150 BPM, so a beat is 24 frames at 60 fps",
            "three labs, three drops, then one clash",
            "Blender for the finale plate, skia for the rest"]
THINK_STEP = 40
THINK_H = 24 + THINK_STEP * len(THINKING)

PROSE = [("On it. A ", ""), ("26.4-second", "b"), (" reel: 16 bars at 150 BPM, 1920 × 1080 at 60 fps, so ", ""),
         ("1,584 frames", "b"), (". Every frame is code: ", ""), ("skia", "code"), (" draws the pictures, ", ""),
         ("Blender", "code"), (" renders the finale plate and ", ""), ("numpy", "code"),
         (" synthesises every sound.", "")]
LINE_H = 48

LIST = [("01", [("Cold open: three labs, one frontier", None)]),
        ("02", [("Three drops: ", None), ("Astra 6", "openai"), ("  ·  ", None), ("Gemini 3.8", "gemini"),
                ("  ·  ", None), ("Fable 5.1", "claude")]),
        ("03", [("Finale: a Blender plate and a light sweep", None)])]
LIST_STEP = 60

CODE = [[("def", "kw"), (" ", "plain"), ("astra", "fn"), ("(c, t):", "pun")],
        [("    k ", "plain"), ("=", "pun"), (" ", "plain"), ("kick_env", "fn"), ("(t)", "pun"),
         ("            ", "plain"), ("# every kick hits the picture", "com")],
        [("    ", "plain"), ("for", "kw"), (" p ", "plain"), ("in", "kw"), (" ", "plain"), ("star_sphere", "fn"),
         ("(", "pun"), ("640", "num"), ("):", "pun")],
        [("        ", "plain"), ("glow", "fn"), ("(c, p, ", "pun"), ("1", "num"), (" + ", "pun"), ("0.4", "num"),
         (" * k)", "pun")]]
CODE_BAR_H = 54
CODE_LH = 42
CODE_H = CODE_BAR_H + CODE_LH * len(CODE) + 34

THUMB_TIMES = [1.0, 3.7, 8.5, 13.3, 17.9, 21.6, 24.6]   # seconds into THE FRONTIER
TOOL_H = 262


# ---------------------------------------------------------------- fonts

def f_body():
    return F("inter", 30, wght=430, opsz=32)


def f_bold():
    return F("inter", 30, wght=650, opsz=32)


def f_code_inline():
    return F("mono", 25, wght=520)


def f_code():
    return F("mono", 24, wght=480)


# ---------------------------------------------------------------- static layout

def _tokens():
    """Split the prose into streamable words; spaces ride along with the word before them."""
    chars = [(ch, st) for text, st in PROSE for ch in text]
    toks, cur, cur_st, trail = [], "", None, ""
    for ch, st in chars:
        if ch == " ":
            trail += ch
            continue
        if trail or (cur and st != cur_st):
            if cur:
                toks.append((cur, cur_st, trail))
            cur, trail = "", ""
        cur += ch
        cur_st = st
    if cur:
        toks.append((cur, cur_st, trail))
    return toks


def _font_for(st):
    return {"b": f_bold(), "code": f_code_inline()}.get(st, f_body())


def _layout():
    out = []
    x, line = 0.0, 0
    space = f_body().width(" ")
    glued = False
    for word, st, trail in _tokens():
        f = _font_for(st)
        w = f.width(word) + (20 if st == "code" else 0)
        if x > 0 and x + w > IW and not glued:
            x, line = 0.0, line + 1
        out.append(dict(word=word, st=st, x=x, line=line, w=w))
        x += w + space * len(trail)
        glued = not trail          # the next token touches this one ("frames" + "."), keep them together
    return out


PROSE_TOK = _layout()
PROSE_LINES = PROSE_TOK[-1]["line"] + 1


def _stream_times():
    """Tokens arrive in bursts of one to three words, like a real stream."""
    n = len(PROSE_TOK)
    chunks, i, k = [], 0, 0
    while i < n:
        size = 1 + int(hash01(k, 71) * 2.99)
        chunks.append(list(range(i, min(n, i + size))))
        i += size
        k += 1
    t0, t1 = T_PROSE
    times = [0.0] * n
    for j, ch in enumerate(chunks):
        tj = t0 + (t1 - t0) * (j + 0.35 * (hash01(j, 72) - 0.5)) / len(chunks)
        for m, idx in enumerate(ch):
            times[idx] = max(t0, tj + 0.018 * m)
    return times


TOK_T = _stream_times()
LINE_T = [min(TOK_T[i] for i, tk in enumerate(PROSE_TOK) if tk["line"] == ln) for ln in range(PROSE_LINES)]
CHUNK_T = sorted(set(round(x, 4) for x in TOK_T))          # for the sound

# vertical positions, relative to the top of the body (below the header and the thinking block)
PROSE_TOP = 0
PROSE_H = 36 + (PROSE_LINES - 1) * LINE_H + 18
LIST_TOP = PROSE_H + 22
LIST_H = LIST_STEP * len(LIST) + 4
CODE_TOP = LIST_TOP + LIST_H + 22
TOOL_TOP = CODE_TOP + CODE_H + 30
BODY_H = TOOL_TOP + TOOL_H
CARD_H = HDR + BODY_H + 26

# (time, body height once that piece is in); the card grows through these
GROWTH = ([(T_PROSE[0] - 0.01, 0.0)] + [(LINE_T[ln], 36 + ln * LINE_H + 18) for ln in range(PROSE_LINES)] +
          [(T_LIST[k], LIST_TOP + LIST_STEP * (k + 1) + 4) for k in range(len(LIST))] +
          [(T_CODE, CODE_TOP + CODE_H), (T_TOOL, TOOL_TOP + TOOL_H - 60), (T_DONE, TOOL_TOP + TOOL_H)])


def think_h(t):
    """Height of the thinking block: grows line by line, then folds away."""
    if t < T_THINK_LINES[0]:
        return 0.0
    h = 24 * snap(clamp((t - T_THINK_LINES[0]) / 0.25))
    for tl in T_THINK_LINES:
        h += THINK_STEP * snap(clamp((t - tl) / 0.25))
    return h * (1 - snap(clamp((t - T_THOUGHT) / 0.34)))


def body_h(t):
    h, prev = 0.0, 0.0
    for tk, hk in GROWTH:
        h += (hk - prev) * snap(clamp((t - tk) / 0.3))
        prev = hk
    return h


def card_h(t):
    return HDR + think_h(t) + body_h(t) + 26


def body_y(t):
    """Board y of the top of the body."""
    return RY + HDR + think_h(t) + 8


def head_y(t):
    """Board y of the newest line: where the camera wants to look."""
    return RY + card_h(t)


# where the cursor clicks "Open" (the thinking block has folded away by then)
OPEN_W, OPEN_H = 142, 52
OPEN_X = RX + RW - PAD - OPEN_W
OPEN_Y = RY + HDR + 8 + TOOL_TOP + 206
OPEN_CENTER = (OPEN_X + OPEN_W / 2, OPEN_Y + OPEN_H / 2)


COPY_CENTER = (RX + PAD + IW - 70 - 10, RY + HDR + 8 + CODE_TOP + 27)


# ---------------------------------------------------------------- film frames

@lru_cache(maxsize=24)
def film_image(idx):
    p = os.path.join(FRAMES_DIR, f"f{idx:04d}.jpg")
    if not os.path.exists(p):
        return None
    return G.image_from_rgba(cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGBA))


@lru_cache(maxsize=32)
def film_thumb(idx, w, h):
    p = os.path.join(FRAMES_DIR, f"f{idx:04d}.jpg")
    if not os.path.exists(p):
        return None
    im = cv2.resize(cv2.imread(p), (w, h), interpolation=cv2.INTER_AREA)
    return G.image_from_rgba(cv2.cvtColor(im, cv2.COLOR_BGR2RGBA))


def frame_index(secs):
    return int(np.clip(int(secs * FRAMES_FPS) + 1, 1, 792))


# ---------------------------------------------------------------- drawing

def _shimmer(c, th, s, x, y, font, t):
    """'Thinking' with a highlight sweeping through it."""
    def draw(cc):
        T(cc, s, x, y, font, th.sub, align=1.0)
    w = font.width(s)
    u = ((t - T_THINK[0]) * 1.1) % 1.0
    G.light_sweep(c, draw, x - w - 120, x + 120, y - 10, u, colors=(th.ink,), width=90, angle=0.0, strength=1.0)


def header(c, th, t):
    x0, y0 = RX + PAD, RY
    thinking = T_RESP <= t < T_THOUGHT + 0.4
    spin = (t - T_THINK[0]) * 380 if t < T_THOUGHT else (T_THOUGHT - T_THINK[0]) * 380 + 200 * snap(clamp((t - T_THOUGHT) / 0.5))
    breathe = 0.35 + 0.65 * (0.5 + 0.5 * math.sin((t - T_THINK[0]) * 8)) if t < T_THOUGHT else 1.0
    LG.claude(c, x0 + 20, y0 + 52, 40, CLAY, 1.0, breathe, rot=spin)
    T(c, "Fable 5.1", x0 + 56, y0 + 63, F("inter", 30, wght=640, opsz=32), th.ink)
    fs = F("inter", 25, wght=500, opsz=24)
    xr = RX + RW - PAD - 34
    u = clamp((t - T_THOUGHT) / 0.4)
    with G.clip_rect(c, xr - 360, y0 + 20, 400, 64):
        if u < 1 and thinking:
            with G.layer(c, alpha=1 - snap(u)):
                with G.xf(c, 0, -40 * snap(u)):
                    _shimmer(c, th, "Thinking", xr, y0 + 62, fs, t)
        if u > 0:
            e = snap(u)
            T(c, "Thought for 12s", xr, y0 + 62 + 40 * (1 - e), fs, th.sub, a=e, align=1.0)
    icon_chevron(c, xr + 20, y0 + 55, 16, th.sub, rot=-90 * snap(u))
    # the thinking block
    h = think_h(t)
    if h > 1:
        with G.clip_rect(c, RX, y0 + HDR - 6, RW, h + 6):
            c.drawRect(skia.Rect.MakeXYWH(x0 + 2, y0 + HDR + 4, 3, h - 16), G.P(th.line))
            ft = F("inter", 24, wght=430, opsz=24)
            for k, (line, tl) in enumerate(zip(THINKING, T_THINK_LINES)):
                if t < tl:
                    continue
                n = int(len(line) * clamp((t - tl) / 0.26))
                a = clamp((t - tl) / 0.12)
                T(c, line[:n], x0 + 26, y0 + HDR + 30 + k * THINK_STEP, ft, th.sub, a=a)


def prose(c, th, t, by):
    live = [i for i, ti in enumerate(TOK_T) if t >= ti]
    if not live:
        return
    for i in live:
        tk = PROSE_TOK[i]
        age = t - TOK_T[i]
        a = clamp(age / 0.14)
        dy = 9 * (1 - snap(clamp(age / 0.22)))
        col = G.mixc(CLAY, th.ink, clamp(age / 0.45))
        x = RX + PAD + tk["x"]
        y = by + PROSE_TOP + 36 + tk["line"] * LINE_H + dy
        if tk["st"] == "code":
            fc = f_code_inline()
            c.drawRRect(rr(x, y - 27, tk["w"], 38, 9), G.P(th.soft, a))
            c.drawRRect(rr(x + 0.5, y - 26.5, tk["w"] - 1, 37, 9), G.P(th.line, a, stroke=1.2))
            T(c, tk["word"], x + 10, y, fc, col, a=a)
        else:
            T(c, tk["word"], x, y, _font_for(tk["st"]), col, a=a)
    # the caret rides the end of the stream
    if T_PROSE[0] <= t < T_PROSE[1] + 0.18:
        tk = PROSE_TOK[live[-1]]
        cx = RX + PAD + tk["x"] + tk["w"] + 14
        cy = by + PROSE_TOP + 36 + tk["line"] * LINE_H - 10
        G.circle(c, cx, cy, 7 * (0.8 + 0.2 * math.sin(t * 30)), G.P(CLAY))


def _logo(c, th, kind, x, y, s, a):
    if kind == "openai":
        LG.mark(c, "openai", x, y, s, G.P(th.ink, a))
    elif kind == "gemini":
        LG.gemini(c, x, y, s, alpha=a)
    else:
        LG.claude(c, x, y, s * 1.1, CLAY, a)


def bullet_list(c, th, t, by):
    fnum = F("mono", 21, wght=600)
    ftx = F("inter", 29, wght=480, opsz=32)
    for k, ((num, parts), tl) in enumerate(zip(LIST, T_LIST)):
        if t < tl:
            continue
        u = clamp((t - tl) / 0.3)
        e = snap(u)
        a = clamp((t - tl) / 0.16)
        y = by + LIST_TOP + 38 + k * LIST_STEP
        x = RX + PAD + 30 * (1 - e)
        c.drawRRect(rr(x, y - 30, 52, 40, 10), G.P(th.soft, a))
        T(c, num, x + 26, y - 1, fnum, th.sub, a=a, align=0.5, tnum=True)
        cx = x + 76
        for text, logo in parts:
            if logo:
                _logo(c, th, logo, cx + 13, y - 10, 26, a)
                cx += 34
            T(c, text, cx, y, ftx, th.ink, a=a)
            cx += ftx.width(text)


def code_block(c, th, t, by):
    if t < T_CODE:
        return
    x, y, w = RX + PAD, by + CODE_TOP, IW
    h = CODE_H * snap(clamp((t - T_CODE) / 0.32))
    if h < 2:
        return
    c.save()
    c.clipRRect(rr(x, y, w, h, 20), skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, CODE_H), G.P(CODE_BG))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, CODE_BAR_H), G.P(CODE_BAR))
    fl = F("mono", 18, wght=560)
    T(c, "python", x + 28, y + 35, fl, "#8e8c86", tracking=0.08)
    pr = press_of(t, [T_COPY])
    with G.xf(c, x + w - 70, y + 27, s=1 - 0.1 * pr):
        if t < T_COPY:
            icon_copy(c, -30, -1, 22, "#8e8c86")
        else:
            icon_check(c, -30, 0, 20, "#8ab4f8", p=snap(clamp((t - T_COPY) / 0.25)))
        T(c, "Copied" if t >= T_COPY else "Copy", -6, 8, F("inter", 20, wght=520, opsz=24),
          "#8ab4f8" if t >= T_COPY else "#8e8c86")
    fc = f_code()
    adv = fc.width("0")
    for k, (line, tl) in enumerate(zip(CODE, T_CODE_LINES)):
        if t < tl:
            continue
        total = sum(len(s) for s, _ in line)
        n = int(math.ceil(total * clamp((t - tl) / 0.18)))
        cx, ly = x + 30, y + CODE_BAR_H + 38 + k * CODE_LH
        shown = 0
        for s, kind in line:
            if shown >= n:
                break
            part = s[:n - shown]
            T(c, part, cx, ly, fc, SYN[kind])
            cx += adv * len(part)
            shown += len(part)
        if n < total or (k == len(CODE) - 1 and t < T_TOOL):
            if n < total or int(t * 2.5) % 2 == 0:
                c.drawRect(skia.Rect.MakeXYWH(cx + 2, ly - 22, 12, 28), G.P(CLAY, 0.9))
    c.restore()
    c.drawRRect(rr(x + 0.5, y + 0.5, w - 1, h - 1, 20), G.P("#ffffff", 0.05, stroke=1.0))


def tool_call(c, th, t, by):
    if t < T_TOOL:
        return
    x, y = RX + PAD, by + TOOL_TOP
    a = clamp((t - T_TOOL) / 0.2)
    e = snap(clamp((t - T_TOOL) / 0.35))
    with G.layer(c, alpha=a):
        with G.xf(c, 0, 16 * (1 - e)):
            c.drawRRect(rr(x, y, 52, 52, 13), G.P(th.soft))
            icon_film(c, x + 26, y + 26, 26, th.ink)
            fr = F("inter", 29, wght=620, opsz=32)
            T(c, "Render", x + 72, y + 36, fr, th.ink)
            T(c, "the-frontier.mp4", x + 72 + fr.width("Render") + 14, y + 35, F("mono", 23, wght=500), th.sub)
            p = in_out_cubic(clamp((t - T_PROG[0]) / (T_PROG[1] - T_PROG[0])))
            frames = int(round(1584 * p))
            fm = F("mono", 23, wght=560)
            T(c, f"{frames:,} / 1,584".rjust(13), x + IW, y + 35, fm, th.ink if p < 1 else th.sub, align=1.0, tnum=True)
            # progress
            py = y + 74
            c.drawRRect(rr(x, py, IW, 8, 4), G.P(th.line))
            if p > 0:
                c.drawRRect(rr(x, py, max(8, IW * p), 8, 4), G.P(CLAY if p < 1 else th.ink))
            # the film strip: a thumbnail lands as the render passes it
            n = len(THUMB_TIMES)
            tw = (IW - 12 * (n - 1)) / n
            thh = tw * 9 / 16
            for k, secs in enumerate(THUMB_TIMES):
                tk = T_PROG[0] + (T_PROG[1] - T_PROG[0]) * (k + 0.6) / n
                s = pop(t, tk, 2.8, 0.5)
                if s <= 0:
                    c.drawRRect(rr(x + k * (tw + 12), py + 26, tw, thh, 10), G.P(th.soft))
                    continue
                tx = x + k * (tw + 12)
                with G.xf(c, tx + tw / 2, py + 26 + thh / 2, s=0.7 + 0.3 * s):
                    c.save()
                    c.clipRRect(rr(-tw / 2, -thh / 2, tw, thh, 10), skia.ClipOp.kIntersect, True)
                    img = film_thumb(frame_index(secs), int(tw), int(thh))
                    if img is not None:
                        G.draw_image(c, img, -tw / 2, -thh / 2, tw, thh, alpha=clamp(s * 1.5))
                    else:
                        c.drawRect(skia.Rect.MakeXYWH(-tw / 2, -thh / 2, tw, thh), G.P("#222226"))
                    flash = clamp(1 - (t - tk) / 0.25)
                    if flash > 0:
                        c.drawRect(skia.Rect.MakeXYWH(-tw / 2, -thh / 2, tw, thh), G.P("#ffffff", 0.6 * flash))
                    c.restore()
            # done
            if t >= T_DONE:
                d = snap(clamp((t - T_DONE) / 0.3))
                ry = y + 206
                G.circle(c, x + 18, ry + 26, 18 * d, G.P(th.ink))
                icon_check(c, x + 18, ry + 27, 18, th.on_ink, p=d, a=d)
                T(c, "Rendered  ·  26.4 s  ·  1,584 frames  ·  4 m 12 s", x + 50, ry + 35,
                  F("inter", 25, wght=520, opsz=24), th.ink, a=d)
                pr = press_of(t, [T_OPEN])
                hov = clamp((t - (T_OPEN - 0.2)) / 0.12)
                with G.xf(c, OPEN_X + OPEN_W / 2, OPEN_Y + OPEN_H / 2, s=(0.9 + 0.1 * d) * (1 - 0.07 * pr)):
                    c.drawRRect(rr(-OPEN_W / 2, -OPEN_H / 2, OPEN_W, OPEN_H, OPEN_H / 2),
                                G.P(G.mixc(th.ink, CLAY, 0.35 * hov), d))
                    icon_play(c, -OPEN_W / 2 + 34, 0, 18, th.on_ink, a=d)
                    T(c, "Open", -OPEN_W / 2 + 54, 9, F("inter", 24, wght=600, opsz=24), th.on_ink, a=d)


def answer(c, th, t):
    """The whole answer card."""
    if t < T_RESP:
        return
    s = pop(t, T_RESP, 2.4, 0.55)
    a = clamp((t - T_RESP) / 0.18)
    h = card_h(t)
    with G.layer(c, alpha=a):
        with G.xf(c, RX + RW / 2, RY, s=0.94 + 0.06 * s):
            c.translate(-(RX + RW / 2), -RY)
            panel(c, th, RX, RY, RW, h, r=34, lift=1.0)
            c.save()
            c.clipRRect(rr(RX, RY, RW, h, 34), skia.ClipOp.kIntersect, True)
            header(c, th, t)
            by = body_y(t)
            prose(c, th, t, by)
            bullet_list(c, th, t, by)
            code_block(c, th, t, by)
            tool_call(c, th, t, by)
            c.restore()


def sending(t):
    """0 -> 1 while the model is busy (the send button shows a stop square)."""
    return clamp((t - T_SEND) / 0.2) * (1 - clamp((t - T_DONE) / 0.2))
