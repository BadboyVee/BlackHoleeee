"""Brand marks, redrawn from memory as vector paths on a 24-unit grid.

The marks are trademarks of OpenAI, Google and Anthropic. They appear here in a fan-made
piece that credits the labs by name; nothing here is official or endorsed.
"""
import math
from functools import lru_cache

import skia

from . import gfx as G

OPENAI = ("M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 "
          "4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 "
          "4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 "
          "5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 "
          "1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 "
          "1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142"
          ".0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 "
          "19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 "
          "0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 "
          "2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 "
          "4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759"
          ".7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 "
          "6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-"
          "3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v"
          "2.9994l-2.5974 1.4997-2.6067-1.4997Z")

GEMINI = ("M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93"
          "a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 "
          "12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81")

ANTHROPIC = ("M17.3041 3.541h-3.6718l6.696 16.918H24Zm-10.6082 0L0 20.459h3.7442l1.3693-3.5527h7.0052l1.3693 "
             "3.5528h3.7442L10.5363 3.5409Zm-.3712 10.2232 2.2914-5.9456 2.2914 5.9456Z")

GOOGLE_G = ("M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 "
            "0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 "
            "0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 "
            "2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z")

_PATHS = {"openai": OPENAI, "gemini": GEMINI, "anthropic": ANTHROPIC, "google": GOOGLE_G}


@lru_cache(maxsize=None)
def path(name):
    p = G.svg_path(_PATHS[name])
    p.setFillType(skia.PathFillType.kWinding if name != "openai" else skia.PathFillType.kWinding)
    return p


def _fit(c, name, cx, cy, size, rot=0.0):
    p = path(name)
    b = p.getBounds()
    s = size / max(b.width(), b.height())
    c.translate(cx, cy)
    if rot:
        c.rotate(rot)
    c.scale(s, s)
    c.translate(-b.centerX(), -b.centerY())
    return p, s


def mark(c, name, cx, cy, size, paint, rot=0.0):
    """Draw a mark so that its larger side is `size` pixels, centred on (cx, cy)."""
    c.save()
    p, _ = _fit(c, name, cx, cy, size, rot)
    c.drawPath(p, paint)
    c.restore()


def mark_path(name, cx, cy, size, rot=0.0):
    """The mark as a path in canvas coordinates (for trims, clips and outlines)."""
    p = path(name)
    b = p.getBounds()
    s = size / max(b.width(), b.height())
    m = skia.Matrix()
    m.setTranslate(-b.centerX(), -b.centerY())
    m.postScale(s, s)
    if rot:
        m.postRotate(rot)
    m.postTranslate(cx, cy)
    out = skia.Path(p)
    out.transform(m)
    return out


GEMINI_STOPS = ["#4285f4", "#9b72cb", "#d96570"]


def gemini(c, cx, cy, size, alpha=1.0, rot=0.0, colors=None):
    """The Gemini sparkle, filled with its blue-to-rose gradient (set up in the mark's own units)."""
    c.save()
    p, _ = _fit(c, "gemini", cx, cy, size, rot)
    b = p.getBounds()
    sh = G.linear_grad(b.left(), b.bottom(), b.right(), b.top(), colors or GEMINI_STOPS, [0.08, 0.55, 0.95],
                       [alpha] * 3)
    c.drawPath(p, G.P("#ffffff", 1.0, shader=sh))
    c.restore()


GOOGLE_COLORS = [("#4285f4", -40, 50), ("#34a853", 50, 140), ("#fbbc05", 140, 205), ("#ea4335", 205, 320)]


def google(c, cx, cy, size, alpha=1.0, mono=None):
    """The Google G: one path, coloured by angular sectors around its centre."""
    if mono:
        mark(c, "google", cx, cy, size, G.P(mono, alpha))
        return
    r = size
    for col, a0, a1 in GOOGLE_COLORS:
        c.save()
        wedge = skia.Path()
        wedge.moveTo(cx, cy)
        wedge.arcTo(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), a0, a1 - a0, False)
        wedge.close()
        c.clipPath(wedge, skia.ClipOp.kIntersect, True)
        mark(c, "google", cx, cy, size, G.P(col, alpha))
        c.restore()
    # the crossbar is blue all the way to its inner end
    c.save()
    p, _ = _fit(c, "google", cx, cy, size)
    c.clipRect(skia.Rect.MakeLTRB(12.2, 10.7, 24.2, 14.4), skia.ClipOp.kIntersect, True)
    c.drawPath(p, G.P("#4285f4", alpha))
    c.restore()


# The Claude spark is drawn procedurally: uneven tapered rays around a small hub.
_RAYS = [(0, 1.00, 0.16), (27, 0.80, 0.14), (58, 0.95, 0.15), (88, 0.74, 0.13), (117, 0.98, 0.16),
         (148, 0.82, 0.14), (178, 0.93, 0.15), (208, 0.77, 0.13), (238, 1.00, 0.16), (267, 0.85, 0.14),
         (298, 0.95, 0.15), (329, 0.78, 0.13)]


def claude(c, cx, cy, size, color="#d97757", alpha=1.0, progress=1.0, rot=0.0, t=0.0, wobble=0.0):
    """The Claude spark: round-capped rays of uneven length meeting at a hub. progress grows them."""
    R = size / 2
    for k, (ang, ln, wd) in enumerate(_RAYS):
        grow = max(0.0, min(1.0, progress * 1.6 - k * 0.05))
        if grow <= 0:
            continue
        a = math.radians(ang + rot + wobble * math.sin(t * 3 + k))
        w = R * wd * 0.95
        L = (R - w / 2) * ln * grow
        c.drawLine(cx, cy, cx + math.cos(a) * L, cy + math.sin(a) * L, G.P(color, alpha, stroke=w, cap="round"))
    G.circle(c, cx, cy, R * 0.17 * min(1.0, progress * 3), G.P(color, alpha))
