"""TOMO, a home robot: its bust (a white shell head with a black glass visor, ear lights, a ribbed neck, white
shoulders on graphite joints) in a few head turns, and the things it does (a stack of folded towels, a stack of
plates, a succulent in a clay pot), each rendered as a sprite with a clear background. The film lights the eyes
on the visor itself, so they can blink and wink: where they sit is written beside each bust.

    python3 blender/tomo.py OUT_DIR [job ...] [--preview]      jobs: bust:<turn>  towels  plates  plant
"""
import json
import math
import os
import sys

import bpy
import mathutils
from bpy_extras.object_utils import world_to_camera_view

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tomo"
JOBS = [a for a in sys.argv[2:] if not a.startswith("--")]
PREVIEW = "--preview" in sys.argv


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def reset(size, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = size
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "16"
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.view_settings.exposure = float(os.environ.get("EXPOSURE", "0.0"))
    c = scn.cycles
    c.device = "CPU"
    c.samples = 32 if PREVIEW else samples
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 8
    c.glossy_bounces = 4
    world = bpy.data.worlds.new("w")
    scn.world = world
    world.use_nodes = True
    N, L = world.node_tree.nodes, world.node_tree.links
    # a studio: light grey all round, brighter overhead, for the glossy shell and visor to reflect
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.18, 0.19, 0.2, 1)
    ramp.color_ramp.elements[1].position = 0.9
    ramp.color_ramp.elements[1].color = (0.95, 0.96, 1.0, 1)
    L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    bg = N["Background"]
    bg.inputs["Strength"].default_value = 0.8
    L.new(ramp.outputs["Color"], bg.inputs["Color"])


def look_at(o, target):
    d = mathutils.Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def softbox(name, loc, energy, size, target=(0, 0, 0), col=(1, 1, 1), shape="RECTANGLE", sy=None):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.shape = shape
    d.size = size
    if sy:
        d.size_y = sy
    d.color = col
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    look_at(o, target)
    return o


def camera(loc, target, lens):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    o = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(o)
    o.location = loc
    look_at(o, target)
    bpy.context.scene.camera = o
    return o


def mat(name, col, rough=0.5, metal=0.0, coat=0.0, coat_rough=0.05, emit=None, strength=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = coat_rough
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def micro(m, scale=900.0, strength=0.04):
    """A faint moulded-plastic grain."""
    N, L = m.node_tree.nodes, m.node_tree.links
    n = N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    b = N.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    L.new(n.outputs["Fac"], b.inputs["Height"])
    L.new(b.outputs["Normal"], N["Principled BSDF"].inputs["Normal"])
    return m


def smooth(o, levels=2, bevel=None):
    if bevel:
        bv = o.modifiers.new("bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 4
        bv.limit_method = "ANGLE"
    sd = o.modifiers.new("sub", "SUBSURF")
    sd.levels = sd.render_levels = levels
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth()
    return o


# ---------------------------------------------------------------- the robot

WHITE = None


def ellipsoid_patch(name, a, b, c, half_w, half_h, zc, power=4.0, n=64, inflate=1.0):
    """A patch of the front of the ellipsoid (a, b, c) inside the superellipse |x/half_w|^p + |(z-zc)/half_h|^p <= 1,
    as a clean grid (so its edge is smooth)."""
    verts, faces = [], []
    for j in range(n + 1):
        for i in range(n + 1):
            u, v = 2 * i / n - 1, 2 * j / n - 1
            # square -> superellipse, keeping the grid regular
            m = max(abs(u), abs(v))
            if m == 0:
                x, z = 0.0, 0.0
            else:
                ang = math.atan2(v, u)
                cu, sv = math.cos(ang), math.sin(ang)
                rr = (abs(cu) ** power + abs(sv) ** power) ** (-1.0 / power)
                x, z = m * rr * cu * half_w, m * rr * sv * half_h
            z += zc
            k = 1.0 - (x / a) ** 2 - (z / c) ** 2
            y = -b * math.sqrt(max(k, 0.0))
            verts.append((x * inflate, y * inflate, z * inflate))
    for j in range(n):
        for i in range(n):
            q = j * (n + 1) + i
            faces.append((q, q + 1, q + n + 2, q + n + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


HEAD = (0.98, 0.9, 0.86)                # the head's ellipsoid
HEAD_Z = 0.55                           # its centre above the neck's pivot
EYE = (0.27, 0.02)                      # the eyes on the visor: x from the middle, z from the head's centre


def robot(turn=0.0, tilt=0.0):
    """The bust. Returns the head's pivot, and the visor's two eye points in world space."""
    shell = micro(mat("shell", srgb("#eceef1"), rough=0.3, coat=0.6, coat_rough=0.08))
    graphite = mat("graphite", srgb("#1b1c20"), rough=0.42, metal=0.35)
    rubber = mat("rubber", srgb("#26272c"), rough=0.7)
    glass = mat("visor", srgb("#040406"), rough=0.02, coat=1.0, coat_rough=0.0, spec=0.6)
    glow = mat("glow", srgb("#3d8bff"), rough=0.4, emit=srgb("#5aa2ff"), strength=5.0)
    body = []

    # the torso: a soft rounded block, broad at the shoulders and narrowing to the waist
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -2.05))
    t = bpy.context.object
    t.scale = (2.3, 1.25, 1.9)
    bpy.ops.object.transform_apply(scale=True)
    for v in t.data.vertices:
        if v.co.z < -2.05:
            v.co.x *= 0.82
            v.co.y *= 0.9
    smooth(t, 3, bevel=0.42)
    t.data.materials.append(shell)
    body.append(t)
    # a seam around the chest, and a status light
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.63, -1.72))
    lamp = bpy.context.object
    lamp.scale = (0.3, 0.04, 0.04)
    smooth(lamp, 2, bevel=0.3)
    lamp.data.materials.append(glow)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.62, -2.35))
    plate = bpy.context.object
    plate.scale = (1.1, 0.03, 0.55)
    smooth(plate, 2, bevel=0.25)
    plate.data.materials.append(graphite)
    # shoulders: graphite joints under white caps, and the tops of the arms
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.34, location=(sx * 1.2, 0.0, -1.35))
        smooth(bpy.context.object, 1)
        bpy.context.object.data.materials.append(graphite)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.5, location=(sx * 1.42, 0.0, -1.45))
        cap = bpy.context.object
        cap.scale = (0.95, 0.95, 0.9)
        smooth(cap, 1)
        cap.data.materials.append(shell)
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.36, depth=1.6, location=(sx * 1.52, 0.0, -2.35))
        arm = bpy.context.object
        arm.rotation_euler = (0, math.radians(sx * 6), 0)
        smooth(arm, 2, bevel=0.2)
        arm.data.materials.append(shell)
    # the neck: ribbed rubber
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.3, depth=0.8, location=(0, 0, -0.85))
    n = bpy.context.object
    smooth(n, 1)
    n.data.materials.append(rubber)
    for k in range(6):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.31, minor_radius=0.032, major_segments=64,
                                         location=(0, 0, -1.08 + k * 0.085))
        bpy.context.object.data.materials.append(rubber)

    # the head, on a pivot at the top of the neck, so it can turn and tilt
    pivot = bpy.data.objects.new("pivot", None)
    bpy.context.collection.objects.link(pivot)
    pivot.location = (0, 0, -0.55)
    parts = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0, location=(0, 0, 0))
    head = bpy.context.object
    head.scale = HEAD
    smooth(head, 1)
    head.data.materials.append(shell)
    parts.append(head)
    vis = ellipsoid_patch("visor", *HEAD, half_w=0.8, half_h=0.42, zc=0.02, power=4.0, inflate=1.012)
    so = vis.modifiers.new("thick", "SOLIDIFY")
    so.thickness = 0.025
    so.offset = 1.0
    bpy.context.view_layer.objects.active = vis
    bpy.ops.object.shade_smooth()
    vis.data.materials.append(glass)
    parts.append(vis)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.008, major_segments=160, minor_segments=8,
                                     location=(0, 0, 0))
    seam = bpy.context.object                                         # the shell's parting line, over the crown
    seam.rotation_euler = (0, math.radians(90), 0)
    seam.scale = (HEAD[2] * 1.002, HEAD[1] * 1.002, HEAD[0] * 1.002)
    seam.data.materials.append(graphite)
    parts.append(seam)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.26, depth=0.16, location=(sx * 0.97, 0.02, 0.0))
        e = bpy.context.object
        e.rotation_euler = (0, math.radians(90), 0)
        smooth(e, 2, bevel=0.2)
        e.data.materials.append(shell)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.018, major_segments=64,
                                         location=(sx * 1.06, 0.02, 0.0))
        r = bpy.context.object
        r.rotation_euler = (0, math.radians(90), 0)
        r.data.materials.append(glow)
        parts += [e, r]
    for ob in parts:                                                  # the head lives HEAD_Z above the pivot
        ob.parent = pivot
        ob.location = ob.location + mathutils.Vector((0, 0, HEAD_Z))
    pivot.rotation_euler = (math.radians(tilt), 0, math.radians(turn))
    bpy.context.view_layer.update()
    ex, ez = EYE
    eyes = []
    for sx in (-1, 1):
        x = sx * ex
        y = -HEAD[1] * math.sqrt(max(0.0, 1 - (x / HEAD[0]) ** 2 - (ez / HEAD[2]) ** 2)) * 1.03
        eyes.append(pivot.matrix_world @ mathutils.Vector((x, y, ez + HEAD_Z)))
    return pivot, eyes


def bust(turn):
    size = (720, 720) if PREVIEW else (1400, 1400)
    reset(size, 128)
    softbox("key", (-5.0, -6.0, 3.0), 2400, 2.2, (0, 0, -0.6), col=srgb("#fff7ee"), sy=7.0)
    softbox("fill", (6.0, -5.0, 0.0), 700, 6.0, (0, 0, -0.6), col=srgb("#eef3ff"))
    softbox("rim", (-1.0, 6.0, 3.5), 1600, 3.0, (0, 0, 0))
    softbox("rim2", (4.0, 5.0, 1.0), 900, 2.0, (0, 0, -1.0), col=srgb("#dfe8ff"))
    softbox("top", (0, -1.5, 7.0), 700, 6.0, (0, 0, 0), shape="DISK")
    cam = camera((0, -11.0, 0.35), (0, 0, -0.95), 62)
    for ob in bpy.context.scene.objects:                              # the lamps light it; the visor reflects a strip
        if ob.type == "LIGHT":
            ob.visible_glossy = False
    strip = mat("strip", (1, 1, 1), emit=(1, 1, 1), strength=6.0)
    N, L = strip.node_tree.nodes, strip.node_tree.links
    g = N.new("ShaderNodeTexGradient")
    g.gradient_type = "QUADRATIC_SPHERE"
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.9, 2.6, 1.0)
    tc = N.new("ShaderNodeTexCoord")
    L.new(tc.outputs["Generated"], mp.inputs["Vector"])
    mp.inputs["Location"].default_value = (0.05, -0.8, 0.0)
    L.new(mp.outputs["Vector"], g.inputs["Vector"])
    L.new(g.outputs["Fac"], N["Principled BSDF"].inputs["Emission Strength"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.6, -4.2, 3.6))
    sb = bpy.context.object
    sb.scale = (6.5, 2.2, 1)
    look_at(sb, (0, 0, 0.3))
    sb.rotation_euler.rotate_axis("X", math.radians(180))
    sb.data.materials.append(strip)
    sb.visible_camera = False
    sb.visible_diffuse = False
    pivot, eyes = robot(turn=float(turn))
    scn = bpy.context.scene
    scn.render.filepath = os.path.join(OUT, f"bust_{turn}.png")
    bpy.ops.render.render(write_still=True)
    W, H = scn.render.resolution_x, scn.render.resolution_y
    pts = []
    for p in eyes:
        v = world_to_camera_view(scn, cam, p)
        pts.append((v.x * W, (1 - v.y) * H))
    with open(os.path.join(OUT, f"bust_{turn}.json"), "w") as fh:
        json.dump({"size": [W, H], "eyes": pts}, fh)


# ---------------------------------------------------------------- the things it does

def product_stage(size=(900, 900)):
    reset((720, 720) if PREVIEW else size, 128)
    vs = bpy.context.scene.view_settings                              # products in their true colours
    vs.view_transform = "Standard"
    vs.exposure = -0.25
    softbox("key", (-4.0, -5.0, 6.0), 1500, 5.0, (0, 0, 0.3), col=srgb("#fff6ea"))
    softbox("fill", (5.0, -4.0, 2.0), 500, 5.0, (0, 0, 0.3), col=srgb("#eef3ff"))
    softbox("rim", (0.0, 5.0, 4.0), 700, 4.0, (0, 0, 0.3))
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    bpy.context.object.is_shadow_catcher = True
    camera((0, -7.2, 3.6), (0, 0, 0.55), 58)


def cloth(name, col):
    m = mat(name, col, rough=0.95)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Sheen Weight"].default_value = 0.9
    N, L = m.node_tree.nodes, m.node_tree.links
    n = N.new("ShaderNodeTexNoise")                                   # terry loops
    n.inputs["Scale"].default_value = 420.0
    n.inputs["Detail"].default_value = 6.0
    w = N.new("ShaderNodeTexWave")                                    # and the weave
    w.inputs["Scale"].default_value = 60.0
    w.inputs["Distortion"].default_value = 2.0
    mx = N.new("ShaderNodeMath")
    mx.operation = "ADD"
    L.new(n.outputs["Fac"], mx.inputs[0])
    L.new(w.outputs["Fac"], mx.inputs[1])
    bu = N.new("ShaderNodeBump")
    bu.inputs["Strength"].default_value = 0.45
    L.new(mx.outputs["Value"], bu.inputs["Height"])
    L.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def towels():
    product_stage()
    cols = ["#f4f1ea", "#9db8a4", "#e6cfb0", "#f4f1ea"]
    z = 0.0
    for i, c in enumerate(cols):
        h = 0.26
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.03 * (i % 2) - 0.015, 0.02 * i, z + h / 2))
        t = bpy.context.object
        t.scale = (2.0, 1.4, h)
        t.rotation_euler = (0, 0, math.radians(-2.5 + 2.2 * i))
        bpy.ops.object.transform_apply(scale=True)
        smooth(t, 3, bevel=0.12)
        # soft, a little slumped: bulge the middle and round the fold at the front
        for v in t.data.vertices:
            v.co.z += 0.03 * (1 - (v.co.x / 1.0) ** 2) * (1 if v.co.z > z + h / 2 else -0.3)
        t.data.materials.append(cloth(f"towel{i}", srgb(c)))
        z += h * 0.96
    bpy.context.scene.render.filepath = os.path.join(OUT, "towels.png")
    bpy.ops.render.render(write_still=True)


def plates():
    product_stage()
    ceramic = micro(mat("ceramic", srgb("#f7f6f2"), rough=0.12, coat=0.8, coat_rough=0.02), 300, 0.01)
    rim = mat("rim", srgb("#2f5d8c"), rough=0.2, coat=0.6)
    prof = [(0.0, 0.0), (0.7, 0.0), (0.78, 0.03), (1.05, 0.12), (1.18, 0.16), (1.2, 0.18), (1.17, 0.19),
            (1.03, 0.15), (0.76, 0.06), (0.0, 0.05)]
    for k in range(5):
        me = bpy.data.meshes.new("plate")
        verts, faces = [], []
        seg = 96
        for j in range(seg):
            a = 2 * math.pi * j / seg
            for (r, h) in prof:
                verts.append((r * math.cos(a), r * math.sin(a), h + 0.075 * k))
        n = len(prof)
        for j in range(seg):
            for i in range(n - 1):
                a0, a1 = j * n + i, ((j + 1) % seg) * n + i
                faces.append((a0, a1, a1 + 1, a0 + 1))
        me.from_pydata(verts, [], faces)
        me.update()
        o = bpy.data.objects.new("plate", me)
        bpy.context.collection.objects.link(o)
        o.location = (0.02 * math.sin(k), 0.02 * math.cos(k * 1.7), 0)
        smooth(o, 1)
        o.data.materials.append(ceramic)
        o.data.materials.append(rim)
        for p in o.data.polygons:
            if 4 <= p.index % (n - 1) <= 5:
                p.material_index = 1
    bpy.context.scene.render.filepath = os.path.join(OUT, "plates.png")
    bpy.ops.render.render(write_still=True)


def plant():
    product_stage()
    clay = micro(mat("clay", srgb("#c46a45"), rough=0.85), 250, 0.12)
    soil = mat("soil", srgb("#3a2a20"), rough=1.0)
    leaf = mat("leaf", srgb("#5f8f5a"), rough=0.45, coat=0.3)
    leaf.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.2
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.9, depth=1.1, location=(0, 0, 0.55))
    pot = bpy.context.object
    for v in pot.data.vertices:
        k = 0.78 + 0.22 * (v.co.z + 0.55) / 1.1
        v.co.x *= k
        v.co.y *= k
    so = pot.modifiers.new("s", "SOLIDIFY")
    so.thickness = 0.06
    smooth(pot, 2, bevel=0.03)
    pot.data.materials.append(clay)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.84, depth=0.06, location=(0, 0, 1.02))
    bpy.context.object.data.materials.append(soil)
    # a succulent: rings of thick pointed leaves
    for ring, (count, rad, tilt, size) in enumerate([(9, 0.55, 62, 0.62), (8, 0.36, 45, 0.52), (6, 0.18, 25, 0.4),
                                                     (4, 0.05, 8, 0.28)]):
        for i in range(count):
            a = 2 * math.pi * (i + 0.5 * ring) / count
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
            lf = bpy.context.object
            lf.scale = (size, size * 0.42, size * 0.16)
            for v in lf.data.vertices:                                 # pointed tips
                if v.co.x > 0:
                    k = v.co.x
                    v.co.y *= (1 - 0.8 * k)
                    v.co.z *= (1 - 0.6 * k)
            lf.location = (math.cos(a) * rad, math.sin(a) * rad, 1.1 + 0.08 * ring)
            lf.rotation_euler = (0, -math.radians(tilt), a)
            smooth(lf, 1)
            lf.data.materials.append(leaf)
    bpy.context.scene.render.filepath = os.path.join(OUT, "plant.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    jobs = JOBS or ["bust:0", "bust:-14", "bust:14", "towels", "plates", "plant"]
    for job in jobs:
        kind, _, arg = job.partition(":")
        if kind == "bust":
            bust(arg or "0")
        else:
            {"towels": towels, "plates": plates, "plant": plant}[kind]()
