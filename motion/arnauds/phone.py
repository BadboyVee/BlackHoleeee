"""The phone: the ask, a glowing input you type into, in the reference's big cropped phone."""
import math
from functools import lru_cache


from engine import gfx as G
from engine.core import clamp, snap, in_out_cubic
from .look import (T, ui, rr, WHITE, INK, glow_rrect, caret, phone, status_bar, icon_arrow, icon_x, icon_plus,
                   icon_send, ground)
from .score import T_PHONE, T_TYPE, PROMPT, T_SEND

# ---------------------------------------------------------------- the ask

PX, PY, PW, PH = 333, 150, 1254, 1300          # the phone, big and cropped, as in the reference
IX, IY, IW, IH = 368, 388, 1184, 318           # the input card


def wrap(text, font, width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.width(test) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


@lru_cache(maxsize=1)
def prompt_lines():
    return wrap(PROMPT, ui(44, 430), IW - 210)


def typed(t):
    n = len(PROMPT)
    return int(round(n * clamp((t - T_TYPE[0]) / (T_TYPE[1] - T_TYPE[0]))))


def ask(c, t):
    """The phone rises out of a 3D tilt and settles; the prompt types itself into the glowing input."""
    ground(c, t)
    u = snap(clamp((t - T_PHONE) / 0.6))
    push = 1.0 + 0.06 * in_out_cubic(clamp((t - T_TYPE[0]) / 2.0))
    c.save()
    c.translate(960, 560)
    c.scale(push, push)
    c.translate(-960, -560)
    # the phone rises up behind the input box the light has just become
    with G.xf(c, 0, 760 * (1 - u)):
        phone(c, PX, PY, PW, PH)
        status_bar(c, PX, PY + 40, PW, a=u)
    glow_rrect(c, IX, IY, IW, IH, 46, t, a=1.0, spread=30, width=22, speed=50)
    c.drawRRect(rr(IX, IY, IW, IH, 46), G.P(WHITE))
    k = clamp((t - T_PHONE - 0.05) / 0.3)
    icon_arrow(c, IX + 72, IY + 66, 34, INK, -1, a=k)
    icon_x(c, IX + IW - 70, IY + 66, 30, INK, a=k)
    icon_plus(c, IX + 64, IY + IH - 56, 30, INK, a=k)
    send_pr = math.exp(-(t - T_SEND) / 0.08) if t >= T_SEND else 0.0
    icon_send(c, IX + IW - 76, IY + IH - 60, 34 * (0.6 + 0.4 * k), a=k, press=send_pr)
    f = ui(44, 430)
    n = typed(t)
    x0, y0 = IX + 104, IY + 142
    shown = n
    cx, cy = x0, y0
    for k, line in enumerate(prompt_lines()):
        part = line[:max(0, shown)]
        if part:
            T(c, part, x0, y0 + k * 58, f, INK)
        if 0 <= shown <= len(line):
            cx, cy = x0 + f.width(part) + 4, y0 + k * 58
        shown -= len(line) + 1
        if shown < 0:
            break
    typing = T_TYPE[0] <= t < T_TYPE[1]
    if t >= T_SEND:
        caret(c, cx + 6, cy - 40, 54)
    else:
        caret(c, cx + 6, cy - 40, 54, a=1.0 if (typing or int(t * 2.4) % 2 == 0) else 0.0)
    c.restore()
    return cx, cy


def caret_local(t):
    f = ui(44, 430)
    shown = typed(t)
    x0, y0 = IX + 104, IY + 142
    cx, cy = x0, y0
    for k, line in enumerate(prompt_lines()):
        part = line[:max(0, shown)]
        if 0 <= shown <= len(line):
            cx, cy = x0 + f.width(part) + 4, y0 + k * 58
        shown -= len(line) + 1
        if shown < 0:
            break
    return cx, cy


def typed_caret(t):
    """Where the camera dives: just behind the caret, on screen (the phone has settled by then)."""
    cx, cy = caret_local(t)
    s = 1.0 + 0.06 * in_out_cubic(clamp((t - T_TYPE[0]) / 2.0))
    x, y = cx + 6 - 35, cy - 13
    return 960 + (x - 960) * s, 560 + (y - 560) * s
