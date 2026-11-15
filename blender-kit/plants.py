"""Procedural plants that Poly Haven has no scan for: palms and clipped hedges."""
import math
import random

import bpy
from mathutils import Matrix, Vector

import kit
from kit import MB


def _mats():
    bark = kit.mat_pbr("palm_bark", "palm_tree_bark", size=0.9, normal=2.0, val=0.9)
    leaf = kit.mat_plain("palm_leaf", (0.07, 0.19, 0.035), rough=0.42, spec=0.5)
    leaf2 = kit.mat_plain("palm_leaf_dry", (0.24, 0.22, 0.08), rough=0.6)
    stem = kit.mat_plain("palm_stem", (0.2, 0.26, 0.08), rough=0.5)
    # a little light passes through fronds
    for m in (leaf,):
        b = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"][0]
        b.inputs["Subsurface Weight"].default_value = 0.0
        try:
            b.inputs["Transmission Weight"].default_value = 0.12
        except Exception:
            pass
    return bark, leaf, leaf2, stem


def palm_mesh(name, height=7.0, fronds=22, frond_len=3.2, seed=0, lean=0.5, collection=None):
    """Royal/coconut-style palm as a single mesh object, base at origin."""
    rnd = random.Random(seed)
    bark, leaf, leaf_dry, stem = _mats()
    mb = MB()
    # trunk: gently curved, slightly swollen base, ringed by bark texture
    n = 18
    la = rnd.uniform(0, 6.28)
    pts, rad = [], []
    for i in range(n + 1):
        t = i / n
        off = lean * t * t
        pts.append(Vector((math.cos(la) * off, math.sin(la) * off, height * t)))
        rad.append(0.2 * (1.0 - 0.45 * t) + 0.09 * math.exp(-t * 9))
    seg = 14
    vacc = 0.0
    rings = []
    for i, p in enumerate(pts):
        rings.append([p + Vector((math.cos(a) * rad[i], math.sin(a) * rad[i], 0)) for a in
                      [2 * math.pi * k / seg for k in range(seg)]])
    for i in range(n):
        dv = (pts[i + 1] - pts[i]).length
        for k in range(seg):
            k2 = (k + 1) % seg
            u0, u1 = k / seg * 1.2, (k + 1) / seg * 1.2
            mb.face([rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]], bark,
                    uvs=[(u0, vacc), (u1, vacc), (u1, vacc + dv), (u0, vacc + dv)], smooth=True)
        vacc += dv
    top = pts[-1]
    # crownshaft
    mb.cyl(top - Vector((0, 0, 0.1)), top + Vector((0, 0, 0.7)), rad[-1] * 1.05, stem, seg=12, r1=rad[-1] * 0.5)
    crown = top + Vector((0, 0, 0.55))
    for f in range(fronds):
        az = f * 2.399963 + rnd.uniform(-0.2, 0.2)
        tier = f / fronds                       # 0 = youngest (upright) .. 1 = oldest (drooping)
        elev = math.radians(75 - 105 * tier + rnd.uniform(-8, 8))
        L = frond_len * rnd.uniform(0.85, 1.1) * (0.75 + 0.35 * math.sin(math.pi * min(1, tier + 0.25)))
        droop = 0.9 + 1.5 * tier
        mat = leaf_dry if (tier > 0.93 and rnd.random() < 0.6) else leaf
        ns = 14
        d0 = Vector((math.cos(az) * math.cos(elev), math.sin(az) * math.cos(elev), math.sin(elev)))
        side = Vector((-math.sin(az), math.cos(az), 0))
        p = crown.copy()
        spine = [p.copy()]
        d = d0.copy()
        for s in range(ns):
            d = (d + Vector((0, 0, -droop * 0.045 * (1 + s * 0.12)))).normalized()
            p = p + d * (L / ns)
            spine.append(p.copy())
        for s in range(ns):
            a, b = spine[s], spine[s + 1]
            w = 0.035 * (1 - s / ns) + 0.006
            up = (b - a).normalized().cross(side).normalized()
            mb.face([a - side * w, a + side * w, b + side * w * 0.8, b - side * w * 0.8], stem)
            if s < 1:
                continue
            t = s / ns
            ll = 0.75 * math.sin(math.pi * min(1.0, t * 1.15 + 0.08)) ** 0.7 * (frond_len / 3.2) + 0.12
            for q in range(3):
                base = a.lerp(b, q / 3.0)
                for sg in (-1, 1):
                    fwd = (b - a).normalized()
                    dirv = (side * sg * 0.85 + fwd * 0.5 - up * 0.05 + Vector((0, 0, -0.35 - 0.25 * tier))).normalized()
                    tip = base + dirv * ll * rnd.uniform(0.85, 1.1)
                    lw = fwd * 0.028
                    mid = base.lerp(tip, 0.5) + Vector((0, 0, 0.03))
                    mb.face([base - lw, base + lw, mid + lw * 1.1, mid - lw * 1.1], mat)
                    mb.face([mid - lw * 1.1, mid + lw * 1.1, tip], mat)
    # a few coconuts / flower stalks for the crown silhouette
    ob = mb.build(name, collection)
    return ob


def hedge(mb, x0, y0, x1, y1, h, mat, z=0.0, seed=0, lump=0.06):
    """Clipped hedge as a lumpy box (displacement comes from the material bump)."""
    mb.box(x0, y0, z, x1, y1, z + h, mat, skip="-z")


def hedge_mat():
    m = kit._mats.get("hedge")
    if m:
        return m
    m, nt, b, out = kit._new("hedge")
    N, L = nt.nodes, nt.links
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 55.0
    nz.inputs["Detail"].default_value = 6.0
    vor = N.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 90.0
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.012, 0.045, 0.008, 1)
    ramp.color_ramp.elements[1].color = (0.09, 0.22, 0.03, 1)
    L.new(nz.outputs[0], ramp.inputs[0])
    L.new(ramp.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 1.0
    bp.inputs["Distance"].default_value = 0.08
    L.new(vor.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.55
    kit._mats["hedge"] = m
    return m
