"""Sahara voyage: three men and two women crossing an erg in a loaded 4x4.

    python3 build.py --cams drive,wide --res 1920x1080 --samples 128
    python3 build.py --save sahara.blend
Shots: drive (3/4 front, dust), side (all five through the glass), wide (scale),
aerial (drone), stop (out of the car on a crest), dusk (low sun, long shadows).
"""
import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blender-kit"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import cast  # noqa: E402
import kit  # noqa: E402
import mh  # noqa: E402
import suv  # noqa: E402

WIND = math.radians(18.0)          # dunes march along this direction


# ------------------------------------------------------------- terrain ---
def _n(x, y, s):
    """Cheap smooth pseudo-noise in [-1, 1] from a few incommensurate sines."""
    return (np.sin(1.31 * x + 0.71 * y + 1.1 + s) * np.cos(0.93 * y - 0.43 * x + 2.3 * s)
            + 0.5 * np.sin(2.17 * x - 1.3 * y + 4.1 * s) * np.cos(1.7 * y + 0.6 * x + s)) / 1.5


def height(x, y):
    """Dune field height in metres at world x, y (numpy arrays or floats)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    u = x * math.cos(WIND) + y * math.sin(WIND)
    v = -x * math.sin(WIND) + y * math.cos(WIND)

    def dunes(u, v, lam, amp, crest, seed, wob):
        ph = u / lam + wob * _n(x / (2.3 * lam), y / (2.3 * lam), seed) + 0.22 * np.sin(v / (1.25 * lam) + seed)
        p = ph - np.floor(ph)
        s = np.clip(p / crest, 0, 1)
        up = (3 * s * s - 2 * s ** 3) ** 0.85                 # long windward ramp
        t = np.clip((p - crest) / (1 - crest), 0, 1)
        down = (1 - t) ** 1.15                                   # short slip face
        prof = np.where(p < crest, up, down)
        a = amp * (0.55 + 0.45 * _n(x / (3.1 * lam), y / (3.1 * lam), seed + 3.0))
        return a * prof

    h = dunes(u, v, 170.0, 30.0, 0.74, 0.0, 0.33)
    u2 = x * math.cos(WIND + 0.5) + y * math.sin(WIND + 0.5)
    v2 = -x * math.sin(WIND + 0.5) + y * math.cos(WIND + 0.5)
    h += dunes(u2, v2, 52.0, 4.2, 0.72, 2.0, 0.25)
    h += 2.5 * _n(x / 210.0, y / 210.0, 5.0) + 0.25 * _n(x / 13.0, y / 13.0, 7.0)
    return h


def normal(x, y, e=0.5):
    hx = float(height(x + e, y) - height(x - e, y)) / (2 * e)
    hy = float(height(x, y + e) - height(x, y - e)) / (2 * e)
    return Vector((-hx, -hy, 1.0)).normalized()


def grid_mesh(name, x0, y0, x1, y1, step, mat, c, zfun, uv_scale=1.0, hole=None):
    nx, ny = int(round((x1 - x0) / step)) + 1, int(round((y1 - y0) / step)) + 1
    xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(xs, ys)
    Z = zfun(X, Y)
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    i = np.arange((ny - 1) * (nx - 1))
    r, q = i // (nx - 1), i % (nx - 1)
    a = r * nx + q
    faces = np.stack([a, a + 1, a + nx + 1, a + nx], axis=1)
    if hole is not None:
        hx0, hy0, hx1, hy1 = hole
        cx, cy = (X.ravel()[a] + X.ravel()[a + nx + 1]) / 2, (Y.ravel()[a] + Y.ravel()[a + nx + 1]) / 2
        faces = faces[~((cx > hx0) & (cx < hx1) & (cy > hy0) & (cy < hy1))]
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(len(faces) * 4)
    me.loops.foreach_set("vertex_index", faces.ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", np.arange(0, len(faces) * 4, 4))
    me.polygons.foreach_set("loop_total", np.full(len(faces), 4))
    me.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
    me.update()
    me.validate()
    uv = me.uv_layers.new(name="UVMap")
    co = verts[faces.ravel()][:, :2] * uv_scale
    uv.data.foreach_set("uv", co.ravel())
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    return ob


def sand_material(haze=(0.78, 0.66, 0.52), haze_dist=2600.0):
    m, nt, b, out = kit._new("sahara_sand")
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    # colour: warm gold with broad tonal drift and fine grain
    n1 = N.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.035
    n1.inputs["Detail"].default_value = 5.0
    L.new(tc.outputs["Object"], n1.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.3
    cr.color_ramp.elements[0].color = (0.56, 0.31, 0.135, 1)
    cr.color_ramp.elements[1].position = 0.75
    cr.color_ramp.elements[1].color = (0.72, 0.45, 0.21, 1)
    L.new(n1.outputs[0], cr.inputs[0])
    grain = N.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 900.0
    L.new(tc.outputs["Object"], grain.inputs["Vector"])
    mixg = N.new("ShaderNodeMix")
    mixg.data_type = "RGBA"
    mixg.blend_type = "OVERLAY"
    mixg.inputs["Factor"].default_value = 0.25
    L.new(cr.outputs[0], mixg.inputs["A"])
    L.new(grain.outputs[0], mixg.inputs["B"])
    # wind ripples: banded waves across the wind, broken up by noise
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, WIND + 0.2)
    L.new(tc.outputs["Object"], mp.inputs[0])
    wv = N.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 5.0
    wv.inputs["Distortion"].default_value = 4.5
    wv.inputs["Detail"].default_value = 3.0
    wv.inputs["Detail Scale"].default_value = 0.6
    L.new(mp.outputs[0], wv.inputs["Vector"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.5
    bp.inputs["Distance"].default_value = 0.07
    L.new(wv.outputs[0], bp.inputs["Height"])
    bp2 = N.new("ShaderNodeBump")
    bp2.inputs["Strength"].default_value = 0.25
    bp2.inputs["Distance"].default_value = 0.004
    L.new(grain.outputs[0], bp2.inputs["Height"])
    L.new(bp.outputs[0], bp2.inputs["Normal"])
    L.new(bp2.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.88
    b.inputs["Specular IOR Level"].default_value = 0.25
    # aerial perspective: fade to the horizon haze with distance from the camera
    cd = N.new("ShaderNodeCameraData")
    ex = N.new("ShaderNodeMath")
    ex.operation = "DIVIDE"
    L.new(cd.outputs["View Distance"], ex.inputs[0])
    ex.inputs[1].default_value = -haze_dist
    e2 = N.new("ShaderNodeMath")
    e2.operation = "EXPONENT"
    L.new(ex.outputs[0], e2.inputs[0])
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(e2.outputs[0], inv.inputs[1])
    mh_ = N.new("ShaderNodeMix")
    mh_.data_type = "RGBA"
    L.new(inv.outputs[0], mh_.inputs["Factor"])
    L.new(mixg.outputs["Result"], mh_.inputs["A"])
    mh_.inputs["B"].default_value = tuple(haze) + (1,)
    L.new(mh_.outputs["Result"], b.inputs["Base Color"])
    return m


def dust_material(density=0.5):
    m = bpy.data.materials.new("dust")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    out = N.new("ShaderNodeOutputMaterial")
    vol = N.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.8, 0.62, 0.42, 1)
    vol.inputs["Anisotropy"].default_value = 0.35
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.65
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    # falloff: dense low and near the car (object +X end), thinning upward and backward
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    fx = N.new("ShaderNodeMapRange")           # along the plume (0 = far tail, 1 = at the wheels)
    fx.inputs["From Min"].default_value = 0.0
    fx.inputs["From Max"].default_value = 1.0
    fx.inputs["To Min"].default_value = 0.08
    fx.inputs["To Max"].default_value = 1.0
    L.new(sep.outputs["X"], fx.inputs["Value"])
    fz = N.new("ShaderNodeMapRange")
    fz.inputs["From Min"].default_value = 0.0
    fz.inputs["From Max"].default_value = 1.0
    fz.inputs["To Min"].default_value = 1.0
    fz.inputs["To Max"].default_value = 0.0
    fz.interpolation_type = "SMOOTHERSTEP"
    L.new(sep.outputs["Z"], fz.inputs["Value"])
    # round the box off sideways so no hard edges show
    fy = N.new("ShaderNodeMath")
    fy.operation = "SUBTRACT"
    L.new(sep.outputs["Y"], fy.inputs[0])
    fy.inputs[1].default_value = 0.5
    fy2 = N.new("ShaderNodeMath")
    fy2.operation = "ABSOLUTE"
    L.new(fy.outputs[0], fy2.inputs[0])
    fy3 = N.new("ShaderNodeMapRange")
    fy3.inputs["From Min"].default_value = 0.15
    fy3.inputs["From Max"].default_value = 0.5
    fy3.inputs["To Min"].default_value = 1.0
    fy3.inputs["To Max"].default_value = 0.0
    L.new(fy2.outputs[0], fy3.inputs["Value"])
    thr = N.new("ShaderNodeMapRange")
    thr.inputs["From Min"].default_value = 0.4
    thr.inputs["From Max"].default_value = 0.72
    L.new(nz.outputs[0], thr.inputs["Value"])
    mul = None
    for a in (fx, fz, fy3, thr):
        if mul is None:
            mul = a.outputs[0]
            continue
        mm = N.new("ShaderNodeMath")
        mm.operation = "MULTIPLY"
        L.new(mul, mm.inputs[0])
        L.new(a.outputs[0], mm.inputs[1])
        mul = mm.outputs[0]
    dn = N.new("ShaderNodeMath")
    dn.operation = "MULTIPLY"
    L.new(mul, dn.inputs[0])
    dn.inputs[1].default_value = density
    L.new(dn.outputs[0], vol.inputs["Density"])
    L.new(vol.outputs[0], out.inputs["Volume"])
    return m


def sky(elevation=24.0, rotation=0.0, strength=0.22, dust=2.2):
    w = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sk = nt.nodes.new("ShaderNodeTexSky")
    sk.sky_type = "MULTIPLE_SCATTERING"
    sk.sun_elevation = math.radians(elevation)
    sk.sun_rotation = math.radians(rotation)
    sk.sun_size = math.radians(0.6)
    sk.sun_intensity = 1.0
    sk.aerosol_density = dust
    sk.air_density = 1.0
    sk.ozone_density = 1.0
    nt.links.new(sk.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w


# ---------------------------------------------------------------- scene ---
def car_matrix(x, y, heading):
    """Rest the truck on the dune: z and tilt from the sand under the four wheels."""
    f = Vector((math.cos(heading), math.sin(heading), 0))
    l = Vector((-math.sin(heading), math.cos(heading), 0))
    pts = []
    for ax in (suv.AX_F, suv.AX_R):
        for s in (-1, 1):
            p = Vector((x, y, 0)) + f * ax + l * s * suv.TRACK
            p.z = float(height(p.x, p.y))
            pts.append(p)
    fl, fr, rl, rr = pts[1], pts[0], pts[3], pts[2]
    fwd = ((fl + fr) / 2 - (rl + rr) / 2).normalized()
    left = ((fl + rl) / 2 - (fr + rr) / 2).normalized()
    up = fwd.cross(left).normalized()
    left = up.cross(fwd).normalized()
    centre = (fl + fr + rl + rr) / 4
    origin = centre - fwd * ((suv.AX_F + suv.AX_R) / 2) - up * 0.045      # tyres bite a little
    m = Matrix((fwd, left, up)).transposed().to_4x4()
    m.translation = origin
    return m


def find_spot(cx=0.0, cy=0.0, rad=120.0):
    """A point on a long windward ramp: gentle slope, well up the dune."""
    best, bp = -1e9, (cx, cy)
    for x in np.arange(cx - rad, cx + rad, 6.0):
        for y in np.arange(cy - rad, cy + rad, 6.0):
            n = normal(x, y, 2.0)
            slope = math.degrees(math.acos(max(-1, min(1, n.z))))
            hh = float(height(x, y))
            sc = hh * 0.35 - abs(slope - 8.0) * 1.2 - 0.004 * ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if sc > best and slope < 12:
                best, bp = sc, (x, y)
    return bp


def tracks_z(X, Y, path, upto, depth=0.07):
    """Fine-patch height: dunes minus two tyre ruts along `path` behind the truck."""
    Z = height(X, Y)
    (px, py), hd = path
    f = np.array([math.cos(hd), math.sin(hd)])
    l = np.array([-math.sin(hd), math.cos(hd)])
    du = (X - px) * f[0] + (Y - py) * f[1]
    dv = (X - px) * l[0] + (Y - py) * l[1]
    behind = du < upto
    for s in (-1, 1):
        d = np.abs(dv - s * suv.TRACK)
        rut = np.clip(1 - (d / 0.17) ** 2, 0, 1)
        berm = np.exp(-((d - 0.27) / 0.07) ** 2)
        tread = 0.25 * (0.5 + 0.5 * np.sin(du * 26.0 + 9 * np.abs(dv - s * suv.TRACK) * 6))
        Z = Z + np.where(behind, -depth * rut * (0.8 + tread) + 0.025 * berm, 0.0)
    return Z


def footprints(mb, mat, pts):
    for (x, y, a) in pts:
        z = float(height(x, y))
        m = Matrix.Translation((x, y, z + 0.004)) @ Matrix.Rotation(a, 4, "Z")
        mb.obox(m, 0.26, 0.1, 0.012, mat)


def build(a):
    kit.reset()
    c = kit.coll("Sahara")
    sand = sand_material()
    sx, sy = find_spot()
    heading = WIND + math.radians(a.heading)          # climbing the windward ramp by default
    print(f"SPOT {sx:.1f} {sy:.1f} h={float(height(sx, sy)):.2f} heading={math.degrees(heading):.0f}")
    # far terrain (4 m grid), mid (1 m) and a fine patch with ruts round the truck
    P = 33.0
    mx, my = round(sx / 6.0) * 6.0, round(sy / 6.0) * 6.0          # snap so the three grids tile exactly
    fx, fy = round(sx), round(sy)
    fine = (fx - P, fy - P, fx + P, fy + P)
    mid = (mx - 222, my - 222, mx + 222, my + 222)
    grid_mesh("dunes_far", -1800, -1800, 1800, 1800, 6.0, sand, c, height, hole=mid)
    grid_mesh("dunes_mid", *mid, 1.0, sand, c, height, hole=fine)
    grid_mesh("dunes_near", *fine, 0.06, sand, c, lambda X, Y: tracks_z(X, Y, ((sx, sy), heading), suv.AX_F + 0.2))

    # the truck and its crew
    lib = suv.build("truck", paint=(0.8, 0.74, 0.62), dusty=True)
    truck = suv.instance(lib, name="truck", collection=c)
    truck.matrix_world = car_matrix(sx, sy, heading)
    cp = kit.coll("People")
    if a.mode == "drive":
        crew = {"driver": cast.make("tunde", "car_drive", cp), "front": cast.make("amina", "car_look_r", cp),
                "rear_l": cast.make("chidi", "car_look_l", cp), "rear_c": cast.make("zainab", "car", cp),
                "rear_r": cast.make("emeka", "car_look_r", cp)}
        suv.seat_people(truck, crew)
        # dust plume: a long box trailing the rear wheels, aligned to the truck
        dm = dust_material(a.dust)
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        d = bpy.context.active_object
        d.name = "dust_plume"
        kit.link(d, c)
        d.data.materials.append(dm)
        Lp, Wp, Hp = 30.0, 6.0, 4.2
        d.matrix_world = truck.matrix_world @ Matrix.Translation((suv.AX_R - Lp / 2 + 0.6, 0, Hp / 2 - 0.3)) @ Matrix.Diagonal((Lp, Wp, Hp, 1))
    else:
        # parked on the dune; everyone is out looking at the view
        f = Vector((math.cos(heading), math.sin(heading), 0))
        l = Vector((-math.sin(heading), math.cos(heading), 0))

        def stand(name, pose, df, dl, face):
            o = cast.make(name, pose, cp)
            p = Vector((sx, sy, 0)) + f * df + l * dl
            o.location = (p.x, p.y, float(height(p.x, p.y)) - 0.03)
            o.rotation_euler = (0, 0, heading + math.radians(face) + math.pi / 2)
            return o

        stand("tunde", "point", 4.6, 1.2, 10)
        stand("amina", "shade_eyes", 5.2, 2.6, -8)
        stand("chidi", "hands_hips", 3.9, -1.9, 20)
        stand("zainab", "stand_relaxed", 5.9, -0.6, -25)
        stand("emeka", "stand", 3.2, 3.4, 60)
        fm = kit.mat_plain("footprint", (0.33, 0.2, 0.09), rough=1.0)
        mb = kit.MB()
        rnd = random.Random(3)
        pts = []
        for k in range(46):
            t = k / 45
            for (df, dl) in [(4.6, 1.2), (5.2, 2.6), (3.9, -1.9), (5.9, -0.6), (3.2, 3.4)]:
                p = Vector((sx, sy, 0)) + f * (1.0 + (df - 1.0) * t) + l * ((1.2 if dl > 0 else -1.2) + (dl - (1.2 if dl > 0 else -1.2)) * t)
                if rnd.random() < 0.5:
                    pts.append((p.x + rnd.uniform(-0.1, 0.1), p.y + rnd.uniform(-0.1, 0.1), heading + rnd.uniform(-0.4, 0.4)))
        footprints(mb, fm, pts)
        mb.build("footprints", c)

    # sparse rocks and dry scrub in the hollows
    rnd = random.Random(8)
    for i in range(70):
        x, y = sx + rnd.uniform(-260, 260), sy + rnd.uniform(-260, 260)
        if abs(x - sx) < 14 and abs(y - sy) < 14:
            continue
        if float(height(x, y)) > 4.0 and rnd.random() < 0.85:      # keep them mostly in the low ground
            continue
        nm = rnd.choice(["namaqualand_boulder_02", "namaqualand_boulder_05", "namaqualand_rocks_01", "namaqualand_stones_01",
                         "wild_rooibos_bush", "wild_rooibos_bush"])
        try:
            kit.place(nm, (x, y, float(height(x, y)) - 0.15), rz=rnd.uniform(0, 6.28), scale=rnd.uniform(0.6, 1.6), collection=c)
        except Exception as e:  # noqa
            print("skip", nm, e)

    sky(a.sun_el, a.sun_rot, a.sky_strength, a.haze)
    w, h = [int(v) for v in a.res.split("x")]
    kit.render_setup(w, h, samples=a.samples, exposure=a.exposure, look="AgX - Medium High Contrast")
    bpy.context.scene.cycles.volume_bounces = 1
    try:
        bpy.context.scene.cycles.volume_step_rate = 2.0
    except Exception:
        pass

    # cameras, placed relative to the truck
    T = truck.matrix_world
    cc = kit.coll("Cameras")

    def cam(name, local, target_local, lens, dof=None):
        loc = T @ Vector(local)
        zt = float(height(loc.x, loc.y))
        if loc.z < zt + 0.35:
            loc.z = zt + 0.35
        return kit.camera(name, loc, T @ Vector(target_local), lens=lens, collection=cc, dof=dof, fstop=5.6)

    cams = {
        "drive": cam("drive", (11.5, -4.6, 0.75), (0.2, 0.0, 1.05), 62),
        "side": cam("side", (0.6, -8.5, 1.35), (0.1, 0.0, 1.15), 50),
        "front": cam("front", (9.5, 1.2, 1.25), (0.5, 0.0, 1.3), 70),
        "wide": cam("wide", (48.0, -30.0, 9.0), (-6.0, 4.0, 1.0), 30),
        "aerial": cam("aerial", (-16.0, -20.0, 30.0), (4.0, 0.0, 0.0), 28),
        "rear": cam("rear", (-9.0, 10.5, 2.4), (1.0, 0.0, 1.0), 38),
        "stop": cam("stop", (11.5, -6.5, 1.5), (3.2, 0.6, 1.1), 38),
        "stopwide": cam("stopwide", (22.0, 10.0, 3.5), (2.0, 0.5, 1.2), 32),
    }
    if a.save:
        bpy.context.scene.camera = cams["drive"]
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
    os.makedirs(a.out, exist_ok=True)
    for n in [x for x in a.cams.split(",") if x]:
        kit.render(cams[n], os.path.join(a.out, f"sahara_{n}.png"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cams", default="drive")
    ap.add_argument("--mode", default="drive", choices=["drive", "stop"])
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--out", default="/home/user/out")
    ap.add_argument("--save", default="")
    ap.add_argument("--heading", type=float, default=0.0, help="degrees off the wind direction")
    ap.add_argument("--sun-el", type=float, default=19.0)
    ap.add_argument("--sun-rot", type=float, default=350.0)
    ap.add_argument("--sky-strength", type=float, default=0.25)
    ap.add_argument("--haze", type=float, default=2.5)
    ap.add_argument("--dust", type=float, default=1.1)
    ap.add_argument("--exposure", type=float, default=-1.6)
    build(ap.parse_args())
