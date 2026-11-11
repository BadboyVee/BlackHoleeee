"""Add-on parts that sit on the body: lamps, mirrors, trim, aero, exhaust, engine, liners.

build(body_parts) -> dict.  Needs the dict returned by body.build() (for the lamp lenses and
door hinges) and ray-casts onto the finished panels so trims follow the real surface.
"""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from . import spec, util, materials, surface, body


def _col(key):
    return util.get_collection(spec.COLLECTIONS[key])


def _bvh(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    return [(BVHTree.FromObject(o, dg), o.matrix_world.copy()) for o in objs if o is not None]


def _cast(trees, origin, direction):
    """Nearest hit over several objects (object matrices are identity/translation here)."""
    best = None
    for t, mw in trees:
        inv = mw.inverted()
        loc, nrm, idx, dist = t.ray_cast(inv @ Vector(origin), inv.to_3x3() @ Vector(direction))
        if loc is not None and (best is None or dist < best[2]):
            best = (mw @ loc, (mw.to_3x3() @ nrm).normalized(), dist)
    return best


def _ribbon(name, pts, nrms, width, height, mat, col):
    """Raised strip following surface points/normals."""
    P = np.array(pts); N = np.array(nrms)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    B = np.cross(T, N); B /= np.linalg.norm(B, axis=1, keepdims=True) + 1e-12
    secs = []
    for p, n, b in zip(P, N, B):
        lo = p - n * 0.002
        secs.append([lo - b * width / 2, p + n * height - b * width * 0.32, p + n * height + b * width * 0.32,
                     lo + b * width / 2])
    v, f = util.loft(secs, closed_v=True, cap_start=True, cap_end=True)
    o = util.mesh_object(name, v, f, collection=col, material=mat)
    util.recalc_normals(o); util.shade_smooth(o, 50)
    return o


def _mirror_obj(o, name):
    """Mirrored copy across Y=0 (new mesh, flipped normals)."""
    c = util.duplicate(o, name)
    for v in c.data.vertices:
        v.co.y = -v.co.y
    c.location.y = -o.location.y
    c.rotation_euler = (-o.rotation_euler.x, o.rotation_euler.y, -o.rotation_euler.z)
    c.data.flip_normals()
    c.data.update()
    return c


def _x_on(obj, y, z):
    """x of the vertex of obj nearest to (y, z)."""
    co = np.array([tuple(obj.matrix_world @ v.co) for v in obj.data.vertices])
    i = np.argmin((co[:, 1] - y) ** 2 + (co[:, 2] - z) ** 2)
    return float(co[i, 0])


def build(bp):
    out = {}
    cb, cl, ca, cp = _col("body"), _col("lights"), _col("aero"), _col("powertrain")
    door_children = {"L": [], "R": []}

    # ------------------------------------------------ wheel-arch liners
    for key, w in spec.WHEELS.items():
        r = (spec.FRONT_ARCH_RADIUS if w["front"] else spec.REAR_ARCH_RADIUS) + 0.008
        s = w["side"]
        yw = float(surface.YW(w["x"])) - 0.03
        prof = [(0.06, s * 0.50 - w["y"]), (r, s * 0.50 - w["y"]), (r, s * yw - w["y"])]
        v, f = util.lathe(prof, segments=48, axis='Y', angle=math.radians(220))
        o = util.mesh_object("BODY_ArchLiner_" + key, v, f, collection=cb, material="plastic_black")
        util.recalc_normals(o)
        o.location = (w["x"], w["y"], w["z"])
        o.rotation_euler = (0, math.radians(20), 0)

    # ------------------------------------------------ headlights: LED modules, DRL, spot lamps
    spots = {}
    for s, sn in ((+1, "L"), (-1, "R")):
        lens = bp["headlight_lens"][sn]
        a = np.array([s * 0.505, 0.615]); b = np.array([s * 0.915, 0.644])
        drl = []
        for i, t in enumerate((0.13, 0.37, 0.62, 0.86)):
            y, z = a + (b - a) * t
            x = _x_on(lens, y, z) - 0.035
            led = util.box("LGT_HeadLED_%s_%d" % (sn, i), (0.012, 0.078, 0.020), (x, y, z), collection=cl,
                           material="emit_headlight", bevel_w=0.003)
            bez = util.box("LGT_HeadBezel_%s_%d" % (sn, i), (0.030, 0.092, 0.034), (x - 0.016, y, z),
                           collection=cl, material="chrome", bevel_w=0.004)
            drl.append((x + 0.012, y, z + 0.021))
        y0, z0 = a - (b - a) * 0.02
        y1, z1 = a + (b - a) * 1.02
        drl = [(_x_on(lens, y0, z0) - 0.022, y0, z0 + 0.021)] + drl + [(_x_on(lens, y1, z1) - 0.022, y1, z1 + 0.021)]
        v, f = util.tube(util.catmull_rom(drl, 6), 0.0035, segments=8)
        util.mesh_object("LGT_DRL_" + sn, v, f, collection=cl, material="emit_drl")
        ld = bpy.data.lights.new("LGT_HeadSpot_" + sn, 'SPOT')
        ld.spot_size = math.radians(70); ld.spot_blend = 0.6; ld.energy = 900; ld.shadow_soft_size = 0.05
        ld.color = (0.86, 0.93, 1.0)
        lo = bpy.data.objects.new("LGT_HeadSpot_" + sn, ld)
        cl.objects.link(lo)
        lo.location = (2.12, s * 0.70, 0.63)
        util.look_at(lo, (9.0, s * 0.9, 0.0))
        lo["base_energy"] = 900.0
        spots[sn] = lo
    out["head_spots"] = spots

    # ------------------------------------------------ tail bar backing (stops red leaking inside)
    tb = bp["tail_bar"]
    back = util.duplicate(tb, "BODY_TailBarBack", collection=cb)
    back.modifiers.clear()
    back.location.x += 0.010
    util.set_material(back, "void_black")

    # ------------------------------------------------ cabin light
    ld = bpy.data.lights.new("LGT_Cabin", 'AREA')
    ld.shape = 'RECTANGLE'; ld.size = 0.55; ld.size_y = 0.30; ld.energy = 14.0; ld.color = (0.80, 0.90, 1.0)
    lo = bpy.data.objects.new("LGT_Cabin", ld)
    cl.objects.link(lo)
    lo.location = (0.12, 0.0, 1.09)
    lo["base_energy"] = 14.0
    out["cabin_light"] = lo

    # ------------------------------------------------ mirrors (ride on the doors)
    for s, sn in ((+1, "L"), (-1, "R")):
        mx, my, mz = spec.MIRROR["x"], s * spec.MIRROR["y"], spec.MIRROR["z"]
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
        for v in bm.verts:
            taper = 1.0 - 0.35 * max(0.0, v.co.x)        # pointed toward the front
            v.co = Vector((v.co.x * 0.105 if v.co.x > -0.35 else -0.035, v.co.y * 0.045 * taper,
                           v.co.z * 0.055 * taper))
        h = util.bmesh_object("BODY_Mirror_%s" % sn, bm, collection=_col("doors"), material="paint_light")
        util.shade_smooth(h, 40)
        h.location = (mx, my, mz)
        g = util.cylinder("BODY_MirrorGlass_%s" % sn, 0.046, 0.003, axis='X', location=(mx - 0.0365, my, mz),
                          collection=_col("doors"), material="chrome", segments=32)
        g.scale = (1, 0.92, 1.12)
        v, f = util.tube(util.catmull_rom([(0.80, s * 0.900, 0.842), (0.77, s * 0.960, 0.852), (mx + 0.01, my - s * 0.03, mz - 0.02)], 6),
                         0.012, segments=10)
        st = util.mesh_object("BODY_MirrorStalk_%s" % sn, v, f, collection=_col("doors"), material="paint_black")
        door_children[sn] += [h, g, st]

    # ------------------------------------------------ wiper (parked on the centre line)
    xs = np.linspace(1.385, 0.88, 14)
    pts = [(x, 0.0, float(surface.ZR(x)) + 0.004) for x in xs]
    v, f = util.tube(pts, 0.006, segments=8)
    util.mesh_object("BODY_WiperArm", v, f, collection=cb, material="plastic_black")
    v, f = util.sweep([(-0.001, -0.009), (0.008, -0.004), (0.008, 0.004), (-0.001, 0.009)], pts[3:], up=(0, 0, 1))
    util.mesh_object("BODY_WiperBlade", v, f, collection=cb, material="rubber_seal")

    # ------------------------------------------------ C-line trim (polished aluminium)
    L = body.lines()
    low = np.concatenate([L['c_arc'][:-1], L['c_low']])
    inner_pt = np.array([0.2, 0.75])

    def offset_path(path, d):
        t = np.gradient(path, axis=0)
        n = np.stack([-t[:, 1], t[:, 0]], axis=1)
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        sign = np.sign(np.einsum('ij,ij->i', n, path - inner_pt))
        return path + n * sign[:, None] * d

    def project(path2d, targets):
        trees = _bvh(targets)
        P, N = [], []
        for x, z in path2d:
            h = _cast(trees, (x, 2.0, z), (0, -1, 0))
            if h is not None and h[0].y > 0.3:
                P.append(tuple(h[0])); N.append(tuple(h[1]))
        return P, N

    fixed = [bp["rear_clam"], bp["sill_L"], bp["canopy_frame"], bp["front_clam"]]
    P, N = project(util.resample_polyline(offset_path(low, 0.009), 150), fixed)
    if len(P) > 4:
        t = _ribbon("BODY_CLine_L", P, N, 0.016, 0.004, "alu_polished", cb)
        _mirror_obj(t, "BODY_CLine_R")
    P, N = project(util.resample_polyline(offset_path(L['c_up'], 0.004), 60), [bp["door_L"][1]])
    if len(P) > 4:
        t = _ribbon("BODY_CLineTop_L", P, N, 0.012, 0.003, "alu_polished", _col("doors"))
        door_children["L"].append(t)
        door_children["R"].append(_mirror_obj(t, "BODY_CLineTop_R"))

    # ------------------------------------------------ tricolour on the sill behind the front wheel
    trees = _bvh([bp["sill_L"]])
    for i, mat in enumerate(("flag_blue", "flag_white", "flag_red")):
        x = 0.66 + i * 0.034
        h = _cast(trees, (x, 2.0, 0.315), (0, -1, 0))
        if h is None:
            continue
        for s, sn in ((+1, "L"), (-1, "R")):
            o = util.box("BODY_Flag_%s_%d" % (sn, i), (0.030, 0.004, 0.055), (x, s * (h[0].y + 0.001), 0.315),
                         collection=cb, material=mat, bevel_w=0.001)
            o.rotation_euler = (0, math.radians(-28), 0)

    # ------------------------------------------------ front splitter
    xs = np.linspace(1.84, 2.405, 24)
    half = [(float(x), float(surface.YW(x)) + 0.014) for x in xs] + [(2.428, 0.20), (2.434, 0.0)]
    outline = np.array(half + [(x, -y) for x, y in half[::-1]][1:])
    v, f = util.extrude_outline(outline, 0.018, plane='XY', offset=0.142)
    sp = util.mesh_object("AERO_Splitter", v, f, collection=ca, material="carbon_gloss", smooth=False)
    util.recalc_normals(sp); util.bevel(sp, 0.004, 2, 40); util.shade_smooth(sp, 40)
    for s in (+1, -1):                                   # horizontal blade across each lower intake
        util.box("BODY_IntakeBlade_%s" % ("L" if s > 0 else "R"), (0.10, 0.50, 0.014), (2.02, s * 0.64, 0.345),
                 collection=cb, material="carbon_gloss", bevel_w=0.004).rotation_euler = (0, 0, s * math.radians(-24))

    # ------------------------------------------------ horseshoe badge (plain red oval) + centre bar
    gx = _x_on(bp["horseshoe_grille"], 0.0, 0.47)
    bd = util.cylinder("BODY_Badge", 0.05, 0.008, axis='X', location=(gx + 0.02, 0, 0.475), collection=cb,
                       material="badge_red", segments=40, bevel_w=0.002)
    bd.scale = (1, 1.0, 0.56)
    br = util.cylinder("BODY_BadgeRim", 0.054, 0.006, axis='X', location=(gx + 0.017, 0, 0.475), collection=cb,
                       material="chrome", segments=40, bevel_w=0.002)
    br.scale = (1, 1.0, 0.58)
    util.box("BODY_HorseshoeBar", (0.012, 0.012, 0.335), (gx + 0.012, 0, 0.397), collection=cb,
             material="plastic_gloss", bevel_w=0.003)

    # ------------------------------------------------ rear: diffuser, strakes, exhaust
    secs = []
    for x, z in ((-1.78, 0.150), (-1.95, 0.175), (-2.12, 0.225), (-2.275, 0.300)):
        secs.append([(x, -0.82, z), (x, 0.82, z), (x, 0.82, z - 0.016), (x, -0.82, z - 0.016)])
    v, f = util.loft(secs, closed_v=True, cap_start=True, cap_end=True)
    d = util.mesh_object("AERO_Diffuser", v, f, collection=ca, material="carbon_gloss", smooth=False)
    util.recalc_normals(d); util.bevel(d, 0.003, 2, 40)
    strake = [(-1.78, 0.125), (-2.285, 0.125), (-2.285, 0.335), (-2.20, 0.285), (-1.95, 0.185)]
    for i, y in enumerate((-0.70, -0.46, -0.22, 0.22, 0.46, 0.70)):
        v, f = util.extrude_outline(strake, 0.014, plane='XZ', offset=y - 0.007)
        o = util.mesh_object("AERO_Strake_%d" % i, v, f, collection=ca, material="carbon_gloss", smooth=False)
        util.recalc_normals(o); util.bevel(o, 0.003, 2, 40)
    util.box("BODY_TailCentre", (0.26, 0.36, 0.25), (-2.07, 0, 0.44), collection=cb, material="plastic_gloss",
             bevel_w=0.02)
    for s, sn in ((+1, "L"), (-1, "R")):
        prof = util.rounded_rect(0.075, 0.17, 0.028, seg=5)
        v, f = util.sweep(prof, [(-1.96, s * 0.40, 0.49), (-2.10, s * 0.40, 0.49), (-2.235, s * 0.40, 0.49)],
                          caps=False, up=(0, 0, 1))
        e = util.mesh_object("PWR_Exhaust_" + sn, v, f, collection=cp, material="titanium")
        util.recalc_normals(e); util.solidify(e, 0.005, offset=-1.0); util.bevel(e, 0.0015, 2, 40)
        util.box("PWR_ExhaustCore_" + sn, (0.02, 0.16, 0.066), (-1.99, s * 0.40, 0.49), collection=cp,
                 material="void_black")

    # ------------------------------------------------ active rear wing on a pivot
    secs = []
    for y in np.linspace(-0.68, 0.68, 13):
        u = (y / 0.68) ** 2
        le, te = -1.872 + 0.15 * u, -2.215 + 0.12 * u
        zc = 0.896 - 0.022 * u
        ch = le - te
        sec = []
        for t, th in ((0.0, 0.0), (0.08, 0.55), (0.3, 1.0), (0.6, 0.75), (0.9, 0.25), (1.0, 0.0)):
            sec.append((le - ch * t, y, zc + 0.016 * th))
        for t, th in ((0.9, 0.12), (0.6, 0.3), (0.3, 0.35), (0.08, 0.25)):
            sec.append((le - ch * t, y, zc - 0.016 * th))
        secs.append(sec)
    v, f = util.loft(secs, closed_v=True, cap_start=True, cap_end=True)
    wing = util.mesh_object("AERO_Wing", v, f, collection=ca, material="paint_dark")
    util.recalc_normals(wing); util.subsurf(wing, 1); util.shade_smooth(wing)
    piv = util.empty("AERO_WingPivot", (-1.90, 0, 0.885), collection=ca, size=0.1)
    piv["base_z"] = 0.885
    for s in (+1, -1):
        st = util.box("AERO_WingStrut_%s" % ("L" if s > 0 else "R"), (0.05, 0.03, 0.22), (-2.02, s * 0.36, 0.775),
                      collection=ca, material="alu_dark", bevel_w=0.006)
        util.parent(st, piv)
    util.parent(wing, piv)
    out["wing_pivot"] = piv

    # ------------------------------------------------ engine under the rear glass
    util.box("PWR_EngineBlock", (1.02, 0.66, 0.36), (-1.22, 0, 0.60), collection=cp, material="alu_dark", bevel_w=0.03)
    for s, sn in ((+1, "L"), (-1, "R")):
        o = util.cylinder("PWR_Plenum_" + sn, 0.105, 0.70, axis='X', location=(-1.22, s * 0.20, 0.835),
                          collection=cp, material="carbon_gloss", segments=32, bevel_w=0.05)
        o.scale = (1, 1.0, 0.72)
        for i in range(8):
            util.cylinder("PWR_Runner_%s_%d" % (sn, i), 0.028, 0.10, axis='Z',
                          location=(-1.52 + i * 0.086, s * 0.20, 0.765), collection=cp, material="alu_brushed",
                          segments=16)
    util.box("PWR_EngineSpine", (0.92, 0.05, 0.03), (-1.22, 0, 0.80), collection=cp, material="badge_red", bevel_w=0.008)

    out["door_children"] = door_children
    return out
