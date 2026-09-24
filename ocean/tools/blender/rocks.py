"""Boulders for the hillsides and the rocky coast (Blender).

Each boulder is an icosphere cut by random fracture planes (flat, faceted
faces like broken basalt), then weathered with fractal noise and settled
with a flat underside. Vertex colours carry cavity occlusion (r) and an
upward-facing moss mask (g); the game textures the rock triplanar with the
Blender-baked basalt from ground.py.

writes assets/terrain/rocks.glb (rock_<i>_lod0 / rock_<i>_lod1) and rocks.json
usage: python tools/blender/rocks.py
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402  (after bpy, which puts it on the path)
from mathutils import Vector, noise  # noqa: E402
from lib import ASSETS, reset, rng  # noqa: E402

OUT = os.path.join(ASSETS, 'terrain')
COUNT = 6


def boulder(seed, subdiv=4):
    g = rng(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    stretch = np.array([g.uniform(1.0, 1.5), g.uniform(0.8, 1.2), g.uniform(0.6, 0.95)])
    planes = []
    for _ in range(int(g.integers(5, 9))):
        n = g.normal(size=3)
        n /= np.linalg.norm(n)
        if n[2] < -0.5:
            n[2] = -n[2]            # keep the fractures off the buried underside
        planes.append((n, g.uniform(0.55, 0.85)))
    off = Vector(g.uniform(-50, 50, 3))
    for v in bm.verts:
        p = np.array(v.co) * stretch
        # fracture planes: pull everything beyond a plane back onto it
        for n, d in planes:
            s = float(np.dot(p, n))
            if s > d:
                p -= n * (s - d) * 0.92
        q = Vector(p) * 1.3 + off
        p *= 1 + 0.09 * noise.fractal(q, 0.55, 2.2, 4) + 0.035 * noise.fractal(q * 3.1, 0.5, 2.0, 3)
        # settle: a flat, slightly buried base
        if p[2] < -0.35:
            p[2] = -0.35 + (p[2] + 0.35) * 0.25
        v.co = Vector(p)
    bm.normal_update()
    return bm, stretch


def to_mesh(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def paint(ob):
    """cavity (vertex below its neighbours' plane) and moss (faces the sky)"""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    cav = np.ones(len(bm.verts))
    for v in bm.verts:
        if not v.link_edges:
            continue
        c = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
        d = (c - v.co).dot(v.normal)
        cav[v.index] = d
    cav = np.clip(1 - (cav - np.median(cav)) * 12, 0.35, 1.0)
    moss = np.array([max(v.normal.z, 0) ** 2 for v in bm.verts])
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    cols = np.stack([cav, moss, np.zeros_like(cav), np.ones_like(cav)], 1).astype(np.float32)
    ca.data.foreach_set('color', cols.ravel())
    me.color_attributes.active_color = ca
    bm.free()


def lod1(ob, ratio):
    dec = ob.modifiers.new('dec', 'DECIMATE')
    dec.ratio = ratio
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    ob.modifiers.remove(dec)
    lo = bpy.data.objects.new(ob.name.replace('lod0', 'lod1'), me)
    bpy.context.scene.collection.objects.link(lo)
    return lo


if __name__ == '__main__':
    reset()
    meta = []
    for i in range(COUNT):
        bm, st = boulder(900 + i)
        ob = to_mesh(f'rock_{i}_lod0', bm)
        bm.free()
        paint(ob)
        lo = lod1(ob, 0.12)
        meta.append({'size': [round(float(x), 3) for x in st], 'lod0_verts': len(ob.data.vertices), 'lod1_verts': len(lo.data.vertices)})
        print(i, meta[-1])
    path = os.path.join(OUT, 'rocks.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_normals=True, export_texcoords=False,
                              export_vertex_color='ACTIVE', export_materials='NONE', export_yup=True,
                              export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7)
    json.dump(meta, open(os.path.join(OUT, 'rocks.json'), 'w'), indent=1)
    print('wrote', path, os.path.getsize(path) // 1024, 'KiB')
