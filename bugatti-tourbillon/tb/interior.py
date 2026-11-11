"""Fixed cabin of the Tourbillon: carbon tub, two bucket seats, twin-wing dashboard,
centre console with its polished blade, fixed-hub steering wheel with the skeleton
instrument cluster, pedals, mirror and the ambient light strips.

    from tb import interior
    parts = interior.build()            # objects go to spec.COLLECTIONS["interior"]

Everything is built directly in car coordinates (+X nose, +Y left / driver, +Z up) and
stays inside ``spec.CABIN`` (see ``envelope_report``).  Object prefix: ``INT_``.

Return dict of ``build()``
    root            INT_Root            Empty at the origin, parent of the whole cabin
    tub             INT_Tub             carbon floor / sills / bulkheads / tunnel
    floor_mats      INT_FloorMats       carpets (child of tub)
    pedals          INT_Pedals          accelerator, brake, footrest (child of tub)
    seat_L, seat_R  INT_Seat_L / _R     carbon shells (driver = L = +Y); pads, trim and
                                        mounts are children of the shell
    dash            INT_Dash            dark dash body; wings, vents, defrost slot, the
                                        steering pivot and its ambient strips are children
    console         INT_Console         leather spine; blade, dials, knob, switches,
                                        selector and its ambient strips are children
    steering_pivot  INT_SteeringPivot   Empty at spec.CABIN["steering_centre"]
    steering_rim    INT_SteeringRim     rim + spokes + rotating collar (child of pivot)
    steering_hub    INT_SteeringHub     FIXED hub pad, control pods, column (child of pivot)
    cluster         INT_Cluster         FIXED three-dial skeleton cluster (child of pivot)
    needles         [INT_Cluster_Needle_C, _L, _R]   children of the cluster
    console_dials   [INT_Console_Dial_Upper, _Lower] local +Z = dial axis
    mirror          INT_Mirror
    ambient         [INT_Ambient_Dash_L, _R, INT_Ambient_Console_L, _R,
                     INT_Ambient_Footwell_L, _R]

Steering convention
    INT_SteeringPivot sits at the wheel centre.  Its local axes are
        +Z  along the column, towards the driver (up and back, raked 22 deg),
        +Y  12 o'clock of the wheel, +X  3 o'clock as the driver sees it (car -Y).
    INT_SteeringRim is a child with an identity local transform: steer by rotating it
    about its local Z (``rim.rotation_euler.z``; negative = clockwise for the driver =
    turning right).  Hub pad, pods, column and the cluster are separate children of the
    pivot and never rotate.  Needles turn about their local Z (clockwise = negative).
"""
import math
import bpy
import bmesh
import numpy as np
from . import spec, util, materials

C = spec.CABIN
PREFIX = "INT_"
PI = math.pi


# ====================================================================== small maths
def _unit(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-12)


def _M(origin=(0, 0, 0), x=(1, 0, 0), y=(0, 1, 0), z=(0, 0, 1)):
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, z, origin
    return m


def _T(x=0.0, y=0.0, z=0.0):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def _S(sx=1.0, sy=1.0, sz=1.0):
    return np.diag([sx, sy, sz, 1.0])


def _R(axis, ang):
    c, s = math.cos(ang), math.sin(ang)
    m = np.eye(4)
    if axis == 'x':
        m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    elif axis == 'y':
        m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    else:
        m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
    return m


def _frame(origin, z_axis, x_hint=(1, 0, 0)):
    """4x4 with local Z = z_axis and local X as close as possible to x_hint."""
    z = _unit(z_axis)
    x = np.asarray(x_hint, float)
    x = _unit(x - z * np.dot(x, z))
    return _M(origin, x, np.cross(z, x), z)


def _lerp(a, b, t):
    return a + (b - a) * t


def _sstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _mat(m):
    return materials.get(m) if isinstance(m, str) else m


def _local_material(name, **inputs):
    """Module-local material (listed in the final report so it can be promoted)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        materials.N(mat).set(**inputs)
    return mat


def _brass():
    """Warm gilt metal for the cluster gear wheels."""
    return _local_material("TB_interior_brass", Base_Color=(0.78, 0.57, 0.26), Metallic=1.0, Roughness=0.22)


# ====================================================================== mesh accumulator
class _MB:
    """Collects (verts, faces) primitives with a material each into one mesh object."""

    def __init__(self):
        self.V, self.F, self.FM, self.mats, self.n = [], [], [], [], 0

    def slot(self, mat):
        for i, m in enumerate(self.mats):
            if m is mat or m == mat:
                return i
        self.mats.append(mat)
        return len(self.mats) - 1

    def add(self, vf, mat, M=None):
        """mat: one material, or a list with one material per face."""
        v, f = vf
        v = np.asarray(v, float).reshape(-1, 3)
        flip = False
        if M is not None:
            M = np.asarray(M, float)
            v = v @ M[:3, :3].T + M[:3, 3]
            flip = np.linalg.det(M[:3, :3]) < 0
        per_face = isinstance(mat, (list, tuple))
        s = None if per_face else self.slot(mat)
        for k, face in enumerate(f):
            idx = [self.n + int(i) for i in face]
            self.F.append(idx[::-1] if flip else idx)
            self.FM.append(self.slot(mat[k]) if per_face else s)
        self.V.append(v)
        self.n += len(v)
        return self

    def build(self, name, col, angle=35.0, recalc=True, matrix=None):
        V = np.vstack(self.V) if self.V else np.zeros((0, 3))
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], self.F)
        me.update()
        for m in self.mats:
            me.materials.append(_mat(m))
        if len(me.polygons) == len(self.FM):
            me.polygons.foreach_set("material_index", self.FM)
        if recalc:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
        me.update()
        obj = bpy.data.objects.new(name, me)
        col.objects.link(obj)
        me.shade_smooth()
        if angle is not None:
            me.set_sharp_from_angle(angle=math.radians(angle))
        if matrix is not None:
            from mathutils import Matrix
            obj.matrix_world = Matrix(np.asarray(matrix).tolist())
        return obj


def _merge(parts):
    V, F, n = [], [], 0
    for v, f in parts:
        v = np.asarray(v, float).reshape(-1, 3)
        V.append(v)
        F += [[n + int(i) for i in face] for face in f]
        n += len(v)
    return np.vstack(V), F


def _xf(vf, M):
    v, f = vf
    v = np.asarray(v, float).reshape(-1, 3)
    M = np.asarray(M, float)
    v = v @ M[:3, :3].T + M[:3, 3]
    if np.linalg.det(M[:3, :3]) < 0:
        f = [list(face)[::-1] for face in f]
    return v, f


# ====================================================================== primitives -> (verts, faces)
def _lathe(profile, seg=32, closed=False):
    """Revolve an (r, z) profile about local Z.  r ~ 0 points become poles."""
    verts, rings = [], []
    for r, z in profile:
        if r < 1e-9:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
        else:
            rings.append(list(range(len(verts), len(verts) + seg)))
            verts += [(r * math.cos(2 * PI * i / seg), r * math.sin(2 * PI * i / seg), z) for i in range(seg)]
    faces = []
    pairs = list(zip(rings[:-1], rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(seg):
            j = (i + 1) % seg
            if len(a) == 1:
                faces.append((a[0], b[j], b[i]))
            elif len(b) == 1:
                faces.append((a[i], a[j], b[0]))
            else:
                faces.append((a[i], a[j], b[j], b[i]))
    return np.array(verts), faces


def _cyl(r, z0, z1, seg=24, bev=0.0):
    if bev > 0:
        prof = [(0, z0), (r - bev, z0), (r, z0 + bev), (r, z1 - bev), (r - bev, z1), (0, z1)]
    else:
        prof = [(0, z0), (r, z0), (r, z1), (0, z1)]
    return _lathe(prof, seg)


def _ring(r0, r1, z0, z1, seg=32, bev=0.0):
    """Annular solid between radii r0 < r1."""
    if bev > 0:
        prof = [(r0, z0), (r1 - bev, z0), (r1, z0 + bev), (r1, z1 - bev), (r1 - bev, z1), (r0, z1)]
    else:
        prof = [(r0, z0), (r1, z0), (r1, z1), (r0, z1)]
    return _lathe(prof, seg, closed=True)


def _knurl_ring(r_out, r_in, z0, z1, n=60, depth=0.0008, bev=0.001):
    """Ring whose outer wall carries n straight knurl ridges (real geometry)."""
    seg = 2 * n
    rows = [(r_in, z0, 0), (r_out - depth - bev, z0, 0), (r_out, z0 + bev, 1),
            (r_out, z1 - bev, 1), (r_out - depth - bev, z1, 0), (r_in, z1, 0)]
    verts = []
    for r, z, kn in rows:
        for i in range(seg):
            rr = r - depth * (i % 2) if kn else r
            a = 2 * PI * i / seg
            verts.append((rr * math.cos(a), rr * math.sin(a), z))
    faces = []
    nr = len(rows)
    for k in range(nr):
        a0, b0 = k * seg, ((k + 1) % nr) * seg
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((a0 + i, a0 + j, b0 + j, b0 + i))
    return np.array(verts), faces


def _box(sx, sy, sz, bev=0.0):
    if bev <= 0:
        x, y, z = sx / 2, sy / 2, sz / 2
        v = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        return np.array(v), f
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bev, 0.45 * min(sx, sy, sz)),
                    segments=1, affect='EDGES', profile=0.5)
    bm.verts.index_update()
    verts = np.array([tuple(v.co) for v in bm.verts])
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return verts, faces


def _offset_outline(P, d):
    """Offset a closed CCW 2D outline outwards by d (negative = inwards)."""
    P = np.asarray(P, float)
    e = np.roll(P, -1, axis=0) - P
    n = np.stack([e[:, 1], -e[:, 0]], axis=1)
    n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
    nv = n + np.roll(n, 1, axis=0)
    nv /= (np.linalg.norm(nv, axis=1, keepdims=True) + 1e-12)
    cosang = np.clip(np.sum(nv * n, axis=1), 0.35, 1.0)
    return P + nv * (d / cosang)[:, None]


def _prism(outline, z0, z1, bev=0.0):
    """Extrude a closed CCW 2D outline along Z (n-gon caps), optional top/bottom chamfer."""
    O = np.asarray(outline, float)
    n = len(O)
    rings = []
    if bev > 0:
        I = _offset_outline(O, -bev)
        rings = [(I, z0), (O, z0 + bev), (O, z1 - bev), (I, z1)]
    else:
        rings = [(O, z0), (O, z1)]
    verts, faces = [], []
    for R2, z in rings:
        verts += [(p[0], p[1], z) for p in R2]
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        faces += [(a + i, a + (i + 1) % n, b + (i + 1) % n, b + i) for i in range(n)]
    faces.append(tuple(range(n))[::-1])
    top = (len(rings) - 1) * n
    faces.append(tuple(range(top, top + n)))
    return np.array(verts), faces


def _stadium(w, l, seg=8, side_seg=6, bend=0.0):
    """Capsule outline: total width w (x), total length l (y), CCW.  bend = sagitta in +x."""
    r, h = w / 2, l / 2 - w / 2
    pts = []
    for i in range(seg + 1):
        a = PI * i / seg
        pts.append((r * math.cos(a), h + r * math.sin(a)))
    for i in range(1, side_seg):
        pts.append((-r, h - 2 * h * i / side_seg))
    for i in range(seg + 1):
        a = PI + PI * i / seg
        pts.append((r * math.cos(a), -h + r * math.sin(a)))
    for i in range(1, side_seg):
        pts.append((r, -h + 2 * h * i / side_seg))
    P = np.array(pts)
    if bend:
        P[:, 0] += bend * (1 - (P[:, 1] / (l / 2)) ** 2)
    return P


def _ellipse(a, b, n=40):
    t = np.linspace(0, 2 * PI, n, endpoint=False)
    return np.stack([a * np.cos(t), b * np.sin(t)], axis=1)


def _sweep_n(profile, path, normals, closed=True, caps=True):
    """Sweep a closed (n, b) profile along a path; n follows the given normals."""
    P = np.asarray(path, float)
    Nn = np.asarray(normals, float)
    if Nn.ndim == 1:
        Nn = np.tile(Nn, (len(P), 1))
    m = len(P)
    if closed:
        T = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    else:
        T = np.gradient(P, axis=0)
    T /= (np.linalg.norm(T, axis=1, keepdims=True) + 1e-12)
    Nn = Nn - T * np.sum(Nn * T, axis=1, keepdims=True)
    Nn /= (np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-12)
    B = np.cross(T, Nn)
    secs = [[P[i] + Nn[i] * pn + B[i] * pb for pn, pb in profile] for i in range(m)]
    return util.loft(secs, closed_v=True, closed_u=closed,
                     cap_start=caps and not closed, cap_end=caps and not closed)


def _half_round(w, h, n=5):
    """Half-round bead profile (n, b): flat on the surface, height h, width w."""
    pts = [(-0.3 * h, -w / 2)]
    for i in range(n + 1):
        a = PI * i / n
        pts.append((h * math.sin(a), -w / 2 * math.cos(a)))
    pts.append((-0.3 * h, w / 2))
    return pts


def _flat_bar(w, h, c=None):
    """Chamfered flat bar profile (n, b): sits on n = 0, height h, width w."""
    c = min(h, w) * 0.3 if c is None else c
    return [(0, -w / 2), (h - c, -w / 2), (h, -w / 2 + c), (h, w / 2 - c), (h - c, w / 2), (0, w / 2)]


def _rod(p0, p1, r, seg=10, r1=None):
    """Round rod between two 3D points (optionally tapered)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    r1 = r if r1 is None else r1
    vf = _lathe([(0, 0), (r, 0), (r1, L), (0, L)], seg)
    d = (p1 - p0) / L
    hint = (1, 0, 0) if abs(d[0]) < 0.9 else (0, 1, 0)
    return _xf(vf, _frame(p0, d, hint))


def _bar(p0, p1, w, t, up=(0, 0, 1), bev=0.0):
    """Rectangular bar from p0 to p1: width w across, thickness t along `up`."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    z = d / L
    u = np.asarray(up, float)
    u = _unit(u - z * np.dot(u, z))
    return _xf(_box(w, t, L, bev), _M((p0 + p1) / 2, np.cross(u, z), u, z))


def _gear(n, r_tip, tooth, thick, r_in=None, hub=0.0, spokes=0, spoke_w=None):
    """Thin spur wheel in the XY plane (centred on z = 0) with optional spokes and hub."""
    r_root = r_tip - tooth
    m = 4 * n
    p = 2 * PI / n
    ang, rad = [], []
    for k in range(n):
        a = k * p
        ang += [a - 0.30 * p, a - 0.13 * p, a + 0.13 * p, a + 0.30 * p]
        rad += [r_root, r_tip, r_tip, r_root]
    ang, rad = np.array(ang), np.array(rad)
    co, si = np.cos(ang), np.sin(ang)
    h = thick / 2
    ot = np.stack([rad * co, rad * si, np.full(m, h)], 1)
    ob = np.stack([rad * co, rad * si, np.full(m, -h)], 1)
    parts = []
    if not r_in:
        V = np.vstack([ot, ob, [(0, 0, h)], [(0, 0, -h)]])
        F = []
        for i in range(m):
            j = (i + 1) % m
            F += [(i, j, 2 * m), (m + j, m + i, 2 * m + 1), (m + i, m + j, j, i)]
        parts.append((V, F))
    else:
        it = np.stack([r_in * co, r_in * si, np.full(m, h)], 1)
        ib = np.stack([r_in * co, r_in * si, np.full(m, -h)], 1)
        V = np.vstack([ot, ob, it, ib])
        F = []
        for i in range(m):
            j = (i + 1) % m
            F += [(i, j, 2 * m + j, 2 * m + i), (m + j, m + i, 3 * m + i, 3 * m + j),
                  (m + i, m + j, j, i), (3 * m + j, 3 * m + i, 2 * m + i, 2 * m + j)]
        parts.append((V, F))
        if hub > 0:
            parts.append(_cyl(hub, -h * 1.5, h * 1.5, 16))
        sw = spoke_w or r_tip * 0.16
        for k in range(spokes):
            a = 2 * PI * k / spokes + 0.3
            L = r_in - hub * 0.7 + 0.0004
            b = _box(L, sw, thick * 0.7)
            parts.append(_xf(b, _R('z', a) @ _T(hub * 0.7 + L / 2, 0, 0)))
    return _merge(parts)


def _pillow(front, skirt, flip=False, back=None):
    """Pillow cage from an (nu, nv, 3) front grid.

    skirt: (nu, nv, 3) grid whose boundary ring becomes a turned-down edge (open pad), or
    back:  full (nu, nv, 3) back grid -> closed manifold pillow (front + back).
    """
    Fg = np.asarray(front, float)
    nu, nv, _ = Fg.shape
    verts = Fg.reshape(-1, 3).tolist()
    faces = util.grid_faces(nu, nv, flip=flip)
    loop = ([(u, nv - 1) for u in range(nu)] + [(nu - 1, v) for v in range(nv - 2, -1, -1)] +
            [(u, 0) for u in range(nu - 2, -1, -1)] + [(0, v) for v in range(1, nv - 1)])
    if not flip:
        loop = loop[::-1]
    lidx = [u * nv + v for u, v in loop]
    if back is not None:
        Bg = np.asarray(back, float)
        off = len(verts)
        verts += Bg.reshape(-1, 3).tolist()
        faces += [tuple(off + i for i in q) for q in util.grid_faces(nu, nv, flip=not flip)]
        bidx = [off + i for i in lidx]
    else:
        Sg = np.asarray(skirt, float)
        off = len(verts)
        verts += [Sg[u, v].tolist() for u, v in loop]
        bidx = [off + k for k in range(len(loop))]
    m = len(lidx)
    for k in range(m):
        k1 = (k + 1) % m
        faces.append((lidx[k1], lidx[k], bidx[k], bidx[k1]))
    return np.array(verts), faces


def _edge_params(a0, a1, n, roll):
    """n values from a0 to a1 with a short first/last step (controls the edge radius)."""
    roll = min(roll, abs(a1 - a0) * 0.2)
    sgn = 1.0 if a1 >= a0 else -1.0
    inner = np.linspace(a0 + sgn * roll, a1 - sgn * roll, n - 2)
    return np.concatenate([[a0], inner, [a1]])


def _obj(name, vf, col, mat, angle=None, recalc=False):
    v, f = vf
    o = util.mesh_object(name, np.asarray(v, float).tolist(), [tuple(int(i) for i in q) for q in f],
                         collection=col, material=_mat(mat), smooth=True)
    if recalc:
        util.recalc_normals(o)
    if angle is not None:
        util.shade_smooth(o, angle)
    return o


def _child(obj, par):
    """Parent while keeping the world transform (cheap: no view-layer update needed
    because every parent used here sits at an already evaluated transform)."""
    obj.parent = par
    obj.matrix_parent_inverse = par.matrix_world.inverted()
    return obj


# ====================================================================== cabin envelope
def half_width_at(z):
    """Inner half-width of the cabin at height z (sill -> door card -> side glass -> roof)."""
    return float(np.interp(z, [0.16, 0.60, 0.84, 1.12, 1.13],
                           [C["half_width_floor"], C["half_width_shoulder"], 0.74, 0.52, C["half_width_roof"]]))


def windshield_z(x):
    """Height of the windshield glass plane above x (valid for x >= header)."""
    k = (spec.WINDSHIELD_TOP_Z - spec.WINDSHIELD_BASE_Z) / (spec.WINDSHIELD_BASE_X - spec.WINDSHIELD_TOP_X)
    return spec.WINDSHIELD_BASE_Z + (spec.WINDSHIELD_BASE_X - x) * k


def cowl_x(y):
    """Windshield base in plan (measured from the blueprint: strongly curved, ~ y^4)."""
    return C["x_cowl"] - 1.65 * abs(y) ** 4


def _footwell_half_width(x):
    """Half-width at floor level: 0.60, narrowing ahead of the door for the wheel houses."""
    return C["half_width_floor"] - 0.08 * min(1.0, max(0.0, (x - 0.85) / 0.40))


def envelope_report(objs, verbose=True):
    """Check every evaluated vertex against the cabin envelope.  Returns the worst margins
    (negative = outside) as a dict; prints per-object bounds when verbose."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    worst = dict(firewall=9.0, floor=9.0, side=9.0, roof=9.0, windshield=9.0, cowl=9.0)
    who = dict.fromkeys(worst, "")
    for o in objs:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        n = len(me.vertices)
        if n == 0:
            ev.to_mesh_clear()
            continue
        co = np.empty(n * 3)
        me.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
        co = co.reshape(-1, 3)
        Mw = np.array(o.matrix_world)
        P = co @ Mw[:3, :3].T + Mw[:3, 3]
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        hw = np.interp(z, [0.16, 0.60, 0.84, 1.12, 1.13], [0.60, 0.72, 0.74, 0.52, 0.50])
        ws = spec.WINDSHIELD_BASE_Z + (spec.WINDSHIELD_BASE_X - x) * 0.40278
        m = dict(firewall=float((x - C["x_firewall"]).min()),
                 floor=float((z - 0.125).min()),
                 side=float((hw - np.abs(y)).min()),
                 roof=float((C["roof_z"] - z).min()),
                 windshield=float((ws - z).min()),
                 cowl=float(np.where(z > 0.70, C["x_cowl"] - 1.65 * np.abs(y) ** 4 - x, 9.0).min()))
        for k in worst:
            if m[k] < worst[k]:
                worst[k], who[k] = m[k], o.name
        if verbose:
            print("  %-28s x[%+.3f %+.3f] y[%+.3f %+.3f] z[%+.3f %+.3f]" % (
                o.name, x.min(), x.max(), y.min(), y.max(), z.min(), z.max()))
    if verbose:
        print("envelope margins (m, negative = outside):")
        for k in worst:
            print("  %-10s %+.4f  (%s)" % (k, worst[k], who[k]))
    return worst


# ====================================================================== console spine curve
_CONSOLE_TOP = [(-0.548, 0.445), (-0.40, 0.418), (-0.15, 0.402), (0.10, 0.402), (0.26, 0.430),
                (0.40, 0.510), (0.55, 0.632), (0.68, 0.742), (0.77, 0.820), (0.86, 0.858),
                (1.00, 0.864), (1.24, 0.861)]
_console_top = util.Curve1D(_CONSOLE_TOP)


def _console_frame(x, y=0.0, lift=0.0):
    """Frame on the console top at x: local X up the slope (forward), Y = car left, Z = normal."""
    z = float(_console_top(x))
    dz = float(_console_top.d(x))
    n = _unit((-dz, 0.0, 1.0))
    o = np.array([x, y, z]) + n * lift
    return _frame(o, n, (1.0, 0.0, dz))


# ====================================================================== TUB
def _build_tub(col):
    mb = _MB()
    CG = "carbon_gloss"
    xf, xb = 1.25, C["x_firewall"]
    # floor slab
    fl = [(xb, -0.598), (0.85, -0.598), (xf, -0.518), (xf, 0.518), (0.85, 0.598), (xb, 0.598)]
    mb.add(_prism(fl, 0.132, C["floor_z"], bev=0.004), CG)
    # inner sill liners, rising into the footwell sides ahead of the door
    for side in (1, -1):
        secs = []
        for x in np.linspace(xb, xf, 41):
            yf = _footwell_half_width(x)
            zt = 0.36 + 0.14 * _sstep(0.62, 0.98, x)
            yo = lambda z: yf + 0.2727 * (z - 0.16) - 0.003
            sec = [(yo(0.16), 0.16), (yo(zt - 0.012), zt - 0.012), (yo(zt) - 0.005, zt),
                   (yo(zt) - 0.011, zt), (yo(zt - 0.012) - 0.016, zt - 0.012), (yo(0.16) - 0.016, 0.16)]
            secs.append([(x, side * yy, zz) for yy, zz in sec])
        mb.add(util.loft(secs, closed_v=True, cap_start=True, cap_end=True), CG)
    # rear bulkhead (firewall) with a raised cross beam and centre spine
    ro = [(-0.598, 0.16), (0.598, 0.16), (0.700, 0.56), (0.700, 0.80), (0.62, 0.95), (0.50, 1.02),
          (-0.50, 1.02), (-0.62, 0.95), (-0.700, 0.80), (-0.700, 0.56)]
    mb.add(util.extrude_outline(ro, 0.014, plane='YZ', offset=xb), CG)
    mb.add(_xf(_box(0.022, 1.16, 0.06, 0.006), _T(xb + 0.022, 0, 0.90)), CG)
    mb.add(_xf(_box(0.020, 0.10, 0.52, 0.006), _T(xb + 0.022, 0, 0.72)), CG)
    # toe board + front bulkhead (one XZ profile)
    tb = [(1.09, 0.158), (xf, 0.158), (xf, 0.62), (1.236, 0.62), (1.236, 0.372), (1.10, 0.170)]
    mb.add(util.extrude_outline(tb, 1.04, plane='XZ', offset=0.0, both=True), CG)
    # centre tunnel structure (hidden under the leather console, visible in the footwells)
    secs = []
    for x in np.linspace(xb + 0.012, xf, 37):
        top = min(float(_console_top(x)) - 0.03, 0.60)
        secs.append([(x, -0.108, 0.16), (x, -0.104, top - 0.02), (x, -0.085, top), (x, 0.085, top),
                     (x, 0.104, top - 0.02), (x, 0.108, 0.16)])
    mb.add(util.loft(secs, closed_v=True, cap_start=True, cap_end=True), CG)
    tub = mb.build(PREFIX + "Tub", col, angle=40)
    util.bevel(tub, 0.003, segments=2, angle_deg=40)

    # ---------------- carpets
    mm = _MB()
    for side in (1, -1):
        # base carpet over the whole floor half
        base = [(xb + 0.016, 0.119), (0.85, 0.119), (1.09, 0.119), (1.09, _footwell_half_width(1.09) - 0.020),
                (0.85, 0.580), (xb + 0.016, 0.580)]
        base = [(x, side * y) for x, y in base]
        if side < 0:
            base = base[::-1]
        mm.add(_prism(base, C["floor_z"], C["floor_z"] + 0.005), "carpet_dark")
        # footwell mat with a leather piping
        w0, w1 = 0.135, 0.560
        cx, cy = 0.745, side * (w0 + w1) / 2
        ol = util.rounded_rect(0.60, w1 - w0, 0.035, seg=5) + np.array([cx, cy])
        mm.add(_prism(ol, C["floor_z"] + 0.005, C["floor_z"] + 0.013, bev=0.002), "carpet_dark")
        path = [(p[0], p[1], C["floor_z"] + 0.0125) for p in ol]
        mm.add(util.tube(path, 0.0035, segments=6, closed_path=True, caps=False), "leather_light")
        # toe board carpet
        tbm = [(1.105, 0.176), (1.236, 0.378), (1.229, 0.383), (1.098, 0.181)]
        v, f = util.extrude_outline(tbm, 0.38, plane='XZ', offset=side * 0.325, both=True)
        mm.add((v, f), "carpet_dark")
    mats = mm.build(PREFIX + "FloorMats", col, angle=40)
    _child(mats, tub)
    return tub, mats


# ====================================================================== SEATS
# Centre-line of the upholstery surface in side view, from under the cushion nose, back
# along the cushion, round the bite line and up the 27 deg backrest to the headrest top.
#   x, z            centre-line point (H-point is at x -0.02, z 0.30)
#   B               bolster height above the centre panel
#   wo, wc          half-width over the bolsters / half-width of the centre panel
_SEAT_CTRL = [
    (0.380, 0.205, 0.000, 0.196, 0.110),   # 0  tucked under the nose
    (0.402, 0.262, 0.010, 0.202, 0.112),   # 1  nose
    (0.372, 0.302, 0.030, 0.208, 0.115),   # 2  front top edge
    (0.290, 0.290, 0.052, 0.212, 0.117),   # 3
    (0.180, 0.262, 0.075, 0.214, 0.118),   # 4
    (0.060, 0.234, 0.098, 0.214, 0.118),   # 5
    (-0.050, 0.214, 0.115, 0.214, 0.118),  # 6
    (-0.122, 0.212, 0.125, 0.214, 0.118),  # 7  bite line
    (-0.166, 0.252, 0.125, 0.214, 0.118),  # 8  corner
    (-0.190, 0.325, 0.105, 0.213, 0.118),  # 9  lumbar
    (-0.236, 0.440, 0.082, 0.214, 0.118),  # 10
    (-0.290, 0.560, 0.085, 0.222, 0.120),  # 11
    (-0.343, 0.680, 0.090, 0.228, 0.115),  # 12 shoulder wings
    (-0.382, 0.770, 0.050, 0.200, 0.090),  # 13 neck / harness slot
    (-0.400, 0.860, 0.028, 0.140, 0.075),  # 14 headrest
    (-0.424, 0.950, 0.030, 0.125, 0.070),  # 15
    (-0.448, 1.020, 0.018, 0.100, 0.055),  # 16 top
]


class _SeatGeom:
    """Parametric seat surface: s = arc length along the centre line, l = lateral offset."""

    def __init__(self, y0):
        self.y0 = y0
        ctrl = np.array(_SEAT_CTRL)
        sps = 12
        dense = util.catmull_rom(ctrl[:, :2], samples_per_seg=sps)
        d = np.linalg.norm(np.diff(dense, axis=0), axis=1)
        S = np.concatenate([[0.0], np.cumsum(d)])
        self.sk_tab = S[::sps]
        self.S, self.dense, self.s_end = S, dense, S[-1]
        ds = 0.004
        su = np.arange(0, S[-1] + ds * 0.5, ds)
        xu, zu = np.interp(su, S, dense[:, 0]), np.interp(su, S, dense[:, 1])
        tx, tz = np.gradient(xu, su), np.gradient(zu, su)
        sig = 0.040 / ds
        k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2)
        k /= k.sum()
        pad = len(k) // 2
        txs = np.convolve(np.pad(tx, pad, mode='edge'), k, mode='valid')
        tzs = np.convolve(np.pad(tz, pad, mode='edge'), k, mode='valid')
        nrm = np.hypot(txs, tzs)
        self.su, self.txs, self.tzs = su, txs / nrm, tzs / nrm
        self.fB = util.Curve1D(list(zip(self.sk_tab, ctrl[:, 2])))
        self.fwo = util.Curve1D(list(zip(self.sk_tab, ctrl[:, 3])))
        self.fwc = util.Curve1D(list(zip(self.sk_tab, ctrl[:, 4])))

    def sk(self, k):
        return float(np.interp(k, np.arange(len(self.sk_tab)), self.sk_tab))

    def frame(self, s):
        """Centre point (x, z) and smoothed occupant-side normal (nx, nz) at s."""
        sc = min(max(s, 0.0), self.s_end)
        x, z = np.interp(sc, self.S, self.dense[:, 0]), np.interp(sc, self.S, self.dense[:, 1])
        tx, tz = np.interp(sc, self.su, self.txs), np.interp(sc, self.su, self.tzs)
        if s > self.s_end:
            x, z = x + tx * (s - self.s_end), z + tz * (s - self.s_end)
        return x, z, tz, -tx

    def B(self, s):
        return float(self.fB(s))

    def wo(self, s):
        return float(self.fwo(s))

    def wc(self, s):
        return float(self.fwc(s))

    def nA(self, s, l):
        """Height of the upholstery surface above the centre line (bolster shape)."""
        a = abs(l)
        wc, wo = self.wc(s), self.wo(s)
        q = min(1.0, max(0.0, (a - wc) / (0.82 * (wo - wc))))
        return 0.006 * (min(a, wc) / wc) ** 2 + self.B(s) * q * q * (3 - 2 * q)

    def n_shell(self, s, l):
        """Inner skin of the carbon shell (behind the pads, rising to a rim at the sides)."""
        a = abs(l)
        wc, wo = self.wc(s), self.wo(s)
        W = wo + 0.015
        if a <= wo:
            return self.nA(s, a) - (0.034 - 0.018 * _sstep(wc * 0.8, wo, a))
        return self.nA(s, wo) - 0.016 + 0.020 * (a - wo) / (W - wo)

    def pt(self, s, l, n):
        x, z, nx, nz = self.frame(s)
        return (x + nx * n, self.y0 + l, z + nz * n)

    def nrm(self, s):
        _, _, nx, nz = self.frame(s)
        return (nx, 0.0, nz)


def _seat_pad(mb, g, k0, k1, l0, l1, na, nb, mat, roll=0.013, drop=0.010, skirt=0.022, puff=0.005):
    """One upholstery panel between control indices k0..k1 and lateral limits l0(s)..l1(s)."""
    s0, s1 = g.sk(k0), g.sk(k1)
    sa = _edge_params(s0, s1, na, roll)
    front = np.zeros((na, nb, 3))
    sk = np.zeros((na, nb, 3))
    for i, s in enumerate(sa):
        a, b = (l0(s), l1(s)) if callable(l0) else (l0, l1)
        lb = _edge_params(a, b, nb, roll)
        for j, l in enumerate(lb):
            nA = g.nA(s, l)
            edge = i in (0, na - 1) or j in (0, nb - 1)
            u, v = i / (na - 1), j / (nb - 1)
            crown = puff * (math.sin(PI * u) * math.sin(PI * v)) ** 0.5
            front[i, j] = g.pt(s, l, nA - drop if edge else nA + crown)
            sk[i, j] = g.pt(s, l, nA - skirt)
    mb.add(_pillow(front, sk, flip=True), mat)


def _build_seat(col, tag, y0):
    g = _SeatGeom(y0)
    # ---------------- carbon shell
    ks = [2.15, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.35, 7.7, 8, 8.4, 9, 9.5, 10, 10.5, 11,
          11.5, 12, 12.42, 12.82, 13.28, 13.68, 14, 14.5, 15, 15.5, 16, 16.2]
    nl = 13
    verts = []
    for k in ks:
        s = g.sk(min(k, 16)) + (0.014 if k > 16 else 0.0)
        wc, wo = g.wc(s), g.wo(s)
        W = wo + 0.015
        half = [0.0, 0.5 * wc, wc, wc + 0.5 * (wo - wc), wo - 0.012, wo + 0.003, W]
        ls = [-a for a in half[:0:-1]] + half
        curl = 1.0 if k <= 15.5 else (0.6 if k <= 16 else 0.0)
        if k < 2.4:
            curl = 0.7
        for l in ls:
            nA = g.nA(s, min(abs(l), wo))
            n = nA + (g.n_shell(s, l) - nA) * curl
            if k > 16:
                n = nA + 0.004
                l *= 0.86
            verts.append(g.pt(s, l, n))
    i0, i1 = ks.index(12.82), ks.index(13.28)
    faces = []
    for q in util.grid_faces(len(ks), nl, flip=True):
        u = min(q) // nl
        v = min(i % nl for i in q)
        if u == i0 and 4 <= v <= 7:          # harness slot between the shoulders
            continue
        faces.append(q)
    shell = _obj(PREFIX + "Seat_" + tag, (verts, faces), col, "carbon_gloss")
    util.solidify(shell, 0.009, offset=-1.0)
    util.subsurf(shell, 2)

    # ---------------- upholstery
    mb = _MB()
    P, L = "leather_perforated", "leather_light"
    gp = 0.003
    wcp = lambda s: g.wc(s) - gp
    wcm = lambda s: -(g.wc(s) - gp)
    bo0 = lambda s: g.wc(s) + gp
    bo1 = lambda s: g.wo(s) - 0.002
    _seat_pad(mb, g, 0.25, 3.45, wcm, wcp, 9, 8, P)                     # cushion, thigh panel
    _seat_pad(mb, g, 3.52, 7.55, wcm, wcp, 11, 8, P)                    # cushion, main panel
    _seat_pad(mb, g, 7.62, 10.25, wcm, wcp, 9, 8, P)                    # back, lumbar panel
    _seat_pad(mb, g, 10.32, 12.55, wcm, wcp, 8, 8, P)                   # back, upper panel
    for sgn in (1, -1):
        a = (lambda s, sgn=sgn: sgn * bo0(s))
        b = (lambda s, sgn=sgn: sgn * bo1(s))
        lo, hi = (a, b) if sgn > 0 else (b, a)
        _seat_pad(mb, g, 0.25, 7.85, lo, hi, 18, 6, L)                  # thigh / hip bolster
        _seat_pad(mb, g, 7.92, 12.6, lo, hi, 14, 6, L)                  # torso bolster
    _seat_pad(mb, g, 13.62, 15.85, lambda s: -(g.wo(s) - 0.012), lambda s: g.wo(s) - 0.012, 8, 9, L)
    pads = mb.build(PREFIX + "Seat_%s_Pads" % tag, col, angle=None, recalc=False)
    util.subsurf(pads, 2)
    _child(pads, shell)

    # ---------------- trim + mounts
    tm = _MB()
    AP = "alu_polished"
    for sgn in (1, -1):
        # slim aluminium handle in the seam between thigh panel and bolster
        ss = np.linspace(g.sk(2.55), g.sk(3.75), 9)
        path = [g.pt(s, sgn * (g.wc(s) + 0.001), g.nA(s, g.wc(s)) - 0.0035) for s in ss]
        nr = [g.nrm(s) for s in ss]
        tm.add(_sweep_n(_half_round(0.011, 0.0065), path, nr, closed=False), AP)
        tm.add(_sweep_n(_flat_bar(0.0045, 0.0072, 0.0008), path[1:-1], nr[1:-1], closed=False), "plastic_black")
        # bright inlay line down the back of the shell
        ss = np.linspace(g.sk(8.9), g.sk(12.35), 22)
        path, nr = [], []
        for s in ss:
            l = sgn * (g.wo(s) - 0.045)
            path.append(g.pt(s, l, g.n_shell(s, l) - 0.0075))
            nr.append(tuple(-c for c in g.nrm(s)))
        tm.add(_sweep_n(_flat_bar(0.006, 0.0035, 0.001), path, nr, closed=False), AP)
        # floor rails
        rail = [(-0.10, 0.164), (0.33, 0.164), (0.33, 0.250), (-0.10, 0.171)]
        tm.add(util.extrude_outline(rail, 0.022, plane='XZ', offset=y0 + sgn * 0.105, both=True), "alu_brushed")
    # trim bar under the harness slot (seen from behind) and at its front lip
    s = g.sk(12.72)
    for side, off in ((-1, -0.0078), (1, -0.0012)):
        ls = np.linspace(-g.wc(s) * 0.86, g.wc(s) * 0.86, 12)
        path = [g.pt(s, l, g.n_shell(s, l) + off) for l in ls]
        nn = tuple(side * c for c in g.nrm(s))
        tm.add(_sweep_n(_flat_bar(0.007, 0.004, 0.001), path, nn, closed=False), AP)
    trim = tm.build(PREFIX + "Seat_%s_Trim" % tag, col, angle=35)
    _child(trim, shell)
    return shell


# ====================================================================== DASHBOARD
_DASH_HALF = 0.700
_DASH_SPS = 6
_WING_H = 0.016            # how far the leather wings stand proud of the dark body
_dash_cache = {}


def _dash_ctrl(a):
    """Closed control loop (x, z) of the dash body section at |y| = a."""
    xr = 0.665 + 0.115 * (1 - a / 0.36) ** 2 if a < 0.36 else 0.665 - 0.035 * ((a - 0.36) / 0.35) ** 2
    xc = cowl_x(a) - 0.018
    zd = 0.845 - 0.020 * (a / 0.71) ** 2
    zl = 0.515 + 0.060 * (a / 0.70) ** 2
    dk = xc - xr - 0.055
    return np.array([
        (xc - 0.02, zl + 0.02),               # 0  underside, front
        (xr + 0.16, zl - 0.012),              # 1  underside
        (xr + 0.060, zl),                     # 2  lower edge              (t = 0)
        (xr + 0.022, zl + 0.06),              # 3
        (xr + 0.004, zl + 0.17),              # 4
        (xr, zd - 0.085),                     # 5  belly of the top roll
        (xr + 0.014, zd - 0.028),             # 6
        (xr + 0.055, zd),                     # 7  deck starts             (tau = 1)
        (xr + 0.055 + 0.3 * dk, zd + 0.008),  # 8
        (xr + 0.055 + 0.7 * dk, zd + 0.010),  # 9
        (xc, zd + 0.006),                     # 10 cowl edge under the windshield
        (xc + 0.004, zd - 0.035),             # 11
        (xc, zl + 0.10),                      # 12
    ])


def _dash_curve(y):
    key = round(abs(float(y)), 5)
    c = _dash_cache.get(key)
    if c is None:
        pts = util.catmull_rom(_dash_ctrl(key), samples_per_seg=_DASH_SPS, closed=True)
        op = pts[:12 * _DASH_SPS + 1]
        S = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(op, axis=0), axis=1))])
        S = S - S[2 * _DASH_SPS]
        c = (pts, op, S, float(S[7 * _DASH_SPS]), float(S[10 * _DASH_SPS]))
        _dash_cache[key] = c
    return c


def _dash_surf(y, t):
    """Point and outward normal of the dash skin at lateral y, arc length t from the lower edge."""
    _, op, S, _, _ = _dash_curve(y)
    x, z = np.interp(t, S, op[:, 0]), np.interp(t, S, op[:, 1])
    e = 0.004
    tx = np.interp(t + e, S, op[:, 0]) - np.interp(t - e, S, op[:, 0])
    tz = np.interp(t + e, S, op[:, 1]) - np.interp(t - e, S, op[:, 1])
    return np.array([x, y, z]), _unit((-tz, 0.0, tx))


def _dash_t(y, tau):
    """tau: 0 = lower edge, 1 = where the deck starts, > 1 = metres forward along the deck."""
    t7 = _dash_curve(y)[3]
    return tau * t7 if tau <= 1.0 else t7 + (tau - 1.0)


_WING_TOP = util.Curve1D([(0.235, 1.40), (0.30, 1.29), (0.40, 1.16), (0.55, 1.06), (0.692, 1.02)])
_WING_INNER = util.Curve1D([(-0.10, 0.122), (0.30, 0.122), (0.70, 0.125), (0.95, 0.138),
                            (1.10, 0.158), (1.25, 0.190), (1.40, 0.235)])
_VENTS = [(0.168, 0.52), (0.612, 0.52)]      # (|y|, tau) of the slot centres on each wing
_VENT_W, _VENT_L, _VENT_BEND = 0.020, 0.105, 0.005


def _wing_coons(u, v):
    """(|y|, tau) of the wing outline patch: u inner -> door, v lower edge -> eyebrow."""
    Y_IN, Y_OUT, Y_PK, TB, TPK, TO = 0.122, 0.692, 0.235, -0.10, 1.40, 1.02
    b = np.array([_lerp(Y_IN, Y_OUT, u), TB])
    yt = _lerp(Y_PK, Y_OUT, u)
    tp = np.array([yt, float(_WING_TOP(yt))])
    ti = _lerp(TB, TPK, v)
    inn = np.array([float(_WING_INNER(ti)), ti])
    out = np.array([Y_OUT, _lerp(TB, TO, v)])
    corners = ((1 - u) * (1 - v) * np.array([Y_IN, TB]) + u * (1 - v) * np.array([Y_OUT, TB]) +
               (1 - u) * v * np.array([Y_PK, TPK]) + u * v * np.array([Y_OUT, TO]))
    return (1 - v) * b + v * tp + (1 - u) * inn + u * out - corners


def _vent_frame(side, yv, tau, lift):
    P0, n = _dash_surf(side * yv, _dash_t(yv, tau))
    T = np.array([n[2], 0.0, -n[0]])
    return _M(P0 + n * lift, (0.0, float(side), 0.0), T, n)


def _build_dash(col):
    # ---------------- dark body: face, top roll, deck under the windshield, underside
    ys = np.linspace(-_DASH_HALF, _DASH_HALF, 59)
    secs = [[(p[0], y, p[1]) for p in _dash_curve(y)[0]] for y in ys]
    nv = len(secs[0])
    v, f = util.loft(secs, closed_v=True, cap_start=True, cap_end=True)
    fm = []
    for u in range(len(ys) - 1):
        for k in range(nv):
            fm.append("alcantara_dark" if 7 <= k // _DASH_SPS <= 11 else "leather_dark")
    fm += ["leather_dark", "leather_dark"]
    dash = _MB().add((v, f), fm).build(PREFIX + "Dash", col, angle=50)

    # ---------------- the two leather wings (closed pillows, slot vents cut by boolean)
    NU, NV = 30, 16
    us = np.concatenate([[0.0, 0.028], np.linspace(0.07, 0.93, NU - 4), [0.972, 1.0]])
    vs = np.concatenate([[0.0, 0.04], np.linspace(0.10, 0.90, NV - 4), [0.96, 1.0]])
    vent_outline = _stadium(_VENT_W, _VENT_L, seg=8, side_seg=8, bend=_VENT_BEND)
    wings = []
    for side, tag in ((1, "L"), (-1, "R")):
        front = np.zeros((NU, NV, 3))
        back = np.zeros((NU, NV, 3))
        for i, u in enumerate(us):
            for j, vv in enumerate(vs):
                yy, tau = _wing_coons(u, vv)
                P, n = _dash_surf(side * yy, _dash_t(yy, tau))
                edge = i in (0, NU - 1) or j in (0, NV - 1)
                front[i, j] = P + n * (0.0 if edge else _WING_H)
                back[i, j] = P - n * 0.030
        wing = _obj(PREFIX + "Dash_Wing_" + tag, _pillow(front, None, flip=side > 0, back=back),
                    col, "leather_light")
        util.subsurf(wing, 2)
        cut = _MB()
        for yv, tau in _VENTS:
            cut.add(_prism(vent_outline, -0.022, 0.030), "void_black", _vent_frame(side, yv, tau, _WING_H))
        cutter = cut.build(PREFIX + "tmp_VentCutter", col, angle=None)
        m = wing.modifiers.new("Vents", 'BOOLEAN')
        m.operation, m.solver, m.object = 'DIFFERENCE', 'EXACT', cutter
        try:
            m.material_mode = 'TRANSFER'
        except Exception:
            pass
        util.apply_modifiers(wing)
        util.delete(cutter)
        util.shade_smooth(wing, 42)
        _child(wing, dash)
        wings.append(wing)

    # ---------------- vent surrounds, vanes, defrost slot
    vb = _MB()
    ring = _offset_outline(vent_outline, 0.0022)
    for side in (1, -1):
        for yv, tau in _VENTS:
            t0 = _dash_t(yv, tau)
            path, nr = [], []
            for a, b in ring:
                P, n = _dash_surf(side * (yv + a), t0 + b)
                path.append(P + n * (_WING_H - 0.0005))
                nr.append(n)
            vb.add(_sweep_n(_half_round(0.0055, 0.0034), path, nr, closed=True), "alu_polished")
            M = _vent_frame(side, yv, tau, _WING_H)
            vb.add(_xf(_box(0.0018, _VENT_L - 0.016, 0.008), _T(_VENT_BEND * 0.6, 0, -0.008)), "alu_brushed", M)
            for b in (-0.034, -0.012, 0.012, 0.034):
                vb.add(_xf(_box(_VENT_W - 0.002, 0.0016, 0.006),
                           _T(_VENT_BEND * (1 - (b / (_VENT_L / 2)) ** 2), b, -0.011)), "plastic_black", M)
    path, nr = [], []
    for y in np.linspace(-0.46, 0.46, 47):
        P, n = _dash_surf(y, _dash_curve(y)[4] - 0.055)
        path.append(P)
        nr.append(n)
    vb.add(_sweep_n(_flat_bar(0.016, 0.0022, 0.0008), path, nr, closed=False), "plastic_black")
    vents = vb.build(PREFIX + "Dash_Vents", col, angle=35)
    _child(vents, dash)

    # ---------------- ambient strips along the base of each wing
    amb = []
    for side, tag in ((1, "L"), (-1, "R")):
        path, nr = [], []
        for yy in np.linspace(0.132, 0.684, 44):
            P, n = _dash_surf(side * yy, _dash_t(yy, -0.10) - 0.009)
            path.append(P)
            nr.append(n)
        st = _obj(PREFIX + "Ambient_Dash_" + tag, _sweep_n(_flat_bar(0.006, 0.003, 0.001), path, nr, closed=False),
                  col, "emit_interior", recalc=True)
        _child(st, dash)
        amb.append(st)
    return dash, wings, amb


# ====================================================================== CENTRE CONSOLE
_BLADE_HW = util.Curve1D([(-0.548, 0.010), (-0.20, 0.010), (0.02, 0.012), (0.14, 0.022), (0.215, 0.036),
                          (0.27, 0.040), (0.33, 0.044), (0.40, 0.047), (0.46, 0.046), (0.505, 0.038),
                          (0.535, 0.046), (0.565, 0.054), (0.610, 0.046), (0.655, 0.054), (0.695, 0.040),
                          (0.735, 0.016), (0.80, 0.007), (1.22, 0.005)])
_BLADE_LIFT = 0.0085        # blade top above the leather spine
_DIAL_X = (0.655, 0.565)    # upper / lower rotary dial
_KNOB_X = 0.497
_TOGGLE_X = (0.458, 0.428, 0.398, 0.368)
_SELECTOR_X = 0.262


def _console_strip(x0, x1, hw, z0, z1, n=40, chamfer=0.0015):
    """Flat strip lying on the console spine between x0 and x1 (hw: half-width or f(x))."""
    secs = []
    for x in np.linspace(x0, x1, n) if np.isscalar(n) else n:
        M = _console_frame(x)
        w = float(hw(x)) if callable(hw) else hw
        c = min(chamfer, 0.6 * w, 0.6 * (z1 - z0))
        prof = [(-w, z0), (-w, z1 - c), (-w + c, z1), (w - c, z1), (w, z1 - c), (w, z0)]
        secs.append([M[:3, 3] + M[:3, 1] * a + M[:3, 2] * b for a, b in prof])
    return util.loft(secs, closed_v=True, cap_start=True, cap_end=True)


def _rotary_dial(scale=1.0, glow=False):
    """Knurled rotary dial with a crystal barrel, built about local Z from z = 0 up."""
    mb = _MB()
    s = scale
    AP, AK = "alu_polished", "alu_knurled"
    mb.add(_lathe([(0, 0), (0.0380 * s, 0), (0.0380 * s, 0.0028), (0.0345 * s, 0.0058), (0, 0.0058)], 48), AP)
    mb.add(_knurl_ring(0.0335 * s, 0.018 * s, 0.0058, 0.0125, n=int(52 * s), depth=0.0008, bev=0.0008), AK)
    # crystal sleeve with the movement visible inside
    z0, z1 = 0.0125, 0.0365 * s + 0.004
    mb.add(_ring(0.0245 * s, 0.0290 * s, z0, z1, 48, bev=0.0006), "crystal")
    mb.add(_lathe([(0, z0), (0.011 * s, z0), (0.011 * s, z0 + 0.004), (0.007 * s, z0 + 0.006),
                   (0.007 * s, z1 - 0.006), (0.011 * s, z1 - 0.004), (0.011 * s, z1), (0, z1)], 24), AP)
    mb.add(_xf(_gear(int(36 * s), 0.0215 * s, 0.0016, 0.0016, r_in=0.015 * s, hub=0.008 * s, spokes=6),
               _T(0, 0, (z0 + z1) / 2)), _brass())
    for k in range(6):
        a = 2 * PI * k / 6
        mb.add(_xf(_cyl(0.0012, z0, z1, 8), _T(0.0225 * s * math.cos(a), 0.0225 * s * math.sin(a), 0)), AP)
    # knurled crown and top
    z2 = z1 + 0.0155
    mb.add(_knurl_ring(0.0345 * s, 0.018 * s, z1, z2, n=int(60 * s), depth=0.0009, bev=0.001), AK)
    mb.add(_lathe([(0.0335 * s, z2), (0.0310 * s, z2 + 0.003), (0.0272 * s, z2 + 0.003), (0.0272 * s, z2 - 0.002)],
                  48, closed=True), AP)
    mb.add(_cyl(0.0272 * s, z2 - 0.004, z2 + 0.0018, 40), "emit_screen" if glow else "plastic_gloss")
    if not glow:
        mb.add(_ring(0.0100 * s, 0.0125 * s, z2, z2 + 0.0028, 32, bev=0.0005), AP)
        mb.add(_cyl(0.0100 * s, z2, z2 + 0.0022, 24), "emit_dial")
        for k in range(12):
            a = 2 * PI * k / 12
            mb.add(_xf(_box(0.0050 * s, 0.0008, 0.0006), _R('z', a) @ _T(0.0215 * s, 0, z2 + 0.002)), "dial_face")
    return mb


def _build_console(col):
    # ---------------- leather spine from the rear bulkhead up into the dash and over the deck
    xs = np.concatenate([np.linspace(C["x_firewall"] + 0.014, 0.10, 14), np.linspace(0.14, 0.90, 30),
                         np.linspace(0.95, 1.24, 5)])
    secs = []
    for x in xs:
        top = float(_console_top(x))
        fz = 1.0 - 0.72 * _sstep(0.74, 0.96, x)
        mid = 0.16 + 0.55 * (top - 0.16)
        half = [(0.115, 0.16), (0.115, mid), (0.112, top - 0.05), (0.102 * fz, top - 0.014),
                (0.075 * fz, top - 0.001), (0.040 * fz, top + 0.003)]
        sec = [(-y, z) for y, z in half] + [(0.0, top + 0.004)] + [(y, z) for y, z in half[::-1]]
        secs.append([(x, y, z) for y, z in sec])
    v, f = util.loft(secs)
    fm = []
    for u in range(len(xs) - 1):
        for k in range(12):
            fm.append("leather_dark" if 4 <= k <= 7 else "leather_light")
    console = _MB().add((v, f), fm).build(PREFIX + "Console", col, angle=None, recalc=False)
    util.subsurf(console, 2)

    # ---------------- polished blade + inlays + screws + the line rising up the bulkhead
    L = _BLADE_LIFT
    mb = _MB()
    AP = "alu_polished"
    bx = np.concatenate([np.linspace(-0.530, 0.0, 12), np.linspace(0.02, 0.80, 110), np.linspace(0.83, 1.215, 12)])
    mb.add(_console_strip(0, 0, _BLADE_HW, -0.004, L, n=bx), AP)
    mb.add(_console_strip(0.345, 0.478, 0.031, L - 0.001, L + 0.0012, n=14, chamfer=0.0005), "plastic_gloss")
    mb.add(_console_strip(0.218, 0.306, 0.024, L - 0.001, L + 0.0012, n=10, chamfer=0.0005), "plastic_gloss")
    for x, y in ((0.515, 0.027), (0.610, 0.036), (0.705, 0.026), (0.325, 0.037), (0.185, 0.022)):
        for sy in (1, -1):
            mb.add(_cyl(0.0026, 0, 0.0012, 10, bev=0.0004), "steel_dark", _console_frame(x, sy * y, lift=L))
    for x in (0.08, -0.05, -0.30):
        mb.add(_cyl(0.0026, 0, 0.0012, 10, bev=0.0004), "steel_dark", _console_frame(x, 0, lift=L))
    xw = C["x_firewall"] + 0.031
    path = [(xw, 0.0, z) for z in np.linspace(0.452, 0.985, 12)]
    mb.add(_sweep_n(_flat_bar(0.020, 0.004, 0.0012), path, (1.0, 0.0, 0.0), closed=False), AP)
    blade = mb.build(PREFIX + "Console_Blade", col, angle=30)
    _child(blade, console)

    # ---------------- the two big rotary dials (own objects: local +Z is the dial axis)
    dials = []
    for x, tag in zip(_DIAL_X, ("Upper", "Lower")):
        d = _rotary_dial(1.0).build(PREFIX + "Console_Dial_" + tag, col, angle=32,
                                    matrix=_console_frame(x, 0, lift=L))
        _child(d, console)
        dials.append(d)

    # ---------------- start knob (glows), toggle field, gear selector
    kb = _rotary_dial(0.52, glow=True)
    kb.add(_ring(0.0205, 0.0222, 0.0, 0.0034, 40), "emit_screen")
    knob = kb.build(PREFIX + "Console_StartKnob", col, angle=32, matrix=_console_frame(_KNOB_X, 0, lift=L))
    _child(knob, console)

    sw = _MB()
    Lt = L + 0.0012
    for r, x in enumerate(_TOGGLE_X):
        for c, y in enumerate((0.0175, -0.0175)):
            M = _console_frame(x, y, lift=Lt)
            sw.add(_knurl_ring(0.0064, 0.0025, 0, 0.0046, n=14, depth=0.0005, bev=0.0006), "alu_knurled", M)
            tilt = math.radians(16 if (r + c) % 2 == 0 else -16)
            lever = _lathe([(0, 0.002), (0.0029, 0.002), (0.0024, 0.0165), (0.0039, 0.0185), (0.0043, 0.0215),
                            (0.0032, 0.0240), (0, 0.0246)], 12)
            sw.add(lever, "alu_polished", M @ _R('y', tilt))
            sw.add(_cyl(0.0017, 0, 0.0009, 10), "emit_screen", M @ _T(0.0, math.copysign(0.0105, y), 0))
        sw.add(_xf(_box(0.014, 0.0045, 0.0022, 0.0006), _T(0, 0, 0.0011)), "alu_brushed",
               _console_frame(x - 0.015, 0, lift=Lt))
    switches = sw.build(PREFIX + "Console_Switches", col, angle=35)
    _child(switches, console)

    sl = _MB()
    gate = np.array([(p[1], p[0]) for p in _stadium(0.034, 0.078, seg=8, side_seg=2)])[::-1]
    slot = np.array([(p[1], p[0]) for p in _stadium(0.012, 0.050, seg=6, side_seg=2)])[::-1]
    sl.add(_prism(gate, 0.0, 0.0030, bev=0.0008), "alu_polished")
    sl.add(_prism(slot, 0.0025, 0.0034), "void_black")
    sl.add(_rod((0.010, 0, 0.002), (0.002, 0, 0.032), 0.0042, 12), "alu_polished")
    Mk = _frame((0.002, 0, 0.030), (-0.25, 0, 1.0), (1, 0, 0))
    sl.add(_knurl_ring(0.0135, 0.004, 0.0, 0.019, n=30, depth=0.0008, bev=0.001), "alu_knurled", Mk)
    sl.add(_lathe([(0.0128, 0.019), (0.0115, 0.0225), (0.0070, 0.0248), (0, 0.0255)], 24), "alu_polished", Mk)
    sl.add(_cyl(0.0045, 0.0245, 0.0262, 12), "emit_screen", Mk)
    selector = sl.build(PREFIX + "Console_Selector", col, angle=32, matrix=_console_frame(_SELECTOR_X, 0, lift=Lt))
    _child(selector, console)

    # ---------------- ambient strips down both sides of the spine
    amb = []
    for side, tag in ((1, "L"), (-1, "R")):
        path, nr = [], []
        for x in np.linspace(-0.32, 0.665, 48):
            M = _console_frame(x)
            path.append(M[:3, 3] + M[:3, 1] * (side * 0.0775) + M[:3, 2] * (-0.0022))
            nr.append(M[:3, 2])
        st = _obj(PREFIX + "Ambient_Console_" + tag, _sweep_n(_flat_bar(0.0045, 0.0032, 0.001), path, nr, closed=False),
                  col, "emit_interior", recalc=True)
        _child(st, console)
        amb.append(st)
    return console, dials, amb


# ====================================================================== STEERING + CLUSTER
def _steering_matrix():
    c = np.array(C["steering_centre"], float)
    a = math.radians(C["steering_rake_deg"])
    zl = (-math.cos(a), 0.0, math.sin(a))      # along the column, towards the driver
    yl = (math.sin(a), 0.0, math.cos(a))       # 12 o'clock
    return _M(c, (0.0, -1.0, 0.0), yl, zl)     # +X = 3 o'clock for the driver


_RIM_A, _RIM_BT, _RIM_BB = 0.165, 0.163, 0.155   # centre-line half-width, top / bottom half-height


def _rim_path(n=132):
    """Rounded-square rim centre line (flatter bottom), evenly spaced, CCW from 3 o'clock."""
    th = np.linspace(0, 2 * PI, 4000, endpoint=False)
    c, s = np.cos(th), np.sin(th)
    top = s >= 0
    ex = np.where(top, 2 / 2.9, 2 / 3.7)
    b = np.where(top, _RIM_BT, _RIM_BB)
    pts = np.stack([_RIM_A * np.sign(c) * np.abs(c) ** ex, b * np.sign(s) * np.abs(s) ** ex], 1)
    return util.resample_polyline(pts, n, closed=True)


def _build_rim(col):
    mb = _MB()
    P = _rim_path()
    n, seg = len(P), 14
    secs, ang = [], []
    for i in range(n):
        t = _unit(P[(i + 1) % n] - P[i - 1])
        nr = np.array([t[1], -t[0]])
        a = math.degrees(math.atan2(P[i][1], P[i][0]))
        ang.append(a)
        grip = 1.0 + 0.16 * math.exp(-((min(abs(a), 180 - abs(a)) - 6) / 15.0) ** 2)
        ra, rb = 0.0150 * grip, 0.0172
        secs.append([(P[i][0] + nr[0] * ra * math.cos(2 * PI * k / seg),
                      P[i][1] + nr[1] * ra * math.cos(2 * PI * k / seg),
                      rb * math.sin(2 * PI * k / seg)) for k in range(seg)])
    fm = []
    for i in range(n):
        a0, a1 = ang[i], ang[(i + 1) % n]
        a = a0 if abs(a1 - a0) > 180 else 0.5 * (a0 + a1)
        if abs(a + 90) < 5.0:
            m = "alu_polished"
        elif abs(a - 90) < 2.3:
            m = "leather_light"
        elif 31 < a < 149:
            m = "leather_dark"
        else:
            m = "leather_light"
        fm += [m] * seg
    mb.add(util.loft(secs, closed_v=True, closed_u=True), fm)

    # spokes: leave the rim, run straight back, then turn inwards behind the fixed hub
    side = [(0.154, -0.002), (0.147, -0.020), (0.142, -0.045), (0.132, -0.068), (0.108, -0.084),
            (0.075, -0.091), (0.046, -0.092)]
    path = util.catmull_rom([(x, -0.012, z) for x, z in side], samples_per_seg=6)
    m_ = len(path)
    prof = util.rounded_rect(0.034, 0.011, 0.004, seg=3)
    sp = _sweep_n(prof, path, (0.0, 1.0, 0.0), closed=False)
    fm = []
    for u in range(m_ - 1):
        fm += ["leather_light" if u < 7 else "carbon_gloss"] * len(prof)
    fm += ["carbon_gloss"] * 2
    mb.add(sp, fm)
    mb.add(sp, fm, _S(-1, 1, 1))
    low = [(-0.143, -0.002), (-0.138, -0.020), (-0.133, -0.045), (-0.124, -0.068), (-0.102, -0.084),
           (-0.072, -0.091), (-0.046, -0.092)]
    for sx in (1, -1):
        path = util.catmull_rom([(sx * 0.0115, y, z) for y, z in low], samples_per_seg=6)
        mb.add(_sweep_n(util.rounded_rect(0.0095, 0.0085, 0.003, seg=2), path, (1.0, 0.0, 0.0), closed=False),
               "carbon_gloss")
    mb.add(_xf(_box(0.036, 0.012, 0.018, 0.003), _T(0, -0.1415, -0.006)), "alu_polished")
    mb.add(_ring(0.034, 0.052, -0.105, -0.080, 40, bev=0.002), "alu_dark")
    return mb.build(PREFIX + "SteeringRim", col, angle=40)


def _build_hub(col):
    """Everything that stays still: column, hub pad with the plain oval, pods, buttons, stalks."""
    mb = _MB()
    AP = "alu_polished"
    HY = -0.035
    Mh = _T(0, HY, 0)
    mb.add(_cyl(0.027, -0.262, -0.045, 32), "alu_dark")
    mb.add(_lathe([(0, -0.068), (0.034, -0.068), (0.046, -0.050), (0.0535, -0.022), (0.0555, -0.009),
                   (0.0535, -0.0045), (0.0505, -0.0040), (0.0505, -0.008), (0, -0.008)], 56), AP, Mh)
    mb.add(_lathe([(0.0505, -0.0075), (0.0505, -0.0035), (0.0490, -0.0012), (0.0440, 0.0010),
                   (0.0320, 0.0030), (0.0160, 0.0040), (0, 0.0043)], 56), "leather_light", Mh)
    mb.add(_prism(_ellipse(0.0265, 0.0170, 44), 0.0022, 0.0058, bev=0.0009), AP, Mh)
    mb.add(_prism(_ellipse(0.0225, 0.0130, 40), 0.0050, 0.0064, bev=0.0003), "alu_brushed", Mh)
    for sx in (1, -1):
        Mp = _T(sx * 0.108, -0.032, -0.016)
        mb.add(_prism(util.rounded_rect(0.038, 0.054, 0.010, 4), -0.010, 0.008, bev=0.002), AP, Mp)
        mb.add(_prism(util.rounded_rect(0.029, 0.045, 0.007, 4), 0.0075, 0.0088), "plastic_gloss", Mp)
        mb.add(_xf(_knurl_ring(0.0052, 0.001, -0.008, 0.008, n=14, depth=0.0005, bev=0.0006), _R('y', PI / 2)),
               "alu_knurled", Mp @ _T(0, 0.010, 0.0098))
        for bx in (-0.0068, 0.0068):
            mb.add(_cyl(0.0047, 0.0085, 0.0108, 14, bev=0.0005), AP, Mp @ _T(bx, -0.010, 0))
        mb.add(_bar((sx * 0.048, -0.034, -0.024), (sx * 0.094, -0.032, -0.020), 0.016, 0.010, up=(0, 0, 1),
                    bev=0.002), AP)
        # round mode buttons below the pods
        Mb = _T(sx * 0.078, -0.086, -0.012)
        mb.add(_knurl_ring(0.0125, 0.004, -0.008, 0.0, n=26, depth=0.0006, bev=0.0008), "alu_knurled", Mb)
        mb.add(_cyl(0.0098, -0.004, 0.0012, 20, bev=0.0005), "plastic_gloss", Mb)
        mb.add(_rod((sx * 0.040, -0.060, -0.032), (sx * 0.078, -0.086, -0.016), 0.005, 10), "alu_dark")
        # column stalks
        p0, p1 = np.array([sx * 0.050, 0.004, -0.152]), np.array([sx * 0.128, 0.012, -0.120])
        mb.add(_rod(p0, p1, 0.0042, 10), AP)
        mb.add(_rod(p1 - (p1 - p0) * 0.30, p1, 0.0068, 14), "alu_knurled")
    # carbon shroud where the column leaves the dash, with a leather boot
    mb.add(_lathe([(0.030, -0.117), (0.049, -0.117), (0.0545, -0.126), (0.0545, -0.200), (0.058, -0.275),
                   (0.030, -0.275)], 40, closed=True), "carbon_gloss")
    mb.add(_lathe([(0.0545, -0.146), (0.0640, -0.152), (0.0680, -0.170), (0.0680, -0.215), (0.0545, -0.215)],
                  40, closed=True), "leather_dark")
    return mb.build(PREFIX + "SteeringHub", col, angle=38)


_CLUSTER_DIALS = [
    # tag, x, y, radius, front z, depth, ticks, needle position (0..1 of the 270 deg scale)
    ("C", 0.0, 0.076, 0.0550, -0.010, 0.046, 54, 0.30),
    ("L", -0.0880, 0.032, 0.0375, -0.015, 0.036, 30, 0.62),
    ("R", 0.0880, 0.032, 0.0375, -0.015, 0.036, 30, 0.42),
]
_MOVEMENT_MAIN = [  # x, y, tip radius, teeth, z, material, spokes
    (0.0, 0.0, 0.0200, 64, -0.0300, "brass", 5),
    (0.0185, -0.0125, 0.0125, 40, -0.0265, "alu_polished", 4),
    (-0.0190, -0.0110, 0.0105, 34, -0.0340, "brass", 4),
    (-0.0070, 0.0215, 0.0085, 28, -0.0270, "alu_polished", 3),
    (0.0205, 0.0125, 0.0065, 20, -0.0235, "brass", 0),
]
_MOVEMENT_SIDE = [
    (0.0, 0.0, 0.0125, 40, -0.0270, "brass", 4),
    (0.0115, -0.0085, 0.0075, 24, -0.0235, "alu_polished", 3),
    (-0.0105, 0.0095, 0.0062, 20, -0.0245, "alu_polished", 0),
    (-0.0090, -0.0115, 0.0055, 18, -0.0300, "brass", 0),
]


def _cluster_dial(mb, gl, x, y, R, zf, D, nt, mirror=False):
    """One skeleton dial: knurled bezel, chapter ring with ticks, open-worked gear train."""
    M = _T(x, y, zf)
    AP = "alu_polished"
    brass = _brass()
    mb.add(_ring(R - 0.0035, R, -D, -0.006, 64, bev=0.0006), AP, M)
    mb.add(_cyl(R - 0.003, -D, -D + 0.0015, 48), "steel_dark", M)
    mb.add(_ring(R - 0.002, R + 0.0065, -D - 0.0005, -D + 0.0028, 64, bev=0.0008), AP, M)
    mb.add(_knurl_ring(R + 0.0035, R - 0.0045, -0.0075, 0.0, n=int(R * 1700), depth=0.0007, bev=0.0012),
           "alu_knurled", M)
    mb.add(_lathe([(R - 0.0045, -0.0015), (R - 0.0045, -0.0075), (0.93 * R, -0.0128), (0.93 * R, -0.0105)],
                  64, closed=True), AP, M)
    mb.add(_ring(0.70 * R, 0.93 * R, -0.0138, -0.0122, 64), "dial_black", M)
    mb.add(_ring(0.665 * R, 0.70 * R, -0.0142, -0.0117, 64), "emit_dial", M)
    major = 6 if nt > 40 else 5
    for k in range(nt + 1):
        a = math.radians(225.0 - 270.0 * k / nt)
        big = k % major == 0
        ln, w = (0.17 * R, 0.0012) if big else (0.09 * R, 0.0006)
        mb.add(_box(ln, w, 0.0006), "emit_dial" if big else "dial_face",
               M @ _R('z', a) @ _T(0.915 * R - ln / 2, 0, -0.0120))
    # skeleton ring + three-arm bridge carrying the centre jewel
    ro = 0.665 * R
    mb.add(_ring(ro - 0.0045, ro + 0.002, -0.0240, -0.0225, 48), "alu_brushed", M)
    zb = -0.0190
    for a in (90, 210, 330):
        a = math.radians(a + (0 if not mirror else 180))
        mb.add(_bar((0, 0, zb), (ro * math.cos(a), ro * math.sin(a), zb), 0.0042, 0.0014, bev=0.0004), AP, M)
        mb.add(_cyl(0.0015, zb + 0.0005, zb + 0.0016, 8), "steel_dark",
               M @ _T(0.86 * ro * math.cos(a), 0.86 * ro * math.sin(a), 0))
    mb.add(_cyl(0.0056, zb - 0.0012, zb + 0.0022, 20, bev=0.0006), AP, M)
    mb.add(_cyl(0.0017, -D + 0.001, -0.0078, 10), AP, M)
    # gear train
    for gx, gy, rt, nteeth, gz, gm, spk in (_MOVEMENT_MAIN if R > 0.05 else _MOVEMENT_SIDE):
        if mirror:
            gx = -gx
        Mg = M @ _T(gx, gy, gz)
        mat = brass if gm == "brass" else gm
        if spk:
            mb.add(_gear(nteeth, rt, 0.0011, 0.0011, r_in=rt * 0.70, hub=rt * 0.24, spokes=spk), mat, Mg)
        else:
            mb.add(_gear(nteeth, rt, 0.0010, 0.0012), mat, Mg)
        mb.add(_gear(10, 0.0026, 0.0009, 0.0036), "steel_dark", Mg @ _T(0, 0, 0.0028))
        mb.add(_cyl(0.0009, -0.006, 0.0085, 8), "steel_dark", Mg)
        if gx or gy:
            # cock (small bridge) from the skeleton ring holding a jewelled bearing
            d = _unit((gx, gy, 0))
            zc = gz + 0.0080
            p1 = d * (ro - 0.001)
            mb.add(_bar((gx, gy, zc), (p1[0], p1[1], zc), 0.0038, 0.0012, bev=0.0003), AP, M)
            Mj = M @ _T(gx, gy, zc)
            mb.add(_ring(0.0015, 0.0027, 0.0, 0.0014, 14), brass, Mj)
            mb.add(_lathe([(0.0015, 0.0006), (0.0012, 0.0018), (0, 0.0021)], 10), "badge_red", Mj)
            mb.add(_cyl(0.0013, 0.0005, 0.0015, 8), "steel_dark",
                   M @ _T(p1[0] - d[0] * 0.003, p1[1] - d[1] * 0.003, zc))
    mb.add(_lathe([(0.0016, 0.0020), (0.0013, 0.0034), (0, 0.0037)], 10), "badge_red", M @ _T(0, 0, zb))
    # crystal
    gl.add(_lathe([(0, -0.0052), (R - 0.0048, -0.0052), (R - 0.0048, -0.0030), (0.6 * R, -0.0019),
                   (0, -0.0014)], 48), "glass_clear", M)


def _build_cluster(col):
    mb, gl = _MB(), _MB()
    needles = []
    for tag, x, y, R, zf, D, nt, pos in _CLUSTER_DIALS:
        _cluster_dial(mb, gl, x, y, R, zf, D, nt, mirror=(tag == "L"))
        nb = _MB()
        ol = [(-0.24 * R, -0.0011), (0.0, -0.0015), (0.86 * R, -0.00035), (0.86 * R, 0.00035),
              (0.0, 0.0015), (-0.24 * R, 0.0011)]
        nb.add(_prism(ol, -0.0004, 0.0004), "needle_red")
        nb.add(_cyl(0.0027, -0.0005, 0.0005, 12), "needle_red", _T(-0.24 * R, 0, 0))
        nb.add(_cyl(0.0052, -0.0008, 0.0022, 20, bev=0.0006), "alu_polished")
        nd = nb.build(PREFIX + "Cluster_Needle_" + tag, col, angle=35)
        needles.append((nd, _T(x, y, zf - 0.0088) @ _R('z', math.radians(225.0 - 270.0 * pos))))
    # carrier: bridges from the fixed hub up to the three cases
    AP = "alu_polished"
    mb.add(_bar((0, 0.026, -0.046), (0, 0.004, -0.046), 0.018, 0.007, bev=0.0015), AP)
    for sx in (1, -1):
        mb.add(_bar((sx * 0.066, 0.010, -0.044), (sx * 0.034, -0.012, -0.046), 0.011, 0.006, bev=0.0015), AP)
        mb.add(_bar((sx * 0.052, 0.058, -0.046), (sx * 0.064, 0.050, -0.046), 0.014, 0.005, bev=0.001), AP)
    cluster = mb.build(PREFIX + "Cluster", col, angle=35)
    glass = gl.build(PREFIX + "Cluster_Glass", col, angle=35)
    return cluster, glass, needles


def _build_steering(col):
    from mathutils import Matrix
    pivot = util.empty(PREFIX + "SteeringPivot", (0, 0, 0), collection=col, size=0.12, kind='ARROWS')
    pivot.matrix_world = Matrix(_steering_matrix().tolist())
    rim = _build_rim(col)
    hub = _build_hub(col)
    cluster, glass, needles = _build_cluster(col)
    for o in (rim, hub, cluster):
        o.parent = pivot                       # local = pivot frame (identity local transform)
    glass.parent = cluster
    out = []
    for nd, Ml in needles:
        nd.parent = cluster
        nd.matrix_basis = Matrix(Ml.tolist())
        out.append(nd)
    return pivot, rim, hub, cluster, out


# ====================================================================== PEDALS, MIRROR, FOOTWELL LIGHT
def _build_pedals(col):
    mb = _MB()

    def pedal_frame(x, y, z, deg):
        a = math.radians(deg)
        return _M((x, y, z), (0, -1, 0), (math.cos(a), 0, math.sin(a)), (-math.sin(a), 0, math.cos(a)))

    def pad(M, w, h, bars):
        mb.add(_prism(util.rounded_rect(w, h, min(w, h) * 0.22, 4), -0.004, 0.004, bev=0.0015), "alu_brushed", M)
        for k in range(bars):
            yy = -h / 2 + h * (k + 0.5) / bars
            mb.add(_xf(_box(w * 0.72, 0.006, 0.0022, 0.0008), _T(0, yy, 0.0045)), "rubber_seal", M)

    y0 = C["seat_y"]
    # accelerator (floor hinged, driver's right = lower y)
    Ma = pedal_frame(1.105, y0 - 0.112, 0.268, 60)
    pad(Ma, 0.052, 0.158, 6)
    mb.add(_xf(_cyl(0.008, -0.03, 0.03, 12), _R('x', PI / 2)), "alu_dark", _T(1.068, y0 - 0.112, 0.186))
    mb.add(_xf(_box(0.05, 0.07, 0.016, 0.003), _T(1.082, y0 - 0.112, 0.176)), "alu_dark")
    # brake (hanging)
    Mbk = pedal_frame(1.092, y0 + 0.010, 0.318, 66)
    pad(Mbk, 0.100, 0.064, 3)
    mb.add(_bar((1.100, y0 + 0.010, 0.322), (1.205, y0 + 0.010, 0.545), 0.014, 0.022, up=(1, 0, 0), bev=0.003),
           "alu_dark")
    # footrest
    Mf = pedal_frame(1.128, y0 + 0.118, 0.292, 56)
    pad(Mf, 0.070, 0.200, 7)
    for dz in (-0.06, 0.06):
        p = Mf[:3, 3] + Mf[:3, 1] * dz
        mb.add(_bar(p - Mf[:3, 2] * 0.004, p - Mf[:3, 2] * 0.075, 0.03, 0.012, up=(0, 1, 0), bev=0.002), "alu_dark")
    return mb.build(PREFIX + "Pedals", col, angle=35)


def _build_mirror(col):
    mb = _MB()
    c = np.array([0.715, 0.0, 1.054])
    M = _frame(c, (-1.0, 0.12, -0.10), (0, 1, 0))
    mb.add(_prism(util.superellipse(0.118, 0.031, 2.6, 56), -0.017, 0.0, bev=0.004), "plastic_gloss", M)
    mb.add(_prism(util.superellipse(0.1135, 0.0268, 2.6, 56), -0.001, 0.0012, bev=0.0004), "chrome", M)
    p0 = c + M[:3, 2] * (-0.014) + np.array([0, 0, 0.012])
    p1 = np.array([0.676, 0.0, 1.094])
    mb.add(_rod(p0, p1, 0.0075, 14, r1=0.0065), "plastic_black")
    mb.add(_xf(_cyl(0.013, -0.004, 0.003, 20, bev=0.002), _frame(p1, (-0.37, 0, 0.93), (0, 1, 0))), "plastic_black")
    return mb.build(PREFIX + "Mirror", col, angle=40)


def _build_footwell_ambient(col, tub):
    out = []
    for side, tag in ((1, "L"), (-1, "R")):
        path = []
        for x in np.linspace(0.74, 1.10, 16):
            z = 0.30
            y = _footwell_half_width(x) + 0.2727 * (z - 0.16) - 0.003 - 0.016
            path.append((x, side * y, z))
        st = _obj(PREFIX + "Ambient_Footwell_" + tag,
                  _sweep_n(_flat_bar(0.008, 0.003, 0.001), path, (0.0, -side, 0.27), closed=False),
                  col, "emit_interior", recalc=True)
        _child(st, tub)
        out.append(st)
    return out


# ====================================================================== BUILD
def build(collection=None):
    """Build the whole cabin.  See the module docstring for the returned dict."""
    if collection is None:
        col = util.get_collection(spec.COLLECTIONS["interior"])
    elif isinstance(collection, str):
        col = util.get_collection(collection)
    else:
        col = collection
    out = {}
    root = util.empty(PREFIX + "Root", (0, 0, 0), collection=col, size=0.3)
    out["root"] = root
    tub, mats = _build_tub(col)
    pedals = _build_pedals(col)
    _child(pedals, tub)
    out.update(tub=tub, floor_mats=mats, pedals=pedals)
    out["seat_L"] = _build_seat(col, "L", +C["seat_y"])
    out["seat_R"] = _build_seat(col, "R", -C["seat_y"])
    dash, wings, amb_dash = _build_dash(col)
    console, dials, amb_con = _build_console(col)
    pivot, rim, hub, cluster, needles = _build_steering(col)
    pivot.parent = dash                         # dash sits at the origin: local == world
    mirror = _build_mirror(col)
    amb_foot = _build_footwell_ambient(col, tub)
    out.update(dash=dash, dash_wings=wings, console=console, console_dials=dials,
               steering_pivot=pivot, steering_rim=rim, steering_hub=hub, cluster=cluster,
               needles=needles, mirror=mirror, ambient=amb_dash + amb_con + amb_foot)
    for k in ("tub", "seat_L", "seat_R", "dash", "console", "mirror"):
        out[k].parent = root
    bpy.context.view_layer.update()
    return out
