"""Finale plate for THE FRONTIER: three monoliths rise out of a black mirror floor.

Run with the `bpy` module (pip install bpy==4.2.0):
    python3 blender/monoliths.py OUT_DIR [first_frame last_frame] [--preview]

Frame 1 of this plate is film time 20.8 s (bar 14, beat 1 at 150 BPM). 60 fps.
"""
import math
import os
import sys

import bpy

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/monoliths"
FIRST = int(sys.argv[2]) if len(sys.argv) > 3 else 1
LAST = int(sys.argv[3]) if len(sys.argv) > 3 else 150
PREVIEW = "--preview" in sys.argv
FPS = 60
BEAT = 0.4  # seconds at 150 BPM
PLATE = 150  # frames in the whole plate; the camera move is timed against this

ACCENTS = [(0.10, 0.95, 0.62), (0.22, 0.30, 1.00), (0.85, 0.44, 0.30)]  # astra, gemini, fable


def srgb_to_lin(c):
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def principled(name, base, rough, metal=0.0, spec=0.5, emit=None, strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new("bevel", "BEVEL")
    bev.width = 0.012
    bev.segments = 3
    o.data.materials.append(mat)
    return o


def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 4


def build():
    reset()
    scn = bpy.context.scene
    scn.render.fps = FPS
    scn.frame_start, scn.frame_end = FIRST, LAST

    world = bpy.data.worlds.new("w")
    scn.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.0008, 0.0008, 0.001, 1)

    floor_m = principled("floor", (0.002, 0.002, 0.0025), 0.2, spec=0.5)
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
    bpy.context.object.data.materials.append(floor_m)

    slab_m = principled("slab", (0.012, 0.012, 0.014), 0.22, metal=0.35, spec=0.7, coat=0.6)
    xs = [-2.45, 0.0, 2.45]
    angles = [16, 0, -16]
    for i, (x, ang, acc) in enumerate(zip(xs, angles, ACCENTS)):
        lin = srgb_to_lin(acc)
        seam_m = principled(f"seam{i}", (0, 0, 0), 0.5, emit=lin, strength=38.0)
        parent = bpy.data.objects.new(f"rig{i}", None)
        scn.collection.objects.link(parent)
        parent.location = (x, 0.0, 0.0)
        parent.rotation_euler = (0, 0, math.radians(ang))
        slab = box(f"slab{i}", (1.15, 0.30, 2.9), (0, 0, 1.45), slab_m)
        seam = box(f"seam{i}", (0.035, 0.02, 2.62), (0, -0.155, 1.45), seam_m)
        cap = box(f"cap{i}", (1.05, 0.02, 0.018), (0, -0.155, 2.86), seam_m)
        for o in (slab, seam, cap):
            o.parent = parent
        bpy.ops.object.light_add(type="AREA", location=(0, 1.1, 1.7))
        L = bpy.context.object
        L.parent = parent
        L.data.shape = "RECTANGLE"
        L.data.size, L.data.size_y = 1.3, 3.0
        L.data.energy = 380
        L.data.color = lin
        L.rotation_euler = (math.radians(-90), 0, 0)
        L.visible_glossy = False
        # rise out of the floor, staggered a sixteenth apart, starting on the downbeat
        t0 = 0.02 + i * BEAT / 4
        for f in range(FIRST, LAST + 1):
            t = (f - 1) / FPS
            u = ease_out((t - t0) / 0.42)
            parent.location.z = -3.2 * (1 - u)
            parent.keyframe_insert("location", index=2, frame=f)

    bpy.ops.object.light_add(type="AREA", location=(0, -4.5, 6.0))
    key = bpy.context.object
    key.data.size = 6.0
    key.data.energy = 140
    key.visible_glossy = False
    key.data.color = (0.95, 0.95, 1.0)
    key.rotation_euler = (math.radians(38), 0, 0)

    # horizon glow far behind the slabs: silhouettes them and lays a soft line into the mirror floor
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 26.0, 6.0))
    back = bpy.context.object
    back.scale = (90.0, 14.0, 1.0)
    back.rotation_euler = (math.radians(90), 0, 0)
    bm = bpy.data.materials.new("horizon")
    bm.use_nodes = True
    nt = bm.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], ramp.inputs[0])
    ramp.color_ramp.interpolation = "EASE"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.05, 0.055, 0.07, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1)
    mid = ramp.color_ramp.elements.new(0.22)
    mid.color = (0.018, 0.02, 0.026, 1)
    nt.links.new(ramp.outputs[0], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs[0])
    back.data.materials.append(bm)

    # a faint high strip behind the camera, seen only in reflections: it gives the slab faces a sheen
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -16.0, 7.5))
    strip = bpy.context.object
    strip.scale = (18.0, 1.2, 1.0)
    strip.rotation_euler = (math.radians(70), 0, 0)
    strip.data.materials.append(principled("strip", (0, 0, 0), 1.0, emit=(0.8, 0.82, 0.9), strength=0.9))
    strip.visible_camera = False
    strip.visible_diffuse = False

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 32
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 3.2
    cam = bpy.data.objects.new("cam", cam_data)
    scn.collection.objects.link(cam)
    scn.camera = cam
    target = bpy.data.objects.new("target", None)
    scn.collection.objects.link(target)
    target.location = (0, 0, 1.5)
    tr = cam.constraints.new("TRACK_TO")
    tr.target = target
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    cam_data.dof.focus_object = target
    dur = (PLATE - 1) / FPS
    for f in range(FIRST, LAST + 1):
        t = (f - 1) / FPS
        u = ease_out(t / max(dur, 1e-6)) if t > 0 else 0.0
        # low, slow push-in with a gentle orbit that settles by the last frame
        ang = math.radians(-14 + 14 * u)
        dist = 11.5 - 3.6 * u
        cam.location = (dist * math.sin(ang), -dist * math.cos(ang), 0.55 + 0.5 * u)
        cam.keyframe_insert("location", frame=f)

    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = (960, 540) if PREVIEW else (1600, 900)
    r.resolution_percentage = 100
    r.film_transparent = False
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.5
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.image_settings.color_depth = "8"
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Punchy"
    c = scn.cycles
    c.device = "CPU"
    c.samples = 8 if PREVIEW else 10
    c.adaptive_threshold = 0.06
    c.blur_glossy = 1.0
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 3
    c.diffuse_bounces = 2
    c.glossy_bounces = 2
    c.transmission_bounces = 0
    c.transparent_max_bounces = 2
    c.sample_clamp_indirect = 6.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    r.use_persistent_data = True
    r.filepath = os.path.join(OUT, "f")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build()
    bpy.ops.render.render(animation=True)
