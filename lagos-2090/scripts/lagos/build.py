"""Lagos 2090 - procedural architecture and street furniture.

Everything is built as plain meshes through MB (a quad soup builder) so that shots
stay light: one object per building, material slots by role.
"""
import bpy, math, random
from mathutils import Vector, Matrix
from . import core, mats

Z = Vector((0, 0, 1))

# Lagos facade paints (linear-ish RGB): cream, faded blue, ochre yellow, terracotta,
# faded green, dusty pink, off-white, sky blue, mustard
PAINTS = [(0.62, 0.52, 0.36), (0.20, 0.36, 0.50), (0.70, 0.47, 0.12), (0.52, 0.20, 0.11),
          (0.26, 0.40, 0.27), (0.60, 0.36, 0.30), (0.66, 0.63, 0.56), (0.30, 0.50, 0.60),
          (0.63, 0.50, 0.20), (0.45, 0.47, 0.42)]


class MB:
    """Quad-soup mesh builder with per-face material index and UVs."""

    def __init__(self):
        self.v = []; self.f = []; self.mi = []; self.uv = []

    def quad(self, a, b, c, d, m=0, uv=None):
        i = len(self.v)
        self.v += [tuple(a), tuple(b), tuple(c), tuple(d)]
        self.f.append((i, i + 1, i + 2, i + 3)); self.mi.append(m)
        self.uv.append(uv or ((0, 0), (1, 0), (1, 1), (0, 1)))

    def tri(self, a, b, c, m=0):
        i = len(self.v)
        self.v += [tuple(a), tuple(b), tuple(c)]
        self.f.append((i, i + 1, i + 2)); self.mi.append(m)
        self.uv.append(((0, 0), (1, 0), (0.5, 1)))

    def obox(self, o, ux, uy, uz, m=0, skip=""):
        """Oriented box: corner o and three edge vectors (right-handed)."""
        o, ux, uy, uz = Vector(o), Vector(ux), Vector(uy), Vector(uz)
        p = lambda a, b, c: o + ux * a + uy * b + uz * c
        if "b" not in skip: self.quad(p(0, 1, 0), p(1, 1, 0), p(1, 0, 0), p(0, 0, 0), m)   # bottom
        if "t" not in skip: self.quad(p(0, 0, 1), p(1, 0, 1), p(1, 1, 1), p(0, 1, 1), m)   # top
        if "f" not in skip: self.quad(p(0, 0, 0), p(1, 0, 0), p(1, 0, 1), p(0, 0, 1), m)   # -uy
        if "k" not in skip: self.quad(p(1, 1, 0), p(0, 1, 0), p(0, 1, 1), p(1, 1, 1), m)   # +uy
        if "l" not in skip: self.quad(p(0, 1, 0), p(0, 0, 0), p(0, 0, 1), p(0, 1, 1), m)   # -ux
        if "r" not in skip: self.quad(p(1, 0, 0), p(1, 1, 0), p(1, 1, 1), p(1, 0, 1), m)   # +ux

    def box(self, lo, hi, m=0, skip=""):
        lo, hi = Vector(lo), Vector(hi)
        d = hi - lo
        self.obox(lo, (d.x, 0, 0), (0, d.y, 0), (0, 0, d.z), m, skip)

    def cbox(self, c, size, m=0, rz=0.0, skip=""):
        """Box by base-centre + size, rotated about Z."""
        c = Vector(c); sx, sy, sz = size
        r = Matrix.Rotation(rz, 3, "Z")
        ux, uy = r @ Vector((sx, 0, 0)), r @ Vector((0, sy, 0))
        self.obox(c - ux / 2 - uy / 2, ux, uy, (0, 0, sz), m, skip)

    def cyl(self, p0, p1, r0, r1=None, m=0, seg=10, caps=True):
        p0, p1 = Vector(p0), Vector(p1)
        r1 = r0 if r1 is None else r1
        ax = (p1 - p0).normalized()
        a = ax.orthogonal().normalized(); b = ax.cross(a)
        ring = lambda p, r: [p + (a * math.cos(t) + b * math.sin(t)) * r for t in [2 * math.pi * i / seg for i in range(seg)]]
        A, B = ring(p0, r0), ring(p1, r1)
        for i in range(seg):
            j = (i + 1) % seg
            self.quad(A[i], A[j], B[j], B[i], m, ((i / seg, 0), ((i + 1) / seg, 0), ((i + 1) / seg, 1), (i / seg, 1)))
        if caps:
            for i in range(1, seg - 1):
                self.tri(B[0], B[i], B[i + 1], m)
                self.tri(A[0], A[i + 1], A[i], m)

    def tube(self, pts, r, m=0, seg=6):
        """Tube along a polyline."""
        pts = [Vector(p) for p in pts]
        rings = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            a = t.cross(Z)
            if a.length < 1e-4:
                a = Vector((1, 0, 0))
            a.normalize(); b = t.cross(a)
            rr = r(i / max(1, len(pts) - 1)) if callable(r) else r
            rings.append([p + (a * math.cos(u) + b * math.sin(u)) * rr for u in [2 * math.pi * k / seg for k in range(seg)]])
        for i in range(len(rings) - 1):
            for k in range(seg):
                j = (k + 1) % seg
                self.quad(rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k], m,
                          ((k / seg, i / len(rings)), ((k + 1) / seg, i / len(rings)), ((k + 1) / seg, (i + 1) / len(rings)), (k / seg, (i + 1) / len(rings))))

    def obj(self, name, materials, smooth=False, collection=None, loc=(0, 0, 0), rz=0.0, color=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        for mt in materials:
            me.materials.append(mt)
        me.polygons.foreach_set("material_index", self.mi)
        uvl = me.uv_layers.new(name="UVMap")
        flat = [c for face in self.uv for co in face for c in co]
        uvl.data.foreach_set("uv", flat)
        if smooth:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.update()
        o = bpy.data.objects.new(name, me)
        o.location = loc; o.rotation_euler = (0, 0, rz)
        if color is not None:
            o.color = (*color, 1.0)
        core.link(o, collection)
        return o


class Frame:
    """Facade frame: origin o, along-wall u, outward normal n (u x Z = n)."""

    def __init__(self, o, u):
        self.o = Vector(o); self.u = Vector(u).normalized(); self.n = self.u.cross(Z)

    def p(self, uu, zz, out=0.0):
        return self.o + self.u * uu + Z * zz + self.n * out


def facade_frames(w, d):
    return {"front": (Frame((-w / 2, -d / 2, 0), (1, 0, 0)), w), "right": (Frame((w / 2, -d / 2, 0), (0, 1, 0)), d),
            "back": (Frame((w / 2, d / 2, 0), (-1, 0, 0)), w), "left": (Frame((-w / 2, d / 2, 0), (0, -1, 0)), d)}


# material slot roles for buildings
WALL, GLASS, DARK, CONC, TRIM, CORR, ACU, SHUT, BREEZE, TANK, SOLAR, STEEL = range(12)


def building_mats(lit=0.12, grime=0.6):
    return [mats.painted("wall_paint", object_color=True, grime=grime),
            mats.glass("win_glass", lit=lit),
            mats.plain("dark_metal", (0.03, 0.03, 0.035), 0.5, 0.6),
            mats.pbr("concrete", "conc_trim", scale=0.4, dirt=0.5, val=0.8),
            mats.painted("trim_paint", (0.62, 0.60, 0.55), grime=grime * 0.8),
            mats.pbr("corrugated", "corr_roof", scale=0.5, dirt=0.4, tint=(0.75, 0.62, 0.5)),
            mats.plain("ac_unit", (0.55, 0.55, 0.52), 0.55, 0.3),
            mats.pbr("corrugated", "shutter", scale=0.9, tint=(0.25, 0.42, 0.5), rot=(0, math.pi / 2, 0)),
            breeze_block(),
            mats.plain("tank_black", (0.012, 0.012, 0.014), 0.42),
            mats.solar_panel(),
            mats.pbr("metal", "steel_frame", scale=1.0, tint=(0.45, 0.45, 0.45), dirt=0.3)]


def breeze_block():
    def make():
        t = mats.NT("breeze_block")
        vec = t.coords("object", 1.0)
        sep = t.n("ShaderNodeSeparateXYZ"); t.l(vec, sep.inputs[0])
        g = t.n("ShaderNodeNewGeometry"); sn = t.n("ShaderNodeSeparateXYZ"); t.l(g.outputs["Normal"], sn.inputs[0])
        u = t.math("ADD", t.math("MULTIPLY", sep.outputs["X"], t.math("ABSOLUTE", sn.outputs["Y"])),
                   t.math("MULTIPLY", sep.outputs["Y"], t.math("ABSOLUTE", sn.outputs["X"])))
        fu = t.math("FRACT", t.math("DIVIDE", u, 0.2)); fz = t.math("FRACT", t.math("DIVIDE", sep.outputs["Z"], 0.2))
        du = t.math("ABSOLUTE", t.math("SUBTRACT", fu, 0.5)); dz = t.math("ABSOLUTE", t.math("SUBTRACT", fz, 0.5))
        hole = t.math("LESS_THAN", t.math("MAXIMUM", du, dz), 0.3)
        col = t.mix(hole, (0.5, 0.47, 0.42), (0.01, 0.01, 0.012))
        t.bsdf(Base_Color=col, Roughness=0.9)
        return t.mat
    return mats._get(("breeze",), make)


def facade_far(name="facade_far", lit=0.1, bay=3.2, fh=3.1):
    """Distant buildings: one box, windows painted by the shader (object colour = paint)."""
    def make():
        t = mats.NT(name)
        vec = t.coords("object", 1.0)
        sep = t.n("ShaderNodeSeparateXYZ"); t.l(vec, sep.inputs[0])
        g = t.n("ShaderNodeNewGeometry"); sn = t.n("ShaderNodeSeparateXYZ"); t.l(g.outputs["Normal"], sn.inputs[0])
        u = t.math("ADD", t.math("MULTIPLY", sep.outputs["X"], t.math("ABSOLUTE", sn.outputs["Y"])),
                   t.math("MULTIPLY", sep.outputs["Y"], t.math("ABSOLUTE", sn.outputs["X"])))
        cu = t.math("DIVIDE", u, bay); cz = t.math("DIVIDE", sep.outputs["Z"], fh)
        fu = t.math("FRACT", cu); fz = t.math("FRACT", cz)
        inu = t.math("MULTIPLY", t.math("GREATER_THAN", fu, 0.22), t.math("LESS_THAN", fu, 0.78))
        inz = t.math("MULTIPLY", t.math("GREATER_THAN", fz, 0.32), t.math("LESS_THAN", fz, 0.78))
        side = t.math("LESS_THAN", t.math("ABSOLUTE", sn.outputs["Z"]), 0.5)
        win = t.math("MULTIPLY", t.math("MULTIPLY", inu, inz), side)
        wn = t.n("ShaderNodeTexWhiteNoise", noise_dimensions="3D")
        cid = t.n("ShaderNodeCombineXYZ")
        t.l(t.math("FLOOR", cu), cid.inputs[0]); t.l(t.math("FLOOR", cz), cid.inputs[1]); t.l(sn.outputs["X"], cid.inputs[2])
        t.l(cid.outputs[0], wn.inputs["Vector"])
        oi = t.n("ShaderNodeObjectInfo")
        n = t.noise(t.coords("world", (0.6, 0.6, 0.05)), 1.5, 4.0, 0.6).outputs["Fac"]
        wall = t.mix(t.math("MULTIPLY", t.ramp(n, [(0.45, (0, 0, 0)), (0.85, (1, 1, 1))]), 0.6), oi.outputs["Color"], (0.06, 0.05, 0.045))
        col = t.mix(win, wall, (0.02, 0.03, 0.035))
        on = t.math("MULTIPLY", t.math("GREATER_THAN", wn.outputs["Value"], 1.0 - lit), win)
        t.bsdf(Base_Color=col, Roughness=t.mix(win, 0.85, 0.12), Emission_Color=(1.0, 0.68, 0.36),
               Emission_Strength=t.math("MULTIPLY", on, 1.2))
        return t.mat
    return mats._get(("ffar", name), make)


# ----------------------------------------------------------------------------- roof kit
def water_tank(mb, c, r=0.62, h=1.45, stand=1.1, m_tank=TANK, m_steel=STEEL):
    c = Vector(c)
    if stand > 0:
        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            mb.cbox(c + Vector((dx * r * 0.75, dy * r * 0.75, 0)), (0.06, 0.06, stand), m_steel)
        mb.cbox(c + Vector((0, 0, stand - 0.06)), (r * 1.7, r * 1.7, 0.06), m_steel)
    b = c + Vector((0, 0, stand))
    mb.cyl(b, b + Vector((0, 0, h * 0.82)), r, r, m_tank, 16)
    for k in range(1, 4):  # moulded ribs
        zz = b + Vector((0, 0, h * 0.82 * k / 4))
        mb.cyl(zz - Vector((0, 0, 0.03)), zz + Vector((0, 0, 0.03)), r * 1.035, r * 1.035, m_tank, 16, caps=False)
    mb.cyl(b + Vector((0, 0, h * 0.82)), b + Vector((0, 0, h * 0.97)), r, r * 0.35, m_tank, 16)
    mb.cyl(b + Vector((0, 0, h * 0.97)), b + Vector((0, 0, h)), r * 0.3, r * 0.3, m_tank, 12)


def dish(mb, c, r=0.45, az=0.0, m=TRIM, m_steel=STEEL):
    c = Vector(c)
    mb.cyl(c, c + Vector((0, 0, 0.9)), 0.025, 0.025, m_steel, 6)
    d = Vector((math.cos(az), math.sin(az), 0.75)).normalized()
    hub = c + Vector((0, 0, 0.9))
    a = d.orthogonal().normalized(); b = d.cross(a)
    seg = 14
    rim = [hub + d * 0.14 + (a * math.cos(2 * math.pi * i / seg) + b * math.sin(2 * math.pi * i / seg)) * r for i in range(seg)]
    for i in range(seg):
        mb.tri(hub, rim[i], rim[(i + 1) % seg], m)
        mb.tri(hub - d * 0.01, rim[(i + 1) % seg], rim[i], m)
    mb.cyl(hub + d * 0.14 + a * r, hub + d * 0.55, 0.012, 0.012, m_steel, 5)
    mb.cyl(hub + d * 0.5, hub + d * 0.62, 0.035, 0.035, m_steel, 6)


def solar_array(mb, c, cols=4, rows=2, pw=1.05, ph=1.75, tilt=math.radians(14), rz=0.0, lift=0.45, m=SOLAR, m_steel=STEEL):
    """Rows of framed PV panels on a light steel rack; c = base centre."""
    c = Vector(c)
    R = Matrix.Rotation(rz, 3, "Z")
    ux = R @ Vector((1, 0, 0)); uy = R @ Vector((0, math.cos(tilt), math.sin(tilt)))
    nz = ux.cross(uy)
    tw, th = cols * (pw + 0.03), rows * (ph + 0.03)
    o = c - ux * tw / 2 - (R @ Vector((0, 1, 0))) * (th * math.cos(tilt) / 2) + Z * lift
    for i in range(cols):
        for j in range(rows):
            p = o + ux * (i * (pw + 0.03)) + uy * (j * (ph + 0.03))
            mb.obox(p, ux * pw, uy * ph, nz * 0.035, m_steel, skip="t")
            q = p + nz * 0.036
            mb.quad(q, q + ux * pw, q + ux * pw + uy * ph, q + uy * ph, m, ((0, 0), (pw / 1.0, 0), (pw / 1.0, ph / 1.0), (0, ph / 1.0)))
    for i in range(cols + 1):  # legs
        for jj in (0.08, 0.92):
            p = o + ux * (i * (pw + 0.03) * 0.999) + uy * (th * jj)
            mb.cyl(Vector((p.x, p.y, c.z)), p, 0.02, 0.02, m_steel, 5, caps=False)


# ----------------------------------------------------------------------------- apartment
def apartment(name, w=22.0, d=11.0, floors=4, color=None, seed=0, lod=2, fh=3.05, bay=3.3, shop=True,
              balcony="front", roof=True, loc=(0, 0, 0), rz=0.0, collection=None, signs=None, lit=0.12,
              solar=0.5, tanks=None, sides=("front", "right", "back", "left")):
    """Mid-rise Lagos apartment block. Front facade faces local -Y. Returns the object;
    sign boards (if any) are separate child objects."""
    rnd = random.Random(seed)
    color = color or rnd.choice(PAINTS)
    mb = MB()
    gh = 3.5 if shop else fh
    zf = [0.0, gh] + [gh + fh * i for i in range(1, floors)]
    top = zf[-1] + fh if floors > 1 else gh
    if floors == 1:
        zf = [0.0]; top = gh
    style = rnd.choice(["solid", "rail", "rail", "solid"])
    wtype = rnd.choice(["louvre", "wide", "louvre"])
    bal_depth = rnd.choice([1.15, 1.35, 1.5])
    frames = facade_frames(w, d)
    sign_objs = []
    for side, (F, length) in frames.items():
        nb = max(1, round(length / bay)); bw = length / nb
        has_bal = balcony in (side, "all") or (balcony == "front+back" and side in ("front", "back"))
        if side not in sides:  # blind wall, single quad per side
            mb.quad(F.p(0, 0), F.p(length, 0), F.p(length, top), F.p(0, top), WALL)
            continue
        stair = rnd.randrange(nb) if nb > 3 and side in ("front", "back") else -1
        for fi, z0 in enumerate(zf):
            z1 = zf[fi + 1] if fi + 1 < len(zf) else top
            for bi in range(nb):
                u0, u1 = bi * bw, (bi + 1) * bw
                if fi == 0 and shop and side == "front":
                    # shop front: roller shutter or dark open bay between piers
                    pier = 0.28
                    mb.quad(F.p(u0, z0), F.p(u0 + pier, z0), F.p(u0 + pier, z1), F.p(u0, z1), WALL)
                    mb.quad(F.p(u1 - pier, z0), F.p(u1, z0), F.p(u1, z1), F.p(u1 - pier, z1), WALL)
                    hz = z0 + 2.75
                    mb.quad(F.p(u0 + pier, hz), F.p(u1 - pier, hz), F.p(u1 - pier, z1), F.p(u0 + pier, z1), WALL)
                    openb = rnd.random() < 0.45
                    dep = -2.2 if openb else -0.12
                    mb.quad(F.p(u0 + pier, z0, dep), F.p(u1 - pier, z0, dep), F.p(u1 - pier, hz, dep), F.p(u0 + pier, hz, dep), DARK if openb else SHUT)
                    mb.quad(F.p(u0 + pier, z0), F.p(u0 + pier, z0, dep), F.p(u0 + pier, hz, dep), F.p(u0 + pier, hz), TRIM)
                    mb.quad(F.p(u1 - pier, z0, dep), F.p(u1 - pier, z0), F.p(u1 - pier, hz), F.p(u1 - pier, hz, dep), TRIM)
                    mb.quad(F.p(u0 + pier, hz, dep), F.p(u1 - pier, hz, dep), F.p(u1 - pier, hz), F.p(u0 + pier, hz), TRIM)
                    if openb:
                        mb.quad(F.p(u0 + pier, z0 + 0.01, dep), F.p(u0 + pier, z0 + 0.01), F.p(u1 - pier, z0 + 0.01), F.p(u1 - pier, z0 + 0.01, dep), CONC)
                    if signs and rnd.random() < 0.9:
                        sp = signs[rnd.randrange(len(signs))]
                        sw, sh = bw - 0.5, 0.62
                        so = sign_board(sp, sw, sh, emit=rnd.choice([0.0, 0.0, 1.2]))
                        so.location = F.p((u0 + u1) / 2, hz + 0.06 + sh / 2, 0.06)
                        so.rotation_euler = (math.pi / 2, 0, math.atan2(F.u.y, F.u.x))
                        sign_objs.append(so)
                    continue
                if bi == stair and fi > 0:
                    mb.quad(F.p(u0, z0), F.p(u1, z0), F.p(u1, z0 + 0.4), F.p(u0, z0 + 0.4), WALL)
                    mb.quad(F.p(u0, z0 + 0.4), F.p(u0 + 0.5, z0 + 0.4), F.p(u0 + 0.5, z1 - 0.3), F.p(u0, z1 - 0.3), WALL)
                    mb.quad(F.p(u1 - 0.5, z0 + 0.4), F.p(u1, z0 + 0.4), F.p(u1, z1 - 0.3), F.p(u1 - 0.5, z1 - 0.3), WALL)
                    mb.quad(F.p(u0, z1 - 0.3), F.p(u1, z1 - 0.3), F.p(u1, z1), F.p(u0, z1), WALL)
                    mb.quad(F.p(u0 + 0.5, z0 + 0.4, -0.08), F.p(u1 - 0.5, z0 + 0.4, -0.08), F.p(u1 - 0.5, z1 - 0.3, -0.08), F.p(u0 + 0.5, z1 - 0.3, -0.08), BREEZE)
                    continue
                door = has_bal and fi > 0 and rnd.random() < 0.5
                if door:
                    ww, wz0, wz1 = 0.95, z0 + 0.02, z0 + 2.15
                elif wtype == "wide":
                    ww, wz0, wz1 = min(2.0, bw - 0.9), z0 + 0.95, z0 + 2.3
                else:
                    ww, wz0, wz1 = min(1.35, bw - 0.9), z0 + 1.0, z0 + 2.25
                if fi == 0 and not (shop and side == "front"):
                    wz0 += 0.25; wz1 += 0.25
                c = (u0 + u1) / 2 + (rnd.uniform(-0.25, 0.25) if door else 0.0)
                a, b = c - ww / 2, c + ww / 2
                dep = -0.16
                # wall around the opening
                mb.quad(F.p(u0, z0), F.p(u1, z0), F.p(u1, wz0), F.p(u0, wz0), WALL)
                mb.quad(F.p(u0, wz1), F.p(u1, wz1), F.p(u1, z1), F.p(u0, z1), WALL)
                mb.quad(F.p(u0, wz0), F.p(a, wz0), F.p(a, wz1), F.p(u0, wz1), WALL)
                mb.quad(F.p(b, wz0), F.p(u1, wz0), F.p(u1, wz1), F.p(b, wz1), WALL)
                # reveals
                mb.quad(F.p(a, wz0), F.p(a, wz0, dep), F.p(a, wz1, dep), F.p(a, wz1), TRIM)
                mb.quad(F.p(b, wz0, dep), F.p(b, wz0), F.p(b, wz1), F.p(b, wz1, dep), TRIM)
                mb.quad(F.p(a, wz1, dep), F.p(b, wz1, dep), F.p(b, wz1), F.p(a, wz1), TRIM)
                mb.quad(F.p(a, wz0), F.p(b, wz0), F.p(b, wz0, dep), F.p(a, wz0, dep), TRIM)
                mb.quad(F.p(a, wz0, dep), F.p(b, wz0, dep), F.p(b, wz1, dep), F.p(a, wz1, dep), DARK if door and rnd.random() < 0.3 else GLASS)
                if lod >= 2:
                    # louvre blades / mullions and burglar-proof bars
                    nm = 2 if ww > 1.6 else 1
                    for k in range(1, nm + 1):
                        x = a + ww * k / (nm + 1)
                        mb.obox(F.p(x - 0.02, wz0, dep), F.u * 0.04, F.n * 0.05, Z * (wz1 - wz0), DARK, skip="bt")
                    if not door:
                        nbl = 7 if wtype == "louvre" else 0
                        for k in range(1, nbl):
                            zz = wz0 + (wz1 - wz0) * k / nbl
                            mb.quad(F.p(a, zz, dep + 0.02), F.p(b, zz, dep + 0.02), F.p(b, zz + 0.015, dep + 0.07), F.p(a, zz + 0.015, dep + 0.07), DARK)
                        if rnd.random() < 0.6:
                            for k in range(1, 6):
                                x = a + ww * k / 6
                                mb.obox(F.p(x - 0.008, wz0, -0.03), F.u * 0.016, F.n * 0.016, Z * (wz1 - wz0), DARK, skip="bt")
                # sun-shade eyebrow
                if lod >= 1 and not has_bal and not door:
                    mb.obox(F.p(a - 0.2, wz1 + 0.08, 0), F.u * (ww + 0.4), F.n * 0.5, Z * 0.08, TRIM, skip="f")
                    mb.obox(F.p(a - 0.12, wz0 - 0.07, 0), F.u * (ww + 0.24), F.n * 0.1, Z * 0.07, TRIM, skip="f")
                # split AC condenser
                if lod >= 1 and not door and fi > 0 and rnd.random() < 0.28:
                    ax = b + 0.12 if b + 0.95 < u1 else a - 0.95
                    off = bal_depth * 0.0 + 0.04
                    mb.obox(F.p(ax, wz0 - 0.1, off), F.u * 0.8, F.n * 0.3, Z * 0.55, ACU)
                    mb.quad(F.p(ax + 0.1, wz0 - 0.02, off + 0.305), F.p(ax + 0.55, wz0 - 0.02, off + 0.305), F.p(ax + 0.55, wz0 + 0.38, off + 0.305), F.p(ax + 0.1, wz0 + 0.38, off + 0.305), DARK)
                    mb.obox(F.p(ax + 0.05, wz0 - 0.14, 0), F.u * 0.7, F.n * 0.34, Z * 0.04, STEEL)
            # balcony slab + balustrade for this floor
            if has_bal and fi > 0 and lod >= 1:
                mb.obox(F.p(-0.0, z0 - 0.16, 0), F.u * length, F.n * bal_depth, Z * 0.16, CONC, skip="f")
                if style == "solid":
                    mb.obox(F.p(0, z0, bal_depth - 0.12), F.u * length, F.n * 0.12, Z * 0.95, WALL)
                    mb.obox(F.p(0, z0 + 0.95, bal_depth - 0.16), F.u * length, F.n * 0.2, Z * 0.06, TRIM)
                else:
                    mb.obox(F.p(0, z0 + 1.0, bal_depth - 0.06), F.u * length, F.n * 0.05, Z * 0.05, DARK)
                    mb.obox(F.p(0, z0 + 0.12, bal_depth - 0.05), F.u * length, F.n * 0.03, Z * 0.03, DARK)
                    npst = int(length / 0.14) if lod >= 2 else int(length / 1.0)
                    for k in range(npst + 1):
                        x = length * k / npst
                        mb.obox(F.p(x - 0.008, z0 + 0.12, bal_depth - 0.045), F.u * 0.016, F.n * 0.016, Z * 0.88, DARK, skip="bt")
                for e in (0.0, length - 0.12):  # end walls
                    mb.obox(F.p(e, z0, 0), F.u * 0.12, F.n * bal_depth, Z * 0.95, WALL, skip="f")
        # balcony columns & roof overhang
        if has_bal and lod >= 1:
            ncol = max(2, round(length / (bw * 2)))
            for k in range(ncol + 1):
                x = min(length - 0.3, length * k / ncol)
                mb.obox(F.p(x, 0, bal_depth - 0.3), F.u * 0.3, F.n * 0.3, Z * top, TRIM)
            mb.obox(F.p(-0.1, top - 0.14, 0), F.u * (length + 0.2), F.n * (bal_depth + 0.25), Z * 0.14, CONC, skip="f")
    # roof slab, parapet
    mb.quad((-w / 2, -d / 2, top), (w / 2, -d / 2, top), (w / 2, d / 2, top), (-w / 2, d / 2, top), CONC)
    ph, pt = 0.55, 0.16
    if roof:
        for side, (F, length) in frames.items():
            mb.obox(F.p(0, top, -pt), F.u * length, F.n * pt, Z * ph, WALL)
            mb.obox(F.p(-0.03, top + ph, -pt - 0.03), F.u * (length + 0.06), F.n * (pt + 0.06), Z * 0.05, TRIM)
        # stair bulkhead
        bx, by = rnd.uniform(-w / 2 + 2.5, w / 2 - 2.5), rnd.uniform(-0.5, d / 2 - 2.2)
        mb.cbox((bx, by, top), (3.2, 3.0, 2.5), WALL)
        mb.cbox((bx, by, top + 2.5), (3.5, 3.3, 0.12), CONC)
        mb.cbox((bx - 0.6, by - 1.51, top), (0.9, 0.04, 2.0), DARK)
        nt = tanks if tanks is not None else rnd.randint(1, 3)
        for k in range(nt):
            if k == 0:
                water_tank(mb, (bx + rnd.uniform(-0.6, 0.6), by + rnd.uniform(-0.4, 0.4), top + 2.62), stand=0.0)
            else:
                water_tank(mb, (rnd.uniform(-w / 2 + 1.2, w / 2 - 1.2), rnd.uniform(-d / 2 + 1.2, d / 2 - 1.2), top),
                           r=rnd.choice([0.55, 0.62, 0.75]), stand=rnd.choice([0.5, 1.1, 1.6]))
        for k in range(rnd.randint(1, 4)):
            dish(mb, (rnd.uniform(-w / 2 + 0.6, w / 2 - 0.6), rnd.choice([-d / 2 + 0.5, d / 2 - 0.5]), top), r=rnd.uniform(0.35, 0.55), az=rnd.uniform(0, 6.28))
        if solar > 0:
            n_arr = max(1, int(w * d * solar / 40))
            for k in range(n_arr):
                cx = -w / 2 + 2.6 + (w - 5.2) * (k + 0.5) / n_arr
                cy = rnd.uniform(-d / 2 + 2.2, -0.5) if abs(cx - bx) > 3.5 else -d / 2 + 2.2
                if abs(cx - bx) < 2.0 and abs(cy - by) < 3.5:
                    continue
                solar_array(mb, (cx, cy, top), cols=rnd.choice([3, 4]), rows=2, rz=rnd.choice([0.0, 0.0, 0.08]))
    ms = building_mats(lit=lit)
    o = mb.obj(name, ms, collection=collection, loc=loc, rz=rz, color=color)
    for s in sign_objs:
        s.parent = o
    o["top"] = top
    return o


def far_block(name, w, d, h, color, loc, rz=0.0, collection=None, mat=None, roof_kit=True, seed=0):
    """Distant building: box + roof clutter, windows from the facade_far shader."""
    rnd = random.Random(seed)
    mb = MB()
    mb.box((-w / 2, -d / 2, 0), (w / 2, d / 2, h), 0, skip="b")
    if roof_kit:
        mb.box((-w / 2, -d / 2, h), (w / 2, d / 2, h + 0.5), 0, skip="bt")
        for k in range(rnd.randint(1, 3)):
            water_tank(mb, (rnd.uniform(-w / 2 + 1, w / 2 - 1), rnd.uniform(-d / 2 + 1, d / 2 - 1), h), stand=rnd.choice([0.4, 1.2]), m_tank=1, m_steel=1)
        if rnd.random() < 0.7:
            solar_array(mb, (rnd.uniform(-w / 4, w / 4), rnd.uniform(-d / 4, d / 4), h), cols=rnd.randint(3, 6), rows=2, m=2, m_steel=1)
    return mb.obj(name, [mat or facade_far(), mats.plain("tank_black", (0.012, 0.012, 0.014), 0.42), mats.solar_panel()],
                  collection=collection, loc=loc, rz=rz, color=color)


def skyline(collection, centre, radius_in, radius_out, n=60, arc=(0, 360), seed=1, h_range=(9, 28), towers=0.12,
            tower_h=(60, 140), lit=0.1):
    """Ring / arc of distant blocks around a point (background city)."""
    rnd = random.Random(seed)
    cx, cy = centre[0], centre[1]
    mat = facade_far(lit=lit)
    out = []
    for i in range(n):
        a = math.radians(rnd.uniform(*arc)); r = rnd.uniform(radius_in, radius_out)
        tower = rnd.random() < towers
        h = rnd.uniform(*tower_h) if tower else rnd.uniform(*h_range)
        w, d = (rnd.uniform(18, 30), rnd.uniform(18, 30)) if tower else (rnd.uniform(14, 34), rnd.uniform(10, 16))
        col = rnd.choice(PAINTS)
        if tower:
            col = rnd.choice([(0.45, 0.47, 0.5), (0.55, 0.52, 0.48), (0.3, 0.36, 0.4)])
        out.append(far_block(f"far{i}", w, d, h, col, (cx + math.cos(a) * r, cy + math.sin(a) * r, centre[2] if len(centre) > 2 else 0),
                             rnd.choice([0, math.pi / 2]) + rnd.uniform(-0.2, 0.2), collection, mat, seed=seed * 1000 + i))
    return out


# ----------------------------------------------------------------------------- signs
def sign_board(image_path, w, h, emit=0.0, name=None, frame=True, collection=None):
    """Sign plane in the local XY plane (normal +Z); rotate into place."""
    mb = MB()
    mb.quad((-w / 2, -h / 2, 0.03), (w / 2, -h / 2, 0.03), (w / 2, h / 2, 0.03), (-w / 2, h / 2, 0.03), 0)
    if frame:
        mb.box((-w / 2 - 0.03, -h / 2 - 0.03, -0.02), (w / 2 + 0.03, h / 2 + 0.03, 0.025), 1)
    nm = name or "sign_" + str(image_path).rsplit("/", 1)[-1].split(".")[0]
    return mb.obj(nm, [mats.sign(nm + ("_e" if emit else ""), image_path, emit=emit, flicker=True if emit else None),
                       mats.plain("sign_frame", (0.05, 0.05, 0.05), 0.5, 0.5)], collection=collection)


# ----------------------------------------------------------------------------- streets
def road(collection, x0, x1, y0, y1, z=0.0, name="road", puddles=0.25, key="asphalt", **kw):
    mb = MB()
    mb.quad((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))
    return mb.obj(name, [mats.ground(key, name + "_mat", puddles=puddles, **kw)], collection=collection)


def kerb(mb, p0, p1, h=0.22, wdt=0.3, m=0):
    """Kerb run between two points on the ground."""
    p0, p1 = Vector(p0), Vector(p1)
    u = p1 - p0; n = Vector((-u.y, u.x, 0)).normalized()
    mb.obox(p0 - n * wdt / 2, u, n * wdt, Z * h, m, skip="b")


def kerb_obj(collection, runs, name="kerbs", h=0.22, wdt=0.3):
    """Yellow/black painted kerbstones - each run is its own object so stripes follow it."""
    out = []
    for i, (p0, p1) in enumerate(runs):
        p0, p1 = Vector(p0), Vector(p1)
        L = (p1 - p0).length
        mb = MB()
        mb.obox((0, -wdt / 2, 0), (L, 0, 0), (0, wdt, 0), (0, 0, h), 0, skip="b")
        o = mb.obj(f"{name}{i}", [mats.striped("kerb_paint", (0.75, 0.55, 0.04), (0.03, 0.03, 0.03), 0.6, "X")], collection=collection, loc=p0,
                   rz=math.atan2(p1.y - p0.y, p1.x - p0.x))
        out.append(o)
    return out


def lane_marks(collection, pts, wdt=0.14, dash=3.0, gap=4.5, z=0.006, name="marks", color=(0.7, 0.68, 0.6)):
    mb = MB()
    for p0, p1 in pts:
        p0, p1 = Vector(p0), Vector(p1)
        u = (p1 - p0); L = u.length; u.normalize(); n = Vector((-u.y, u.x, 0))
        s = 0.0
        while s < L:
            e = min(L, s + (dash if gap > 0 else L))
            a, b = p0 + u * s, p0 + u * e
            mb.quad(a - n * wdt / 2 + Z * z, b - n * wdt / 2 + Z * z, b + n * wdt / 2 + Z * z, a + n * wdt / 2 + Z * z)
            s = e + gap if gap > 0 else L
    def make():
        t = mats.NT("road_paint")
        nz = t.noise(t.coords("world", 1.0), 7.0, 6.0, 0.7).outputs["Fac"]
        m = t.ramp(nz, [(0.38, (0, 0, 0)), (0.62, (1, 1, 1))])
        b = t.n("ShaderNodeBsdfPrincipled"); b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = 0.7
        tr = t.n("ShaderNodeBsdfTransparent")
        mx = t.n("ShaderNodeMixShader"); t.l(m, mx.inputs[0]); t.l(tr.outputs[0], mx.inputs[1]); t.l(b.outputs[0], mx.inputs[2])
        t.l(mx.outputs[0], t.out.inputs["Surface"])
        return t.mat
    return mb.obj(name, [mats._get(("roadpaint", color), make)], collection=collection)


def catenary(p0, p1, sag, n=14):
    p0, p1 = Vector(p0), Vector(p1)
    return [p0.lerp(p1, i / n) - Z * (sag * 4 * (i / n) * (1 - i / n)) for i in range(n + 1)]


def cables(collection, spans, name="cables", r=0.014, mat=None):
    """Overhead cables: spans = [(p0, p1, sag), ...]."""
    mb = MB()
    for p0, p1, sag in spans:
        mb.tube(catenary(p0, p1, sag), r, 0, 5)
    return mb.obj(name, [mat or mats.plain("cable", (0.012, 0.012, 0.012), 0.6)], smooth=True, collection=collection)


def utility_pole(collection, loc, h=9.0, rz=0.0, name="pole", arms=2, transformer=False):
    """Concrete utility pole with cross-arms and insulators; returns (object, [attach points world])."""
    mb = MB()
    mb.cyl((0, 0, 0), (0, 0, h), 0.17, 0.11, 0, 8)
    pts = []
    for k in range(arms):
        zz = h - 0.35 - k * 0.9
        mb.box((-1.1, -0.05, zz), (1.1, 0.05, zz + 0.09), 1)
        for x in (-1.0, -0.45, 0.45, 1.0):
            mb.cyl((x, 0, zz + 0.09), (x, 0, zz + 0.24), 0.035, 0.02, 2, 6)
            pts.append(Vector((x, 0, zz + 0.25)))
    if transformer:
        mb.box((-0.45, -0.75, h - 3.2), (0.45, -0.15, h - 2.1), 1)
        mb.cyl((0, -0.45, h - 2.1), (0, -0.45, h - 1.75), 0.06, 0.04, 2, 6)
        mb.box((-0.6, -0.8, h - 3.3), (0.6, 0.1, h - 3.2), 1)
    mb.cyl((0.12, 0.12, 2.5), (0.5, 0.5, h - 1.2), 0.012, 0.012, 1, 4)   # stay / service wire
    o = mb.obj(name, [mats.pbr("concrete", "pole_conc", scale=0.6, dirt=0.4, val=0.75),
                      mats.pbr("rust", "pole_steel", scale=1.2, tint=(0.5, 0.45, 0.42)),
                      mats.plain("insulator", (0.45, 0.2, 0.12), 0.3)], collection=collection, loc=loc, rz=rz)
    R = Matrix.Rotation(rz, 3, "Z")
    return o, [Vector(loc) + R @ p for p in pts]


def umbrella(collection, loc, colors, r=1.55, h=2.35, tilt=(0.0, 0.0), panels=8, name="umbrella", rz=0.0):
    """Market umbrella: alternating coloured panels, valance, ribs and pole. The canopy is a
    separate object so it can sway."""
    mbp = MB()
    mbp.cyl((0, 0, 0), (0, 0, h + 0.12), 0.022, 0.022, 0, 8)
    mbp.cyl((0, 0, 0), (0, 0, 0.12), 0.2, 0.17, 1, 10)
    pole = mbp.obj(name + "_pole", [mats.plain("umb_pole", (0.5, 0.5, 0.5), 0.35, 0.9), mats.pbr("concrete", "umb_base", scale=1.0)],
                   collection=collection, loc=loc, rz=rz)
    mb = MB()
    drop = r * 0.36
    apex = Vector((0, 0, 0.0))
    rim = [Vector((math.cos(2 * math.pi * i / panels) * r, math.sin(2 * math.pi * i / panels) * r, -drop)) for i in range(panels)]
    for i in range(panels):
        a, b = rim[i], rim[(i + 1) % panels]
        m = i % len(colors)
        # panel in 3 bands for a slightly domed profile
        prev_a, prev_b = apex, apex
        for k in (1, 2, 3):
            t = k / 3
            bulge = 0.06 * r * math.sin(math.pi * t)
            pa = apex.lerp(a, t) + Z * bulge; pb = apex.lerp(b, t) + Z * bulge
            mid_sag = Z * (-0.03 * r * t)
            if k == 1:
                mb.tri(apex, pa, pb, m)
            else:
                mb.quad(prev_a, pa, pb, prev_b, m)
            prev_a, prev_b = pa, pb
        # valance
        mb.quad(a, b, b - Z * 0.16, a - Z * 0.16, (i + 1) % len(colors))
        mb.tube([apex - Z * 0.02, a - Z * 0.01], 0.006, len(colors), 4)
    cms = [mats.cloth(f"umb_cloth_{i}_{'_'.join(f'{c:.2f}' for c in col)}", col, translucency=0.35, rough=0.7) for i, col in enumerate(colors)]
    can = mb.obj(name + "_canopy", cms + [mats.plain("umb_rib", (0.6, 0.6, 0.6), 0.4, 0.8)], collection=collection)
    can.parent = pole
    can.location = (0, 0, h)
    can.rotation_euler = (tilt[0], tilt[1], 0)
    can["sway"] = [0.012, 0.012, 0.0, 0.55, random.random() * 6.28]
    can["rot0"] = list(can.rotation_euler)
    return pole, can


def kiosk(collection, loc, rz=0.0, color=(0.55, 0.035, 0.03), w=2.6, d=2.0, h=2.45, name="kiosk", sign=None, sign_side=None,
          open_front=True, awning=True, shelf_items=True):
    """Roadside container kiosk: painted sheet-metal box on blocks, service hatch, awning,
    corrugated roof, signboard. Front faces local -Y."""
    mb = MB()
    P, DK, CORRM, WOOD, CONCM, TRIMM = range(6)
    t = 0.05
    base = 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cbox((sx * (w / 2 - 0.25), sy * (d / 2 - 0.25), 0), (0.4, 0.25, base), CONCM)
    z0, z1 = base, base + h
    mb.box((-w / 2, -d / 2, z0), (w / 2, d / 2, z0 + 0.06), P)                 # floor
    mb.box((-w / 2, d / 2 - t, z0), (w / 2, d / 2, z1), P)                      # back
    mb.box((-w / 2, -d / 2, z0), (-w / 2 + t, d / 2, z1), P)                    # left
    mb.box((w / 2 - t, -d / 2, z0), (w / 2, d / 2, z1), P)                      # right
    hz0, hz1 = z0 + 0.95, z0 + 2.05
    if open_front:
        mb.box((-w / 2, -d / 2, z0), (w / 2, -d / 2 + t, hz0), P)              # counter wall
        mb.box((-w / 2, -d / 2, hz1), (w / 2, -d / 2 + t, z1), P)              # header
        mb.box((-w / 2, -d / 2, hz0), (-w / 2 + 0.18, -d / 2 + t, hz1), P)
        mb.box((w / 2 - 0.18, -d / 2, hz0), (w / 2, -d / 2 + t, hz1), P)
        mb.box((-w / 2 - 0.02, -d / 2 - 0.28, hz0 - 0.04), (w / 2 + 0.02, -d / 2 + 0.25, hz0), WOOD)   # counter top
        mb.box((-w / 2 + t, -d / 2 + t, z0 + 0.06), (w / 2 - t, d / 2 - t, z0 + 0.07), DK)
        for zz in (z0 + 1.25, z0 + 1.65, z0 + 2.0):                                                     # back shelves
            mb.box((-w / 2 + t, d / 2 - t - 0.3, zz), (w / 2 - t, d / 2 - t, zz + 0.025), WOOD)
    else:
        mb.box((-w / 2, -d / 2, z0), (w / 2, -d / 2 + t, z1), P)
    # pressed ribs on the walls
    for k in range(int(w / 0.3)):
        x = -w / 2 + 0.15 + k * 0.3
        mb.box((x - 0.02, d / 2, z0 + 0.1), (x + 0.02, d / 2 + 0.015, z1 - 0.1), P)
        if not open_front or True:
            mb.box((x - 0.02, -d / 2 - 0.012, z0 + 0.08), (x + 0.02, -d / 2, hz0 - 0.06), P)
    for k in range(int(d / 0.3)):
        y = -d / 2 + 0.15 + k * 0.3
        for sx in (-1, 1):
            mb.box((sx * w / 2 - (0.015 if sx < 0 else 0), y - 0.02, z0 + 0.1), (sx * w / 2 + (0.015 if sx > 0 else 0), y + 0.02, z1 - 0.1), P)
    # roof: corrugated, slight fall to the back, overhang
    mb.quad((-w / 2 - 0.2, -d / 2 - 0.35, z1 + 0.16), (w / 2 + 0.2, -d / 2 - 0.35, z1 + 0.16), (w / 2 + 0.2, d / 2 + 0.2, z1 + 0.04), (-w / 2 - 0.2, d / 2 + 0.2, z1 + 0.04), CORRM,
            ((0, 0), (w, 0), (w, d), (0, d)))
    mb.quad((-w / 2 - 0.2, d / 2 + 0.2, z1 + 0.03), (w / 2 + 0.2, d / 2 + 0.2, z1 + 0.03), (w / 2 + 0.2, -d / 2 - 0.35, z1 + 0.15), (-w / 2 - 0.2, -d / 2 - 0.35, z1 + 0.15), CORRM)
    if awning:
        mb.quad((-w / 2, -d / 2 - 1.15, hz1 + 0.02), (w / 2, -d / 2 - 1.15, hz1 + 0.02), (w / 2, -d / 2, z1 - 0.05), (-w / 2, -d / 2, z1 - 0.05), P)
        mb.quad((-w / 2, -d / 2, z1 - 0.06), (w / 2, -d / 2, z1 - 0.06), (w / 2, -d / 2 - 1.15, hz1 + 0.01), (-w / 2, -d / 2 - 1.15, hz1 + 0.01), P)
        for sx in (-1, 1):
            mb.cyl((sx * (w / 2 - 0.05), -d / 2 - 1.1, hz1 + 0.02), (sx * (w / 2 - 0.05), -d / 2, hz0 + 0.2), 0.012, 0.012, DK, 5)
    msl = [mats.car_paint(f"kiosk_paint_{color[0]:.2f}_{color[1]:.2f}", color, rough=0.45, wear=0.7, dust=0.9),
           mats.plain("kiosk_dark", (0.02, 0.02, 0.022), 0.7),
           mats.pbr("corrugated", "kiosk_roof", scale=0.7, tint=(0.8, 0.7, 0.6), dirt=0.5, dirt_color=(0.25, 0.1, 0.04)),
           mats.pbr("wood", "kiosk_wood", scale=0.8, tint=(0.75, 0.6, 0.45)),
           mats.pbr("concrete", "kiosk_block", scale=0.8, val=0.8),
           mats.plain("kiosk_trim", (0.8, 0.75, 0.6), 0.6)]
    o = mb.obj(name, msl, collection=collection, loc=loc, rz=rz)
    if sign:
        so = sign_board(sign, w + 0.2, 0.55, emit=0.0, collection=collection)
        so.parent = o
        so.location = (0, -d / 2 - 0.37, z1 + 0.45)
        so.rotation_euler = (math.radians(84), 0, 0)
    return o


def stall_table(collection, loc, rz=0.0, w=2.0, d=0.9, h=0.78, name="stall", cloth_color=None):
    """Rough timber market table; returns (object, top z)."""
    mb = MB()
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cbox((sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), 0), (0.06, 0.06, h - 0.03), 0)
    n = 6
    for k in range(n):
        y0 = -d / 2 + d * k / n
        mb.box((-w / 2, y0 + 0.004, h - 0.03), (w / 2, y0 + d / n - 0.004, h), 0)
    mb.box((-w / 2 + 0.05, -d / 2 + 0.03, h - 0.12), (w / 2 - 0.05, -d / 2 + 0.05, h - 0.03), 0)
    mb.box((-w / 2 + 0.05, d / 2 - 0.05, h - 0.12), (w / 2 - 0.05, d / 2 - 0.03, h - 0.03), 0)
    ms = [mats.pbr("wood", "stall_wood", scale=0.9, tint=(0.7, 0.6, 0.5), dirt=0.4)]
    if cloth_color:
        mb.box((-w / 2 - 0.03, -d / 2 - 0.03, h), (w / 2 + 0.03, d / 2 + 0.03, h + 0.006), 1)
        mb.quad((-w / 2 - 0.03, -d / 2 - 0.03, h + 0.003), (w / 2 + 0.03, -d / 2 - 0.03, h + 0.003), (w / 2 + 0.03, -d / 2 - 0.035, h - 0.3), (-w / 2 - 0.03, -d / 2 - 0.035, h - 0.3), 1)
        ms.append(mats.cloth(f"stall_cloth_{cloth_color[0]:.2f}{cloth_color[1]:.2f}", cloth_color, (0.9, 0.8, 0.5), "ankara", 6.0))
    return mb.obj(name, ms, collection=collection, loc=loc, rz=rz), h + (0.006 if cloth_color else 0)


def fence_run(collection, p0, p1, name="fence"):
    """Chain-link fence run from the Poly Haven modular kit (posts + double panels)."""
    p0, p1 = Vector(p0), Vector(p1)
    u = p1 - p0; L = u.length; rz = math.atan2(u.y, u.x); u.normalize()
    panel = core.asset("modular-chainlink-fence", "fence_double")[0]
    post = [o for o in core.asset("modular-chainlink-fence") if o.name.endswith("modular_chainlink_fence_post")][0]
    pw = panel.dimensions.x
    n = max(1, round(L / (pw + 0.06)))
    step = L / n
    out = []
    for i in range(n):
        out.append(core.inst(panel, p0 + u * (step * (i + 0.5)), (0, 0, rz), (step / pw * 0.97, 1, 1), collection))
    for i in range(n + 1):
        out.append(core.inst(post, p0 + u * (step * i), (0, 0, rz), 1.0, collection))
    return out
