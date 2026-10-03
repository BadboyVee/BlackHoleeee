"""Plates for HORIZON: rolling green hills (the sky left transparent: the film paints its own, with clouds), and
the sea at sunset. Stills, rendered once; the film grades them and moves over them in 2D (slow push-ins, drifting
clouds, birds), so each plate is rendered a little larger than the frame.

Run with the `bpy` module (pip install bpy==4.2.0):
    python3 blender/hills.py OUT_DIR [hills|sunset|all] [--preview]
"""
import math
import os
import sys

import bpy
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/horizon"
WHICH = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "all"
PREVIEW = "--preview" in sys.argv
W, H = (768, 432) if PREVIEW else (2304, 1296)        # 1.2 x the frame, for the 2D moves
SKY_SUN = float(os.environ.get("SKY_SUN", "200"))
VIEW = os.environ.get("VIEW", "Standard")
LIGHT_ROT = float(os.environ.get("LIGHT_ROT", "300"))     # the sun the clouds are lit by (blender/clouds.py)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def render_settings(samples):
    scn = bpy.context.scene
    r = scn.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = W, H
    r.resolution_percentage = 100
    r.image_settings.file_format = "PNG"
    r.image_settings.color_depth = "16"
    scn.view_settings.view_transform = VIEW
    if VIEW == "AgX":
        scn.view_settings.look = "AgX - Punchy"
    scn.view_settings.exposure = float(os.environ.get("EXPOSURE", "0"))
    c = scn.cycles
    c.device = "CPU"
    c.samples = 16 if PREVIEW else samples
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 4
    c.diffuse_bounces = 2
    c.glossy_bounces = 2
    c.transmission_bounces = 2
    c.volume_bounces = 0


def heightfield(n, size, seed, hills, base_noise=0.0):
    """A smooth rolling terrain: a sum of broad bumps, a gentle swell, a little noise."""
    rng = np.random.default_rng(seed)
    xs = np.linspace(-size / 2, size / 2, n)
    X, Y = np.meshgrid(xs, xs)
    Z = np.zeros_like(X)
    for (cx, cy, r, h) in hills:
        Z += h * np.exp(-(((X - cx) ** 2 + (Y - cy) ** 2) / (2 * r * r)))
    if base_noise:
        for k in range(4):
            f = (k + 1) * 2 * math.pi / size * (1.7 ** k) * 3
            ph = rng.uniform(0, 2 * math.pi, 2)
            ang = rng.uniform(0, math.pi)
            Z += base_noise / (1.9 ** k) * np.sin(f * (X * math.cos(ang) + Y * math.sin(ang)) + ph[0]) * \
                np.cos(f * 0.7 * (X * math.sin(ang) - Y * math.cos(ang)) + ph[1])
    return X, Y, Z


def terrain_mesh(name, X, Y, Z, mat):
    n = X.shape[0]
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    idx = np.arange(n * n).reshape(n, n)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def sky(sun_elev, sun_rot, strength=1.0, air=1.0, dust=1.0, ozone=1.0, sun_disc=False):
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    N, L = world.node_tree.nodes, world.node_tree.links
    s = N.new("ShaderNodeTexSky")
    s.sky_type = "NISHITA"
    s.sun_elevation = math.radians(sun_elev)
    s.sun_rotation = math.radians(sun_rot)
    s.air_density = air
    s.dust_density = dust
    s.ozone_density = ozone
    s.sun_disc = sun_disc
    s.sun_size = math.radians(1.2)
    s.sun_intensity = 1.0
    bg = N["Background"]
    bg.inputs["Strength"].default_value = strength
    L.new(s.outputs["Color"], bg.inputs["Color"])
    return world


def sun(elev, rot, strength, color=(1.0, 0.96, 0.9)):
    d = bpy.data.lights.new("sun", "SUN")
    d.energy = strength
    d.color = color
    d.angle = math.radians(1.0)
    o = bpy.data.objects.new("sun", d)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - elev), 0, math.radians(rot))
    return o


def camera(loc, look, lens=35.0, dof=None):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_end = 5000
    o = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(o)
    o.location = loc
    d = np.array(look) - np.array(loc)
    o.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance, cd.dof.aperture_fstop = dof
    bpy.context.scene.camera = o
    return o


def gradient_sky(horizon, zenith, light=0.35, ground=(0.05, 0.08, 0.04)):
    """A clean sky: horizon to zenith by the view's height, seen at full strength by the camera and at `light`
    by everything it lights."""
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
    e[0].position, e[0].color = 0.0, (*horizon, 1)
    e[1].position, e[1].color = 0.5, (*zenith, 1)
    L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    lp = N.new("ShaderNodeLightPath")
    strength = N.new("ShaderNodeMix")
    strength.data_type = "FLOAT"
    strength.inputs["A"].default_value = light
    strength.inputs["B"].default_value = 1.0
    L.new(lp.outputs["Is Camera Ray"], strength.inputs["Factor"])
    bg = N["Background"]
    L.new(ramp.outputs["Color"], bg.inputs["Color"])
    L.new(strength.outputs["Result"], bg.inputs["Strength"])
    return world


HILLS = [   # (x, y, radius, height), placed by hand like a countryside seen from the flank of a hill: steep round
            # hills in layers, each bigger and hazier, a far ridge; the first one is the hill the camera stands on
    (-40, -20, 60, 30),
    (-70, 115, 55, 36), (95, 150, 60, 32),
    (-10, 300, 70, 40), (175, 360, 80, 46), (-225, 400, 90, 52),
    (60, 600, 110, 62), (-285, 680, 130, 72), (385, 740, 140, 78),
    (-100, 1000, 180, 100), (380, 1080, 200, 112), (-600, 1100, 220, 120),
    (-650, 1600, 340, 170), (300, 1700, 370, 190), (1050, 1700, 400, 180), (-1400, 1750, 420, 170),
]


def hills():
    """The countryside under the sky: the hills laid out by hand, dressed as fields with hedgerows and trees, in
    a low afternoon sun from the left, cloud shadows passing over them. The sky is left clear for the film."""
    import country
    reset()
    render_settings(64)
    horizon, zenith = (0.60, 0.77, 0.98), (0.08, 0.25, 0.76)
    gradient_sky(horizon, zenith, light=0.32)
    sun(22, LIGHT_ROT, 2.1, color=(1.0, 0.95, 0.85))
    haze = (0.50, 0.67, 0.95)
    haze_start, haze_end = 700.0, 6500.0
    mat = country.grass(haze, haze_start, haze_end)
    X, Y, Z = heightfield(800, 4000.0, 7, [(x, y - 1800, r, h) for x, y, r, h in HILLS], base_noise=1.2)
    ground = terrain_mesh("hills", X, Y + 1800, Z, mat)
    leaf = country.leaves("leaves", (0.020, 0.085, 0.012), (0.045, 0.130, 0.018), haze, haze_start, haze_end)
    hedge_leaf = country.leaves("hedge", (0.018, 0.075, 0.010), (0.035, 0.115, 0.014), haze, haze_start, haze_end)
    bark = bpy.data.materials.new("bark")
    bark.use_nodes = True
    bark.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.04, 0.03, 1)
    shrub = country.bush(hedge_leaf)
    oaks = (country.tree(leaf, bark, 1), country.tree(leaf, bark, 2))
    country.countryside(ground, shrub, oaks, near=180.0)
    country.cloud_shadows()
    n = X.shape[0]

    def z_at(x, y):
        i = int(round((y - 1800 + 2000) / 4000 * (n - 1)))
        j = int(round((x + 2000) / 4000 * (n - 1)))
        return float(Z[min(max(i, 0), n - 1), min(max(j, 0), n - 1)])

    camera((0, 0, z_at(0, 0) + 3), (0, 800, 88), lens=30)
    print("camera z", z_at(0, 0) + 3, flush=True)
    bpy.context.scene.render.film_transparent = True        # the film lays its own sky and the clouds behind
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    bpy.context.scene.render.filepath = os.path.join(OUT, "hills.png")
    bpy.ops.render.render(write_still=True)


def sunset_sky():
    """Dusk: warm at the horizon, through rose, to a deep blue overhead."""
    world = bpy.data.worlds.new("dusk")
    bpy.context.scene.world = world
    world.use_nodes = True
    N, L = world.node_tree.nodes, world.node_tree.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    e = ramp.color_ramp.elements
    # world Generated is the view direction: Z is 0 at the horizon, 1 straight up
    e[0].position, e[0].color = 0.0, (1.0, 0.33, 0.05, 1)
    e[1].position, e[1].color = 0.45, (0.02, 0.04, 0.14, 1)
    for pos, col in [(0.035, (1.0, 0.56, 0.18)), (0.10, (0.85, 0.36, 0.26)), (0.20, (0.30, 0.17, 0.34))]:
        el = e.new(pos)
        el.color = (*col, 1)
    L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    bg = N["Background"]
    bg.inputs["Strength"].default_value = 1.0
    L.new(ramp.outputs["Color"], bg.inputs["Color"])


def sunset():
    reset()
    render_settings(64)
    sunset_sky()
    sun(3.0, 180, 1.1, color=(1.0, 0.58, 0.28))
    # the sun itself, a disc just above the sea
    disc = bpy.data.materials.new("disc")
    disc.use_nodes = True
    N, L = disc.node_tree.nodes, disc.node_tree.links
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.72, 0.38, 1)
    em.inputs["Strength"].default_value = 6.0
    L.new(em.outputs["Emission"], N["Material Output"].inputs["Surface"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=60, location=(120, 4000, 150))
    bpy.context.object.data.materials.append(disc)
    bpy.ops.object.shade_smooth()
    # the sea: small waves in the bump, glossy, so the sun lays a road of light across it
    m = bpy.data.materials.new("sea")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.01, 0.015, 0.03, 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Specular IOR Level"].default_value = 0.7
    tex = N.new("ShaderNodeTexCoord")
    mapn = N.new("ShaderNodeMapping")
    mapn.inputs["Scale"].default_value = (1.0, 4.0, 1.0)
    L.new(tex.outputs["Object"], mapn.inputs["Vector"])
    wave = N.new("ShaderNodeTexNoise")
    wave.inputs["Scale"].default_value = 0.9
    wave.inputs["Detail"].default_value = 10.0
    wave.inputs["Roughness"].default_value = 0.62
    L.new(mapn.outputs["Vector"], wave.inputs["Vector"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.55
    L.new(wave.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    bpy.ops.mesh.primitive_plane_add(size=12000, location=(0, 0, 0))
    bpy.context.object.data.materials.append(m)
    # a low headland far off to one side
    land = bpy.data.materials.new("land")
    land.use_nodes = True
    lb = land.node_tree.nodes["Principled BSDF"]
    lb.inputs["Base Color"].default_value = (0.015, 0.012, 0.02, 1)
    lb.inputs["Roughness"].default_value = 1.0
    X, Y, Zh = heightfield(120, 1400, 5, [(0, 0, 220, 70), (260, 90, 170, 46), (-240, 60, 150, 30)])
    terrain_mesh("headland", X - 1500, Y + 3300, Zh - 6, land)
    camera((0, -10, 2.6), (0, 400, 4.5), lens=38)
    bpy.context.scene.render.filepath = os.path.join(OUT, "sunset.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if WHICH in ("hills", "all"):
        hills()
    if WHICH in ("sunset", "all"):
        sunset()
