"""HORIZON's meadow: the wildflowers and long grass right in front of the lens when Scout's phone floats over the
field, rendered with a wide-open lens focused on the phone, so they fall into soft bokeh at the bottom corners of
the frame. The background is left clear for the film's own hills.

Run with the `bpy` module (pip install bpy==4.2.0):
    python3 blender/meadow.py OUT_DIR [--preview]
"""
import math
import os
import sys

import bpy
import mathutils
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/meadow"
PREVIEW = "--preview" in sys.argv
W, H = (960, 540) if PREVIEW else (1920, 1080)
CAM = (0.0, 0.0, 0.55)
FOCUS = 2.2                                    # where the phone floats
rng = np.random.default_rng(7)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = W, H
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "16"
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Punchy"
    c = scn.cycles
    c.device = "CPU"
    c.samples = 32 if PREVIEW else 160
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 6
    c.transmission_bounces = 4


def light():
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    N, L = world.node_tree.nodes, world.node_tree.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.45, (0.10, 0.16, 0.06, 1)          # the meadow below
    e[1].position, e[1].color = 0.55, (0.55, 0.70, 0.95, 1)          # the sky above
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], N["Background"].inputs["Color"])
    N["Background"].inputs["Strength"].default_value = 0.9
    d = bpy.data.lights.new("sun", "SUN")
    d.energy = 4.2
    d.angle = math.radians(1.0)
    d.color = (1.0, 0.95, 0.85)
    o = bpy.data.objects.new("sun", d)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - 24), 0, math.radians(300))   # low from the left, as on the hills


def petal_mat(name, col, glow=0.35, gloss=0.45):
    """A petal: thin, so the sun shines through it from behind."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = gloss
    b.inputs["Sheen Weight"].default_value = 0.3
    tr = N.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (*col, 1)
    mix = N.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = glow
    L.new(b.outputs[0], mix.inputs[1])
    L.new(tr.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def blade_mat():
    m = petal_mat("blade", (0.06, 0.28, 0.02), glow=0.4, gloss=0.5)
    N, L = m.node_tree.nodes, m.node_tree.links
    rnd = N.new("ShaderNodeObjectInfo")                              # each blade its own green
    ramp = N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].color = (0.035, 0.20, 0.012, 1)
    e[1].color = (0.12, 0.36, 0.03, 1)
    L.new(rnd.outputs["Random"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], N["Principled BSDF"].inputs["Base Color"])
    L.new(ramp.outputs["Color"], N["Translucent BSDF"].inputs["Color"])
    return m


def ribbon(name, pts, widths, mat, normal_hint=(1, 0, 0)):
    """A flat strip along pts, as wide as widths at each point: a blade of grass, or a stem."""
    verts, faces = [], []
    hint = mathutils.Vector(normal_hint)
    for i, (p, w) in enumerate(zip(pts, widths)):
        p = mathutils.Vector(p)
        t = (mathutils.Vector(pts[min(i + 1, len(pts) - 1)]) - mathutils.Vector(pts[max(i - 1, 0)])).normalized()
        side = t.cross(hint).normalized() * (w / 2)
        verts += [tuple(p - side), tuple(p + side)]
        if i:
            k = 2 * i
            faces.append((k - 2, k - 1, k + 1, k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for f in me.polygons:
        f.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(mat)
    return o


def curve_pts(base, height, lean, bend, n=10):
    """A stem's or blade's centre line: up from base, leaning over and bending as it goes."""
    out = []
    for i in range(n + 1):
        s = i / n
        out.append((base[0] + lean[0] * s + bend[0] * s * s, base[1] + lean[1] * s + bend[1] * s * s,
                    base[2] + height * s - 0.15 * height * s * s * (abs(bend[0]) + abs(bend[1])) / max(height, 1e-3)))
    return out


def blade(base, mat, h=None):
    h = h or rng.uniform(0.22, 0.5)
    lean = (rng.uniform(-0.08, 0.08), rng.uniform(-0.05, 0.05))
    bend = (rng.uniform(-0.18, 0.18), rng.uniform(-0.1, 0.1))
    pts = curve_pts(base, h, lean, bend)
    wid = rng.uniform(0.004, 0.009)
    widths = [wid * (1 - (i / 10) ** 1.6) + 0.0004 for i in range(11)]
    ang = rng.uniform(0, math.pi)
    return ribbon("blade", pts, widths, mat, (math.cos(ang), math.sin(ang), 0))


def stem(base, h, mat):
    lean = (rng.uniform(-0.04, 0.04), rng.uniform(-0.03, 0.03))
    bend = (rng.uniform(-0.05, 0.05), rng.uniform(-0.03, 0.03))
    pts = curve_pts(base, h, lean, bend)
    ribbon("stem", pts, [0.003] * len(pts), mat, (1, 0, 0))
    ribbon("stem", pts, [0.003] * len(pts), mat, (0, 1, 0))
    return mathutils.Vector(pts[-1])


def disc(name, rx, ry, rz, loc, rot, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (rx, ry, rz)
    o.rotation_euler = rot
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def head(kind, top, mats):
    """A flower head facing up and a little toward the camera."""
    face = (math.radians(rng.uniform(15, 40)), 0, math.radians(rng.uniform(-30, 30)))
    fm = mathutils.Euler(face).to_matrix()

    def at(v):
        return tuple(top + fm @ mathutils.Vector(v))

    if kind == "daisy":
        n, ln, wd, cup = 18, 0.024, 0.006, 10
        disc("eye", 0.009, 0.009, 0.005, at((0, 0, 0.002)), face, mats["eye"])
        petal = mats["white"]
    elif kind == "poppy":
        n, ln, wd, cup = 4, 0.030, 0.026, 45
        disc("eye", 0.007, 0.007, 0.006, at((0, 0, 0.004)), face, mats["dark"])
        petal = mats["red"]
    elif kind == "buttercup":
        n, ln, wd, cup = 5, 0.016, 0.014, 45
        disc("eye", 0.004, 0.004, 0.003, at((0, 0, 0.003)), face, mats["eye"])
        petal = mats["yellow"]
    else:                                                             # clover: a pink ball
        disc("clover", 0.017, 0.017, 0.014, at((0, 0, 0.008)), face, mats["pink"])
        return
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.1, 0.1)
        tilt = math.radians(cup + rng.uniform(-8, 8))
        d = mathutils.Vector((math.cos(a) * math.cos(tilt), math.sin(a) * math.cos(tilt), math.sin(tilt)))
        c = fm @ (d * ln * 0.55)
        rot = (fm @ mathutils.Euler((0, -tilt, a)).to_matrix()).to_euler()
        disc("petal", ln * 0.55, wd * 0.5, 0.0009, tuple(top + c), rot, petal)


def flower(base, kind, mats):
    h = {"daisy": rng.uniform(0.24, 0.4), "poppy": rng.uniform(0.3, 0.46), "buttercup": rng.uniform(0.24, 0.38),
         "clover": rng.uniform(0.18, 0.28)}[kind]
    top = stem(base, h, mats["stem"])
    head(kind, top, mats)


def meadow():
    reset()
    light()
    mats = {"white": petal_mat("white", (0.85, 0.84, 0.80), 0.4), "red": petal_mat("red", (0.80, 0.04, 0.02), 0.5),
            "yellow": petal_mat("yellow", (0.95, 0.62, 0.02), 0.3, 0.2),
            "pink": petal_mat("pink", (0.85, 0.25, 0.45), 0.35, 0.6),
            "eye": petal_mat("eye", (0.9, 0.55, 0.02), 0.1, 0.7), "dark": petal_mat("dark", (0.02, 0.03, 0.02), 0.0, 0.5),
            "stem": blade_mat()}
    grass = blade_mat()
    kinds = ["daisy"] * 6 + ["poppy"] * 3 + ["buttercup"] * 5 + ["clover"] * 2
    # two banks, left and right, close to the lens; the middle open for the phone
    for side in (-1, 1):
        for _ in range(380):
            y = rng.uniform(0.35, 1.6)
            x = side * rng.uniform(0.3, 0.95) * y * 0.75 + side * 0.05
            blade((x, y, 0.0), grass)
        for _ in range(30):
            y = rng.uniform(0.4, 1.2)
            x = side * rng.uniform(0.32, 0.85) * y * 0.75 + side * 0.06
            flower((x, y, 0.0), kinds[int(rng.integers(len(kinds)))], mats)
    # a low fringe of grass along the bottom edge
    for _ in range(200):
        y = rng.uniform(0.3, 0.7)
        x = rng.uniform(-0.6, 0.6) * y
        blade((x, y, 0.0), grass, h=rng.uniform(0.12, 0.24))
    cd = bpy.data.cameras.new("cam")
    cd.lens = 35
    cd.dof.use_dof = True
    cd.dof.focus_distance = FOCUS
    cd.dof.aperture_fstop = 1.4
    cd.dof.aperture_blades = 7
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    cam.location = CAM
    cam.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = os.path.join(OUT, "meadow.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    meadow()
