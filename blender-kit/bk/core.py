"""bk.core -- geometry kit for building scenes procedurally in Blender (bpy 5.x).

Everything is built in metres, Z up.  The central piece is ``MB`` (mesh
builder): parts are appended as raw arrays (verts / faces / UVs / material
slots) and turned into one Blender object by ``finish()``.  Every primitive
writes real-world-scale UVs (1 UV unit = 1 m) with U along the longest
dimension, so wood grain, planks and tiles line up without unwrapping.
"""
import math
import random
import warnings

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

warnings.simplefilter("ignore", DeprecationWarning)

PI = math.pi
TAU = 2 * math.pi
_rng = random.Random(7)


def rad(d):
    return d * PI / 180.0


# --------------------------------------------------------------------------
# scene / collections
# --------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    return sc


_CUR = [None]


def coll(name, parent=None, activate=True):
    """Get or create a collection; by default it becomes the current target."""
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    if activate:
        _CUR[0] = c
    return c


def cur_coll():
    return _CUR[0] or bpy.context.scene.collection


def link(o, c=None):
    (c or cur_coll()).objects.link(o)
    return o


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(deg, axis='Z'):
    return Matrix.Rotation(rad(deg), 4, axis)


def S(x=1.0, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return Matrix.Diagonal((x, y, z, 1.0))


def TR(x=0.0, y=0.0, z=0.0, rz=0.0):
    """Translate then rotate about Z (degrees): the usual 'place furniture' matrix."""
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rad(rz), 4, 'Z')


def look_rot(direction, up=(0, 0, 1)):
    """Rotation matrix whose local Z points along *direction*."""
    d = Vector(direction).normalized()
    u = Vector(up)
    if abs(d.dot(u)) > 0.999:
        u = Vector((1, 0, 0))
    x = u.cross(d).normalized()
    y = d.cross(x)
    m = Matrix((x, y, d)).transposed()
    return m.to_4x4()


def seg_matrix(a, b):
    """Matrix placing a unit-Z primitive from point a to point b (returns M, length)."""
    a = Vector(a)
    b = Vector(b)
    d = b - a
    L = d.length
    return Matrix.Translation((a + b) / 2) @ look_rot(d), L


# --------------------------------------------------------------------------
# mesh builder
# --------------------------------------------------------------------------
class MB:
    def __init__(self, name="obj"):
        self.name = name
        self.V = []          # list of (n,3) arrays
        self.F = []          # list of tuples (global indices)
        self.UV = []         # per-loop uv tuples
        self.MI = []         # per-face material index
        self.SM = []         # per-face smooth flag
        self.mats = []
        self.nv = 0
        self.xf = [Matrix.Identity(4)]   # transform stack

    # ---- transform stack -------------------------------------------------
    def push(self, m):
        self.xf.append(self.xf[-1] @ m)
        return self

    def pop(self):
        self.xf.pop()
        return self

    def _m(self, m):
        return self.xf[-1] @ m if m is not None else self.xf[-1]

    # ---- low level -------------------------------------------------------
    def slot(self, mat):
        if mat is None:
            return 0 if self.mats else self._ensure_default()
        for i, m in enumerate(self.mats):
            if m is mat:
                return i
        self.mats.append(mat)
        return len(self.mats) - 1

    def _ensure_default(self):
        self.mats.append(None)
        return 0

    def raw(self, verts, faces, uvs, mat=None, smooth=True, m=None):
        """verts: (n,3) array-like in local space; faces: index tuples; uvs: per loop."""
        v = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
        M = self._m(m)
        A = np.array(M)
        v = v @ A[:3, :3].T + A[:3, 3]
        flip = M.to_3x3().determinant() < 0
        mi = self.slot(mat)
        base = self.nv
        self.V.append(v)
        self.nv += len(v)
        k = 0
        for f in faces:
            n = len(f)
            if flip:
                self.F.append(tuple(base + i for i in reversed(f)))
                self.UV.extend(reversed(uvs[k:k + n]))
            else:
                self.F.append(tuple(base + i for i in f))
                self.UV.extend(uvs[k:k + n])
            k += n
            self.MI.append(mi)
            self.SM.append(smooth)
        return self

    def from_bm(self, bm, mat=None, smooth=True, m=None, uv=None, dims=None, uvscale=1.0):
        """Append a temp bmesh.  uv: None -> triplanar box projection in local space."""
        bm.normal_update()
        bm.verts.index_update()
        verts = [v.co[:] for v in bm.verts]
        faces = []
        uvs = []
        if dims is None:
            xs = np.array(verts)
            dims = tuple(xs.max(0) - xs.min(0)) if len(xs) else (1, 1, 1)
        order = sorted(range(3), key=lambda i: -dims[i])
        ox, oy = _rng.uniform(0, 7), _rng.uniform(0, 7)
        lay = bm.loops.layers.uv.active if uv == 'layer' else None
        for f in bm.faces:
            faces.append(tuple(v.index for v in f.verts))
            if lay is not None:
                for l in f.loops:
                    uvs.append(tuple(l[lay].uv))
                continue
            n = f.normal
            a = max(range(3), key=lambda i: abs(n[i]))
            ax = [i for i in order if i != a]
            for v in f.verts:
                c = v.co
                uvs.append((c[ax[0]] * uvscale + ox, c[ax[1]] * uvscale + oy))
        self.raw(verts, faces, uvs, mat, smooth, m)
        bm.free()
        return self

    # ---- primitives ------------------------------------------------------
    def box(self, size, loc=(0, 0, 0), mat=None, bevel=0.0, segs=2, m=None, rz=None, smooth=None,
            base=False):
        """Box of *size* centred at *loc* (base=True: loc is the centre of the bottom face)."""
        sx, sy, sz = size
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= sx
            v.co.y *= sy
            v.co.z *= sz
        if bevel > 0:
            b = min(bevel, 0.45 * min(sx, sy, sz))
            if b > 1e-5:
                bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, offset_type='OFFSET', segments=segs,
                                profile=0.5, affect='EDGES', clamp_overlap=False)
        M = Matrix.Translation((loc[0], loc[1], loc[2] + (sz / 2 if base else 0)))
        if rz:
            M = M @ Matrix.Rotation(rad(rz), 4, 'Z')
        if m is not None:
            M = m @ M
        if smooth is None:
            smooth = bevel > 0
        return self.from_bm(bm, mat, smooth, M, dims=(sx, sy, sz))

    def bx(self, x0, y0, z0, x1, y1, z1, mat=None, bevel=0.0, segs=2, m=None):
        """Box from min/max corners."""
        return self.box((abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)),
                        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), mat, bevel, segs, m)

    def cyl(self, r, h, loc=(0, 0, 0), mat=None, segs=32, r2=None, bevel=0.0, m=None, axis='Z',
            base=False, caps=True, bsegs=2):
        """Cylinder / cone along *axis* centred at loc (base=True: loc at bottom centre)."""
        r2 = r if r2 is None else r2
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segs, radius1=r, radius2=r2,
                              depth=h)
        if bevel > 0 and caps:
            bm.normal_update()
            ed = [e for e in bm.edges if len(e.link_faces) == 2 and
                  abs(e.link_faces[0].normal.dot(e.link_faces[1].normal)) < 0.5]
            bmesh.ops.bevel(bm, geom=ed, offset=min(bevel, 0.45 * min(r, r2, h)), offset_type='OFFSET',
                            segments=bsegs, profile=0.5, affect='EDGES', clamp_overlap=False)
        lay = bm.loops.layers.uv.new("uv")
        bm.normal_update()
        ra = max(r, r2)
        for f in bm.faces:
            if abs(f.normal.z) > 0.9:
                for l in f.loops:
                    l[lay].uv = (l.vert.co.x, l.vert.co.y)
            else:
                ang = [math.atan2(l.vert.co.y, l.vert.co.x) for l in f.loops]
                if max(ang) - min(ang) > PI:
                    ang = [a + TAU if a < 0 else a for a in ang]
                for l, a in zip(f.loops, ang):
                    l[lay].uv = (l.vert.co.z, a * ra)
        M = Matrix.Translation((loc[0], loc[1], loc[2]))
        if axis == 'X':
            M = M @ Matrix.Rotation(PI / 2, 4, 'Y')
        elif axis == 'Y':
            M = M @ Matrix.Rotation(-PI / 2, 4, 'X')
        if base:
            M = M @ Matrix.Translation((0, 0, h / 2))
        if m is not None:
            M = m @ M
        return self.from_bm(bm, mat, True, M, uv='layer')

    def rod(self, a, b, r, mat=None, segs=16, r2=None, caps=True):
        """Cylinder between two points."""
        M, L = seg_matrix(a, b)
        return self.cyl(r, L, (0, 0, 0), mat, segs, r2, m=M, caps=caps)

    def sphere(self, r, loc=(0, 0, 0), mat=None, segs=32, rings=16, scale=(1, 1, 1), m=None):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
        M = Matrix.Translation(loc) @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1))
        if m is not None:
            M = m @ M
        return self.from_bm(bm, mat, True, M)

    def lathe(self, profile, mat=None, segs=48, m=None, loc=(0, 0, 0), angle=TAU, smooth=True, close=False):
        """Revolve profile [(r, z), ...] about Z.  r == 0 points collapse to the axis."""
        P = [(float(r), float(z)) for r, z in profile]
        if close:
            P = P + [P[0]]
        n = len(P)
        full = abs(angle - TAU) < 1e-6
        ns = segs if full else segs + 1
        ang = np.linspace(0, angle, segs + 1)[:ns]
        verts = []
        idx = []
        for (r, z) in P:
            if r < 1e-7:
                idx.append([len(verts)] * ns)
                verts.append((0, 0, z))
            else:
                row = []
                for a in ang:
                    row.append(len(verts))
                    verts.append((r * math.cos(a), r * math.sin(a), z))
                idx.append(row)
        # arc length along profile for V
        sl = [0.0]
        for i in range(1, n):
            sl.append(sl[-1] + math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]))
        faces = []
        uvs = []
        rmax = max(p[0] for p in P) or 1.0
        nseg = segs if full else segs
        for i in range(n - 1):
            for j in range(nseg):
                j2 = (j + 1) % ns if full else j + 1
                a, b, c, d = idx[i][j], idx[i][j2], idx[i + 1][j2], idx[i + 1][j]
                u0, u1 = j / segs * angle * rmax, (j + 1) / segs * angle * rmax
                q = [(a, (u0, sl[i])), (b, (u1, sl[i])), (c, (u1, sl[i + 1])), (d, (u0, sl[i + 1]))]
                seen = []
                for vi, uvv in q:
                    if not seen or vi != seen[-1][0]:
                        seen.append((vi, uvv))
                if len(seen) > 1 and seen[0][0] == seen[-1][0]:
                    seen.pop()
                if len(seen) >= 3:
                    faces.append(tuple(s[0] for s in seen))
                    uvs.extend(s[1] for s in seen)
        M = Matrix.Translation(loc)
        if m is not None:
            M = m @ M
        # profile is assumed to run so that outward normals are right for a
        # counter-clockwise outline in the (r, z) half-plane going bottom -> top.
        return self.raw(verts, faces, uvs, mat, smooth, M)

    def prism(self, poly, z0, z1, mat=None, m=None, mat_side=None, mat_bottom=None, top=True, bottom=True,
              uvscale=1.0, side=True, side_fn=None):
        """Extrude a 2D polygon (shapely Polygon/MultiPolygon or list of (x, y)) from z0 to z1."""
        polys = _as_polys(poly)
        mat_side = mat if mat_side is None else mat_side
        mat_bottom = mat if mat_bottom is None else mat_bottom
        for outer, holes in polys:
            rings = [outer] + holes
            flat = [p for r in rings for p in r]
            n = len(flat)
            if n < 3:
                continue
            tris = tessellate_polygon([[Vector((x, y, 0)) for x, y in r] for r in rings])
            vb = [(x, y, z0) for x, y in flat]
            vt = [(x, y, z1) for x, y in flat]
            if top:
                fs, uv = [], []
                for a, b, c in tris:
                    # tessellate_polygon winding is not guaranteed: fix to +Z
                    ax, ay = flat[a]
                    bx_, by_ = flat[b]
                    cx, cy = flat[c]
                    if (bx_ - ax) * (cy - ay) - (by_ - ay) * (cx - ax) < 0:
                        a, c = c, a
                    fs.append((a, b, c))
                    uv += [(flat[a][0] * uvscale, flat[a][1] * uvscale), (flat[b][0] * uvscale, flat[b][1] * uvscale),
                           (flat[c][0] * uvscale, flat[c][1] * uvscale)]
                self.raw(vt, fs, uv, mat, False, m)
            if bottom:
                fs, uv = [], []
                for a, b, c in tris:
                    ax, ay = flat[a]
                    bx_, by_ = flat[b]
                    cx, cy = flat[c]
                    if (bx_ - ax) * (cy - ay) - (by_ - ay) * (cx - ax) > 0:
                        a, c = c, a
                    fs.append((a, b, c))
                    uv += [(flat[a][0] * uvscale, flat[a][1] * uvscale), (flat[b][0] * uvscale, flat[b][1] * uvscale),
                           (flat[c][0] * uvscale, flat[c][1] * uvscale)]
                self.raw(vb, fs, uv, mat_bottom, False, m)
            if side:
                off = 0
                for ri, r in enumerate(rings):
                    k = len(r)
                    vs = [(x, y, z0) for x, y in r] + [(x, y, z1) for x, y in r]
                    fs, uv = [], []
                    d = 0.0
                    groups = {}
                    for i in range(k):
                        j = (i + 1) % k
                        seg = math.hypot(r[j][0] - r[i][0], r[j][1] - r[i][1])
                        f = (i, j, j + k, i + k)
                        u = [(d * uvscale, z0 * uvscale), ((d + seg) * uvscale, z0 * uvscale),
                             ((d + seg) * uvscale, z1 * uvscale), (d * uvscale, z1 * uvscale)]
                        d += seg
                        if side_fn is not None and seg > 1e-9:
                            nx, ny = (r[j][1] - r[i][1]) / seg, -(r[j][0] - r[i][0]) / seg
                            mt = side_fn((r[i][0] + r[j][0]) / 2, (r[i][1] + r[j][1]) / 2, nx, ny, (z0 + z1) / 2)
                            g = groups.setdefault(id(mt), (mt, [], []))
                            g[1].append(f)
                            g[2].extend(u)
                        else:
                            fs.append(f)
                            uv += u
                    if fs:
                        self.raw(vs, fs, uv, mat_side, False, m)
                    for mt, gf, gu in groups.values():
                        self.raw(vs, gf, gu, mt if mt is not None else mat_side, False, m)
                    off += k
        return self

    def tube(self, path, r, mat=None, segs=12, closed=False, caps=True, m=None, profile=None, up=None,
             smooth=True, radii=None):
        """Sweep a circle (or 2D *profile* [(a, b)...]) along a 3D polyline using parallel transport."""
        P = [Vector(p) for p in path]
        n = len(P)
        if n < 2:
            return self
        tang = []
        for i in range(n):
            if closed:
                t = P[(i + 1) % n] - P[i - 1]
            elif i == 0:
                t = P[1] - P[0]
            elif i == n - 1:
                t = P[-1] - P[-2]
            else:
                t = (P[i + 1] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()
            tang.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
        # initial normal
        if up is not None:
            nrm = Vector(up) - tang[0] * Vector(up).dot(tang[0])
            if nrm.length < 1e-6:
                nrm = tang[0].orthogonal()
        else:
            nrm = tang[0].orthogonal()
        nrm.normalize()
        if profile is None:
            prof = [(math.cos(TAU * k / segs), math.sin(TAU * k / segs)) for k in range(segs)]
            scale = r
        else:
            prof = list(profile)
            scale = 1.0
        k = len(prof)
        # perimeter for uv
        per = [0.0]
        for i in range(k):
            a, b = prof[i], prof[(i + 1) % k]
            per.append(per[-1] + math.hypot(b[0] - a[0], b[1] - a[1]) * scale)
        verts = []
        frames = []
        for i in range(n):
            if i > 0:
                if up is not None:
                    nn = Vector(up) - tang[i] * Vector(up).dot(tang[i])
                    nrm = nn.normalized() if nn.length > 1e-6 else nrm
                else:
                    axis = tang[i - 1].cross(tang[i])
                    if axis.length > 1e-8:
                        ang = tang[i - 1].angle(tang[i])
                        nrm = Matrix.Rotation(ang, 3, axis.normalized()) @ nrm
                    nrm = (nrm - tang[i] * nrm.dot(tang[i])).normalized()
            bi = tang[i].cross(nrm).normalized()
            frames.append((nrm.copy(), bi))
            # mitre scale at corners
            ms = 1.0
            if 0 < i < n - 1 or closed:
                a = (P[i] - P[i - 1]).normalized()
                b = (P[(i + 1) % n] - P[i]).normalized()
                c = max(-0.999, min(1.0, a.dot(b)))
                ms = min(3.0, 1.0 / max(0.3, math.sqrt((1 + c) / 2)))
            rr = scale * (radii[i] / r if radii is not None and profile is None else 1.0)
            for (a_, b_) in prof:
                verts.append(tuple(P[i] + (nrm * a_ + bi * b_) * rr * (ms if profile is not None else 1.0)))
        faces = []
        uvs = []
        d = 0.0
        rng = n if closed else n - 1
        for i in range(rng):
            j = (i + 1) % n
            seg = (P[j] - P[i]).length
            for q in range(k):
                q2 = (q + 1) % k
                faces.append((i * k + q, i * k + q2, j * k + q2, j * k + q))
                uvs += [(d, per[q]), (d, per[q + 1]), (d + seg, per[q + 1]), (d + seg, per[q])]
            d += seg
        if caps and not closed:
            faces.append(tuple(range(k - 1, -1, -1)))
            uvs += [(prof[q][0] * scale, prof[q][1] * scale) for q in range(k - 1, -1, -1)]
            faces.append(tuple((n - 1) * k + q for q in range(k)))
            uvs += [(prof[q][0] * scale, prof[q][1] * scale) for q in range(k)]
        return self.raw(verts, faces, uvs, mat, smooth, m)

    def grid(self, fn, nu, nv, mat=None, m=None, smooth=True, su=1.0, sv=1.0, close_u=False, close_v=False,
             flip=False):
        """Parametric surface.  fn(u, v) -> (x, y, z) for u, v in [0, 1] (numpy arrays in, arrays out)."""
        u = np.linspace(0, 1, nu + 1)
        v = np.linspace(0, 1, nv + 1)
        if close_u:
            u = u[:-1]
        if close_v:
            v = v[:-1]
        U, Vv = np.meshgrid(u, v, indexing='ij')
        X, Y, Z = fn(U, Vv)
        X = np.broadcast_to(X, U.shape)
        Y = np.broadcast_to(Y, U.shape)
        Z = np.broadcast_to(Z, U.shape)
        verts = np.stack([X, Y, Z], -1).reshape(-1, 3)
        cu, cv = U.shape
        faces = []
        uvs = []
        ru = cu if close_u else cu - 1
        rv = cv if close_v else cv - 1
        for i in range(ru):
            i2 = (i + 1) % cu
            for j in range(rv):
                j2 = (j + 1) % cv
                q = [(i * cv + j, (i / nu * su, j / nv * sv)), (i2 * cv + j, ((i + 1) / nu * su, j / nv * sv)),
                     (i2 * cv + j2, ((i + 1) / nu * su, (j + 1) / nv * sv)), (i * cv + j2, (i / nu * su, (j + 1) / nv * sv))]
                if flip:
                    q.reverse()
                faces.append(tuple(a for a, _ in q))
                uvs.extend(b for _, b in q)
        return self.raw(verts, faces, uvs, mat, smooth, m)

    def cushion(self, size, loc=(0, 0, 0), mat=None, e=5.0, puff=0.0, n=8, m=None, rz=None, base=False,
                pinch=0.0, sag=0.0):
        """Soft rounded box (superellipsoid).  e: boxiness (2 = ellipsoid, 8 = boxy);
        puff: extra dome on top/bottom (m); pinch: pulls the 4 vertical corners in (pillow ears)."""
        sx, sy, sz = size
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=n, use_grid_fill=True)
        for v in bm.verts:
            x, y, z = v.co
            d = (abs(x) ** e + abs(y) ** e + abs(z) ** e) ** (1.0 / e)
            x, y, z = x / d, y / d, z / d
            if puff:
                z += math.copysign(puff / (sz / 2), z) * (1 - x * x) * (1 - y * y) * (abs(z) ** 0.5)
            if pinch:
                k = 1 - pinch * (abs(x) * abs(y)) ** 2 * (1 - abs(z)) ** 0.5
                z *= k
            if sag:
                z -= sag / (sz / 2) * (1 - x * x) * (1 - y * y) * (1 if z > 0 else 0)
            v.co = (x * sx / 2, y * sy / 2, z * sz / 2)
        M = Matrix.Translation((loc[0], loc[1], loc[2] + (sz / 2 if base else 0)))
        if rz:
            M = M @ Matrix.Rotation(rad(rz), 4, 'Z')
        if m is not None:
            M = m @ M
        return self.from_bm(bm, mat, True, M, dims=(sx, sy, sz))

    def torus(self, R_, r, loc=(0, 0, 0), mat=None, segs=48, rsegs=12, m=None, axis='Z'):
        prof = [(R_ + r * math.cos(TAU * k / rsegs), r * math.sin(TAU * k / rsegs)) for k in range(rsegs)]
        M = Matrix.Translation(loc)
        if axis == 'X':
            M = M @ Matrix.Rotation(PI / 2, 4, 'Y')
        elif axis == 'Y':
            M = M @ Matrix.Rotation(-PI / 2, 4, 'X')
        if m is not None:
            M = m @ M
        return self.lathe(prof, mat, segs, M, close=True)

    def add_obj(self, o, m=None, mat=None):
        """Append an existing object's evaluated mesh (keeps its materials unless mat is given)."""
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        M = (m if m is not None else Matrix.Identity(4)) @ o.matrix_world
        verts = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", verts)
        uvl = me.uv_layers.active
        slots = [s.material for s in o.material_slots] or [None]
        for p in me.polygons:
            idx = tuple(p.vertices)
            uv = [tuple(uvl.data[li].uv) for li in p.loop_indices] if uvl else [(0, 0)] * len(idx)
            self._one(verts, idx, uv, mat or slots[min(p.material_index, len(slots) - 1)], p.use_smooth, M)
        o.evaluated_get(dg).to_mesh_clear()
        return self

    def _one(self, verts, idx, uv, mat, smooth, M):
        pts = [verts[i * 3:i * 3 + 3] for i in idx]
        self.raw(pts, [tuple(range(len(idx)))], uv, mat, smooth, M)

    # ---- output ----------------------------------------------------------
    def finish(self, name=None, c=None, sharp=None, weighted=False, subsurf=0, loc=None, merge=None,
               origin=None):
        name = name or self.name
        me = bpy.data.meshes.new(name)
        if self.nv:
            V = np.concatenate(self.V)
            if origin is not None:
                V = V - np.array(origin)
            me.from_pydata(V.tolist(), [], self.F)
            me.polygons.foreach_set("material_index", self.MI)
            me.polygons.foreach_set("use_smooth", self.SM)
            uvl = me.uv_layers.new(name="UVMap")
            uvl.data.foreach_set("uv", np.asarray(self.UV, dtype=np.float32).ravel())
        for mt in self.mats:
            me.materials.append(mt)
        me.update()
        if merge:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
            bm.to_mesh(me)
            bm.free()
        if sharp is not None:
            me.set_sharp_from_angle(angle=rad(sharp))
        o = bpy.data.objects.new(name, me)
        link(o, c)
        if origin is not None:
            o.location = origin
        if loc is not None:
            o.location = loc
        if subsurf:
            sm = o.modifiers.new("subsurf", 'SUBSURF')
            sm.levels = subsurf
            sm.render_levels = subsurf
        if weighted:
            wn = o.modifiers.new("wn", 'WEIGHTED_NORMAL')
            wn.keep_sharp = True
            wn.weight = 60
        self.V, self.F, self.UV, self.MI, self.SM = [], [], [], [], []
        self.nv = 0
        return o


def _as_polys(poly):
    """-> list of (outer [(x,y)...] CCW, [holes CW])."""
    out = []
    if isinstance(poly, (list, tuple)):
        pts = [(float(p[0]), float(p[1])) for p in poly]
        if _area(pts) < 0:
            pts.reverse()
        return [(pts, [])]
    gt = poly.geom_type
    geoms = [poly] if gt == 'Polygon' else [g for g in getattr(poly, 'geoms', []) if g.geom_type == 'Polygon']
    for g in geoms:
        if g.is_empty or g.area < 1e-9:
            continue
        ext = _clean(list(g.exterior.coords)[:-1])
        if _area(ext) < 0:
            ext.reverse()
        holes = []
        for r in g.interiors:
            h = _clean(list(r.coords)[:-1])
            if _area(h) > 0:
                h.reverse()
            if len(h) >= 3:
                holes.append(h)
        if len(ext) >= 3:
            out.append((ext, holes))
    return out


def _clean(pts, eps=1e-7):
    res = []
    for p in pts:
        p = (float(p[0]), float(p[1]))
        if not res or abs(p[0] - res[-1][0]) > eps or abs(p[1] - res[-1][1]) > eps:
            res.append(p)
    if len(res) > 1 and abs(res[0][0] - res[-1][0]) < eps and abs(res[0][1] - res[-1][1]) < eps:
        res.pop()
    return res


def _area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2


# --------------------------------------------------------------------------
# object utilities
# --------------------------------------------------------------------------
def inst(o, loc=(0, 0, 0), rz=0.0, c=None, name=None, scale=None, rot=None):
    """Linked duplicate (shares mesh data) -- cheap instancing for repeated furniture."""
    n = bpy.data.objects.new(name or o.name, o.data)
    n.location = loc
    if rot is not None:
        n.rotation_euler = rot
    else:
        n.rotation_euler = (0, 0, rad(rz))
    if scale is not None:
        n.scale = scale if isinstance(scale, (tuple, list)) else (scale,) * 3
    for md in o.modifiers:
        nm = n.modifiers.new(md.name, md.type)
        for p in md.bl_rna.properties:
            if not p.is_readonly and p.identifier not in ('name', 'type'):
                try:
                    setattr(nm, p.identifier, getattr(md, p.identifier))
                except Exception:
                    pass
    link(n, c)
    return n


def place(o, x=0.0, y=0.0, z=0.0, rz=0.0):
    o.location = (x, y, z)
    o.rotation_euler = (0, 0, rad(rz))
    return o


def apply_mods(o):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = o.data
    o.modifiers.clear()
    o.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return o


def empty(name, loc=(0, 0, 0), c=None):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    e.empty_display_size = 0.2
    link(e, c)
    return e


def parent(children, par):
    for ch in children:
        ch.parent = par
    return par


def fillet(points, r, n=6, closed=False):
    """Round the corners of a 3D polyline with arcs of radius r (returns a denser polyline)."""
    P = [Vector(p) for p in points]
    out = []
    m = len(P)
    rng = range(m) if closed else range(1, m - 1)
    if not closed:
        out.append(P[0])
    for i in rng:
        a, b, c = P[i - 1], P[i], P[(i + 1) % m]
        d1 = (a - b)
        d2 = (c - b)
        l1, l2 = d1.length, d2.length
        if l1 < 1e-9 or l2 < 1e-9:
            out.append(b)
            continue
        d1.normalize()
        d2.normalize()
        ang = d1.angle(d2)
        if ang > PI - 1e-3 or ang < 1e-3:
            out.append(b)
            continue
        t = min(r / math.tan(ang / 2), l1 * 0.49, l2 * 0.49)
        rr = t * math.tan(ang / 2)
        p1 = b + d1 * t
        p2 = b + d2 * t
        bis = (d1 + d2).normalized()
        cen = b + bis * (rr / math.sin(ang / 2))
        v1 = p1 - cen
        v2 = p2 - cen
        axis = v1.cross(v2)
        sweep = v1.angle(v2)
        if axis.length < 1e-9:
            out += [p1, p2]
            continue
        axis.normalize()
        for k in range(n + 1):
            out.append(cen + Matrix.Rotation(sweep * k / n, 3, axis) @ v1)
    if not closed:
        out.append(P[-1])
    return out


def bezier(p0, p1, p2, p3, n=16):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3)
    return out


def catmull(points, n=8, closed=False):
    """Catmull-Rom spline through points."""
    P = [Vector(p) for p in points]
    m = len(P)
    out = []
    rng = m if closed else m - 1
    for i in range(rng):
        p0 = P[(i - 1) % m] if (closed or i > 0) else P[0]
        p1 = P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if (closed or i + 2 < m) else P[-1]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed:
        out.append(P[-1])
    return out


def rnd(a=0.0, b=1.0):
    return _rng.uniform(a, b)


def seed(s):
    _rng.seed(s)
