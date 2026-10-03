"""HORIZON's devices as real hardware: a phone in black titanium and a laptop in aluminium, each rendered from the
front with its screen cut out (a holdout), so the film can play its own screen behind the glass and lay the
render over it. The geometry follows horizon/devices.py, so the cut-out falls exactly where the film draws.

Run with the `bpy` module (pip install bpy==4.2.0):
    python3 blender/devices.py OUT_DIR [phone|laptop|all] [--preview]
"""
import json
import math
import os
import sys

import bpy
import bmesh
from bpy_extras.object_utils import world_to_camera_view

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/devices"
WHICH = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "all"
PREVIEW = "--preview" in sys.argv
PX = 6.0 if PREVIEW else 14.0                 # pixels per millimetre (the phone; the laptop gets half)

# the film's proportions (horizon/devices.py), in millimetres for a phone 71.5 mm wide
PHONE_W = 71.5
PHONE_H = PHONE_W * 860 / 420
PHONE_R = 68.0 / 440 * PHONE_W
PHONE_B = 12.0 / 440 * PHONE_W
PHONE_T = 8.25
MARGIN = 3.0                                  # room round the body for the buttons
# the laptop's lid, 312 mm wide
LAP_W = 312.0
LAP_H = LAP_W * 0.64
LAP_R = LAP_W * 0.022
LAP_B = LAP_W * 0.022


def reset(w_mm, h_mm, samples=96, px=PX):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = int(round(w_mm * px)), int(round(h_mm * px))
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "16"
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    c = scn.cycles
    c.device = "CPU"
    c.samples = 24 if PREVIEW else samples
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    # a studio for the reflections: a soft grey room, bright overhead, darker below
    world = bpy.data.worlds.new("studio")
    scn.world = world
    world.use_nodes = True
    N, L = world.node_tree.nodes, world.node_tree.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.30, (0.20, 0.21, 0.23, 1)           # a light room, so aluminium reads as silver
    e[1].position, e[1].color = 0.75, (0.85, 0.86, 0.90, 1)
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], N["Background"].inputs["Color"])
    N["Background"].inputs["Strength"].default_value = 0.8


def softbox(name, loc, rot, radiance, size, sy=None):
    """An area light by how bright it looks (its radiance), since its size is what the metal reflects."""
    d = bpy.data.lights.new(name, "AREA")
    d.energy = radiance * math.pi * size * (sy or size)
    d.shape = "RECTANGLE"
    d.size = size
    d.size_y = sy or size
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    return o


def mat(name, col, rough, metal=0.0, coat=0.0, aniso=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Anisotropic"].default_value = aniso
    return m


def holdout(name="screen"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N["Principled BSDF"])
    L.new(N.new("ShaderNodeHoldout").outputs[0], N["Material Output"].inputs["Surface"])
    return m


def rounded_rect(name, w, h, r, z0, z1, segs=24, bevel=0.0, bevel_segs=6):
    """A rounded rectangle prism, centred on x, y, from z0 to z1, optionally with its edges rounded over."""
    bm = bmesh.new()
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for k in range(segs + 1):
            a = math.radians(a0 + 90 * k / segs)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    bottom = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(bottom[::-1])
    bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    if bevel > 0:
        bv = o.modifiers.new("bevel", "BEVEL")
        bv.width = bevel
        bv.segments = bevel_segs
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(50)
        bv.harden_normals = True
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def ortho_camera(w_mm, h_mm, tilt=0.0, dist=500.0, target=(0, 0, 0)):
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = max(w_mm, h_mm)
    cd.sensor_fit = "AUTO"
    cd.clip_end = 5000
    o = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(o)
    t = math.radians(tilt)
    o.location = (target[0], target[1] - dist * math.sin(t), target[2] + dist * math.cos(t))
    o.rotation_euler = (t, 0, 0)
    bpy.context.scene.camera = o
    return o


def write_rects(name, rects):
    """Where each named rectangle (four world corners) lands in the picture, in pixels: (x, y, w, h)."""
    scn = bpy.context.scene
    bpy.context.view_layer.update()                                   # so the camera's matrix is where we put it
    W, H = scn.render.resolution_x, scn.render.resolution_y
    out = {"size": [W, H]}
    for key, corners in rects.items():
        pts = [world_to_camera_view(scn, scn.camera, mathutils_vec(c)) for c in corners]
        xs = [p.x * W for p in pts]
        ys = [(1 - p.y) * H for p in pts]
        out[key] = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
    with open(os.path.join(OUT, f"{name}.json"), "w") as f:
        json.dump(out, f)


def mathutils_vec(c):
    import mathutils
    return mathutils.Vector(c)


def phone():
    """Face up, seen from straight above: the black titanium band rounded over at its edges, the black glass, the
    screen cut out, the buttons standing proud of the sides."""
    w, h = PHONE_W + 2 * MARGIN, PHONE_H + 2 * MARGIN
    reset(w, h)
    titanium = mat("titanium", (0.09, 0.09, 0.10), 0.26, metal=1.0, aniso=0.3)
    glass = mat("glass", (0.004, 0.004, 0.005), 0.04, coat=1.0)
    rounded_rect("band", PHONE_W, PHONE_H, PHONE_R, -PHONE_T, 0.0, bevel=1.4).data.materials.append(titanium)
    g = rounded_rect("glass", PHONE_W - 1.0, PHONE_H - 1.0, PHONE_R - 0.5, -0.4, 0.25, bevel=0.35, bevel_segs=4)
    g.data.materials.append(glass)
    s = rounded_rect("screen", PHONE_W - 2 * PHONE_B, PHONE_H - 2 * PHONE_B, PHONE_R - PHONE_B, 0.26, 0.27)
    s.data.materials.append(holdout())
    for side, y0, length in ((-1, 30.0, 6.0), (-1, 17.0, 10.5), (-1, 4.0, 10.5), (1, 12.0, 16.0), (1, -24.0, 8.0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(side * (PHONE_W / 2 + 0.35), y0, -PHONE_T / 2))
        btn = bpy.context.object
        btn.scale = (1.2, length, 3.2)
        bv = btn.modifiers.new("bevel", "BEVEL")
        bv.width = 0.5
        bv.segments = 4
        btn.data.materials.append(titanium)
    # the studio: a long soft strip high on the left that runs down the band, a key, a kicker on the right
    softbox("strip", (-90, 40, 160), (0, -30, 0), 9.0, 40, 400)
    softbox("key", (60, 120, 220), (-25, 15, 0), 4.0, 160).visible_glossy = False   # no hard edge in the glass
    softbox("kick", (140, -60, 60), (40, 60, 0), 5.0, 60, 300)
    ortho_camera(w, h)
    write_rects("phone", {"body": [(-PHONE_W / 2, -PHONE_H / 2, 0), (PHONE_W / 2, PHONE_H / 2, 0)]})
    bpy.context.scene.render.filepath = os.path.join(OUT, "phone.png")
    bpy.ops.render.render(write_still=True)


def laptop():
    """Open, seen from the front and a little above: the aluminium lid with its black glass bezel and the screen
    cut out, the notch, and the deck below it with the keyboard in shadow."""
    tilt = 5.0                                                        # seen from a little above...
    deck_d = 221.0
    w, h = LAP_W * 1.1, LAP_H + 52.0
    reset(w, h, px=PX / 2)
    alu = mat("aluminium", (0.80, 0.81, 0.83), 0.32, metal=1.0, aniso=0.2)
    glass = mat("bezel", (0.004, 0.004, 0.005), 0.05, coat=1.0)
    keys = mat("keys", (0.012, 0.012, 0.014), 0.55)
    lid = rounded_rect("lid", LAP_W, LAP_H, LAP_R, -6.0, 0.0, bevel=1.2)
    lid.data.materials.append(alu)
    bz = rounded_rect("bezel", LAP_W - 2.0, LAP_H - 2.0, LAP_R - 1.0, -0.5, 0.3, bevel=0.3, bevel_segs=3)
    bz.data.materials.append(glass)
    scr = rounded_rect("screen", LAP_W - 2 * LAP_B, LAP_H - 2 * LAP_B - LAP_W * 0.008, LAP_R * 0.4, 0.31, 0.32)
    for v in scr.data.vertices:                                       # the chin is a little deeper than the brow
        v.co.y += LAP_W * 0.004
    scr.data.materials.append(holdout())
    lid_parts = [lid, bz, scr]
    # the deck: hinged at the lid's bottom edge, lying flat toward the viewer
    deck = rounded_rect("deck", LAP_W, deck_d, LAP_R * 1.4, -15.5, 0.0, bevel=2.5)
    deck.data.materials.append(alu)
    well = rounded_rect("keys", LAP_W * 0.86, deck_d * 0.42, 4.0, -0.6, 0.05)
    well.data.materials.append(keys)
    well.location = (0, deck_d * 0.16, 0)
    pad = rounded_rect("pad", LAP_W * 0.42, deck_d * 0.36, 5.0, -0.25, 0.02)
    pad.data.materials.append(mat("pad", (0.70, 0.71, 0.73), 0.45, metal=1.0))
    pad.location = (0, -deck_d * 0.26, 0)
    base = [deck, well, pad]
    # stand the lid up (it faces -y, the viewer) and lay the deck in front of it
    lean = math.radians(tilt)                                         # ...so the lid, leaning back as far, faces us square
    for o in lid_parts:
        o.rotation_euler = (math.pi / 2 - lean, 0, 0)
        o.location = (0, LAP_H / 2 * math.sin(lean), LAP_H / 2 * math.cos(lean))
    for o in base:
        o.location = (o.location.x, -deck_d / 2 - 2.0 + o.location.y, o.location.z - 1.0)
    softbox("key", (-160, -260, 320), (40, 0, -20), 3.0, 300).visible_glossy = False
    softbox("strip", (200, -200, 120), (60, 0, 35), 6.0, 60, 500)
    softbox("top", (0, 80, 420), (0, 0, 0), 2.0, 400, 200)
    ortho_camera(w, h, tilt=90 - tilt, target=(0, -12, LAP_H * 0.40))
    c, sn = math.cos(lean), math.sin(lean)
    write_rects("laptop", {"lid": [(-LAP_W / 2, 0, 0), (LAP_W / 2, LAP_H * sn, LAP_H * c)]})
    bpy.context.scene.render.filepath = os.path.join(OUT, "laptop.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if WHICH in ("phone", "all"):
        phone()
    if WHICH in ("laptop", "all"):
        laptop()
