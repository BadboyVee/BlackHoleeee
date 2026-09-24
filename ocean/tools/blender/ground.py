"""Tileable ground materials for the terrain, built as real geometry in
Blender and rendered straight down with Cycles.

    grass    turf: thousands of leaning, curled blades over soil
    forest   leaf litter: fallen leaves (the leaves.py blades), twigs,
             seeds and soil
    rock     weathered basalt: a displaced grid (periodic fBm + cracks)
             with lichen
    soil     red-brown volcanic soil: clods and scattered stones

Every tile wraps: scattered pieces that cross an edge are repeated on the
opposite side, and the procedural fields are periodic (spectral synthesis).

Outputs (assets/terrain/<name>_c.webp, <name>_n.webp):
    _c   albedo (sRGB), roughness in alpha
    _n   normal xy, height, cavity AO

usage: python tools/blender/ground.py [names...]
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from lib import ASSETS, linear_to_srgb, mesh_object, ortho_camera, render_passes, reset, rng, save_image, to_u8  # noqa: E402
from leaves import PROFILES, blade, hsv_jitter, place  # noqa: E402

OUT = os.path.join(ASSETS, 'terrain')
PX = 1024


# ------------------------------------------------------------------ periodic fields
def fbm_field(n, seed, beta=2.0, lo=2, hi=None):
    """Periodic fBm on an n x n grid by spectral synthesis, normalized to [0, 1]."""
    g = rng(seed)
    f = np.fft.fftfreq(n) * n
    kx, ky = np.meshgrid(f, f)
    k = np.sqrt(kx ** 2 + ky ** 2)
    amp = np.where(k >= lo, 1 / np.maximum(k, 1) ** (beta / 2), 0)
    if hi:
        amp *= np.exp(-(k / hi) ** 2)
    spec = (g.normal(size=(n, n)) + 1j * g.normal(size=(n, n))) * amp
    field = np.real(np.fft.ifft2(spec))
    field -= field.min()
    return field / (field.max() + 1e-9)


def worley(n, points, seed):
    """Periodic Worley F1, F2 on an n x n grid (unit tile)."""
    g = rng(seed)
    pts = g.random((points, 2))
    ys, xs = np.mgrid[0:n, 0:n] / n
    f1 = np.full((n, n), 9.0)
    f2 = np.full((n, n), 9.0)
    idx = np.zeros((n, n), np.int32)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xs - px)
        dx = np.minimum(dx, 1 - dx)
        dy = np.abs(ys - py)
        dy = np.minimum(dy, 1 - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        idx = np.where(closer, i, idx)
        f1 = np.where(closer, d, f1)
    return f1 * math.sqrt(points), f2 * math.sqrt(points), idx


def image_texture(name, rgb):
    """numpy (H, W, 3) linear colour -> blender image (float)"""
    h, w = rgb.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=False, float_buffer=True)
    px = np.concatenate([rgb[::-1], np.ones((h, w, 1))], -1).astype(np.float32)
    im.pixels.foreach_set(px.ravel())
    im.colorspace_settings.name = 'Linear Rec.709'
    im.pack()                    # Cycles would otherwise re-generate a blank image
    return im


def plane_material(name, img, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = img
    t.extension = 'REPEAT'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = roughness
    return m


def vcol_material(name, roughness=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    a = nt.nodes.new('ShaderNodeAttribute')
    a.attribute_name = 'Col'
    nt.links.new(a.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = roughness
    return m


def grid_mesh(name, T, n, height, colors, material):
    """a T x T grid (n x n quads) displaced by height (n+1 x n+1), per-vertex colours"""
    ys, xs = np.mgrid[0:n + 1, 0:n + 1] / n * T
    v = np.stack([xs.ravel(), ys.ravel(), height.ravel()], 1)
    idx = np.arange((n + 1) * (n + 1)).reshape(n + 1, n + 1)
    a = idx[:-1, :-1].ravel()
    faces = np.stack([a, a + 1, a + n + 2, a + n + 1], 1)
    cols = np.concatenate([colors.reshape(-1, 3), np.ones(((n + 1) * (n + 1), 1))], 1)
    return mesh_object(name, v, faces.tolist(), colors=cols, material=material)


def wrap_copies(T, x, y, reach):
    """offsets (dx, dy) that repeat a piece at (x, y) across the tile edges"""
    out = [(0.0, 0.0)]
    xs = [0.0] + ([T] if x < reach else []) + ([-T] if x > T - reach else [])
    ys = [0.0] + ([T] if y < reach else []) + ([-T] if y > T - reach else [])
    for dx in xs:
        for dy in ys:
            if dx or dy:
                out.append((dx, dy))
    return out


def dome(c, r, flat, rings=3, seg=7):
    """a pebble: the top of a squashed sphere sitting at c"""
    v, f = [], []
    for k in range(rings):
        th = k / rings * math.pi / 2                  # 0 at the rim .. up
        for j in range(seg):
            ph = j / seg * 2 * math.pi
            v.append((c[0] + math.cos(ph) * math.cos(th) * r, c[1] + math.sin(ph) * math.cos(th) * r, c[2] + math.sin(th) * r * flat))
    top = len(v)
    v.append((c[0], c[1], c[2] + r * flat))
    for k in range(rings - 1):
        for j in range(seg):
            a = k * seg + j
            f.append((a, k * seg + (j + 1) % seg, (k + 1) * seg + (j + 1) % seg, (k + 1) * seg + j))
    for j in range(seg):
        f.append(((rings - 1) * seg + j, (rings - 1) * seg + (j + 1) % seg, top))
    return v, f


def periodic_sample(field, T, x, y):
    n = field.shape[0]
    return field[int(y / T * n) % n, int(x / T * n) % n]


# ------------------------------------------------------------------ render + pack
def render_tile(name, T, roughness, samples=32, ao=0.02, height_range=None):
    ortho_camera((T / 2, T / 2), T, T, PX, PX, height=20)
    P = render_passes(samples=samples, passes=('DiffCol', 'Normal', 'Depth', 'AO', 'Alpha'), ao_distance=ao)
    albedo = P['DiffCol'][..., :3]
    nrm = P['Normal'][..., :3]
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-6
    z = 20 - P['Depth'][..., 0]
    z = np.where(np.isfinite(z) & (z > -5), z, 0)
    lo, hi = height_range if height_range else (np.percentile(z, 1), np.percentile(z, 99.5))
    h01 = np.clip((z - lo) / max(hi - lo, 1e-4), 0, 1)
    occl = np.clip(P['AO'][..., 0], 0, 1)
    rough = roughness if np.ndim(roughness) else np.full(h01.shape, roughness)
    c = np.concatenate([linear_to_srgb(albedo), rough[..., None]], -1)
    n = np.concatenate([nrm[..., :2] * 0.5 + 0.5, h01[..., None], occl[..., None]], -1)
    s1 = save_image(os.path.join(OUT, f'{name}_c.webp'), to_u8(c), quality=90)
    s2 = save_image(os.path.join(OUT, f'{name}_n.webp'), to_u8(n), quality=84)
    print(f'{name}: {T} m tile, albedo mean {albedo.reshape(-1, 3).mean(0).round(3)}, colour {s1 // 1024} KiB, normal {s2 // 1024} KiB')


# ------------------------------------------------------------------ materials
def grass():
    reset()
    T = 2.0
    g = rng(11)
    # soil underneath, barely visible between the blades
    soil = fbm_field(256, 5, 2.2)
    soil_rgb = (0.07 + 0.045 * soil)[..., None] * np.array([1.0, 0.8, 0.58])
    bpy.ops.mesh.primitive_plane_add(size=T, location=(T / 2, T / 2, 0))
    bpy.context.object.data.materials.append(plane_material('soil', image_texture('soil', soil_rgb)))
    # patches: denser, greener clumps and thinner, drier ones
    clump = fbm_field(128, 7, 2.5)
    dry = fbm_field(128, 9, 2.8)
    mat = vcol_material('blade', 0.55)
    verts, faces, cols = [], [], []
    count = 0
    n_blades = 34000
    for _ in range(n_blades):
        x, y = g.random() * T, g.random() * T
        c = periodic_sample(clump, T, x, y)
        if g.random() > 0.35 + 0.65 * c:
            continue
        L = g.uniform(0.05, 0.16) * (0.7 + 0.5 * c)
        W = g.uniform(0.003, 0.006)
        lean = g.uniform(0.35, 1.25)                     # from vertical
        yaw = g.uniform(0, 2 * math.pi)
        curl = g.uniform(0.2, 0.9)
        dr = periodic_sample(dry, T, x, y)
        r = g.random()
        if r < 0.05 + 0.25 * dr:
            base = (0.2, 0.17, 0.07)                      # dry, straw-coloured
        elif r < 0.09 + 0.25 * dr:
            base = (0.09, 0.065, 0.035)                   # dead, brown
        else:
            base = (0.06 + 0.04 * dr, 0.12 + 0.02 * c, 0.028)
        col = hsv_jitter(base, g, 0.02, 0.12, 0.22)
        # blade centre line: rises, leans, curls over
        segs = 5
        pts, wid = [], []
        for k in range(segs + 1):
            t = k / segs
            el = math.pi / 2 - lean * (0.4 + t * curl)
            rr = L * t
            pts.append((math.cos(el) * rr * 0.9, math.sin(el) * rr))
            wid.append(W * (1 - t ** 1.6))
        side = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
        fwd = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        for dx, dy in wrap_copies(T, x, y, L):
            b = len(verts)
            for k in range(segs + 1):
                p = np.array([x + dx, y + dy, 0.0]) + fwd * pts[k][0] + np.array([0, 0, pts[k][1]])
                verts.append(p - side * wid[k])
                verts.append(p + side * wid[k])
                cols.append((*col, 1.0))
                cols.append((*col, 1.0))
            for k in range(segs):
                a = b + k * 2
                faces.append((a, a + 1, a + 3, a + 2))
        count += 1
    mesh_object('blades', np.array(verts), faces, colors=np.array(cols), material=mat)
    print('grass blades', count)
    render_tile('grass', T, 0.9, samples=24, ao=0.03)


def forest():
    reset()
    T = 2.0
    g = rng(21)
    soil = fbm_field(256, 3, 2.0)
    soil_rgb = (0.03 + 0.03 * soil)[..., None] * np.array([1.0, 0.75, 0.5])
    bpy.ops.mesh.primitive_plane_add(size=T, location=(T / 2, T / 2, 0))
    bpy.context.object.data.materials.append(plane_material('soil', image_texture('soil', soil_rgb)))
    mat = vcol_material('litter', 0.8)
    verts, faces, cols = [], [], []
    z = 0.001
    palette = [(0.2, 0.11, 0.04), (0.28, 0.17, 0.06), (0.14, 0.08, 0.035), (0.33, 0.24, 0.08), (0.09, 0.06, 0.03), (0.07, 0.1, 0.03)]
    for i in range(2600):
        x, y = g.random() * T, g.random() * T
        L = g.uniform(0.04, 0.14)
        prof = ['elliptic', 'obovate', 'lanceolate', 'ovate'][int(g.integers(0, 4))]
        v, uvs, fc = blade(L, L * g.uniform(0.35, 0.55), PROFILES[prof], g.uniform(0.0, 0.3), g.uniform(-0.3, 0.1), g.uniform(-0.3, 0.3), seg_l=8, seg_w=2, wave=g.uniform(0, 0.4))
        col = hsv_jitter(palette[int(g.integers(0, len(palette)))], g, 0.03, 0.15, 0.25)
        z += 0.00002
        for dx, dy in wrap_copies(T, x, y, L):
            vv = place(v, (x + dx, y + dy, z), g.uniform(0, 6.283), 0.0)
            vv[:, 2] = np.maximum(vv[:, 2], 0.0005) + z
            b = len(verts)
            verts.extend(vv)
            cols.extend([(*col, 1.0)] * len(vv))
            faces.extend([tuple(i + b for i in f) for f in fc])
    # twigs
    for i in range(70):
        x, y = g.random() * T, g.random() * T
        L = g.uniform(0.08, 0.35)
        a = g.uniform(0, 6.283)
        r = g.uniform(0.002, 0.006)
        col = hsv_jitter((0.12, 0.08, 0.045), g)
        for dx, dy in wrap_copies(T, x, y, L):
            p0 = np.array([x + dx, y + dy, r + 0.004])
            d = np.array([math.cos(a), math.sin(a), 0.0])
            side = np.array([-d[1], d[0], 0.0])
            b = len(verts)
            for t in (0.0, 1.0):
                p = p0 + d * L * t
                for k in range(4):
                    ang = k / 4 * 2 * math.pi
                    verts.append(p + side * math.cos(ang) * r + np.array([0, 0, math.sin(ang) * r]))
                    cols.append((*col, 1.0))
            for k in range(4):
                faces.append((b + k, b + (k + 1) % 4, b + 4 + (k + 1) % 4, b + 4 + k))
    mesh_object('litter', np.array(verts), faces, colors=np.array(cols), material=mat)
    render_tile('forest', T, 0.85, samples=24, ao=0.02)


def warped_worley(n, points, seed, warp, wseed):
    """Worley cells on a domain warped by periodic fBm: irregular fracture lines"""
    wx = (fbm_field(n, wseed, 2.2, lo=1) - 0.5) * warp
    wy = (fbm_field(n, wseed + 1, 2.2, lo=1) - 0.5) * warp
    g = rng(seed)
    pts = g.random((points, 2))
    ys, xs = np.mgrid[0:n, 0:n] / n
    xs = (xs + wx) % 1.0
    ys = (ys + wy) % 1.0
    f1 = np.full((n, n), 9.0)
    f2 = np.full((n, n), 9.0)
    for px, py in pts:
        dx = np.abs(xs - px)
        dx = np.minimum(dx, 1 - dx)
        dy = np.abs(ys - py)
        dy = np.minimum(dy, 1 - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        f1 = np.where(closer, d, f1)
    return f1 * math.sqrt(points), f2 * math.sqrt(points)


def rock():
    reset()
    T, n = 4.0, 512
    big = fbm_field(n + 1, 31, 2.3, lo=1)
    mid = fbm_field(n + 1, 39, 2.0, lo=3)
    f1, f2 = warped_worley(n + 1, 14, 32, 0.35, 50)
    g1, g2 = warped_worley(n + 1, 45, 33, 0.25, 52)
    # a few deep, wandering fractures and many faint hairline ones
    crack = np.clip((f2 - f1) / 0.16, 0, 1) ** 0.7
    crack2 = np.clip((g2 - g1) / 0.07, 0, 1)
    fade2 = fbm_field(n + 1, 53, 2.5, lo=2)
    crack2 = 1 - (1 - crack2) * np.clip((fade2 - 0.4) * 3, 0, 1)
    grain = fbm_field(n + 1, 34, 1.3, lo=10)
    h = (big * 0.6 + mid * 0.25 + grain * 0.07) * (0.3 + 0.7 * crack) * (0.85 + 0.15 * crack2)
    height = h * 0.22
    tone = fbm_field(n + 1, 35, 2.1)
    base = np.stack([0.075 + 0.1 * tone, 0.072 + 0.09 * tone, 0.066 + 0.076 * tone], -1)
    base *= (0.8 + 0.35 * mid)[..., None]
    lich = np.clip((fbm_field(n + 1, 37, 2.6, lo=3) - 0.6) / 0.12, 0, 1) * crack
    base = base * (1 - lich[..., None] * 0.5) + np.array([0.34, 0.31, 0.17]) * lich[..., None] * 0.5
    white = np.clip((fbm_field(n + 1, 38, 2.8, lo=4) - 0.7) / 0.1, 0, 1) * crack
    base = base * (1 - white[..., None] * 0.3) + np.array([0.4, 0.4, 0.38]) * white[..., None] * 0.3
    # dark weathering streaks run down the face (the tile's +y is up-slope)
    streak = fbm_field(n + 1, 54, 2.0, lo=1)
    streak = np.clip((np.roll(streak, 0, 0) - 0.55) * 4, 0, 1) * 0.25
    base *= (1 - streak)[..., None] * (0.35 + 0.65 * crack * crack2)[..., None]
    grid_mesh('rock', T, n, height, base, vcol_material('rock', 0.8))
    render_tile('rock', T, 0.85, samples=24, ao=0.12)


def soil():
    reset()
    T, n = 2.0, 512
    clods = fbm_field(n + 1, 41, 2.2, lo=2)
    fine = fbm_field(n + 1, 42, 1.5, lo=10)
    f1, f2 = warped_worley(n + 1, 10, 43, 0.3, 60)
    crack = 1 - (1 - np.clip((f2 - f1) / 0.05, 0, 1)) * 0.6
    height = (clods * 0.6 + fine * 0.15) * (0.6 + 0.4 * crack) * 0.05
    tone = fbm_field(n + 1, 44, 2.3)
    base = np.stack([0.1 + 0.06 * tone, 0.066 + 0.036 * tone, 0.044 + 0.022 * tone], -1) * (0.8 + 0.2 * crack)[..., None]
    grid_mesh('soil', T, n, height, base, vcol_material('soil', 0.9))
    g = rng(45)
    mat = vcol_material('stones', 0.7)
    verts, faces, cols = [], [], []
    for i in range(160):
        x, y = g.random() * T, g.random() * T
        r = g.uniform(0.006, 0.03)
        col = hsv_jitter((0.11, 0.1, 0.09), g, 0.02, 0.2, 0.35)
        hz = periodic_sample(height, T, x, y)
        for dx, dy in wrap_copies(T, x, y, r * 1.5):
            dv, df = dome((x + dx, y + dy, hz), r, 0.6)
            b = len(verts)
            verts.extend(dv)
            cols.extend([(*col, 1.0)] * len(dv))
            faces.extend([tuple(i + b for i in f) for f in df])
    mesh_object('stones', np.array(verts), faces, colors=np.array(cols), material=mat)
    render_tile('soil', T, 0.9, samples=24, ao=0.03)


MATERIALS = {'grass': grass, 'forest': forest, 'rock': rock, 'soil': soil}

if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or list(MATERIALS)
    os.makedirs(OUT, exist_ok=True)
    for n_ in names:
        MATERIALS[n_]()
