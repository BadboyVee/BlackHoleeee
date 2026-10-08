"""Trees, palms, shrubs and ferns for the island, modelled in Blender.

Every plant is grown from a branch skeleton (recursive, with gravitropism
and phyllotaxis), swept into bark tubes with parallel-transported frames,
and dressed with the twig/frond cards baked by leaves.py. Two LODs per
variant go into one GLB; far away the trees become octahedral impostors
(see impostors.py).

Vertex data the game's wind and shading read:
    COLOR_0     r  flexibility (0 at the root, 1 at twig tips)
                g  branch phase (0..1, per scaffold limb)
                b  leaf flutter weight (1 on cards)
                a  crown occlusion (1 outside, darker deep in the crown)
    TEXCOORD_1  x  tint (0 living, 1 dead frond / coconut husk)

usage: python tools/blender/trees.py [species...]
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from lib import ASSETS, reset, rng  # noqa: E402

OUT = os.path.join(ASSETS, 'vegetation')
ATLAS = json.load(open(os.path.join(OUT, 'atlases.json')))
UP = np.array([0.0, 0.0, 1.0])


def norm(v):
    return v / (np.linalg.norm(v) + 1e-12)


def rotate(v, axis, ang):
    """Rodrigues rotation of v about a unit axis."""
    axis = norm(axis)
    return v * math.cos(ang) + np.cross(axis, v) * math.sin(ang) + axis * np.dot(axis, v) * (1 - math.cos(ang))


def perpendicular(v):
    a = np.cross(v, UP)
    if np.linalg.norm(a) < 1e-4:
        a = np.cross(v, [1.0, 0, 0])
    return norm(a)


# ------------------------------------------------------------------ mesh builder
class Builder:
    """Accumulates one material's geometry with the game's vertex attributes."""

    def __init__(self):
        self.v, self.n, self.uv, self.uv2, self.col, self.f = [], [], [], [], [], []
        self.count = 0

    def add(self, verts, normals, uvs, faces, col, tint=0.0):
        k = self.count
        self.v.append(np.asarray(verts, np.float32))
        self.n.append(np.asarray(normals, np.float32))
        self.uv.append(np.asarray(uvs, np.float32))
        self.uv2.append(np.tile([tint, 0.0], (len(verts), 1)).astype(np.float32))
        c = np.asarray(col, np.float32)
        self.col.append(np.tile(c, (len(verts), 1)) if c.ndim == 1 else c)
        self.f.extend([[i + k for i in face] for face in faces])
        self.count += len(verts)

    def arrays(self):
        if not self.count:
            return None
        return (np.concatenate(self.v), np.concatenate(self.n), np.concatenate(self.uv),
                np.concatenate(self.uv2), np.concatenate(self.col), self.f)


def sweep(bld, pts, radii, sides, col_fn, bark_tile=1.2, buttress=None, rings=0.0, tint=0.0, cap=False):
    """Tube along pts (n,3) with parallel-transport frames; col_fn(t) -> rgba per ring."""
    pts = np.asarray(pts, float)
    n = len(pts)
    tang = [norm(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]) for i in range(n)]
    nrm = perpendicular(tang[0])
    frames = []
    for i in range(n):
        if i:
            # parallel transport: rotate the previous normal by the change in tangent
            axis = np.cross(tang[i - 1], tang[i])
            s = np.linalg.norm(axis)
            if s > 1e-8:
                nrm = rotate(nrm, axis / s, math.asin(min(s, 1.0)))
        nrm = norm(nrm - tang[i] * np.dot(nrm, tang[i]))
        frames.append((nrm, np.cross(tang[i], nrm)))
    verts, norms, uvs, cols, faces = [], [], [], [], []
    length = 0.0
    circ = 2 * math.pi * max(radii[0], 0.01)
    u_rep = max(1, round(circ / bark_tile))
    for i in range(n):
        if i:
            length += np.linalg.norm(pts[i] - pts[i - 1])
        a, b = frames[i]
        r0 = radii[i]
        t = i / (n - 1)
        c = col_fn(t)
        for j in range(sides + 1):
            ang = j / sides * 2 * math.pi
            d = a * math.cos(ang) + b * math.sin(ang)
            r = r0
            if buttress is not None:
                r *= buttress(ang, pts[i][2])
            if rings:
                r *= 1 + rings * max(math.sin(length * 2 * math.pi / 0.16), 0) ** 6
            verts.append(pts[i] + d * r)
            norms.append(d)
            uvs.append((j / sides * u_rep, length / bark_tile))
            cols.append(c)
    row = sides + 1
    for i in range(n - 1):
        for j in range(sides):
            p = i * row + j
            faces.append((p, p + 1, p + row + 1, p + row))
    if cap:
        # close the top (thin tips are left open: they end inside foliage)
        c0 = len(verts)
        verts.append(pts[-1])
        norms.append(tang[-1])
        uvs.append((0.5, length / bark_tile))
        cols.append(col_fn(1.0))
        base = (n - 1) * row
        for j in range(sides):
            faces.append((base + j, base + j + 1, c0))
    bld.add(verts, norms, uvs, faces, np.asarray(cols), tint)
    return length


def card(bld, origin, axis_up, axis_right, w, h, uv_rect, col, normal_bias=None, fold=0.0, tint=0.0):
    """A leaf card: bottom-centre at origin, height along axis_up; optional
    V fold along the centre line and normals bent toward normal_bias."""
    u0, v0, u1, v1 = uv_rect
    up = norm(axis_up)
    rt = norm(axis_right)
    fn = norm(np.cross(rt, up))
    lift = fn * (w * 0.5 * math.sin(fold))
    half = rt * (w * 0.5 * math.cos(fold))
    P = [origin - half + lift, origin, origin + half + lift,
         origin - half + lift + up * h, origin + up * h, origin + half + lift + up * h]
    uv = [(u0, v0), ((u0 + u1) / 2, v0), (u1, v0), (u0, v1), ((u0 + u1) / 2, v1), (u1, v1)]
    nn = fn if normal_bias is None else norm(fn * 0.35 + normal_bias * 0.65)
    N = [nn] * 6
    faces = [(0, 1, 4, 3), (1, 2, 5, 4)]
    bld.add(P, N, uv, faces, col, tint)


# ------------------------------------------------------------------ skeletons
class Branch:
    def __init__(self, pts, radii, level, phase):
        self.pts = np.asarray(pts, float)
        self.radii = np.asarray(radii, float)
        self.level = level
        self.phase = phase


def grow(g, start, direction, length, r0, r1, seg, bend_up, wander, droop=0.0):
    """Polyline growing from start: bends toward the sky (bend_up > 0) or
    sags (droop), wandering a little per segment."""
    n = max(3, int(round(length / seg)) + 1)
    pts = [np.asarray(start, float)]
    d = norm(np.asarray(direction, float))
    step = length / (n - 1)
    for i in range(1, n):
        d = norm(d + UP * bend_up * step - UP * droop * step * (i / n) + g.normal(0, wander, 3) * step)
        pts.append(pts[-1] + d * step)
    radii = np.linspace(r0, r1, n)
    return pts, radii


def point_on(br, t):
    n = len(br.pts)
    x = t * (n - 1)
    i = min(int(x), n - 2)
    f = x - i
    p = br.pts[i] * (1 - f) + br.pts[i + 1] * f
    r = br.radii[i] * (1 - f) + br.radii[i + 1] * f
    d = norm(br.pts[i + 1] - br.pts[i])
    return p, r, d


def child_dir(g, parent_dir, angle, azimuth):
    side = perpendicular(parent_dir)
    side = rotate(side, parent_dir, azimuth)
    return norm(rotate(parent_dir, side, angle))


# ------------------------------------------------------------------ species
def broadleaf(seed, umbrella=False):
    """Tropical canopy tree. umbrella=False: rounded, clumpy crown on a few
    scaffold limbs; umbrella=True: tiered, near-horizontal branches carrying
    flat layers of foliage (Terminalia / rain tree habit)."""
    g = rng(seed)
    H = g.uniform(11, 16) if not umbrella else g.uniform(9, 13)
    trunk_h = H * (g.uniform(0.32, 0.42) if not umbrella else g.uniform(0.3, 0.38))
    r_base = g.uniform(0.26, 0.36) * H / 13
    lean = norm(np.array([g.normal(0, 0.08), g.normal(0, 0.08), 1.0]))
    tp, trd = grow(g, [0, 0, -0.3], lean, trunk_h + 0.3 + (H * 0.25 if umbrella else 0), r_base, r_base * 0.62, 0.45, 0.0, 0.03)
    trunk = Branch(tp, trd, 0, 0.0)
    branches = [trunk]
    tips = []   # (point, direction, level, phase)
    fork_t = (trunk_h + 0.3) / (np.linalg.norm(tp[-1] - tp[0]) + 1e-6)
    if umbrella:
        tiers = int(g.integers(3, 5))
        limbs = []
        for k in range(tiers):
            t = min(fork_t + k * (1 - fork_t) / tiers, 0.97)
            for m in range(int(g.integers(3, 5))):
                az = m / 4 * 2 * math.pi + k * 0.9 + g.uniform(-0.3, 0.3)
                el = g.uniform(0.05, 0.28) + k * 0.06
                d = norm(np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)]))
                limbs.append((t, d, g.uniform(3.2, 5.5) * (1 - k * 0.15) * H / 11))
    else:
        limbs = []
        nl = int(g.integers(4, 7))
        for m in range(nl):
            t = min(fork_t + g.uniform(-0.06, 0.1), 0.98)
            az = m / nl * 2 * math.pi + g.uniform(-0.35, 0.35)
            el = g.uniform(0.35, 0.85)
            d = norm(np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)]))
            limbs.append((t, d, g.uniform(0.45, 0.62) * H))
        limbs.append((0.99, lean, H - trunk_h - 0.5))   # leader
    for li, (t, d, L1) in enumerate(limbs):
        p, r, _ = point_on(trunk, t)
        phase = g.uniform(0, 1)
        r1 = min(r * 0.62, 0.2)
        pts, rad = grow(g, p, d, L1, r1, r1 * 0.3, 0.35, 0.05 if umbrella else 0.11, 0.05)
        limb = Branch(pts, rad, 1, phase)
        branches.append(limb)
        # secondaries along the outer part of the limb
        ns = int(g.integers(7, 11))
        for k in range(ns):
            ts = g.uniform(0.28, 1.0) if k else 1.0
            ps, rs, ds = point_on(limb, ts)
            az = k * 2.4 + g.uniform(-0.3, 0.3)
            if umbrella:
                dd = norm(child_dir(g, ds, g.uniform(0.35, 0.8), az) * np.array([1, 1, 0.35]) + UP * 0.05)
            else:
                dd = child_dir(g, ds, g.uniform(0.4, 0.9), az)
            L2 = L1 * g.uniform(0.3, 0.46) * (1.15 - ts * 0.4)
            pts2, rad2 = grow(g, ps, dd, L2, max(rs * 0.6, 0.02), 0.012, 0.4, 0.1 if umbrella else 0.25, 0.08)
            sec = Branch(pts2, rad2, 2, phase)
            branches.append(sec)
            for q in range(int(g.integers(4, 7))):
                tq = g.uniform(0.3, 1.0)
                pq, rq, dq = point_on(sec, tq)
                dd3 = child_dir(g, dq, g.uniform(0.3, 0.8), q * 2.4 + g.uniform(0, 1))
                if umbrella:
                    dd3 = norm(dd3 * np.array([1, 1, 0.4]))
                L3 = g.uniform(0.8, 1.6)
                pts3, rad3 = grow(g, pq, dd3, L3, max(rq * 0.6, 0.012), 0.006, 0.45, 0.15, 0.1)
                tw = Branch(pts3, rad3, 3, phase)
                branches.append(tw)
                tips.append((tw, phase))
            tips.append((sec, phase))
    return dict(branches=branches, tips=tips, height=H, kind='umbrella' if umbrella else 'broad')


def dress_broadleaf(tree, g, lod):
    """Bark tubes and twig cards for a broadleaf skeleton."""
    bark, leaves = Builder(), Builder()
    H = tree['height']
    cell = ATLAS['broad']['cell']
    sides = {0: 14, 1: 8, 2: 5, 3: 3} if lod == 0 else {0: 8, 1: 5, 2: 3, 3: 3}
    maxlev = 3 if lod == 0 else 1
    flat = tree['kind'] == 'umbrella'

    def flex(p):
        return float(np.clip(p[2] / H, 0, 1)) ** 1.5

    for br in tree['branches']:
        if br.level > maxlev:
            continue
        buttress = None
        if br.level == 0:
            lobes = int(g.integers(4, 7))
            ph = g.uniform(0, 6.28)
            rb = br.radii[0]
            buttress = (lambda ang, z, lobes=lobes, ph=ph, rb=rb:
                        1 + 1.4 * max(math.cos(lobes * ang + ph), 0) ** 3 * math.exp(-max(z, 0) / (rb * 3.2)))
        lev = br.level
        col = (lambda t, br=br, lev=lev: (min(1.0, 0.12 * lev + flex(br.pts[min(int(t * (len(br.pts) - 1)), len(br.pts) - 1)])), br.phase, 0.0, 1.0))
        sweep(bark, br.pts, br.radii, sides[lev], col, bark_tile=1.4 if lev == 0 else 0.9, buttress=buttress, cap=lev <= 1)
    # crown extent for occlusion and bent normals
    tip_pts = np.array([b.pts[-1] for b, _ in tree['tips']])
    centre = tip_pts.mean(0)
    centre[2] = centre[2] * (0.92 if not flat else 0.97)
    ext = np.maximum(np.abs(tip_pts - centre).max(0), 0.5)
    n_cards = 0
    step = 1 if lod == 0 else 3
    for idx, (tw, phase) in enumerate(tree['tips']):
        per = 4 if tw.level == 3 else 3
        for k in range(per):
            if (idx * per + k) % step:
                continue
            t = 1.0 if k == 0 else g.uniform(0.35, 0.95)
            p, _, d = point_on(tw, t)
            # the twig points out along the branch, its face turned to the sky
            out = norm(d + norm(p - centre) * 0.6)
            up_face = UP if not flat else UP * 1.6
            right = norm(np.cross(out, up_face))
            if np.linalg.norm(np.cross(out, up_face)) < 1e-3:
                right = perpendicular(out)
            right = rotate(right, out, g.uniform(-0.6, 0.6))
            s = cell * g.uniform(1.25, 1.85) * (1.7 if lod else 1.0)
            cx = int(g.integers(0, 2))
            cy = int(g.integers(0, 2))
            uv = (cx * 0.5, cy * 0.5, cx * 0.5 + 0.5, cy * 0.5 + 0.5)
            rel = (p - centre) / ext
            depth = float(np.clip(np.linalg.norm(rel), 0, 1.2))
            occl = float(np.clip(0.3 + 0.75 * depth ** 1.3, 0.3, 1.0))
            bias = norm(rel + UP * 0.35)
            card(leaves, p - out * s * 0.08, out, right, s, s, uv, (1.0, phase, 1.0, occl), normal_bias=bias, fold=0.35)
            n_cards += 1
    return bark, leaves, n_cards


def palm(seed):
    """Coconut palm: curved ringed trunk, swollen bole, a spiral crown of
    arching V-folded fronds, a few dead ones hanging, coconuts."""
    g = rng(seed)
    H = g.uniform(7.5, 13.0)
    lean_dir = g.uniform(0, 2 * math.pi)
    lean = g.uniform(0.08, 0.35)
    pts = []
    for i in range(18):
        t = i / 17
        off = math.sin(t * math.pi * 0.55) * lean * H * t + t * t * 0.3 * lean * H
        pts.append(np.array([math.cos(lean_dir) * off, math.sin(lean_dir) * off, t * H - 0.3]))
    radii = [0.19 * (1 - t * 0.32) + 0.14 * (1 - t) ** 10 for t in np.linspace(0, 1, 18)]
    return dict(pts=pts, radii=radii, height=H, top=pts[-1], lean=lean, g=g, seed=seed)


def dress_palm(tree, g, lod):
    bark, leaves = Builder(), Builder()
    H = tree['height']
    top = tree['top']
    sweep(bark, tree['pts'], tree['radii'], 12 if lod == 0 else 7,
          lambda t: (t ** 1.3 * 0.8, 0.5, 0.0, 1.0), bark_tile=0.9, rings=0.05 if lod == 0 else 0.0, cap=True)
    Lr, Wd = ATLAS['palm']['length'], ATLAS['palm']['width']
    n = int(g.integers(19, 26))
    phase = g.uniform(0, 1)
    fronds = []
    for k in range(n):
        az = k * 2.39996 + g.uniform(-0.15, 0.15)
        age = k / n                                        # 0 young (upright) .. 1 old (drooping)
        el = math.radians(62 - 85 * age + g.uniform(-8, 8))
        L = Lr * g.uniform(0.85, 1.08) * (0.75 + 0.25 * min(1.0, age * 2.5))
        fronds.append((az, el, L, 0.0))
    for k in range(int(g.integers(1, 4))):                 # dead fronds hanging along the trunk
        fronds.append((g.uniform(0, 6.28), math.radians(-70 + g.uniform(-10, 10)), Lr * g.uniform(0.7, 0.9), 1.0))
    step = 1 if lod == 0 else 2
    for k, (az, el, L, dead) in enumerate(fronds):
        if k % step and not dead:
            continue
        d0 = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
        side = norm(np.array([-math.sin(az), math.cos(az), 0.0]))
        segs = 12 if lod == 0 else 6
        p = top + d0 * 0.25
        d = d0.copy()
        spine = [p.copy()]
        for i in range(segs):
            # the rachis arches: gravity bends it more toward the tip
            d = norm(d - UP * (0.09 + 0.02 * i) * (1.0 if not dead else 0.3))
            p = p + d * (L / segs)
            spine.append(p.copy())
        spine = np.array(spine)
        # V-folded ribbon: leaflets rise from the rachis on both sides, and
        # the fold opens toward the tip
        verts, uvs, norms, cols = [], [], [], []
        for i, sp in enumerate(spine):
            t = i / segs
            tg = norm(spine[min(i + 1, segs)] - spine[max(i - 1, 0)])
            sd = norm(side - tg * np.dot(side, tg))
            up = norm(np.cross(sd, tg))
            fold = math.radians(38 - 22 * t) if not dead else math.radians(70)
            w = Wd * 0.5 * (1 if not dead else 0.55)
            twist = g.uniform(-0.05, 0.05)
            for s_ in (-1, 0, 1):
                off = sd * (s_ * w * math.cos(fold)) + up * (abs(s_) * w * math.sin(fold))
                verts.append(sp + off + sd * twist * abs(s_))
                uvs.append((t, 0.5 + 0.5 * s_))
                norms.append(norm(up * 0.8 + norm(sp - top) * 0.2 + UP * 0.2))
                cols.append((min(1.0, 0.55 + 0.45 * t), phase, 1.0, 0.75 + 0.25 * t))
        faces = []
        for i in range(segs):
            a = i * 3
            faces += [(a, a + 1, a + 4, a + 3), (a + 1, a + 2, a + 5, a + 4)]
        leaves.add(verts, norms, uvs, faces, np.asarray(cols), tint=dead)
    # coconuts
    if lod == 0:
        for k in range(int(g.integers(4, 10))):
            az = g.uniform(0, 6.28)
            c = top + np.array([math.cos(az) * 0.28, math.sin(az) * 0.28, -0.3 - g.uniform(0, 0.25)])
            sph_v, sph_n, sph_f = uv_sphere(0.13, 7, 5)
            bark.add(sph_v + c, sph_n, np.zeros((len(sph_v), 2)), sph_f, (0.9, phase, 0.0, 0.8), tint=1.0)
    return bark, leaves, len(fronds)


def uv_sphere(r, seg, rings):
    v, n, f = [], [], []
    for i in range(rings + 1):
        th = i / rings * math.pi
        for j in range(seg):
            ph = j / seg * 2 * math.pi
            d = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)])
            v.append(d * r)
            n.append(d)
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            f.append((a, b, b + seg, a + seg))
    return np.array(v), np.array(n), f


def shrub(seed):
    g = rng(seed)
    H = g.uniform(1.2, 2.6)
    branches, tips = [], []
    for s in range(int(g.integers(4, 8))):
        az = g.uniform(0, 6.28)
        el = g.uniform(0.9, 1.35)
        d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
        pts, rad = grow(g, [g.normal(0, 0.08), g.normal(0, 0.08), -0.1], d, H * g.uniform(0.7, 1.0), 0.035, 0.01, 0.2, 0.1, 0.25)
        b = Branch(pts, rad, 1, g.uniform(0, 1))
        branches.append(b)
        for k in range(int(g.integers(3, 6))):
            t = g.uniform(0.3, 1.0)
            p, r, dd = point_on(b, t)
            dd2 = child_dir(g, dd, g.uniform(0.4, 1.0), g.uniform(0, 6.28))
            pts2, rad2 = grow(g, p, dd2, H * g.uniform(0.25, 0.45), r * 0.7, 0.006, 0.15, 0.1, 0.25)
            c = Branch(pts2, rad2, 2, b.phase)
            branches.append(c)
            tips.append((c, b.phase))
        tips.append((b, b.phase))
    return dict(branches=branches, tips=tips, height=H, kind='shrub')


def dress_shrub(tree, g, lod):
    bark, leaves = Builder(), Builder()
    H = tree['height']
    cell = ATLAS['shrub']['cell']
    if lod == 0:
        for br in tree['branches']:
            sweep(bark, br.pts, br.radii, 4, lambda t, br=br: (min(1.0, 0.3 + t * 0.6), br.phase, 0.0, 0.8), bark_tile=0.5)
    tip_pts = np.array([b.pts[-1] for b, _ in tree['tips']])
    centre = tip_pts.mean(0)
    centre[2] *= 0.7
    ext = np.maximum(np.abs(tip_pts - centre).max(0), 0.3)
    step = 1 if lod == 0 else 2
    k = 0
    for tw, phase in tree['tips']:
        for q in range(4):
            k += 1
            if k % step:
                continue
            t = 1.0 if q == 0 else g.uniform(0.3, 0.95)
            p, _, d = point_on(tw, t)
            out = norm(d + norm(p - centre) * 0.8)
            right = rotate(perpendicular(out), out, g.uniform(-0.8, 0.8))
            s = cell * g.uniform(1.1, 1.6) * (1.35 if lod else 1.0)
            cx, cy = int(g.integers(0, 2)), int(g.integers(0, 2))
            rel = (p - centre) / ext
            occl = float(np.clip(0.35 + 0.7 * np.linalg.norm(rel) ** 1.2, 0.35, 1.0))
            card(leaves, p - out * s * 0.1, out, right, s, s, (cx * 0.5, cy * 0.5, cx * 0.5 + 0.5, cy * 0.5 + 0.5),
                 (min(1.0, 0.4 + 0.6 * p[2] / H), phase, 1.0, occl), normal_bias=norm(rel + UP * 0.4), fold=0.3)
    return bark, leaves, k


def fern(seed):
    g = rng(seed)
    return dict(g=g, height=g.uniform(0.6, 1.1), count=int(g.integers(9, 15)), kind='fern')


def dress_fern(tree, g, lod):
    bark, leaves = Builder(), Builder()
    Lr, Wd = ATLAS['fern']['length'], ATLAS['fern']['width']
    for k in range(tree['count']):
        if lod and k % 2:
            continue
        az = k * 2.39996 + g.uniform(-0.2, 0.2)
        el = math.radians(g.uniform(35, 70))
        L = Lr * g.uniform(0.6, 1.0) * tree['height']
        side = np.array([-math.sin(az), math.cos(az), 0.0])
        d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
        p = np.array([0.0, 0.0, 0.02])
        spine = [p.copy()]
        segs = 8
        for i in range(segs):
            d = norm(d - UP * 0.2)
            p = p + d * (L / segs)
            spine.append(p.copy())
        verts, uvs, norms, cols = [], [], [], []
        w = Wd * 0.5 * L / Lr
        for i, sp in enumerate(spine):
            t = i / segs
            tg = norm(spine[min(i + 1, segs)] - spine[max(i - 1, 0)])
            up = norm(np.cross(side, tg))
            for s_ in (-1, 0, 1):
                verts.append(sp + side * s_ * w * 0.94 + up * abs(s_) * w * 0.25)
                uvs.append((t, 0.5 + 0.5 * s_))
                norms.append(norm(up + UP * 0.3))
                cols.append((0.5 + 0.5 * t, g.uniform(0, 1), 1.0, 0.6 + 0.4 * t))
        faces = []
        for i in range(segs):
            a = i * 3
            faces += [(a, a + 1, a + 4, a + 3), (a + 1, a + 2, a + 5, a + 4)]
        leaves.add(verts, norms, uvs, faces, np.asarray(cols))
    return bark, leaves, tree['count']


def ironwood(seed):
    """Casuarina: tall and irregular, ascending limbs that fork, the whole
    crown hung with fine drooping sprays in soft layers."""
    g = rng(seed)
    H = g.uniform(12, 17)
    r_base = 0.24 * H / 14
    lean = norm(np.array([g.normal(0, 0.06), g.normal(0, 0.06), 1.0]))
    tp, trd = grow(g, [0, 0, -0.3], lean, H, r_base, 0.02, 0.6, 0.0, 0.025)
    trunk = Branch(tp, trd, 0, 0.0)
    branches, tips = [trunk], []
    nl = int(g.integers(16, 24))
    for k in range(nl):
        t = g.uniform(0.25, 0.97)
        p, r, d = point_on(trunk, t)
        dd = child_dir(g, d, g.uniform(0.55, 1.05), k * 2.39996)
        L = H * g.uniform(0.2, 0.36) * (1.3 - t * 0.75)
        pts, rad = grow(g, p, dd, L, max(r * 0.5, 0.02), 0.008, 0.35, 0.12, 0.08)
        b = Branch(pts, rad, 1, g.uniform(0, 1))
        branches.append(b)
        for q in range(int(g.integers(2, 4))):
            tq = g.uniform(0.35, 0.9)
            pq, rq, dq = point_on(b, tq)
            d2 = child_dir(g, dq, g.uniform(0.4, 0.9), q * 2.4 + g.uniform(0, 1))
            pts2, rad2 = grow(g, pq, d2, L * g.uniform(0.35, 0.55), max(rq * 0.6, 0.01), 0.005, 0.4, 0.1, 0.1)
            b2 = Branch(pts2, rad2, 2, b.phase)
            branches.append(b2)
            for w in range(int(g.integers(3, 6))):
                pw, _, dw = point_on(b2, g.uniform(0.2, 1.0))
                tips.append((pw, dw, b.phase))
        for w in range(int(g.integers(5, 9))):
            pq, _, dq = point_on(b, g.uniform(0.25, 1.0))
            tips.append((pq, dq, b.phase))
    return dict(branches=branches, tips=tips, height=H, kind='ironwood')


def dress_ironwood(tree, g, lod):
    bark, leaves = Builder(), Builder()
    H = tree['height']
    cell = ATLAS['needle']['cell']
    for br in tree['branches']:
        if br.level > (1 if lod else 2):
            continue
        sweep(bark, br.pts, br.radii, 10 if br.level == 0 and lod == 0 else (5 if br.level == 1 else 3),
              lambda t, br=br: (min(1.0, 0.1 + 0.9 * t) if br.level else t * 0.6, br.phase, 0.0, 1.0), bark_tile=1.0, cap=True)
    step = 1 if lod == 0 else 2
    n = 0
    for k, (p, d, phase) in enumerate(tree['tips']):
        for q in range(2):
            n += 1
            if n % step:
                continue
            s = cell * g.uniform(1.6, 2.4) * (1.3 if lod else 1.0)
            az = g.uniform(0, 6.28)
            right = np.array([math.cos(az), math.sin(az), 0.0])
            down = norm(np.array([d[0] * 0.25, d[1] * 0.25, -1.0]))
            # sprays hang from the branch: the card's top edge at the branch
            origin = p + down * s * 0.95 + norm(np.array([d[0], d[1], 0])) * g.uniform(0, 0.4)
            cx = int(g.integers(0, 2))
            card(leaves, origin, -down, right, s * 0.5, s, (cx * 0.5, 1.0, cx * 0.5 + 0.5, 0.0),
                 (min(1.0, 0.5 + 0.5 * p[2] / H), phase, 1.0, 0.85), normal_bias=norm(np.array([p[0], p[1], 0.3])), fold=0.2)
    return bark, leaves, n


SPECIES = {
    'broad': (lambda s: broadleaf(s), dress_broadleaf, [21, 22, 23, 24], 'broad'),
    'umbrella': (lambda s: broadleaf(s, umbrella=True), dress_broadleaf, [51, 52], 'broad'),
    'palm': (palm, dress_palm, [11, 12, 13, 14], 'palm'),
    'ironwood': (ironwood, dress_ironwood, [61, 62], 'needle'),
    'shrub': (shrub, dress_shrub, [41, 42, 43], 'shrub'),
    'fern': (fern, dress_fern, [71, 72], 'fern'),
}


# ------------------------------------------------------------------ export
def to_object(name, bld, mat):
    arr = bld.arrays()
    if arr is None:
        return None
    v, n, uv, uv2, col, faces = arr
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], faces)
    loop_v = np.zeros(len(me.loops), np.int32)
    me.loops.foreach_get('vertex_index', loop_v)
    l1 = me.uv_layers.new(name='UVMap')
    l1.data.foreach_set('uv', uv[loop_v].ravel())
    l2 = me.uv_layers.new(name='UVMap.001')
    l2.data.foreach_set('uv', uv2[loop_v].ravel())
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', col.ravel())
    me.color_attributes.active_color = ca
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    me.normals_split_custom_set(n[loop_v].tolist())
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def build(names):
    reset()
    mats = {}
    for m in ('bark', 'leaves'):
        mats[m] = bpy.data.materials.new(m)
    info = {}
    for sp in names:
        make, dress, seeds, atlas = SPECIES[sp]
        info[sp] = {'atlas': atlas, 'variants': []}
        for vi, seed in enumerate(seeds):
            tree = make(seed)
            entry = {'height': round(float(tree['height']), 2)}
            for lod in (0, 1):
                g = rng(seed * 7 + lod)
                bark, leaves, cards = dress(tree, g, lod)
                parts = []
                for part, bld in (('bark', bark), ('leaves', leaves)):
                    ob = to_object(f'{sp}_{vi}_lod{lod}_{part}', bld, mats[part])
                    if ob is not None:
                        parts.append(ob)
                        entry[f'lod{lod}_{part}_verts'] = bld.count
                entry[f'lod{lod}_cards'] = cards
            info[sp]['variants'].append(entry)
            print(sp, vi, entry)
    return info


def export(path):
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=False,
        export_texcoords=True, export_normals=True, export_vertex_color='ACTIVE',
        export_all_vertex_colors=False, export_materials='PLACEHOLDER', export_apply=False,
        export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
        export_draco_position_quantization=14, export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12, export_draco_color_quantization=10,
        export_yup=True)


if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(SPECIES)
    info = build(names)
    path = os.path.join(OUT, 'plants.glb')
    export(path)
    meta_path = os.path.join(OUT, 'plants.json')
    with open(meta_path, 'w') as f:
        json.dump(info, f, indent=1)
    print('wrote', path, os.path.getsize(path) // 1024, 'KiB')
