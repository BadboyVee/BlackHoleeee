"""Sakura textures, modelled as real geometry in Blender and rendered with Cycles.

Nothing here is painted. Every blossom is built from five notched, cupped,
veined petals around a calyx, a ring of stamens with anthers and a pistil;
blossoms and buds hang on pedicels from umbels that spiral up a twig, with a
few young bronze leaves. The pieces are laid out on one atlas and rendered
straight down with an orthographic camera, in three passes:

    albedo   vertex colours through an emission shader      -> colour, coverage
    normal   shading normal                                 -> tangent-space normal
    data     translucency (per part) and ambient occlusion  -> shading inputs

None of the textures carries an alpha channel (coverage is the red channel of
the mask), so no browser can premultiply the colour away at the petal edges.

The atlas (1.2 m of world on a side):

    sleeves      a twig flowering all the way round, 30 cm and 15 cm long:
                 the cards that follow every twig of the tree
    fans, bushes forked sprays, for the ends of branches
    umbels       one cluster at twice the size, for blossoms seen close
    blossoms     single flowers, face on
    petals       four loose petals, and a scatter of fallen ones

The same run makes the other surfaces:

    bark    a cherry trunk tile: plates split by furrows, rows of lenticels,
            lichen and moss. The height field is built from periodic fields,
            then raised as real geometry and rendered for its normals and
            occlusion.
    grass   a tileable square of turf: fourteen thousand curled blades and
            clover over soil, rendered from above.
    soil, stone   periodic fields (numpy).

Outputs:

    assets/textures.js      everything the page needs, as data URIs
                            (so index.html works from file:// as well)
    tools/blender/out/      the same textures as .webp plus previews (ignored by git)

usage, either with the `bpy` module or the Blender app:

    python tools/blender/build_assets.py [--fast] [blossoms bark grass soil stone]
    blender -b --python tools/blender/build_assets.py
"""

import base64
import io
import json
import math
import os
import sys
import tempfile
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ASSETS = os.path.join(ROOT, 'assets')
OUT = os.path.join(HERE, 'out')

FAST = '--fast' in sys.argv
GRID = 4
CELL = 0.30
ATLAS = GRID * CELL                  # metres of world the atlas covers
PX = 1024 if FAST else 2048          # colour atlas
PX_DATA = 512 if FAST else 1024      # normal / occlusion / translucency atlas
BARK_PX = 1024 if FAST else 2048
GRASS_PX = 512 if FAST else 1024
PIVOT_Y = 0.008                      # a twig enters its cell this far above the bottom edge
AO_DIST = 0.011

TAU = math.tau


def rng(seed):
    return np.random.default_rng(seed)


def lin(hexstr):
    """'#rrggbb' (sRGB) -> linear rgb."""
    h = hexstr.lstrip('#')
    c = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def to_u8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = np.asarray(t, np.float64)
    if t.ndim:
        t = t[..., None]
    return np.asarray(a) * (1 - t) + np.asarray(b) * t


# ------------------------------------------------------------------ palette
PETAL_TIP = lin('#fff7fa')
PETAL_MID = lin('#ffe4ed')
PETAL_BASE = lin('#f5a6c1')
PETAL_CLAW = lin('#dc6a93')
PETAL_VEIN = lin('#f8bccf')
PETAL_PINK = lin('#ffc6d9')       # a pinker blossom
PETAL_WHITE = lin('#fffbfc')      # a paler one
THROAT_FRESH = lin('#e9dd8e')
THROAT_AGED = lin('#c93a66')
FILAMENT = lin('#fff2f4')
FILAMENT_AGED = lin('#f08fae')
ANTHER = lin('#f7d453')
ANTHER_OLD = lin('#c98529')
PISTIL = lin('#cfe2a2')
CALYX = lin('#8a2d47')
CALYX_GREEN = lin('#6f6a34')
PEDICEL_GREEN = lin('#8a9c41')
PEDICEL_RED = lin('#9a4d47')
BUD_TIP = lin('#e2507f')
BUD_BASE = lin('#f9bcd1')
BUD_OPENING = lin('#ffd9e6')
TWIG = lin('#4a3833')
TWIG_LIGHT = lin('#77655c')
SCALE = lin('#6b4632')
LEAF_GREEN = lin('#a2b94f')
LEAF_BRONZE = lin('#b9783c')
LEAF_RIB = lin('#6f7f2e')


# ------------------------------------------------------------------ geometry soup
class Soup:
    """Accumulates one big mesh: positions, faces, albedo and per-vertex data."""

    def __init__(self):
        self.v, self.q, self.t, self.c, self.d = [], [], [], [], []
        self.n = 0

    def add(self, verts, quads=None, tris=None, cols=None, trans=1.0, scale=1.0):
        verts = np.asarray(verts, np.float32).reshape(-1, 3)
        k = len(verts)
        cols = np.asarray(cols, np.float32)
        if cols.ndim == 1:
            cols = np.broadcast_to(cols, (k, 3))
        self.v.append(verts)
        self.c.append(cols.astype(np.float32))
        d = np.zeros((k, 3), np.float32)
        d[:, 0] = trans
        d[:, 1] = scale
        self.d.append(d)
        if quads is not None and len(quads):
            self.q.append(np.asarray(quads, np.int32).reshape(-1, 4) + self.n)
        if tris is not None and len(tris):
            self.t.append(np.asarray(tris, np.int32).reshape(-1, 3) + self.n)
        self.n += k

    def build(self, name):
        v = np.concatenate(self.v)
        q = np.concatenate(self.q) if self.q else np.zeros((0, 4), np.int32)
        t = np.concatenate(self.t) if self.t else np.zeros((0, 3), np.int32)
        c = np.concatenate(self.c)
        d = np.concatenate(self.d)
        me = bpy.data.meshes.new(name)
        me.vertices.add(len(v))
        me.vertices.foreach_set('co', v.ravel())
        loops = np.concatenate([q.ravel(), t.ravel()]).astype(np.int32)
        starts = np.concatenate([np.arange(len(q)) * 4, len(q) * 4 + np.arange(len(t)) * 3]).astype(np.int32)
        me.loops.add(len(loops))
        me.polygons.add(len(starts))
        me.loops.foreach_set('vertex_index', loops)
        me.polygons.foreach_set('loop_start', starts)
        me.update(calc_edges=True)
        me.validate()
        me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
        for attr, data, w in (('Col', c, 1.0), ('Dat', d, 1.0)):
            ca = me.color_attributes.new(attr, 'FLOAT_COLOR', 'POINT')
            rgba = np.concatenate([data, np.full((len(data), 1), w, np.float32)], 1)
            ca.data.foreach_set('color', rgba.ravel())
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


# ------------------------------------------------------------------ transforms
def translate(p):
    m = np.eye(4)
    m[:3, 3] = p
    return m


def scale_m(s):
    m = np.eye(4)
    m[0, 0] = m[1, 1] = m[2, 2] = s
    return m


def rot(axis, ang):
    axis = np.asarray(axis, np.float64)
    axis = axis / np.linalg.norm(axis)
    x, y, z = axis
    c, s = math.cos(ang), math.sin(ang)
    m = np.eye(4)
    m[:3, :3] = [[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                 [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                 [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]]
    return m


RX = lambda a: rot((1, 0, 0), a)
RY = lambda a: rot((0, 1, 0), a)
RZ = lambda a: rot((0, 0, 1), a)


def unit(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v) + 1e-12)


def perp(d):
    """Two unit vectors orthogonal to d."""
    d = unit(d)
    a = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = unit(np.cross(a, d))
    return e1, np.cross(d, e1)


def frame(origin, z, roll=0.0):
    """Matrix placing a local +Z-up object at `origin` with +Z along `z`."""
    z = unit(z)
    e1, e2 = perp(z)
    x = e1 * math.cos(roll) + e2 * math.sin(roll)
    y = np.cross(z, x)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, z, origin
    return m


def xf(m, v):
    v = np.asarray(v, np.float64).reshape(-1, 3)
    return v @ m[:3, :3].T + m[:3, 3]


# ------------------------------------------------------------------ primitives
def grid_quads(rows, cols, wrap=False):
    i, j = np.meshgrid(np.arange(rows - 1), np.arange(cols if wrap else cols - 1), indexing='ij')
    a = i * cols + j
    b = i * cols + (j + 1) % cols
    return np.stack([a, b, b + cols, a + cols], -1).reshape(-1, 4)


def tube(points, radii, sides=5):
    """Tube along a polyline (parallel transport). Returns verts, quads, tip tris, ring index per vertex."""
    p = np.asarray(points, np.float64)
    n = len(p)
    radii = np.broadcast_to(np.asarray(radii, np.float64), (n,))
    tan = np.gradient(p, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-12
    e1, _ = perp(tan[0])
    ang = np.arange(sides) * TAU / sides
    verts = np.zeros((n, sides, 3))
    for i in range(n):
        e1 = unit(e1 - tan[i] * np.dot(e1, tan[i]))
        e2 = np.cross(tan[i], e1)
        verts[i] = p[i] + radii[i] * (np.cos(ang)[:, None] * e1 + np.sin(ang)[:, None] * e2)
    quads = grid_quads(n, sides, wrap=True)
    verts = np.concatenate([verts.reshape(-1, 3), p[-1:]])           # closing point
    last = (n - 1) * sides
    tris = np.array([[last + k, last + (k + 1) % sides, n * sides] for k in range(sides)])
    ring = np.concatenate([np.repeat(np.arange(n), sides), [n - 1]])
    return verts, quads, tris, ring


def revolve(z, r, sides=8):
    """Surface of revolution around +Z, closed at both ends."""
    z = np.asarray(z, np.float64)
    r = np.asarray(r, np.float64)
    ang = np.arange(sides) * TAU / sides
    v = np.stack([r[:, None] * np.cos(ang), r[:, None] * np.sin(ang), np.broadcast_to(z[:, None], (len(z), sides))], -1)
    return v.reshape(-1, 3), grid_quads(len(z), sides, wrap=True)


OCTA_V = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]], np.float64)
OCTA_T = np.array([[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4], [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5]])


# ------------------------------------------------------------------ petal
def petal_mesh(g, L=0.0170, W=0.0138, notch=0.10, cup=1.0, tint=0.0, nu=11, nt=14):
    """One petal: base at the origin, growing along +Y, upper face +Z.

    The outline is w(t) across, cut at the tip by a smooth V (the notch that
    makes a cherry petal a cherry petal). Columns of the grid run from the claw
    to the tip, which is also how the veins run.
    """
    u = np.linspace(-1, 1, nu)

    tm = 0.60

    def w(t):
        t = np.clip(t, 0, 1)
        lower = np.sin(np.pi / 2 * np.clip(t / tm, 0, 1) ** 1.1)
        upper = (1 - np.clip((t - tm) / (1 - tm), 0, 1) ** 2.3) ** (1 / 2.3)
        return np.where(t <= tm, lower, upper)

    s, e = 0.62, 0.035
    lo, hi = np.full(nu, 0.5), np.ones(nu)
    for _ in range(26):
        mid = (lo + hi) / 2
        f = mid - ((1 - notch) + s * (np.sqrt((u * w(mid)) ** 2 + e * e) - e))
        hi = np.where(f > 0, mid, hi)
        lo = np.where(f > 0, lo, mid)
    T = (lo + hi) / 2
    tau = 0.015 + 0.985 * (1 - (1 - np.linspace(0, 1, nt)) ** 1.8)      # more rows where the outline turns
    t = tau[:, None] * T[None, :]
    uu = np.broadcast_to(u[None, :], t.shape)
    xh = uu * w(t)
    x = xh * W / 2
    y = t * L
    ph1, ph2 = g.uniform(0, TAU, 2)
    z = L * (cup * 0.26 * t ** 1.6
             + cup * 0.42 * xh ** 2 * (0.3 + 0.7 * t) * (W / L)
             + 0.035 * np.sin(uu * 5.5 + ph1) * t ** 3
             + 0.022 * np.sin(t * 9 + ph2) * np.abs(uu) * t
             - 0.03 * np.exp(-(uu / 0.14) ** 2) * np.sin(np.pi * np.minimum(t * 1.1, 1)))
    verts = np.stack([x, y, z], -1).reshape(-1, 3)

    tip = mix(PETAL_TIP, PETAL_PINK, max(tint, 0)) if tint >= 0 else mix(PETAL_TIP, PETAL_WHITE, -tint)
    mid_c = mix(PETAL_MID, PETAL_PINK, max(tint, 0) * 0.8) if tint >= 0 else mix(PETAL_MID, PETAL_WHITE, -tint * 0.7)
    c = mix(PETAL_CLAW, PETAL_BASE, smooth(0.0, 0.14, t))
    c = mix(c, mid_c, smooth(0.06, 0.46, t))
    c = mix(c, tip, smooth(0.38, 1.0, t))
    vein = (0.5 + 0.5 * np.cos(uu * np.pi * 8)) ** 8 * smooth(0.05, 0.3, t) * (1 - smooth(0.62, 0.98, t)) * 0.32
    c = mix(c, PETAL_VEIN, vein)
    c = mix(c, PETAL_PINK, smooth(0.72, 1.0, np.abs(uu)) * 0.16)
    return verts, grid_quads(nt, nu), c.reshape(-1, 3)


def add_petal(soup, g, m, sc=1.0, **kw):
    if 'nu' not in kw:
        kw['nu'], kw['nt'] = (9, 12) if sc < 1.5 else (13, 16) if sc < 3 else (23, 26)
    v, q, c = petal_mesh(g, **kw)
    soup.add(xf(m, v), quads=q, cols=c, trans=1.0, scale=sc)


# ------------------------------------------------------------------ blossom
def blossom(soup, g, m, openness=1.0, aged=0.0, tint=0.0, sc=1.0):
    """A cherry blossom at the origin of `m`, facing +Z."""
    a0 = g.uniform(0, TAU)
    tilt0 = math.radians(19 + (1 - openness) * 46)
    for k in range(5):
        ang = a0 + k * TAU / 5 + g.normal(0, 0.05)
        mp = RZ(ang) @ translate((0, 0.0011, 0.0002 * k)) @ RX(tilt0 + g.normal(0, 0.05)) @ RY(math.radians(6) + g.normal(0, 0.03))
        add_petal(soup, g, m @ mp, sc, L=0.0170 * g.uniform(0.93, 1.07), W=0.0138 * g.uniform(0.93, 1.07),
                  notch=g.uniform(0.08, 0.13), cup=g.uniform(0.7, 1.25) * (1.5 - 0.5 * openness), tint=tint + g.normal(0, 0.06))

    # calyx tube and sepals (seen from behind and from the side)
    zc = np.array([-0.0068, -0.0052, -0.0030, -0.0010, 0.0002])
    rc = np.array([0.00055, 0.00125, 0.00195, 0.00235, 0.0024])
    v, q = revolve(zc, rc, 8)
    cc = mix(CALYX_GREEN, CALYX, smooth(-0.0068, -0.003, v[:, 2]))
    soup.add(xf(m, v), quads=q, cols=cc, trans=0.2, scale=sc)
    for k in range(5):
        ang = a0 + (k + 0.5) * TAU / 5
        tt = np.linspace(0, 1, 4)
        ww = 0.0013 * (1 - tt ** 1.5)
        sv = np.concatenate([np.stack([-ww, 0.0018 + tt * 0.0056, -0.0006 * tt], -1), np.stack([ww, 0.0018 + tt * 0.0056, -0.0006 * tt], -1)])
        sq = np.array([[i, i + 4, i + 5, i + 1] for i in range(3)])
        soup.add(xf(m @ RZ(ang) @ RX(math.radians(-6)), sv), quads=sq, cols=mix(CALYX, CALYX_GREEN, 0.25), trans=0.3, scale=sc)

    # throat
    ang = np.arange(10) * TAU / 10
    tv = np.concatenate([[[0, 0, 0.0007]], np.stack([0.0021 * np.cos(ang), 0.0021 * np.sin(ang), np.full(10, 0.0004)], -1)])
    tt = np.array([[0, 1 + i, 1 + (i + 1) % 10] for i in range(10)])
    throat = mix(THROAT_FRESH, THROAT_AGED, aged)
    soup.add(xf(m, tv), tris=tt, cols=throat, trans=0.4, scale=sc)

    # stamens
    fil_c = mix(FILAMENT, FILAMENT_AGED, aged * 0.8)
    for _ in range(int(g.integers(24, 32))):
        az = g.uniform(0, TAU)
        pol = math.radians(8 + 44 * g.uniform(0, 1) ** 0.7)
        ln = g.uniform(0.0056, 0.0086) * (1 - 0.2 * pol)
        radial = np.array([math.cos(az), math.sin(az), 0.0])
        d = radial * math.sin(pol) + np.array([0, 0, math.cos(pol)])
        s = np.linspace(0, 1, 4)[:, None]
        pts = radial * 0.0010 + np.array([0, 0, 0.0004]) + d * ln * s - radial * 0.0009 * s ** 2
        v, q, t, _ = tube(pts, 0.00017, 3)
        soup.add(xf(m, v), quads=q, tris=t, cols=mix(fil_c, FILAMENT, 0.3), trans=0.6, scale=sc)
        ma = frame(pts[-1], unit(pts[-1] - pts[-2]), g.uniform(0, TAU))
        av = OCTA_V * np.array([0.00052, 0.00042, 0.00088])
        soup.add(xf(m @ ma, av), tris=OCTA_T, cols=mix(ANTHER, ANTHER_OLD, g.uniform(0, 1) ** 2 * (0.4 + 0.6 * aged)), trans=0.3, scale=sc)

    # pistil
    s = np.linspace(0, 1, 4)[:, None]
    bend = np.array([g.normal(0, 0.0006), g.normal(0, 0.0006), 0])
    pts = np.array([0, 0, 0.0005]) + np.array([0, 0, 0.0088]) * s + bend * s ** 2
    v, q, t, _ = tube(pts, 0.00028, 4)
    soup.add(xf(m, v), quads=q, tris=t, cols=PISTIL, trans=0.5, scale=sc)
    soup.add(xf(m @ translate(pts[-1]), OCTA_V * 0.00055), tris=OCTA_T, cols=mix(PISTIL, ANTHER, 0.4), trans=0.4, scale=sc)


def bud(soup, g, m, stage=0.5, sc=1.0):
    """A flower bud at the origin of `m`, pointing along +Z."""
    Lb = 0.0092 + 0.0048 * stage
    Rb = 0.0031 + 0.0019 * stage
    rings, sides = 10, 9
    s = np.linspace(0, 1, rings)
    r = Rb * np.sin(np.pi * (0.05 + 0.95 * s) ** 0.85) ** 0.8
    r[-1] = Rb * 0.04
    v, q = revolve(s * Lb, r, sides)
    ss = np.repeat(s, sides)
    th = np.tile(np.arange(sides) * TAU / sides, rings)
    c = mix(BUD_BASE, BUD_TIP, ss ** 0.8)
    c = mix(c, BUD_OPENING, smooth(0.55, 1.0, ss) * max(stage - 0.45, 0) * 1.8)
    # swirl of the furled petals
    c = mix(c, BUD_TIP, (0.5 + 0.5 * np.cos(th * 2.5 + ss * 5)) ** 3 * 0.25 * smooth(0.3, 0.6, ss))
    # calyx with five sepal points climbing the bud
    edge = 0.30 + 0.22 * np.abs(np.cos(th * 2.5)) ** 1.5
    cal = 1 - smooth(edge - 0.06, edge + 0.02, ss)
    c = mix(c, mix(CALYX, CALYX_GREEN, 0.3), cal)
    v[:, :2] *= (1 + 0.07 * cal)[:, None]
    soup.add(xf(m, v), quads=q, cols=c, trans=0.45, scale=sc)


def pedicel(soup, g, a, b, sc=1.0, r=0.00045):
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    d = b - a
    e1, e2 = perp(d)
    off = (e1 * g.normal(0, 0.12) + e2 * g.normal(0, 0.12)) * np.linalg.norm(d)
    s = np.linspace(0, 1, 6)[:, None]
    pts = a + d * s + off * (4 * s * (1 - s))
    v, q, t, ring = tube(pts, r * (1 + 0.35 * np.linspace(0, 1, 6) ** 3), 4)
    k = g.uniform(0, 1)
    c = mix(mix(PEDICEL_GREEN, PEDICEL_RED, k), CALYX_GREEN, (ring / 5.0) ** 2 * 0.5)
    soup.add(v, quads=q, tris=t, cols=c, trans=0.25, scale=sc)
    return unit(pts[-1] - pts[-2])


def leaf(soup, g, m, L=0.032, bronze=0.4, sc=1.0, col=None):
    """A young leaf: base at the origin, along +Y, folded on the midrib."""
    nu, nt = 7, 10
    u = np.linspace(-1, 1, nu)
    t = np.linspace(0.02, 1, nt)[:, None]
    w = (np.sin(np.pi * t ** 0.8) ** 0.9) * (1 - 0.35 * t ** 3) * L * 0.21
    x = u[None, :] * w
    y = np.broadcast_to(t * L, x.shape)
    fold = g.uniform(0.25, 0.7)
    z = np.abs(x) * fold + L * 0.18 * t ** 2 * g.uniform(-0.6, 1.0) + L * 0.02 * np.sin(u[None, :] * 9 + t * 14) * t
    verts = np.stack([x, y, z], -1).reshape(-1, 3)
    if col is None:
        c = mix(LEAF_GREEN, LEAF_BRONZE, np.clip(bronze + 0.35 * np.abs(u[None, :]) * np.ones_like(t) - 0.2 * (1 - t), 0, 1))
        c = mix(c, LEAF_RIB, np.exp(-(u[None, :] / 0.16) ** 2) * np.ones_like(t) * 0.6)
        side = (0.5 + 0.5 * np.cos(t * 26 + np.abs(u[None, :]) * 9)) ** 6 * 0.22
        c = mix(c, LEAF_RIB, side)
    else:
        c = np.broadcast_to(col, (nt, nu, 3))
    soup.add(xf(m, verts), quads=grid_quads(nt, nu), cols=np.asarray(c).reshape(-1, 3), trans=0.7, scale=sc)


# ------------------------------------------------------------------ umbel / spray
def umbel(soup, g, base, axis, n, sc=1.0, p_bud=0.2, aged_p=0.35, tint=0.0, inside=None, leaves=0, ped=(0.020, 0.032)):
    """Flowers on pedicels from one point, like spokes of a little umbrella."""
    base = np.asarray(base, np.float64)
    axis = unit(axis)
    e1, e2 = perp(axis)
    ph = g.uniform(0, TAU)
    for i in range(n):
        az = ph + i * TAU / n + g.uniform(-0.4, 0.4)
        pol = math.radians(g.uniform(16, 64))
        d = axis * math.cos(pol) + (e1 * math.cos(az) + e2 * math.sin(az)) * math.sin(pol)
        end = base + d * g.uniform(*ped)
        if inside is not None and not inside(end):
            continue
        tan = pedicel(soup, g, base, end, sc)
        fz = unit(tan + axis * 0.15 + g.normal(0, 0.12, 3))
        mf = frame(end + fz * 0.0066, fz, g.uniform(0, TAU))
        if g.uniform() < p_bud:
            bud(soup, g, frame(end, fz, g.uniform(0, TAU)), stage=g.uniform(0, 1), sc=sc)
        else:
            blossom(soup, g, mf, openness=g.uniform(0.72, 1.0), aged=float(g.uniform() < aged_p) * g.uniform(0.6, 1.0),
                    tint=tint + g.normal(0, 0.15), sc=sc)
    # bud scales at the foot of the umbel
    for i in range(3):
        d = unit(axis + (e1 * math.cos(i * 2.1 + ph) + e2 * math.sin(i * 2.1 + ph)) * 0.9)
        leaf(soup, g, frame(base, d, g.uniform(0, TAU)) @ RX(math.radians(90)), L=g.uniform(0.004, 0.0065), sc=sc, col=mix(SCALE, PEDICEL_RED, 0.3))
    for i in range(leaves):
        d = unit(axis * g.uniform(0.2, 0.9) + e1 * g.normal(0, 1) + e2 * g.normal(0, 1))
        end = base + d * 0.006
        if inside is not None and not inside(end + d * 0.03):
            continue
        pedicel(soup, g, base, end, sc, r=0.0004)
        leaf(soup, g, frame(end, d, g.uniform(0, TAU)) @ RX(math.radians(90)), L=g.uniform(0.022, 0.04), bronze=g.uniform(0.1, 0.8), sc=sc)


def twig(soup, g, start, d0, length, r0, r1, sc=1.0, n=12, wander=0.085, ok=None):
    """A woody twig in (roughly) the plane of the card. Returns its points and tangents."""
    for attempt in range(80):
        pts = [np.asarray(start, np.float64)]
        d = unit(d0)
        side = unit(np.cross(d, (0, 0, 1)))
        k = g.normal(0, wander)
        for i in range(n):
            k = 0.6 * k + 0.4 * g.normal(0, wander)
            d = unit(d + side * k + np.array([0, 0, g.normal(0, 0.03) - pts[-1][2] * 4]))
            side = unit(np.cross(d, (0, 0, 1)))
            pts.append(pts[-1] + d * length / n)
        if ok is None or all(ok(p) for p in pts[1:]):
            break
    else:
        raise RuntimeError('twig does not fit its cell')
    pts = np.array(pts)
    rad = np.linspace(r0, r1, len(pts))
    v, q, t, ring = tube(pts, rad, 6)
    c = mix(TWIG, TWIG_LIGHT, 0.25 + 0.25 * np.sin(ring * 2.3 + v[:, 0] * 900))
    soup.add(v, quads=q, tris=t, cols=c, trans=0.0, scale=sc)
    tan = np.gradient(pts, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    return pts, tan


def spray(soup, g, m, kind='fan', density=1.0, p_bud=0.18, leaves=0.15, tint=0.0):
    """A flowering twig filling one atlas cell. Local frame: x across, y up the card, z to the camera."""
    half = CELL / 2

    def inside(p):
        w = xf(np.linalg.inv(m), p)[0]
        return abs(w[0]) < half - 0.030 and 0.036 < w[1] < CELL - 0.030

    def fits(p):
        w = xf(np.linalg.inv(m), p)[0]
        return abs(w[0]) < half - 0.022 and w[1] < CELL - 0.022

    def P(p):
        return xf(m, p)[0]

    def D(d):
        return unit(np.asarray(d, np.float64) @ m[:3, :3].T)

    base = np.array([0.0, PIVOT_Y, 0.0])
    arms = []
    layouts = {
        'fan': (0.055, ((-0.62, 0.180), (0.0, 0.198), (0.62, 0.180))),
        'fork': (0.075, ((-0.42, 0.190), (0.40, 0.190))),
        'bush': (0.045, ((-1.18, 0.108), (-0.60, 0.165), (0.0, 0.200), (0.60, 0.165), (1.18, 0.108))),
    }
    if kind in layouts:
        stem_len, spokes = layouts[kind]
        stem, tan = twig(soup, g, P(base), D((g.normal(0, 0.05), 1, 0)), stem_len, 0.0034, 0.0029, n=5, ok=fits)
        arms.append((stem, tan))
        for a, ln in spokes:
            a += g.normal(0, 0.06)
            arms.append(twig(soup, g, stem[-1], D((math.sin(a), math.cos(a), 0)), ln * g.uniform(0.92, 1.04), 0.0026, 0.0012, ok=fits))
    else:
        arms.append(twig(soup, g, P(base), D((g.normal(0, 0.1), 1, 0)), 0.255, 0.0032, 0.0012, n=16, wander=0.11, ok=fits))

    zc = D((0, 0, 1))
    spacing = 0.047 / density
    sign = 1.0
    for pts, tan in arms:
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        dist = np.concatenate([[0], np.cumsum(seg)])
        s = g.uniform(0.3, 0.9) * spacing
        while s < dist[-1] - 0.012:
            i = int(np.searchsorted(dist, s))
            p, t = pts[i], tan[i]
            sd = unit(np.cross(t, zc))
            d = unit(sd * 0.7 * sign + zc * g.uniform(0.35, 0.8) + t * 0.3 + g.normal(0, 0.18, 3))
            spur = p + d * g.uniform(0.005, 0.013)
            pedicel(soup, g, p, spur, 1.0, r=0.0011)
            umbel(soup, g, spur, unit(d + zc * 0.45), int(g.integers(3, 6)), p_bud=p_bud, tint=tint, inside=inside,
                  leaves=int(g.uniform() < leaves) * int(g.integers(1, 3)))
            sign = -sign
            s += spacing * g.uniform(0.75, 1.25)
        if pts is not arms[0][0] or len(arms) == 1:
            umbel(soup, g, pts[-1], unit(tan[-1] + zc * 0.6), int(g.integers(4, 7)), p_bud=p_bud * 1.5, tint=tint, inside=inside,
                  leaves=int(g.uniform() < leaves * 2) * 2)


def sleeve(soup, g, m, length, width, density=1.0, p_bud=0.12, leaves=0.05, tint=0.0, aged_p=0.3):
    """A twig running up the middle of its rectangle, flowering on short spurs all the way round.

    This is what a cherry in bloom is made of: every node of last year's wood carries an umbel, and the umbels
    spiral up the twig, so the twig disappears in a sleeve of blossom about a hand wide.
    """
    half = width / 2
    inv = np.linalg.inv(m)

    def inside(p):
        w = xf(inv, p)[0]
        return abs(w[0]) < half - 0.031 and 0.030 < w[1] < length - 0.031

    def fits(p):
        w = xf(inv, p)[0]
        return abs(w[0]) < 0.013 and w[1] < length - 0.03

    def D(d):
        return unit(np.asarray(d, np.float64) @ m[:3, :3].T)

    pts, tan = twig(soup, g, xf(m, (0.0, PIVOT_Y, 0.0))[0], D((0, 1, 0)), length - 0.05, 0.0030 if length > 0.2 else 0.0024, 0.0012,
                    n=14 if length > 0.2 else 8, wander=0.035, ok=fits)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    dist = np.concatenate([[0], np.cumsum(seg)])
    spacing = 0.022 / density
    s = g.uniform(0.35, 0.9) * spacing
    az = g.uniform(0, TAU)
    while s < dist[-1] - 0.006:
        i = int(np.searchsorted(dist, s))
        p, t = pts[i], tan[i]
        e1, e2 = perp(t)
        radial = e1 * math.cos(az) + e2 * math.sin(az)
        d = unit(radial + t * 0.35 + g.normal(0, 0.14, 3))
        spur = p + d * g.uniform(0.004, 0.010)
        pedicel(soup, g, p, spur, 1.0, r=0.0010)
        umbel(soup, g, spur, unit(d + t * 0.2), int(g.integers(4, 7)), p_bud=p_bud, aged_p=aged_p, tint=tint, inside=inside,
              leaves=int(g.uniform() < leaves) * int(g.integers(1, 3)), ped=(0.016, 0.027))
        az += 2.4 + g.normal(0, 0.3)                          # 2/5 phyllotaxis, give or take
        s += spacing * g.uniform(0.75, 1.25)
    umbel(soup, g, pts[-1], tan[-1], int(g.integers(4, 7)), p_bud=p_bud * 1.4, aged_p=aged_p, tint=tint, inside=inside,
          leaves=int(g.uniform() < leaves * 2), ped=(0.014, 0.024))


def rect_origin(x0, y0, w, h):
    """World position of the bottom centre of an atlas rectangle (metres from the atlas's top-left corner)."""
    return np.array([-ATLAS / 2 + x0 + w / 2, ATLAS / 2 - (y0 + h), 0.0])


def rect_meta(kind, x0, y0, w, h, size, pivot):
    """What the page needs to know about one piece: its uv rectangle (v up), its size in the world, where it hangs from."""
    return {'kind': kind, 'rect': [x0 / ATLAS, 1 - (y0 + h) / ATLAS, w / ATLAS, h / ATLAS], 'size': size, 'pivot': pivot,
            'px': [x0 / ATLAS, y0 / ATLAS, w / ATLAS, h / ATLAS]}


def build_atlas_geometry():
    soup = Soup()
    g = rng(20260411)
    meta = []
    H = CELL
    # density, buds, leaves, tint, aged: from just opened (buds, pale) to late bloom (red throats, first leaves)
    styles = [(1.00, 0.10, 0.04, 0.00, 0.25), (1.10, 0.06, 0.00, 0.10, 0.20), (0.90, 0.24, 0.00, -0.10, 0.10), (1.00, 0.10, 0.18, 0.18, 0.50),
              (1.15, 0.05, 0.00, -0.15, 0.20), (0.95, 0.30, 0.00, 0.05, 0.10), (1.05, 0.08, 0.26, 0.12, 0.60), (1.00, 0.14, 0.05, -0.05, 0.30)]

    # row 0: eight sleeves, 15 x 30 cm
    for k, st in enumerate(styles):
        x0 = k * 0.15
        sleeve(soup, g, translate(rect_origin(x0, 0, 0.15, H)), H, 0.15, *st)
        meta.append(rect_meta('sleeve', x0, 0, 0.15, H, [0.15, H], [0.5, PIVOT_Y / H]))

    # row 1, left half: eight twiglets, 15 x 15 cm
    for k in range(8):
        x0, y0 = (k % 4) * 0.15, H + (k // 4) * 0.15
        sleeve(soup, g, translate(rect_origin(x0, y0, 0.15, 0.15)), 0.15, 0.15, *styles[(k * 3 + 1) % 8])
        meta.append(rect_meta('twiglet', x0, y0, 0.15, 0.15, [0.15, 0.15], [0.5, PIVOT_Y / 0.15]))

    # row 1, right half: two fans; row 2, left half: two bushes
    for n, (kind, dens, pb, lv, tint) in enumerate([('fan', 1.15, 0.12, 0.10, 0.0), ('fan', 1.0, 0.2, 0.2, 0.1), ('bush', 1.0, 0.14, 0.1, 0.05), ('bush', 0.9, 0.22, 0.25, -0.1)]):
        x0, y0 = (2 * H + n * H, H) if n < 2 else ((n - 2) * H, 2 * H)
        spray(soup, g, translate(rect_origin(x0, y0, H, H)), kind, dens, pb, lv, tint)
        meta.append(rect_meta('spray', x0, y0, H, H, [H, H], [0.5, PIVOT_Y / H]))

    # row 2, right half: one umbel on a stub, twice life size
    for n in range(2):
        x0, y0, S = 2 * H + n * H, 2 * H, 2.0
        m = translate(rect_origin(x0, y0, H, H)) @ scale_m(S)
        half = CELL / 2

        def inside(p, S=S):                                    # the umbel is built at life size, then enlarged
            return abs(p[0]) * S < half - 0.05 and 0.07 < p[1] * S < CELL - 0.05

        sub = Soup()
        pts, tan = twig(sub, g, (0, PIVOT_Y / S, 0), (g.normal(0, 0.1), 1, 0), 0.058, 0.0030, 0.0022, n=6)
        umbel(sub, g, pts[-1], unit(tan[-1] * 0.5 + np.array([0, 0.25, 1])), 6, p_bud=0.25, tint=0.1 * n, leaves=2, ped=(0.022, 0.03), inside=inside)
        umbel(sub, g, pts[3], unit(np.array([0.8 * (1 if n == 0 else -1), 0.2, 0.7])), 3, p_bud=0.5, tint=0.0, ped=(0.016, 0.024), inside=inside)
        for d in sub.d:
            d[:, 1] = S
        soup.v += [xf(m, v).astype(np.float32) for v in sub.v]
        soup.c += sub.c
        soup.d += sub.d
        soup.q += [q + soup.n for q in sub.q]
        soup.t += [t + soup.n for t in sub.t]
        soup.n += sub.n
        meta.append(rect_meta('umbel', x0, y0, H, H, [H / S, H / S], [0.5, PIVOT_Y / H]))

    # row 3: two single blossoms, face on
    for n in range(2):
        x0, y0, S = n * H, 3 * H, 6.6
        m = translate(rect_origin(x0, y0, H, H) + np.array([0, H / 2, 0])) @ scale_m(S)
        tilt = RX(math.radians(g.uniform(-8, 8))) @ RY(math.radians(g.uniform(-8, 8)))
        blossom(soup, g, m @ tilt, openness=1.0 if n == 0 else 0.9, aged=0.0 if n == 0 else 0.9, tint=0.0 if n == 0 else 0.2, sc=S)
        meta.append(rect_meta('blossom', x0, y0, H, H, [H / S, H / S], [0.5, 0.5]))

    # four loose petals
    S = 6.9
    for k in range(4):
        x0, y0 = 2 * H + (k % 2) * H / 2, 3 * H + (k // 2) * H / 2
        m = translate(rect_origin(x0, y0, H / 2, H / 2) + np.array([0, H / 4 - 0.0170 * S * 0.48, 0])) @ scale_m(S)
        add_petal(soup, g, m, S, L=0.0170, W=0.0138 * g.uniform(0.94, 1.08), notch=g.uniform(0.08, 0.13), cup=g.uniform(0.5, 1.2), tint=(-0.2, 0.0, 0.2, 0.35)[k])
        meta.append(rect_meta('petal', x0, y0, H / 2, H / 2, [H / 2 / S, H / 2 / S], [0.5, 0.5]))

    # a scatter of fallen petals
    x0, y0, S = 3 * H, 3 * H, 1.5
    centre = rect_origin(x0, y0, H, H) + np.array([0, H / 2, 0])
    for k in range(60):
        r = 0.118 * math.sqrt(g.uniform(0, 1)) * g.uniform(0.6, 1.0)
        a = g.uniform(0, TAU)
        m = translate(centre + np.array([r * math.cos(a), r * math.sin(a), 0.0004 * k])) @ scale_m(S) \
            @ RZ(g.uniform(0, TAU)) @ RX(g.normal(0, 0.12)) @ RY(g.normal(0, 0.12)) @ translate((0, -0.008, 0))
        if g.uniform() < 0.2:
            m = m @ RY(math.pi)
        add_petal(soup, g, m, S, cup=g.uniform(0.3, 1.3), tint=g.normal(0.05, 0.2), nu=7, nt=9)
    meta.append(rect_meta('scatter', x0, y0, H, H, [H / S, H / S], [0.5, 0.5]))
    return soup, meta


# ------------------------------------------------------------------ rendering
def node_material(name):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt, nt.nodes.new('ShaderNodeOutputMaterial')


def emit(nt, out, socket):
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(socket, em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])


def materials():
    albedo, nt, out = node_material('albedo')
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'Col'
    emit(nt, out, at.outputs['Color'])

    normal, nt, out = node_material('normal')
    ge = nt.nodes.new('ShaderNodeNewGeometry')
    ma = nt.nodes.new('ShaderNodeVectorMath')
    ma.operation = 'MULTIPLY_ADD'
    ma.inputs[1].default_value = (0.5, 0.5, 0.5)
    ma.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(ge.outputs['Normal'], ma.inputs[0])
    emit(nt, out, ma.outputs['Vector'])

    data, nt, out = node_material('data')
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'Dat'
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(at.outputs['Color'], sep.inputs['Color'])
    dist = nt.nodes.new('ShaderNodeMath')
    dist.operation = 'MULTIPLY'
    dist.inputs[1].default_value = AO_DIST
    nt.links.new(sep.outputs['Green'], dist.inputs[0])
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
    ao.samples = 6
    nt.links.new(dist.outputs['Value'], ao.inputs['Distance'])
    comb = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(sep.outputs['Red'], comb.inputs['Red'])
    nt.links.new(ao.outputs['AO'], comb.inputs['Green'])
    emit(nt, out, comb.outputs['Color'])
    return albedo, normal, data


def setup_scene(ortho=ATLAS):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.max_bounces = 0
    sc.cycles.transparent_max_bounces = 8
    sc.render.film_transparent = True
    sc.render.use_persistent_data = True
    world = bpy.data.worlds.new('world')
    sc.world = world
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[1].default_value = 0.0
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = ortho
    cam.clip_start, cam.clip_end = 0.01, 20
    ob = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(ob)
    ob.location = (0, 0, 5)
    sc.camera = ob
    s = sc.render.image_settings
    s.file_format = 'OPEN_EXR'
    s.color_mode = 'RGBA'
    s.color_depth = '32'
    return sc


def render(sc, material, px, samples):
    """Render the scene with every surface replaced by `material`. Returns (px, px, 4) float32, row 0 at the top."""
    bpy.context.view_layer.material_override = material
    sc.render.resolution_x = sc.render.resolution_y = px
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    path = os.path.join(tempfile.gettempdir(), 'sakura_%s.exr' % material.name)
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    a = np.empty(px * px * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    os.remove(path)
    print('  %-7s %4d px  %3d spp  %.1fs' % (material.name, px, samples, time.time() - t), flush=True)
    return a.reshape(px, px, 4)[::-1].copy()


def pull_push(rgb, w):
    """Fill texels with no coverage from their covered neighbours (so mip levels have no dark fringes)."""
    levels = [(rgb * w[..., None], w)]
    while levels[-1][1].shape[0] > 1:
        c, a = levels[-1]
        h = c.shape[0] // 2
        levels.append((c.reshape(h, 2, h, 2, -1).sum((1, 3)), a.reshape(h, 2, h, 2).sum((1, 3))))
    fill = levels[-1][0] / np.maximum(levels[-1][1][..., None], 1e-6)
    for c, a in reversed(levels[:-1]):
        up = np.repeat(np.repeat(fill, 2, 0), 2, 1)
        k = np.clip(a, 0, 1)[..., None]
        fill = (c / np.maximum(a[..., None], 1e-6)) * k + up * (1 - k)
    return fill


def encode(arr_u8, quality=92, lossless=False):
    from PIL import Image
    im = Image.fromarray(arr_u8, 'RGBA' if arr_u8.shape[-1] == 4 else 'RGB')
    buf = io.BytesIO()
    im.save(buf, 'WEBP', quality=100 if lossless else quality, lossless=lossless, method=6, alpha_quality=100, exact=True)
    return buf.getvalue()


def build_blossoms():
    print('blossoms: modelling', flush=True)
    t = time.time()
    sc = setup_scene()
    soup, meta = build_atlas_geometry()
    ob = soup.build('sakura')
    print('  %d vertices, %d faces  %.1fs' % (len(ob.data.vertices), len(ob.data.polygons), time.time() - t), flush=True)
    albedo, normal, data = materials()
    ob.data.materials.append(albedo)
    print('blossoms: rendering', flush=True)
    A = render(sc, albedo, PX, 24 if FAST else 64)
    N = render(sc, normal, PX_DATA, 16 if FAST else 32)
    D = render(sc, data, PX_DATA, 16 if FAST else 48)

    alpha = np.clip(A[..., 3], 0, 1)
    # the render is premultiplied: divide the coverage out, then bleed colour into the empty texels
    rgb = pull_push(np.where(alpha[..., None] > 1e-4, A[..., :3] / np.maximum(alpha[..., None], 1e-4), 0), alpha)
    colour = linear_to_srgb(rgb)

    na = np.clip(N[..., 3], 0, 1)
    n = np.where(na[..., None] > 1e-4, N[..., :3] / np.maximum(na[..., None], 1e-4), 0.5) * 2 - 1
    n = pull_push(n, na)
    n[..., 2] = np.maximum(np.abs(n[..., 2]), 0.05)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9

    # occlusion and translucency are rendered at half size; coverage keeps the full resolution
    da = np.clip(D[..., 3], 0, 1)
    d = pull_push(np.where(da[..., None] > 1e-4, D[..., :3] / np.maximum(da[..., None], 1e-4), 0), da)
    d = np.repeat(np.repeat(d, PX // PX_DATA, 0), PX // PX_DATA, 1)
    d = (d + np.roll(d, 1, 0) + np.roll(d, 1, 1) + np.roll(np.roll(d, 1, 0), 1, 1)) / 4
    mask = np.stack([alpha, d[..., 1], d[..., 0]], -1)

    # every piece must be empty along the border of its rectangle, or neighbours would bleed into each other
    leak, cover = 0.0, []
    for mt in meta:
        x0, y0, w, h = (int(round(v * PX)) for v in mt['px'])
        a = alpha[y0:y0 + h, x0:x0 + w]
        cover.append(float(a.mean()))
        frame_ = np.zeros_like(a, bool)
        frame_[:2, :] = frame_[-2:, :] = frame_[:, :2] = frame_[:, -2:] = True
        if mt['kind'] in ('sleeve', 'twiglet', 'spray', 'umbel'):                 # the twig crosses the bottom edge
            frame_[-2:, w // 2 - 14:w // 2 + 14] = False
        mine = float((a * frame_).max())
        if mine >= 0.05:
            print('  %s at %s crosses its border (%.2f)' % (mt['kind'], mt['px'][:2], mine), flush=True)
        leak = max(leak, mine)
    print('  coverage %.1f%% (sleeves %.0f%%), border leak %.3f' % (alpha.mean() * 100, 100 * np.mean(cover[:8]), leak), flush=True)
    if leak >= 0.05 and not os.environ.get('SAKURA_DRAFT'):                 # a draft still writes the preview, to see where
        raise AssertionError('geometry crosses the border of its rectangle')
    for mt in meta:
        del mt['px']
    return {'blossomColor': encode(to_u8(colour), 90), 'blossomMask': encode(to_u8(mask), 92), 'blossomNormal': encode(to_u8(n * 0.5 + 0.5), 88)}, meta


# ------------------------------------------------------------------ periodic fields
def periodic(n, seed, beta=2.0, sx=1.0, sy=1.0, lo=1.0, hi=None):
    """Tileable noise by spectral synthesis; sx / sy > 1 stretches features along x / y. Normalised to [0, 1]."""
    g = rng(seed)
    f = np.fft.fftfreq(n) * n
    kx, ky = np.meshgrid(f, f)
    k = np.sqrt((kx * sx) ** 2 + (ky * sy) ** 2)
    amp = np.where(k >= lo, 1 / np.maximum(k, 1e-6) ** (beta / 2), 0)
    if hi:
        amp = amp * np.exp(-(k / hi) ** 2)
    spec = (g.normal(size=(n, n)) + 1j * g.normal(size=(n, n))) * amp
    field = np.real(np.fft.ifft2(spec))
    lo_, hi_ = np.percentile(field, [0.5, 99.5])
    return np.clip((field - lo_) / (hi_ - lo_), 0, 1)


def blur(a, sigma):
    n = a.shape[0]
    f = np.fft.fftfreq(n)
    kx, ky = np.meshgrid(f, f)
    return np.real(np.fft.ifft2(np.fft.fft2(a) * np.exp(-2 * (np.pi * sigma) ** 2 * (kx ** 2 + ky ** 2))))


def enlarge(a, n2):
    """Periodic (band-limited) resize of a square field."""
    n = a.shape[0]
    if n == n2:
        return a
    F = np.fft.fftshift(np.fft.fft2(a))
    pad = (n2 - n) // 2
    return np.real(np.fft.ifft2(np.fft.ifftshift(np.pad(F, pad)))) * (n2 / n) ** 2


def worley(n, points, stretch, seed, warp=0.03):
    """Periodic cellular distances F1, F2 on the unit tile, with cells `stretch` times longer along y."""
    g = rng(seed)
    pts = g.random((points, 2))
    ys, xs = np.mgrid[0:n, 0:n] / n
    X = xs + (periodic(n, seed + 11, beta=2.4, lo=2, hi=20) - 0.5) * warp * 2
    Y = ys + (periodic(n, seed + 12, beta=2.4, lo=2, hi=20) - 0.5) * warp
    f1 = np.full((n, n), 9.0)
    f2 = np.full((n, n), 9.0)
    for px_, py_ in pts:
        dx = (X - px_ + 0.5) % 1 - 0.5
        dy = ((Y - py_ + 0.5) % 1 - 0.5) / stretch
        d = np.sqrt(dx * dx + dy * dy)
        f2 = np.where(d < f1, f1, np.minimum(f2, d))
        f1 = np.minimum(f1, d)
    return f1, f2


def height_normal(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(h)], -1)                  # image rows run down, texture v runs up
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def render_relief(h, tile, amp, px, ao_dist):
    """Raise a height field as real geometry and render its normals and occlusion with Cycles.

    A margin of wrapped geometry surrounds the tile, so the occlusion is seamless too.
    """
    sc = setup_scene(ortho=tile)
    step = max(1, h.shape[0] // 1024)
    hs = h[::step, ::step]
    k = hs.shape[0]
    mg = k // 16
    idx = np.arange(-mg, k + mg) % k
    hh = hs[np.ix_(idx, idx)]
    c = (np.arange(-mg, k + mg) + 0.5) / k * tile - tile / 2
    X, Y = np.meshgrid(c, -c)                                     # row 0 at the top
    soup = Soup()
    soup.add(np.stack([X, Y, hh * amp], -1).reshape(-1, 3), quads=grid_quads(len(c), len(c)), cols=np.array([0.5, 0.5, 0.5]), trans=0.0, scale=ao_dist / AO_DIST)
    ob = soup.build('relief')
    albedo, normal, data = materials()
    ob.data.materials.append(albedo)
    N = render(sc, normal, px, 8 if FAST else 16)
    D = render(sc, data, px, 12 if FAST else 40)
    n = N[..., :3] * 2 - 1
    n[..., 2] = np.maximum(n[..., 2], 0.05)
    return n / np.linalg.norm(n, axis=-1, keepdims=True), np.clip(D[..., 1], 0, 1)


# ------------------------------------------------------------------ bark
def build_bark(n=BARK_PX):
    """Old cherry bark, tileable, one metre square. x runs around the trunk, y along it."""
    print('bark: fields', flush=True)
    g = rng(77)
    m = min(n, 1024)

    # plates split by furrows: a cellular pattern, stretched along the trunk
    f1, f2 = worley(m, 150, 5.4, 5, warp=0.012)
    e = f2 - f1
    width = 0.010 * (0.55 + 0.9 * periodic(m, 21, beta=2.6, lo=1, hi=10))
    old = smooth(0.25, 0.75, periodic(m, 22, beta=2.8, lo=1, hi=5))          # where the bark has split deeply
    breaks = smooth(0.28, 0.6, periodic(m, 23, beta=2.2, lo=3, hi=28))            # furrows open and close along their length
    furrow = np.clip(enlarge((1 - smooth(0.0, 1.0, e / width)) * (0.3 + 0.7 * old) * (0.4 + 0.6 * breaks), n), 0, 1)
    plate = np.clip(enlarge(smooth(0.0, 0.03, e) ** 0.55, n), 0, 1)
    old = np.clip(enlarge(old, n), 0, 1)

    stri = periodic(n, 2, beta=1.5, sx=7.0, sy=1, lo=5, hi=n * 0.3)            # satin horizontal grain
    fine = periodic(n, 3, beta=1.0, lo=n * 0.05, hi=n * 0.42)
    tone = periodic(n, 9, beta=2.4, sx=1, sy=2.0, lo=1, hi=30)
    bumps = periodic(n, 15, beta=2.0, lo=10, hi=110)                               # the plates are not smooth
    checks = smooth(0.60, 0.72, periodic(n, 16, beta=1.6, sx=1, sy=6.0, lo=24, hi=n * 0.13)) * plate   # fine vertical checks in them

    # lenticels: corky horizontal dashes in loose rows around the trunk
    lent = np.zeros((n, n))
    rows = np.sort(g.uniform(0, n, 36))
    for _ in range(440):
        cx = g.uniform(0, n)
        cy = rows[int(g.integers(0, len(rows)))] + g.normal(0, n * 0.007)
        a = g.uniform(0.008, 0.050) * n * g.uniform(0.5, 1.0)
        b = g.uniform(0.0019, 0.0044) * n
        ix = np.arange(int(cx - 2 * a) - 2, int(cx + 2 * a) + 3)
        iy = np.arange(int(cy - 4 * b) - 2, int(cy + 4 * b) + 3)
        dx = (ix - cx)[None, :]
        dy = (iy - cy)[:, None] + dx * g.normal(0, 0.03)
        blob = np.exp(-((dx / a) ** 4 + (dy / b) ** 2)) * g.uniform(0.6, 1.0)
        sel = np.ix_(iy % n, ix % n)
        lent[sel] = np.maximum(lent[sel], blob)
    lent = smooth(0.25, 0.75, lent * (0.55 + 0.9 * periodic(n, 8, beta=1.6, lo=14, hi=n * 0.2))) * (1 - furrow)

    # lichen crusts (hard, ragged edges) and moss in the furrows
    lf = periodic(n, 11, beta=2.3, lo=3, hi=70)
    lichen = smooth(0.80, 0.825, lf) * (1 - furrow)
    rim = smooth(0.80, 0.825, lf) - smooth(0.845, 0.87, lf)
    gold = smooth(0.90, 0.93, periodic(n, 13, beta=2.2, lo=8, hi=90)) * (1 - furrow)
    moss = smooth(0.50, 0.74, periodic(n, 14, beta=2.9, lo=1, hi=10)) * np.clip(furrow * 1.6 + smooth(0.6, 0.2, plate) * 0.6, 0, 1) * (0.45 + 0.55 * fine) * 0.3     # the page adds moss where it grows: low on the trunk, on top of the limbs

    h = 0.62 * plate - 0.95 * furrow + 0.13 * stri * plate + 0.24 * lent + 0.035 * fine + 0.14 * (tone - 0.5) + 0.12 * (bumps - 0.5) - 0.10 * checks + 0.05 * lichen + 0.05 * gold + 0.08 * moss
    h = (h - h.min()) / (h.max() - h.min())

    print('bark: relief', flush=True)
    nrm, ao = render_relief(h, 1.0, 0.016, n, 0.022)
    nrm = nrm + (height_normal(h - blur(h, 1.5), 30.0 * n / 1024) - np.array([0, 0, 1])) * 0.8     # the grain finer than the mesh
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    ao = np.clip(0.25 + 0.75 * smooth(0.1, 0.9, ao), 0, 1)

    sheen = smooth(0.45, 0.95, stri) * plate * (1 - old * 0.7)
    c = mix(lin('#4a3d3c'), lin('#6c5a53'), smooth(0.15, 0.9, tone))
    c = mix(c, lin('#7d5348'), sheen * 0.6)                                                        # the red satin of young bark
    c = mix(c, lin('#857e78'), smooth(0.5, 0.85, periodic(n, 10, beta=2.2, lo=2, hi=40)) * 0.45 * plate)  # silver weathering
    c = mix(c, lin('#c0a886'), lent * 0.9)
    c = mix(c, lin('#171212'), np.clip(furrow * 0.9 + checks * 0.4, 0, 1))
    c = mix(c, mix(lin('#9ea896'), lin('#c2c8b6'), fine), lichen * 0.8)
    c = mix(c, lin('#70786a'), np.clip(rim, 0, 1) * 0.5)
    c = mix(c, lin('#c7ad55'), gold * 0.7)
    c = mix(c, mix(lin('#48602a'), lin('#6f8a35'), fine), np.clip(moss, 0, 1) * 0.8)
    c = c * (0.62 + 0.38 * ao[..., None]) * (0.88 + 0.24 * fine[..., None])

    rough = np.clip(0.62 - 0.16 * sheen + 0.30 * lent + 0.30 * furrow + 0.28 * lichen + 0.2 * moss, 0.36, 1)
    orm = to_u8(np.stack([ao, rough, h], -1))
    if n > 1024:                                                                                     # occlusion and roughness are soft: half size is plenty
        orm = orm.reshape(n // 2, 2, n // 2, 2, 3).mean((1, 3)).astype(np.uint8)
    return {'barkColor': encode(to_u8(linear_to_srgb(c)), 86), 'barkNormal': encode(to_u8(nrm * 0.5 + 0.5), 82), 'barkOrm': encode(orm, 86)}


# ------------------------------------------------------------------ grass
def build_grass(tile=1.2, px=GRASS_PX, blades=15000):
    """A tileable square of turf, modelled blade by blade and rendered from straight above."""
    print('grass: modelling', flush=True)
    g = rng(404)
    sc = setup_scene(ortho=tile)
    soup = Soup()

    # the soil under it
    k = 72
    c = np.linspace(-tile * 0.62, tile * 0.62, k)
    X, Y = np.meshgrid(c, c)
    w = TAU / tile
    Z = 0.004 * (np.sin(X * w * 3 + 1) * np.cos(Y * w * 2) + 0.6 * np.sin(X * w * 7 + Y * w * 5))
    shade = 0.5 + 0.5 * np.sin(X * w * 5 + 2) * np.cos(Y * w * 4 + 1)
    soup.add(np.stack([X, Y, Z], -1).reshape(-1, 3), quads=grid_quads(k, k), cols=mix(lin('#33291f'), lin('#54453a'), shade).reshape(-1, 3), trans=0.0, scale=2.7)

    # blades: in tufts, leaning and drooping, some yellowing at the tip, a few dead
    N = blades
    tufts = g.uniform(0, tile, (1100, 2))
    ti = g.integers(0, len(tufts), N)
    base = np.where((g.uniform(size=N) < 0.62)[:, None], tufts[ti] + g.normal(0, 0.011, (N, 2)), g.uniform(0, tile, (N, 2))) % tile
    hgt = np.clip(g.lognormal(math.log(0.072), 0.32, N), 0.03, 0.15)
    az = g.uniform(0, TAU, N)
    lean = g.uniform(0.08, 1.0, N) ** 1.3
    w0 = g.uniform(0.0030, 0.0056, N)
    T = np.array([0.0, 0.3, 0.56, 0.8, 1.0])
    dx, dy = np.cos(az), np.sin(az)
    cx = base[:, 0, None] + dx[:, None] * (lean * hgt)[:, None] * T ** 1.7
    cy = base[:, 1, None] + dy[:, None] * (lean * hgt)[:, None] * T ** 1.7
    cz = hgt[:, None] * (T - 0.32 * lean[:, None] * T ** 2)
    wid = w0[:, None] * (1 - T ** 1.6) * 0.5
    twist = g.normal(0, 0.5, N)[:, None] * T
    sx, sy = -np.sin(az[:, None] + twist), np.cos(az[:, None] + twist)
    V = np.stack([np.stack([cx - sx * wid, cy - sy * wid, cz], -1), np.stack([cx + sx * wid, cy + sy * wid, cz + 0.0006], -1)], 2)   # (N, 5, 2, 3)
    green = mix(mix(lin('#3f6f26'), lin('#5f9230'), g.uniform(size=N)), lin('#7da53a'), g.uniform(size=N) ** 3 * 0.8)
    straw = lin('#b3a468')
    dry = (g.uniform(size=N) < 0.3) * g.uniform(0.2, 0.9, N)
    dead = g.uniform(size=N) < 0.06
    col = green[:, None, :] * (0.5 + 0.62 * T)[None, :, None]
    col = col * (1 - (dry[:, None] * smooth(0.5, 1.0, T))[..., None]) + straw * (dry[:, None] * smooth(0.5, 1.0, T))[..., None]
    col = np.where(dead[:, None, None], straw * (0.55 + 0.4 * T)[None, :, None], col)
    C = np.repeat(col[:, :, None, :], 2, 2)
    # copies across the edges make it tile
    near = 0.17
    Vs, Cs = [V], [C]
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if ox == 0 and oy == 0:
                continue
            sel = np.ones(N, bool)
            if ox:
                sel &= (base[:, 0] < near) if ox > 0 else (base[:, 0] > tile - near)
            if oy:
                sel &= (base[:, 1] < near) if oy > 0 else (base[:, 1] > tile - near)
            Vs.append(V[sel] + np.array([ox * tile, oy * tile, 0]))
            Cs.append(C[sel])
    V, C = np.concatenate(Vs), np.concatenate(Cs)
    M = len(V)
    b0 = np.arange(M)[:, None] * 10 + np.arange(4)[None, :] * 2
    quads = np.stack([b0, b0 + 1, b0 + 3, b0 + 2], -1).reshape(-1, 4)
    soup.add(V.reshape(-1, 3) - np.array([tile / 2, tile / 2, 0]), quads=quads, cols=C.reshape(-1, 3), trans=1.0, scale=2.7)

    # clover
    ang = np.arange(9) * TAU / 9
    for _ in range(110):
        p = g.uniform(0, tile, 2)
        z = g.uniform(0.02, 0.045)
        r = g.uniform(0.0045, 0.0075)
        a0 = g.uniform(0, TAU)
        leafc = mix(lin('#356f2c'), lin('#4f8f3a'), g.uniform())
        for ox in (-tile, 0, tile):
            for oy in (-tile, 0, tile):
                q = p + np.array([ox, oy]) - tile / 2
                if abs(q[0]) > tile * 0.6 or abs(q[1]) > tile * 0.6:
                    continue
                for j in range(3):
                    a = a0 + j * TAU / 3
                    cen = np.array([q[0] + math.cos(a) * r * 0.95, q[1] + math.sin(a) * r * 0.95, z])
                    disc = np.concatenate([[cen + np.array([0, 0, 0.0012])], cen + np.stack([np.cos(ang) * r, np.sin(ang) * r, -0.001 * np.cos(ang - a)], -1)])
                    cc = np.concatenate([[mix(leafc, lin('#9bc27a'), 0.5)], np.broadcast_to(leafc, (9, 3))])
                    soup.add(disc, tris=np.array([[0, 1 + i, 1 + (i + 1) % 9] for i in range(9)]), cols=cc, trans=1.0, scale=2.7)

    ob = soup.build('turf')
    print('  %d vertices' % len(ob.data.vertices), flush=True)
    albedo, normal, data = materials()
    ob.data.materials.append(albedo)
    A = render(sc, albedo, px, 24 if FAST else 64)
    Nm = render(sc, normal, px, 12 if FAST else 24)
    D = render(sc, data, px, 12 if FAST else 48)
    n = Nm[..., :3] * 2 - 1
    n[..., 2] = np.maximum(n[..., 2], 0.05)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    blade, ao = np.clip(D[..., 0], 0, 1), np.clip(D[..., 1], 0, 1)
    rough = 0.95 - 0.33 * blade
    return {'grassColor': encode(to_u8(linear_to_srgb(A[..., :3])), 88), 'grassNormal': encode(to_u8(n * 0.5 + 0.5), 82),
            'grassOrm': encode(to_u8(np.stack([ao, rough, blade], -1)), 84)}


# ------------------------------------------------------------------ soil, stone
def build_soil(n=512):
    """Bare earth under the tree: clods, grit and a few small stones. Tileable."""
    print('soil', flush=True)
    clods = periodic(n, 31, beta=2.3, lo=3, hi=90)
    fine = periodic(n, 32, beta=1.1, lo=30, hi=n * 0.45)
    peb = smooth(0.76, 0.82, periodic(n, 34, beta=2.0, lo=16, hi=56))
    h = 0.6 * clods + 0.3 * peb + 0.14 * fine
    cav = np.clip(0.5 + 3.0 * (h - blur(h, 5)), 0, 1)
    c = mix(lin('#33281f'), lin('#5d4c3b'), smooth(0.2, 0.9, 0.7 * clods + 0.3 * fine))
    c = mix(c, mix(lin('#6f695f'), lin('#9a9488'), periodic(n, 35, beta=2.0, lo=4, hi=40)), peb * 0.9)
    c = c * (0.6 + 0.4 * smooth(0.15, 0.7, cav)[..., None]) * (0.9 + 0.2 * fine[..., None])
    return {'soilColor': encode(to_u8(linear_to_srgb(c)), 86), 'soilNormal': encode(to_u8(height_normal(blur(h, 0.7), 70.0) * 0.5 + 0.5), 84)}


def build_stone(n=512):
    """Weathered granite for the lantern and the rocks (used triplanar, so only colour). Tileable."""
    print('stone', flush=True)
    g = rng(55)
    mott = periodic(n, 41, beta=2.2, lo=2, hi=40)
    grain = blur(g.uniform(size=(n, n)), 0.7)
    grain = (grain - grain.min()) / (grain.max() - grain.min())
    lo_, hi_ = np.percentile(grain, [11, 86])
    c = mix(lin('#84827d'), lin('#9c9a94'), mott)
    c = mix(c, lin('#474643'), smooth(lo_ + 0.01, lo_ - 0.01, grain) * 0.85)
    c = mix(c, lin('#cbc8c0'), smooth(hi_ - 0.01, hi_ + 0.01, grain) * 0.8)
    c = mix(c, lin('#a8937f'), smooth(0.62, 0.66, periodic(n, 42, beta=1.4, lo=40, hi=n * 0.4)) * 0.5)
    stain = smooth(0.55, 0.8, periodic(n, 43, beta=2.6, lo=1, hi=12))
    c = mix(c, lin('#5c5d50'), stain * 0.45)                                           # algae in the damp
    lich = smooth(0.74, 0.76, periodic(n, 44, beta=2.3, lo=3, hi=50))
    c = mix(c, lin('#b9bdab'), lich * 0.7)
    return {'stoneColor': encode(to_u8(linear_to_srgb(c)), 86)}


# ------------------------------------------------------------------ main
def data_uri(blob):
    return 'data:image/webp;base64,' + base64.b64encode(blob).decode('ascii')


GROUPS = {
    'blossoms': ('blossomColor', 'blossomMask', 'blossomNormal'),
    'bark': ('barkColor', 'barkNormal', 'barkOrm'),
    'grass': ('grassColor', 'grassNormal', 'grassOrm'),
    'soil': ('soilColor', 'soilNormal'),
    'stone': ('stoneColor',),
}


def main():
    from PIL import Image
    t0 = time.time()
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    wanted = [a for a in args if a in GROUPS] or list(GROUPS)
    meta_path = os.path.join(OUT, 'atlas.json')
    blobs, meta = {}, None
    for group, names in GROUPS.items():
        cached = all(os.path.exists(os.path.join(OUT, n + '.webp')) for n in names) and (group != 'blossoms' or os.path.exists(meta_path))
        if group in wanted or not cached:                      # anything not asked for is taken from the last run
            out = {'blossoms': build_blossoms, 'bark': build_bark, 'grass': build_grass, 'soil': build_soil, 'stone': build_stone}[group]()
            if group == 'blossoms':
                out, meta = out
                with open(meta_path, 'w') as f:
                    json.dump(meta, f)
            for n, blob in out.items():
                with open(os.path.join(OUT, n + '.webp'), 'wb') as f:
                    f.write(blob)
        for n in names:
            with open(os.path.join(OUT, n + '.webp'), 'rb') as f:
                blobs[n] = f.read()
    if meta is None:
        with open(meta_path) as f:
            meta = json.load(f)
    for n, blob in blobs.items():
        print('  %-14s %7.1f KB' % (n, len(blob) / 1024))

    info = {'size': ATLAS, 'pieces': meta, 'blender': bpy.app.version_string}
    js = ['// Generated by tools/blender/build_assets.py (Blender %s, Cycles). Do not edit.' % bpy.app.version_string,
          'window.SAKURA_TEXTURES = {', '  atlas: %s,' % json.dumps(info, separators=(',', ':'))]
    js += ['  %s: "%s",' % (n, data_uri(blob)) for n, blob in blobs.items()]
    js.append('};\n')
    with open(os.path.join(ASSETS, 'textures.js'), 'w') as f:
        f.write('\n'.join(js))

    # previews: the atlas lit by its own occlusion over a dusk blue; the tiles side by side
    def img(n):
        return np.asarray(Image.open(io.BytesIO(blobs[n])).convert('RGB'), np.float32)
    colour, mask = img('blossomColor'), img('blossomMask')
    a, occ = mask[..., :1] / 255, mask[..., 1:2] / 255
    prev = colour * (0.35 + 0.65 * occ) * a + np.array([38, 52, 84], np.float32) * (1 - a)
    Image.fromarray(prev.astype(np.uint8)).save(os.path.join(OUT, 'blossoms_preview.png'))
    for group in ('bark', 'grass'):
        tiles = [np.asarray(Image.open(io.BytesIO(blobs[n])).convert('RGB').resize((768, 768), Image.LANCZOS)) for n in GROUPS[group]]
        Image.fromarray(np.concatenate(tiles, 1)).save(os.path.join(OUT, group + '_preview.png'))
    lit = img('barkColor') * (0.55 + 0.45 * np.clip(img('barkNormal')[..., :1] / 127.5 - 1 + 0.6, 0, 1.4))
    Image.fromarray(np.clip(np.tile(lit, (1, 2, 1)), 0, 255).astype(np.uint8)).resize((1536, 768), Image.LANCZOS).save(os.path.join(OUT, 'bark_lit.png'))
    print('done in %.0fs -> %s (%.0f KB)' % (time.time() - t0, os.path.join(ASSETS, 'textures.js'),
                                             os.path.getsize(os.path.join(ASSETS, 'textures.js')) / 1024))


if __name__ == '__main__':
    main()
