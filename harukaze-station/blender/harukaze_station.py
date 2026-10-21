"""Harukaze Station (春風駅): the spring railway diorama, rebuilt in Blender.

The same scene as ../index.html, generated entirely from code: every mesh is built from
primitives in Python, the grass, road and vending-machine faces are painted into packed
images with numpy, and the signs are text objects in Blender's bundled Noto Sans CJK.

Usage (Blender 4.2 LTS or newer, EEVEE):

    blender --python harukaze_station.py                     # build it and look around
    blender -b --python harukaze_station.py -- --save harukaze_station.blend
    blender -b --python harukaze_station.py -- --render day.png --frame 300
    blender -b --python harukaze_station.py -- --render night.png --night
    blender -b --python harukaze_station.py -- --quality ultra --render ultra.png
    blender -b --python harukaze_station.py -- --video loop.mp4

Everything loops every 32 s (768 frames at 24 fps): the train, doors, crossing lamps and
barrier arms, the petals and a full turn of the camera. Drag the Night slider on the
scene (Scene properties > Custom Properties > night) to go from day to night.
"""

import argparse
import math
import os
import sys

import bpy  # first: as a pip module, bpy is what puts bmesh and mathutils on the path
import bmesh
import numpy as np
from mathutils import Matrix, Vector

# --------------------------------------------------------------------------- seeded random
# mulberry32, as in the web version, so the build is identical on every run.


def mulberry32(seed):
    state = seed & 0xFFFFFFFF

    def imul(a, b):
        return (a * b) & 0xFFFFFFFF

    def rnd():
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = imul(state ^ (state >> 15), 1 | state)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rnd


rng = mulberry32(0x5A4C2E01)


def rand(a=0.0, b=1.0):
    return a + (b - a) * rng()


def pick(seq):
    return seq[int(rng() * len(seq))]


# --------------------------------------------------------------------------- layout
# Authored in the web version's frame: x runs west to east along the track, y is up and
# z runs north (-) to south (+). Vertices are turned into Blender's Z-up frame
# (x, -z, y) when the meshes are made. The block top sits at y = 0. One unit is a metre.

W, D = 64.0, 40.0
TRACK_Z = -1.0
RAIL_Y = 0.62
PORTAL = 22.0
CLIP_X = PORTAL + 0.7
HILL_FRONT = PORTAL + 1.25
CONTACT_Y = 4.5
PLAT = dict(x0=-14.0, x1=10.0, z0=-7.8, z1=-2.45, h=1.15)
ROAD_X, ROAD_W = 16.0, 5.2
ROAD_X0, ROAD_X1 = ROAD_X - ROAD_W / 2, ROAD_X + ROAD_W / 2
LANE = (8.2, 9.8)
PLAZA = dict(x0=-16.5, x1=0.5, z0=-20.0, z1=-9.6)
PATCH = dict(x0=-8.6, x1=2.6, z0=12.3, z1=18.6)

HILLS = [dict(s=s, cx=s * (W / 2 - 2.5), cz=TRACK_Z + s * 0.5, rx=12.5, ry=8.6, rz=10.5) for s in (-1, 1)]

CHERRIES = [
    (-19.5, 5.0, 1.15), (-10.5, 4.7, 1.25), (-1.8, 7.0, 1.05), (6.6, 6.9, 1.15),
    (-19.2, -12.6, 1.1), (2.8, -11.9, 1.0), (7.6, -16.8, 1.15),
    (20.6, 12.4, 0.95), (-29.2, 11.2, 0.9),
    (-27.6, 4.6, 0.85), (28.2, -6.4, 0.85),
]

HOUSES = [
    dict(x=-25.0, z=14.6, w=5.2, d=4.2, h=2.7, wall='wall', roof='roofGrey'),
    dict(x=-15.6, z=15.0, w=4.6, d=4.0, h=4.6, wall='wallPink', roof='roofRed', floors=2),
    dict(x=7.6, z=14.8, w=5.0, d=4.0, h=2.7, wall='wallBlue', roof='roofBlue'),
    dict(x=25.4, z=15.2, w=5.0, d=4.2, h=2.6, wall='wall', roof='roofBrown', ry=math.pi / 2),
    dict(x=25.6, z=-15.8, w=4.8, d=4.0, h=4.5, wall='wallBlue', roof='roofGrey', ry=math.pi / 2, floors=2),
    dict(x=-26.4, z=-16.0, w=5.0, d=4.0, h=2.7, wall='wallPink', roof='roofRed', ry=math.pi),
]

# the timetable, in seconds of a 32 s cycle
FPS = 24
CYCLE = 32.0
FRAMES = int(CYCLE * FPS)
HERO_FRAME = 300  # 12.5 s in: the train stands at the platform with its doors open

# Two tiers of the same art direction. Classic is the scene as designed; Ultra adds
# geometric detail (bevels, rounder crowns, a meadow of grass tufts and fallen petals,
# more petals in the air), a tilt-shift depth of field, motion blur and more samples.
QUALITY = {
    'classic': dict(resolution=(1920, 1080), samples=16, video_samples=8, petals=460, detail=False,
                    dof=False, fstop=0.0, motion_blur=False, bloom=0.55, shadow_rays=1, shadow_steps=6),
    'ultra': dict(resolution=(3840, 2160), samples=64, video_samples=16, petals=1100, detail=True,
                  dof=True, fstop=0.12, motion_blur=True, bloom=0.8, shadow_rays=2, shadow_steps=8),
}
Q = QUALITY['classic']

# Ultra modifiers per material key: soft subdivision for the round things, a small bevel
# that catches a highlight on everything built from boxes
ROUNDED = {'blossom1', 'blossom2', 'blossom3', 'leaf', 'leafDark', 'leafLight', 'cloud'}
BEVELLED = {'wall', 'wallPink', 'wallBlue', 'roofTeal', 'roofRed', 'roofBlue', 'roofGrey', 'roofBrown',
            'concrete', 'concreteDark', 'wood', 'earthDark', 'stone', 'stoneLight', 'signBoard', 'signWood',
            'vendRed', 'binBlue', 'binGreen', 'binYellow', 'shelterWall', 'frame', 'tWhite', 'tGrey', 'tDark'}
T_ARR0, T_ARR1, T_DEP0, T_DEP1 = 2.0, 10.0, 17.0, 25.0
CAR_L, CAR_GAP = 9.4, 0.5
CAR_OFF = (CAR_L + CAR_GAP) / 2
TRAIN_HALF = CAR_L + CAR_GAP / 2
X_START = -CLIP_X - TRAIN_HALF - 0.6
X_STOP = (PLAT['x0'] + PLAT['x1']) / 2
X_END = CLIP_X + TRAIN_HALF + 0.6


def smoothstep(x, e0, e1):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def hill_height(x, z):
    for h in HILLS:
        if h['s'] * x < HILL_FRONT:
            continue
        u = (x - h['cx']) / h['rx']
        v = (z - h['cz']) / h['rz']
        q = 1 - u * u - v * v
        edge = 1 - 0.78 * smoothstep(abs(x), W / 2 - 6.5, W / 2)
        if q > 0:
            return h['ry'] * math.sqrt(q) * edge
    return 0.0


def to_blender(v):
    return (v[0], -v[2], v[1])


# --------------------------------------------------------------------------- colours

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_srgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lin(h, a=1.0):
    return tuple(srgb_to_linear(c) for c in hex_srgb(h)) + (a,)


# --------------------------------------------------------------------------- geometry
# A Geo is a small vertex/face list with three.js-style chainable transforms, so the
# builders below read like the web version.


class Geo:
    def __init__(self, verts, faces, smooth=False, uvs=None):
        self.v = [Vector(p) for p in verts]
        self.f = [tuple(f) for f in faces]
        self.smooth = smooth
        self.uvs = uvs  # per face, a tuple of (u, v) per corner

    def apply(self, m):
        self.v = [m @ p for p in self.v]
        return self

    def translate(self, x, y, z):
        return self.apply(Matrix.Translation((x, y, z)))

    def rotate_x(self, a):
        return self.apply(Matrix.Rotation(a, 4, 'X'))

    def rotate_y(self, a):
        return self.apply(Matrix.Rotation(a, 4, 'Y'))

    def rotate_z(self, a):
        return self.apply(Matrix.Rotation(a, 4, 'Z'))

    def scale(self, x, y, z):
        return self.apply(Matrix.Diagonal((x, y, z, 1.0)))


def box(w, h, d, x=0.0, y=0.0, z=0.0):
    """An axis-aligned box whose bottom sits at y."""
    a, b, c = w / 2, h / 2, d / 2
    verts = [(-a, -b, -c), (a, -b, -c), (a, b, -c), (-a, b, -c), (-a, -b, c), (a, -b, c), (a, b, c), (-a, b, c)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 4, 7, 3), (1, 2, 6, 5), (0, 1, 5, 4), (3, 7, 6, 2)]
    return Geo(verts, faces).translate(x, y + h / 2, z)


def cyl(rt, rb, h, x=0.0, y=0.0, z=0.0, seg=10):
    """A (tapered) cylinder or cone standing on y; flat-shaded like low-poly."""
    verts, faces = [], []
    for i in range(seg):
        t = 2 * math.pi * i / seg
        verts.append((rb * math.sin(t), 0.0, rb * math.cos(t)))
    if rt > 0:
        for i in range(seg):
            t = 2 * math.pi * i / seg
            verts.append((rt * math.sin(t), h, rt * math.cos(t)))
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((i, j, seg + j, seg + i))
        faces.append(tuple(seg + i for i in range(seg)))
    else:
        verts.append((0.0, h, 0.0))
        for i in range(seg):
            faces.append((i, (i + 1) % seg, seg))
    faces.append(tuple(reversed(range(seg))))
    return Geo(verts, faces).translate(x, y, z)


def cone(r, h, seg=7):
    """Centred on its middle like three.js ConeGeometry."""
    return cyl(0.0, r, h, 0.0, -h / 2, 0.0, seg)


def icosphere(r, detail=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=detail + 1, radius=r)
    verts = [v.co.copy() for v in bm.verts]
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces


def ball(r, x=0.0, y=0.0, z=0.0, detail=1, smooth=True):
    verts, faces = icosphere(r, detail)
    return Geo(verts, faces, smooth).translate(x, y, z)


def puff(r, x, y, z, sy=1.0, detail=1, jitter=None):
    """A lumpy blob: an icosphere nudged in and out, with smooth shading."""
    verts, faces = icosphere(r, detail)
    out = []
    for p in verts:
        k = 1 + (jitter or rand)(-0.07, 0.07)
        out.append((p.x * k, p.y * k * sy, p.z * k))
    return Geo(out, faces, True).translate(x, y, z)


def rock(r):
    verts, faces = icosphere(r, 0)
    return Geo(verts, faces)


def prism(points, depth):
    """Extrude a 2D outline along +z from 0 to depth, like THREE.ExtrudeGeometry."""
    pts = [(float(p[0]), float(p[1])) for p in points]
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if area < 0:
        pts.reverse()
    n = len(pts)
    verts = [(x, y, 0.0) for x, y in pts] + [(x, y, depth) for x, y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return Geo(verts, faces)


def beam(a, b, t=0.08, t2=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    g = box(t, d.length, t if t2 is None else t2, 0.0, -d.length / 2, 0.0)
    q = Vector((0.0, 1.0, 0.0)).rotation_difference(d.normalized())
    g.apply(q.to_matrix().to_4x4())
    mid = (a + b) / 2
    return g.translate(mid.x, mid.y, mid.z)


def tube(points, r=0.03, seg=5):
    pts = [Vector(p) for p in points]
    verts, faces = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0.0, 1.0, 0.0)))
        if side.length < 1e-4:
            side = t.cross(Vector((1.0, 0.0, 0.0)))
        side.normalize()
        up = side.cross(t).normalized()
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append(p + side * (math.cos(a) * r) + up * (math.sin(a) * r))
    for i in range(len(pts) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((i * seg + k, (i + 1) * seg + k, (i + 1) * seg + k2, i * seg + k2))
    return Geo(verts, faces, True)


def sag_wire(a, b, sag, r=0.028):
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(13):
        t = i / 12
        p = a.lerp(b, t)
        p.y -= sag * 4 * t * (1 - t)
        pts.append(p)
    return tube(pts, r, 4)


def plane_up(w, d, x=0.0, y=0.0, z=0.0, uv=False):
    """A horizontal rectangle facing up; with uv=True its north edge maps to v = 1."""
    verts = [(-w / 2, 0.0, -d / 2), (w / 2, 0.0, -d / 2), (w / 2, 0.0, d / 2), (-w / 2, 0.0, d / 2)]
    uvs = [((0, 1), (0, 0), (1, 0), (1, 1))] if uv else None
    return Geo(verts, [(0, 3, 2, 1)], uvs=uvs).translate(x, y, z)


def plane_front(w, h, uv=True):
    """An upright rectangle centred on the origin, facing +z."""
    verts = [(-w / 2, -h / 2, 0.0), (w / 2, -h / 2, 0.0), (w / 2, h / 2, 0.0), (-w / 2, h / 2, 0.0)]
    return Geo(verts, [(0, 1, 2, 3)], uvs=[((0, 0), (1, 0), (1, 1), (0, 1))] if uv else None)


def disc(r, seg=24):
    verts = [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), 0.0) for i in range(seg)]
    return Geo(verts, [tuple(range(seg))])


# --------------------------------------------------------------------------- batching
# Static parts are collected per material key in world space and merged into one object
# per material, the same way the web version merges its draw calls.


class Part:
    def __init__(self):
        self.v, self.f, self.smooth, self.uvs = [], [], [], []


BATCH = {}
XF = Matrix.Identity(4)


def add(key, geo):
    part = BATCH.setdefault(key, Part())
    base = len(part.v)
    part.v.extend(XF @ p for p in geo.v)
    part.f.extend(tuple(base + i for i in f) for f in geo.f)
    part.smooth.extend([geo.smooth] * len(geo.f))
    part.uvs.extend(geo.uvs if geo.uvs else [None] * len(geo.f))
    return geo


class at:
    """Build inside a local frame translated to (x, y, z) and turned ry about y."""

    def __init__(self, x, y, z, ry=0.0):
        self.m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(ry, 4, 'Y')

    def __enter__(self):
        global XF
        self.prev = XF
        XF = XF @ self.m

    def __exit__(self, *exc):
        global XF
        XF = self.prev


def to_world(x, y, z):
    return XF @ Vector((x, y, z))


class batch_scope:
    """Collect into a fresh batch (for the moving parts) and restore afterwards."""

    def __enter__(self):
        global BATCH, XF
        self.saved = (BATCH, XF)
        BATCH, XF = {}, Matrix.Identity(4)
        return self

    def __exit__(self, *exc):
        global BATCH, XF
        self.batch = BATCH
        BATCH, XF = self.saved


# --------------------------------------------------------------------------- materials


def find_socket(sockets, name, kind=None):
    for s in sockets:
        if s.name == name and (kind is None or s.type == kind):
            return s
    raise KeyError(name)


def node_group_night():
    """A one-node group whose value is driven by scene['night'], shared by every material."""
    ng = bpy.data.node_groups.get('Night')
    if ng:
        return ng
    ng = bpy.data.node_groups.new('Night', 'ShaderNodeTree')
    ng.interface.new_socket('Night', in_out='OUTPUT', socket_type='NodeSocketFloat')
    out = ng.nodes.new('NodeGroupOutput')
    val = ng.nodes.new('ShaderNodeValue')
    val.name = 'night'
    ng.links.new(val.outputs[0], out.inputs[0])
    fc = val.outputs[0].driver_add('default_value')
    drive(fc, 'n')
    return ng


def drive(fcurve, expression, extra=()):
    """Point a driver at scene['night'] (as n), plus any (name, id, path) extras."""
    drv = fcurve.driver
    drv.type = 'SCRIPTED'
    var = drv.variables.new()
    var.name = 'n'
    var.targets[0].id_type = 'SCENE'
    var.targets[0].id = SCENE
    var.targets[0].data_path = '["night"]'
    for name, idb, path in extra:
        v = drv.variables.new()
        v.name = name
        v.targets[0].id_type = 'OBJECT'
        v.targets[0].id = idb
        v.targets[0].data_path = path
    drv.expression = expression


# Toon bands, measured against the key light: a sunlit top reads about 1.15 by day and
# moonlight about 0.105 at night. Light is divided by the key, quantised into five tinted
# bands and scaled to the time of day; only lamplight reaches the hot band.
KEY_DAY, KEY_NIGHT = 1.15, 0.105
LEVEL_NIGHT = 0.34
TOON_BANDS = [  # (light / key, band colour)
    (0.0, (0.42, 0.43, 0.58)),   # core shadow, cool
    (0.15, (0.60, 0.61, 0.75)),  # cast shadow
    (0.47, (0.84, 0.84, 0.90)),  # turned away from the sun
    (0.85, (1.0, 1.0, 1.0)),     # lit
    (1.65, (2.2, 1.95, 1.6)),    # lamplight pools at night
]


def node_group_toon():
    """Quantise the light falling on a white diffuse surface into flat, tinted bands
    relative to the key light, keep the light's own colour (warm lamps, blue moonlight)
    and tint the base colour with it."""
    ng = bpy.data.node_groups.get('Toon')
    if ng:
        return ng
    ng = bpy.data.node_groups.new('Toon', 'ShaderNodeTree')
    ng.interface.new_socket('Color', in_out='INPUT', socket_type='NodeSocketColor').default_value = (1, 1, 1, 1)
    ng.interface.new_socket('Glow', in_out='INPUT', socket_type='NodeSocketColor').default_value = (0, 0, 0, 1)
    ng.interface.new_socket('Glow Strength', in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.0
    ng.interface.new_socket('Shader', in_out='OUTPUT', socket_type='NodeSocketShader')
    n, l = ng.nodes, ng.links
    gin, gout = n.new('NodeGroupInput'), n.new('NodeGroupOutput')

    def value(name, expression):
        v = n.new('ShaderNodeValue')
        v.name = name
        drive(v.outputs[0].driver_add('default_value'), expression)
        return v.outputs[0]

    def math(op, a, b):
        m = n.new('ShaderNodeMath')
        m.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                l.new(x, m.inputs[i])
        return m.outputs[0]

    def vec(op, a, b, scale=False):
        m = n.new('ShaderNodeVectorMath')
        m.operation = op
        l.new(a, m.inputs[0])
        l.new(b, find_socket(m.inputs, 'Scale') if scale else m.inputs[1])
        return m.outputs[0]

    key = value('key', f'{KEY_DAY} + ({KEY_NIGHT - KEY_DAY}) * n')
    level = value('level', f'1 + ({LEVEL_NIGHT - 1}) * n')
    diffuse = n.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (1, 1, 1, 1)
    to_rgb = n.new('ShaderNodeShaderToRGB')
    l.new(diffuse.outputs[0], to_rgb.inputs[0])
    bw = n.new('ShaderNodeRGBToBW')
    l.new(to_rgb.outputs['Color'], bw.inputs[0])
    ramp = n.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    while len(cr.elements) < len(TOON_BANDS):
        cr.elements.new(0.5)
    for el, (pos, col) in zip(cr.elements, TOON_BANDS):
        el.position = pos * 0.5  # the ramp spans 0..2 x key
        el.color = col + (1,)
    l.new(math('MULTIPLY', math('DIVIDE', bw.outputs[0], key), 0.5), ramp.inputs[0])
    # the light's colour with its brightness taken out, then the band, then the hour
    chroma = vec('SCALE', to_rgb.outputs['Color'], math('DIVIDE', 1.0, math('MAXIMUM', bw.outputs[0], 0.0005)), True)
    light = vec('SCALE', vec('MULTIPLY', chroma, ramp.outputs['Color']), level, True)
    tint = vec('MULTIPLY', gin.outputs['Color'], light)
    glow = vec('SCALE', gin.outputs['Glow'], gin.outputs['Glow Strength'], True)
    emit = n.new('ShaderNodeEmission')
    l.new(vec('ADD', tint, glow), emit.inputs['Color'])
    l.new(emit.outputs[0], gout.inputs['Shader'])
    return ng


def node_group_clip():
    """1 between the tunnel mouths, 0 inside the hills: the train's clipping planes."""
    ng = bpy.data.node_groups.get('TunnelClip')
    if ng:
        return ng
    ng = bpy.data.node_groups.new('TunnelClip', 'ShaderNodeTree')
    ng.interface.new_socket('Visible', in_out='OUTPUT', socket_type='NodeSocketFloat')
    n, l = ng.nodes, ng.links
    geo = n.new('ShaderNodeNewGeometry')
    sep = n.new('ShaderNodeSeparateXYZ')
    l.new(geo.outputs['Position'], sep.inputs[0])
    absx = n.new('ShaderNodeMath')
    absx.operation = 'ABSOLUTE'
    l.new(sep.outputs['X'], absx.inputs[0])
    less = n.new('ShaderNodeMath')
    less.operation = 'LESS_THAN'
    less.inputs[1].default_value = CLIP_X
    l.new(absx.outputs[0], less.inputs[0])
    out = n.new('NodeGroupOutput')
    l.new(less.outputs[0], out.inputs[0])
    return ng


MATERIALS = {}


def use_nodes(idblock):
    # always on (and deprecated) from Blender 5.0
    if bpy.app.version < (5, 0, 0):
        idblock.use_nodes = True


def new_material(name):
    m = bpy.data.materials.new(name)
    use_nodes(m)
    m.node_tree.nodes.clear()
    return m


def finish_clip(m, shader_socket):
    """Route a shader through the tunnel clip (transparent outside the portals)."""
    n, l = m.node_tree.nodes, m.node_tree.links
    clip = n.new('ShaderNodeGroup')
    clip.node_tree = node_group_clip()
    transparent = n.new('ShaderNodeBsdfTransparent')
    mix = n.new('ShaderNodeMixShader')
    l.new(clip.outputs[0], mix.inputs[0])
    l.new(transparent.outputs[0], mix.inputs[1])
    l.new(shader_socket, mix.inputs[2])
    if hasattr(m, 'use_transparent_shadow'):
        m.use_transparent_shadow = True
    return mix.outputs[0]


def toon_material(key, color, glow=None, image=None, clip=False, double_sided=False):
    m = new_material(key)
    n, l = m.node_tree.nodes, m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial')
    toon = n.new('ShaderNodeGroup')
    toon.node_tree = node_group_toon()
    toon.inputs['Color'].default_value = lin(color)
    m.diffuse_color = lin(color)
    if image is not None:
        tex = n.new('ShaderNodeTexImage')
        tex.image = image
        tex.interpolation = 'Cubic' if image.size[0] < 300 else 'Linear'
        l.new(tex.outputs['Color'], toon.inputs['Color'])
        if glow:
            l.new(tex.outputs['Color'], toon.inputs['Glow'])
    if glow:
        # glow = (colour, strength at full night[, socket to drive instead])
        gcolor, strength = glow[0], glow[1]
        if image is None:
            toon.inputs['Glow'].default_value = lin(gcolor)
        night = n.new('ShaderNodeGroup')
        night.node_tree = node_group_night()
        mul = n.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = strength
        l.new(night.outputs[0], mul.inputs[0])
        l.new(mul.outputs[0], toon.inputs['Glow Strength'])
    shader = toon.outputs[0]
    if clip:
        shader = finish_clip(m, shader)
    l.new(shader, out.inputs['Surface'])
    m.use_backface_culling = not double_sided
    return m


def ink_material(clip=False):
    name = 'ink_clip' if clip else 'ink'
    if name in MATERIALS:
        return MATERIALS[name]
    m = new_material(name)
    n, l = m.node_tree.nodes, m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial')
    emit = n.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = (0.012, 0.009, 0.022, 1)
    shader = emit.outputs[0]
    if clip:
        shader = finish_clip(m, shader)
    l.new(shader, out.inputs['Surface'])
    m.use_backface_culling = True
    if hasattr(m, 'use_backface_culling_shadow'):
        m.use_backface_culling_shadow = True
    m.diffuse_color = (0.02, 0.02, 0.03, 1)
    MATERIALS[name] = m
    return m


def glow_material(name, color, strength, clip=False, keyed=False):
    """A soft emissive orb: bright where it faces the camera, transparent at the rim.
    Its strength is the night value times `strength`, or a keyed Value node."""
    m = new_material(name)
    n, l = m.node_tree.nodes, m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial')
    weight = n.new('ShaderNodeLayerWeight')
    weight.inputs['Blend'].default_value = 0.5
    inv = n.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    l.new(weight.outputs['Facing'], inv.inputs[1])
    falloff = n.new('ShaderNodeMath')
    falloff.operation = 'POWER'
    falloff.inputs[1].default_value = 3.0
    l.new(inv.outputs[0], falloff.inputs[0])
    level = n.new('ShaderNodeValue')
    level.name = 'level'
    level.outputs[0].default_value = 0.0
    if not keyed:
        fc = level.outputs[0].driver_add('default_value')
        drive(fc, 'n')
    k = n.new('ShaderNodeMath')
    k.operation = 'MULTIPLY'
    k.inputs[1].default_value = strength
    l.new(level.outputs[0], k.inputs[0])
    amount = n.new('ShaderNodeMath')
    amount.operation = 'MULTIPLY'
    l.new(falloff.outputs[0], amount.inputs[0])
    l.new(k.outputs[0], amount.inputs[1])
    emit = n.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = lin(color)
    l.new(amount.outputs[0], emit.inputs['Strength'])
    transparent = n.new('ShaderNodeBsdfTransparent')
    add_shader = n.new('ShaderNodeAddShader')
    l.new(transparent.outputs[0], add_shader.inputs[0])
    l.new(emit.outputs[0], add_shader.inputs[1])
    shader = add_shader.outputs[0]
    if clip:
        shader = finish_clip(m, shader)
    l.new(shader, out.inputs['Surface'])
    m.use_backface_culling = True
    if hasattr(m, 'use_transparent_shadow'):
        m.use_transparent_shadow = True
    MATERIALS[name] = m
    return m


# key: (sRGB colour, outline thickness in metres or 0, options)
SPEC = {
    'grassTop': ('#ffffff', 0, dict(image='grass')),
    'grassLip': ('#78c159', 0.07, {}),
    'earth': ('#b9794b', 0.07, {}),
    'earthDark': ('#8a573a', 0.05, {}),
    'stone': ('#aaa5b8', 0.05, {}),
    'stoneLight': ('#c3bfcd', 0.04, {}),
    'stoneDark': ('#7e7a93', 0.06, {}),
    'hill': ('#71c35a', 0.07, dict(night_shift=('#3f6f78', 0.3))),
    'ballast': ('#a49c92', 0.03, {}),
    'sleeper': ('#d3cdc1', 0.015, {}),
    'rail': ('#8a6a58', 0.012, {}),
    'railHead': ('#d7dce2', 0, {}),
    'whiteLine': ('#f8f5ee', 0, {}),
    'concrete': ('#e4ded2', 0.05, {}),
    'concreteDark': ('#bfb7a8', 0.05, {}),
    'tactile': ('#ffc928', 0, {}),
    'road': ('#ffffff', 0, dict(image='road')),
    'tunnelDark': ('#16131f', 0, {}),
    'wall': ('#f6eddb', 0.05, {}),
    'wallPink': ('#f9e4e0', 0.05, {}),
    'wallBlue': ('#e2ebf5', 0.05, {}),
    'wood': ('#c3874f', 0.03, {}),
    'roofTeal': ('#1fa59c', 0.05, {}),
    'roofRed': ('#dc5a4d', 0.05, {}),
    'roofBlue': ('#4a79c1', 0.05, {}),
    'roofGrey': ('#6d7489', 0.05, {}),
    'roofBrown': ('#ad6240', 0.05, {}),
    'window': ('#a6d3ee', 0.02, dict(glow=('#ffc768', 1.1))),
    'window2': ('#b9dcef', 0.02, dict(glow=('#ffdf9a', 0.75))),
    'windowOff': ('#8fb8d6', 0.02, {}),
    'frame': ('#5b4740', 0.02, {}),
    'metalDark': ('#525a69', 0.025, {}),
    'catMast': ('#9ba6b3', 0.025, {}),
    'lampLight': ('#fff4d8', 0, dict(glow=('#fff1c8', 1.4))),
    'shelterRoof': ('#f39a6b', 0.04, {}),
    'shelterWall': ('#e6c08f', 0.04, {}),
    'fence': ('#f1f3ee', 0.02, {}),
    'trunk': ('#8f5a45', 0.04, {}),
    'blossom1': ('#ffb3c8', 0.06, {}),
    'blossom2': ('#ff97b6', 0.06, {}),
    'blossom3': ('#ffd4e0', 0.06, {}),
    'leaf': ('#62b74d', 0.05, dict(night_shift=('#3f6f78', 0.3))),
    'leafDark': ('#3f9548', 0.05, dict(night_shift=('#3f6f78', 0.3))),
    'leafLight': ('#96d46b', 0.04, dict(night_shift=('#3f6f78', 0.3))),
    'cedar': ('#2f8156', 0.05, dict(night_shift=('#3f6f78', 0.3))),
    'pole': ('#cbc5b9', 0.03, {}),
    'wire': ('#2a2733', 0, dict(double_sided=True)),
    'stripe': ('#ffcd1c', 0.025, dict(stripes=True)),
    'black': ('#2d2b35', 0.02, {}),
    'lampA': ('#5c1616', 0.015, dict(blink='A')),
    'lampB': ('#5c1616', 0.015, dict(blink='B')),
    'vendRed': ('#e2474b', 0.04, {}),
    'binBlue': ('#3f8ad8', 0.03, {}),
    'binGreen': ('#45b06c', 0.03, {}),
    'binYellow': ('#f5c33b', 0.03, {}),
    'vend1': ('#ffffff', 0, dict(image='vend1', glow=('#ffffff', 0.85))),
    'vend2': ('#ffffff', 0, dict(image='vend2', glow=('#ffffff', 0.85))),
    'signBoard': ('#fbfaf6', 0.025, dict(glow=('#fbfaf6', 0.35))),
    'signWood': ('#5b3a29', 0.025, {}),
    'signPink': ('#ff6f9d', 0, {}),
    'textDark': ('#25222e', 0, {}),
    'textCream': ('#fff7e6', 0, dict(glow=('#fff7e6', 0.35))),
    'textWhite': ('#ffffff', 0, {}),
    'clockFace': ('#fffdf7', 0, dict(glow=('#fffdf7', 0.45))),
    'clockHand': ('#2b2a33', 0, {}),
    'clockPin': ('#e8426b', 0, {}),
    'cloud': ('#ffffff', 0.06, dict(night_tint='#6d7393')),
    'paddyWater': ('#93c8dc', 0, dict(glow=('#3a4f7a', 0.25))),
    'nanohana': ('#ffd83a', 0.03, {}),
    'nanohanaLight': ('#fff07a', 0.025, {}),
    'shu': ('#e0533a', 0.035, {}),
    'signWhite': ('#f4f2ec', 0.02, {}),
    'mirrorPole': ('#f08b2b', 0.025, {}),
    'mirrorGlass': ('#cfe3ef', 0, dict(glow=('#cfe3ef', 0.25))),
    'icPad': ('#2f7fe0', 0.01, dict(glow=('#5fb0ff', 0.9))),
    'gutter': ('#d6d0c4', 0.012, {}),
    'arrowLit': ('#3b3842', 0, dict(blink='R')),
    'arrowDim': ('#3b3842', 0, {}),
    'timetable': ('#ffffff', 0, dict(image='timetable', glow=('#ffffff', 0.25))),
    'posterSakura': ('#ffffff', 0, dict(image='posterSakura', glow=('#ffffff', 0.25))),
    'posterSea': ('#ffffff', 0, dict(image='posterSea', glow=('#ffffff', 0.25))),
    # the train
    'tWhite': ('#f7f8fb', 0.04, dict(clip=True)),
    'tPink': ('#ff77a4', 0, dict(clip=True)),
    'tPinkDark': ('#e0457d', 0, dict(clip=True)),
    'tBlack': ('#25232c', 0.02, dict(clip=True)),
    'tGlass': ('#3d5470', 0.015, dict(clip=True, glow=('#ffe9b8', 1.0))),
    'tDark': ('#4a4e5a', 0.025, dict(clip=True)),
    'tGrey': ('#a9b0bb', 0.02, dict(clip=True)),
    'tSilver': ('#d9dee6', 0.012, dict(clip=True)),
    'tWheel': ('#33343b', 0.012, dict(clip=True)),
    'tHead': ('#fff7d6', 0.012, dict(clip=True, glow=('#fff1c4', 0.0), always=0.9)),
    'tTail': ('#ff4a4a', 0.012, dict(clip=True, glow=('#ff2d2d', 0.0), always=0.8)),
    'tLampOff': ('#9aa0aa', 0.012, dict(clip=True)),
    'tDoor': ('#dfe4ea', 0.015, dict(clip=True)),
    'tDoorway': ('#1e1d26', 0, dict(clip=True)),
    'tDest': ('#16151c', 0, dict(clip=True, glow=('#ffa63d', 0.0), always=0.6)),
}


def material(key):
    if key in MATERIALS:
        return MATERIALS[key]
    color, _, opt = SPEC[key]
    if key == 'tunnelDark':
        m = new_material(key)
        n = m.node_tree.nodes
        out = n.new('ShaderNodeOutputMaterial')
        emit = n.new('ShaderNodeEmission')
        emit.inputs['Color'].default_value = lin(color)
        m.node_tree.links.new(emit.outputs[0], out.inputs['Surface'])
    else:
        image = IMAGES.get(opt.get('image')) if opt.get('image') else None
        m = toon_material(key, color, opt.get('glow'), image, opt.get('clip', False), opt.get('double_sided', False))
        toon = next(nd for nd in m.node_tree.nodes if nd.type == 'GROUP' and nd.node_tree.name == 'Toon')
        if 'always' in opt:
            # head, tail and destination lamps glow day and night
            toon.inputs['Glow'].default_value = lin(opt['glow'][0])
            for link in list(toon.inputs['Glow Strength'].links):
                m.node_tree.links.remove(link)
            toon.inputs['Glow Strength'].default_value = opt['always']
        if opt.get('stripes'):
            add_stripes(m, toon)
        if opt.get('blink'):
            add_blink(m, toon, opt['blink'])
        if opt.get('night_tint'):
            add_night_tint(m, toon, color, opt['night_tint'])
        if opt.get('night_shift'):
            target, amount = opt['night_shift']
            mixed = tuple(a + (b - a) * amount for a, b in zip(hex_srgb(color), hex_srgb(target)))
            add_night_tint(m, toon, color, '#' + ''.join(f'{round(c * 255):02x}' for c in mixed))
    MATERIALS[key] = m
    return m


def add_stripes(m, toon):
    """Yellow and black diagonal stripes from object coordinates, for the crossing."""
    n, l = m.node_tree.nodes, m.node_tree.links
    coords = n.new('ShaderNodeTexCoord')
    sep = n.new('ShaderNodeSeparateXYZ')
    l.new(coords.outputs['Object'], sep.inputs[0])
    s1 = n.new('ShaderNodeMath')
    s1.operation = 'ADD'
    l.new(sep.outputs['X'], s1.inputs[0])
    l.new(sep.outputs['Y'], s1.inputs[1])
    s2 = n.new('ShaderNodeMath')
    s2.operation = 'ADD'
    l.new(s1.outputs[0], s2.inputs[0])
    l.new(sep.outputs['Z'], s2.inputs[1])
    per = n.new('ShaderNodeMath')
    per.operation = 'PINGPONG'
    per.inputs[1].default_value = 0.21
    l.new(s2.outputs[0], per.inputs[0])
    step = n.new('ShaderNodeMath')
    step.operation = 'GREATER_THAN'
    step.inputs[1].default_value = 0.105
    l.new(per.outputs[0], step.inputs[0])
    mix = n.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    l.new(step.outputs[0], find_socket(mix.inputs, 'Factor', 'VALUE'))
    find_socket(mix.inputs, 'A', 'RGBA').default_value = lin('#ffcd1c')
    find_socket(mix.inputs, 'B', 'RGBA').default_value = lin('#26232e')
    l.new(find_socket(mix.outputs, 'Result', 'RGBA'), toon.inputs['Color'])


def add_blink(m, toon, which):
    """Crossing lamps (A, B, alternating red) and the arrow (R, steady amber): a keyed 0/1
    value lights them."""
    n, l = m.node_tree.nodes, m.node_tree.links
    val = n.new('ShaderNodeValue')
    val.name = 'blink'
    val.outputs[0].default_value = 0.0
    toon.inputs['Glow'].default_value = lin('#ffc65a' if which == 'R' else '#ff2a2a')
    mul = n.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 1.4
    l.new(val.outputs[0], mul.inputs[0])
    l.new(mul.outputs[0], toon.inputs['Glow Strength'])
    BLINKERS[which].append(val)


def add_night_tint(m, toon, day, night):
    n, l = m.node_tree.nodes, m.node_tree.links
    ng = n.new('ShaderNodeGroup')
    ng.node_tree = node_group_night()
    mix = n.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    l.new(ng.outputs[0], find_socket(mix.inputs, 'Factor', 'VALUE'))
    find_socket(mix.inputs, 'A', 'RGBA').default_value = lin(day)
    find_socket(mix.inputs, 'B', 'RGBA').default_value = lin(night)
    l.new(find_socket(mix.outputs, 'Result', 'RGBA'), toon.inputs['Color'])


BLINKERS = {'A': [], 'B': [], 'R': []}
IMAGES = {}

# --------------------------------------------------------------------------- painted textures
# numpy stands in for the web version's canvases; the images are packed into the .blend.

np_rng = np.random.default_rng(0x5A4C2E01)


def hex_np(h):
    return np.array(hex_srgb(h), np.float32)


def upsample(coarse, h, w):
    ys = np.linspace(0, coarse.shape[0] - 1, h)
    xs = np.linspace(0, coarse.shape[1] - 1, w)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, coarse.shape[0] - 1)
    x1 = np.minimum(x0 + 1, coarse.shape[1] - 1)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    a, b = coarse[np.ix_(y0, x0)], coarse[np.ix_(y0, x1)]
    c, d = coarse[np.ix_(y1, x0)], coarse[np.ix_(y1, x1)]
    return a * (1 - fy) * (1 - fx) + b * (1 - fy) * fx + c * fy * (1 - fx) + d * fy * fx


def stamp(img, rows, cols, colors, h=2, w=2):
    hh, ww = img.shape[:2]
    for dy in range(h):
        for dx in range(w):
            r = np.clip(rows + dy, 0, hh - 1)
            c = np.clip(cols + dx, 0, ww - 1)
            img[r, c] = colors


def to_image(name, arr):
    """arr: rows run north to south (top to bottom), sRGB floats."""
    h, w = arr.shape[:2]
    img = bpy.data.images.get(name) or bpy.data.images.new(name, width=w, height=h, alpha=False)
    if tuple(img.size) != (w, h):
        img.scale(w, h)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.clip(np.flipud(arr), 0, 1)
    img.pixels.foreach_set(rgba.ravel())
    img.update()
    img.pack()
    return img


def paint_grass(px=24):
    h, w = int(D * px), int(W * px)
    X = lambda x: ((np.asarray(x) + W / 2) * px).astype(int)
    Z = lambda z: ((np.asarray(z) + D / 2) * px).astype(int)
    img = np.empty((h, w, 3), np.float32)
    img[:] = hex_np('#86c95c')
    blot = upsample(np_rng.random((h // 40 + 2, w // 40 + 2)), h, w)
    img += ((blot - 0.5) * 2)[..., None] * np.array([0.07, 0.09, 0.04], np.float32)
    fine = np_rng.random((h, w))
    img[fine > 0.9] *= np.array([0.88, 0.93, 0.85], np.float32)
    img[fine < 0.08] = img[fine < 0.08] * 0.85 + hex_np('#a9de78') * 0.15

    def patch(x0, x1, z0, z1, base, specks, jag=0.18):
        rows = np.arange(h)[:, None] / px - D / 2
        cols = np.arange(w)[None, :] / px - W / 2
        edge = upsample(np_rng.random((h // 6 + 2, w // 6 + 2)), h, w) * jag * 2 - jag
        mask = (cols > x0 + edge) & (cols < x1 - edge) & (rows > z0 + edge) & (rows < z1 - edge)
        img[mask] = hex_np(base)
        n = int((x1 - x0) * (z1 - z0) * 26)
        rr = Z(np_rng.uniform(z0, z1, n))
        cc = X(np_rng.uniform(x0, x1, n))
        palette = np.stack([hex_np(s) for s in specks])
        stamp(img, rr, cc, palette[np_rng.integers(0, len(specks), n)])

    # gravel shoulder along the line
    img[Z(TRACK_Z - 2.6):Z(TRACK_Z + 2.6)] = hex_np('#c9c0b0')
    n = 4000
    stamp(img, Z(TRACK_Z + np_rng.uniform(-2.6, 2.6, n)), np_rng.integers(0, w, n),
          np.stack([hex_np(c) for c in ('#b3aa9b', '#ddd5c6', '#a69d90')])[np_rng.integers(0, 3, n)])
    patch(-W / 2 - 1, ROAD_X0 + 0.2, LANE[0], LANE[1], '#dcc396', ['#cdb284', '#ead6ad', '#bfa477'])
    patch(PLAZA['x0'], PLAZA['x1'], PLAZA['z0'] - 1, PLAZA['z1'], '#e4d8c0', ['#d2c5aa', '#f0e7d4', '#c7b998'])
    patch(PLAZA['x1'] - 0.5, ROAD_X0 + 0.2, -18.9, -17.3, '#e4d8c0', ['#d2c5aa', '#f0e7d4'])
    patch(PATCH['x0'], PATCH['x1'], PATCH['z0'], PATCH['z1'], '#9a6a45', ['#86593a', '#ad7b52', '#7a5034'], 0.1)
    for hs in HOUSES:
        ry = hs.get('ry', 0.0)
        fx, fz = round(-math.sin(ry)), round(-math.cos(ry))
        dx, dz = hs['x'] + fx * (hs['d'] / 2 + 1.2), hs['z'] + fz * (hs['d'] / 2 + 1.2)
        patch(dx - 1.0, dx + 1.0, dz - 1.0, dz + 1.0, '#e0d3b8', ['#cfc1a3', '#efe5d0'], 0.25)

    # wild flowers
    n = 3600
    flowers = np.stack([hex_np(c) for c in ('#fff6a8', '#ffffff', '#ffd84a', '#c9a8ff', '#ff9ec2')])
    stamp(img, np_rng.integers(0, h, n), np_rng.integers(0, w, n), flowers[np_rng.integers(0, 5, n)])

    # fallen sakura petals under every tree, and a scatter on the wind
    petals = np.stack([hex_np(c) for c in ('#ffc4d4', '#ffb0c6', '#ffd9e3', '#ff9fbb', '#ffe6ec')])
    fallen = np.zeros((h, w, 3), np.float32)
    for tx, tz, s in CHERRIES:
        n = int(700 * s)
        r = np.abs(np_rng.normal(size=n)) * 1.6 * s + np_rng.uniform(0, 0.8, n)
        a = np_rng.uniform(0, 2 * math.pi, n)
        rows, cols = Z(tz + np.sin(a) * r * 0.9), X(tx + np.cos(a) * r + 0.6)
        stamp(img, rows, cols, petals[np_rng.integers(0, 5, n)], 2, 3)
        stamp(fallen, rows, cols, np.ones(3, np.float32), 2, 3)
    n = 1600
    stamp(img, np_rng.integers(0, h, n), np_rng.integers(0, w, n), petals[np_rng.integers(0, 5, n)], 2, 3)

    # ground under the new details, from its own seed so the rest of the painting is unchanged
    drs = np.random.default_rng(0xDE7A11)
    for x0, x1, z0, z1 in PADDIES:
        img[Z(z0):Z(z1), X(x0):X(x1)] = hex_np('#7d5a3c')
    for x0, x1, z0, z1, n in ((-21.2, 11.9, 2.2, 3.8, 9000), (-21.6, -14.6, -5.4, -3.95, 2000)):
        sel = (slice(Z(z0), Z(z1)), slice(X(x0), X(x1)))
        img[sel] = img[sel] * 0.8 + hex_np('#6fae4a') * 0.2
        rr, cc = Z(drs.uniform(z0, z1, n)), X(drs.uniform(x0, x1, n))
        stamp(img, rr, cc, np.stack([hex_np(c) for c in ('#ffe14a', '#ffd21c', '#fff3a0')])[drs.integers(0, 3, n)])
    x0, x1, z0, z1 = SHRINE
    img[Z(z0):Z(z1), X(x0):X(x1)] = img[Z(z0):Z(z1), X(x0):X(x1)] * 0.3 + hex_np('#d8c9a8') * 0.7

    # the Ultra meadow mask: red where grass tufts may grow (painted green, outside roads,
    # buildings and the hills), green where 3D petals lie under the trees
    zs = (np.arange(h)[:, None] + 0.5) / px - D / 2
    xs = (np.arange(w)[None, :] + 0.5) / px - W / 2
    grows = (img[..., 1] > img[..., 0] * 1.12) & (img[..., 1] > img[..., 2] * 1.35)
    blocked = [(ROAD_X0 - 0.25, ROAD_X1 + 0.25, -D / 2, D / 2),
               (PLAT['x0'] - 0.1, PLAT['x1'] + 2.3, PLAT['z0'] - 1.8, PLAT['z1'] + 0.1),
               (-12.4, -3.6, -16.7, -9.9)] + [(x0 - 0.2, x1 + 0.2, z0 - 0.2, z1 + 0.2) for x0, x1, z0, z1 in PADDIES] + [SHED, SHRINE]
    for hs in HOUSES:
        turned = abs(math.sin(hs.get('ry', 0.0))) > 0.5
        hx = (hs['d'] if turned else hs['w']) / 2 + 0.45
        hz = (hs['w'] if turned else hs['d']) / 2 + 0.45
        blocked.append((hs['x'] - hx, hs['x'] + hx, hs['z'] - hz, hs['z'] + hz))
    for x0, x1, z0, z1 in blocked:
        grows &= ~((xs > x0) & (xs < x1) & (zs > z0) & (zs < z1))
    for hl in HILLS:
        inside = ((xs - hl['cx']) / hl['rx']) ** 2 + ((zs - hl['cz']) / hl['rz']) ** 2 < 1.0
        grows &= ~(inside & (hl['s'] * xs > HILL_FRONT - 0.5))
    mask = np.zeros((h, w, 3), np.float32)
    mask[..., 0] = grows
    mask[..., 1] = fallen[..., 0]
    IMAGES['meadow'] = to_image('harukaze_meadow_mask', mask)
    IMAGES['meadow'].colorspace_settings.name = 'Non-Color'
    return to_image('harukaze_grass', img)


def paint_road():
    w, h = 256, 2048
    px, pz = w / ROAD_W, h / D
    Z = lambda z: int((z + D / 2) * pz)
    X = lambda x: int(x * px)
    img = np.empty((h, w, 3), np.float32)
    img[:] = hex_np('#7a7581')
    noise = np_rng.random((h, w))
    img[noise > 0.85] = hex_np('#8e8995')
    img[noise < 0.15] = hex_np('#6d6874')
    deck0, deck1 = TRACK_Z - 1.95, TRACK_Z + 1.95
    img[Z(deck0):Z(deck1)] = hex_np('#a9a39a')
    for k in range(5):
        c = min(w - 2, int(k * w / 4))
        img[Z(deck0):Z(deck1), c:c + 2] = hex_np('#8b857d')
    for rz in (TRACK_Z - 0.55, TRACK_Z + 0.55):
        img[Z(rz - 0.09):Z(rz + 0.09)] = hex_np('#5b5751')
    white = hex_np('#f6f3ea')
    for ex in (0.28, ROAD_W - 0.28):
        img[:Z(deck0 - 0.3), X(ex - 0.07):X(ex + 0.07)] = white
        img[Z(deck1 + 0.3):, X(ex - 0.07):X(ex + 0.07)] = white
    z = -D / 2 + 0.5
    while z < D / 2:
        if not (z + 1.8 > -11 and z < 9.5):
            img[Z(z):Z(z + 1.8), X(ROAD_W / 2 - 0.06):X(ROAD_W / 2 + 0.06)] = white
        z += 3.2
    img[Z(4.1):Z(4.52), X(0.28):X(ROAD_W / 2 - 0.02)] = white
    img[Z(-6.5):Z(-6.08), X(ROAD_W / 2 + 0.02):X(ROAD_W - 0.28)] = white
    return to_image('harukaze_road', img)


def paint_vending(name, body, accent, drinks):
    w, h = 64, 128
    img = np.empty((h, w, 3), np.float32)
    img[:] = hex_np(body)
    img[4:66, 4:60] = hex_np('#f4f8fb')
    for row in range(3):
        y = 8 + row * 20
        img[y + 14:y + 16, 5:59] = hex_np('#d6e2ea')
        for i in range(6):
            x = 6 + i * 9
            img[y + 2:y + 14, x:x + 6] = hex_np(drinks[(row * 6 + i * 5) % len(drinks)])
            img[y + 17:y + 18, x + 1:x + 4] = hex_np('#42d47a')
    img[70:93, 4:60] = hex_np(accent)
    for i in range(48):
        yy = int(81 + math.sin(i / 48 * math.pi * 3) * 4)
        img[yy:yy + 2, 8 + i] = 1.0
    img[97:108, 49:57] = hex_np('#d7dbe2')
    img[110:122, 8:56] = hex_np('#25232c')
    return to_image(name, img)


# --------------------------------------------------------------------------- the block


def build_block():
    add('grassTop', plane_up(W, D, uv=True))
    add('grassLip', box(W + 0.5, 0.56, D + 0.5, 0, -0.58, 0))
    add('earth', box(W + 0.1, 2.0, D + 0.1, 0, -2.55, 0))
    add('earthDark', box(W - 0.3, 0.85, D - 0.3, 0, -3.4, 0))
    add('stoneDark', box(W - 1.2, 2.0, D - 1.2, 0, -5.4, 0))
    for _ in range(70):
        side = int(rand(0, 4))
        t = rand(-0.48, 0.48)
        y = rand(-2.35, -0.85)
        r = rand(0.2, 0.5)
        x = t * W if side < 2 else (1 if side == 2 else -1) * (W / 2 + 0.05)
        z = ((1 if side == 0 else -1) * (D / 2 + 0.05)) if side < 2 else t * D
        add('stoneLight', rock(r).rotate_y(rand(0, 3)).translate(x, y, z))
    for row in range(2):
        y = -4.35 - row * 0.95
        inset = 0.45 + row * 0.25
        for length, along in ((W, 'x'), (D, 'z')):
            for s in (-1, 1):
                p = -length / 2 + inset + (0.9 if row else 0)
                while p < length / 2 - inset - 0.4:
                    seg = min(rand(1.6, 3.4), length / 2 - inset - p)
                    hh = rand(0.8, 0.92)
                    out = rand(-0.08, 0.12)
                    key = 'stone' if rng() < 0.55 else 'stoneLight'
                    across = (D if along == 'x' else W) / 2 - inset + out
                    if along == 'x':
                        add(key, box(seg - 0.08, hh, 0.9, p + seg / 2, y, s * (across - 0.45)))
                    else:
                        add(key, box(0.9, hh, seg - 0.08, s * (across - 0.45), y, p + seg / 2))
                    p += seg


# --------------------------------------------------------------------------- hills and tunnels


def build_hills():
    for h in HILLS:
        s = h['s']
        rings, seg = 12, 30
        grid = {}
        verts = []

        def vert(iv, iu):
            key = (iv, iu % seg) if iv > 0 else (0, 0)
            if key in grid:
                return grid[key]
            theta = (math.pi / 2) * iv / rings
            phi = 2 * math.pi * (iu % seg) / seg
            dx, dy, dz = -math.cos(phi) * math.sin(theta), math.cos(theta), math.sin(phi) * math.sin(theta)
            n = math.sin(iv * 12.9898 + (iu % seg) * 78.233 + s * 4.1) * 43758.5453
            k = 1 + ((n - math.floor(n)) - 0.5) * 0.12 if dy > 0.02 else 1.0
            x = h['cx'] + dx * h['rx'] * k
            edge = 1 - 0.78 * smoothstep(abs(x), W / 2 - 6.5, W / 2)
            y = max(0.0, dy * h['ry'] * k * edge)
            z = min(D / 2, max(-D / 2, h['cz'] + dz * h['rz'] * k))
            x = min(-HILL_FRONT, max(-W / 2, x)) if s < 0 else min(W / 2, max(HILL_FRONT, x))
            grid[key] = len(verts)
            verts.append(Vector((x, y, z)))
            return grid[key]

        faces = []
        for iu in range(seg):
            faces.append((vert(0, 0), vert(1, iu), vert(1, iu + 1)))
        for iv in range(1, rings):
            for iu in range(seg):
                faces.append((vert(iv, iu), vert(iv + 1, iu), vert(iv + 1, iu + 1), vert(iv, iu + 1)))
        parts = {'hill': [], 'concreteDark': [], 'earth': []}
        for f in faces:
            pts = [verts[i] for i in f]
            area = sum(((pts[i] - pts[0]).cross(pts[i + 1] - pts[0])).length for i in range(1, len(pts) - 1))
            if area < 1e-5:
                continue
            on_front = all(abs(abs(p.x) - HILL_FRONT) < 1e-4 for p in pts)
            on_back = all(abs(abs(p.x) - W / 2) < 1e-4 for p in pts)
            parts['concreteDark' if on_front else 'earth' if on_back else 'hill'].append(f)
        for key, fs in parts.items():
            if not fs:
                continue
            remap = {}
            local_v, local_f = [], []
            for f in fs:
                nf = []
                for i in f:
                    if i not in remap:
                        remap[i] = len(local_v)
                        local_v.append(verts[i])
                    nf.append(remap[i])
                local_f.append(nf)
            add(key, Geo(local_v, local_f))
        build_portal(s)


def build_portal(s):
    shape = [(-4.6, 0), (-2.45, 0), (-2.45, 3.4)]
    for i in range(1, 14):
        a = math.pi - math.pi * i / 14
        shape.append((2.45 * math.cos(a), 3.4 + 2.45 * math.sin(a)))
    shape += [(2.45, 3.4), (2.45, 0), (4.6, 0), (4.6, 6.9), (-4.6, 6.9)]
    face = prism(shape, 1.1).rotate_y(math.pi / 2).translate(-(PORTAL + 1.1) if s < 0 else PORTAL, 0, TRACK_Z)
    add('concrete', face)
    add('concrete', box(1.5, 0.4, 10.0, s * (PORTAL + 0.45), 6.9, TRACK_Z))
    for side in (-1, 1):
        add('concreteDark', box(1.25, 6.9, 0.55, s * (PORTAL + 0.5), 0, TRACK_Z + side * 4.5))
    add('concreteDark', box(1.18, 0.7, 0.8, s * (PORTAL + 0.52), 5.55, TRACK_Z))
    add('stoneDark', box(1.16, 0.55, 2.6, s * (PORTAL + 0.52), 6.2, TRACK_Z))
    SIGNS.append(('桜台隧道' if s < 0 else '山彦隧道', 0.3, Vector((s * (PORTAL - 0.075), 6.475, TRACK_Z)),
                  '+x' if s < 0 else '-x', 'textCream', dict(spacing=1.15)))
    add('tunnelDark', box(0.5, 6.3, 5.4, s * (CLIP_X + 0.25), 0, TRACK_Z))


# --------------------------------------------------------------------------- track and road


def build_track():
    profile = [(-1.95, 0), (1.95, 0), (1.3, 0.42), (-1.3, 0.42)]
    for x0, x1 in ((-CLIP_X, ROAD_X0 - 0.05), (ROAD_X1 + 0.05, CLIP_X)):
        add('ballast', prism(profile, x1 - x0).rotate_y(math.pi / 2).translate(x0, 0, TRACK_Z))
        x = x0 + 0.35
        while x < x1 - 0.2:
            add('sleeper', box(0.3, 0.1, 2.35, x, 0.4, TRACK_Z))
            x += 0.64
    for s in (-1, 1):
        z = TRACK_Z + s * 0.55
        add('rail', box(CLIP_X * 2, 0.13, 0.1, 0, 0.47, z))
        add('railHead', box(CLIP_X * 2, 0.03, 0.12, 0, RAIL_Y - 0.03, z))


def road_y(z):
    up = smoothstep(z, TRACK_Z - 3.6, TRACK_Z - 1.95)
    down = 1 - smoothstep(z, TRACK_Z + 1.95, TRACK_Z + 3.6)
    return 0.03 + (RAIL_Y - 0.035) * up * down


def build_road():
    rows = 160
    verts, faces, uvs = [], [], []
    for i in range(rows + 1):
        z = -D / 2 + D * i / rows
        verts += [(ROAD_X0, road_y(z), z), (ROAD_X1, road_y(z), z)]
    for i in range(rows):
        a, b = i * 2, i * 2 + 2
        v0, v1 = 1 - i / rows, 1 - (i + 1) / rows
        faces.append((a, b, b + 1, a + 1))
        uvs.append(((0, v0), (0, v1), (1, v1), (1, v0)))
    add('road', Geo(verts, faces, uvs=uvs))
    pts = []
    z = TRACK_Z - 3.7
    while z <= TRACK_Z + 3.7 + 1e-6:
        pts.append((z, road_y(z) - 0.01))
        z += 0.2
    pts += [(TRACK_Z + 3.7, 0), (TRACK_Z - 3.7, 0)]
    add('metalDark', prism(pts, ROAD_W - 0.02).rotate_y(-math.pi / 2).translate(ROAD_X1 - 0.01, 0, 0))


# --------------------------------------------------------------------------- platform and station

LAMPS = []


def build_platform():
    x0, x1, z0, z1, h = PLAT['x0'], PLAT['x1'], PLAT['z0'], PLAT['z1'], PLAT['h']
    add('concrete', prism([(x0, 0), (x1 + 2.2, 0), (x1, h), (x0, h)], z1 - z0).translate(0, 0, z0))
    add('whiteLine', box(x1 - x0, 0.02, 0.16, (x0 + x1) / 2, h, z1 - 0.08))
    add('tactile', box(x1 - x0, 0.035, 0.42, (x0 + x1) / 2, h, z1 - 0.75))
    # tactile dots
    x = x0 + 0.1
    while x < x1 - 0.05:
        for dz in (-0.12, 0.0, 0.12):
            add('tactile', box(0.06, 0.02, 0.06, x, h + 0.035, z1 - 0.75 + dz))
        x += 0.15
    for i in range(3):
        add('concrete', box(2.0, h * (3 - i) / 4, 0.56, -7.6, 0, z0 - 0.28 - i * 0.56))
    for sx in (-8.65, -6.55):
        add('catMast', box(0.06, 0.9, 0.06, sx, h, z0 + 0.02))
        add('catMast', box(0.06, 0.9, 0.06, sx, 0.29, z0 - 1.6))
        add('catMast', beam((sx, h + 0.9, z0 + 0.02), (sx, 1.19, z0 - 1.6), 0.06))
    fz = z0 + 0.06
    for a, b in ((x0 + 0.1, -8.75), (-6.45, x1 - 0.1)):
        n = round((b - a) / 1.5)
        for i in range(n + 1):
            add('fence', box(0.08, 1.0, 0.08, a + (b - a) * i / n, h, fz))
        for ry in (0.42, 0.86):
            add('fence', box(b - a, 0.06, 0.05, (a + b) / 2, h + ry, fz))
    x = -21.6
    while x <= x0 - 0.4:
        add('fence', box(0.07, 0.8, 0.07, x, 0, TRACK_Z - 2.75))
        x += 1.45
    for ry in (0.32, 0.68):
        add('fence', box(x0 - 0.4 + 21.6, 0.05, 0.04, (x0 - 0.4 - 21.6) / 2, ry, TRACK_Z - 2.75))

    build_shelter()
    bench(0.9, h, -6.75, 0)
    bench(4.9, h, -6.75, 0)
    name_board(-4.3, -7.0)
    vending_machine(-13.15, 'vendRed', 'vend1')
    vending_machine(-12.0, 'binBlue', 'vend2')
    bins(-10.95)
    platform_lamp(-9.6)
    platform_lamp(8.9)


def bench(x, y, z, ry, length=2.1):
    with at(x, y, z, ry):
        for sx in (-length / 2 + 0.2, length / 2 - 0.2):
            add('metalDark', box(0.07, 0.42, 0.44, sx, 0, 0))
            add('metalDark', box(0.07, 0.5, 0.07, sx, 0.42, -0.22))
        for sz in (-0.15, 0, 0.15):
            add('wood', box(length, 0.05, 0.13, 0, 0.42, sz))
        for sy in (0.62, 0.8):
            add('wood', box(length, 0.13, 0.04, 0, sy, -0.24))


SIGNS = []  # (text, glyph height in metres, web position, facing, material, options)


def name_board(x, z):
    h = PLAT['h']
    with at(x, h, z, 0):
        for sx in (-1.45, 1.45):
            add('metalDark', box(0.1, 2.75, 0.06, sx, 0, 0))
        add('signBoard', box(3.55, 1.6, 0.08, 0, 1.18, 0))
        add('metalDark', box(3.6, 0.07, 0.12, 0, 2.78, 0))
        for face in (1, -1):
            zf = face * 0.045
            add('signPink', box(3.4, 0.24, 0.012, 0, 1.4, zf))
            facing = '+z' if face > 0 else '-z'
            # Sakuradai lies west (-x) and Yamabiko east, whichever face you read
            west, east = ('LEFT', 'RIGHT') if face > 0 else ('RIGHT', 'LEFT')
            SIGNS.append(('はるかぜ', 0.5, to_world(0, 2.26, zf), facing, 'textDark', {}))
            SIGNS.append(('春風  Harukaze', 0.17, to_world(0, 1.82, zf), facing, 'textDark', {}))
            zb = zf + face * 0.012  # in front of the pink band
            SIGNS.append(('◀ さくらだい' if face > 0 else 'さくらだい ▶', 0.14, to_world(-1.6, 1.52, zb), facing, 'textWhite', dict(align=west)))
            SIGNS.append(('やまびこ ▶' if face > 0 else '◀ やまびこ', 0.14, to_world(1.6, 1.52, zb), facing, 'textWhite', dict(align=east)))
            SIGNS.append(('Sakuradai', 0.08, to_world(-1.25, 1.27, zf), facing, 'textDark', dict(align=west)))
            SIGNS.append(('Yamabiko', 0.08, to_world(1.25, 1.27, zf), facing, 'textDark', dict(align=east)))


def vending_machine(x, body, face):
    with at(x, PLAT['h'], PLAT['z0'] + 0.65, 0):
        add(body, box(1.05, 1.9, 0.75))
        add('metalDark', box(1.1, 0.08, 0.8, 0, 1.9, 0))
        add(face, plane_front(0.95, 1.8).translate(0, 0.96, 0.378))


def bins(x):
    for i, key in enumerate(('binBlue', 'binGreen', 'binYellow')):
        with at(x + i * 0.38, PLAT['h'], PLAT['z0'] + 0.5, 0):
            add(key, box(0.34, 0.82, 0.36))
            add('fence', box(0.36, 0.04, 0.38, 0, 0.82, 0))
            add('black', cyl(0.07, 0.07, 0.02, 0, 0.86, 0.02, 10))


def platform_lamp(x):
    with at(x, PLAT['h'], PLAT['z0'] + 0.35, 0):
        add('metalDark', cyl(0.06, 0.08, 3.4))
        add('metalDark', beam((0, 3.3, 0), (0, 3.45, 1.0), 0.07))
        add('metalDark', box(1.15, 0.1, 0.26, 0, 3.32, 1.0))
        add('lampLight', box(1.05, 0.04, 0.18, 0, 3.29, 1.0))
        LAMPS.append((to_world(0, 3.05, 1.0), 1.0))


def build_shelter():
    x0, length, back, depth = -0.6, 7.8, PLAT['z0'], 4.5
    h = PLAT['h']
    y_back = h + 3.35
    slope = math.atan(0.35 / depth)
    for px in (-0.2, 3.3, 6.8):
        add('fence', box(0.18, 3.3, 0.18, px, h, back + 0.45))
        add('fence', beam((px, y_back - 0.18, back + 0.2), (px, y_back - 0.51, back + depth - 0.3), 0.14, 0.12))
        add('fence', beam((px, h + 2.35, back + 0.45), (px, y_back - 0.3, back + 2.2), 0.09))
    add('shelterWall', box(length - 0.6, 2.15, 0.08, x0 + length / 2, h + 0.15, back + 0.32))
    add('fence', box(length - 0.4, 0.14, 0.14, x0 + length / 2, h + 2.3, back + 0.32))
    amp, period = 0.05, 0.34
    n = round(length / period * 6)
    pts = [((i / n) * length, amp * math.sin((i / n) * length / period * math.pi * 2)) for i in range(n + 1)]
    pts += [((i / n) * length, amp * math.sin((i / n) * length / period * math.pi * 2) - 0.05) for i in range(n, -1, -1)]
    add('shelterRoof', prism(pts, depth).rotate_x(slope).translate(x0, y_back, back))
    add('fence', box(length + 0.05, 0.22, 0.08, x0 + length / 2, y_back - depth * math.sin(slope) - 0.2, back + depth))
    add('metalDark', box(1.4, 0.08, 0.2, 3.3, y_back - 0.62, back + 2.9))
    add('lampLight', box(1.3, 0.03, 0.14, 3.3, y_back - 0.65, back + 2.9))
    LAMPS.append((Vector((3.3, y_back - 0.9, back + 2.9)), 0.9))
    # two-faced clock on the front beam, set to ten past ten
    cx, cz, cy = 1.5, back + depth - 0.45, y_back - 1.15
    add('metalDark', box(0.04, 0.55, 0.04, cx, cy + 0.3, cz))
    add('fence', cyl(0.36, 0.36, 0.14, 0, -0.07, 0, 24).rotate_x(math.pi / 2).translate(cx, cy, cz))
    for face in (1, -1):
        zf = cz + face * 0.072
        add('clockFace', disc(0.3).rotate_y(0 if face > 0 else math.pi).translate(cx, cy, zf))
        for i in range(12):
            a = i / 12 * 2 * math.pi
            add('clockHand', box(0.025, 0.06 if i % 3 else 0.09, 0.004, 0, 0.18, 0).rotate_z(-a).translate(cx, cy, zf + face * 0.004))
        add('clockHand', box(0.03, 0.15, 0.006, 0, 0, 0).rotate_z(face * -math.radians(305)).translate(cx, cy, zf + face * 0.008))
        add('clockHand', box(0.022, 0.23, 0.006, 0, 0, 0).rotate_z(face * -math.radians(60)).translate(cx, cy, zf + face * 0.012))
        add('clockPin', cyl(0.025, 0.025, 0.012, 0, 0, 0, 10).rotate_x(math.pi / 2).translate(cx, cy, zf + face * 0.016))


def kawara(width, length, thick=0.12, amp=0.035, period=0.26):
    """A slab of rolled clay tiles: a sine-wave section across the roof, run down the slope
    (along z, centred), like the corrugated shelter roof."""
    n = max(8, round(width / period * 6))
    top = [(-width / 2 + width * i / n, amp * math.sin(2 * math.pi * (width * i / n) / period)) for i in range(n + 1)]
    bottom = [(x, y - thick) for x, y in reversed(top)]
    return prism(top + bottom, length).translate(0, thick / 2, -length / 2)


def gable(roof, wall_key, w, d, y, pitch=0.5, over=0.45, thick=0.16, tiles=False):
    half = d / 2 + over
    rise = (d / 2) * math.tan(pitch)
    slab = half / math.cos(pitch)
    for s in (-1, 1):
        g = kawara(w + over * 2, slab) if tiles else box(w + over * 2, thick, slab, 0, -thick / 2, 0)
        g.rotate_x(s * pitch)
        add(roof, g.translate(0, y + rise - (half / 2) * math.tan(pitch) + thick / 2, s * half / 2))
    add(wall_key, prism([(-d / 2, 0), (d / 2, 0), (0, rise)], w).rotate_y(math.pi / 2).translate(-w / 2, y, 0))
    ridge_y = y + rise + thick * 0.4
    if tiles:
        # stacked ridge tiles with a round cap, and an oni-gawara block at each end
        span = w + over * 2 + 0.1
        add(roof, box(span, 0.1, 0.42, 0, ridge_y - 0.02, 0))
        add(roof, box(span - 0.05, 0.1, 0.3, 0, ridge_y + 0.08, 0))
        add(roof, cyl(0.1, 0.1, span, 0, -span / 2, 0, 10).rotate_z(math.pi / 2).translate(0, ridge_y + 0.2, 0))
        for sx in (-1, 1):
            add(roof, box(0.16, 0.52, 0.52, sx * span / 2, ridge_y - 0.1, 0))
    else:
        add(roof, box(w + over * 2 + 0.1, 0.16, 0.3, 0, ridge_y, 0))
    return rise


def window_on(face, along, y, offset, w, h, glass='window'):
    n = 1 if face[0] == '+' else -1
    on_z = face[1] == 'z'

    def place(g, out):
        if on_z:
            return g.translate(along, y, n * (offset + out))
        return g.rotate_y(math.pi / 2).translate(n * (offset + out), y, along)

    add('frame', place(box(w + 0.18, h + 0.18, 0.06, 0, -(h + 0.18) / 2, 0), 0.02))
    add(glass, place(box(w, h, 0.06, 0, -h / 2, 0), 0.05))
    add('frame', place(box(w + 0.3, 0.07, 0.16, 0, -h / 2 - 0.135, 0), 0.06))


def pick_window():
    return pick(['window', 'window', 'window2', 'window2', 'windowOff'])


def build_station():
    w, d, h = 8.0, 5.0, 3.0
    with at(-8, 0, -12.5, 0):
        add('concreteDark', box(w + 0.4, 0.25, d + 0.4))
        add('earthDark', box(w + 0.06, 0.9, d + 0.06, 0, 0.25, 0))
        add('wall', box(w, h - 0.25, d, 0, 0.25, 0))
        for sx in (-1, 1):
            for sz in (-1, 1):
                add('wood', box(0.2, h - 0.25, 0.2, sx * w / 2, 0.25, sz * d / 2))
        add('wood', box(w + 0.1, 0.16, d + 0.1, 0, h - 0.16, 0))
        gable('roofTeal', 'wall', w, d, h, 0.52, 0.6)
        # north front: glass doors under a small gabled porch
        add('frame', box(2.1, 2.35, 0.08, 0, 0.25, -d / 2 - 0.02))
        add('window', box(0.85, 2.05, 0.06, -0.47, 0.3, -d / 2 - 0.06))
        add('window', box(0.85, 2.05, 0.06, 0.47, 0.3, -d / 2 - 0.06))
        for px in (-1.35, 1.35):
            add('wood', box(0.2, 2.75, 0.2, px, 0.25, -d / 2 - 1.5))
        add('wood', box(3.0, 0.3, 0.22, 0, 2.75, -d / 2 - 1.5))
        add('wood', box(0.2, 0.3, 1.4, -1.35, 2.75, -d / 2 - 0.8))
        add('wood', box(0.2, 0.3, 1.4, 1.35, 2.75, -d / 2 - 0.8))
        with at(0, 0, -d / 2 - 0.8, math.pi / 2):
            gable('roofTeal', 'wall', 1.7, 3.0, 3.05, 0.6, 0.3, 0.14)
        add('signWood', box(2.4, 0.7, 0.06, 0, 2.5, -d / 2 - 1.65))
        SIGNS.append(('春風駅', 0.42, to_world(0, 2.85, -d / 2 - 1.69), '-z', 'textCream', dict(spacing=1.3)))
        window_on('-z', -2.7, 1.75, d / 2, 1.3, 1.0)
        window_on('-z', 2.7, 1.75, d / 2, 1.3, 1.0)
        # south side faces the platform: doorway, windows and a second sign
        add('frame', box(1.3, 2.25, 0.08, 0.4, 0.25, d / 2 + 0.02))
        add('black', box(1.1, 2.1, 0.06, 0.4, 0.25, d / 2 + 0.04))
        window_on('+z', 2.7, 1.6, d / 2, 1.4, 0.9)
        window_on('+z', -2.4, 1.6, d / 2, 1.2, 0.9, 'window2')
        add('signWood', box(2.75, 0.72, 0.06, -2.2, 2.35, d / 2 + 0.03))
        SIGNS.append(('春風駅', 0.46, to_world(-2.2, 2.71, d / 2 + 0.07), '+z', 'textCream', dict(spacing=1.3)))
        window_on('+x', 0, 1.6, w / 2, 1.2, 0.9)
        window_on('-x', 0, 1.6, w / 2, 1.2, 0.9, 'window2')
    with at(-11.6, 0, -16.6, 0):
        add('metalDark', cyl(0.07, 0.09, 3.0))
        add('lampLight', box(0.42, 0.5, 0.42, 0, 3.0, 0))
        add('metalDark', cyl(0.0, 0.42, 0.4, 0, 3.5, 0, 4).rotate_y(math.pi / 4))
        LAMPS.append((to_world(0, 3.25, 0), 1.0))
    with at(-2.6, 0, -16.2, 0):
        add('vendRed', cyl(0.3, 0.3, 1.25, 0, 0, 0, 14))
        add('vendRed', ball(0.3, 0, 1.25, 0, 1))
        add('black', box(0.3, 0.05, 0.1, 0, 0.95, -0.27))
    bench(-5.4, 0, -15.6, math.pi, 1.8)


# --------------------------------------------------------------------------- houses and garden


def house(o):
    w, d, h = o['w'], o['d'], o['h']
    wall, roof = o['wall'], o['roof']
    with at(o['x'], 0, o['z'], o.get('ry', 0.0)):
        add('concreteDark', box(w + 0.2, 0.3, d + 0.2))
        add(wall, box(w, h, d, 0, 0.3, 0))
        gable(roof, wall, w, d, h + 0.3, rand(0.45, 0.6), 0.45, tiles=True)
        dx = -w * 0.22
        floors = o.get('floors', 1)
        add('earthDark', box(0.95, 1.9, 0.08, dx, 0.3, -d / 2 - 0.03))
        add(roof, box(1.5, 0.1, 0.7, dx, 2.45, -d / 2 - 0.3))
        for f in range(floors):
            wy = 0.3 + 1.45 + f * 2.05
            if f > 0:
                window_on('-z', dx, wy, d / 2, 0.9, 0.75, pick_window())
            window_on('-z', w * 0.24, wy, d / 2, 1.2, 0.8, pick_window())
            # one-storey houses open onto an engawa instead (the draws keep the scene's seed order)
            for along, ww in ((-w * 0.2, 1.3), (w * 0.25, 0.8)):
                glass = pick_window()
                if floors > 1 or f > 0:
                    window_on('+z', along, wy, d / 2, ww, 0.8, glass)
            window_on('-x', 0, wy, w / 2, 0.9, 0.75, pick_window())
            window_on('+x', 0, wy, w / 2, 0.9, 0.75, pick_window())
        if floors > 1:
            # a 下屋 skirt roof between the storeys on both long sides
            for s in (-1, 1):
                skirt = kawara(w + 0.5, 0.85, 0.1).rotate_x(s * 0.42)
                add(roof, skirt.translate(0, 3.05 - 0.85 * math.sin(0.42) / 2, s * (d / 2 + 0.85 * math.cos(0.42) / 2)))
        else:
            # engawa: a raised timber veranda with floor-length sliding glass and a stepping stone
            ew = w * 0.72
            add('wood', box(ew, 0.09, 0.9, -w * 0.05, 0.55, d / 2 + 0.45))
            for px in (-ew / 2 + 0.1, -0.15, ew / 2 - 0.25):
                add('wood', box(0.1, 0.55, 0.1, -w * 0.05 + px, 0.0, d / 2 + 0.85))
            add('stoneLight', box(0.62, 0.22, 0.42, -w * 0.05, 0.0, d / 2 + 1.2))
            for i in range(4):
                add('window', box(ew / 4 - 0.06, 1.85, 0.05, -w * 0.05 - ew / 2 + ew / 8 + i * ew / 4, 0.66, d / 2 + 0.03))
            add('frame', box(0.35, 1.9, 0.12, -w * 0.05 + ew / 2 + 0.2, 0.62, d / 2 + 0.07))
            eave = kawara(ew + 0.6, 1.1, 0.1).rotate_x(0.35)
            add(roof, eave.translate(-w * 0.05, h + 0.12 - 1.1 * math.sin(0.35) / 2, d / 2 + 1.1 * math.cos(0.35) / 2))
        add('fence', box(0.7, 0.5, 0.3, w * 0.3, 0.3, d / 2 + 0.17))
        add('earthDark', cyl(0.2, 0.15, 0.3, dx + 0.85, 0, -d / 2 - 0.4))
        add('leaf', puff(0.3, dx + 0.85, 0.5, -d / 2 - 0.4))


def build_garden():
    x0, x1, z0, z1 = PATCH['x0'], PATCH['x1'], PATCH['z0'], PATCH['z1']
    for r in range(5):
        z = z0 + 0.7 + r * ((z1 - z0 - 1.2) / 4)
        add('earthDark', box(x1 - x0 - 1.6, 0.26, 0.62, (x0 + x1) / 2 - 0.6, 0, z))
        x = x0 + 0.5
        while x < x1 - 1.6:
            if r < 2:
                add('leafLight', puff(0.27, x, 0.42, z, 0.75))
            elif r == 2:
                for dz in (-0.08, 0.08):
                    add('leaf', cyl(0.035, 0.045, rand(0.5, 0.75), x, 0.24, z + dz, 5))
            elif r == 3:
                add('wood', box(0.04, 1.1, 0.04, x, 0.24, z))
                add('leafDark', puff(0.22, x + 0.05, 0.75, z, 1.2))
                if rng() < 0.7:
                    add('vendRed', ball(0.07, x + 0.13, 0.65, z + 0.12, 0))
            else:
                add('leafLight', cone(0.18, 0.4, 5).translate(x, 0.45, z))
            x += 0.34 if r == 2 else 0.72
    with at(x1 - 0.9, 0, (z0 + z1) / 2, -0.3):
        add('wood', box(0.08, 1.9, 0.08))
        add('wood', box(1.4, 0.07, 0.07, 0, 1.4, 0))
        add('binBlue', box(0.62, 0.65, 0.22, 0, 0.95, 0))
        add('wall', ball(0.2, 0, 1.78, 0, 1))
        add('binYellow', cyl(0.06, 0.42, 0.22, 0, 1.88, 0, 12))
        add('binYellow', cyl(0.13, 0.15, 0.16, 0, 2.06, 0, 12))
    for i in range(11):
        add('binYellow', box(0.06, 0.6, 0.06, x0 + (x1 - x0) * i / 10, 0, z0 - 0.1))
    add('binYellow', box(x1 - x0, 0.05, 0.05, (x0 + x1) / 2, 0.45, z0 - 0.1))


# --------------------------------------------------------------------------- trees, bushes, clouds


def cherry(x, z, s):
    base = hill_height(x, z) - 0.15
    with at(x, base, z, rand(0, math.pi * 2)):
        trunk_h = 2.1 * s
        add('trunk', cyl(0.17 * s, 0.27 * s, trunk_h, 0, 0, 0, 7))
        add('trunk', beam((0, trunk_h * 0.75, 0), (1.2 * s, trunk_h + 1.1 * s, 0.3 * s), 0.17 * s))
        add('trunk', beam((0, trunk_h * 0.7, 0), (-1.0 * s, trunk_h + 1.0 * s, -0.5 * s), 0.15 * s))
        add('trunk', beam((0, trunk_h * 0.9, 0), (0.1 * s, trunk_h + 1.4 * s, 0.9 * s), 0.13 * s))
        cy = trunk_h + 1.35 * s
        add(pick(['blossom1', 'blossom2']), puff(1.75 * s, 0, cy, 0))
        for i in range(7):
            a = (i / 7) * math.pi * 2 + rand(-0.3, 0.3)
            r = rand(1.15, 1.6) * s
            add(pick(['blossom1', 'blossom2', 'blossom3']), puff(rand(0.85, 1.25) * s, math.cos(a) * r, cy + rand(-0.55, 0.65) * s, math.sin(a) * r))
        add('blossom3', puff(1.0 * s, rand(-0.4, 0.4) * s, cy + 1.1 * s, rand(-0.4, 0.4) * s))


def cedar(x, z, s):
    with at(x, hill_height(x, z) - 0.2, z, rand(0, 3)):
        add('trunk', cyl(0.12 * s, 0.18 * s, 1.2 * s, 0, 0, 0, 7))
        for i in range(3):
            add('cedar', cone((1.35 - i * 0.32) * s, 1.9 * s, 7).translate(0, (1.9 + i * 1.05) * s, 0))


def round_tree(x, z, s):
    with at(x, hill_height(x, z) - 0.15, z, 0):
        add('trunk', cyl(0.13 * s, 0.2 * s, 1.6 * s, 0, 0, 0, 7))
        add('leaf', puff(1.3 * s, 0, 2.3 * s, 0))
        add('leafDark', puff(0.9 * s, 0.7 * s, 1.9 * s, 0.4 * s))
        add('leafLight', puff(0.8 * s, -0.5 * s, 2.8 * s, -0.3 * s))


def bush(x, z, s=1.0, flowers=False):
    y = hill_height(x, z)
    add(pick(['leaf', 'leafDark']), puff(0.6 * s, x, y + 0.35 * s, z, 0.8))
    add(pick(['leaf', 'leafLight']), puff(0.45 * s, x + 0.5 * s, y + 0.28 * s, z + 0.2 * s, 0.8))
    add('leafDark', puff(0.4 * s, x - 0.45 * s, y + 0.25 * s, z - 0.15 * s, 0.8))
    if flowers:
        for _ in range(7):
            a = rand(0, math.pi * 2)
            add('blossom2', ball(0.1 * s, x + math.cos(a) * 0.45 * s, y + rand(0.45, 0.7) * s, z + math.sin(a) * 0.4 * s, 0))


def build_nature():
    for x, z, s in CHERRIES:
        cherry(x, z, s)
    for x, z, s in ((-30.2, -6.2, 1.1), (-27.2, -8.6, 0.95), (-25.6, 6.6, 0.9), (-30.6, 1.8, 1.0),
                    (29.8, 3.8, 1.1), (26.6, 6.4, 0.9), (29.6, -9.2, 0.95), (25.2, -8.4, 0.85)):
        cedar(x, z, s)
    for x, z, s in ((-29.4, -14.0, 1.0), (-8.6, 18.6, 0.85), (30.0, 17.6, 0.9), (-20.6, 18.2, 0.85), (13.0, -15.4, 0.8)):
        round_tree(x, z, s)
    bushes = [
        (-13.8, -8.6, 1, True), (-11.4, -8.7, 0.9), (-5.6, -8.6, 1, True), (-2.6, -8.7, 0.9), (1.5, -8.6, 1.1, True), (6.2, -8.7, 1),
        (-12.9, -15.6, 0.9, True), (-3.2, -14.7, 1), (-14.6, -10.6, 0.9),
        (-28.2, 13.0, 1, True), (-22.2, 12.3, 0.9), (-18.4, 12.9, 1, True), (-13.0, 12.6, 0.9), (5.0, 12.7, 0.9, True), (10.6, 13.0, 1),
        (22.4, 13.0, 0.9), (22.8, 17.6, 1, True), (22.6, -13.4, 1), (23.0, -18.4, 0.9, True), (-23.4, -14.0, 0.9), (-29.6, -18.4, 1, True),
        (-26.0, -2.0, 1.2), (27.0, 1.5, 1.2), (-24.0, -6.4, 1.0), (24.4, -4.0, 1.0),
        (-16.2, 1.6, 0.8), (-6.6, 1.7, 0.8), (3.0, 1.9, 0.7), (11.2, 2.2, 0.8, True),
    ]
    for b in bushes:
        bush(b[0], b[1], b[2], len(b) > 3)
    for x, z, r in ((-17.5, -4.5, 0.4), (9.5, 6.8, 0.35), (-24.0, 9.0, 0.45), (19.6, -11.0, 0.4), (1.2, -18.6, 0.35), (-6.0, 10.6, 0.3)):
        add('stoneLight', rock(r).scale(1, 0.6, 1).translate(x, r * 0.25, z))


# --------------------------------------------------------------------------- the details of a rural halt
# Everything in this section draws from its own seed, so none of it moves the rest of the scene.

drng = mulberry32(0xDE7A11)


def drand(a=0.0, b=1.0):
    return a + (b - a) * drng()


PADDIES = [(3.6, 7.3, -15.4, -10.2), (7.5, 11.2, -15.4, -10.2)]
SHED = (-16.2, -12.4, -19.6, -17.8)
SHRINE = (-23.2, -19.9, -10.9, -7.1)


def build_paddies():
    """Two flooded rice paddies behind the platform, with earth levees; the second has
    its first rows of seedlings in."""
    for i, (x0, x1, z0, z1) in enumerate(PADDIES):
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        add('paddyWater', plane_up(x1 - x0 - 0.3, z1 - z0 - 0.3, cx, 0.07, cz))
        add('earthDark', box(x1 - x0 - 0.3, 0.06, z1 - z0 - 0.3, cx, 0.0, cz))
        for (w, d, x, z) in ((x1 - x0, 0.3, cx, z0 + 0.15), (x1 - x0, 0.3, cx, z1 - 0.15),
                             (0.3, z1 - z0 - 0.6, x0 + 0.15, cz), (0.3, z1 - z0 - 0.6, x1 - 0.15, cz)):
            add('hill', box(w, 0.16, d, x, 0, z))
        if i == 1:
            z = z0 + 0.6
            while z < z1 - 0.5:
                x = x0 + 0.55
                while x < x1 - 0.45:
                    add('leafLight', cone(0.05, 0.22, 4).translate(x + drand(-0.03, 0.03), 0.17, z))
                    x += 0.32
                z += 0.42


def nanohana_clump(x, z, s):
    add('leaf', puff(0.24 * s, x, 0.22 * s, z, 0.8, 1, drand))
    for _ in range(3):
        key = 'nanohana' if drng() < 0.6 else 'nanohanaLight'
        add(key, ball(drand(0.12, 0.2) * s, x + drand(-0.18, 0.18) * s, drand(0.5, 0.8) * s, z + drand(-0.18, 0.18) * s, 0))


def build_nanohana():
    """菜の花 along the line: rape blossom in staggered rows south of the track and beyond
    the boundary fence to the west."""
    step = 0.32 if Q['detail'] else 0.45
    masts = (-20.5, -11, -1.5, 8.5)
    for row, z in enumerate((2.45, 3.0, 3.55)):
        x = -21.0 + (step / 2 if row % 2 else 0)
        while x < 11.6:
            if not any(abs(x - m) < 0.55 for m in masts) or z > 2.8:
                nanohana_clump(x + drand(-0.08, 0.08), z + drand(-0.08, 0.08), drand(0.8, 1.15))
            x += step
    for z in (-5.1, -4.6, -4.15):
        x = -21.3
        while x < -14.9:
            nanohana_clump(x + drand(-0.08, 0.08), z + drand(-0.06, 0.06), drand(0.8, 1.1))
            x += step


def torii(x, z, ry, s=1.0):
    with at(x, 0, z, ry):
        for sx in (-0.75, 0.75):
            add('shu', cyl(0.09 * s, 0.11 * s, 2.5 * s, sx * s, 0, 0, 10))
            add('black', cyl(0.15 * s, 0.15 * s, 0.18 * s, sx * s, 0, 0, 10))
        add('shu', box(2.0 * s, 0.13 * s, 0.13 * s, 0, 1.95 * s, 0))
        add('shu', box(0.12 * s, 0.34 * s, 0.1 * s, 0, 2.08 * s, 0))
        add('shu', box(2.2 * s, 0.14 * s, 0.2 * s, 0, 2.45 * s, 0))
        for sx in (-1, 1):
            add('black', beam((0, 2.66 * s, 0), (sx * 1.38 * s, 2.8 * s, 0), 0.14 * s, 0.26 * s))


def stone_lantern(x, z):
    with at(x, 0, z, 0):
        add('stoneLight', cyl(0.2, 0.24, 0.15))
        add('stoneLight', cyl(0.08, 0.09, 0.55, 0, 0.15, 0, 8))
        add('stoneLight', box(0.32, 0.08, 0.32, 0, 0.7, 0))
        add('stoneLight', box(0.26, 0.24, 0.26, 0, 0.78, 0))
        add('lampLight', box(0.14, 0.12, 0.27, 0, 0.84, 0))
        add('stoneLight', cyl(0.0, 0.28, 0.2, 0, 1.02, 0, 4).rotate_y(math.pi / 4).translate(0, 0, 0))
        add('stoneLight', ball(0.05, 0, 1.25, 0, 0))


def jizo(x, z, ry):
    with at(x, 0, z, ry):
        add('stoneLight', cyl(0.13, 0.16, 0.42, 0, 0.05, 0, 10))
        add('stoneLight', ball(0.12, 0, 0.58, 0, 1))
        add('shu', cyl(0.15, 0.19, 0.14, 0, 0.3, 0, 10))
        add('stoneLight', box(0.4, 0.06, 0.34))


def build_shrine():
    """A little hillside shrine at the foot of the west hill: torii, hokora and two stone
    lanterns; and a pair of jizo by the road, red bibs on."""
    torii(-20.9, -9.0, math.pi / 2)
    with at(-22.55, 0, -9.0, -math.pi / 2):
        add('stoneLight', box(1.0, 0.45, 0.9))
        add('wood', box(0.7, 0.65, 0.6, 0, 0.45, 0))
        add('earthDark', box(0.3, 0.45, 0.02, 0, 0.5, -0.31))
        gable('roofGrey', 'wood', 0.7, 0.6, 1.1, 0.6, 0.18, 0.08)
    for z in (-10.1, -7.9):
        stone_lantern(-21.6, z)
    with at(12.48, 0, 7.1, 0):
        for px in (-0.3, 0.3):
            add('wood', box(0.06, 0.95, 0.06, px, 0, -0.2))
        add('roofGrey', box(0.8, 0.06, 0.55, 0, 0.95, -0.05))
    for x in (12.33, 12.63):
        jizo(x, 7.1, math.pi / 2)


def stop_sign(x, z, ry):
    """止まれ: the red inverted triangle with a white rim, on the driver's left."""
    face = '+z' if ry == 0 else '-z'
    with at(x, 0, z, ry):
        add('catMast', cyl(0.035, 0.04, 2.25, 0, 0, 0, 8))
        tri = lambda r: [(-r, 0.0), (r, 0.0), (0.0, -1.732 * r)]
        add('signWhite', prism(tri(0.46), 0.03).translate(0, 2.3, 0.04))
        add('vendRed', prism(tri(0.38), 0.03).translate(0, 2.25, 0.055))
        SIGNS.append(('止まれ', 0.12, to_world(0, 2.08, 0.09), face, 'textWhite', {}))
        SIGNS.append(('STOP', 0.045, to_world(0, 1.93, 0.09), face, 'textWhite', {}))


def crossing_warning(x, z, ry):
    """踏切あり: a yellow diamond with a little electric car."""
    with at(x, 0, z, ry):
        add('catMast', cyl(0.035, 0.04, 2.45, 0, 0, 0, 8))
        add('black', box(0.62, 0.62, 0.02, 0, -0.31, 0).rotate_z(math.pi / 4).translate(0, 2.45, 0.04))
        add('binYellow', box(0.54, 0.54, 0.02, 0, -0.27, 0).rotate_z(math.pi / 4).translate(0, 2.45, 0.052))
        add('black', box(0.3, 0.11, 0.01, 0, 2.38, 0.066))
        for wx in (-0.09, 0.09):
            add('black', box(0.05, 0.05, 0.01, wx, 2.33, 0.066))
        add('black', prism([(-0.06, 0.0), (0.06, 0.0), (0.0, 0.07)], 0.01).translate(0, 2.49, 0.061))


def curve_mirror(x, z, ry):
    with at(x, 0, z, ry):
        add('mirrorPole', cyl(0.045, 0.05, 3.0, 0, 0, 0, 8))
        add('mirrorPole', cyl(0.42, 0.42, 0.06, 0, -0.03, 0, 20).rotate_x(math.pi / 2).translate(0, 3.0, 0.08))
        add('mirrorGlass', disc(0.37).translate(0, 3.0, 0.115))
        add('mirrorPole', box(0.7, 0.04, 0.16, 0, 3.42, 0.14))


def bus_stop(x, z):
    with at(x, 0, z, 0):
        add('concreteDark', cyl(0.3, 0.32, 0.2))
        add('catMast', cyl(0.04, 0.04, 2.2, 0, 0.2, 0, 8))
        add('vendRed', cyl(0.3, 0.3, 0.05, 0, -0.025, 0, 20).rotate_x(math.pi / 2).translate(0, 2.25, 0))
        add('signWhite', cyl(0.22, 0.22, 0.07, 0, -0.035, 0, 20).rotate_x(math.pi / 2).translate(0, 2.25, 0))
        add('signWhite', box(0.36, 0.5, 0.04, 0, 1.05, 0.05))
        for face, zz in (('+z', 0.04), ('-z', -0.04)):
            SIGNS.append(('春風駅前', 0.06, to_world(0, 2.25, zz), face, 'textDark', {}))


def build_road_furniture():
    """Lidded 側溝 gutters on both verges, stop and level-crossing signs on each approach,
    curve mirrors at the two junctions and a bus stop."""
    for gx, segments in ((ROAD_X0 - 0.22, [(-20.0, TRACK_Z - 3.8), (TRACK_Z + 4.4, 20.0)]),
                         (ROAD_X1 + 0.22, [(-20.0, TRACK_Z - 4.5), (TRACK_Z + 3.8, 20.0)])):
        for z0, z1 in segments:
            add('concreteDark', box(0.4, 0.04, z1 - z0, gx, 0, (z0 + z1) / 2))
            z = z0
            while z < z1 - 0.3:
                add('gutter', box(0.38, 0.05, 0.48, gx, 0.02, z + 0.25))
                z += 0.5
    stop_sign(ROAD_X0 - 0.7, 4.6, 0.0)
    stop_sign(ROAD_X1 + 0.7, -7.0, math.pi)
    crossing_warning(ROAD_X0 - 0.7, 12.4, 0.0)
    crossing_warning(ROAD_X1 + 0.7, -14.0, math.pi)
    curve_mirror(ROAD_X1 + 0.75, 9.0, -math.pi / 2)
    curve_mirror(ROAD_X1 + 0.75, -18.1, -math.pi / 2)
    bus_stop(ROAD_X1 + 0.9, -11.0)


def build_pole_dressing():
    """Transformers, service drops to three houses with meter boxes, guy wires with yellow
    guards and tiger-striped sleeves on the poles by the road."""
    for x, z in ((2.6, 10.6), (-16.2, 10.6)):
        add('catMast', cyl(0.26, 0.26, 0.75, x, 5.75, z + 0.38, 12))
        add('metalDark', cyl(0.28, 0.27, 0.06, x, 6.5, z + 0.38, 12))
        add('metalDark', box(0.1, 0.5, 0.2, x, 5.9, z + 0.14))
        for off in (-0.12, 0.0, 0.12):
            add('wire', tube([(x + off, 6.56, z + 0.38), (x + off * 3, 6.85, z + 0.15), (x + off * 6, 7.12, z)], 0.012, 4))
    drops = [((-25.6, 10.6), (-23.8, 2.85, 12.45)), ((-16.2, 10.6), (-15.0, 4.55, 12.95)), ((2.6, 10.6), (6.4, 2.85, 12.75))]
    for (px, pz), (ex, ey, ez) in drops:
        for off in (-0.06, 0.06):
            add('wire', sag_wire((px + off, 5.6, pz), (ex + off, ey, ez), 0.18, 0.014))
        add('fence', box(0.22, 0.32, 0.1, ex, 1.25, ez - 0.02))
        add('fence', cyl(0.03, 0.03, 0.1, ex, ey - 0.05, ez - 0.05, 6))
    for (px, pz), (ax, az) in (((-25.6, 10.6), (-28.4, 10.6)), ((11.9, -17.8), (11.9, -19.7))):
        top, anchor = Vector((px, 6.8, pz)), Vector((ax, 0.0, az))
        add('wire', tube([top, anchor], 0.018, 4))
        add('binYellow', beam(anchor, anchor + (top - anchor).normalized() * 1.8, 0.09))
        add('concreteDark', box(0.3, 0.12, 0.3, ax, 0, az))
    for z in (-17.8, -9.2, 10.6):
        add('stripe', cyl(0.185, 0.19, 1.8, 11.9, 0, z, 10))


def build_platform_kit():
    """The kit of an unmanned halt: an IC card reader at the foot of the steps, the
    one-man driver's mirror, the stop marker, a timetable and posters in the shelter."""
    h = PLAT['h']
    with at(-9.05, 0, -9.72, 0):
        add('fence', box(0.3, 1.0, 0.24))
        add('metalDark', box(0.32, 0.06, 0.3, 0, -0.03, 0).rotate_x(0.35).translate(0, 1.03, 0))
        add('icPad', box(0.17, 0.02, 0.14, 0, -0.01, 0).rotate_x(0.35).translate(0, 1.07, 0.02))
    with at(9.55, h, -3.85, -1.22):
        add('catMast', cyl(0.04, 0.05, 2.5, 0, 0, 0, 8))
        add('shelterRoof', box(0.98, 0.68, 0.05, 0, 1.8, 0.04))
        add('mirrorGlass', box(0.88, 0.58, 0.02, 0, 1.85, 0.075))
    with at(7.75, h, -2.95, 0):
        add('catMast', cyl(0.03, 0.03, 1.1, 0, 0, 0, 6))
        add('signWhite', box(0.04, 0.42, 0.34, 0, 1.0, 0))
        SIGNS.append(('2', 0.24, to_world(-0.025, 1.21, 0), '-x', 'textDark', {}))
    back = PLAT['z0'] + 0.37
    add('timetable', plane_front(0.62, 0.92).translate(2.9, h + 1.42, back))
    for x, key in ((0.9, 'posterSakura'), (4.9, 'posterSea'), (6.55, 'posterSakura')):
        add(key, plane_front(0.5, 0.72).translate(x, h + 1.55, back))


def bicycle(x, z, ry, key):
    """A mamachari: step-through frame, basket, rear rack."""
    with at(x, 0, z, ry):
        for wx in (-0.52, 0.42):
            ring = [(wx + 0.33 * math.cos(a), 0.34 + 0.33 * math.sin(a), 0.0) for a in [i / 14 * 2 * math.pi for i in range(15)]]
            add('black', tube(ring, 0.024, 4))
            add('catMast', cyl(0.04, 0.04, 0.12, 0, -0.06, 0, 6).rotate_x(math.pi / 2).translate(wx, 0.34, 0))
        for a, b in (((0.36, 0.92), (0.0, 0.36)), ((0.0, 0.36), (-0.14, 0.86)), ((0.0, 0.36), (-0.52, 0.34)),
                     ((-0.14, 0.82), (-0.52, 0.34)), ((0.36, 0.92), (0.42, 0.34))):
            add(key, beam((a[0], a[1], 0), (b[0], b[1], 0), 0.035))
        add('catMast', box(0.04, 0.04, 0.56, 0.34, 1.0, 0))
        add('black', box(0.24, 0.06, 0.13, -0.15, 0.88, 0))
        add('fence', box(0.3, 0.22, 0.34, 0.56, 0.8, 0))
        add('catMast', box(0.34, 0.03, 0.26, -0.45, 0.7, 0))


def build_bikes():
    x0, x1, z0, z1 = SHED
    for px in (x0, x1):
        for pz in (z0, z1):
            add('metalDark', cyl(0.05, 0.05, 2.2, px, 0, pz, 8))
    add('shelterRoof', kawara(x1 - x0 + 0.4, z1 - z0 + 0.5, 0.04, 0.03, 0.22).rotate_x(0.12).translate((x0 + x1) / 2, 2.25, (z0 + z1) / 2))
    add('metalDark', box(x1 - x0 - 0.4, 0.05, 0.05, (x0 + x1) / 2, 0.3, z0 + 0.25))
    colours = ['vendRed', 'binBlue', 'fence', 'catMast', 'binGreen', 'binYellow']
    for i in range(6):
        bicycle(x0 + 0.55 + i * 0.6, (z0 + z1) / 2 + drand(-0.08, 0.08), math.pi / 2 + drand(-0.05, 0.05), colours[i])
    bicycle(-10.3, -16.9, 0.25, 'fence')


def paint_sign(name, kind):
    """Small painted faces for the shelter: a timetable and two travel posters."""
    rs = np.random.default_rng(0x51695)
    w, h = 64, 96
    img = np.empty((h, w, 3), np.float32)
    if kind == 'timetable':
        img[:] = hex_np('#fbfaf6')
        img[0:12] = hex_np('#1f6fb5')
        for r in range(18):
            y = 15 + r * 4
            img[y:y + 3, 3:9] = hex_np('#d9433b')
            for k in range(int(rs.integers(1, 5))):
                xx = 13 + k * 11 + int(rs.integers(0, 5))
                img[y:y + 3, xx:xx + 6] = hex_np('#2b2a33')
    elif kind == 'sakura':
        img[:] = hex_np('#fde8ef')
        for _ in range(40):
            cy, cx, r = rs.integers(0, h), rs.integers(0, w), rs.integers(3, 9)
            yy, xx = np.ogrid[:h, :w]
            img[(yy - cy) ** 2 + (xx - cx) ** 2 < r * r] = hex_np(['#ffb3c8', '#ff97b6', '#ffd4e0'][int(rs.integers(0, 3))])
        img[70:84] = hex_np('#ffffff')
        img[74:80, 10:54] = hex_np('#e0457d')
    else:
        for y in range(h):
            img[y] = hex_np('#8ed2f5') * (1 - y / h) + hex_np('#2f7fe0') * (y / h)
        yy, xx = np.ogrid[:h, :w]
        img[(yy - 22) ** 2 + (xx - 44) ** 2 < 64] = hex_np('#ffd84a')
        for k in range(5):
            y0 = 50 + k * 8
            for x in range(w):
                yv = int(y0 + 2 * math.sin(x / 5 + k))
                img[yv:yv + 2, x] = 1.0
    return to_image(name, img)


# --------------------------------------------------------------------------- poles, wires, catenary, lamps


def crossarm(x, z, ry):
    with at(x, 0, z, ry):
        add('pole', box(1.9, 0.12, 0.12, 0, 7.0, 0))
        for ax in (-0.8, 0, 0.8):
            add('fence', cyl(0.05, 0.07, 0.18, ax, 7.12, 0, 6))


def utility_pole(x, z, ry):
    with at(x, 0, z, ry):
        add('pole', cyl(0.12, 0.17, 7.6, 0, 0, 0, 8))
        add('metalDark', box(0.5, 0.08, 0.08, 0, 5.6, 0))
        for i in range(6):
            add('metalDark', box(0.06, 0.03, 0.22, 0, 1.8 + i * 0.4, 0))
    crossarm(x, z, ry)


def build_poles():
    lines = [
        [(11.9, -17.8), (11.9, -9.2), (11.9, 10.6)],
        [(11.9, 10.6), (2.6, 10.6), (-6.8, 10.6), (-16.2, 10.6), (-25.6, 10.6)],
    ]
    placed = set()
    for line in lines:
        for i, (x, z) in enumerate(line):
            nxt = line[min(i + 1, len(line) - 1)]
            prv = line[max(i - 1, 0)]
            ry = math.atan2(nxt[0] - prv[0], nxt[1] - prv[1])
            if (x, z) not in placed:
                placed.add((x, z))
                utility_pole(x, z, ry)
            else:
                crossarm(x, z, ry)
            if i == len(line) - 1:
                continue
            nx, nz = nxt
            span = math.hypot(nx - x, nz - z)
            d = Vector((nx - x, 0, nz - z)).normalized()
            across = Vector((d.z, 0, -d.x))
            for off in (-0.8, 0, 0.8):
                a = Vector((x, 7.2, z)) + across * off
                b = Vector((nx, 7.2, nz)) + across * off
                add('wire', sag_wire(a, b, 0.25 + span * 0.025))
            add('wire', sag_wire((x, 5.6, z), (nx, 5.6, nz), 0.35 + span * 0.03, 0.05))
    add('catMast', cyl(0.28, 0.28, 0.8, 12.25, 5.9, -9.2, 10))


def build_catenary():
    masts = [-20.5, -11, -1.5, 8.5, 20.5]
    mz, arm_y = TRACK_Z + 2.85, 5.55
    for x in masts:
        add('concreteDark', box(0.6, 0.35, 0.6, x, 0, mz))
        add('concrete', cyl(0.12, 0.17, 6.4, x, 0.3, mz, 10))
        add('catMast', box(0.06, 0.06, 0.5, x, 6.3, mz + 0.25))
        add('fence', cyl(0.05, 0.06, 0.16, x, 6.36, mz + 0.48, 6))
        add('catMast', beam((x, arm_y, mz), (x, arm_y, TRACK_Z - 0.6), 0.08))
        add('catMast', beam((x, 4.75, mz), (x, arm_y - 0.02, TRACK_Z - 0.2), 0.07))
        add('catMast', beam((x, CONTACT_Y + 0.02, TRACK_Z - 0.4), (x, arm_y - 0.05, TRACK_Z - 0.4), 0.05))
        add('fence', cyl(0.07, 0.07, 0.3, 0, -0.15, 0, 7).rotate_x(math.pi / 2).translate(x, arm_y, mz - 0.3))
    add('wire', box(CLIP_X * 2, 0.04, 0.04, 0, CONTACT_Y, TRACK_Z))
    for a, b in zip(masts, masts[1:]):
        add('wire', sag_wire((a, 6.52, mz + 0.48), (b, 6.52, mz + 0.48), 0.3, 0.03))  # feeder
        add('wire', sag_wire((a, 6.7, mz), (b, 6.7, mz), 0.22, 0.02))                # earth wire
    stops = [-CLIP_X] + masts + [CLIP_X]
    for a, b in zip(stops, stops[1:]):
        sag = 0.42 * (b - a) / 10
        add('wire', sag_wire((a, arm_y - 0.04, TRACK_Z), (b, arm_y - 0.04, TRACK_Z), sag, 0.03))
        x = a + 1.1
        while x < b - 0.6:
            t = (x - a) / (b - a)
            top = arm_y - 0.04 - sag * 4 * t * (1 - t)
            add('wire', box(0.02, top - CONTACT_Y, 0.02, x, CONTACT_Y, TRACK_Z))
            x += 1.4


def street_lamp(x, z, ry):
    with at(x, 0, z, ry):
        add('metalDark', cyl(0.07, 0.1, 4.4))
        add('metalDark', beam((0, 4.2, 0), (0, 4.55, 1.3), 0.07))
        add('metalDark', box(0.32, 0.14, 0.62, 0, 4.45, 1.45))
        add('lampLight', box(0.24, 0.04, 0.5, 0, 4.42, 1.45))
        LAMPS.append((to_world(0, 4.2, 1.45), 1.15))


# --------------------------------------------------------------------------- level crossing

CROSS_GLOWS = {'A': [], 'B': []}
ARMS = []  # (batch, pivot (web), yaw)


def crossing_pole(x, z, ry):
    with at(x, 0, z, ry):
        add('concreteDark', box(0.55, 0.15, 0.55))
        add('stripe', cyl(0.085, 0.085, 3.75, 0, 0.15, 0, 10))
        add('black', cyl(0.11, 0.09, 0.12, 0, 3.9, 0))
        for s in (-1, 1):
            add('stripe', box(1.55, 0.24, 0.05, 0, -0.12, 0).rotate_z(s * 0.58).translate(0, 3.5, 0.12))
        add('black', box(1.2, 0.12, 0.12, 0, 2.82, 0))
        # 方向指示器: the arrow points the way the train will come (it always runs east)
        add('black', box(0.7, 0.26, 0.16, 0, 2.23, 0))
        east = 1 if ry == 0 else -1
        for face in (-1, 1):
            z = face * 0.085
            for lit, key in ((1, 'arrowLit'), (-1, 'arrowDim')):
                d = lit * east
                head = prism([(0.0, -0.08), (0.12 * d, 0.0), (0.0, 0.08)], 0.02).translate(0, 0, -0.01)
                add(key, head.translate(d * 0.04, 2.36, z + face * 0.002))
                add(key, box(0.12, 0.05, 0.02, lit * east * -0.02, 2.335, z + face * 0.002))
        # 非常ボタン, the emergency button box
        add('binYellow', box(0.18, 0.26, 0.1, 0, 1.12, 0.12))
        add('vendRed', cyl(0.045, 0.045, 0.03, 0, -0.015, 0, 10).rotate_x(math.pi / 2).translate(0, 1.27, 0.18))
        for face in (-1, 1):
            for side in (-1, 1):
                lx = side * 0.47
                add('black', cyl(0.22, 0.22, 0.08, 0, -0.04, 0, 16).rotate_x(math.pi / 2).translate(lx, 2.88, face * 0.1))
                add('black', box(0.44, 0.035, 0.26, 0, 0, 0).rotate_x(face * 0.25).translate(lx, 3.1, face * 0.23))
                key = 'A' if (side < 0) == (face > 0) else 'B'
                add('lamp' + key, cyl(0.16, 0.16, 0.06, 0, -0.03, 0, 16).rotate_x(math.pi / 2).translate(lx, 2.88, face * 0.16))
                CROSS_GLOWS[key].append(to_world(lx, 2.88, face * 0.3))
        add('concrete', box(0.42, 1.1, 0.42, 0.5, 0, 0.05))
        add('black', box(0.46, 0.08, 0.46, 0.5, 1.1, 0.05))
        pivot = to_world(0.5, 0.92, 0.3)
    with batch_scope() as arm:
        add('stripe', box(3.25, 0.09, 0.09, 1.75, -0.045, 0))
        add('black', box(0.5, 0.2, 0.14, -0.2, -0.1, 0))
        add('black', box(0.16, 0.16, 0.16, 0, -0.08, -0.02))
    ARMS.append((arm.batch, pivot, ry))


# --------------------------------------------------------------------------- the train

DOORS = []  # (Geo in train space, slide direction)


def car(lamp, platform_side, car_ry):
    L, hw, y0, y1, r = CAR_L, 1.25, 0.5, 3.2, 0.5
    k = 0.55 / (y1 - y0)
    xf = lambda y: L / 2 - k * (y - y0)
    tilt = math.atan(k)

    shape = [(-hw + 0.06, y0), (hw - 0.06, y0), (hw, y0 + 0.08), (hw, y1 - r)]
    for i in range(1, 5):
        a = (math.pi / 2) * i / 4
        shape.append((hw - r + r * math.cos(a), y1 - r + r * math.sin(a)))
    for i in range(0, 5):
        a = math.pi / 2 + (math.pi / 2) * i / 4
        shape.append((-hw + r + r * math.cos(a), y1 - r + r * math.sin(a)))
    shape.append((-hw, y0 + 0.08))
    body = prism(shape, L).rotate_y(math.pi / 2).translate(-L / 2, 0, 0)
    for p in body.v:
        if p.x > L / 2 - 1e-3:
            p.x = xf(p.y)
    add('tWhite', body)

    def front(key, w, h, y, z, depth=0.05, out=0.02):
        add(key, box(depth, h, w, 0, -h / 2, 0).rotate_z(tilt).translate(xf(y) + out, y, z))

    front('tBlack', 2.2, 1.2, 2.42, 0, 0.05, 0.015)
    for z in (-0.52, 0.52):
        front('tGlass', 0.92, 0.92, 2.4, z, 0.05, 0.035)
    front('tDest', 0.95, 0.24, 2.98, 0, 0.03, 0.05)
    front('tPink', 2.48, 0.3, 1.62, 0, 0.05, 0.01)
    front('tPinkDark', 2.48, 0.07, 1.4, 0, 0.05, 0.01)
    for z in (-0.52, 0.52):
        add('tBlack', beam((xf(1.98) + 0.07, 1.98, z - 0.3), (xf(2.6) + 0.07, 2.6, z + 0.05), 0.03))
    front('tGrey', 0.5, 0.15, 3.2, -0.62, 0.02, 0.03)  # ワンマン plate
    for z in (-0.8, 0.8):
        front('tHead' if lamp == 'head' else 'tLampOff', 0.34, 0.16, 1.12, z, 0.06, 0.03)
    for z in (-0.47, 0.47):
        front('tTail' if lamp == 'tail' else 'tLampOff', 0.2, 0.14, 1.12, z, 0.06, 0.03)
    add('tDark', box(0.35, 0.5, 2.25, L / 2 - 0.2, 0.02, 0))
    add('tGrey', box(0.4, 0.14, 0.24, L / 2 + 0.05, 0.25, 0))

    for side in (-1, 1):
        zs = side * (hw + 0.012)
        add('tPink', box(L - 0.75, 0.3, 0.03, -0.2, 1.47, zs))
        add('tPinkDark', box(L - 0.75, 0.07, 0.03, -0.2, 1.33, zs))
        for a, b in ((-L / 2 + 0.45, -3.15), (-1.55, 1.55), (3.15, L / 2 - 1.25)):
            add('tGlass', box(b - a, 0.9, 0.035, (a + b) / 2, 1.97, side * (hw + 0.015)))
        add('tGlass', box(0.5, 0.8, 0.035, L / 2 - 0.82, 2.02, side * (hw + 0.015)))
        add('tDest', box(0.62, 0.18, 0.02, -0.4, 2.62, side * (hw + 0.02)))
        for dx in (-2.35, 2.35):
            add('tDoorway', box(1.32, 2.2, 0.02, dx, 0.6, side * (hw + 0.006)))
            for leaf in (-1, 1):
                g = box(0.64, 2.16, 0.04, dx + leaf * 0.33, 0.62, side * (hw + 0.03))
                window = box(0.42, 0.75, 0.01, dx + leaf * 0.33, 1.75, side * (hw + 0.055))
                if side == platform_side:
                    DOORS.append((g.apply(XF.copy()), window.apply(XF.copy()), (XF.to_3x3() @ Vector((leaf, 0, 0)))))
                else:
                    add('tDoor', g)
                    add('tGlass', window)

    for ax in (-2.4, 2.2):
        add('tGrey', box(1.7, 0.32, 1.4, ax, y1 - 0.06, 0))
    add('tGrey', box(L - 3, 0.08, 0.5, -0.3, y1 - 0.02, 0))
    add('tDark', box(L - 2.2, 0.38, 2.1, 0, 0.13, 0))
    for bx in (-3.05, 3.05):
        add('tDark', box(2.3, 0.28, 2.25, bx, 0.18, 0))
        for wx in (-0.75, 0.75):
            for wz in (-0.55, 0.55):
                add('tWheel', cyl(0.3, 0.3, 0.12, 0, -0.06, 0, 12).rotate_x(math.pi / 2).translate(bx + wx, 0.3, wz))
    add('tDark', box(0.26, 2.3, 1.55, -L / 2 - 0.13, 0.65, 0))


def pantograph(px):
    yb = 3.2
    top = CONTACT_Y - RAIL_Y - 0.03
    add('tGrey', box(1.3, 0.1, 1.1, px, yb + 0.05, 0))
    for ix in (-0.5, 0.5):
        for iz in (-0.4, 0.4):
            add('tSilver', cyl(0.05, 0.06, 0.12, px + ix, yb - 0.05, iz, 6))
    for z in (-0.25, 0.25):
        add('tSilver', beam((px - 0.55, yb + 0.18, z), (px + 0.75, yb + 0.48, z * 0.4), 0.05))
    add('tSilver', beam((px + 0.75, yb + 0.48, 0), (px - 0.25, top - 0.04, 0), 0.05))
    add('tSilver', box(0.12, 0.05, 1.45, px - 0.25, top - 0.05, 0))
    for z in (-1, 1):
        add('tSilver', beam((px - 0.25, top - 0.03, z * 0.72), (px - 0.25, top - 0.2, z * 0.92), 0.04))


# --------------------------------------------------------------------------- Blender objects

SCENE = None
COLLECTIONS = {}


def collection(name, parent=None):
    if name in COLLECTIONS:
        return COLLECTIONS[name]
    c = bpy.data.collections.new(name)
    (parent or SCENE.collection).children.link(c)
    COLLECTIONS[name] = c
    return c


def make_mesh_object(name, key, part, coll, parent=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([to_blender(v) for v in part.v], [], part.f)
    mesh.polygons.foreach_set('use_smooth', part.smooth)
    if any(part.uvs):
        layer = mesh.uv_layers.new(name='UVMap')
        coords = []
        for poly, uv in zip(mesh.polygons, part.uvs):
            coords.extend(uv if uv else [(0.0, 0.0)] * poly.loop_total)
        layer.data.foreach_set('uv', [c for p in coords for c in p])
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    mesh.materials.append(material(key))
    if Q['detail'] and key in ROUNDED:
        sub = obj.modifiers.new('Ultra smooth', 'SUBSURF')
        sub.levels, sub.render_levels = 1, 2
    elif Q['detail'] and key in BEVELLED:
        bev = obj.modifiers.new('Ultra bevel', 'BEVEL')
        bev.width = 0.025
        bev.segments = 2
        bev.limit_method = 'ANGLE'
        bev.angle_limit = math.radians(40)
    thickness = SPEC[key][1]
    if thickness:
        mesh.materials.append(ink_material(SPEC[key][2].get('clip', False)))
        mod = obj.modifiers.new('Ink outline', 'SOLIDIFY')
        mod.thickness = thickness
        mod.offset = 1.0
        mod.use_flip_normals = True
        mod.use_rim = False
        mod.material_offset = 1
    return obj


def bake(batch, coll, prefix='', parent=None):
    objs = []
    for key, part in batch.items():
        objs.append(make_mesh_object(prefix + key, key, part, coll, parent))
    return objs


def text_object(body, height, pos, facing, mat_key, opt, coll):
    """A sign's lettering. Fonts differ in how big a glyph is at a given size, so the
    object is scaled to `height` once it has been measured (see fit_text)."""
    curve = bpy.data.curves.new('sign', 'FONT')
    curve.body = body
    if FONT is not None:
        curve.font = FONT
    curve.size = 1.0
    curve.align_x = opt.get('align', 'CENTER')
    curve.align_y = 'CENTER'
    curve.space_character = opt.get('spacing', 1.0)
    curve.offset = 0.0 if any('\u3400' <= ch <= '\u9fff' for ch in body) else 0.012
    obj = bpy.data.objects.new('sign_' + body.strip()[:6], curve)
    coll.objects.link(obj)
    obj.location = to_blender(pos)
    if facing == '+z':
        obj.rotation_euler = (math.pi / 2, 0, 0)
    elif facing == '-z':
        obj.rotation_euler = (math.pi / 2, 0, math.pi)
    elif facing == '+x':
        obj.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    elif facing == '-x':
        obj.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
    elif facing == 'up':
        obj.rotation_euler = (0, 0, opt.get('yaw', 0.0))
    obj['height'] = height
    obj['stretch'] = opt.get('stretch', 1.0)
    obj.data.materials.append(material(mat_key))
    return obj


def fit_text(objs):
    SCENE.view_layers[0].update()
    for obj in objs:
        k = obj['height'] / max(obj.dimensions.y, 1e-4)
        obj.scale = (k, k * obj['stretch'], k)


def find_cjk_font():
    candidates = []
    try:
        fonts = bpy.utils.system_resource('DATAFILES', path='fonts')
        candidates.append(os.path.join(fonts, 'Noto Sans CJK Regular.woff2'))
    except Exception:
        pass
    candidates += [
        'C:/Windows/Fonts/YuGothB.ttc', 'C:/Windows/Fonts/meiryob.ttc', 'C:/Windows/Fonts/msgothic.ttc',
        '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                font = bpy.data.fonts.load(path, check_existing=True)
                font.pack()
                return font
            except Exception:
                continue
    print("Harukaze: no Japanese font found; signs will use Blender's default font")
    return None


FONT = None


# --------------------------------------------------------------------------- petals (geometry nodes)


def build_petals(blossoms, coll):
    """460 petals shed from the blossom crowns. Each one falls with a period of 32/k
    seconds (k = 2..4) and sways on whole-cycle sines, so the loop is seamless."""
    # measure what the scatter will see: the evaluated crowns, outline shell included
    layer = SCENE.view_layers[0]
    layer.update()
    depsgraph = layer.depsgraph
    area = 0.0
    for o in blossoms:
        area += sum(p.area for p in o.evaluated_get(depsgraph).data.polygons)
    ng = bpy.data.node_groups.new('Sakura petals', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, l = ng.nodes, ng.links

    def math_node(op, a=None, b=None, c=None):
        m = n.new('ShaderNodeMath')
        m.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                l.new(v, m.inputs[i])
        return m.outputs[0]

    def random_float(lo, hi, seed):
        r = n.new('FunctionNodeRandomValue')
        r.data_type = 'FLOAT'
        find_socket(r.inputs, 'Min', 'VALUE').default_value = lo
        find_socket(r.inputs, 'Max', 'VALUE').default_value = hi
        find_socket(r.inputs, 'Seed', 'INT').default_value = seed
        return find_socket(r.outputs, 'Value', 'VALUE')

    join = n.new('GeometryNodeJoinGeometry')
    for o in blossoms:
        info = n.new('GeometryNodeObjectInfo')
        info.transform_space = 'RELATIVE'
        info.inputs['Object'].default_value = o
        l.new(info.outputs['Geometry'], join.inputs['Geometry'])
    scatter = n.new('GeometryNodeDistributePointsOnFaces')
    scatter.inputs['Density'].default_value = Q['petals'] / max(area, 1.0)
    scatter.inputs['Seed'].default_value = 7
    l.new(join.outputs[0], scatter.inputs['Mesh'])

    pos = n.new('GeometryNodeInputPosition')
    sep = n.new('ShaderNodeSeparateXYZ')
    l.new(pos.outputs[0], sep.inputs[0])
    time = n.new('GeometryNodeInputSceneTime')
    tc = math_node('MODULO', time.outputs['Seconds'], CYCLE)
    cycles = math_node('DIVIDE', tc, CYCLE)
    k = math_node('FLOOR', random_float(2.0, 4.999, 1))
    phase = random_float(0.0, 1.0, 2)
    sway = random_float(0.15, 0.55, 3)
    frac = math_node('FRACT', math_node('ADD', math_node('MULTIPLY', cycles, k), phase))
    height = math_node('MAXIMUM', sep.outputs['Z'], 0.2)
    fallen = math_node('MULTIPLY', frac, height)
    two_pi = 2 * math.pi
    wave1 = math_node('SINE', math_node('ADD', math_node('MULTIPLY', cycles, two_pi * 3), math_node('MULTIPLY', phase, 6.283)))
    wave2 = math_node('COSINE', math_node('ADD', math_node('MULTIPLY', cycles, two_pi * 2), math_node('MULTIPLY', phase, 9.0)))
    x = math_node('ADD', math_node('ADD', sep.outputs['X'], math_node('MULTIPLY', fallen, 1.3)), math_node('MULTIPLY', wave1, sway))
    y = math_node('ADD', math_node('SUBTRACT', sep.outputs['Y'], math_node('MULTIPLY', fallen, 0.35)), math_node('MULTIPLY', wave2, sway))
    z = math_node('MAXIMUM', math_node('SUBTRACT', sep.outputs['Z'], fallen), 0.03)
    combine = n.new('ShaderNodeCombineXYZ')
    l.new(x, combine.inputs['X'])
    l.new(y, combine.inputs['Y'])
    l.new(z, combine.inputs['Z'])
    set_pos = n.new('GeometryNodeSetPosition')
    l.new(scatter.outputs['Points'], set_pos.inputs['Geometry'])
    l.new(combine.outputs[0], set_pos.inputs['Position'])
    # petals blown past the edge of the block are dropped rather than left hanging in the air
    now = n.new('GeometryNodeInputPosition')
    now_sep = n.new('ShaderNodeSeparateXYZ')
    l.new(now.outputs[0], now_sep.inputs[0])
    off_x = math_node('GREATER_THAN', math_node('ABSOLUTE', now_sep.outputs['X']), W / 2)
    off_y = math_node('GREATER_THAN', math_node('ABSOLUTE', now_sep.outputs['Y']), D / 2)
    cull = n.new('GeometryNodeDeleteGeometry')
    l.new(set_pos.outputs['Geometry'], cull.inputs['Geometry'])
    l.new(math_node('MAXIMUM', off_x, off_y), cull.inputs['Selection'])

    spin = n.new('ShaderNodeCombineXYZ')
    l.new(math_node('ADD', math_node('MULTIPLY', cycles, two_pi * 5), math_node('MULTIPLY', phase, 6.0)), spin.inputs['X'])
    l.new(math_node('MULTIPLY', cycles, two_pi * 3), spin.inputs['Y'])
    l.new(math_node('MULTIPLY', phase, 12.0), spin.inputs['Z'])

    petal = n.new('GeometryNodeMeshCircle')
    petal.fill_type = 'NGON'
    petal.inputs['Vertices'].default_value = 6
    petal.inputs['Radius'].default_value = 0.1
    squash = n.new('GeometryNodeTransform')
    find_socket(squash.inputs, 'Scale').default_value = (1.0, 0.62, 1.0)
    l.new(petal.outputs['Mesh'], squash.inputs['Geometry'])
    paint = n.new('GeometryNodeSetMaterial')
    paint.inputs['Material'].default_value = PETAL_MATERIAL
    l.new(squash.outputs['Geometry'], paint.inputs['Geometry'])

    inst = n.new('GeometryNodeInstanceOnPoints')
    l.new(cull.outputs['Geometry'], inst.inputs['Points'])
    l.new(paint.outputs['Geometry'], inst.inputs['Instance'])
    l.new(spin.outputs[0], inst.inputs['Rotation'])
    l.new(random_float(0.9, 1.6, 4), inst.inputs['Scale'])
    out = n.new('NodeGroupOutput')
    l.new(inst.outputs['Instances'], out.inputs['Geometry'])

    mesh = bpy.data.meshes.new('Sakura petals')
    obj = bpy.data.objects.new('Sakura petals', mesh)
    coll.objects.link(obj)
    mod = obj.modifiers.new('Petals', 'NODES')
    mod.node_group = ng
    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = False
    return obj


PETAL_MATERIAL = None
SHOTS = []


def tuft_source(coll):
    """Three leaning grass blades; normals point up so tufts shade like the meadow."""
    verts, faces = [], []
    for b in range(3):
        a = b / 3 * 2 * math.pi + 0.4
        ca, sa = math.cos(a), math.sin(a)
        base = len(verts)
        verts += [(-sa * 0.028, ca * 0.028, 0.0), (sa * 0.028, -ca * 0.028, 0.0), (ca * 0.08, sa * 0.08, 0.26 - b * 0.04)]
        faces.append((base, base + 1, base + 2))
    mesh = bpy.data.meshes.new('Grass tuft')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    try:
        mesh.normals_split_custom_set([(0.0, 0.0, 1.0)] * len(mesh.loops))
    except Exception:
        pass
    m = new_material('tuft')
    n, l = m.node_tree.nodes, m.node_tree.links
    out = n.new('ShaderNodeOutputMaterial')
    toon = n.new('ShaderNodeGroup')
    toon.node_tree = node_group_toon()
    attr = n.new('ShaderNodeAttribute')
    attr.attribute_type = 'INSTANCER'
    attr.attribute_name = 'tone'
    ramp = n.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    stops = [(0.0, '#5ea947'), (0.35, '#6fbd4e'), (0.7, '#86cf5c'), (1.0, '#9ad96d')]
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for el, (pos, col) in zip(cr.elements, stops):
        el.position = pos
        el.color = lin(col)
    l.new(attr.outputs['Fac'], ramp.inputs[0])
    l.new(ramp.outputs['Color'], toon.inputs['Color'])
    l.new(toon.outputs[0], out.inputs['Surface'])
    m.use_backface_culling = False
    mesh.materials.append(m)
    obj = bpy.data.objects.new('Grass tuft (source)', mesh)
    coll.objects.link(obj)
    obj.location = (0, 0, -60)
    obj.hide_render = True
    return obj


def build_meadow(coll, ground):
    """Ultra: grass tufts where the painted meadow is green and petals lying on the grass
    where they were painted under the trees, both read from the packed meadow mask."""
    source = tuft_source(coll)
    ng = bpy.data.node_groups.new('Meadow', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, l = ng.nodes, ng.links

    def math_node(op, a, b=None):
        m = n.new('ShaderNodeMath')
        m.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                l.new(v, m.inputs[i])
        return m.outputs[0]

    def random_float(lo, hi, seed):
        r = n.new('FunctionNodeRandomValue')
        r.data_type = 'FLOAT'
        find_socket(r.inputs, 'Min', 'VALUE').default_value = lo
        find_socket(r.inputs, 'Max', 'VALUE').default_value = hi
        find_socket(r.inputs, 'Seed', 'INT').default_value = seed
        return find_socket(r.outputs, 'Value', 'VALUE')

    ground_info = n.new('GeometryNodeObjectInfo')
    ground_info.transform_space = 'RELATIVE'
    ground_info.inputs['Object'].default_value = ground
    source_info = n.new('GeometryNodeObjectInfo')
    source_info.transform_space = 'ORIGINAL'
    source_info.inputs['Object'].default_value = source
    join = n.new('GeometryNodeJoinGeometry')

    def scatter(density, seed, channel, instance, scale, lift, tone_name=None):
        dist = n.new('GeometryNodeDistributePointsOnFaces')
        dist.inputs['Density'].default_value = density
        dist.inputs['Seed'].default_value = seed
        l.new(ground_info.outputs['Geometry'], dist.inputs['Mesh'])
        sep = n.new('ShaderNodeSeparateXYZ')
        l.new(n.new('GeometryNodeInputPosition').outputs[0], sep.inputs[0])
        uv = n.new('ShaderNodeCombineXYZ')
        l.new(math_node('ADD', math_node('DIVIDE', sep.outputs['X'], W), 0.5), uv.inputs['X'])
        l.new(math_node('ADD', math_node('DIVIDE', sep.outputs['Y'], D), 0.5), uv.inputs['Y'])
        tex = n.new('GeometryNodeImageTexture')
        tex.interpolation = 'Closest'
        tex.inputs['Image'].default_value = IMAGES['meadow']
        l.new(uv.outputs[0], tex.inputs['Vector'])
        split = n.new('FunctionNodeSeparateColor')
        l.new(tex.outputs['Color'], split.inputs['Color'])
        cull = n.new('GeometryNodeDeleteGeometry')
        l.new(dist.outputs['Points'], cull.inputs['Geometry'])
        l.new(math_node('LESS_THAN', split.outputs[channel], 0.5), cull.inputs['Selection'])
        lifted = n.new('GeometryNodeSetPosition')
        l.new(cull.outputs['Geometry'], lifted.inputs['Geometry'])
        find_socket(lifted.inputs, 'Offset').default_value = (0.0, 0.0, lift)
        turn = n.new('ShaderNodeCombineXYZ')
        l.new(random_float(0.0, 2 * math.pi, seed + 1), turn.inputs['Z'])
        inst = n.new('GeometryNodeInstanceOnPoints')
        l.new(lifted.outputs['Geometry'], inst.inputs['Points'])
        l.new(instance, inst.inputs['Instance'])
        l.new(turn.outputs[0], inst.inputs['Rotation'])
        l.new(random_float(scale[0], scale[1], seed + 2), inst.inputs['Scale'])
        result = inst.outputs['Instances']
        if tone_name:
            store = n.new('GeometryNodeStoreNamedAttribute')
            store.data_type = 'FLOAT'
            store.domain = 'INSTANCE'
            l.new(result, store.inputs['Geometry'])
            store.inputs['Name'].default_value = tone_name
            l.new(random_float(0.0, 1.0, seed + 3), find_socket(store.inputs, 'Value', 'VALUE'))
            result = store.outputs['Geometry']
        l.new(result, join.inputs['Geometry'])

    scatter(11.0, 31, 'Red', source_info.outputs['Geometry'], (0.7, 1.45), 0.0, 'tone')
    petal = n.new('GeometryNodeMeshCircle')
    petal.fill_type = 'NGON'
    petal.inputs['Vertices'].default_value = 6
    petal.inputs['Radius'].default_value = 0.09
    squash = n.new('GeometryNodeTransform')
    find_socket(squash.inputs, 'Scale').default_value = (1.0, 0.62, 1.0)
    l.new(petal.outputs['Mesh'], squash.inputs['Geometry'])
    paint = n.new('GeometryNodeSetMaterial')
    paint.inputs['Material'].default_value = PETAL_MATERIAL
    l.new(squash.outputs['Geometry'], paint.inputs['Geometry'])
    scatter(26.0, 47, 'Green', paint.outputs['Geometry'], (0.8, 1.3), 0.012)
    out = n.new('NodeGroupOutput')
    l.new(join.outputs[0], out.inputs['Geometry'])

    obj = bpy.data.objects.new('Meadow', bpy.data.meshes.new('Meadow'))
    coll.objects.link(obj)
    obj.modifiers.new('Meadow', 'NODES').node_group = ng
    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = False
    return obj


def build_compositor(scene, strength):
    """Bloom on what glows: the threshold sits above the brightest day colours, so it
    mostly blooms the lamps, windows and lights at night."""
    if hasattr(scene, 'compositing_node_group'):  # Blender 5: compositing is a node group
        ng = bpy.data.node_groups.new('Harukaze glow', 'CompositorNodeTree')
        ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        n, l = ng.nodes, ng.links
        layers = n.new('CompositorNodeRLayers')
        layers.scene = scene
        glare = n.new('CompositorNodeGlare')
        glare.inputs['Type'].default_value = 'Bloom'
        glare.inputs['Quality'].default_value = 'High'
        glare.inputs['Threshold'].default_value = 1.0
        glare.inputs['Strength'].default_value = strength
        glare.inputs['Size'].default_value = 0.6
        out = n.new('NodeGroupOutput')
        l.new(layers.outputs['Image'], glare.inputs['Image'])
        l.new(glare.outputs['Image'], out.inputs[0])
        scene.compositing_node_group = ng
    else:  # Blender 4.x
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        layers = tree.nodes.new('CompositorNodeRLayers')
        glare = tree.nodes.new('CompositorNodeGlare')
        glare.glare_type = 'BLOOM'
        glare.quality = 'HIGH'
        glare.threshold = 1.0
        glare.size = 8
        glare.mix = strength - 1.0
        comp = tree.nodes.new('CompositorNodeComposite')
        tree.links.new(layers.outputs['Image'], glare.inputs['Image'])
        tree.links.new(glare.outputs['Image'], comp.inputs['Image'])


# --------------------------------------------------------------------------- timetable


def train_x(t):
    if t < T_ARR0:
        return X_START
    if t < T_ARR1:
        u = (t - T_ARR0) / (T_ARR1 - T_ARR0)
        return X_START + (X_STOP - X_START) * (1 - (1 - u) ** 2)
    if t < T_DEP0:
        return X_STOP
    if t < T_DEP1:
        u = (t - T_DEP0) / (T_DEP1 - T_DEP0)
        return X_STOP + (X_END - X_STOP) * u * u
    return X_END


T_CLEAR = next(T_DEP0 + i * 0.01 for i in range(800) if train_x(T_DEP0 + i * 0.01) - TRAIN_HALF > ROAD_X1 + 0.5)
RING_START, RING_END = T_DEP0 - 3.2, T_CLEAR + 0.35
ARM_UP = math.radians(82)


def crossing_state(t):
    ringing = RING_START < t < RING_END
    down = 0.0
    if RING_START + 1.0 < t < RING_END:
        down = smoothstep(t, RING_START + 1.0, RING_START + 3.0)
    elif t >= RING_END:
        down = 1 - smoothstep(t, RING_END, RING_END + 2.6)
    return ringing, down


def door_open(t):
    if t < T_ARR1 + 0.6 or t > T_DEP0 - 1.6:
        return 0.0
    return min(smoothstep(t, T_ARR1 + 0.6, T_ARR1 + 1.6), 1 - smoothstep(t, T_DEP0 - 2.6, T_DEP0 - 1.6))


def fcurves_of(idblock):
    """An ID's F-curves, from slotted actions (4.4+) or the older flat list."""
    ad = idblock.animation_data
    if ad is None or ad.action is None:
        return []
    try:
        from bpy_extras import anim_utils
        bag = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        if bag is not None:
            return list(bag.fcurves)
    except (ImportError, AttributeError):
        pass
    return list(ad.action.fcurves)


def set_interpolation(idblock, interpolation):
    for fc in fcurves_of(idblock):
        for kp in fc.keyframe_points:
            kp.interpolation = interpolation


def animate(train, doors, arms, beam_owner):
    """Key one 32 s cycle frame by frame from the timetable; the extra last frame wraps
    back to t = 0 so the loop closes."""
    for f in range(1, FRAMES + 2):
        t = ((f - 1) / FPS) % CYCLE
        x = train_x(t)
        train.location.x = x
        train.keyframe_insert('location', index=0, frame=f)
        nose = x + TRAIN_HALF
        beam_owner['beam'] = smoothstep(nose, -CLIP_X - 2, -CLIP_X + 2) * (1 - smoothstep(nose, CLIP_X + 1, CLIP_X + 5))
        beam_owner.keyframe_insert('["beam"]', frame=f)
        opening = door_open(t)
        for obj, slide in doors:
            obj.location = Vector(to_blender(slide * opening * 0.62))
            obj.keyframe_insert('location', frame=f)
        _, down = crossing_state(t)
        for obj in arms:
            obj.rotation_euler[1] = -ARM_UP * (1 - down)
            obj.keyframe_insert('rotation_euler', index=1, frame=f)
    for idblock in [train] + [d for d, _ in doors] + arms:
        set_interpolation(idblock, 'LINEAR')

    # crossing lamps: the two sides alternate twice a second while the bell rings
    for which, nodes in BLINKERS.items():
        prev = None
        for f in range(1, FRAMES + 1):
            t = (f - 1) / FPS
            ringing, _ = crossing_state(t)
            if which == 'R':
                on = 1.0 if ringing else 0.0
            else:
                on = 1.0 if ringing and int(t * 2) % 2 == (0 if which == 'A' else 1) else 0.0
            if on != prev:
                for node in nodes:
                    node.outputs[0].default_value = on
                    node.outputs[0].keyframe_insert('default_value', frame=f)
                prev = on
        for node in nodes:
            set_interpolation(node.id_data, 'CONSTANT')


# --------------------------------------------------------------------------- world, lights, camera


def build_world():
    world = bpy.data.worlds.new('Harukaze sky')
    SCENE.world = world
    use_nodes(world)
    n, l = world.node_tree.nodes, world.node_tree.links
    n.clear()
    out = n.new('ShaderNodeOutputWorld')
    coords = n.new('ShaderNodeTexCoord')
    night = n.new('ShaderNodeGroup')
    night.node_tree = node_group_night()

    def ramp(stops):
        r = n.new('ShaderNodeValToRGB')
        cr = r.color_ramp
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for el, (pos, col) in zip(cr.elements, stops):
            el.position = pos
            el.color = lin(col)
        return r

    def mix(a, b, fac):
        m = n.new('ShaderNodeMix')
        m.data_type = 'RGBA'
        l.new(fac, find_socket(m.inputs, 'Factor', 'VALUE'))
        l.new(a, find_socket(m.inputs, 'A', 'RGBA'))
        l.new(b, find_socket(m.inputs, 'B', 'RGBA'))
        return find_socket(m.outputs, 'Result', 'RGBA')

    # the backdrop: a screen-space pastel gradient, as in the web version
    sep = n.new('ShaderNodeSeparateXYZ')
    l.new(coords.outputs['Window'], sep.inputs[0])
    day_sky = ramp([(0.0, '#fff3dc'), (0.25, '#ffe4ef'), (0.55, '#cfe8ff'), (1.0, '#8ccfff')])
    night_sky = ramp([(0.0, '#563c70'), (0.2, '#352c63'), (0.5, '#18204e'), (1.0, '#060a24')])
    l.new(sep.outputs['Y'], day_sky.inputs[0])
    l.new(sep.outputs['Y'], night_sky.inputs[0])
    backdrop = mix(day_sky.outputs['Color'], night_sky.outputs['Color'], night.outputs[0])

    # stars: a voronoi field over every view direction, so they sit at infinity and turn
    # with the orbit (the camera looks down, so they surround the floating block); night
    # only, fading towards the bottom of the frame
    def math(op, a, b=None, c=None):
        m = n.new('ShaderNodeMath')
        m.operation = op
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                l.new(x, m.inputs[i])
        return m.outputs[0]

    cells = n.new('ShaderNodeTexVoronoi')
    cells.voronoi_dimensions = '3D'
    cells.feature = 'F1'
    cells.inputs['Scale'].default_value = 150.0
    l.new(coords.outputs['Generated'], cells.inputs['Vector'])
    pick = n.new('ShaderNodeTexWhiteNoise')
    pick.noise_dimensions = '3D'
    l.new(cells.outputs['Position'], pick.inputs['Vector'])
    core = math('LESS_THAN', cells.outputs['Distance'], 0.075)
    lit = math('GREATER_THAN', pick.outputs['Value'], 0.88)
    shine = math('MULTIPLY_ADD', pick.outputs['Value'], 5.0, -3.9)  # 0.5 .. 1.1 across the lit cells
    fade = math('MINIMUM', math('MAXIMUM', math('MULTIPLY_ADD', sep.outputs['Y'], 1.8, -0.35), 0.0), 1.0)
    star = math('MULTIPLY', math('MULTIPLY', math('MULTIPLY', core, lit), shine), math('MULTIPLY', fade, night.outputs[0]))
    twinkle = n.new('ShaderNodeVectorMath')
    twinkle.operation = 'ADD'
    l.new(backdrop, twinkle.inputs[0])
    l.new(math('MULTIPLY', star, 2.2), twinkle.inputs[1])
    backdrop = twinkle.outputs[0]

    # the light: a hemisphere, sky above and meadow below
    dirsep = n.new('ShaderNodeSeparateXYZ')
    l.new(coords.outputs['Generated'], dirsep.inputs[0])
    up = n.new('ShaderNodeMapRange')
    up.inputs['From Min'].default_value = -0.4
    up.inputs['From Max'].default_value = 1.0
    l.new(dirsep.outputs['Z'], up.inputs['Value'])
    day_amb = ramp([(0.0, '#7d9a5c'), (1.0, '#b9d6f2')])
    night_amb = ramp([(0.0, '#11131f'), (1.0, '#24305e')])
    l.new(up.outputs[0], day_amb.inputs[0])
    l.new(up.outputs[0], night_amb.inputs[0])
    ambient = mix(day_amb.outputs['Color'], night_amb.outputs['Color'], night.outputs[0])

    path = n.new('ShaderNodeLightPath')
    bg = n.new('ShaderNodeBackground')
    l.new(mix(ambient, backdrop, path.outputs['Is Camera Ray']), bg.inputs['Color'])
    l.new(bg.outputs[0], out.inputs['Surface'])


def build_lights(coll, train):
    sun_data = bpy.data.lights.new('Sun', 'SUN')
    sun_data.angle = math.radians(1.5)
    sun = bpy.data.objects.new('Sun', sun_data)
    coll.objects.link(sun)
    # from the south-west, about 37 degrees up: long enough shadows to read under the trees
    sun.rotation_euler = Vector(to_blender((-30, 30, 26))).to_track_quat('Z', 'Y').to_euler()
    drive(sun_data.driver_add('energy'), '3.4 - 2.9 * n')
    for i, (day, night) in enumerate(zip((1.0, 0.95, 0.88), (0.6, 0.7, 1.0))):
        drive(sun_data.driver_add('color', i), f'{day} + ({night - day}) * n')

    def point(name, pos, color, expression, radius=0.25, shadow=True, cutoff=None):
        data = bpy.data.lights.new(name, 'POINT')
        data.color = color
        data.shadow_soft_size = radius
        data.use_shadow = shadow
        if hasattr(data, 'use_soft_falloff'):
            data.use_soft_falloff = True
        if cutoff and hasattr(data, 'use_custom_distance'):
            data.use_custom_distance = True
            data.cutoff_distance = cutoff
        drive(data.driver_add('energy'), expression)
        obj = bpy.data.objects.new(name, data)
        coll.objects.link(obj)
        obj.location = to_blender(pos)
        return obj

    # warm sodium-ish pools under the platform, plaza and street lamps
    for i, (pos, k) in enumerate(LAMPS):
        point(f'Lamp {i + 1}', pos - Vector((0, 0.25, 0)), (1.0, 0.66, 0.36), f'{200 * k} * n')
    # yozakura: every cherry lit from just under its crown, so the blossom glows at night
    for i, (x, z, s) in enumerate(CHERRIES):
        y = hill_height(x, z) - 0.15 + 2.1 * s + 0.35
        point(f'Yozakura {i + 1}', Vector((x, y, z)), (1.0, 0.8, 0.88), f'{75 * s} * n', 0.6, False, 3.6 * s)
    # lamplight spilling out of the station's windows onto the plaza and platform
    point('Station windows', Vector((-8.0, 1.8, -12.5)), (1.0, 0.75, 0.45), '60 * n', 1.5, False, 7.5)

    head = bpy.data.lights.new('Headlight', 'SPOT')
    head.spot_size = math.radians(70)
    head.spot_blend = 0.6
    head.color = (1.0, 0.95, 0.82)
    head.shadow_soft_size = 0.2
    obj = bpy.data.objects.new('Headlight', head)
    coll.objects.link(obj)
    obj.parent = train
    obj.location = to_blender((CAR_OFF + CAR_L / 2 + 0.3, 1.2, 0))
    obj.rotation_euler = (0, math.radians(-90 + 8), 0)
    drive(head.driver_add('energy'), '2500 * n * beam', [('beam', train, '["beam"]')])


def build_glows(coll, train):
    lamp_mat = glow_material('glow_lamp', '#ffd590', 6.0)
    glows = []
    for pos, k in LAMPS:
        glows.append(('lamp', pos, 0.55 * k, lamp_mat, None))
    for which in ('A', 'B'):
        mat = glow_material(f'glow_cross_{which}', '#ff3b3b', 8.0, keyed=True)
        level = mat.node_tree.nodes['level']
        BLINKERS[which].append(level)
        for p in CROSS_GLOWS[which]:
            glows.append(('cross', p, 0.38, mat, None))
    head_mat = glow_material('glow_head', '#fff3d1', 6.0, clip=True)
    tail_mat = glow_material('glow_tail', '#ff4545', 4.0, clip=True)
    head_x = CAR_OFF + CAR_L / 2 + 0.15
    for z in (-0.8, 0.8):
        glows.append(('head', Vector((head_x, 1.12, z)), 0.42, head_mat, train))
    for z in (-0.47, 0.47):
        glows.append(('tail', Vector((-head_x, 1.12, z)), 0.3, tail_mat, train))
    verts, faces = icosphere(1.0, 2)
    for name, pos, r, mat, parent in glows:
        mesh = bpy.data.meshes.new('glow')
        mesh.from_pydata([to_blender(v * r) for v in verts], [], faces)
        mesh.polygons.foreach_set('use_smooth', [True] * len(faces))
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(f'glow_{name}', mesh)
        coll.objects.link(obj)
        obj.location = to_blender(pos)
        if parent is not None:
            obj.parent = parent
        if hasattr(obj, 'visible_shadow'):
            obj.visible_shadow = False


ORBIT_TARGET = (-1.0, -1.2, -1.0)        # web frame; the block's visual centre
ORBIT_VIEW = (0.46, 0.53, 0.71)           # from the target towards the camera, ~32 deg up
ORBIT_EASE = 0.45                         # radians of lead/lag around the hero view
FOV_Y = math.radians(30)


def orbit_yaw(f):
    """One eased turn per loop: 55% speed through the hero view (frame HERO_FRAME, yaw 0),
    145% through the stretch with no train. Seamless: yaw(f + FRAMES) = yaw(f) + 2 pi."""
    u = (f - HERO_FRAME) / FRAMES
    return 2 * math.pi * u - ORBIT_EASE * math.sin(2 * math.pi * u)


def fit_distances(aspect=16 / 9, margin=(0.92, 0.88)):
    """For every frame of the orbit, the camera distance that keeps the whole block (slab,
    hills, trees and poles) inside the frame, then smoothed into a slow dolly that never
    comes closer than the fit."""
    pts = [Vector(to_blender((x, y, z))) for x in (-32.25, 32.25) for z in (-20.25, 20.25) for y in (0.0, -6.4)]
    pts += [Vector(to_blender(p)) for p in ((-29.8, 10.5, 3.8), (29.8, 10.5, 3.8), (-29.6, 10.0, -9.2), (29.6, 10.0, -9.2),
                                            (11.9, 7.6, -17.8), (11.9, 7.6, 10.6), (-25.6, 7.6, 10.6), (25.4, 7.0, 15.2))]
    target = Vector(to_blender(ORBIT_TARGET))
    view = Vector(to_blender(ORBIT_VIEW)).normalized()
    ty = math.tan(FOV_Y / 2)
    tx = ty * aspect
    up_world = Vector((0, 0, 1))

    def fits(d, direction):
        cam = target + direction * d
        fwd = (target - cam).normalized()
        right = fwd.cross(up_world).normalized()
        up = right.cross(fwd)
        for p in pts:
            v = p - cam
            depth = v.dot(fwd)
            if depth <= 0.1 or abs(v.dot(right)) / (depth * tx) > margin[0] or abs(v.dot(up)) / (depth * ty) > margin[1]:
                return False
        return True

    fit = []
    for f in range(1, FRAMES + 1):
        direction = Matrix.Rotation(orbit_yaw(f), 3, 'Z') @ view
        lo, hi = 30.0, 400.0
        for _ in range(22):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if fits(mid, direction) else (mid, hi)
        fit.append(hi)
    # widen each frame's need over +-2 s, then average over +-2 s: smooth, and never too close
    half = 2 * FPS
    need = [max(fit[(i + k) % FRAMES] for k in range(-half, half + 1)) for i in range(FRAMES)]
    return [sum(need[(i + k) % FRAMES] for k in range(-half, half + 1)) / (2 * half + 1) for i in range(FRAMES)]


def build_camera(coll):
    rig = bpy.data.objects.new('Orbit', None)
    coll.objects.link(rig)
    rig.location = to_blender(ORBIT_TARGET)
    cam_data = bpy.data.cameras.new('Camera')
    cam_data.sensor_fit = 'VERTICAL'
    cam_data.angle_y = FOV_Y
    cam_data.clip_start = 0.5
    cam_data.clip_end = 3000
    cam = bpy.data.objects.new('Camera', cam_data)
    coll.objects.link(cam)
    cam.parent = rig
    # Ultra: a shallow focus on the orbit centre blurs the near and far edges of the
    # block, the tilt-shift look that makes a diorama read as a miniature
    cam_data.dof.use_dof = Q['dof']
    cam_data.dof.focus_object = rig
    cam_data.dof.aperture_fstop = max(Q['fstop'], 0.01)
    cam_data.dof.aperture_blades = 6
    view = Vector(to_blender(ORBIT_VIEW)).normalized()
    distances = fit_distances()
    SCENE['orbit_distance'] = distances[HERO_FRAME - 1]
    cam.location = view * distances[HERO_FRAME - 1]
    track = cam.constraints.new('TRACK_TO')
    track.target = rig
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    SCENE.camera = cam
    for f in range(1, FRAMES + 2):
        rig.rotation_euler.z = orbit_yaw(f)
        rig.keyframe_insert('rotation_euler', index=2, frame=f)
        cam.location = view * distances[(f - 1) % FRAMES]
        cam.keyframe_insert('location', frame=f)
    set_interpolation(rig, 'LINEAR')
    set_interpolation(cam, 'LINEAR')
    return rig


# Authored stills: (name, eye, target in the web frame, frame, night, vertical fov,
# f-stop for Ultra's depth of field, or 'ortho' for the map). With no eye the still is
# taken from the orbit camera at that frame, dollied in by the factor in the fov slot.
SHOT_LIST = [
    ('hero', None, None, HERO_FRAME, 0.0, 0.84, None),
    ('hero_night', None, None, 430, 1.0, 0.84, None),
    ('platform', (9.2, PLAT['h'] + 1.55, -5.7), (-6.0, PLAT['h'] + 1.3, -4.2), 300, 0.0, 40, 1.4),
    ('fumikiri', (16.9, 1.15, 9.8), (15.6, 2.1, -1.0), 486, 0.0, 36, 1.8),
    ('tunnel', (-11.5, 5.6, -10.5), (-21.5, 2.6, -2.0), 64, 0.0, 36, 2.8),
    ('paddies', (-2.5, 3.6, -19.2), (8.0, 1.2, -9.0), HERO_FRAME, 0.0, 40, 2.0),
    ('platform_night', (-12.6, PLAT['h'] + 2.2, -9.4), (2.0, PLAT['h'] + 1.0, -3.2), 300, 1.0, 40, 1.6),
    ('map', (0.0, 140.0, 0.0), (0.0, 0.0, 0.0), HERO_FRAME, 0.0, 'ortho', None),
]


def build_shots(coll):
    """Cameras for the authored stills, kept off the timeline so the loop's orbit camera
    stays in charge of the animation."""
    shots = []
    for name, eye, target, frame, night, fov, fstop in SHOT_LIST:
        if eye is None:
            SCENE.frame_set(frame)
            orbit = SCENE.camera
            cam = bpy.data.objects.new(f'Shot {name}', orbit.data.copy())
            coll.objects.link(cam)
            t = Vector(to_blender(ORBIT_TARGET))
            loc, rot, _ = orbit.matrix_world.decompose()
            cam.location = t + (loc - t) * fov
            cam.rotation_euler = rot.to_euler()
            cam.data.shift_y = -0.04      # the block sits below the orbit target on screen
            shots.append((name, cam, frame, night))
            continue
        data = bpy.data.cameras.new(f'Shot {name}')
        data.clip_start, data.clip_end = 0.1, 3000
        cam = bpy.data.objects.new(f'Shot {name}', data)
        coll.objects.link(cam)
        e, t = Vector(to_blender(eye)), Vector(to_blender(target))
        cam.location = e
        if fov == 'ortho':
            data.type = 'ORTHO'
            data.ortho_scale = 74
            cam.rotation_euler = (0, 0, 0)
        else:
            data.sensor_fit = 'VERTICAL'
            data.angle_y = math.radians(fov)
            cam.rotation_euler = (t - e).to_track_quat('-Z', 'Y').to_euler()
            data.dof.use_dof = Q['dof'] and fstop is not None
            data.dof.focus_distance = (t - e).length
            data.dof.aperture_fstop = fstop or 2.8
        shots.append((name, cam, frame, night))
    return shots


def render_shots(scene, shots, folder):
    os.makedirs(folder, exist_ok=True)
    keep = scene.camera, scene['night']
    for name, cam, frame, night in shots:
        scene.camera = cam
        scene['night'] = night
        scene.frame_set(frame)
        scene.render.filepath = os.path.join(folder, f'{name}.png')
        bpy.ops.render.render(write_still=True)
        print(f'Harukaze: shot {name}', flush=True)
    scene.camera, scene['night'] = keep


# --------------------------------------------------------------------------- assemble


def build(scene, night=0.0, quality='classic'):
    global SCENE, FONT, PETAL_MATERIAL, XF, BATCH, Q
    SCENE = scene
    Q = QUALITY[quality]
    BATCH, XF = {}, Matrix.Identity(4)
    scene['night'] = float(night)
    scene['quality'] = quality
    try:
        scene.id_properties_ui('night').update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description='0 = day, 1 = night')
    except Exception:
        pass
    FONT = find_cjk_font()
    IMAGES['grass'] = paint_grass()
    IMAGES['road'] = paint_road()
    IMAGES['timetable'] = paint_sign('harukaze_timetable', 'timetable')
    IMAGES['posterSakura'] = paint_sign('harukaze_poster_sakura', 'sakura')
    IMAGES['posterSea'] = paint_sign('harukaze_poster_sea', 'sea')
    IMAGES['vend1'] = paint_vending('harukaze_vend_red', '#e2474b', '#c2313a', ['#3b8be0', '#ffb43c', '#f05a5a', '#5fc46f', '#8a5cd6', '#f7f2e8', '#2fb3c4'])
    IMAGES['vend2'] = paint_vending('harukaze_vend_blue', '#3b7fd4', '#2d63ad', ['#d94a64', '#78c850', '#f7d35a', '#e8eef5', '#4b4b58', '#ff8f5a', '#8fd3f5'])
    PETAL_MATERIAL = toon_material('petal', '#ffc1d3', double_sided=True)

    build_block()
    build_hills()
    build_track()
    build_road()
    build_platform()
    build_station()
    for hs in HOUSES:
        house(hs)
    build_garden()
    build_nature()
    build_poles()
    build_catenary()
    build_paddies()
    build_nanohana()
    build_shrine()
    build_road_furniture()
    build_pole_dressing()
    build_platform_kit()
    build_bikes()
    street_lamp(12.7, -6.6, math.pi / 2)
    street_lamp(-11.4, 10.9, math.pi)
    crossing_pole(ROAD_X0 - 0.55, TRACK_Z + 3.95, 0.0)
    crossing_pole(ROAD_X1 + 0.55, TRACK_Z - 3.95, math.pi)

    root = collection('Harukaze Station')
    static = bake(BATCH, collection('Diorama', root))
    blossoms = [o for o in static if o.name.startswith('blossom')]

    signs = collection('Signs', root)
    texts = [text_object(body, size, pos, facing, key, opt, signs) for body, size, pos, facing, key, opt in SIGNS]
    for i, ch in enumerate('止まれ'):
        # 止 sits nearest the stop line; read from the driver's seat
        texts.append(text_object(ch, 1.0, (ROAD_X0 + ROAD_W / 4 + 0.05, 0.05, 7.05 + (i - 1) * 1.5), 'up', 'textWhite', dict(stretch=1.35), signs))
        texts.append(text_object(ch, 1.0, (ROAD_X0 + ROAD_W * 0.75 - 0.05, 0.05, -9.45 - (i - 1) * 1.5), 'up', 'textWhite', dict(stretch=1.35, yaw=math.pi), signs))
    fit_text(texts)

    moving = collection('Moving', root)
    arms = []
    for i, (batch, pivot, ry) in enumerate(ARMS):
        holder = bpy.data.objects.new(f'Barrier arm {i + 1}', None)
        moving.objects.link(holder)
        holder.location = to_blender(pivot)
        holder.rotation_euler = (0.0, 0.0, ry)
        bake(batch, moving, f'arm{i + 1}_', holder)
        arms.append(holder)

    train = bpy.data.objects.new('Train', None)
    moving.objects.link(train)
    train.location = to_blender((X_START, RAIL_Y, TRACK_Z))
    train['beam'] = 0.0
    with batch_scope() as tb:
        with at(CAR_OFF, 0, 0, 0):
            car('head', -1, 0.0)
            pantograph(-2.6)
        with at(-CAR_OFF, 0, 0, math.pi):
            car('tail', 1, math.pi)
    bake(tb.batch, moving, 'train_', train)
    doors = []
    for i, (leaf, window, slide) in enumerate(DOORS):
        part = {'tDoor': Part(), 'tGlass': Part()}
        for key, g in (('tDoor', leaf), ('tGlass', window)):
            part[key].v, part[key].f = list(g.v), list(g.f)
            part[key].smooth, part[key].uvs = [False] * len(g.f), [None] * len(g.f)
        holder = bpy.data.objects.new(f'Door leaf {i + 1}', None)
        moving.objects.link(holder)
        holder.parent = train
        bake(part, moving, f'door{i + 1}_', holder)
        doors.append((holder, slide))

    sky = collection('Sky and petals', root)
    with batch_scope() as cb:
        # a bank of flattened clouds ringing the block below its base, so it reads as
        # floating from every side of the orbit, and three big ones far off for depth
        crng = mulberry32(0xC10D5)
        rings = [(i / 12 * 2 * math.pi + (crng() - 0.5) * 0.35, 48 + crng() * 12, -11 - crng() * 4, 0.9 + crng() * 0.5, 7) for i in range(12)]
        rings += [(a, 175, -24, 3.2, 8) for a in (0.7, 2.9, 4.8)]
        for a, r, y, s, count in rings:
            cx, cz = math.cos(a) * r, math.sin(a) * r
            for _ in range(count):
                k = 1.6 + crng() * 1.4
                add('cloud', puff(k * s, cx + (crng() - 0.5) * 9 * s, y + (crng() - 0.3) * 1.2 * s, cz + (crng() - 0.5) * 5 * s, 0.5))
    for o in bake(cb.batch, sky):
        if hasattr(o, 'visible_shadow'):
            o.visible_shadow = False
    build_petals(blossoms, sky)
    if Q['detail']:
        build_meadow(sky, next(o for o in static if o.name == 'grassTop'))

    lights = collection('Lights and camera', root)
    build_world()
    build_lights(lights, train)
    build_glows(lights, train)
    build_camera(lights)
    SHOTS[:] = build_shots(collection('Shots', root))
    animate(train, doors, arms, train)

    scene.frame_start, scene.frame_end = 1, FRAMES
    scene.render.fps = FPS
    scene.frame_set(HERO_FRAME)
    configure_render(scene, quality)
    build_compositor(scene, Q['bloom'])
    notes = bpy.data.texts.new('Harukaze README')
    notes.write(__doc__)


def configure_render(scene, quality='classic', samples=None):
    q = QUALITY[quality]
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = next(e for e in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE') if e in engines)
    ee = scene.eevee
    ee.taa_render_samples = samples or q['samples']
    ee.taa_samples = 16
    if hasattr(ee, 'use_shadows'):
        ee.use_shadows = True
    if hasattr(ee, 'shadow_ray_count'):
        ee.shadow_ray_count = q['shadow_rays']
        ee.shadow_step_count = q['shadow_steps']
    scene.render.resolution_x, scene.render.resolution_y = q['resolution']
    scene.render.resolution_percentage = 100
    scene.render.use_motion_blur = q['motion_blur']
    scene.render.motion_blur_shutter = 0.5
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'


def make_scene():
    """In the background, reuse the startup scene; in the UI, open a new one."""
    if bpy.app.background or bpy.context.window is None:
        scene = bpy.context.scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        scene.name = 'Harukaze Station'
        return scene
    scene = bpy.data.scenes.new('Harukaze Station')
    bpy.context.window.scene = scene
    return scene


def show_in_viewport():
    if bpy.context.window is None:
        return
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'
                    space.region_3d.view_perspective = 'CAMERA'


def render_frames(scene, folder, first, last):
    """Render frames first..last as PNGs, skipping any already on disk, so a long
    render can be stopped and picked up again."""
    os.makedirs(folder, exist_ok=True)
    for f in range(first, last + 1):
        path = os.path.join(folder, f'frame_{f:04d}.png')
        if os.path.exists(path) and os.path.getsize(path) > 0:
            continue
        scene.frame_set(f)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f'Harukaze: frame {f}/{last}', flush=True)


def encode_video(folder, out_path):
    """Encode the PNG frames to H.264 with the ffmpeg found on the PATH."""
    import shutil
    import subprocess
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        print('Harukaze: ffmpeg not found; frames are in', folder)
        return False
    subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(folder, 'frame_%04d.png'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    out_path], check=True)
    return True


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser(prog='harukaze_station.py', description='Build the Harukaze Station diorama in Blender.')
    ap.add_argument('--quality', choices=sorted(QUALITY), default='classic', help='classic, or ultra for the most detailed build')
    ap.add_argument('--night', action='store_true', help='start at night')
    ap.add_argument('--frame', type=int, default=HERO_FRAME, help=f'frame to render (1-{FRAMES}); {HERO_FRAME} has the train at the platform')
    ap.add_argument('--render', metavar='PNG', help='render one frame to this file')
    ap.add_argument('--video', metavar='MP4', help='render the 32 s loop and encode it as an H.264 video')
    ap.add_argument('--frames', metavar='A-B', help=f'with --video, render only frames A to B (default 1-{FRAMES})')
    ap.add_argument('--shots', metavar='DIR', help='render the authored stills (hero, platform, crossing, tunnel, paddies, night...) into DIR')
    ap.add_argument('--save', metavar='BLEND', help='save the scene as a .blend file')
    ap.add_argument('--resolution', metavar='WxH', help='override the tier resolution, e.g. 1920x1080')
    ap.add_argument('--samples', type=int, help='override the tier sample count')
    args = ap.parse_args(argv)

    scene = make_scene()
    build(scene, 1.0 if args.night else 0.0, args.quality)
    configure_render(scene, args.quality)
    scene.frame_set(args.frame)
    if args.save:
        # saved with the tier's own settings; --samples and --resolution only steer this run
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save), compress=True)
    if args.samples:
        scene.eevee.taa_render_samples = args.samples
    if args.resolution:
        w, h = (int(v) for v in args.resolution.lower().split('x'))
        scene.render.resolution_x, scene.render.resolution_y = w, h
    if args.render:
        scene.render.filepath = os.path.abspath(args.render)
        bpy.ops.render.render(write_still=True)
    if args.shots:
        render_shots(scene, SHOTS, os.path.abspath(args.shots))
    if args.video:
        if not args.samples:
            scene.eevee.taa_render_samples = QUALITY[args.quality]['video_samples']
        out = os.path.abspath(args.video)
        folder = os.path.splitext(out)[0] + '_frames'
        first, last = (int(v) for v in (args.frames or f'1-{FRAMES}').split('-'))
        render_frames(scene, folder, first, last)
        if all(os.path.exists(os.path.join(folder, f'frame_{f:04d}.png')) for f in range(1, FRAMES + 1)):
            encode_video(folder, out)
    show_in_viewport()


if __name__ == '__main__':
    main()
