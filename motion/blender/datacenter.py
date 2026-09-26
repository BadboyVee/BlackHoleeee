"""Plate for the Dario film: "a country of geniuses in a datacenter".

A night flyover of a city whose buildings are server racks. On the downbeat the windows light
up in a wave that runs out from under the camera to the horizon.

    python3 blender/datacenter.py OUT_DIR [first_frame last_frame] [--preview]

Frame 1 is film time 20.0 s (bar 11 at 120 BPM). 60 fps.
"""
import math
import os
import sys

import bpy
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/datacenter"
FIRST = int(sys.argv[2]) if len(sys.argv) > 3 else 1
LAST = int(sys.argv[3]) if len(sys.argv) > 3 else 150
PREVIEW = "--preview" in sys.argv
FPS = 60
PLATE = 150
N = 110           # blocks per side
PITCH = 1.5       # block spacing; blocks are 1.0 wide, the rest is street
WAVE_Y = -25.0    # the light wave starts under the camera's first position


def lin(c):
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def city_mesh():
    rng = np.random.default_rng(21)
    verts, faces, rnd = [], [], []
    half = N * PITCH / 2
    cube_v = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float)
    cube_f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    for i in range(N):
        for j in range(N):
            x = i * PITCH - half
            y = j * PITCH - half * 0.35
            if abs(x) < 1.6 or j % 13 == 0 or i % 17 == 0:   # avenues split the grid into districts
                continue
            h = 0.35 + rng.gamma(1.6, 0.42) * (0.7 + 1.1 * math.sin(x * 0.09 + y * 0.05) ** 2)
            w = 1.0 if rng.random() > 0.12 else 0.7
            v = cube_v * [w, w, h] + [x, y, 0]
            base = len(verts)
            verts.extend(v.tolist())
            r = rng.random()
            for f in cube_f:
                faces.append([base + k for k in f])
                rnd.append(r)
    me = bpy.data.meshes.new("city")
    me.from_pydata(verts, [], faces)
    attr = me.attributes.new("rnd", "FLOAT", "FACE")
    attr.data.foreach_set("value", rnd)
    me.update()
    return me


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def city_material():
    m = bpy.data.materials.new("racks")
    # thousands of lit windows: seen directly, never sampled as lights (same look, twice the speed)
    m.cycles.emission_sampling = "NONE"
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    body = node(nt, "ShaderNodeBsdfPrincipled")
    body.inputs["Base Color"].default_value = (0.008, 0.008, 0.009, 1)
    body.inputs["Roughness"].default_value = 0.45
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "rnd"
    at.attribute_type = "GEOMETRY"

    def math_(op, a, b=None, val=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for idx, src in enumerate((a, b)):
            if src is None:
                continue
            if isinstance(src, (int, float)):
                n.inputs[idx].default_value = src
            else:
                L(src, n.inputs[idx])
        return n.outputs[0]

    def vmath(op, a, b=None, scale=None):
        n = nt.nodes.new("ShaderNodeVectorMath")
        n.operation = op
        L(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (tuple, list)):
                n.inputs[1].default_value = b
            else:
                L(b, n.inputs[1])
        return n.outputs[0]

    # windows: one cell per floor (0.25 tall) and per 0.22 of facade; only side faces get them
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], nsep.inputs[0])
    side = math_("LESS_THAN", math_("ABSOLUTE", nsep.outputs["Z"]), 0.5)
    rows = math_("FRACT", math_("MULTIPLY", sep.outputs["Z"], 4.0))
    row_on = math_("MULTIPLY", math_("GREATER_THAN", rows, 0.35), math_("LESS_THAN", rows, 0.8))
    cols = math_("FRACT", math_("MULTIPLY", math_("ADD", sep.outputs["X"], sep.outputs["Y"]), 4.5))
    col_on = math_("MULTIPLY", math_("GREATER_THAN", cols, 0.18), math_("LESS_THAN", cols, 0.82))
    slot = math_("MULTIPLY", math_("MULTIPLY", row_on, col_on), side)
    cell = vmath("FLOOR", vmath("MULTIPLY", tc.outputs["Object"], (4.5, 4.5, 4.0)))
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    L(cell, wn.inputs["Vector"])
    lit = math_("GREATER_THAN", math_("ADD", wn.outputs["Value"], math_("MULTIPLY", at.outputs["Fac"], 0.25)), 0.72)
    # the wave: a radius that grows over time from under the camera's start point
    dist = math_("SQRT", math_("ADD", math_("MULTIPLY", sep.outputs["X"], sep.outputs["X"]),
                               math_("MULTIPLY", math_("SUBTRACT", sep.outputs["Y"], WAVE_Y), math_("SUBTRACT", sep.outputs["Y"], WAVE_Y))))
    radius = nt.nodes.new("ShaderNodeValue")
    radius.name = "wave"
    front = math_("LESS_THAN", dist, radius.outputs[0])
    edge = math_("MULTIPLY", math_("GREATER_THAN", dist, math_("SUBTRACT", radius.outputs[0], 6.0)), front)
    mask = math_("MULTIPLY", math_("MULTIPLY", slot, lit), front)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    wn2 = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn2.noise_dimensions = "3D"
    L(vmath("ADD", cell, (17.0, 3.0, 5.0)), wn2.inputs["Vector"])
    L(wn2.outputs["Value"], ramp.inputs[0])
    ramp.color_ramp.elements[0].color = (*lin((1.0, 0.62, 0.34)), 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (*lin((0.93, 0.42, 0.28)), 1)
    e = ramp.color_ramp.elements.new(0.9)
    e.color = (*lin((0.92, 0.93, 1.0)), 1)
    strength = math_("MULTIPLY", mask, math_("ADD", 2.6, math_("MULTIPLY", edge, 14.0)))
    L(ramp.outputs[0], body.inputs["Emission Color"])
    L(strength, body.inputs["Emission Strength"])
    L(body.outputs[0], out.inputs[0])
    return m, radius


def stream_material():
    """Dashes of light that race along the avenues toward the horizon."""
    m = bpy.data.materials.new("streams")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*lin((1.0, 0.55, 0.32)), 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])
    off = nt.nodes.new("ShaderNodeValue")
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "SUBTRACT"
    L(sep.outputs["Y"], add.inputs[0])
    L(off.outputs[0], add.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 14.0
    L(add.outputs[0], mul.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    L(mul.outputs[0], fr.inputs[0])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 6.0
    L(fr.outputs[0], pw.inputs[0])
    sc = nt.nodes.new("ShaderNodeMath")
    sc.operation = "MULTIPLY"
    sc.inputs[1].default_value = 9.0
    L(pw.outputs[0], sc.inputs[0])
    L(sc.outputs[0], em.inputs["Strength"])
    L(em.outputs[0], out.inputs[0])
    return m, off


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.fps = FPS
    scn.frame_start, scn.frame_end = FIRST, LAST

    world = bpy.data.worlds.new("w")
    scn.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.002, 0.0014, 0.0012, 1)
    world.mist_settings.start = 12.0
    world.mist_settings.depth = 130.0
    world.mist_settings.falloff = "QUADRATIC"

    city = bpy.data.objects.new("city", city_mesh())
    scn.collection.objects.link(city)
    mat, radius = city_material()
    city.data.materials.append(mat)

    ground = bpy.data.materials.new("ground")
    ground.use_nodes = True
    gb = ground.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.006, 0.005, 0.005, 1)
    gb.inputs["Roughness"].default_value = 0.3
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
    bpy.context.object.data.materials.append(ground)

    streams, offset = stream_material()
    half = N * PITCH / 2
    for i in range(N):
        x = i * PITCH - half
        if i % 17 == 0 or abs(x) < 1.6:
            for dx in ((-0.35, 0.35) if abs(x) < 1.6 else (0.0,)):
                bpy.ops.mesh.primitive_plane_add(size=1, location=(x + dx if abs(x) >= 1.6 else dx, 20.0, 0.01))
                o = bpy.context.object
                o.scale = (0.05, 260.0, 1.0)
                o.data.materials.append(streams)

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 24
    cam_data.clip_end = 400
    cam = bpy.data.objects.new("cam", cam_data)
    scn.collection.objects.link(cam)
    scn.camera = cam
    for f in range(FIRST, LAST + 1):
        t = (f - 1) / FPS
        u = t / ((PLATE - 1) / FPS)
        y = WAVE_Y - 16.0 + 16.0 * u
        cam.location = (0.0, y, 14.5 - 2.5 * u)
        cam.rotation_euler = (math.radians(66 + 4 * u), math.radians(-3.0 + 3.0 * u), 0)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        # the wave: starts on the downbeat, reaches the horizon in about one bar
        radius.outputs[0].default_value = 1.0 + 190.0 * (1 - (1 - min(1.0, t / 2.3)) ** 2.4)
        radius.outputs[0].keyframe_insert("default_value", frame=f)
        offset.outputs[0].default_value = t * 1.9
        offset.outputs[0].keyframe_insert("default_value", frame=f)

    vl = scn.view_layers[0]
    vl.use_pass_mist = True
    scn.use_nodes = True
    tree = scn.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    rl = tree.nodes.new("CompositorNodeRLayers")
    mix = tree.nodes.new("CompositorNodeMixRGB")
    mix.blend_type = "MIX"
    fog = (0.05, 0.028, 0.022, 1)
    mix.inputs[2].default_value = fog
    comp = tree.nodes.new("CompositorNodeComposite")
    gamma = tree.nodes.new("CompositorNodeMath")
    gamma.operation = "POWER"
    gamma.inputs[1].default_value = 1.6
    tree.links.new(rl.outputs["Mist"], gamma.inputs[0])
    tree.links.new(gamma.outputs[0], mix.inputs[0])
    tree.links.new(rl.outputs["Image"], mix.inputs[1])
    tree.links.new(mix.outputs[0], comp.inputs[0])

    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = (960, 540) if PREVIEW else (1600, 900)
    r.resolution_percentage = 100
    r.use_motion_blur = False
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Punchy"
    c = scn.cycles
    c.device = "CPU"
    c.samples = 6 if PREVIEW else 8
    c.adaptive_threshold = 0.06
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 3
    c.diffuse_bounces = 1
    c.glossy_bounces = 2
    c.transmission_bounces = 0
    c.blur_glossy = 1.0
    c.sample_clamp_indirect = 6.0
    r.use_persistent_data = True
    r.filepath = os.path.join(OUT, "f")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build()
    bpy.ops.render.render(animation=True)
