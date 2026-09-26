"""Skia drawing helpers: colour, paint, variable-font typography, paths, layers."""
import math
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import skia
import uharfbuzz as hb

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
FAMILIES = {
    "archivo": "Archivo-Var.ttf",
    "archivo-italic": "Archivo-Italic-Var.ttf",
    "inter": "Inter-Var.ttf",
    "mono": "JetBrainsMono-Var.ttf",
    "fraunces": "Fraunces-Var.ttf",
    "fraunces-italic": "Fraunces-Italic-Var.ttf",
    "serif": "InstrumentSerif-Regular.ttf",
    "serif-italic": "InstrumentSerif-Italic.ttf",
    "dejavu-serif-italic": "DejaVuSerif-Italic.ttf",   # math symbols the display faces lack (∝)
    "dejavu-sans-bold": "DejaVuSans-Bold.ttf",         # key symbols the UI face lacks (⌘ ⏎)
}


# ---------------------------------------------------------------- colour

def rgb(c):
    """'#rrggbb' | (r, g, b) floats -> (r, g, b) floats in 0..1."""
    if isinstance(c, str):
        c = c.lstrip("#")
        return (int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255)
    return tuple(float(v) for v in c[:3])


def mixc(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def c4(c, a=1.0):
    r, g, b = rgb(c)
    return skia.Color4f(r, g, b, max(0.0, min(1.0, a)))


def cint(c, a=1.0):
    r, g, b = rgb(c)
    return skia.Color(int(r * 255 + .5), int(g * 255 + .5), int(b * 255 + .5), int(max(0, min(1, a)) * 255 + .5))


_CAPS = {"butt": skia.Paint.kButt_Cap, "round": skia.Paint.kRound_Cap, "square": skia.Paint.kSquare_Cap}


def P(color="#ffffff", a=1.0, stroke=0.0, blend=None, blur=0.0, cap="butt", shader=None,
      effect=None, aa=True, join=None):
    """One-call paint. stroke > 0 makes a stroke paint of that width."""
    p = skia.Paint()
    p.setAntiAlias(aa)
    p.setColor4f(c4(color, a))
    if stroke > 0:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(_CAPS[cap])
        if join == "round":
            p.setStrokeJoin(skia.Paint.kRound_Join)
    if blend is not None:
        p.setBlendMode(blend)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
    if effect is not None:
        p.setPathEffect(effect)
    return p


ADD = skia.BlendMode.kPlus
SCREEN = skia.BlendMode.kScreen
MULT = skia.BlendMode.kMultiply
DIFF = skia.BlendMode.kDifference
CLEAR = skia.BlendMode.kClear
DST_IN = skia.BlendMode.kDstIn
DST_OUT = skia.BlendMode.kDstOut
SRC_IN = skia.BlendMode.kSrcIn
XOR = skia.BlendMode.kXor


def linear_grad(x0, y0, x1, y1, colors, stops=None, alphas=None):
    alphas = alphas or [1.0] * len(colors)
    cols = [cint(c, a) for c, a in zip(colors, alphas)]
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, stops)


def radial_grad(x, y, r, colors, stops=None, alphas=None):
    alphas = alphas or [1.0] * len(colors)
    cols = [cint(c, a) for c, a in zip(colors, alphas)]
    return skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 1e-3), cols, stops)


def trim(start, end):
    start, end = max(0.0, min(1.0, start)), max(0.0, min(1.0, end))
    if end <= start:
        return skia.TrimPathEffect.Make(0.0, 0.0)
    return skia.TrimPathEffect.Make(start, end)


def dash(on, off, phase=0.0):
    return skia.DashPathEffect.Make([on, off], phase)


# ---------------------------------------------------------------- layers

@contextmanager
def layer(c, alpha=1.0, blend=None, blur=0.0, blur_xy=None, bounds=None):
    p = skia.Paint()
    p.setAlphaf(max(0.0, min(1.0, alpha)))
    if blend is not None:
        p.setBlendMode(blend)
    if blur_xy is not None:
        bx, by = blur_xy
        if bx > 0.05 or by > 0.05:
            p.setImageFilter(skia.ImageFilters.Blur(max(bx, 0.0), max(by, 0.0)))
    elif blur > 0.05:
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    c.saveLayer(bounds, p)
    try:
        yield c
    finally:
        c.restore()


@contextmanager
def xf(c, x=0.0, y=0.0, s=1.0, rot=0.0, sx=None, sy=None, px=0.0, py=0.0, skx=0.0):
    """Translate to (x, y), then rotate/scale/skew around the local pivot (px, py)."""
    c.save()
    c.translate(x, y)
    if rot or s != 1.0 or sx is not None or sy is not None or skx:
        c.translate(px, py)
        if rot:
            c.rotate(rot)
        if skx:
            c.skew(skx, 0)
        c.scale(sx if sx is not None else s, sy if sy is not None else s)
        c.translate(-px, -py)
    try:
        yield c
    finally:
        c.restore()


@contextmanager
def clip_rect(c, x, y, w, h):
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h), skia.ClipOp.kIntersect, True)
    try:
        yield c
    finally:
        c.restore()


# ---------------------------------------------------------------- shapes

def rect(c, x, y, w, h, paint):
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint)


def rrect(c, x, y, w, h, r, paint):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint)


def circle(c, x, y, r, paint):
    if r > 0:
        c.drawCircle(x, y, r, paint)


def line(c, x0, y0, x1, y1, paint):
    c.drawLine(x0, y0, x1, y1, paint)


def poly(points, closed=True):
    path = skia.Path()
    if len(points) == 0:
        return path
    path.moveTo(float(points[0][0]), float(points[0][1]))
    for x, y in points[1:]:
        path.lineTo(float(x), float(y))
    if closed:
        path.close()
    return path


def arc_path(cx, cy, r, start_deg, sweep_deg):
    path = skia.Path()
    path.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), start_deg, sweep_deg)
    return path


def star_points(n, r_out, r_in, rot=-90.0, cx=0.0, cy=0.0):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180.0 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def resample_closed(points, n):
    """Evenly resample a closed polyline to n points (for shape morphing)."""
    pts = np.asarray(points, dtype=np.float64)
    seg = np.roll(pts, -1, axis=0) - pts
    lens = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(lens)])
    total = cum[-1]
    out = np.empty((n, 2))
    for k in range(n):
        d = total * k / n
        i = min(np.searchsorted(cum, d, side="right") - 1, len(pts) - 1)
        u = (d - cum[i]) / lens[i] if lens[i] > 0 else 0.0
        out[k] = pts[i] + seg[i] * u
    return out


# ---------------------------------------------------------------- typography

def _tag(s):
    return (ord(s[0]) << 24) | (ord(s[1]) << 16) | (ord(s[2]) << 8) | ord(s[3])


class _Family:
    def __init__(self, filename):
        self.path = str(FONT_DIR / filename)
        self.sk = skia.Typeface.MakeFromFile(self.path)
        self.face = hb.Face(hb.Blob.from_file_path(self.path))
        self.upem = self.face.upem
        self.axes = {}
        for a in (self.sk.getVariationDesignParameters() or []):
            tag = "".join(chr((a.tag >> s) & 0xFF) for s in (24, 16, 8, 0))
            self.axes[tag] = (a.min, getattr(a, "def"), a.max)
        self._inst = OrderedDict()

    def instance(self, axes):
        key = []
        for k, v in sorted(axes.items()):
            if k in self.axes:
                lo, _, hi = self.axes[k]
                key.append((k, round(max(lo, min(hi, float(v))), 1)))
        key = tuple(key)
        hit = self._inst.get(key)
        if hit is not None:
            self._inst.move_to_end(key)
            return hit
        if key:
            VP = skia.FontArguments.VariationPosition
            coords = VP.Coordinates([VP.Coordinate(_tag(k), v) for k, v in key])
            fa = skia.FontArguments()
            fa.setVariationDesignPosition(VP(coords))
            tf = self.sk.makeClone(fa)
        else:
            tf = self.sk
        hbf = hb.Font(self.face)
        if key:
            hbf.set_variations(dict(key))
        self._inst[key] = (tf, hbf, key)
        if len(self._inst) > 600:
            self._inst.popitem(last=False)
        return self._inst[key]


_FAMS = {}


def family(name):
    f = _FAMS.get(name)
    if f is None:
        f = _FAMS[name] = _Family(FAMILIES[name])
    return f


_BLOBS = OrderedDict()


class Font:
    """A sized, variation-instanced font with HarfBuzz shaping (kerning included)."""

    def __init__(self, fam, size, **axes):
        self.fam = family(fam)
        self.name = fam
        self.tf, self.hbf, self.key = self.fam.instance(axes)
        self.size = float(size)
        sk = skia.Font(self.tf, self.size)
        sk.setSubpixel(True)
        sk.setLinearMetrics(True)
        sk.setEdging(skia.Font.Edging.kAntiAlias)
        sk.setHinting(skia.FontHinting.kNone)
        self.sk = sk
        self.scale = self.size / self.fam.upem
        m = sk.getMetrics()
        self.asc = -m.fAscent
        self.desc = m.fDescent
        self.cap = m.fCapHeight if m.fCapHeight > 0 else self.size * 0.7
        self.xh = m.fXHeight if m.fXHeight > 0 else self.size * 0.5

    def shape(self, text, tracking=0.0, features=None):
        """tracking is in em (0.1 = 10% of the font size added after each glyph).
        features adds OpenType features, e.g. {"tnum": True} for tabular figures."""
        if not text:
            return Run(self, [], [], [], 0.0, text)
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": True, **(features or {})})
        gids, xs, adv = [], [], []
        x = 0.0
        tr = tracking * self.size
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            gids.append(info.codepoint)
            xs.append(x + pos.x_offset * self.scale)
            a = pos.x_advance * self.scale
            adv.append(a)
            x += a + tr
        width = x - tr if gids else 0.0
        return Run(self, gids, xs, adv, width, text)

    def width(self, text, tracking=0.0, features=None):
        return self.shape(text, tracking, features).width

    def glyph_blob(self, gid):
        k = (self.name, self.key, self.size, gid)
        b = _BLOBS.get(k)
        if b is None:
            bld = skia.TextBlobBuilder()
            bld.allocRunPos(self.sk, [gid], [skia.Point(0, 0)])
            b = _BLOBS[k] = bld.make()
            if len(_BLOBS) > 4000:
                _BLOBS.popitem(last=False)
        return b

    def glyph_path(self, gid):
        return self.sk.getPath(gid)


class Run:
    def __init__(self, font, gids, xs, adv, width, text):
        self.font, self.gids, self.xs, self.adv, self.width, self.text = font, gids, xs, adv, width, text

    def blob(self):
        if not self.gids:
            return None
        bld = skia.TextBlobBuilder()
        bld.allocRunPos(self.font.sk, self.gids, [skia.Point(x, 0) for x in self.xs])
        return bld.make()

    def draw(self, c, x, y, paint):
        b = self.blob()
        if b is not None:
            c.drawTextBlob(b, x, y, paint)

    def path(self, x=0.0, y=0.0):
        out = skia.Path()
        for gid, gx in zip(self.gids, self.xs):
            gp = self.font.glyph_path(gid)
            if gp is not None:
                out.addPath(gp, x + gx, y)
        return out

    def glyphs(self):
        """(index, gid, x, advance) per glyph, for per-letter animation."""
        return list(zip(range(len(self.gids)), self.gids, self.xs, self.adv))


def baseline_for(font, y, anchor):
    if anchor == "cap":        # y is the vertical centre of the capitals
        return y + font.cap / 2
    if anchor == "x":          # y is the centre of the x-height
        return y + font.xh / 2
    if anchor == "top":        # y is the top of the capitals
        return y + font.cap
    return y                   # baseline


def text(c, s, x, y, font, paint, align=0.0, tracking=0.0, anchor="baseline", features=None):
    run = font.shape(s, tracking, features)
    run.draw(c, x - run.width * align, baseline_for(font, y, anchor), paint)
    return run


def glyph(c, font, gid, x, y, paint):
    c.drawTextBlob(font.glyph_blob(gid), x, y, paint)


SCRAMBLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&*+=/<>"


def scramble(s, p, seed=0, t=0.0, charset=SCRAMBLE):
    """Decode effect: characters resolve left to right as p goes 0 -> 1."""
    out = []
    n = max(len(s), 1)
    for i, ch in enumerate(s):
        if ch == " ":
            out.append(" ")
            continue
        lock = (i + 1) / n
        if p >= lock:
            out.append(ch)
        elif p >= lock - 0.35:
            k = int(t * 30 + i * 7 + seed) % len(charset)
            out.append(charset[k])
        else:
            out.append(" " if p < 0.02 else "·")
    return "".join(out)


# ---------------------------------------------------------------- images

def image_from_rgba(arr):
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.ColorType.kRGBA_8888_ColorType)


def draw_image(c, img, x, y, w, h, alpha=1.0):
    p = skia.Paint()
    p.setAlphaf(alpha)
    c.drawImageRect(img, skia.Rect.MakeXYWH(x, y, w, h),
                    skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)


# ---------------------------------------------------------------- SVG path data

import re as _re

_NUM = _re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


def svg_path(d):
    """Parse SVG path data (every command, absolute and relative, arcs included) into a skia.Path."""
    p = skia.Path()
    i, n = 0, len(d)
    cmd = None
    x = y = sx = sy = 0.0
    lcx = lcy = None      # last cubic control point, for S
    lqx = lqy = None      # last quadratic control point, for T

    def skip():
        nonlocal i
        while i < n and d[i] in " ,\t\n\r":
            i += 1

    def num():
        nonlocal i
        skip()
        m = _NUM.match(d, i)
        if not m:
            raise ValueError(f"number expected at {i}: {d[i:i + 12]!r}")
        i = m.end()
        return float(m.group())

    def flag():
        nonlocal i
        skip()
        ch = d[i]
        i += 1
        return ch == "1"

    while True:
        skip()
        if i >= n:
            break
        if d[i].isalpha():
            cmd = d[i]
            i += 1
        elif cmd is None:
            raise ValueError("path must start with a command")
        rel = cmd.islower()
        C = cmd.upper()
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if C == "Z":
            p.close()
            x, y = sx, sy
            lcx = lqx = None
            continue
        if C == "M":
            x, y = ox + num(), oy + num()
            p.moveTo(x, y)
            sx, sy = x, y
            cmd = "l" if rel else "L"
            lcx = lqx = None
        elif C == "L":
            x, y = ox + num(), oy + num()
            p.lineTo(x, y)
            lcx = lqx = None
        elif C == "H":
            x = ox + num()
            p.lineTo(x, y)
            lcx = lqx = None
        elif C == "V":
            y = oy + num()
            p.lineTo(x, y)
            lcx = lqx = None
        elif C == "C":
            x1, y1, x2, y2 = ox + num(), oy + num(), ox + num(), oy + num()
            x, y = ox + num(), oy + num()
            p.cubicTo(x1, y1, x2, y2, x, y)
            lcx, lcy, lqx = x2, y2, None
        elif C == "S":
            x1, y1 = (2 * x - lcx, 2 * y - lcy) if lcx is not None else (x, y)
            x2, y2 = ox + num(), oy + num()
            x, y = ox + num(), oy + num()
            p.cubicTo(x1, y1, x2, y2, x, y)
            lcx, lcy, lqx = x2, y2, None
        elif C == "Q":
            x1, y1 = ox + num(), oy + num()
            x, y = ox + num(), oy + num()
            p.quadTo(x1, y1, x, y)
            lqx, lqy, lcx = x1, y1, None
        elif C == "T":
            x1, y1 = (2 * x - lqx, 2 * y - lqy) if lqx is not None else (x, y)
            x, y = ox + num(), oy + num()
            p.quadTo(x1, y1, x, y)
            lqx, lqy, lcx = x1, y1, None
        elif C == "A":
            rx, ry, rot = num(), num(), num()
            large, sweep = flag(), flag()
            x, y = ox + num(), oy + num()
            p.arcTo(rx, ry, rot,
                    skia.Path.ArcSize.kLarge_ArcSize if large else skia.Path.ArcSize.kSmall_ArcSize,
                    skia.PathDirection.kCW if sweep else skia.PathDirection.kCCW, x, y)
            lcx = lqx = None
        else:
            raise ValueError(f"unknown command {cmd}")
    return p


def light_sweep(c, draw_fn, x0, x1, y, u, colors=("#ffffff",), width=260, angle=20.0, strength=0.9):
    """CC Light Sweep: a bright diagonal band that passes over whatever draw_fn paints, and only over it.
    u runs 0 -> 1 as the band travels from x0 to x1."""
    if not 0.0 < u < 1.0:
        draw_fn(c)
        return
    with layer(c):
        draw_fn(c)
        cx = x0 + (x1 - x0) * u
        dx = math.cos(math.radians(angle)) * width
        dy = math.sin(math.radians(angle)) * width
        cols = list(colors)
        if len(cols) == 1:
            cols = [cols[0]] * 3
        stops = [i / (len(cols) + 1) for i in range(1, len(cols) + 1)]
        sh = skia.GradientShader.MakeLinear(
            [skia.Point(cx - dx, y - dy), skia.Point(cx + dx, y + dy)],
            [cint(cols[0], 0.0)] + [cint(col, strength) for col in cols] + [cint(cols[-1], 0.0)],
            [0.0] + stops + [1.0])
        p = skia.Paint()
        p.setShader(sh)
        p.setBlendMode(skia.BlendMode.kSrcATop)
        c.drawPaint(p)
