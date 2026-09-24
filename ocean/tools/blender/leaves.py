"""Leaf and twig card atlases for the vegetation, modelled and rendered in Blender.

Each twig is real geometry - folded, drooping leaf blades with veins, on a
stem - rendered straight down with Cycles. The render passes become the
card textures the trees use:

    <name>_c.webp   albedo (sRGB) + coverage alpha, colour bled into the
                    empty texels so mip levels have no dark fringes
    <name>_n.webp   tangent-space normal (xy), ambient occlusion, 255

usage (from the ocean/ folder, with the bpy module installed):

    python tools/blender/leaves.py [names...]
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from lib import (ASSETS, dilate, linear_to_srgb, mesh_object, ortho_camera, render_passes, reset, rng,  # noqa: E402
                 save_image, to_u8)

OUT = os.path.join(ASSETS, 'vegetation')


# ------------------------------------------------------------------ materials
def leaf_material(name, gloss=0.45, vein=0.35):
    """Per-leaf colour from the 'Col' attribute; midrib and lateral veins from the UVs."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    L = nt.links
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = gloss
    uv = N.new('ShaderNodeUVMap')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(uv.outputs['UV'], sep.inputs[0])
    col = N.new('ShaderNodeAttribute')
    col.attribute_name = 'Col'

    def math_node(op, a=None, b_=None, va=None, vb=None):
        n = N.new('ShaderNodeMath')
        n.operation = op
        if a is not None:
            L.new(a, n.inputs[0])
        elif va is not None:
            n.inputs[0].default_value = va
        if b_ is not None:
            L.new(b_, n.inputs[1])
        elif vb is not None:
            n.inputs[1].default_value = vb
        return n.outputs[0]

    across = math_node('ABSOLUTE', math_node('SUBTRACT', sep.outputs['X'], vb=0.5))       # 0 at the midrib
    along = sep.outputs['Y']
    # midrib: a thin line, fading toward the tip
    mid = math_node('SUBTRACT', va=1.0, b_=math_node('MINIMUM', math_node('DIVIDE', across, vb=0.022), vb=1.0))
    mid = math_node('MULTIPLY', mid, math_node('SUBTRACT', va=1.0, b_=math_node('MULTIPLY', along, vb=0.55)))
    # lateral veins: arcs from the midrib toward the margin and the tip
    ph = math_node('ADD', math_node('MULTIPLY', along, vb=10.0), math_node('MULTIPLY', across, vb=-7.0))
    lat = math_node('COSINE', math_node('MULTIPLY', ph, vb=2 * math.pi))
    lat = math_node('POWER', math_node('MAXIMUM', lat, vb=0.0), vb=24.0)
    lat = math_node('MULTIPLY', lat, math_node('SUBTRACT', va=1.0, b_=math_node('MULTIPLY', across, vb=1.7)))
    veins = math_node('MAXIMUM', mid, math_node('MULTIPLY', lat, vb=0.55))
    # mottling
    noise = N.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 18.0
    noise.inputs['Detail'].default_value = 4.0
    L.new(uv.outputs['UV'], noise.inputs['Vector'])
    mott = math_node('ADD', math_node('MULTIPLY', noise.outputs['Fac'], vb=0.35), vb=0.82)
    base = N.new('ShaderNodeMix')
    base.data_type = 'RGBA'
    base.blend_type = 'MULTIPLY'
    base.inputs[0].default_value = 1.0
    L.new(col.outputs['Color'], base.inputs[6])
    comb = N.new('ShaderNodeCombineXYZ')
    for k in ('X', 'Y', 'Z'):
        L.new(mott, comb.inputs[k])
    L.new(comb.outputs[0], base.inputs[7])
    # veins are paler and a touch yellower
    vcol = N.new('ShaderNodeMix')
    vcol.data_type = 'RGBA'
    L.new(math_node('MULTIPLY', veins, vb=vein), vcol.inputs[0])
    L.new(base.outputs[2], vcol.inputs[6])
    bright = N.new('ShaderNodeMix')
    bright.data_type = 'RGBA'
    bright.blend_type = 'MULTIPLY'
    bright.inputs[0].default_value = 1.0
    L.new(base.outputs[2], bright.inputs[6])
    bright.inputs[7].default_value = (1.9, 1.9, 1.3, 1)
    L.new(bright.outputs[2], vcol.inputs[7])
    L.new(vcol.outputs[2], b.inputs['Base Color'])
    # sunken veins
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.002
    L.new(math_node('MULTIPLY', veins, vb=-1.0), bump.inputs['Height'])
    L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def stem_material(color=(0.09, 0.07, 0.035)):
    m = bpy.data.materials.new('stem')
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.7
    return m


# ------------------------------------------------------------------ geometry
def blade(length, width, profile, fold, droop, roll, seg_l=16, seg_w=5, wave=0.0, r=None):
    """A leaf blade in its own frame: base at the origin, midrib along +Y, upper side +Z."""
    verts, uvs, faces = [], [], []
    for i in range(seg_l + 1):
        t = i / seg_l
        w = width * 0.5 * profile(t)
        for j in range(-seg_w, seg_w + 1):
            s = j / seg_w
            x = s * w
            y = t * length
            z = -abs(s) * w * fold - droop * t * t * length
            if wave:
                z += math.sin(t * 9 + s * 2) * wave * w * abs(s)
            # roll about the midrib
            c, sn = math.cos(roll), math.sin(roll)
            verts.append((x * c - z * sn, y, x * sn + z * c))
            uvs.append((0.5 + 0.5 * s, t))
    row = 2 * seg_w + 1
    for i in range(seg_l):
        for j in range(row - 1):
            a = i * row + j
            faces.append((a, a + 1, a + row + 1, a + row))
    return np.array(verts), np.array(uvs), faces


def place(verts, origin, yaw, pitch):
    """Rotate a blade (pitch about X, then yaw about Z) and move it to origin."""
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    v = verts.copy()
    y = v[:, 1] * cp - v[:, 2] * sp
    z = v[:, 1] * sp + v[:, 2] * cp
    x = v[:, 0]
    return np.stack([x * cy - y * sy + origin[0], x * sy + y * cy + origin[1], z + origin[2]], 1)


def tube(points, radius0, radius1, sides=6):
    verts, faces = [], []
    pts = np.asarray(points, float)
    n = len(pts)
    for i, p in enumerate(pts):
        t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        t /= np.linalg.norm(t) + 1e-9
        a = np.cross(t, [0, 0, 1])
        if np.linalg.norm(a) < 1e-3:
            a = np.cross(t, [1, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(t, a)
        r = radius0 + (radius1 - radius0) * i / (n - 1)
        for k in range(sides):
            ang = k / sides * 2 * math.pi
            verts.append(p + (a * math.cos(ang) + b * math.sin(ang)) * r)
    for i in range(n - 1):
        for k in range(sides):
            a0 = i * sides + k
            a1 = i * sides + (k + 1) % sides
            faces.append((a0, a1, a1 + sides, a0 + sides))
    return np.array(verts), faces


def hsv_jitter(base, g, hue=0.03, sat=0.15, val=0.18):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*base)
    h = (h + g.uniform(-hue, hue)) % 1
    s = min(max(s * (1 + g.uniform(-sat, sat)), 0), 1)
    v = v * (1 + g.uniform(-val, val))
    return colorsys.hsv_to_rgb(h, s, v)


PROFILES = {
    'elliptic': lambda t: math.sin(math.pi * min(t * 1.02, 1.0)) ** 0.85 * (1 - 0.1 * t),
    'obovate': lambda t: (min(t, 1.0) ** 0.75 * max(1 - t, 0.0) ** 0.45) / 0.55,
    'lanceolate': lambda t: math.sin(math.pi * min(t, 1.0)) ** 0.7 * (1 - t) ** 0.25,
    'ovate': lambda t: (min(t, 1.0) ** 0.45 * max(1 - t, 0.0) ** 0.8) / 0.49,
}


def leaf_at(g, p, yaw, spec, scale, leaf_mat, z):
    L = spec['length'] * g.uniform(0.75, 1.15) * scale
    Wd = L * spec['aspect'] * g.uniform(0.85, 1.1)
    v, uv, fc = blade(L, Wd, PROFILES[spec['profile']], spec['fold'] * g.uniform(0.6, 1.3),
                      spec['droop'] * g.uniform(0.5, 1.4), g.uniform(-0.45, 0.45), wave=spec.get('wave', 0.0))
    # petiole offset, then pitch toward/away from the camera for depth
    pitch = g.uniform(-0.45, 0.35)
    pet = np.array([-math.sin(yaw), math.cos(yaw), 0]) * spec['petiole']
    v = place(v, p + pet + np.array([0, 0, z]), yaw, pitch)
    c = spec['color']
    roll = g.random()
    if roll < spec.get('yellow', 0.08):
        c = (c[0] * 1.7, c[1] * 1.3, c[2] * 0.85)          # an older, yellowing leaf
    elif roll < spec.get('yellow', 0.08) + 0.08:
        c = (c[0] * 0.72, c[1] * 0.75, c[2] * 0.8)         # a shaded, darker one
    c = hsv_jitter(c, g)
    mesh_object('leaf', v, fc, uvs=uv, colors=np.tile([*c, 1.0], (len(v), 1)), material=leaf_mat)
    return pet


def bezier(a, b, c, n):
    return [(1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for t in np.linspace(0, 1, n)]


def twig(seed, cx, cy, cell, spec, leaf_mat, stem_mat):
    """One twig card: a stem rising up the cell with side shoots; leaves at
    alternate nodes and a crowded tuft at every shoot tip."""
    g = rng(seed)
    base = np.array([cx + g.uniform(-0.03, 0.03) * cell, cy - cell * 0.47, 0.0])
    top = np.array([cx + g.uniform(-0.1, 0.1) * cell, cy + cell * spec.get('reach', 0.3), 0.02])
    ctrl = (base + top) / 2 + np.array([g.uniform(-0.08, 0.08) * cell, 0, 0.03])
    main = bezier(base, ctrl, top, 12)
    shoots = [(main, spec['stem'])]
    for k in range(spec.get('shoots', 2)):
        t = g.uniform(0.3, 0.62)
        i = int(t * 11)
        a = main[i]
        side = 1 if k % 2 == 0 else -1
        ang = side * g.uniform(0.55, 0.95)
        L = cell * g.uniform(0.28, 0.4)
        end = a + np.array([math.sin(-ang) * L, math.cos(ang) * L * 0.8, 0.015])
        mid = (a + end) / 2 + np.array([0, -0.03 * cell, 0.01])
        shoots.append((bezier(a, mid, end, 8), spec['stem'] * 0.7))
    z = 0.0
    for si, (pts, r0) in enumerate(shoots):
        sv, sf = tube(pts, r0 * 1.4, r0 * 0.55, 6)
        mesh_object('stem', sv, sf, material=stem_mat)
        n = spec['count'] if si == 0 else max(4, spec['count'] // 2)
        tuft = spec['tuft'] if si == 0 else max(3, spec['tuft'] - 1)
        m = len(pts) - 1
        for k in range(n):
            tip = k >= n - tuft
            t = 0.2 + 0.75 * (k / max(n - tuft - 1, 1)) if not tip else 0.97
            t = min(t, 0.97)
            i = min(int(t * m), m - 1)
            f = t * m - i
            p = pts[i] * (1 - f) + pts[i + 1] * f
            d = pts[min(i + 1, m)] - pts[i]
            heading = math.atan2(-d[0], d[1])
            side = 1 if k % 2 else -1
            yaw = heading + (g.uniform(-1.2, 1.2) if tip else side * g.uniform(0.7, 1.2) * (1 - t * 0.3))
            scale = 0.8 + 0.4 * math.sin(math.pi * min(t, 0.95))
            z += 0.0015
            pet = leaf_at(g, p, yaw, spec, scale, leaf_mat, z)
            pv, pf = tube([p, p + pet * 1.02], spec['stem'] * 0.5, spec['stem'] * 0.4, 4)
            mesh_object('pet', pv, pf, material=stem_mat)


# ------------------------------------------------------------------ atlases
def render_atlas(name, size_px, world_w, world_h, samples=24, ao=0.06, meta=None):
    ortho_camera((world_w / 2, world_h / 2), world_w, world_h, size_px[0], size_px[1])
    P = render_passes(samples=samples, passes=('Alpha', 'DiffCol', 'Normal', 'AO'), ao_distance=ao)
    a = P['Alpha'][..., 0]
    inv = 1 / np.maximum(a, 1e-4)
    albedo = P['DiffCol'][..., :3] * inv[..., None]
    occl = np.clip(P['AO'][..., 0] * inv, 0, 1)
    albedo *= (0.55 + 0.45 * occl)[..., None]
    nrm = P['Normal'][..., :3] * inv[..., None]
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-6
    albedo = dilate(albedo, a)
    nrm = dilate(nrm, a)
    occl = dilate(occl[..., None], a)[..., 0]
    c = np.concatenate([linear_to_srgb(albedo), a[..., None]], -1)
    n = np.concatenate([nrm[..., :2] * 0.5 + 0.5, occl[..., None], np.ones_like(a)[..., None]], -1)
    s1 = save_image(os.path.join(OUT, f'{name}_c.webp'), to_u8(c), quality=92)
    s2 = save_image(os.path.join(OUT, f'{name}_n.webp'), to_u8(n), quality=95)
    cover = float((a > 0.5).mean())
    print(f'{name}: colour {s1 // 1024} KiB, normal {s2 // 1024} KiB, coverage {cover:.2f}')
    return {'width': world_w, 'height': world_h, 'coverage': cover, **(meta or {})}


def broadleaf_atlas():
    """2x2 twigs of a glossy tropical broadleaf (Terminalia-like rosettes)."""
    reset()
    cell = 0.72
    lm = leaf_material('leaf', gloss=0.4)
    sm = stem_material()
    specs = [
        dict(count=13, tuft=6, shoots=2, length=0.2, aspect=0.46, profile='obovate', fold=0.18, droop=0.12, petiole=0.02, stem=0.0045, color=(0.05, 0.11, 0.026)),
        dict(count=12, tuft=5, shoots=2, length=0.21, aspect=0.5, profile='obovate', fold=0.22, droop=0.18, petiole=0.024, stem=0.005, color=(0.055, 0.12, 0.028)),
        dict(count=15, tuft=6, shoots=3, length=0.16, aspect=0.42, profile='elliptic', fold=0.2, droop=0.1, petiole=0.018, stem=0.004, color=(0.045, 0.1, 0.024)),
        dict(count=13, tuft=5, shoots=2, length=0.18, aspect=0.48, profile='elliptic', fold=0.15, droop=0.2, petiole=0.02, stem=0.0045, color=(0.06, 0.118, 0.03), yellow=0.12),
    ]
    for k, spec in enumerate(specs):
        cx = cell * (k % 2 + 0.5)
        cy = cell * (k // 2 + 0.5)
        twig(100 + k, cx, cy, cell, spec, lm, sm)
    return render_atlas('leaves_broad', (1024, 1024), cell * 2, cell * 2, meta={'cells': [2, 2], 'cell': cell})


def shrub_atlas():
    """2x2 twigs of small-leaved shrubs (hibiscus / sea grape scrub)."""
    reset()
    cell = 0.5
    lm = leaf_material('leaf', gloss=0.5, vein=0.25)
    sm = stem_material((0.08, 0.06, 0.035))
    specs = [
        dict(count=17, tuft=5, shoots=3, length=0.09, aspect=0.6, profile='ovate', fold=0.15, droop=0.1, petiole=0.012, stem=0.003, color=(0.05, 0.1, 0.024), wave=0.15, reach=0.32),
        dict(count=19, tuft=6, shoots=3, length=0.08, aspect=0.55, profile='elliptic', fold=0.2, droop=0.15, petiole=0.01, stem=0.0028, color=(0.06, 0.115, 0.03), reach=0.34),
        dict(count=15, tuft=4, shoots=3, length=0.1, aspect=0.7, profile='ovate', fold=0.1, droop=0.08, petiole=0.015, stem=0.003, color=(0.07, 0.12, 0.035), yellow=0.12, wave=0.2, reach=0.3),
        dict(count=21, tuft=6, shoots=3, length=0.07, aspect=0.45, profile='lanceolate', fold=0.25, droop=0.2, petiole=0.008, stem=0.0025, color=(0.045, 0.095, 0.022), reach=0.34),
    ]
    for k, spec in enumerate(specs):
        twig(200 + k, cell * (k % 2 + 0.5), cell * (k // 2 + 0.5), cell, spec, lm, sm)
    return render_atlas('leaves_shrub', (1024, 1024), cell * 2, cell * 2, meta={'cells': [2, 2], 'cell': cell})


def leaflet_yaw(ang, side):
    """yaw for place() so a blade (+Y along it) points forward along +X at `ang`
    from the rachis, to the +Y side (side > 0) or the -Y side."""
    return ang - math.pi / 2 if side > 0 else -ang - math.pi / 2


def palm_frond_atlas():
    """A coconut frond, flat: rachis along +X, drooping leaflets angled toward the tip."""
    reset()
    Lr, Wd = 4.2, 1.05                        # card: 4.2 m x 1.05 m
    lm = leaf_material('leaflet', gloss=0.35, vein=0.12)
    sm = stem_material((0.11, 0.1, 0.045))
    g = rng(7)
    y0 = Wd / 2
    # rachis tapers toward the tip
    pts = [(x, y0 + 0.01 * math.sin(x * 2), 0) for x in np.linspace(0.02, Lr - 0.05, 30)]
    rv, rf = tube(pts, 0.035, 0.006, 6)
    mesh_object('rachis', rv, rf, material=sm)
    count = 92
    for side in (-1, 1):
        for k in range(count):
            t = (k + g.uniform(-0.3, 0.3)) / count
            if g.random() < 0.05:
                continue                            # a torn-out leaflet
            x = 0.12 + t * (Lr - 0.2)
            env = math.sin(math.pi * min(t * 0.92 + 0.08, 1.0)) ** 0.6
            L = (0.52 * env + 0.06) * g.uniform(0.9, 1.08)
            wdt = 0.032 * (0.7 + 0.5 * env) * g.uniform(0.85, 1.1)
            v, uv, fc = blade(L, wdt, PROFILES['lanceolate'], 0.55, g.uniform(0.25, 0.5), g.uniform(-0.2, 0.2), seg_l=10, seg_w=2)
            ang = math.radians(g.uniform(48, 62)) * (1 - 0.25 * t)
            vv = place(v, (x, y0, 0.01), leaflet_yaw(ang, side), g.uniform(-0.1, 0.1))
            c = hsv_jitter((0.085, 0.15, 0.03), g, 0.02, 0.1, 0.15)
            if t > 0.85 and g.random() < 0.3:
                c = (c[0] * 1.8, c[1] * 1.3, c[2])   # a sun-bleached tip
            mesh_object('leaflet', vv, fc, uvs=uv, colors=np.tile([*c, 1.0], (len(vv), 1)), material=lm)
    return render_atlas('frond_palm', (2048, 512), Lr, Wd, ao=0.04, meta={'length': Lr, 'width': Wd})


def fern_atlas():
    """A fern frond seen from above: pinnae with lobed pinnules."""
    reset()
    Lr, Wd = 1.2, 0.6
    lm = leaf_material('pinna', gloss=0.55, vein=0.15)
    sm = stem_material((0.07, 0.08, 0.03))
    g = rng(21)
    y0 = Wd / 2
    pts = [(x, y0, 0) for x in np.linspace(0.0, Lr - 0.02, 20)]
    rv, rf = tube(pts, 0.006, 0.0015, 5)
    mesh_object('rachis', rv, rf, material=sm)
    for side in (-1, 1):
        for k in range(26):
            t = (k + 0.5) / 26
            x = 0.05 + t * (Lr - 0.1)
            L = (0.27 * math.sin(math.pi * min(t * 0.95 + 0.05, 1.0)) ** 0.7 + 0.02) * g.uniform(0.92, 1.05)
            v, uv, fc = blade(L, L * 0.2, PROFILES['lanceolate'], 0.1, 0.12, 0.0, seg_l=12, seg_w=3, wave=0.5)
            ang = math.radians(70 - 20 * t)
            vv = place(v, (x, y0, 0.005), leaflet_yaw(ang, side), 0.0)
            c = hsv_jitter((0.05, 0.12, 0.03), g, 0.02, 0.1, 0.1)
            mesh_object('pinna', vv, fc, uvs=uv, colors=np.tile([*c, 1.0], (len(vv), 1)), material=lm)
    return render_atlas('frond_fern', (1024, 512), Lr, Wd, ao=0.03, meta={'length': Lr, 'width': Wd})


def needle_atlas():
    """Casuarina (ironwood) sprays: a stem forking into drooping sub-stems,
    each hung with hundreds of fine jointed branchlets; 2x1 variants."""
    reset()
    cell = 0.6
    lm = leaf_material('needle', gloss=0.6, vein=0.0)
    sm = stem_material((0.12, 0.09, 0.05))
    for k in range(2):
        g = rng(300 + k)
        cx = cell * (k + 0.5)
        top = np.array([cx, cell * 0.97, 0.0])
        stems = []
        main = [top + np.array([0.02 * math.sin(t * 3), -cell * 0.9 * t, 0]) for t in np.linspace(0, 1, 10)]
        stems.append(main)
        for j in range(3):
            t0 = 0.15 + 0.2 * j
            a = main[int(t0 * 9)]
            side = 1 if j % 2 else -1
            end = a + np.array([side * g.uniform(0.12, 0.2), -g.uniform(0.3, 0.45), 0.01])
            stems.append([a + (end - a) * t + np.array([0, 0.03 * math.sin(t * math.pi), 0]) for t in np.linspace(0, 1, 7)])
        for st in stems:
            sv, sf = tube(st, 0.0035, 0.0012, 5)
            mesh_object('stem', sv, sf, material=sm)
            for q in range(150):
                t = g.uniform(0.05, 1.0)
                i = min(int(t * (len(st) - 1)), len(st) - 2)
                p = np.array(st[i]) + np.array([g.uniform(-0.006, 0.006), 0, g.uniform(0, 0.01)])
                # branchlets hang down and out, fanning from the stem
                ang = math.pi + g.uniform(-0.75, 0.75)
                L = g.uniform(0.1, 0.24)
                v, uv, fc = blade(L, 0.0024, lambda s_: 1.0, 0.0, g.uniform(0.2, 0.6), 0, seg_l=8, seg_w=1)
                vv = place(v, p, ang, g.uniform(-0.3, 0.3))
                c = hsv_jitter((0.035, 0.075, 0.03), g, 0.02, 0.1, 0.18)
                mesh_object('needle', vv, fc, uvs=uv, colors=np.tile([*c, 1.0], (len(vv), 1)), material=lm)
    return render_atlas('leaves_needle', (1024, 512), cell * 2, cell, ao=0.03, meta={'cells': [2, 1], 'cell': cell})


ATLASES = {
    'broad': broadleaf_atlas,
    'shrub': shrub_atlas,
    'palm': palm_frond_atlas,
    'fern': fern_atlas,
    'needle': needle_atlas,
}

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    names = args or list(ATLASES)
    os.makedirs(OUT, exist_ok=True)
    meta_path = os.path.join(OUT, 'atlases.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for n in names:
        meta[n] = ATLASES[n]()
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=1)
