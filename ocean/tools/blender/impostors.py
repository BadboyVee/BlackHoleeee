"""Octahedral impostors for the far trees (Blender + Cycles).

Each tree variant is rendered from a hemi-octahedral grid of view directions
(FRAMES x FRAMES, grid points uv = k / (FRAMES - 1), horizon on the square's
edges). All frames come out of ONE render: the tree is instanced once per
frame, each copy rotated so that its view direction faces the orthographic
camera overhead, and laid out on the grid.

Conventions (shared with src/world/impostor.js), three.js tree space (y up):
    decode(uv):  e = uv*2-1;  p = ((e.x+e.y)/2, (e.x-e.y)/2);
                 v = normalize(p.x, 1-|p.x|-|p.y|, p.y)
    frame basis: right = normalize(cross((0,1,0), v)), up = cross(v, right)
    frame image: x = dot(P - centre, right), y = dot(P - centre, up), both
                 divided by 2*radius, + 0.5

Outputs per variant (atlas with FRAMES x FRAMES cells, frame (i, j) at
column i, row j counted from the top):
    imp_<name>_c.webp   albedo (sRGB) + coverage
    imp_<name>_n.webp   octahedral normal (tree space) xy, depth along the
                        view direction (0.5 = crown centre plane, +-radius),
                        ambient occlusion

usage: python tools/blender/impostors.py [species...]
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402
import trees  # noqa: E402
from lib import ASSETS, dilate, linear_to_srgb, ortho_camera, render_passes, reset, rng, save_image, to_u8  # noqa: E402

OUT = os.path.join(ASSETS, 'vegetation')
FRAMES = 8
FRAME_PX = 128
SPECIES = ['broad', 'umbrella', 'palm', 'ironwood']
ATLAS_FOR = {'broad': 'leaves_broad', 'umbrella': 'leaves_broad', 'palm': 'frond_palm', 'ironwood': 'leaves_needle'}


def decode(u, v):
    ex, ey = u * 2 - 1, v * 2 - 1
    px, pz = (ex + ey) / 2, (ex - ey) / 2
    d = np.array([px, 1 - abs(px) - abs(pz), pz])
    return d / np.linalg.norm(d)


def basis(v):
    right = np.cross([0.0, 1.0, 0.0], v)
    right /= np.linalg.norm(right)
    up = np.cross(v, right)
    return right, up


def oct_encode(n):
    """unit vectors (..., 3) -> [0,1]^2 full octahedral encoding"""
    n = n / (np.abs(n).sum(-1, keepdims=True) + 1e-9)
    x, y, z = n[..., 0], n[..., 1], n[..., 2]
    ox, oz = x.copy(), z.copy()
    neg = y < 0
    ox[neg] = (1 - np.abs(z[neg])) * np.sign(x[neg] + 1e-12)
    oz[neg] = (1 - np.abs(x[neg])) * np.sign(z[neg] + 1e-12)
    return np.stack([ox, oz], -1) * 0.5 + 0.5


# blender (x, y, z) -> three (x, z, -y)
B2T = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)


def render_materials(species):
    bark = bpy.data.materials.new('imp_bark')
    bark.use_nodes = True
    b = bark.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.1, 0.085, 0.07, 1) if species != 'palm' else (0.2, 0.18, 0.15, 1)
    leaves = bpy.data.materials.new('imp_leaves')
    leaves.use_nodes = True
    nt = leaves.node_tree
    lb = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(OUT, f'{ATLAS_FOR[species]}_c.webp'))
    # straight alpha would be un-premultiplied by Cycles: keep channels as they are
    tex.image.alpha_mode = 'CHANNEL_PACKED'
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    nt.links.new(uv.outputs[0], tex.inputs[0])
    nt.links.new(tex.outputs['Color'], lb.inputs['Base Color'])
    # hard alpha test, like the game's cards
    gt = nt.nodes.new('ShaderNodeMath')
    gt.operation = 'GREATER_THAN'
    gt.inputs[1].default_value = 0.5
    nt.links.new(tex.outputs['Alpha'], gt.inputs[0])
    nt.links.new(gt.outputs[0], lb.inputs['Alpha'])
    # dead fronds / husks (TEXCOORD_1.x = 1) are brown
    uv2 = nt.nodes.new('ShaderNodeUVMap')
    uv2.uv_map = 'UVMap.001'
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv2.outputs[0], sep.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    nt.links.new(sep.outputs['X'], mix.inputs[0])
    nt.links.new(tex.outputs['Color'], mix.inputs[6])
    mix.inputs[7].default_value = (0.2, 0.13, 0.06, 1)
    nt.links.new(mix.outputs[2], lb.inputs['Base Color'])
    return bark, leaves


def bake(species, vi, seed):
    reset()
    make, dress, _, _ = trees.SPECIES[species]
    tree = make(seed)
    bark_b, leaf_b, _ = dress(tree, rng(seed * 7 + 0), 0)
    bark_m, leaf_m = render_materials(species)
    parts = [o for o in (trees.to_object('bark', bark_b, bark_m), trees.to_object('leaves', leaf_b, leaf_m)) if o is not None]
    # bounding sphere (blender space) from the vertices
    vs = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in parts])
    lo, hi = vs.min(0), vs.max(0)
    centre = (lo + hi) / 2
    radius = float(np.linalg.norm(vs - centre, axis=1).max()) * 1.01
    cell = 2 * radius
    size = cell * FRAMES
    rots = {}
    for j in range(FRAMES):
        for i in range(FRAMES):
            v = decode(i / (FRAMES - 1), j / (FRAMES - 1))
            right, up = basis(v)
            R = np.stack([right, up, v])                 # three-space -> (image x, image y, toward viewer)
            A = R @ B2T                                  # blender-local -> camera-aligned
            rots[(i, j)] = R
            # frame (i, j): column i, row j from the TOP of the image
            cx = (i + 0.5) * cell - size / 2
            cy = size / 2 - (j + 0.5) * cell
            M = Matrix.Translation((cx, cy, 0)) @ Matrix([list(A[0]) + [0], list(A[1]) + [0], list(A[2]) + [0], [0, 0, 0, 1]]) @ Matrix.Translation((-centre[0], -centre[1], -centre[2]))
            for o in parts:
                inst = o.copy()                           # shares the mesh
                bpy.context.scene.collection.objects.link(inst)
                inst.matrix_world = M
    for o in parts:
        bpy.context.scene.collection.objects.unlink(o)
    px = FRAMES * FRAME_PX
    cam_h = radius * 4 + 10
    ortho_camera((0, 0), size, size, px, px, height=cam_h)
    P = render_passes(samples=48, passes=('Alpha', 'DiffCol', 'Normal', 'Depth', 'AO'), ao_distance=radius * 0.18)
    a = P['Alpha'][..., 0]
    inv = 1 / np.maximum(a, 1e-4)
    albedo = P['DiffCol'][..., :3] * inv[..., None]
    nw = P['Normal'][..., :3] * inv[..., None]
    depth = P['Depth'][..., 0]
    ao = np.clip(P['AO'][..., 0] * inv, 0, 1)
    # per frame: world normal (camera-aligned) -> three tree space; depth relative to the centre plane
    n_tree = np.zeros_like(nw)
    d01 = np.full(a.shape, 0.5, np.float32)
    for (i, j), R in rots.items():
        ys, xs = slice(j * FRAME_PX, (j + 1) * FRAME_PX), slice(i * FRAME_PX, (i + 1) * FRAME_PX)
        n = nw[ys, xs]
        n_tree[ys, xs] = n @ R                            # R^T n  (rows of R are the basis)
        z = cam_h - depth[ys, xs]                          # height above the centre plane, toward the viewer
        d01[ys, xs] = np.clip(z / radius * 0.5 + 0.5, 0, 1)
    n_tree /= np.linalg.norm(n_tree, axis=-1, keepdims=True) + 1e-6
    covered = a > 0.02
    d01[~covered] = 0.5
    # data channels are only trustworthy where the coverage is solid
    solid = np.where(a > 0.3, a, 0.0)
    albedo = dilate(albedo, solid, 24)
    enc = dilate(oct_encode(n_tree), solid, 24)
    ao = dilate(ao[..., None], solid, 24)[..., 0]
    d01 = dilate(d01[..., None], solid, 24)[..., 0]
    name = f'{species}_{vi}'
    c = np.concatenate([linear_to_srgb(albedo), a[..., None]], -1)
    nmap = np.concatenate([enc, d01[..., None], ao[..., None]], -1)
    s1 = save_image(os.path.join(OUT, f'imp_{name}_c.webp'), to_u8(c), quality=88)
    s2 = save_image(os.path.join(OUT, f'imp_{name}_n.webp'), to_u8(nmap), quality=82)
    # the crown centre in three space, relative to the tree's origin
    c3 = B2T @ centre
    print(f'impostor {name}: radius {radius:.2f} m, colour {s1 // 1024} KiB, normal {s2 // 1024} KiB')
    return {'centre': [round(float(x), 3) for x in c3], 'radius': round(radius, 3)}


if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if not a.startswith('-')] or SPECIES
    meta_path = os.path.join(OUT, 'impostors.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    meta['frames'] = FRAMES
    meta['framePx'] = FRAME_PX
    for sp in names:
        seeds = trees.SPECIES[sp][2]
        meta[sp] = [bake(sp, vi, seed) for vi, seed in enumerate(seeds)]
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=1)
