"""Lagos 2090 - procedural tropical vegetation (coconut palms, hanging vines, ivy,
bougainvillea), scatter helpers and the wind animation shared by all shots.

No pine / fir. Broadleaf trees come from the Poly Haven scans in the asset library.
"""
import bpy, math, random
from mathutils import Vector, Matrix, Euler
from . import core, mats
from .build import MB, Z

_frond_cache = {}


# ----------------------------------------------------------------------------- wind
def sway(o, ax=0.02, ay=0.02, az=0.0, freq=0.4, phase=None):
    o["sway"] = [ax, ay, az, freq, random.random() * 6.28 if phase is None else phase]
    o["rot0"] = list(o.rotation_euler)
    return o


_sway_objs = None


def animate_sway(sc, f, gust=1.0):
    """Apply wind sway to every object tagged with sway()."""
    global _sway_objs
    try:
        if _sway_objs is not None:
            _sway_objs[0][0].name
    except (ReferenceError, IndexError):
        _sway_objs = None
    if _sway_objs is None:
        _sway_objs = [(o, list(o["sway"]), list(o["rot0"])) for o in sc.objects if "sway" in o.keys()]
    t = f / 24.0
    g = gust * (0.75 + 0.25 * math.sin(t * 0.9))            # slow gust envelope
    for o, s, r0 in _sway_objs:
        ax, ay, az, fr, ph = s
        w = 2 * math.pi * fr * t
        a = math.sin(w + ph) * 0.7 + math.sin(w * 2.3 + ph * 1.7) * 0.3
        b = math.sin(w * 0.8 + ph * 2.1) * 0.7 + math.sin(w * 1.9 + ph) * 0.3
        o.rotation_euler = (r0[0] + ax * a * g, r0[1] + ay * b * g, r0[2] + az * a * g)


# ----------------------------------------------------------------------------- palms
def _frond_mesh(length, droop, seed):
    key = (round(length, 1), round(droop, 2), seed)
    if key in _frond_cache:
        try:
            _frond_cache[key].name
            return _frond_cache[key]
        except ReferenceError:
            pass
    rnd = random.Random(seed)
    mb = MB()
    n = 54
    pts, tans, ups = [], [], []
    p = Vector((0, 0, 0)); th = 0.0
    for i in range(n + 1):
        s = i / n
        th = -droop * (s ** 1.5) * 1.5
        t = Vector((math.cos(th), 0, math.sin(th)))
        pts.append(p.copy()); tans.append(t); ups.append(Vector((-math.sin(th), 0, math.cos(th))))
        p = p + t * (length / n)
    mb.tube(pts, lambda s: 0.034 * (1 - s) ** 0.8 + 0.004, 1, 5)
    lmax = length * 0.21
    for i in range(6, n + 1):
        s = i / n
        ll = lmax * (math.sin(math.pi * min(1.0, (s * 1.02) ** 0.62)) ** 0.55 + 0.08) * rnd.uniform(0.9, 1.08)
        fwd = math.radians(22 + 38 * s)
        hang = 0.35 + 0.55 * s + rnd.uniform(-0.1, 0.1)
        for side in (-1, 1):
            d = (Vector((0, side, 0)) * math.cos(fwd) + tans[i] * math.sin(fwd))
            d = (d * math.cos(hang) - ups[i] * math.sin(hang)).normalized()
            wv = tans[i] * (0.026 + 0.012 * math.sin(math.pi * s))
            p0 = pts[i] + Vector((0, side * 0.012, 0))
            g = Vector((0, 0, -1))
            p1 = p0 + d * ll * 0.4
            d2 = (d + g * 0.22).normalized(); p2 = p1 + d2 * ll * 0.35
            d3 = (d2 + g * 0.35).normalized(); p3 = p2 + d3 * ll * 0.25
            if side > 0:
                mb.quad(p0 - wv, p0 + wv, p1 + wv * 0.95, p1 - wv * 0.95, 0)
                mb.quad(p1 - wv * 0.95, p1 + wv * 0.95, p2 + wv * 0.6, p2 - wv * 0.6, 0)
                mb.tri(p2 - wv * 0.6, p2 + wv * 0.6, p3, 0)
            else:
                mb.quad(p0 + wv, p0 - wv, p1 - wv * 0.95, p1 + wv * 0.95, 0)
                mb.quad(p1 + wv * 0.95, p1 - wv * 0.95, p2 - wv * 0.6, p2 + wv * 0.6, 0)
                mb.tri(p2 + wv * 0.6, p2 - wv * 0.6, p3, 0)
    me = bpy.data.meshes.new(f"frond_{key[0]}_{key[1]}_{seed}")
    me.from_pydata(mb.v, [], mb.f)
    me.materials.append(mats.leaf("palm_leaf", (0.055, 0.16, 0.02), (0.17, 0.26, 0.035), rough=0.38, translucency=0.5))
    me.materials.append(mats.plain("palm_rachis", (0.28, 0.3, 0.08), 0.5))
    me.polygons.foreach_set("material_index", mb.mi)
    me.update()
    _frond_cache[key] = me
    return me


def _trunk_mat():
    def make():
        t = mats.NT("palm_trunk")
        vec = t.coords("object", (1, 1, 1))
        w = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
        t.val(w, Scale=5.5, Distortion=1.4, Detail=2.0, Detail_Scale=2.0)
        t.l(vec, w.inputs["Vector"])
        n = t.noise(vec, 9.0, 6.0, 0.7).outputs["Fac"]
        col = t.mix(w.outputs["Fac"], (0.16, 0.13, 0.1), (0.36, 0.31, 0.25))
        col = t.mix(t.math("MULTIPLY", n, 0.5), col, (0.1, 0.09, 0.07))
        h = t.math("ADD", t.math("MULTIPLY", w.outputs["Fac"], 0.7), t.math("MULTIPLY", n, 0.3))
        t.bsdf(Base_Color=col, Roughness=0.9, Normal=t.bump(h, 0.9, 0.03))
        return t.mat
    return mats._get(("palmtrunk",), make)


def palm(collection, loc, height=9.0, lean=(1.2, 0.4), seed=0, fronds=22, frond_len=4.3, wind=1.0, name="palm", coconuts=True):
    """Coconut palm. Returns the trunk object (fronds are children)."""
    rnd = random.Random(seed)
    mb = MB()
    n = 22
    pts = []
    for i in range(n + 1):
        s = i / n
        pts.append(Vector((lean[0] * s * s, lean[1] * s * s, height * s)))
    mb.tube(pts, lambda s: 0.14 + 0.12 * math.exp(-s * 14) + 0.05 * (1 - s), 0, 10)
    top = pts[-1]
    # crown shaft + coconuts
    mb.cyl(top - Z * 0.5, top + Z * 0.25, 0.2, 0.09, 0, 10)
    trunk = mb.obj(name, [_trunk_mat()], smooth=True, collection=collection, loc=loc)
    if coconuts:
        cm = MB()
        for k in range(rnd.randint(4, 9)):
            a = rnd.uniform(0, 6.28); c = top + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, -0.35 - rnd.uniform(0, 0.25)))
            _sphere(cm, c, rnd.uniform(0.10, 0.14), 0)
        co = cm.obj(name + "_nuts", [mats.plain("coconut", (0.2, 0.26, 0.06), 0.45)], smooth=True, collection=collection)
        co.parent = trunk
    for i in range(fronds):
        s = i / max(1, fronds - 1)
        elev = math.radians(78 - 118 * (s ** 0.85)) + rnd.uniform(-0.08, 0.08)
        yaw = i * 2.39996 + rnd.uniform(-0.2, 0.2)
        droop = 0.32 + 0.5 * s + rnd.uniform(-0.05, 0.08)
        me = _frond_mesh(frond_len * rnd.choice([0.85, 0.95, 1.0, 1.1]), round(droop * 5) / 5, rnd.randrange(3))
        o = bpy.data.objects.new(name + "_frond", me)
        core.link(o, collection)
        o.parent = trunk
        o.location = top + Vector((math.cos(yaw) * 0.08, math.sin(yaw) * 0.08, 0.05))
        o.rotation_euler = (rnd.uniform(-0.25, 0.25), -elev, yaw)
        amp = (0.03 + 0.05 * s) * wind
        sway(o, amp * 1.4, amp, amp * 0.5, rnd.uniform(0.28, 0.42))
    return trunk


def _sphere(mb, c, r, m, seg=10, rings=6):
    c = Vector(c)
    P = [[c + Vector((math.cos(2 * math.pi * j / seg) * math.sin(math.pi * i / rings) * r,
                      math.sin(2 * math.pi * j / seg) * math.sin(math.pi * i / rings) * r,
                      math.cos(math.pi * i / rings) * r)) for j in range(seg)] for i in range(rings + 1)]
    for i in range(rings):
        for j in range(seg):
            k = (j + 1) % seg
            mb.quad(P[i + 1][j], P[i + 1][k], P[i][k], P[i][j], m)


# ----------------------------------------------------------------------------- leaves
def _leaf(mb, p, d, n, size, m=0, fold=0.25, wide=0.62):
    """Ovate leaf: base p, pointing along d, face normal n."""
    d = d.normalized(); s = d.cross(n)
    if s.length < 1e-4:
        s = d.orthogonal()
    s.normalize(); n2 = s.cross(d)
    mid = p + d * size * 0.45 - n2 * size * fold * 0.3
    tip = p + d * size
    a = p + d * size * 0.38 + s * size * wide * 0.5 + n2 * size * fold * 0.25
    b = p + d * size * 0.38 - s * size * wide * 0.5 + n2 * size * fold * 0.25
    mb.quad(p, a, tip, mid, m)
    mb.quad(p, mid, tip, b, m)


def vine_mats(flower=None):
    ms = [mats.leaf("vine_leaf", (0.035, 0.14, 0.02), (0.12, 0.24, 0.03), rough=0.32, translucency=0.4),
          mats.plain("vine_stem", (0.1, 0.09, 0.04), 0.7)]
    if flower:
        ms.append(mats.leaf("vine_flower_%.2f_%.2f" % (flower[0], flower[1]), flower, tuple(min(1, c * 1.5) for c in flower), rough=0.6, translucency=0.6, vary=0.5))
    return ms


def vine_curtain(collection, p0, p1, n=60, length=(1.5, 4.0), seed=0, cluster=4, leaf=0.11, density=34, out=(0, -1, 0),
                 name="vine", flower=None, spread=0.25, wind=1.0):
    """Hanging vine strands along the edge p0->p1. Strands are grouped in clusters; each
    cluster is one pendulum object."""
    rnd = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1); outv = Vector(out).normalized()
    objs = []
    ncl = max(1, n // cluster)
    for ci in range(ncl):
        tc = (ci + rnd.random()) / ncl
        anchor = p0.lerp(p1, tc)
        mb = MB()
        maxlen = 0
        for k in range(cluster):
            L = rnd.uniform(*length) * (0.6 + 0.8 * rnd.random() ** 2)
            maxlen = max(maxlen, L)
            off = (p1 - p0).normalized() * rnd.uniform(-1, 1) * (p1 - p0).length / ncl * 0.6 + outv * rnd.uniform(0, spread)
            pts = [off.copy()]
            q = off.copy(); dv = Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), -1))
            steps = max(3, int(L / 0.18))
            for s in range(steps):
                dv = (dv + Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), -0.25))).normalized()
                q = q + dv * (L / steps); pts.append(q.copy())
            mb.tube(pts, 0.006, 1, 4)
            nl = int(L * density)
            for j in range(nl):
                u = rnd.random() ** 0.8 * (len(pts) - 1)
                i0 = int(u); pp = pts[i0].lerp(pts[min(i0 + 1, len(pts) - 1)], u - i0)
                az = rnd.uniform(0, 6.28)
                nrm = Vector((math.cos(az), math.sin(az), rnd.uniform(-0.2, 0.5))).normalized()
                dd = Vector((math.cos(az + 1.57) * 0.5, math.sin(az + 1.57) * 0.5, -1 + rnd.uniform(-0.3, 0.5)))
                side = Vector((math.cos(az), math.sin(az), 0)) * rnd.uniform(0.0, 0.07)
                isf = flower is not None and rnd.random() < 0.12
                _leaf(mb, pp + side, dd, nrm, (leaf * rnd.uniform(0.6, 1.25)) * (0.55 if isf else 1.0), 2 if isf else 0)
        o = mb.obj(f"{name}{ci}", vine_mats(flower), collection=collection, loc=anchor)
        a = 0.022 * wind / max(1.0, maxlen * 0.5)
        sway(o, a * 1.0, a * 1.0, 0.0, rnd.uniform(0.22, 0.34))
        objs.append(o)
    return objs


def ivy_patch(collection, origin, u, v, nrm, w, h, density=180, seed=0, leaf=0.1, name="ivy", flower=None, edge_fade=0.3, hang=True):
    """Leaves carpeting a rectangle (origin + u*[0,w] + v*[0,h]) with outward normal nrm."""
    rnd = random.Random(seed)
    o0, u, v, nrm = Vector(origin), Vector(u).normalized(), Vector(v).normalized(), Vector(nrm).normalized()
    mb = MB()
    nl = int(w * h * density)
    for i in range(nl):
        a, b = rnd.random(), rnd.random()
        if edge_fade > 0:
            e = min(a, 1 - a, b, 1 - b) / edge_fade
            if rnd.random() > min(1.0, e + 0.35):
                continue
        p = o0 + u * (a * w) + v * (b * h) + nrm * rnd.uniform(0.01, 0.09)
        nn = (nrm + Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(-0.2, 0.6)))).normalized()
        dd = (Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), -1.0 if hang else rnd.uniform(-1, 1)))).normalized()
        dd = (dd - nn * dd.dot(nn))
        if dd.length < 1e-3:
            continue
        isf = flower is not None and rnd.random() < 0.1
        _leaf(mb, p, dd, nn, leaf * rnd.uniform(0.6, 1.3) * (0.55 if isf else 1.0), 2 if isf else 0)
    return mb.obj(name, vine_mats(flower), collection=collection)


def bougainvillea(collection, loc, size=2.2, seed=0, color=(0.75, 0.03, 0.32), canes=22, name="bougainvillea", wind=1.0, lean=(0, 0)):
    """Arching bougainvillea: green leaves with dense paper-thin bracts on the outer canes."""
    rnd = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    root.location = loc
    core.link(root, collection)
    ms = vine_mats(color)
    for ci in range(canes):
        mb = MB()
        az = rnd.uniform(0, 6.28)
        reach = size * rnd.uniform(0.55, 1.1); h = size * rnd.uniform(0.6, 1.15)
        dirv = Vector((math.cos(az), math.sin(az), 0)) + Vector((lean[0], lean[1], 0))
        pts = []
        steps = 14
        for s in range(steps + 1):
            t = s / steps
            x = reach * t
            zz = h * (1.7 * t - 1.25 * t * t) + rnd.uniform(-0.02, 0.02)   # rises then droops
            pts.append(dirv * x + Z * zz + Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0)))
        mb.tube(pts, lambda s: 0.014 * (1 - s) + 0.003, 1, 4)
        for j in range(int(170 * size / 2.2)):
            t = rnd.random() ** 0.6
            u = t * steps; i0 = min(steps - 1, int(u)); pp = pts[i0].lerp(pts[i0 + 1], u - i0)
            pp = pp + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * (0.05 + 0.16 * t)
            nn = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 1))).normalized()
            dd = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.7, 0.5)))
            isf = rnd.random() < (0.15 + 0.75 * t)
            _leaf(mb, pp, dd, nn, rnd.uniform(0.035, 0.06) if isf else rnd.uniform(0.05, 0.085), 2 if isf else 0, wide=0.8 if isf else 0.6)
        o = mb.obj(f"{name}_cane{ci}", ms, collection=collection)
        o.parent = root
        a = 0.02 * wind
        sway(o, a, a, a * 0.5, rnd.uniform(0.3, 0.5))
    return root


def banana_plant(collection, loc, height=3.0, seed=0, name="banana", wind=1.0):
    """Banana / plantain: pseudo-stem with big torn paddle leaves (common in Lagos compounds)."""
    rnd = random.Random(seed)
    mb = MB()
    mb.tube([Vector((0, 0, 0)), Vector((0.03, 0.02, height * 0.5)), Vector((0.05, 0.0, height * 0.72))], lambda s: 0.13 - 0.06 * s, 1, 8)
    stem = mb.obj(name, [mats.leaf("banana_leaf", (0.07, 0.2, 0.025), (0.2, 0.32, 0.05), rough=0.3, translucency=0.5),
                         mats.plain("banana_stem", (0.2, 0.26, 0.08), 0.5)], smooth=True, collection=collection, loc=loc)
    for i in range(rnd.randint(6, 9)):
        lb = MB()
        L = height * rnd.uniform(0.55, 0.8); wdt = L * 0.22
        n = 12
        droop = rnd.uniform(0.5, 1.3)
        p = Vector((0, 0, 0)); th = math.radians(rnd.uniform(35, 70))
        mids = []
        for k in range(n + 1):
            s = k / n
            mids.append(p.copy())
            a = th - droop * s * 1.6
            p = p + Vector((math.cos(a), 0, math.sin(a))) * (L / n)
        for k in range(n):
            s0, s1 = k / n, (k + 1) / n
            w0 = wdt * math.sin(math.pi * min(1, s0 * 0.9 + 0.1)) ** 0.6; w1 = wdt * math.sin(math.pi * min(1, s1 * 0.9 + 0.1)) ** 0.6
            if k < 2:
                w0 *= 0.15 if k == 0 else 0.6; w1 *= 0.6 if k == 0 else 1.0
            for side in (-1, 1):
                if rnd.random() < 0.12:
                    continue                                    # wind-torn gap
                e0 = mids[k] + Vector((0, side * w0, -w0 * 0.25)); e1 = mids[k + 1] + Vector((0, side * w1, -w1 * 0.25))
                if side > 0:
                    lb.quad(mids[k], e0, e1, mids[k + 1], 0)
                else:
                    lb.quad(mids[k], mids[k + 1], e1, e0, 0)
        lb.tube(mids, lambda s: 0.022 * (1 - s) + 0.004, 1, 4)
        o = lb.obj(name + "_leaf", stem.data.materials[:], collection=collection)
        o.parent = stem
        o.location = (0.04, 0, height * 0.68)
        o.rotation_euler = (rnd.uniform(-0.2, 0.2), 0, i * 2.4 + rnd.uniform(-0.3, 0.3))
        sway(o, 0.05 * wind, 0.035 * wind, 0.02 * wind, rnd.uniform(0.3, 0.45))
    return stem


# ----------------------------------------------------------------------------- scatter
def scatter(collection, asset_name, n, region, scale=(0.8, 1.3), seed=0, pieces=None, wind=0.0, z=0.0, tilt=0.08, avoid=None):
    """Instance pieces of a library asset at random spots. region = (x0, x1, y0, y1) or a
    callable rnd -> (x, y)."""
    rnd = random.Random(seed)
    tmpl = core.asset(asset_name)
    if pieces:
        tmpl = [t for t in tmpl if any(p in t.name for p in pieces)]
    out = []
    for i in range(n):
        if callable(region):
            x, y = region(rnd)
        else:
            x, y = rnd.uniform(region[0], region[1]), rnd.uniform(region[2], region[3])
        if avoid and avoid(x, y):
            continue
        zz = z(x, y) if callable(z) else z
        t = rnd.choice(tmpl)
        o = core.inst(t, (x, y, zz), (rnd.uniform(-tilt, tilt), rnd.uniform(-tilt, tilt), rnd.uniform(0, 6.28)), rnd.uniform(*scale), collection)
        if wind > 0:
            sway(o, wind, wind, 0.0, rnd.uniform(0.35, 0.6))
        out.append(o)
    return out


def gn_scatter(surface, templates, density=40.0, scale=(0.7, 1.3), seed=0, wind=0.12, wind_freq=0.5, wind_scale=0.35,
               name="scatter", collection=None, align_tilt=0.15, density_attr=None):
    """Geometry-nodes scatter with a travelling wind wave (for lawns / ground cover).
    templates: list of template objects; they are gathered into a hidden collection."""
    src = bpy.data.collections.new(name + "_src")
    for t in templates:
        o = bpy.data.objects.new(t.name + "_src", t.data)
        src.objects.link(o)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes.new, ng.links.new
    gi, go = N("NodeGroupInput"), N("NodeGroupOutput")
    dist = N("GeometryNodeDistributePointsOnFaces")
    dist.distribute_method = "RANDOM"
    dist.inputs["Density"].default_value = density
    dist.inputs["Seed"].default_value = seed
    L(gi.outputs[0], dist.inputs["Mesh"])
    if density_attr:
        na = N("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"; na.inputs["Name"].default_value = density_attr
        mul = N("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = density
        L(na.outputs["Attribute"], mul.inputs[0]); L(mul.outputs[0], dist.inputs["Density"])
    ci = N("GeometryNodeCollectionInfo")
    ci.inputs["Collection"].default_value = src
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = N("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    L(dist.outputs["Points"], iop.inputs["Points"]); L(ci.outputs[0], iop.inputs["Instance"])
    ridx = N("FunctionNodeRandomValue"); ridx.data_type = "INT"
    ridx.inputs["Min"].default_value = 0; ridx.inputs["Max"].default_value = max(0, len(templates) - 1)
    ridx.inputs["Seed"].default_value = seed + 1
    L(ridx.outputs["Value"], iop.inputs["Instance Index"])
    rs = N("FunctionNodeRandomValue"); rs.data_type = "FLOAT"
    rs.inputs["Min"].default_value = scale[0]; rs.inputs["Max"].default_value = scale[1]; rs.inputs["Seed"].default_value = seed + 2
    cs = N("ShaderNodeCombineXYZ")
    for i in range(3):
        L(rs.outputs["Value"], cs.inputs[i])
    L(cs.outputs[0], iop.inputs["Scale"])
    # rotation: random yaw + wind tilt wave  sin(k.x - w t + noise)
    ryaw = N("FunctionNodeRandomValue"); ryaw.data_type = "FLOAT"
    ryaw.inputs["Min"].default_value = 0.0; ryaw.inputs["Max"].default_value = 6.283; ryaw.inputs["Seed"].default_value = seed + 3
    rt = N("FunctionNodeRandomValue"); rt.data_type = "FLOAT_VECTOR"
    rt.inputs["Min"].default_value = (-align_tilt, -align_tilt, 0); rt.inputs["Max"].default_value = (align_tilt, align_tilt, 0)
    rt.inputs["Seed"].default_value = seed + 4
    pos = N("GeometryNodeInputPosition"); sp = N("ShaderNodeSeparateXYZ"); L(pos.outputs[0], sp.inputs[0])
    tm = N("GeometryNodeInputSceneTime")
    ph = N("ShaderNodeMath"); ph.operation = "MULTIPLY_ADD"
    L(sp.outputs["X"], ph.inputs[0]); ph.inputs[1].default_value = wind_scale
    ph2 = N("ShaderNodeMath"); ph2.operation = "MULTIPLY_ADD"; L(sp.outputs["Y"], ph2.inputs[0]); ph2.inputs[1].default_value = wind_scale * 0.6
    L(ph2.outputs[0], ph.inputs[2])
    tmul = N("ShaderNodeMath"); tmul.operation = "MULTIPLY"; L(tm.outputs["Seconds"], tmul.inputs[0]); tmul.inputs[1].default_value = -6.283 * wind_freq
    L(tmul.outputs[0], ph2.inputs[2])
    nz = N("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; L(pos.outputs[0], nz.inputs["Vector"])
    nadd = N("ShaderNodeMath"); nadd.operation = "MULTIPLY_ADD"; L(nz.outputs[0], nadd.inputs[0]); nadd.inputs[1].default_value = 6.0
    L(ph.outputs[0], nadd.inputs[2])
    sn = N("ShaderNodeMath"); sn.operation = "SINE"; L(nadd.outputs[0], sn.inputs[0])
    amp = N("ShaderNodeMath"); amp.operation = "MULTIPLY_ADD"; L(sn.outputs[0], amp.inputs[0]); amp.inputs[1].default_value = wind
    amp.inputs[2].default_value = wind * 0.6
    cw = N("ShaderNodeCombineXYZ"); L(amp.outputs[0], cw.inputs[0])
    amp2 = N("ShaderNodeMath"); amp2.operation = "MULTIPLY"; L(sn.outputs[0], amp2.inputs[0]); amp2.inputs[1].default_value = wind * 0.4
    L(amp2.outputs[0], cw.inputs[1])
    add = N("ShaderNodeVectorMath"); add.operation = "ADD"; L(cw.outputs[0], add.inputs[0]); L(rt.outputs["Value"], add.inputs[1])
    L(add.outputs[0], iop.inputs["Rotation"])
    # yaw first (instance local), then wind tilt in world: rotate instances about Z locally
    rot = N("GeometryNodeRotateInstances")
    cy = N("ShaderNodeCombineXYZ"); L(ryaw.outputs["Value"], cy.inputs[2])
    L(iop.outputs[0], rot.inputs["Instances"]); L(cy.outputs[0], rot.inputs["Rotation"])
    rot.inputs["Local Space"].default_value = True
    jn = N("GeometryNodeJoinGeometry")
    L(rot.outputs[0], jn.inputs[0]); L(gi.outputs[0], jn.inputs[0])
    L(jn.outputs[0], go.inputs[0])
    md = surface.modifiers.new(name, "NODES")
    md.node_group = ng
    return md
