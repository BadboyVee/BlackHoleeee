"""HORIZON's clouds: a fair-weather cumulus field, real volumes lit by the low sun that lights the hills, rendered
with a clear background in three layers by distance (near, mid, far), so the film can lay them over its own sky,
haze the far ones into it and drift each layer at its own speed.

Each cloud is a heap of spheres (a row of base puffs, towers climbing toward the middle) worn into cauliflower
billows by inverted Worley noise at three scales, flat at its base where the air condenses; the density is baked
into a grid with Geometry Nodes (Volume Cube), so Cycles steps through it voxel by voxel and stays fast.

Run with the `bpy` module (pip install bpy==4.2.0):
    python3 blender/clouds.py OUT_DIR [near|mid|far|all] [--preview]
"""
import math
import os
import sys

import bpy
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/clouds"
WHICH = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "all"
PREVIEW = "--preview" in sys.argv
WIDE = 1.25                                    # the sky is 1.25 x as wide as the hills, so it can drift
W, H = (720, 324) if PREVIEW else (2880, 1296)
SUN_ELEV, SUN_ROT = 22.0, 300.0                # the same sun as the hills (blender/hills.py)
CAM_Z = 26.59                                  # the hills' camera, standing on the flank of its hill
LOOK = (0.0, 800.0, 88.0)
BASE = 1050.0                                  # the condensation level: every cloud is flat at this height
LAYERS = {"near": (2400.0, 5200.0), "mid": (5200.0, 10500.0), "far": (10500.0, 30000.0)}


def reset(samples):
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
    scn.view_settings.look = "AgX - Base Contrast"
    scn.view_settings.exposure = float(os.environ.get("EXPOSURE", "0.0"))
    c = scn.cycles
    c.device = "CPU"
    c.samples = 16 if PREVIEW else samples
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.volume_bounces = 24
    c.max_bounces = 26
    c.volume_step_rate = 1.0
    c.volume_max_steps = 1024


def sky_light():
    """The sky lights the clouds' shaded sides blue; the camera never sees it (the film paints its own)."""
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    N, L = world.node_tree.nodes, world.node_tree.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.55, 0.72, 0.95, 1)
    e[1].position, e[1].color = 0.5, (0.07, 0.22, 0.72, 1)
    L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    bg = N["Background"]
    bg.inputs["Strength"].default_value = 1.0
    L.new(ramp.outputs["Color"], bg.inputs["Color"])
    d = bpy.data.lights.new("sun", "SUN")
    d.energy = 8.0
    d.angle = math.radians(0.6)
    d.color = (1.0, 0.96, 0.9)
    o = bpy.data.objects.new("sun", d)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - SUN_ELEV), 0, math.radians(SUN_ROT))
    # the ground under them, for the faint warm light it throws back up into their bases
    me = bpy.data.meshes.new("ground")
    s = 60000.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("ground", me)
    bpy.context.collection.objects.link(g)
    m = bpy.data.materials.new("ground")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.16, 0.05, 1)
    me.materials.append(m)
    g.visible_camera = False


def cloud_material(name, density):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N["Principled BSDF"])
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (1, 1, 1, 1)
    vol.inputs["Anisotropy"].default_value = 0.3
    vol.inputs["Density"].default_value = density            # x the baked grid, named "density"
    L.new(vol.outputs["Volume"], N["Material Output"].inputs["Volume"])
    return m


def density_group(name, spheres, seed, lo, hi, res, mat, billow):
    """Geometry Nodes: the cloud's density, baked into a grid over its box, with its material set."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links

    def vmath(op, a, b=None, scale=None):
        n = N.new("ShaderNodeVectorMath")
        n.operation = op
        L.new(a, n.inputs[0])
        if isinstance(b, tuple):
            n.inputs[1].default_value = b
        elif b is not None:
            L.new(b, n.inputs[1])
        if scale is not None:
            n.inputs["Scale"].default_value = scale
        return n.outputs[1] if op in ("DISTANCE", "LENGTH", "DOT_PRODUCT") else n.outputs["Vector"]

    def math_(op, a, b=None, c=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs["Value"]

    P = N.new("GeometryNodeInputPosition").outputs["Position"]
    # a slow domain warp, so the billows are not round
    wn = N.new("ShaderNodeTexNoise")
    wn.inputs["Scale"].default_value = 1 / (2.2 * billow)
    wn.inputs["Detail"].default_value = 2.0
    L.new(vmath("ADD", P, (seed * 131.0, seed * 71.0, seed * 37.0)), wn.inputs["Vector"])
    warp = vmath("SCALE", vmath("SUBTRACT", wn.outputs["Color"], (0.5, 0.5, 0.5)), scale=0.75 * billow)
    Pw = vmath("ADD", P, warp)
    # the heap: 1 at a sphere's centre, 0 on its surface
    env = None
    for (x, y, z, rad) in spheres:
        k = math_("MULTIPLY_ADD", vmath("DISTANCE", Pw, (x, y, z)), -1.0 / rad, 1.0)
        env = k if env is None else math_("MAXIMUM", env, k)
    # cauliflower billows, three scales of inverted Worley noise
    acc = env
    for i, (size, wgt) in enumerate(((billow, 0.55), (billow * 0.42, 0.30), (billow * 0.18, 0.09))):
        vo = N.new("ShaderNodeTexVoronoi")
        vo.inputs["Scale"].default_value = 1.0 / size
        L.new(vmath("ADD", Pw, (seed * 53.0 + i * 17.0, seed * 29.0, i * 41.0)), vo.inputs["Vector"])
        acc = math_("ADD", math_("MULTIPLY_ADD", vo.outputs["Distance"], -wgt, acc), wgt * 0.5)
    # a crisp surface, and flat underneath
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(P, sep.inputs["Vector"])
    base = N.new("ShaderNodeMapRange")
    base.inputs["From Min"].default_value = 0.0
    base.inputs["From Max"].default_value = 0.04 * billow * 4
    L.new(sep.outputs["Z"], base.inputs["Value"])
    edge = N.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 0.0
    edge.inputs["From Max"].default_value = 0.08
    L.new(acc, edge.inputs["Value"])
    dens = math_("MULTIPLY", edge.outputs["Result"], base.outputs["Result"])
    vc = N.new("GeometryNodeVolumeCube")
    L.new(dens, vc.inputs["Density"])
    vc.inputs["Min"].default_value = tuple(lo)
    vc.inputs["Max"].default_value = tuple(hi)
    for ax, n in zip("XYZ", res):
        vc.inputs[f"Resolution {ax}"].default_value = int(n)
    sm = N.new("GeometryNodeSetMaterial")                  # a volume made in nodes takes its material here
    sm.inputs["Material"].default_value = mat
    L.new(vc.outputs["Volume"], sm.inputs["Geometry"])
    out = N.new("NodeGroupOutput")
    L.new(sm.outputs["Geometry"], out.inputs["Geometry"])
    return ng


def heap(rng, width, height):
    """A cumulus as spheres in metres about its base centre: a row of base puffs, towers climbing toward the middle,
    each capped by smaller and smaller heads."""
    s = []
    n = int(rng.integers(4, 8))
    for i in range(n):
        x = (i / (n - 1) - 0.5) * width * 0.78 + rng.uniform(-0.05, 0.05) * width
        mid = 1 - abs(x) / (width * 0.5)
        rad = width * rng.uniform(0.10, 0.15) * (0.75 + 0.45 * mid)
        s.append((x, rng.uniform(-0.15, 0.15) * width, rad * 0.5, rad))
        top = height * (0.3 + 0.7 * mid ** 1.3) * rng.uniform(0.65, 1.0)
        z, r = rad * 0.5, rad
        for _ in range(7):                             # the heads shrink as they climb, so stop when they are small
            if z + r >= top or r < 0.25 * rad:
                break
            r *= rng.uniform(0.74, 0.9)
            z += r * rng.uniform(0.8, 1.05)
            s.append((x + rng.uniform(-0.45, 0.45) * r, rng.uniform(-0.3, 0.3) * r, z, r))
    return s


def field(seed=11):
    """Where the clouds sit: (layer, x, y, width, height), placed in rows by distance across the view, the near
    ones big and few, the far ones small and many, piling up toward the horizon."""
    rng = np.random.default_rng(seed)
    half = math.radians(37.0 + 6.0)                   # half the sky's view, and a little beyond for the drift
    rows = [(2600, 3600, 3, 1300, 900), (3600, 5200, 4, 1100, 800), (5200, 7500, 6, 1000, 650),
            (7500, 10500, 8, 900, 520), (10500, 15000, 10, 900, 420), (15000, 24000, 12, 1000, 360)]
    out = []
    for d0, d1, n, wid, hgt in rows:
        for k in range(n):
            y = rng.uniform(d0, d1)
            span = math.tan(half) * y
            x = (k + rng.uniform(0.15, 0.85)) / n * 2 * span - span
            w = wid * rng.uniform(0.55, 1.15)
            h = hgt * rng.uniform(0.6, 1.2)
            layer = next(name for name, (a, b) in LAYERS.items() if a <= y < b)
            out.append((layer, x, y, w, h))
    return out


def cloud(name, layer, x, y, w, h, seed):
    rng = np.random.default_rng(seed)
    spheres = heap(rng, w, h)
    sp = np.array(spheres)
    lo = (sp[:, :3] - sp[:, 3:4] * 1.3).min(0)
    hi = (sp[:, :3] + sp[:, 3:4] * 1.3).max(0)
    lo[2] = -2.0
    dist = math.hypot(x, y)
    vox = max(2.5, dist * (1.1e-3 if not PREVIEW else 3.5e-3))       # about two pixels a voxel
    res = np.maximum(np.ceil((hi - lo) / vox), 8).astype(int)
    billow = float(np.clip(w * 0.13, 70.0, 160.0))
    mat = cloud_material(name, 0.1)
    ng = density_group(name, spheres, seed, lo, hi, res, mat, billow)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(0, 0, 0)], [], [])
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = (x, y, BASE - CAM_Z)
    o.rotation_euler = (0, 0, rng.uniform(-0.5, 0.5))
    o.modifiers.new("cloud", "NODES").node_group = ng
    print(f"{name} {layer} d={dist:.0f} {w:.0f}x{h:.0f} vox={vox:.1f} res={tuple(res)}", flush=True)
    return o


def camera():
    cd = bpy.data.cameras.new("cam")
    cd.lens = 30.0
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0 * WIDE                      # the hills' camera, its view widened for the drift
    cd.clip_end = 100000.0
    o = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(o)
    o.location = (0.0, 0.0, 0.0)                       # the scene is set relative to the camera's height
    d = np.array(LOOK) - np.array((0.0, 0.0, CAM_Z))
    o.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    bpy.context.scene.camera = o


def render(layer):
    reset(48)
    sky_light()
    camera()
    for i, (lay, x, y, w, h) in enumerate(field()):
        if lay == layer:
            cloud(f"cu{i:02d}", lay, x, y, w, h, 100 + i)
    bpy.context.scene.objects["ground"].location.z = -CAM_Z
    bpy.context.scene.render.filepath = os.path.join(OUT, f"clouds_{layer}.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for layer in (["far", "mid", "near"] if WHICH == "all" else [WHICH]):
        render(layer)
