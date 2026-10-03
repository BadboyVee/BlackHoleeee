"""The sparks: five plush agents for the sparks spot, made like real toys. Each is a soft body in short clumped
fur, with glossy black safety-bead eyes, an embroidered smile, felt cheeks and one accessory for its job; the lead
wears a felt spark on a bent wire. Rendered as sprites with a clear background, one per expression (eyes open, or
stitched closed: happy or asleep), plus each one's shadow on its own, so the film can make them hop.

    python3 blender/sparks.py OUT_DIR [name[:variant] ...] [--preview]
"""
import math
import os
import sys

import bpy
import mathutils

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sparks"
JOBS = [a for a in sys.argv[2:] if not a.startswith("--")]
PREVIEW = "--preview" in sys.argv
SIZE = 400 if PREVIEW else 900


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


# ---------------------------------------------------------------- the studio

def reset(samples=96):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x = r.resolution_y = SIZE
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "16"
    scn.view_settings.view_transform = os.environ.get("VIEW", "Standard")
    if scn.view_settings.view_transform == "AgX":
        scn.view_settings.look = os.environ.get("LOOK", "AgX - Punchy")
    scn.view_settings.exposure = float(os.environ.get("EXPOSURE", "-0.6"))
    c = scn.cycles
    c.device = "CPU"
    c.samples = 24 if PREVIEW else samples
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 6
    c.transparent_max_bounces = 16
    world = bpy.data.worlds.new("w")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*srgb("#f4f5f8"), 1)
    bg.inputs[1].default_value = 0.7


def look_at(o, target):
    d = mathutils.Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def area(name, loc, energy, size, col=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.shape = "DISK"
    d.size = size
    d.color = col
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    look_at(o, (0, 0, 0))
    return o


def stage():
    cd = bpy.data.cameras.new("cam")
    cd.lens = 118
    cd.sensor_width = 36
    o = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(o)
    o.location = (0, -11.5, 2.4)
    look_at(o, (0, 0, 0.32))
    bpy.context.scene.camera = o
    area("key", (-5, -6, 6), 1400, 5.0, srgb("#fff6ec"))
    area("fill", (6, -5, 1.5), 420, 6.0, srgb("#eef3ff"))
    area("rim", (1.5, 6, 5), 900, 3.5)
    area("top", (0, 0, 8), 250, 6.0)


def ground(shadow_only=False):
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, FLOOR))
    g = bpy.context.object
    g.is_shadow_catcher = True
    return g


FLOOR = -0.86


# ---------------------------------------------------------------- materials

def mat(name, col, rough=0.5, metal=0.0, coat=0.0, sheen=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.03
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
        b.inputs["Sheen Tint"].default_value = (1, 1, 1, 1)
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.3, 0.15, 0.1)
    return m


def felt(name, col):
    """Felt: matte, soft sheen, a fine fibrous bump."""
    m = mat(name, col, rough=0.9, sheen=0.8)
    N, L = m.node_tree.nodes, m.node_tree.links
    n = N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 180.0
    n.inputs["Detail"].default_value = 8.0
    b = N.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 0.25
    L.new(n.outputs["Fac"], b.inputs["Height"])
    L.new(b.outputs["Normal"], N["Principled BSDF"].inputs["Normal"])
    return m


def fur_material(col):
    m = bpy.data.materials.new("fur")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N["Principled BSDF"])
    hair = N.new("ShaderNodeBsdfHairPrincipled")
    hair.parametrization = "COLOR"
    hair.inputs["Roughness"].default_value = 0.38
    hair.inputs["Radial Roughness"].default_value = 0.75
    hair.inputs["Coat"].default_value = 0.12
    info = N.new("ShaderNodeHairInfo")
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*[v * 0.70 for v in col], 1)
    ramp.color_ramp.elements[1].color = (*[min(1.0, v * 1.10) for v in col], 1)
    L.new(info.outputs["Random"], ramp.inputs["Fac"])
    # roots a touch darker than the tips, as real pile is
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = (*[v * 0.55 for v in col], 1)
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(info.outputs["Intercept"], inv.inputs[1])
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    L.new(inv.outputs["Value"], pw.inputs[0])
    L.new(pw.outputs["Value"], mix.inputs["Factor"])
    L.new(ramp.outputs["Color"], mix.inputs["A"])
    L.new(mix.outputs["Result"], hair.inputs["Color"])
    L.new(hair.outputs["BSDF"], N["Material Output"].inputs["Surface"])
    return m


# ---------------------------------------------------------------- the body

def body(col, sx=1.0, sy=0.96, sz=0.9, pear=0.08, fur=0.085, count=70000, face_trim=0.45, bald_above=None):
    """A soft body that sits: a sphere, fuller low down, flattened where it rests, in short clumped fur, the pile
    trimmed shorter on the face as real plush is."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0, location=(0, 0, 0))
    o = bpy.context.object
    o.name = "body"
    for v in o.data.vertices:
        x, y, z = v.co
        k = 1.0 + pear * max(0.0, -z)
        v.co = mathutils.Vector((x * sx * k, y * sy * k, z * sz))
        if v.co.z < FLOOR + 0.02:                                  # where it sits, it is flattened
            v.co.z = FLOOR + 0.02 - (FLOOR + 0.02 - v.co.z) * 0.12
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat("skin", tuple(v * 0.75 for v in col), rough=0.95, sheen=0.5))
    o.data.materials.append(fur_material(col))
    # the face: a vertex group for shorter pile
    vg = o.vertex_groups.new(name="pile")
    for v in o.data.vertices:
        d = (mathutils.Vector((v.co.x, v.co.y, v.co.z)).normalized() - mathutils.Vector((0, -1, 0.05)).normalized()).length
        w = 1.0 - (1.0 - face_trim) * max(0.0, 1.0 - d / 0.75)
        if bald_above is not None and v.co.z > bald_above:          # nothing grows under a cap
            w = 0.0
        vg.add([v.index], w, "REPLACE")
    ps = o.modifiers.new("fur", "PARTICLE_SYSTEM").particle_system
    ps.vertex_group_length = "pile"
    s = ps.settings
    s.type = "HAIR"
    s.count = count // (3 if PREVIEW else 1)
    s.hair_length = fur
    s.use_advanced_hair = True
    s.material = 2
    s.child_type = "INTERPOLATED"
    s.child_percent = 4
    s.rendered_child_count = 3 if PREVIEW else 8
    s.clump_factor = 0.25
    s.clump_shape = 0.3
    s.roughness_1 = 0.035
    s.roughness_1_size = 0.4
    s.roughness_endpoint = 0.025
    s.roughness_2 = 0.04
    s.roughness_2_size = 1.0
    s.root_radius = 1.0
    s.tip_radius = 0.0
    s.radius_scale = 0.0045
    s.use_close_tip = True
    s.display_step = 3
    s.render_step = 3
    s.hair_step = 4
    s.use_hair_bspline = True
    return o


def surface(o, direction):
    """Where a ray from inside the body along direction meets its surface."""
    d = mathutils.Vector(direction).normalized()
    ok, loc, nrm, idx = o.ray_cast(d * 3.0, -d)
    return loc, nrm


def place(obj, loc, nrm, out=0.0):
    obj.location = loc + nrm * out
    obj.rotation_euler = nrm.to_track_quat("Z", "Y").to_euler()


# ---------------------------------------------------------------- faces

EYE_Y, EYE_X, EYE_R = 0.10, 0.30, 0.125


def bead_eyes(o, spread=EYE_X, height=EYE_Y, r=EYE_R):
    m = mat("bead", srgb("#0b0b0d"), rough=0.04, coat=1.0)
    for sx in (-1, 1):
        loc, nrm = surface(o, (sx * spread, -1.0, height))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=r)
        e = bpy.context.object
        e.scale = (1, 1, 0.62)
        place(e, loc, nrm, out=-r * 0.12)
        bpy.ops.object.shade_smooth()
        e.data.materials.append(m)


def stitched(o, kind, spread=EYE_X, height=EYE_Y, r=EYE_R):
    """Eyes stitched shut in thread: happy (arcs up) or asleep (arcs down)."""
    m = mat("thread", srgb("#1a1414"), rough=0.7, sheen=0.4)
    for sx in (-1, 1):
        loc, nrm = surface(o, (sx * spread, -1.0, height - 0.02))
        arc(loc, nrm, r * 0.95, up=(kind == "happy"), thick=0.024, material=m)


def arc(loc, nrm, radius, up=True, thick=0.02, material=None, span=150.0):
    """A stitched arc lying on the surface at loc, facing along nrm: a bent thick thread."""
    cu = bpy.data.curves.new("arc", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = thick
    cu.bevel_resolution = 4
    sp = cu.splines.new("POLY")
    n = 16
    sp.points.add(n - 1)
    a0 = math.radians(90 - span / 2)
    for i in range(n):
        a = a0 + math.radians(span) * i / (n - 1)
        x = radius * math.cos(a)
        y = radius * math.sin(a) * (1 if up else -1) - (radius * 0.55 if up else -radius * 0.55)
        sp.points[i].co = (x, y, 0.0, 1)
    ob = bpy.data.objects.new("arc", cu)
    bpy.context.collection.objects.link(ob)
    ob.location = loc + nrm * 0.035
    # lay the arc in the surface's tangent plane, upright to the world
    z = nrm.normalized()
    x = mathutils.Vector((0, 0, 1)).cross(z).normalized()
    if x.length < 1e-3:
        x = mathutils.Vector((1, 0, 0))
    y = z.cross(x)
    ob.matrix_world = mathutils.Matrix((
        (x.x, y.x, z.x, ob.location.x), (x.y, y.y, z.y, ob.location.y), (x.z, y.z, z.z, ob.location.z), (0, 0, 0, 1)))
    ob.scale = (-1, 1, 1)
    if material:
        ob.data.materials.append(material)
    return ob


def smile(o, height=-0.16, width=0.16):
    m = mat("thread", srgb("#1a1414"), rough=0.7, sheen=0.4)
    loc, nrm = surface(o, (0, -1.0, height))
    arc(loc, nrm, width, up=False, thick=0.02, material=m, span=120.0)


def cheeks(o, spread=0.52, height=-0.08, col="#ff8fa3"):
    m = felt("cheek", srgb(col))
    for sx in (-1, 1):
        loc, nrm = surface(o, (sx * spread, -1.0, height))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1)
        ch = bpy.context.object
        ch.scale = (1.25, 0.9, 0.25)
        place(ch, loc, nrm, out=0.035)
        bpy.ops.object.shade_smooth()
        ch.data.materials.append(m)


def face(o, variant, **kw):
    if variant == "open":
        bead_eyes(o, **kw)
    else:
        stitched(o, variant, **kw)
    smile(o)
    cheeks(o)


# ---------------------------------------------------------------- accessories

def spark(loc, size, material, rays=8, rot=0.0):
    """A felt spark: rounded rays of two lengths around a centre."""
    parts = []
    for i in range(rays):
        a = rot + 2 * math.pi * i / rays
        L = size * (1.0 if i % 2 == 0 else 0.68)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
        r = bpy.context.object
        r.scale = (L * 0.5, size * 0.13, size * 0.1)
        r.location = (loc[0] + math.cos(a) * L * 0.5, loc[1], loc[2] + math.sin(a) * L * 0.5)
        r.rotation_euler = (0, -a, 0)
        bpy.ops.object.shade_smooth()
        r.data.materials.append(material)
        parts.append(r)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size * 0.2, location=loc)
    c = bpy.context.object
    c.scale = (1, 0.6, 1)
    bpy.ops.object.shade_smooth()
    c.data.materials.append(material)
    return parts


def wire(points, radius, material):
    cu = bpy.data.curves.new("wire", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new("wire", cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def lead(variant):
    """Terracotta, a cream felt spark on a bent wire."""
    o = body(srgb("#d9774f"))
    face(o, variant)
    stem = felt("stem", srgb("#8a4a32"))
    top = o.ray_cast((0, 0, 3), (0, 0, -1))[1]
    wire([(top.x, top.y, top.z - 0.05), (0.06, 0.0, top.z + 0.3), (0.26, -0.02, top.z + 0.55)], 0.03, stem)
    spark((0.3, -0.03, top.z + 0.72), 0.34, felt("spark", srgb("#f6efe4")), rot=0.2)


def builder(variant):
    """Mint, in a yellow hard hat."""
    o = body(srgb("#57c8a0"), sz=0.92)
    face(o, variant)
    hat = mat("hat", srgb("#ffc21a"), rough=0.28, coat=0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.8, location=(0, 0.02, 0.5))
    d = bpy.context.object
    d.scale = (1.0, 1.0, 0.8)
    for v in d.data.vertices:                                       # a dome: nothing below its rim
        if v.co.z < 0:
            v.co.z = 0
    bpy.ops.object.shade_smooth()
    d.data.materials.append(hat)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.98, depth=0.05, location=(0, -0.06, 0.5))
    b = bpy.context.object
    b.scale = (1.0, 1.12, 1.0)
    b.rotation_euler = (math.radians(-7), 0, 0)
    bev = b.modifiers.new("b", "BEVEL")
    bev.width = 0.02
    bev.segments = 3
    bpy.ops.object.shade_smooth()
    b.data.materials.append(hat)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.02, 0.98))
    ridge = bpy.context.object
    ridge.scale = (0.14, 1.3, 0.1)
    bev = ridge.modifiers.new("b", "BEVEL")
    bev.width = 0.05
    bev.segments = 4
    sub = ridge.modifiers.new("s", "SUBSURF")
    sub.levels = sub.render_levels = 2
    ridge.data.materials.append(hat)
    sw = ridge.modifiers.new("fit", "SHRINKWRAP")
    sw.target = d
    sw.wrap_mode = "OUTSIDE_SURFACE"
    sw.offset = 0.04


def talker(variant):
    """Butter yellow, in a headset with a boom mic."""
    o = body(srgb("#ffcf5a"), sy=0.98)
    face(o, variant)
    plastic = mat("headset", srgb("#26262b"), rough=0.35, coat=0.3)
    cushion = mat("cushion", srgb("#3a3a42"), rough=0.8, sheen=0.3)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.02, minor_radius=0.055, major_segments=96, minor_segments=16,
                                     location=(0, 0.05, 0.05))
    band = bpy.context.object
    band.rotation_euler = (math.radians(90), 0, 0)
    band.scale = (1.0, 1.02, 1.0)
    for v in band.data.vertices:                                    # keep the arch over the top
        if v.co.y < -0.05:
            v.co.y = -0.05
    band.data.materials.append(plastic)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.27, depth=0.22, location=(sx * 1.02, 0.05, 0.0))
        cup = bpy.context.object
        cup.rotation_euler = (0, math.radians(90), 0)
        bev = cup.modifiers.new("b", "BEVEL")
        bev.width = 0.06
        bev.segments = 5
        bpy.ops.object.shade_smooth()
        cup.data.materials.append(plastic)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.07, location=(sx * 0.9, 0.05, 0.0))
        cu = bpy.context.object
        cu.rotation_euler = (0, math.radians(90), 0)
        cu.data.materials.append(cushion)
    wire([(-1.0, -0.12, -0.05), (-0.85, -0.7, -0.35), (-0.42, -1.02, -0.36)], 0.028, plastic)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(-0.36, -1.04, -0.35))
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(cushion)


def reader(variant):
    """Lavender, in round gold wire glasses."""
    o = body(srgb("#a78bfa"), sx=0.98, sz=0.94, pear=0.12)
    face(o, variant)
    gold = mat("gold", srgb("#c9a14a"), rough=0.2, metal=1.0)
    lens = mat("lens", (1, 1, 1), rough=0.0)
    lens.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
    lens.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.2
    for sx in (-1, 1):
        loc, nrm = surface(o, (sx * EYE_X, -1.0, EYE_Y))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.017, major_segments=64, minor_segments=12)
        rim = bpy.context.object
        place(rim, loc, nrm, out=0.16)
        rim.data.materials.append(gold)
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.195, depth=0.01)
        ln = bpy.context.object
        place(ln, loc, nrm, out=0.16)
        ln.data.materials.append(lens)
        loc2, nrm2 = surface(o, (sx * 0.95, -0.2, EYE_Y + 0.05))
        wire([tuple(loc + nrm * 0.16 + mathutils.Vector((sx * 0.19, 0, 0))), tuple(loc2 + nrm2 * 0.05)], 0.012, gold)
    l1, n1 = surface(o, (-0.1, -1.0, EYE_Y + 0.02))
    l2, n2 = surface(o, (0.1, -1.0, EYE_Y + 0.02))
    wire([tuple(l1 + n1 * 0.17), (0, l1.y - 0.2, l1.z + 0.05), tuple(l2 + n2 * 0.17)], 0.012, gold)


def sleeper(variant):
    """Deep indigo, in a knitted nightcap that flops over, with a pompom."""
    o = body(srgb("#4f5bd5"), sz=0.88, bald_above=0.36)
    face(o, variant)
    knit = felt("knit", srgb("#eef1ff"))
    stripe = felt("stripe", srgb("#8fa3ff"))
    pom = felt("pom", srgb("#ffd23f"))
    # the cap: a cone seated over the crown, its top half bent over to one side, in bands
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.96, radius2=0.06, depth=1.5, end_fill_type="NOTHING",
                                    location=(0, 0, 0.0))
    cap = bpy.context.object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=14)
    bpy.ops.object.mode_set(mode="OBJECT")
    tip_i = max(range(len(cap.data.vertices)), key=lambda i: cap.data.vertices[i].co.z)
    for v in cap.data.vertices:
        h = max(0.0, ((v.co.z + 0.75) / 1.5 - 0.3) / 0.7)
        v.co.x += 1.15 * h ** 1.7
        v.co.z -= 0.95 * h ** 2.1
    cap.location = (0, 0.02, 0.36 + 0.75)
    bpy.ops.object.shade_smooth()
    cap.data.materials.append(knit)
    cap.data.materials.append(stripe)
    for p in cap.data.polygons:
        z = sum(cap.data.vertices[i].co.z for i in p.vertices) / len(p.vertices)
        p.material_index = 1 if int((z + 1.0) * 6) % 2 else 0
    bpy.ops.mesh.primitive_torus_add(major_radius=0.93, minor_radius=0.14, major_segments=96, minor_segments=24,
                                     location=(0, 0.02, 0.4))
    brim = bpy.context.object
    brim.scale = (1.0, 1.0, 0.8)
    brim.data.materials.append(knit)
    tip = cap.matrix_world @ cap.data.vertices[tip_i].co
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.18, location=tip)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(pom)


CAST = {"lead": lead, "builder": builder, "talker": talker, "reader": reader, "sleeper": sleeper}
VARIANTS = {"lead": ["open", "happy"], "builder": ["open", "happy"], "talker": ["open", "happy"],
            "reader": ["open", "happy"], "sleeper": ["open", "asleep"]}


def render(name, variant):
    reset()
    stage()
    CAST[name](variant)
    bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}_{variant}.png")
    bpy.ops.render.render(write_still=True)


def render_shadow(name):
    """Only the shadow it casts on the floor: the toy itself hidden from the camera."""
    reset(samples=48)
    stage()
    CAST[name]("open")
    for ob in list(bpy.context.scene.objects):
        if ob.type in ("MESH", "CURVE"):
            ob.visible_camera = False
    ground()
    bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}_shadow.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    jobs = JOBS or [f"{n}:{v}" for n in CAST for v in VARIANTS[n] + ["shadow"]]
    for job in jobs:
        name, _, variant = job.partition(":")
        variant = variant or "open"
        if variant == "shadow":
            render_shadow(name)
        else:
            render(name, variant)
