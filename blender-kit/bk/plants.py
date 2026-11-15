"""bk.plants -- procedural vegetation: palms, broadleaf trees, hedges, shrubs, lawn grass, potted plants."""
import math
import random

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import mats
from .core import MB, PI, TAU, R, T, rad


# --------------------------------------------------------------------------
# materials
# --------------------------------------------------------------------------
def m_palm_leaf():
    return mats.leaf("palm_leaflet", '#27481a', '#48702a', trans=0.3, rough=0.4)


def m_leaf(name="leaf_green", c1='#2b4a1b', c2='#547a2c', trans=0.3):
    return mats.leaf(name, c1, c2, trans=trans)


def m_rachis():
    return mats.plain("palm_rachis", '#7c8a3c', rough=0.5)


def m_trunk_palm():
    return mats.bark("palm_trunk", '#958e7e', '#5f594e', scale=0.5, rings=42.0)


def m_bark():
    return mats.bark("tree_bark", '#5c4a3a', '#2b2119', scale=1.0)


# --------------------------------------------------------------------------
# leaves
# --------------------------------------------------------------------------
def _strip(V, F, UV, p, d, n, length, width, droop=0.3, segs=4, rng=None):
    """Narrow drooping leaflet as a quad strip (appended to python lists)."""
    s = d.cross(n)
    if s.length < 1e-6:
        return
    s.normalize()
    base = len(V)
    for k in range(segs + 1):
        t = k / segs
        c = p + d * (length * t) + Vector((0, 0, -1)) * (droop * length * t * t)
        hw = max(0.002, width / 2 * (1 - t ** 1.6) * (0.55 + 0.45 * math.sin(PI * min(1.0, t * 1.6 + 0.2))))
        V.append(tuple(c - s * hw))
        V.append(tuple(c + s * hw))
    for k in range(segs):
        a = base + k * 2
        F.append((a, a + 1, a + 3, a + 2))
        UV.extend([(k / segs, 0), (k / segs, 1), ((k + 1) / segs, 1), ((k + 1) / segs, 0)])


def frond(mb, origin, yaw, phi0, phi1, L, pairs, leaf_len, leaf_w, rng, leaf_mat, rachis_mat, r0=0.03,
          droop=0.35, vee=0.3):
    """Feather (pinnate) palm frond: curved rachis with leaflet pairs."""
    N = 22
    pos = Vector(origin)
    pts, tans = [pos.copy()], []
    side0 = Vector((-math.sin(yaw), math.cos(yaw), 0))
    for i in range(N):
        t = (i + 0.5) / N
        phi = phi0 + (phi1 - phi0) * t ** 1.4
        d = Vector((math.sin(phi) * math.cos(yaw), math.sin(phi) * math.sin(yaw), math.cos(phi)))
        pos = pos + d * (L / N)
        pts.append(pos.copy())
        tans.append(d)
    tans.append(tans[-1])
    mb.tube(pts, r0, rachis_mat, segs=6, radii=[r0 * (1 - 0.85 * i / N) for i in range(N + 1)], caps=False)
    V, F, UV = [], [], []
    for j in range(pairs):
        t = 0.1 + 0.88 * j / max(1, pairs - 1)
        f = t * N
        i = min(N - 1, int(f))
        p = pts[i].lerp(pts[i + 1], f - i)
        tau = tans[i]
        n = side0.cross(tau).normalized()
        ll = leaf_len * max(0.25, math.sin(PI * t ** 0.75) ** 0.55) * rng.uniform(0.85, 1.1)
        for sgn in (-1, 1):
            d = (side0 * sgn + tau * rng.uniform(0.25, 0.5) + n * vee * rng.uniform(0.6, 1.3)).normalized()
            _strip(V, F, UV, p, d, n, ll, leaf_w * rng.uniform(0.8, 1.15), droop * rng.uniform(0.7, 1.3), 4)
    mb.raw(V, F, UV, leaf_mat, True)


def broad_leaf(mb, M, length, width, mat, droop=0.25, fold=0.18, nu=6, nv=4, wave=0.0, phase=0.0):
    """Ovate leaf with a midrib fold, base at the local origin pointing along +X."""
    def fn(u, v):
        s = (v - 0.5) * 2
        half = width / 2 * np.sin(PI * np.clip(u, 0, 1) ** 0.85) ** 0.9
        x = u * length
        y = s * half
        z = np.abs(s) * half * fold - droop * length * u * u + wave * np.sin(u * 9 + phase) * np.abs(s)
        return x, y, z
    mb.grid(fn, nu, nv, mat, m=M, su=length, sv=width)


# --------------------------------------------------------------------------
# palms / trees
# --------------------------------------------------------------------------
def palm(name="royal_palm", height=7.5, n_fronds=17, seed=3, lean=0.35, c=None):
    rng = random.Random(seed)
    mb = MB(name)
    hz = height
    path, radii = [], []
    ang = rng.uniform(0, TAU)
    for i in range(15):
        t = i / 14
        z = t * hz
        off = lean * t * t
        path.append((off * math.cos(ang), off * math.sin(ang), z))
        radii.append(0.2 + 0.11 * math.exp(-z * 1.6) + 0.035 * math.exp(-((z - hz * 0.45) / (hz * 0.22)) ** 2))
    mb.tube(path, 0.2, m_trunk_palm(), segs=18, radii=radii, caps=True)
    top = Vector(path[-1])
    cs = [tuple(top + Vector((0, 0, z))) for z in (0, 0.3, 0.7, 1.05, 1.3)]
    mb.tube(cs, 0.17, mats.plain("palm_crownshaft", '#5a7a33', rough=0.45), segs=16,
            radii=[0.2, 0.19, 0.165, 0.13, 0.07], caps=True)
    org = top + Vector((0, 0, 1.15))
    lm, rm = m_palm_leaf(), m_rachis()
    for i in range(n_fronds):
        a = i / (n_fronds - 1)
        yaw = i * rad(137.5) + rng.uniform(-0.15, 0.15)
        phi0 = rad(8 + a * 58)
        phi1 = rad(55 + a * 95 + rng.uniform(-8, 8))
        L = (2.6 + 1.1 * math.sin(PI * (0.15 + 0.85 * a))) * rng.uniform(0.92, 1.08)
        frond(mb, org, yaw, phi0, phi1, L, int(34 * L / 3.2), 0.72, 0.04, rng, lm, rm)
    return mb.finish(c=c)


def tree(name="tree", height=7.0, crown=3.0, seed=1, leaf=('#2c4a1b', '#58802c'), c=None, leaf_size=0.11,
         per_cluster=220):
    """Simple broadleaf tree for the neighbourhood: branching skeleton + clusters of leaf cards."""
    rng = random.Random(seed)
    mb = MB(name)
    bark = m_bark()
    lm = m_leaf(f"leaf_{name}", leaf[0], leaf[1])
    tips = []

    def grow(p, d, length, r, depth):
        q = p + d * length
        mid = p.lerp(q, 0.5) + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * length * 0.06
        mb.tube([p, mid, q], r, bark, segs=8 if depth < 2 else 5, radii=[r, r * 0.85, r * 0.68], caps=False)
        if depth >= 3:
            tips.append(q)
            tips.append(p.lerp(q, 0.55))
            return
        for _ in range(3):
            nd = (d + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.1, 0.75))) * 0.95).normalized()
            grow(q, nd, length * rng.uniform(0.58, 0.78), r * 0.62, depth + 1)

    trunk_h = height * 0.38
    grow(Vector((0, 0, 0)), Vector((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 1)).normalized(), trunk_h,
         0.11 + height * 0.014, 0)
    V, F, UV = [], [], []
    cr = crown * 0.2
    for tp in tips:
        for _ in range(per_cluster):
            p = tp + Vector((rng.gauss(0, cr), rng.gauss(0, cr), rng.gauss(0, cr * 0.75)))
            n = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0.7, 1))).normalized()
            t = n.orthogonal().normalized()
            t = (Matrix.Rotation(rng.uniform(0, TAU), 3, n) @ t)
            b = n.cross(t)
            L, w = leaf_size * rng.uniform(0.7, 1.3), leaf_size * 0.55
            base = len(V)
            V.extend([tuple(p - b * w * 0.5), tuple(p + t * L * 0.5 - b * w * 0.55), tuple(p + t * L),
                      tuple(p + t * L * 0.5 + b * w * 0.55), tuple(p + b * w * 0.5)])
            F.append((base, base + 1, base + 2, base + 3, base + 4))
            UV.extend([(0, 0), (0.5, 0), (1, 0.5), (0.5, 1), (0, 1)])
    mb.raw(V, F, UV, lm, True)
    return mb.finish(c=c)


# --------------------------------------------------------------------------
# leafy surfaces: hedges and shrubs
# --------------------------------------------------------------------------
def _leaf_cards(mb, pts, nrm, mat, size=0.045, rng=None, lift=0.02):
    rng = rng or random.Random(1)
    V, F, UV = [], [], []
    for p, n in zip(pts, nrm):
        n = (Vector(n) + Vector((rng.gauss(0, 0.55), rng.gauss(0, 0.55), rng.gauss(0, 0.55)))).normalized()
        t = n.orthogonal().normalized()
        t = Matrix.Rotation(rng.uniform(0, TAU), 3, n) @ t
        b = n.cross(t)
        L = size * rng.uniform(0.7, 1.35)
        w = L * 0.55
        p = Vector(p) + Vector(n) * rng.uniform(-lift * 0.3, lift)
        base = len(V)
        V.extend([tuple(p - t * L * 0.5), tuple(p - b * w * 0.5), tuple(p + t * L * 0.5), tuple(p + b * w * 0.5)])
        F.append((base, base + 1, base + 2, base + 3))
        UV.extend([(0, 0.5), (0.5, 0), (1, 0.5), (0.5, 1)])
    mb.raw(V, F, UV, mat, True)


def hedge(mb, x0, y0, x1, y1, h, z0=0.0, density=1700, seed=1, mat=None, core=None, leaf=0.045):
    """Clipped box hedge: dark core + thousands of leaf cards on the five visible faces."""
    rng = random.Random(seed)
    mat = mat or m_leaf("hedge_leaf", '#24401a', '#44682a', trans=0.25)
    core = core or mats.plain("hedge_core", '#0e1a09', rough=1.0)
    ins = 0.035
    mb.bx(x0 + ins, y0 + ins, z0, x1 - ins, y1 - ins, z0 + h - ins, core)
    faces = [((x0, y0, z0), (x1 - x0, 0, 0), (0, 0, h), (0, -1, 0)), ((x0, y1, z0), (x1 - x0, 0, 0), (0, 0, h), (0, 1, 0)),
             ((x0, y0, z0), (0, y1 - y0, 0), (0, 0, h), (-1, 0, 0)), ((x1, y0, z0), (0, y1 - y0, 0), (0, 0, h), (1, 0, 0)),
             ((x0, y0, z0 + h), (x1 - x0, 0, 0), (0, y1 - y0, 0), (0, 0, 1))]
    pts, nrm = [], []
    for o, u, v, n in faces:
        area = Vector(u).length * Vector(v).length
        for _ in range(int(area * density)):
            a, b = rng.random(), rng.random()
            pts.append((o[0] + u[0] * a + v[0] * b, o[1] + u[1] * a + v[1] * b, o[2] + u[2] * a + v[2] * b))
            nrm.append(n)
    _leaf_cards(mb, pts, nrm, mat, leaf, rng)


def shrub(mb, loc, r=0.5, h=None, seed=1, mat=None, flowers=None, density=1500, leaf=0.05):
    """Rounded bush (ixora / boxwood ball).  flowers: colour for scattered blossom clusters."""
    rng = random.Random(seed)
    h = h or r * 1.7
    mat = mat or m_leaf("shrub_leaf", '#2a4a1c', '#4f7a2c', trans=0.25)
    core = mats.plain("hedge_core", '#0e1a09', rough=1.0)
    cx, cy, cz = loc
    mb.sphere(1.0, (cx, cy, cz + h * 0.5), core, segs=16, rings=10, scale=(r * 0.9, r * 0.9, h * 0.47))
    area = 4 * PI * ((r * r + r * h / 2 + r * h / 2) / 3)
    pts, nrm = [], []
    for _ in range(int(area * density)):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
        if v.z < -0.75:
            continue
        k = 1 + 0.12 * math.sin(v.x * 7 + seed) * math.cos(v.y * 6 + seed * 2)
        pts.append((cx + v.x * r * k, cy + v.y * r * k, cz + h * 0.5 + v.z * h * 0.5 * k))
        nrm.append(tuple(v))
    _leaf_cards(mb, pts, nrm, mat, leaf, rng)
    if flowers:
        fm = mats.plain(f"petal_{flowers}", flowers, rough=0.6)
        for _ in range(int(14 * r / 0.5)):
            v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), abs(rng.gauss(0.3, 1)))).normalized()
            p = (cx + v.x * r * 1.03, cy + v.y * r * 1.03, cz + h * 0.5 + v.z * h * 0.52)
            for _ in range(7):
                q = (p[0] + rng.gauss(0, 0.025), p[1] + rng.gauss(0, 0.025), p[2] + rng.gauss(0, 0.02))
                mb.sphere(0.018, q, fm, segs=6, rings=4)


# --------------------------------------------------------------------------
# grass
# --------------------------------------------------------------------------
def add_grass(o, count, length=0.07, children=20, seed=1, mat=None, clump=0.35, width=0.0045):
    """Hair-particle lawn on object *o* (all faces emit)."""
    mat = mat or mats.grass_strand()
    if mat.name not in [m.name for m in o.data.materials if m]:
        o.data.materials.append(mat)
    slot = [m.name if m else '' for m in o.data.materials].index(mat.name) + 1
    md = o.modifiers.new("grass", 'PARTICLE_SYSTEM')
    ps = md.particle_system
    s = ps.settings
    s.type = 'HAIR'
    s.count = count
    s.hair_length = length
    s.hair_step = 4
    s.render_step = 3
    s.display_step = 2
    s.emit_from = 'FACE'
    s.distribution = 'RAND'
    s.use_even_distribution = True
    s.use_advanced_hair = True
    s.length_random = 0.55
    s.factor_random = 0.022
    s.brownian_factor = 0.012
    s.normal_factor = 0.035
    s.child_type = 'INTERPOLATED'
    s.child_percent = max(1, children // 10)
    s.rendered_child_count = children
    s.child_length = 1.0
    s.child_length_threshold = 0.0
    s.child_radius = 0.045
    s.child_roundness = 0.4
    s.clump_factor = clump
    s.clump_shape = 0.2
    s.roughness_1 = 0.012
    s.roughness_1_size = 0.12
    s.roughness_endpoint = 0.02
    s.roughness_2 = 0.012
    s.roughness_2_size = 0.05
    s.material = slot
    s.root_radius = 1.0
    s.tip_radius = 0.1
    s.radius_scale = width
    s.shape = 0.2
    ps.seed = seed
    return ps


# --------------------------------------------------------------------------
# potted plants
# --------------------------------------------------------------------------
def pot(mb, r=0.18, h=0.36, mat=None, loc=(0, 0, 0), style='taper', soil=True, m=None, lip=0.012):
    mat = mat or mats.ceramic("pot_white", '#ebe8e2', rough=0.25)
    if style == 'taper':
        prof = [(0, 0), (r * 0.68, 0), (r * 0.72, 0.01), (r, h), (r - lip, h), (r * 0.7 - lip, 0.04), (0, 0.04)]
    elif style == 'cyl':
        prof = [(0, 0), (r - 0.01, 0), (r, 0.01), (r, h), (r - lip, h), (r - lip, 0.04), (0, 0.04)]
    elif style == 'bowl':
        prof = [(0, 0), (r * 0.45, 0), (r * 0.8, h * 0.3), (r, h * 0.75), (r * 0.97, h), (r * 0.97 - lip, h),
                (r - lip, h * 0.75), (r * 0.8 - lip, h * 0.33), (0, 0.04)]
    else:  # belly
        prof = [(0, 0), (r * 0.55, 0), (r * 0.9, h * 0.2), (r, h * 0.5), (r * 0.85, h * 0.85), (r * 0.72, h),
                (r * 0.72 - lip, h), (r * 0.85 - lip, h * 0.85), (r - lip, h * 0.5), (0, 0.04)]
    M = T(*loc) if m is None else m @ T(*loc)
    mb.lathe(prof, mat, segs=36, m=M)
    if soil:
        top = r * (0.72 if style == 'belly' else 0.97) - lip
        mb.lathe([(0, h - 0.035), (top, h - 0.04)], mats.soil(), segs=24, m=M)
    return h


def snake_plant(mb, loc=(0, 0, 0), n=11, h=0.75, seed=1, pot_r=0.16, pot_h=0.3, pot_mat=None, m=None):
    rng = random.Random(seed)
    M0 = T(*loc) if m is None else m @ T(*loc)
    pot(mb, pot_r, pot_h, pot_mat, m=M0, style='cyl')
    lm = mats.leaf("snake_leaf", '#1f3d22', '#56733a', trans=0.1, rough=0.35)
    for i in range(n):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0, pot_r * 0.55)
        hh = h * rng.uniform(0.55, 1.0)
        tilt = rng.uniform(2, 14)
        M = M0 @ T(rr * math.cos(a), rr * math.sin(a), pot_h - 0.04) @ R(math.degrees(a)) @ R(-90 + tilt, 'Y')
        broad_leaf(mb, M @ R(rng.uniform(0, 360), 'X'), hh, 0.075, lm, droop=-0.02, fold=0.5, nu=8, nv=2, wave=0.006,
                   phase=rng.uniform(0, 6))


def fiddle_fig(mb, loc=(0, 0, 0), h=1.7, seed=2, pot_r=0.21, pot_h=0.38, pot_mat=None, m=None, leaves=26):
    rng = random.Random(seed)
    M0 = T(*loc) if m is None else m @ T(*loc)
    pot(mb, pot_r, pot_h, pot_mat, m=M0, style='taper')
    bark = mats.plain("fig_stem", '#4a3b2a', rough=0.8)
    lm = mats.leaf("fig_leaf", '#1e3a17', '#3f6424', trans=0.18, rough=0.3)
    base = Vector((0, 0, pot_h - 0.04))
    pts = [base, base + Vector((0.02, 0.01, h * 0.35)), base + Vector((-0.02, 0.03, h * 0.7)), base + Vector((0.01, 0, h - pot_h))]
    mb.tube(pts, 0.014, bark, segs=8, radii=[0.016, 0.014, 0.011, 0.007], m=M0)
    for i in range(leaves):
        t = 0.3 + 0.7 * i / (leaves - 1)
        seg = t * 3
        k = min(2, int(seg))
        p = pts[k].lerp(pts[k + 1], seg - k)
        yaw = i * 137.5 + rng.uniform(-15, 15)
        up = rng.uniform(15, 55)
        L = rng.uniform(0.2, 0.3) * (0.75 + 0.5 * (1 - abs(t - 0.6)))
        M = M0 @ T(*p) @ R(yaw) @ R(-up, 'Y')
        broad_leaf(mb, M @ T(0.03, 0, 0), L, L * 0.62, lm, droop=0.45, fold=0.22, nu=6, nv=4, wave=0.012,
                   phase=rng.uniform(0, 6))
        mb.rod(tuple((M0 @ T(*p)).translation), tuple((M @ T(0.035, 0, 0)).translation), 0.003, bark, segs=5)


def areca(mb, loc=(0, 0, 0), h=1.6, seed=3, pot_r=0.22, pot_h=0.4, pot_mat=None, m=None, n=11):
    rng = random.Random(seed)
    M0 = T(*loc) if m is None else m @ T(*loc)
    pot(mb, pot_r, pot_h, pot_mat, m=M0, style='belly')
    lm = mats.leaf("areca_leaf", '#2e5a1e', '#5e8f33', trans=0.3)
    rm = mats.plain("areca_stem", '#8fa04a', rough=0.5)
    mb.push(M0)
    for i in range(n):
        yaw = i * rad(137.5) + rng.uniform(-0.2, 0.2)
        a = i / (n - 1)
        L = h * rng.uniform(0.7, 1.0)
        org = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), pot_h - 0.05)
        frond(mb, org, yaw, rad(4 + a * 22), rad(40 + a * 55), L, int(16 * L / 1.2), 0.3 * h / 1.6, 0.022, rng, lm, rm,
              r0=0.008, droop=0.25, vee=0.45)
    mb.pop()


def succulent(mb, loc=(0, 0, 0), r=0.07, seed=4, pot_mat=None, m=None):
    rng = random.Random(seed)
    M0 = T(*loc) if m is None else m @ T(*loc)
    ph = pot(mb, r * 0.95, r * 1.1, pot_mat or mats.concrete("pot_concrete", '#9a9893', bump=0.1), m=M0, style='cyl', lip=0.006)
    lm = mats.plain("succulent", '#5f8d6a', rough=0.45)
    for ring, (cnt, ln, up) in enumerate(((7, r * 1.0, 20), (6, r * 0.8, 42), (5, r * 0.55, 62), (3, r * 0.35, 80))):
        for i in range(cnt):
            yaw = i * 360 / cnt + ring * 25 + rng.uniform(-6, 6)
            M = M0 @ T(0, 0, ph - 0.01) @ R(yaw) @ R(-up, 'Y')
            broad_leaf(mb, M, ln, ln * 0.55, lm, droop=-0.25, fold=0.5, nu=4, nv=2)


def stems_in_vase(mb, loc=(0, 0, 0), h=0.55, n=7, seed=5, kind='eucalyptus', m=None, spread=0.35, z0=0.2):
    """Loose arrangement of stems rising out of a vase mouth at z0 above loc."""
    rng = random.Random(seed)
    M0 = T(*loc) if m is None else m @ T(*loc)
    stem = mats.plain("stem_brown", '#5a4a34', rough=0.7)
    if kind == 'eucalyptus':
        lm = mats.plain("eucalyptus_leaf", '#6f8f7c', rough=0.55)
    elif kind == 'pampas':
        lm = mats.plain("pampas", '#d9cbb0', rough=0.95)
    else:
        lm = m_leaf("stem_leaf", '#2f5a22', '#5b8a35')
    for i in range(n):
        a = rng.uniform(0, TAU)
        sp = rng.uniform(0.05, spread)
        hh = h * rng.uniform(0.7, 1.05)
        p0 = Vector((0, 0, z0 - 0.15))
        p1 = Vector((math.cos(a) * sp * 0.25, math.sin(a) * sp * 0.25, z0 + hh * 0.5))
        p2 = Vector((math.cos(a) * sp * hh, math.sin(a) * sp * hh, z0 + hh))
        pts = [p0.lerp(p1, t) * (1 - t) + p1.lerp(p2, t) * t for t in [k / 8 for k in range(9)]]
        mb.tube(pts, 0.0025, stem, segs=5, m=M0, caps=False)
        if kind == 'pampas':
            for k in range(60):
                t = rng.uniform(0.55, 1.0)
                q = pts[min(8, int(t * 8))]
                d = Vector((rng.gauss(0, 0.5), rng.gauss(0, 0.5), rng.uniform(0.2, 1))).normalized()
                mb.rod(tuple(M0 @ q), tuple(M0 @ (q + d * rng.uniform(0.03, 0.07))), 0.0012, lm, segs=3, caps=False)
        else:
            for k in range(3, 9):
                q = pts[k]
                for s in (-1, 1):
                    yaw = math.degrees(a) + 90 * s + rng.uniform(-30, 30)
                    M = M0 @ T(*q) @ R(yaw) @ R(rng.uniform(-40, 10), 'Y')
                    L = 0.045 if kind == 'eucalyptus' else 0.07
                    broad_leaf(mb, M, L, L * (0.9 if kind == 'eucalyptus' else 0.5), lm, droop=0.1, fold=0.1, nu=3, nv=2)


def flowers_in_vase(mb, loc=(0, 0, 0), n=9, h=0.3, seed=6, color='#f2ede4', m=None, z0=0.2):
    rng = random.Random(seed)
    M0 = T(*loc) if m is None else m @ T(*loc)
    stem = mats.plain("flower_stem", '#3f6a2a', rough=0.6)
    pm = mats.plain(f"petals_{color}", color, rough=0.7, sheen=0.3)
    lm = m_leaf("stem_leaf", '#2f5a22', '#5b8a35')
    for i in range(n):
        a = rng.uniform(0, TAU)
        sp = rng.uniform(0.0, 0.3)
        hh = h * rng.uniform(0.75, 1.1)
        p0 = Vector((0, 0, z0 - 0.12))
        p2 = Vector((math.cos(a) * sp * hh, math.sin(a) * sp * hh, z0 + hh))
        mb.tube([p0, p0.lerp(p2, 0.5) + Vector((0, 0, 0.02)), p2], 0.003, stem, segs=5, m=M0, caps=False)
        for k in range(9):
            yaw = k * 40 + rng.uniform(-8, 8)
            up = 25 + (k % 3) * 22
            M = M0 @ T(*p2) @ R(yaw) @ R(-up, 'Y')
            broad_leaf(mb, M, 0.04, 0.035, pm, droop=-0.6, fold=0.3, nu=3, nv=2)
        q = p0.lerp(p2, 0.6)
        M = M0 @ T(*q) @ R(math.degrees(a) + rng.uniform(-60, 60)) @ R(-30, 'Y')
        broad_leaf(mb, M, 0.08, 0.035, lm, droop=0.2, fold=0.2, nu=3, nv=2)
