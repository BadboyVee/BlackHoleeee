"""Preview rendering helpers: quick neutral studio + standard views.

Used by every module's self-test and by the critics.  Keep previews cheap:
this machine has 4 CPU cores and no GPU.
"""
import math, os
import bpy
from mathutils import Vector
from . import util

VIEWS = {
    # name: (camera position, target, lens mm)   [+X forward, +Y left]
    "front34": ((5.6, 4.2, 1.55), (0.15, 0.0, 0.52), 60),
    "rear34": ((-5.6, 4.4, 1.9), (-0.15, 0.0, 0.52), 60),
    "front34_low": ((5.2, -3.4, 0.55), (0.2, 0.0, 0.55), 50),
    "side": ((0.0, 9.5, 0.75), (0.0, 0.0, 0.60), 85),
    "front": ((9.0, 0.0, 0.75), (0.0, 0.0, 0.58), 85),
    "rear": ((-9.0, 0.0, 0.8), (0.0, 0.0, 0.58), 85),
    "top": ((0.0, 0.0, 11.0), (0.0, 0.0, 0.0), 85),
    "high34": ((4.6, 3.6, 3.6), (0.0, 0.0, 0.45), 55),
}

ORTHO = {
    # name: (direction the camera looks FROM, ortho scale, centre)
    "ortho_side": ((0, 1, 0), 5.2, (0.075, 0, 0.60)),     # sees the LEFT side, nose to the right? see note
    "ortho_top": ((0, 0, 1), 5.2, (0.075, 0, 0.0)),
    "ortho_front": ((1, 0, 0), 2.6, (0, 0, 0.60)),
    "ortho_rear": ((-1, 0, 0), 2.6, (0, 0, 0.60)),
}


def setup_cycles(scene, samples=24, res=(960, 540), denoise=True, threads=0, transparent=False):
    r = scene.render
    r.engine = 'CYCLES'
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.film_transparent = transparent
    if threads:
        r.threads_mode = 'FIXED'
        r.threads = threads
    c = scene.cycles
    c.device = 'CPU'
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.adaptive_min_samples = min(8, samples)
    c.use_denoising = denoise
    if denoise:
        c.denoiser = 'OPENIMAGEDENOISE'
    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 4
    c.transmission_bounces = 6
    c.transparent_max_bounces = 8
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.image_settings.file_format = 'PNG'
    return scene


def quick_studio(scene, floor=True, strength=1.0):
    """Neutral soft studio for part previews (grey cyc floor, big top softbox, two strips)."""
    col = util.get_collection("PREVIEW_Studio")
    w = scene.world or bpy.data.worlds.new("PreviewWorld")
    scene.world = w
    bg = next((n for n in w.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'), None)
    if bg:
        bg.inputs['Color'].default_value = (0.020, 0.021, 0.024, 1)
        bg.inputs['Strength'].default_value = 1.0 * strength

    def area(name, loc, size, energy, target=(0, 0, 0.5), colour=(1, 1, 1)):
        l = bpy.data.lights.new(name, 'AREA')
        l.shape = 'RECTANGLE'
        l.size, l.size_y = size
        l.energy = energy * strength
        l.color = colour
        o = bpy.data.objects.new(name, l)
        col.objects.link(o)
        o.location = loc
        util.look_at(o, target)
        return o

    area("PV_Top", (0, 0, 5.0), (7.0, 3.2), 520)
    area("PV_Left", (0.5, 6.0, 2.2), (8.0, 1.6), 360)
    area("PV_Right", (0.5, -6.0, 2.2), (8.0, 1.6), 240)
    area("PV_Front", (7.5, 0.0, 2.0), (1.5, 5.0), 180)
    area("PV_Rear", (-7.5, 0.0, 2.2), (1.5, 5.0), 180)
    if floor:
        fl = util.mesh_object("PV_Floor", [(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)],
                              [(0, 1, 2, 3)], collection=col, smooth=False)
        m = bpy.data.materials.new("PV_FloorMat")
        b = next(n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
        b.inputs['Base Color'].default_value = (0.10, 0.10, 0.105, 1)
        b.inputs['Roughness'].default_value = 0.35
        fl.data.materials.append(m)
    return col


def camera(scene, name="PV_Cam"):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
        scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.clip_start = 0.02
    cam.data.clip_end = 200
    return cam


def render_view(scene, path, pos, target, lens=60, ortho_scale=None):
    cam = camera(scene)
    cam.location = pos
    util.look_at(cam, target)
    if ortho_scale:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho_scale
    else:
        cam.data.type = 'PERSP'
        cam.data.lens = lens
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def render_views(scene, out_dir, names=("front34", "rear34", "side"), prefix="", offset=(0, 0, 0)):
    """Render named perspective views from VIEWS. offset shifts cam+target (for single parts)."""
    os.makedirs(out_dir, exist_ok=True)
    out = []
    o = Vector(offset)
    for n in names:
        pos, tgt, lens = VIEWS[n]
        out.append(render_view(scene, os.path.join(out_dir, f"{prefix}{n}.png"),
                               tuple(Vector(pos) + o), tuple(Vector(tgt) + o), lens))
    return out


def render_ortho(scene, out_dir, which=("ortho_side", "ortho_top", "ortho_front", "ortho_rear"), prefix=""):
    """Orthographic views framed like the blueprint (nose to the right in side/top)."""
    os.makedirs(out_dir, exist_ok=True)
    out = []
    for n in which:
        d, scale, c = ORTHO[n]
        cam = camera(scene)
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = scale
        c = Vector(c)
        if n == "ortho_side":
            # look along +Y from the -Y side so that +X (nose) is on the right of the image
            cam.location = c + Vector((0, -20, 0))
            cam.rotation_euler = (math.radians(90), 0, 0)
        elif n == "ortho_top":
            cam.location = c + Vector((0, 0, 20))
            cam.rotation_euler = (0, 0, 0)                 # +X right, +Y up
        elif n == "ortho_front":
            cam.location = c + Vector((20, 0, 0))
            cam.rotation_euler = (math.radians(90), 0, math.radians(90))
        else:
            cam.location = c + Vector((-20, 0, 0))
            cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
        scene.render.filepath = os.path.join(out_dir, f"{prefix}{n}.png")
        bpy.ops.render.render(write_still=True)
        out.append(scene.render.filepath)
    return out


def part_camera_views(scene, out_dir, centre, radius, prefix="", names=("a", "b", "c"), lens=70):
    """Three views orbiting a single part: front-left, rear-left, top-ish."""
    os.makedirs(out_dir, exist_ok=True)
    c = Vector(centre)
    d = radius * 3.2
    table = {
        "a": Vector((0.72, 0.62, 0.32)), "b": Vector((-0.72, 0.62, 0.32)),
        "c": Vector((0.35, 0.25, 0.9)), "d": Vector((0.0, 1.0, 0.05)), "e": Vector((1.0, 0.0, 0.05)),
        "f": Vector((0.72, -0.62, 0.32)), "g": Vector((-1.0, 0.0, 0.1)),
    }
    out = []
    for n in names:
        v = table[n].normalized() * d
        out.append(render_view(scene, os.path.join(out_dir, f"{prefix}{n}.png"), tuple(c + v), tuple(c), lens))
    return out
