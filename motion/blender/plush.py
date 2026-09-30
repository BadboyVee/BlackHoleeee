"""Plush agents for the Claude Code spot: soft round toys in fur, each with its own accessory, rendered as sprites
with a clear background (the film draws their faces, so they can blink and talk, and their shadows).

    python3 blender/plush.py OUT_DIR [name ...] [--preview]
"""
import math
import os
import sys

import bpy

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/plush"
NAMES = [a for a in sys.argv[2:] if not a.startswith("--")]
PREVIEW = "--preview" in sys.argv
SIZE = 360 if PREVIEW else 720


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x = r.resolution_y = SIZE
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    scn.view_settings.view_transform = "Standard"
    c = scn.cycles
    c.device = "CPU"
    c.samples = 24 if PREVIEW else 64
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    world = bpy.data.worlds.new("w")
    scn.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.55


def material(name, col, rough=0.5, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    return m


def fur_material(col):
    m = bpy.data.materials.new("fur")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N["Material Output"]
    N.remove(N["Principled BSDF"])
    hair = N.new("ShaderNodeBsdfHairPrincipled")
    hair.parametrization = "COLOR"
    hair.inputs["Color"].default_value = (*col, 1)
    hair.inputs["Roughness"].default_value = 0.45
    hair.inputs["Radial Roughness"].default_value = 0.8
    hair.inputs["Coat"].default_value = 0.15
    # a little variation from strand to strand
    info = N.new("ShaderNodeHairInfo")
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*[v * 0.72 for v in col], 1)
    ramp.color_ramp.elements[1].color = (*[min(1.0, v * 1.12) for v in col], 1)
    L.new(info.outputs["Random"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], hair.inputs["Color"])
    L.new(hair.outputs["BSDF"], out.inputs["Surface"])
    return m


def body(col, sx=1.0, sy=1.0, sz=0.92, fur=0.09, count=90000):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(0, 0, 0))
    o = bpy.context.object
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    for v in o.data.vertices:                          # a touch fuller low down, like a toy that sits
        k = 1.0 + 0.06 * max(0.0, -v.co.z)
        v.co.x *= k
        v.co.y *= k
    bpy.ops.object.shade_smooth()
    skin = material("skin", tuple(v * 0.8 for v in col), rough=0.9)
    o.data.materials.append(skin)
    o.data.materials.append(fur_material(col))
    ps = o.modifiers.new("fur", "PARTICLE_SYSTEM").particle_system
    s = ps.settings
    s.type = "HAIR"
    s.count = count // (2 if PREVIEW else 1)
    s.hair_length = fur
    s.use_advanced_hair = True
    s.material = 2
    s.child_type = "INTERPOLATED"
    s.child_percent = 3
    s.rendered_child_count = 6 if not PREVIEW else 3
    s.child_length = 1.0
    s.roughness_1 = 0.02
    s.roughness_2 = 0.03
    s.root_radius = 1.0
    s.tip_radius = 0.0
    s.radius_scale = 0.006
    s.display_step = 3
    s.render_step = 3
    s.hair_step = 4
    s.use_hair_bspline = True
    return o


def light(kind, loc, energy, size=2.0, rot=(0, 0, 0), col=(1, 1, 1)):
    d = bpy.data.lights.new(kind, "AREA")
    d.energy = energy
    d.size = size
    d.color = col
    o = bpy.data.objects.new(kind, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    look(o, (0, 0, 0))
    return o


def look(o, target):
    import mathutils
    d = mathutils.Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera():
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = 3.0
    o = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(o)
    o.location = (0, -10, 0.25)
    look(o, (0, 0, 0.1))
    bpy.context.scene.camera = o


def stage():
    camera()
    light("key", (-4, -5, 5), 900, 4.0, col=(1.0, 0.97, 0.93))
    light("fill", (5, -4, 1), 300, 5.0, col=(0.92, 0.95, 1.0))
    light("rim", (2, 5, 4), 500, 3.0)


# ---------------------------------------------------------------- the cast

def fixer():
    """Coral, in a yellow hard hat."""
    body(srgb("#e0785a"))
    hat = material("hat", srgb("#ffc21a"), rough=0.35, coat=0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.78, location=(0, 0, 0.62))
    dome = bpy.context.object
    dome.scale = (1.0, 1.0, 0.78)
    bpy.ops.object.shade_smooth()
    dome.data.materials.append(hat)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.98, depth=0.06, location=(0, -0.05, 0.62))
    brim = bpy.context.object
    brim.rotation_euler = (math.radians(-8), 0, 0)
    bpy.ops.object.shade_smooth()
    brim.data.materials.append(hat)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.9, location=(0, 0, 1.0))
    ridge = bpy.context.object
    ridge.rotation_euler = (0, math.radians(90), 0)
    ridge.scale = (1, 0.5, 1)
    ridge.data.materials.append(hat)


def tester():
    """Mint, safety goggles pushed up on its head."""
    body(srgb("#5fd3a3"), sz=0.95)
    band = material("band", srgb("#2b2b33"), rough=0.6)
    lens = material("lens", srgb("#9fd8ff"), rough=0.05, coat=1.0)
    frame = material("frame", srgb("#ff8a3d"), rough=0.4)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.02, minor_radius=0.05, location=(0, 0, 0.42))
    t = bpy.context.object
    t.rotation_euler = (math.radians(12), 0, 0)
    t.data.materials.append(band)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.26, depth=0.16, location=(sx * 0.3, -0.9, 0.62))
        f = bpy.context.object
        f.rotation_euler = (math.radians(80), 0, 0)
        bpy.ops.object.shade_smooth()
        f.data.materials.append(frame)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(sx * 0.3, -0.98, 0.64))
        l = bpy.context.object
        l.scale = (1, 0.45, 1)
        bpy.ops.object.shade_smooth()
        l.data.materials.append(lens)


def reader():
    """Lavender, square reading glasses low on its nose."""
    body(srgb("#b69cff"))
    rim = material("rim", srgb("#1e1e24"), rough=0.3, coat=0.5)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.035, location=(sx * 0.3, -1.04, -0.12))
        g = bpy.context.object
        g.rotation_euler = (math.radians(90), 0, 0)
        g.scale = (1.15, 1, 0.85)
        g.data.materials.append(rim)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.2, location=(0, -1.06, -0.1))
    br = bpy.context.object
    br.rotation_euler = (0, math.radians(90), 0)
    br.data.materials.append(rim)


def planner():
    """Sky blue, in a striped propeller beanie."""
    body(srgb("#58b4ff"), sz=0.9)
    cap = [material("c0", srgb("#ff4f6d"), 0.55), material("c1", srgb("#ffd23f"), 0.45, coat=0.4),
           material("c2", srgb("#3ecf8e"), 0.45, coat=0.4)]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.86, location=(0, 0, 0.42))
    b = bpy.context.object
    b.scale = (1.04, 1.04, 0.74)
    bpy.ops.object.shade_smooth()
    b.data.materials.append(cap[0])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.88, minor_radius=0.07, location=(0, 0, 0.44))
    bpy.context.object.data.materials.append(cap[1])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.2, location=(0, 0, 1.13))
    bpy.context.object.data.materials.append(cap[1])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(0, 0, 1.24))
    bpy.context.object.data.materials.append(cap[1])
    for k in range(2):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.23))
        p = bpy.context.object
        p.scale = (0.62, 0.12, 0.025)
        p.rotation_euler = (math.radians(12), 0, math.radians(90 * k + 25))
        bev = p.modifiers.new("b", "BEVEL")
        bev.width = 0.04
        bev.segments = 3
        p.data.materials.append(cap[2 if k else 1])


def nightowl():
    """Indigo, in a periwinkle nightcap with a yellow pompom."""
    body(srgb("#5a5fd6"))
    cap = material("cap", srgb("#9fb4ff"), 0.85)
    band = material("band", srgb("#eef1ff"), 0.9)
    pom = material("pom", srgb("#ffd23f"), 0.9)
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.9, radius2=0.08, depth=1.05, location=(0.26, 0, 0.9))
    c = bpy.context.object
    c.rotation_euler = (0, math.radians(38), 0)
    bpy.ops.object.shade_smooth()
    c.data.materials.append(cap)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.17, location=(0.62, 0, 1.3))
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(pom)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.1, location=(0.03, 0, 0.44))
    r = bpy.context.object
    r.rotation_euler = (0, math.radians(8), 0)
    r.scale = (1, 1, 0.8)
    r.data.materials.append(band)


CAST = {"fixer": fixer, "tester": tester, "reader": reader, "planner": planner, "nightowl": nightowl}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name in NAMES or list(CAST):
        reset()
        stage()
        CAST[name]()
        bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}.png")
        bpy.ops.render.render(write_still=True)
