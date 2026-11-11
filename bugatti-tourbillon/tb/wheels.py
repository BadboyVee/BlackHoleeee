"""Wheels: four complete wheel assemblies (rim, tyre, brake disc, caliper, centre cap).

    from tb import wheels
    roots = wheels.build()                 # {"FL": obj, "FR": obj, "RL": obj, "RR": obj}
    root = wheels.build_single("FL")       # one corner only (close-ups / tests)

Hierarchy per corner <P> in FL / FR / RL / RR
    WHL_<P>             Empty at the wheel centre (spec.WHEELS[P]).  Unrotated; rotate about Z to steer.
      WHL_<P>_Spin      Empty at the same point, unrotated.  Rotate about its local Y to roll the wheel
                        (positive angle = rolling forward, on all four corners).
        WHL_<P>_Rim     forged five twin-spoke rim   (slots: alu_machined, alu_dark)
        WHL_<P>_Tyre    tyre with cut tread          (rubber_tyre)
        WHL_<P>_Disc    ventilated drilled disc+bell (brake_disc, alu_dark, steel_dark)
        WHL_<P>_Cap     plain domed centre cap       (alu_polished)
        WHL_<P>_Lugs    five wheel bolts + valve stem (steel_dark)
      WHL_<P>_Caliper   monoblock caliper + pads     (caliper, steel_dark, plastic_black) - does not spin
      WHL_<P>_Carrier   hub carrier / upright        (alu_dark)                           - does not spin

All meshes are modelled in wheel space: origin at the wheel centre, axle along Y, styled face
towards +Y.  Left and right corners share mesh data; the spinning parts of the right-hand
wheels are rotated 180 deg about Z, the static parts are placed with pure rotations as well
(the caliper and carrier are top/bottom symmetric), so nothing has a negative scale.
Front calipers sit behind the axle (-X), rear calipers ahead of it (+X).

Rim layout (see refs A3a / B5): five pads on the rim, each carried by two blades (a "frame")
with a through window between them; neighbouring frames merge into one stout stem towards
the hub, i.e. every stem splits into two blades ("Y").  The stems carry a dark recessed
pocket that hosts the wheel bolt and are slightly skewed off the radial for a pinwheel twist.
"""
import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

from . import spec, util, materials

PREFIX = "WHL_"
PI = math.pi
TAU = 2.0 * math.pi


# ====================================================================== parameters
def _params(front):
    """All dimensions of one axle's wheel (metres, wheel space)."""
    if front:
        P = dict(tag="F", R_tyre=spec.FRONT_TYRE_RADIUS, W_tyre=spec.FRONT_TYRE_WIDTH,
                 R_rim=spec.FRONT_RIM_RADIUS, rim_w=10.0 * 0.0254,
                 disc_r=0.210, disc_band=0.075, y_disc=-0.005, disc_rows=24,
                 cal_span_deg=76.0, cal_pistons=4, s_in=0.42, drop=0.0045, shoulder_b=0.024)
    else:
        P = dict(tag="R", R_tyre=spec.REAR_TYRE_RADIUS, W_tyre=spec.REAR_TYRE_WIDTH,
                 R_rim=spec.REAR_RIM_RADIUS, rim_w=12.0 * 0.0254,
                 disc_r=0.200, disc_band=0.072, y_disc=0.0, disc_rows=22,
                 cal_span_deg=62.0, cal_pistons=3, s_in=0.50, drop=0.0050, shoulder_b=0.026)
    P["front"] = front
    # rim section
    P["y_fi"] = P["rim_w"] / 2.0            # tyre-side face of the flanges
    P["y_lip"] = P["y_fi"] + 0.010          # outer face of the flange (rim lip plane)
    P["y_pad"] = P["y_lip"] - 0.004         # machined pad face, just below the lip
    P["R_ft"] = P["R_rim"] + 0.0175         # flange tip radius
    P["R_f"] = P["R_rim"] - 0.0085          # radius where the spoke face meets the lip
    P["segs"] = 100                         # angular resolution of the barrel
    # dish (face = surface of revolution: flat pads, conical sweep to a flat hub)
    P["s_out"] = 0.06
    P["r_c"] = P["R_f"] - 0.0405
    P["t_hub"] = 0.036
    P["t_spoke"] = 0.028
    # spoke layout
    P["r_J"] = 0.40 * P["R_f"]              # radius where a stem splits into two blades
    P["twist_deg"] = 7.0                    # stems skewed off the radial (pinwheel)
    P["pad_half_deg"] = 15.5                # blade centre lines meet the rim at +- this angle
    P["w_plus"] = 0.026                     # wide blade (the +theta one of each frame)
    P["w_minus"] = 0.019                    # slim blade
    P["h_stem"] = 0.028                     # stem half width
    P["w_ridge"] = 0.0085                   # bright ridge around the stem pocket
    P["r_pad_in"] = P["R_f"] - 0.031        # inner edge of the pads
    P["r_win_out"] = P["R_f"] - 0.005       # outer edge of the windows between the pads
    P["r_pocket_in"] = 0.047
    P["r_bore"] = 0.0355                    # counterbore of the centre cap
    P["r_lug"] = 0.062
    P["rc_win"] = 0.0075                    # corner radius of the through windows
    P["rc_pocket"] = 0.0050
    P["pocket_depth"] = 0.0075
    P["bore_depth"] = 0.0045
    P["R_b"] = P["r_win_out"]               # outer radius of the spoke plate's back face
    return P


def _s01(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class _Dish:
    """Face height F(r) and back height B(r) of the spoke plate (surface of revolution)."""

    def __init__(self, P):
        self.P = P
        r = np.linspace(0.0, P["R_f"] + 0.05, 2400)
        s = P["s_in"] + (P["s_out"] - P["s_in"]) * _s01((r - (P["r_c"] - 0.012)) / 0.024)
        s = s * _s01((r - 0.050) / 0.035)
        s = np.where(r > P["R_f"], 0.0, s)
        integ = np.concatenate([[0.0], np.cumsum(0.5 * (s[1:] + s[:-1]) * np.diff(r))])
        i_rf = np.interp(P["R_f"], r, integ)
        self._r, self._f, self._s = r, P["y_pad"] - (i_rf - integ), s

    def F(self, r):
        return np.interp(r, self._r, self._f)

    def slope(self, r):
        return np.interp(r, self._r, self._s)

    def T(self, r):
        P = self.P
        return P["t_hub"] + (P["t_spoke"] - P["t_hub"]) * _s01((np.asarray(r) - 0.055) / 0.065)

    def B(self, r):
        return self.F(r) - self.T(r)


# ====================================================================== mesh builder
class _MB:
    """Indexed mesh accumulator with per-face material index."""

    def __init__(self):
        self._v, self.n, self.faces, self.mats = [], 0, [], []

    def add(self, pts):
        pts = np.asarray(pts, float).reshape(-1, 3)
        idx = np.arange(self.n, self.n + len(pts))
        self._v.append(pts)
        self.n += len(pts)
        return idx

    def face(self, idx, mat=0):
        self.faces.append(tuple(int(i) for i in idx))
        self.mats.append(mat)

    def tris(self, tri_idx, mat=0):
        for t in tri_idx:
            self.face(t, mat)

    def strip(self, a, b, mat=0, closed=True):
        """Quads between two equally long vertex rows."""
        n = len(a)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            self.face((a[i], a[j], b[j], b[i]), mat)

    def fan(self, ring, centre, mat=0):
        n = len(ring)
        for i in range(n):
            self.face((ring[i], ring[(i + 1) % n], centre), mat)

    def grid(self, idx2d, closed_u=False, closed_v=False, mat=0):
        nu, nv = idx2d.shape
        for u in range(nu if closed_u else nu - 1):
            u1 = (u + 1) % nu
            for v in range(nv if closed_v else nv - 1):
                v1 = (v + 1) % nv
                self.face((idx2d[u, v], idx2d[u1, v], idx2d[u1, v1], idx2d[u, v1]), mat)

    def lathe(self, prof, ang, mats=0, first=None, last=None):
        """Revolve [(r, y), ...] about Y over the angles `ang` (full turn).

        mats: one index or a list with one entry per profile segment.
        first / last: existing vertex rings to use instead of the end points of the profile.
        A point with r == 0 becomes a single pole vertex.  Returns the list of rings.
        """
        c, s = np.cos(ang), np.sin(ang)
        rings = []
        for k, (r, y) in enumerate(prof):
            if k == 0 and first is not None:
                rings.append(first)
            elif k == len(prof) - 1 and last is not None:
                rings.append(last)
            elif r < 1e-9:
                rings.append(int(self.add([(0.0, y, 0.0)])[0]))
            else:
                rings.append(self.add(np.column_stack([r * c, np.full(len(ang), y), r * s])))
        for k in range(len(rings) - 1):
            m = mats[k] if isinstance(mats, (list, tuple)) else mats
            a, b = rings[k], rings[k + 1]
            if isinstance(a, int) and isinstance(b, int):
                continue
            if isinstance(a, int):
                self.fan(b, a, m)
            elif isinstance(b, int):
                self.fan(a, b, m)
            else:
                self.strip(a, b, m)
        return rings

    def box(self, lo, hi, mat=0):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        i = self.add([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                      (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.face([i[k] for k in f], mat)

    def cylinder(self, centre, axis, r, h0, h1, segs=16, mat=0, cap0=False, cap1=True):
        """Cylinder along a unit axis from offset h0 to h1 around `centre`."""
        ax = np.asarray(axis, float)
        ax = ax / np.linalg.norm(ax)
        ref = np.array([1.0, 0.0, 0.0]) if abs(ax[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u = np.cross(ax, ref)
        u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        a = np.arange(segs) * TAU / segs
        circ = np.outer(np.cos(a), u) + np.outer(np.sin(a), v)
        c = np.asarray(centre, float)
        r0 = self.add(c + ax * h0 + r * circ)
        r1 = self.add(c + ax * h1 + r * circ)
        self.strip(r0, r1, mat)
        if cap1:
            self.face(r1, mat)
        if cap0:
            self.face(r0[::-1], mat)
        return r0, r1

    def to_object(self, name, mats, collection, recalc=True):
        V = np.vstack(self._v)
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], self.faces)
        me.polygons.foreach_set("material_index", np.asarray(self.mats, dtype=np.int32))
        for m in mats:
            me.materials.append(materials.get(m) if isinstance(m, str) else m)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context='VERTS')
        if recalc:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
        obj = bpy.data.objects.new(name, me)
        collection.objects.link(obj)
        return obj


def _finish(obj, sharp_deg=None, weighted=True):
    """Smooth shading (+ sharp edges above sharp_deg) and baked face-area weighted normals,
    so that flat faces stay flat and all the shading change happens inside the bevels."""
    util.shade_smooth(obj, sharp_deg)
    if weighted:
        m = obj.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
        m.keep_sharp = True
        m.mode = 'FACE_AREA'
        m.weight = 90
        util.apply_modifiers(obj)
    return obj


def _bevel_apply(obj, width, segments=3, angle_deg=30.0):
    m = obj.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle_deg)
    m.harden_normals = False
    util.apply_modifiers(obj)
    return obj


def _merge_into(dst, src):
    """Append src's mesh to dst (same material slots) and delete src."""
    bm = bmesh.new()
    bm.from_mesh(dst.data)
    bm.from_mesh(src.data)
    bm.to_mesh(dst.data)
    bm.free()
    dst.data.update()
    util.delete(src)
    return dst


def _transform_verts(obj, fn):
    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = fn(co.reshape(-1, 3))
    me.vertices.foreach_set("co", np.ascontiguousarray(co, dtype=float).ravel())
    me.update()


# ====================================================================== 2D helpers
def _dir(a):
    return np.array([math.cos(a), math.sin(a)])


def _hp_side(Pt, d, side, shift):
    """Half-plane (n, c) meaning n.p <= c: keep the points at least `shift` to the left
    (side=+1) or to the right (side=-1) of the directed line through Pt along d."""
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    nl = np.array([-d[1], d[0]])
    n = -side * nl
    return n, float(n @ Pt) - shift


def _clip(poly, n, c):
    out = []
    m = len(poly)
    for i in range(m):
        a, b = poly[i], poly[(i + 1) % m]
        da, db = float(n @ a) - c, float(n @ b) - c
        if da <= 0.0:
            out.append(a)
        if (da < 0.0 < db) or (db < 0.0 < da):
            out.append(a + (b - a) * (da / (da - db)))
    return out


def _convex(halfplanes, erode=0.0, big=2.0):
    """CCW convex polygon = intersection of half-planes, each moved inwards by `erode`."""
    poly = [np.array(p, float) for p in ((-big, -big), (big, -big), (big, big), (-big, big))]
    for n, c in halfplanes:
        poly = _clip(poly, np.asarray(n, float), c - erode)
        if len(poly) < 3:
            raise ValueError("empty window polygon")
    out = []
    for p in poly:
        if not out or np.linalg.norm(p - out[-1]) > 2e-5:
            out.append(p)
    if np.linalg.norm(out[0] - out[-1]) <= 2e-5:
        out.pop()
    return np.array(out)


def _ring_samples(poly, seg=0.011, arc_deg=18.0, min_turn_deg=7.0):
    """Sample the 'normal bundle' of a convex CCW polygon -> (C, N).
    C + b * N is the outline offset outwards by b (rounded corners of radius b); every
    offset has the same number of points, so offsets loft into clean quad strips."""
    Pl = np.asarray(poly, float)
    n = len(Pl)
    E = np.roll(Pl, -1, 0) - Pl
    L = np.linalg.norm(E, axis=1)
    D = E / L[:, None]
    Nrm = np.column_stack([D[:, 1], -D[:, 0]])
    C, N = [], []
    for i in range(n):
        n0, n1 = Nrm[i - 1], Nrm[i]
        a = math.atan2(n0[0] * n1[1] - n0[1] * n1[0], float(n0 @ n1))
        if a < math.radians(min_turn_deg):
            b = n0 + n1
            b = b / np.linalg.norm(b) / math.cos(a / 2.0)
            C.append(Pl[i])
            N.append(b)
        else:
            k = max(1, int(math.ceil(math.degrees(a) / arc_deg)))
            a0 = math.atan2(n0[1], n0[0])
            for j in range(k + 1):
                C.append(Pl[i])
                N.append(_dir(a0 + a * j / k))
        m = int(math.ceil(L[i] / seg)) - 1
        for j in range(1, m + 1):
            C.append(Pl[i] + E[i] * j / (m + 1))
            N.append(n1)
    return np.array(C), np.array(N)


def _rot2(A, ang):
    c, s = math.cos(ang), math.sin(ang)
    A = np.asarray(A, float)
    return np.column_stack([c * A[:, 0] - s * A[:, 1], s * A[:, 0] + c * A[:, 1]])


def _in_poly(pts, poly):
    """Even-odd point-in-polygon test (vectorised over pts)."""
    x, y = pts[:, 0], pts[:, 1]
    inside = np.zeros(len(pts), bool)
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        if ay == by:
            continue
        cond = ((ay > y) != (by > y)) & (x < (bx - ax) * (y - ay) / (by - ay) + ax)
        inside ^= cond
    return inside


def _densify(loop, step):
    out = []
    n = len(loop)
    for i in range(n):
        a, b = loop[i], loop[(i + 1) % n]
        k = max(1, int(math.ceil(np.linalg.norm(b - a) / step)))
        for j in range(k):
            out.append(a + (b - a) * j / k)
    return np.array(out)


def _steiner(r0, r1, spacing, avoid, min_d, sym=5):
    """Polar grid of fill points between r0 and r1, at least min_d from the `avoid` points."""
    from scipy.spatial import cKDTree
    pts = []
    nr = max(1, int(round((r1 - r0) / spacing)))
    for i in range(nr + 1):
        r = r0 + (r1 - r0) * i / nr
        if r < 1e-6:
            pts.append((0.0, 0.0))
            continue
        n = max(sym, int(round(TAU * r / spacing / sym)) * sym)
        a = (np.arange(n) + 0.5 * (i % 2)) * TAU / n
        pts += list(zip(r * np.cos(a), r * np.sin(a)))
    pts = np.array(pts, float).reshape(-1, 2)
    if len(avoid) and len(pts):
        d, _ = cKDTree(avoid).query(pts)
        pts = pts[d > min_d]
    return pts


def _cdt(pts2, loops):
    """Constrained Delaunay triangulation of the whole convex hull.
    Returns (tris indexing into pts2 + extra, extra points created by the solver)."""
    verts = [Vector((float(a), float(b))) for a, b in pts2]
    edges = []
    for Lp in loops:
        Lp = [int(i) for i in Lp]
        edges += [(Lp[i], Lp[(i + 1) % len(Lp)]) for i in range(len(Lp))]
    ov, _, of, orig, _, _ = delaunay_2d_cdt(verts, edges, [], 0, 1e-9, True)
    remap = np.empty(len(ov), int)
    extra = []
    for i, o in enumerate(orig):
        if len(o):
            remap[i] = o[0]
        else:
            remap[i] = len(pts2) + len(extra)
            extra.append((ov[i][0], ov[i][1]))
    tris = np.array([[remap[i] for i in f] for f in of if len(f) == 3], int).reshape(-1, 3)
    return tris, np.array(extra, float).reshape(-1, 2)


def _to3(p2, y):
    p2 = np.asarray(p2, float)
    return np.column_stack([p2[:, 0], np.broadcast_to(y, (len(p2),)), p2[:, 1]])


# ====================================================================== rim
def _stem_axis(P, k):
    """(J, unit direction) of stem k's centre line in the wheel plane (x, z)."""
    psi = math.radians(90.0 + 72.0 * k + 36.0)
    return P["r_J"] * _dir(psi), _dir(psi + math.radians(P["twist_deg"]))


def _lug_positions(P):
    """Bolt centres: on each stem's centre line at radius r_lug."""
    out = []
    for k in range(5):
        J, d = _stem_axis(P, k)
        # |J - s d| = r_lug  ->  s^2 - 2 s (J.d) + |J|^2 - r^2 = 0  (take the root towards the hub)
        b = float(J @ d)
        s = b - math.sqrt(max(b * b - float(J @ J) + P["r_lug"] ** 2, 0.0))
        out.append(J - s * d)
    return np.array(out)


def _rim_features(P):
    """Windows / pockets of the spoke plate as offset-able convex outlines (all five sectors)."""
    rad = math.radians
    Rf = P["R_f"]
    phi0, sec = rad(90.0), rad(72.0)
    al = rad(P["pad_half_deg"])
    wp, wm, hs, wr = P["w_plus"], P["w_minus"], P["h_stem"], P["w_ridge"]

    def J(k):
        return _stem_axis(P, k)[0]

    def sd(k):
        return _stem_axis(P, k)[1]

    def Pp(k):
        return Rf * _dir(phi0 + sec * k + al)

    def Pm(k):
        return Rf * _dir(phi0 + sec * k - al)

    psi0 = phi0 + sec / 2.0
    # --- through window inside frame 0 (under the pad at 12 o'clock)
    Rp = 2.2 * P["r_pad_in"]
    cen = (P["r_pad_in"] - Rp) * _dir(phi0)
    frame = []
    for a in np.radians(np.arange(-14.0, 14.01, 2.0)):
        n = _dir(phi0 + a)
        frame.append((n, float(n @ cen) + Rp))
    frame.append(_hp_side(J(0), Pp(0) - J(0), -1, wp / 2.0))
    frame.append(_hp_side(J(-1), Pm(0) - J(-1), +1, wm / 2.0))
    frame.append(_hp_side(J(0), sd(0), -1, hs))
    frame.append(_hp_side(J(-1), sd(-1), +1, hs))
    # --- through window in the crotch of stem 0 (between two pads, bounded by the barrel)
    crotch = [(_dir(psi0 + a), P["r_win_out"]) for a in np.radians(np.arange(-32.0, 32.01, 2.0))]
    crotch.append(_hp_side(J(0), Pp(0) - J(0), +1, wp / 2.0))
    crotch.append(_hp_side(J(0), Pm(1) - J(0), -1, wm / 2.0))
    # --- blind pocket on stem 0
    hpk = hs - wr
    pocket = [_hp_side(J(0), sd(0), +1, -hpk), _hp_side(J(0), sd(0), -1, -hpk),
              (-_dir(psi0), -P["r_pocket_in"]),
              _hp_side(J(0), Pp(0) - J(0), -1, -(wp / 2.0 - wr)),
              _hp_side(J(0), Pm(1) - J(0), +1, -(wm / 2.0 - wr))]

    base = []
    for kind, hps, rc, seg in (("win", frame, P["rc_win"], 0.011), ("win", crotch, P["rc_win"], 0.011),
                               ("pocket", pocket, P["rc_pocket"], 0.009)):
        C, N = _ring_samples(_convex(hps, erode=rc), seg=seg)
        base.append((kind, C, N, rc))
    feats = []
    for k in range(5):
        for kind, C, N, rc in base:
            feats.append(dict(kind=kind, C=_rot2(C, sec * k), N=_rot2(N, sec * k), rc=rc))
    a = np.arange(48) * TAU / 48
    feats.append(dict(kind="bore", C=np.zeros((48, 2)), N=np.column_stack([np.cos(a), np.sin(a)]),
                      rc=P["r_bore"]))
    return feats


def _barrel_profile(P, dish):
    """Rim section from the spoke face over the lip, round the tyre side and back along the
    inside of the barrel to the back of the spoke plate: [(r, y, material of the next segment)]."""
    Rf, Rr, Rft, Rb = P["R_f"], P["R_rim"], P["R_ft"], P["R_b"]
    yl, yp, yfi = P["y_lip"], P["y_pad"], P["y_fi"]
    M, D = 0, 1
    pr = [(Rf, yp, M)]
    for t in (0.25, 0.5, 0.75, 1.0):                       # soft step up to the lip
        pr.append((Rf + 0.008 * t, yp + (yl - yp) * float(_s01(t)), M))
    rr = 0.0085                                            # flange edge radius
    pr.append((Rft - rr, yl, M))
    for a in (22.5, 45.0, 67.5):
        pr.append((Rft - rr + rr * math.sin(math.radians(a)), yl - rr + rr * math.cos(math.radians(a)), M))
    pr.append((Rft, yl - rr, D))
    pr += [(Rft - 0.0006, yfi + 0.0003, D), (Rft - 0.002, yfi, D),
           (Rr + 0.004, yfi, D), (Rr + 0.001, yfi - 0.002, D), (Rr, yfi - 0.005, D),
           (Rr, yfi - 0.020, D), (Rr - 0.0015, yfi - 0.026, D)]
    yw0, yw1 = -yfi + 0.050, -yfi + 0.022                  # drop centre (towards the inboard side)
    pr += [(Rr - 0.0015, yw0 + 0.006, D), (Rr - 0.018, yw0, D), (Rr - 0.018, yw1, D),
           (Rr - 0.0015, yw1 - 0.004, D), (Rr, -yfi + 0.005, D),
           (Rr + 0.001, -yfi + 0.002, D), (Rr + 0.004, -yfi, D), (Rft - 0.002, -yfi, D),
           (Rft - 0.0006, -yfi - 0.0003, D), (Rft, -yl + rr, D)]
    for a in (67.5, 45.0, 22.5):
        pr.append((Rft - rr + rr * math.sin(math.radians(a)), -yl + rr - rr * math.cos(math.radians(a)), D))
    pr += [(Rft - rr, -yl, D), (Rf + 0.006, -yl, D), (Rf + 0.002, -yl + 0.0012, D), (Rf, -yl + 0.005, D),
           (Rf, yw1 - 0.006, D), (Rf - 0.0155, yw1 + 0.002, D), (Rf - 0.0155, yw0 - 0.002, D),
           (Rf, yw0 + 0.008, D)]
    yB = float(dish.B(Rb))
    pr += [(Rf, yB - 0.050, D), (Rb + 0.0008, yB - 0.014, D), (Rb, yB - 0.004, D), (Rb, yB, D)]
    return pr


def _build_rim(P, col):
    mb = _MB()
    dish = _Dish(P)
    feats = _rim_features(P)
    segs = P["segs"]
    ang = np.arange(segs) * TAU / segs
    circ = np.column_stack([np.cos(ang), np.sin(ang)])
    M, D = 0, 1
    rad = math.radians

    def radius(p2):
        return np.hypot(p2[:, 0], p2[:, 1])

    # edge profile of the windows: fillet radius rho, wall draft delta
    for f in feats:
        if f["kind"] == "win":
            f["rho"], f["delta"] = 0.0022, rad(9.0)
        elif f["kind"] == "pocket":
            f["rho"], f["delta"] = 0.0016, rad(12.0)
        else:
            f["rho"], f["delta"] = 0.0012, rad(4.0)

    # ---------------------------------------------------------------- front face (CDT)
    pts, loops, n = [P["R_f"] * circ], [np.arange(segs)], segs
    for f in feats:
        r0 = f["C"] + (f["rc"] + f["rho"] * math.cos(f["delta"])) * f["N"]
        f["ring0"] = r0
        loops.append(np.arange(n, n + len(r0)))
        pts.append(r0)
        n += len(r0)
    con = np.vstack(pts)
    avoid = np.vstack([_densify(con[Lp], 0.003) for Lp in loops])
    st = _steiner(0.040, P["R_f"] - 0.004, 0.0085, avoid, 0.0036)
    for f in feats:
        st = st[~_in_poly(st, f["ring0"])]
    all2 = np.vstack([con, st])
    tris, extra = _cdt(all2, loops)
    if len(extra):
        all2 = np.vstack([all2, extra])
    cen = all2[tris].mean(axis=1)
    keep = radius(cen) < P["R_f"]
    for f in feats:
        keep &= ~_in_poly(cen, f["ring0"])
    base = mb.add(_to3(all2, dish.F(radius(all2))))
    mb.tris(base[tris[keep]], M)
    front_outer = base[:segs]

    # ---------------------------------------------------------------- window walls / pockets
    cb = 0.0015                                             # chamfer on the back edge
    Tn = P["t_spoke"]
    for f, Lp in zip(feats, loops[1:]):
        C, N, rc, rho, dl = f["C"], f["N"], f["rc"], f["rho"], f["delta"]
        prev = base[Lp]
        a_end = PI / 2.0 - dl
        d_e = rho * (1.0 - math.cos(a_end))
        for j, a in enumerate(np.linspace(0.0, a_end, 5)[1:]):         # rolled edge
            p2 = C + (rc + rho * (math.cos(dl) - math.sin(a))) * N
            ring = mb.add(_to3(p2, dish.F(radius(p2)) - rho * (1.0 - math.cos(a))))
            mb.strip(prev, ring, M if j == 0 else D)
            prev = ring
        if f["kind"] == "win":
            db_end = -math.tan(dl) * (Tn - d_e - cb)
            p2 = C + (rc + 0.5 * db_end) * N
            r_ = radius(p2)
            ring = mb.add(_to3(p2, 0.5 * (dish.F(r_) - d_e + dish.B(r_) + cb)))
            mb.strip(prev, ring, D)
            prev = ring
            p2 = C + (rc + db_end) * N
            ring = mb.add(_to3(p2, dish.B(radius(p2)) + cb))
            mb.strip(prev, ring, D)
            prev = ring
            p2 = C + (rc + db_end + cb) * N
            f["back2d"] = p2
            f["back_prev"] = prev
        else:
            depth = P["pocket_depth"] if f["kind"] == "pocket" else P["bore_depth"]
            db = -math.tan(dl) * (depth - d_e - 0.001)
            p2 = C + (rc + db) * N
            ring = mb.add(_to3(p2, dish.F(radius(p2)) - (depth - 0.001)))
            mb.strip(prev, ring, D)
            prev = ring
            p2 = C + (rc + db - 0.0012) * N
            ring = mb.add(_to3(p2, dish.F(radius(p2)) - depth))
            mb.strip(prev, ring, D)
            c2 = p2.mean(axis=0)[None, :]
            cidx = mb.add(_to3(c2, dish.F(radius(c2)) - depth))[0]
            mb.fan(ring, cidx, D)

    # ---------------------------------------------------------------- back face (CDT)
    pts, loops_b, n = [P["R_b"] * circ], [np.arange(segs)], segs
    wins = [f for f in feats if f["kind"] == "win"]
    for f in wins:
        loops_b.append(np.arange(n, n + len(f["back2d"])))
        pts.append(f["back2d"])
        n += len(f["back2d"])
    con = np.vstack(pts)
    avoid = np.vstack([_densify(con[Lp], 0.004) for Lp in loops_b])
    st = _steiner(0.0, P["R_b"] - 0.006, 0.016, avoid, 0.006)
    for f in wins:
        st = st[~_in_poly(st, f["back2d"])]
    all2 = np.vstack([con, st])
    tris, extra = _cdt(all2, loops_b)
    if len(extra):
        all2 = np.vstack([all2, extra])
    cen = all2[tris].mean(axis=1)
    keep = radius(cen) < P["R_b"]
    for f in wins:
        keep &= ~_in_poly(cen, f["back2d"])
    bbase = mb.add(_to3(all2, dish.B(radius(all2))))
    mb.tris(bbase[tris[keep]], D)
    for f, Lp in zip(wins, loops_b[1:]):
        mb.strip(f["back_prev"], bbase[Lp], D)
    back_outer = bbase[:segs]

    # ---------------------------------------------------------------- barrel
    prof = _barrel_profile(P, dish)
    mb.lathe([(r, y) for r, y, _ in prof], ang, mats=[m for _, _, m in prof[:-1]],
             first=front_outer, last=back_outer)

    obj = mb.to_object("WHL__rim", ["alu_machined", "alu_dark"], col)
    return _finish(obj, sharp_deg=None)


# ====================================================================== tyre
def _tyre_side_profile(P):
    """Outer surface of one sidewall, bead to buttress: [(y, r)] for the +Y side."""
    hw = P["W_tyre"] / 2.0
    Rr, Rft, yfi, yl = P["R_rim"], P["R_ft"], P["y_fi"], P["y_lip"]
    r_e = P["R_tyre"] - P["drop"]
    r_s = r_e - P["shoulder_b"]
    r_a = Rft + 0.0035
    Hs = r_s - r_a
    cur = util.Curve1D([(r_a, yl - 0.001), (r_a + 0.13 * Hs, hw - 0.0008), (r_a + 0.28 * Hs, hw - 0.0016),
                        (r_a + 0.50 * Hs, hw - 0.0030), (r_a + 0.75 * Hs, hw - 0.0022), (r_s, hw - 0.0040)])
    pts = [(yfi - 0.012, Rr + 0.0012), (yfi - 0.0005, Rr + 0.0035), (yfi - 0.0005, Rft - 0.003),
           (yfi + 0.0015, Rft + 0.0012), (yfi + 0.006, Rft + 0.0022)]

    def base(f):
        r = r_a + f * Hs
        return (float(cur(r)), r)

    def rib(f, h=0.0010):
        r = r_a + f * Hs
        return [(float(cur(r - 0.0030)), r - 0.0030), (float(cur(r - 0.0013)) + h, r - 0.0013),
                (float(cur(r + 0.0013)) + h, r + 0.0013), (float(cur(r + 0.0030)), r + 0.0030)]

    for f in (0.0, 0.05, 0.11, 0.17, 0.24, 0.32):
        pts.append(base(f))
    pts += rib(0.41)
    pts += [base(0.49), base(0.55)]
    pts += rib(0.63)
    for f in (0.72, 0.80, 0.88, 0.95):
        pts.append(base(f))
    pts.append((hw - 0.009, r_s + 0.001))                  # tucked under the tread band
    return pts


def _tread_stations(P):
    """Stations across the tread band from the outer (+Y) buttress to the inner one.
    Returns arrays y, r, ny, nr (outward normal), rib (index, -1 on groove floors), depth
    (how far the bottom lines of a lateral slot sit below the surface) and the rib table."""
    hw = P["W_tyre"] / 2.0
    R = P["R_tyre"]
    drop = P["drop"]
    ye = hw - 0.021
    r_e = R - drop
    bsh = P["shoulder_b"]
    r_s = r_e - bsh
    ash = hw - 0.0015 - ye

    def crown(y):
        return R - drop * abs(y / ye) ** 2.2

    # grooves: (centre as a fraction of the half tread width, width)
    grooves = [(+0.50, 0.010), (+0.12, 0.013), (-0.27, 0.013), (-0.66, 0.010)]
    gd = 0.0065
    ribs = [dict(w=0.0055, ang=22.0, phase=0.00, depth=0.0055),     # outer shoulder: wide blind slots
            dict(w=0.0016, ang=-30.0, phase=0.50, depth=0.0040),    # thin sipes
            dict(w=0.0, ang=0.0, phase=0.0, depth=0.0),             # plain centre rib
            dict(w=0.0016, ang=-30.0, phase=0.00, depth=0.0040),    # thin sipes
            dict(w=0.0045, ang=15.0, phase=0.50, depth=0.0055)]     # inner shoulder: open slots
    S = []

    def add(y, r, ny, nr, rib, depth):
        S.append((y, r, ny, nr, rib, depth))

    def shoulder(sign, rib, d_full, outward):
        rows = [(None, 0.0), (None, 0.0), (90.0, 0.27), (68.0, 0.64), (45.0, 0.90), (22.0, 1.0), (0.0, 1.0)]
        out = []
        for i, (t, df) in enumerate(rows):
            if t is None:
                if i == 0:
                    out.append((sign * (ye + ash - 0.004), r_s - 0.0078, sign * 1.0, 0.0, rib, 0.0))
                else:
                    out.append((sign * (ye + ash - 0.0002), r_s - 0.0070, sign * 1.0, 0.0, rib, 0.0))
            else:
                a = math.radians(t)
                ny, nr = math.sin(a) / ash, math.cos(a) / bsh
                ln = math.hypot(ny, nr)
                out.append((sign * (ye + ash * math.sin(a)), r_s + bsh * math.cos(a),
                            sign * ny / ln, nr / ln, rib, d_full * df))
        return out if outward else out[::-1]

    # outer shoulder + rib 0
    S += shoulder(+1, 0, ribs[0]["depth"], True)
    edges = []
    for cf, w in grooves:
        edges.append((cf * ye + w / 2.0, cf * ye - w / 2.0))
    g0a = edges[0][0]
    y_bl = g0a + 0.30 * (ye - g0a)
    d0 = ribs[0]["depth"]
    add(0.5 * (ye + y_bl), crown(0.5 * (ye + y_bl)), 0.0, 1.0, 0, d0)
    add(y_bl + 0.0012, crown(y_bl), 0.0, 1.0, 0, d0)
    add(y_bl, crown(y_bl), 0.0, 1.0, 0, 0.0)
    add(g0a, crown(g0a), 0.0, 1.0, 0, 0.0)
    for gi, (ya, yb) in enumerate(edges):
        add(ya - 0.0012, crown(ya) - gd, 0.0, 1.0, -1, 0.0)
        add(yb + 0.0012, crown(yb) - gd, 0.0, 1.0, -1, 0.0)
        rib = gi + 1
        d = ribs[rib]["depth"]
        if rib < 4:
            y_next = edges[gi + 1][0]
            add(yb, crown(yb), 0.0, 1.0, rib, d)
            add(0.5 * (yb + y_next), crown(0.5 * (yb + y_next)), 0.0, 1.0, rib, d)
            add(y_next, crown(y_next), 0.0, 1.0, rib, d)
        else:
            add(yb, crown(yb), 0.0, 1.0, rib, d)
            add(0.5 * (yb - ye), crown(0.5 * (yb - ye)), 0.0, 1.0, rib, d)
            S += shoulder(-1, rib, d, False)
    A = np.array(S, float)
    return dict(y=A[:, 0], r=A[:, 1], ny=A[:, 2], nr=A[:, 3], rib=A[:, 4].astype(int), depth=A[:, 5],
                ribs=ribs)


def _build_tyre(P, col):
    mb = _MB()
    R = P["R_tyre"]
    # ---------------------------------------------------------------- sidewalls (lathe)
    segs = 96
    ang = np.arange(segs) * TAU / segs
    side = _tyre_side_profile(P)
    mb.lathe([(r, y) for y, r in side], ang)
    mb.lathe([(r, -y) for y, r in side], ang)

    # ---------------------------------------------------------------- tread band (sheared grid)
    T = _tread_stations(P)
    ns = len(T["y"])
    n_pitch = 60
    pitch = TAU * R / n_pitch                               # arc length of one pitch at the crown
    wall = 0.0008
    # arc length across the profile, used to shear the lateral slots
    ell = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(T["y"]), np.diff(T["r"])))])
    off = np.zeros((ns, 4))
    shift = np.zeros(ns)
    for m, rb in enumerate(T["ribs"]):
        sel = np.where(T["rib"] == m)[0]
        if rb["w"] > 0.0:
            h = rb["w"] / 2.0
            off[sel] = (-(h + wall), -h, h, h + wall)
        else:
            off[sel] = np.array((-0.375, -0.125, 0.125, 0.375)) * pitch
        lref = ell[sel].mean()
        shift[sel] = rb["phase"] * pitch + (ell[sel] - lref) * math.tan(math.radians(rb["ang"]))
    for i in np.where(T["rib"] < 0)[0]:                     # groove floors copy the nearer rib edge
        j = i - 1 if T["rib"][i - 1] >= 0 else i + 1
        off[i], shift[i] = off[j], shift[j]
    idx = np.empty((n_pitch * 4, ns), int)
    for p in range(n_pitch):
        for t in range(4):
            th = (p * pitch + shift + off[:, t]) / R
            dep = T["depth"] if t in (1, 2) else 0.0
            y = T["y"] - dep * T["ny"]
            r = T["r"] - dep * T["nr"]
            idx[p * 4 + t] = mb.add(np.column_stack([r * np.cos(th), y, r * np.sin(th)]))
    mb.grid(idx, closed_u=True)

    obj = mb.to_object("WHL__tyre", ["rubber_tyre"], col)
    return _finish(obj, sharp_deg=38.0, weighted=False)


# ====================================================================== brake disc
def _disc_holes(P):
    """Cross-drilling pattern: swept rows of four holes."""
    ro, ri = P["disc_r"], P["disc_r"] - P["disc_band"]
    rows = P["disc_rows"]
    out = []
    fr = (0.20, 0.40, 0.60, 0.80)
    for k in range(rows):
        a0 = TAU * k / rows
        for j, f in enumerate(fr):
            r = ri + f * (ro - ri)
            a = a0 + math.radians(4.2) * (j - 1.5) + (math.radians(3.6) if j % 2 else 0.0)
            out.append((r * math.cos(a), r * math.sin(a)))
    return np.array(out)


def _drilled_face(mb, ri, ro, yf, sgn, yg, holes, r_h, sides, segs=96, mat=0):
    """One friction plate: drilled face at yf (normal sgn*Y), edges, plain back at yg."""
    ang = np.arange(segs) * TAU / segs
    circ = np.column_stack([np.cos(ang), np.sin(ang)])
    ce, ch, depth = 0.0010, 0.0006, 0.009
    ha = np.arange(sides) * TAU / sides
    hc = np.column_stack([np.cos(ha), np.sin(ha)])
    pts, loops, n = [(ro - ce) * circ, (ri + ce) * circ], [np.arange(segs), np.arange(segs, 2 * segs)], 2 * segs
    rings0 = []
    for h in holes:
        r0 = h[None, :] + (r_h + ch) * hc
        rings0.append(r0)
        loops.append(np.arange(n, n + sides))
        pts.append(r0)
        n += sides
    con = np.vstack(pts)
    avoid = np.vstack([_densify(con[Lp], 0.004) for Lp in loops[:2]] + pts[2:])
    st = _steiner(ri + 0.008, ro - 0.008, 0.013, avoid, 0.0055, sym=1)
    all2 = np.vstack([con, st])
    tris, extra = _cdt(all2, loops)
    if len(extra):
        all2 = np.vstack([all2, extra])
    cen = all2[tris].mean(axis=1)
    rc = np.hypot(cen[:, 0], cen[:, 1])
    keep = (rc < ro - ce) & (rc > ri + ce)
    if len(holes):
        from scipy.spatial import cKDTree
        d, _ = cKDTree(holes).query(cen)
        keep &= d > (r_h + ch) * math.cos(PI / sides) * 0.999
    base = mb.add(_to3(all2, yf))
    mb.tris(base[tris[keep]], mat)
    for h, Lp in zip(holes, loops[2:]):
        r1 = mb.add(_to3(h[None, :] + r_h * hc, yf - sgn * ch))
        r2 = mb.add(_to3(h[None, :] + r_h * hc, yf - sgn * depth))
        mb.strip(base[Lp], r1, mat)
        mb.strip(r1, r2, mat)
        mb.face(r2, mat)
    outer, inner = base[:segs], base[segs:2 * segs]
    # plate edges and plain gap-side face
    mb.lathe([(ro - ce, yf), (ro, yf - sgn * ce), (ro, yg), (ri, yg), (ri, yf - sgn * ce), (ri + ce, yf)],
             ang, mats=mat, first=outer, last=inner)


def _build_disc(P, col):
    mb = _MB()
    ro, ri, yd = P["disc_r"], P["disc_r"] - P["disc_band"], P["y_disc"]
    T, gap = 0.038, 0.014
    holes = _disc_holes(P)
    _drilled_face(mb, ri, ro, yd + T / 2, +1, yd + gap / 2, holes, 0.0028, 8)
    _drilled_face(mb, ri, ro, yd - T / 2, -1, yd - gap / 2, holes, 0.0028, 6)
    # vanes + root wall between the plates
    segs = 96
    ang = np.arange(segs) * TAU / segs
    rw = ri + 0.016
    w0 = mb.add(np.column_stack([rw * np.cos(ang), np.full(segs, yd - gap / 2), rw * np.sin(ang)]))
    w1 = mb.add(np.column_stack([rw * np.cos(ang), np.full(segs, yd + gap / 2), rw * np.sin(ang)]))
    mb.strip(w0, w1, 0)
    nv = 40
    for k in range(nv):
        a0 = TAU * k / nv
        a1 = a0 + math.radians(9.0)
        r0, r1, ht = rw - 0.001, ro - 0.0015, 0.0028
        p0, p1 = r0 * _dir(a0), r1 * _dir(a1)
        d = (p1 - p0) / np.linalg.norm(p1 - p0)
        nrm = np.array([-d[1], d[0]]) * ht
        q = [p0 - nrm, p1 - nrm, p1 + nrm, p0 + nrm]
        lo = mb.add([(p[0], yd - gap / 2, p[1]) for p in q])
        hi = mb.add([(p[0], yd + gap / 2, p[1]) for p in q])
        mb.strip(lo, hi, 0)
    # aluminium bell
    ym = P["y_mount"]
    rh = 0.088
    yfl = yd + 0.008
    prof = [(ri - 0.0006, yd - 0.008), (ri - 0.0006, yfl - 0.0015), (ri - 0.0022, yfl),
            (ri - 0.0155, yfl), (ri - 0.0195, yfl + 0.0016), (rh + 0.0045, ym - 0.0055),
            (rh + 0.0012, ym - 0.0015), (rh - 0.003, ym), (0.034, ym), (0.034, ym - 0.010)]
    mb.lathe(prof, np.arange(72) * TAU / 72, mats=1)
    # floating bobbins round the bell flange
    nb = 12
    for k in range(nb):
        a = TAU * (k + 0.5) / nb
        c = (ri - 0.0085) * _dir(a)
        mb.cylinder((c[0], yfl - 0.001, c[1]), (0, 1, 0), 0.0055, 0.0, 0.0042, segs=12, mat=2)
        mb.cylinder((c[0], yfl - 0.001, c[1]), (0, 1, 0), 0.0028, 0.0, 0.0058, segs=8, mat=2)
    obj = mb.to_object("WHL__disc", ["brake_disc", "alu_dark", "steel_dark"], col)
    return _finish(obj, sharp_deg=50.0)


# ====================================================================== caliper
def _voxel_cage(mb, xs, ys, zs, solid, mat=0):
    """Boundary quads of the union of the solid cells of a rectilinear grid (shared vertices)."""
    nx, ny, nz = solid.shape
    vid = {}

    def v(i, j, k):
        key = (i, j, k)
        if key not in vid:
            vid[key] = int(mb.add([(xs[i], ys[j], zs[k])])[0])
        return vid[key]

    def full(i, j, k):
        return 0 <= i < nx and 0 <= j < ny and 0 <= k < nz and bool(solid[i, j, k])

    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if not solid[i, j, k]:
                    continue
                if not full(i + 1, j, k):
                    mb.face((v(i + 1, j, k), v(i + 1, j + 1, k), v(i + 1, j + 1, k + 1), v(i + 1, j, k + 1)), mat)
                if not full(i - 1, j, k):
                    mb.face((v(i, j, k), v(i, j, k + 1), v(i, j + 1, k + 1), v(i, j + 1, k)), mat)
                if not full(i, j + 1, k):
                    mb.face((v(i, j + 1, k), v(i, j + 1, k + 1), v(i + 1, j + 1, k + 1), v(i + 1, j + 1, k)), mat)
                if not full(i, j - 1, k):
                    mb.face((v(i, j, k), v(i + 1, j, k), v(i + 1, j, k + 1), v(i, j, k + 1)), mat)
                if not full(i, j, k + 1):
                    mb.face((v(i, j, k + 1), v(i + 1, j, k + 1), v(i + 1, j + 1, k + 1), v(i, j + 1, k + 1)), mat)
                if not full(i, j, k - 1):
                    mb.face((v(i, j, k), v(i, j + 1, k), v(i + 1, j + 1, k), v(i + 1, j, k)), mat)


def _build_caliper(P, col):
    """Monoblock caliper modelled in unrolled coordinates (a = arc length, b = Y, c = radius),
    bevelled there, then wrapped round the disc at 9 o'clock (-X).  Top/bottom symmetric."""
    yd, ro = P["y_disc"], P["disc_r"]
    ri = ro - P["disc_band"]
    c0, c1, c2 = ri - 0.007, ro + 0.0055, ro + 0.026
    rmid = 0.5 * (c0 + c2)
    La = rmid * math.radians(P["cal_span_deg"]) / 2.0
    na = 24
    xs = np.linspace(-La, La, na + 1)
    yo0, yo1 = yd + 0.0355, yd + 0.065                      # outboard half
    yi0, yi1 = yd - 0.0600, yd - 0.0355                     # inboard half
    ys = [yi0, yi1, yo0, yo1]
    mats = ["caliper", "steel_dark", "plastic_black"]

    # --- body: two halves joined by three bridges over the disc
    mb = _MB()
    solid = np.zeros((na, 3, 2), bool)
    solid[:, 0, :] = True
    solid[:, 2, :] = True
    e = 4
    solid[:e, 1, 1] = True
    solid[-e:, 1, 1] = True
    solid[na // 2 - 1:na // 2 + 1, 1, 1] = True
    _voxel_cage(mb, xs, ys, [c0, c1, c2], solid, 0)
    # piston bosses on both faces
    nb = P["cal_pistons"]
    span_b = La * 0.80
    ab = np.linspace(-span_b, span_b, nb) * (1.0 - 1.0 / (2 * nb)) if nb > 1 else [0.0]
    step = (ab[1] - ab[0]) if nb > 1 else 0.06
    rb = min(0.0215, step / 2.0 - 0.0035)
    cb = 0.5 * (c0 + c1) + 0.003
    for a in ab:
        for yface, sg in ((yo1, +1.0), (yi0, -1.0)):
            mb.cylinder((a, yface, cb), (0, sg, 0), rb, -0.002, 0.0055, segs=20, mat=0)
            mb.cylinder((a, yface, cb), (0, sg, 0), rb * 0.42, 0.0, 0.0072, segs=14, mat=0)
    body = mb.to_object("WHL__cal", mats, col)
    _bevel_apply(body, 0.0042, segments=3, angle_deg=30.0)

    # --- pads, pad pins and bleed screws (small bevels)
    mb = _MB()
    npad = 16
    xp = np.linspace(-0.80 * La, 0.80 * La, npad + 1)
    one = np.ones((npad, 1, 1), bool)
    for sg in (+1.0, -1.0):
        f0, f1, f2 = yd + sg * 0.0198, yd + sg * 0.0300, yd + sg * 0.0352
        _voxel_cage(mb, xp, sorted([f0, f1]), [ri + 0.003, ro - 0.0015], one, 2)
        _voxel_cage(mb, xp, sorted([f1, f2]), [ri + 0.001, ro + 0.003], one, 1)
    for a in (-0.42 * La, 0.42 * La):                       # pad retaining pins across the windows
        mb.cylinder((a, yi1 - 0.002, c1 + 0.008), (0, 1, 0), 0.0032, 0.0, (yo0 - yi1) + 0.004, segs=12, mat=1,
                    cap1=False)
    for a in (-0.84 * La, 0.84 * La):                       # bleed screws
        mb.cylinder((a, yo0 + 0.016, c2 - 0.003), (0, 0, 1), 0.0045, 0.0, 0.008, segs=12, mat=1)
        mb.cylinder((a, yo0 + 0.016, c2 - 0.003), (0, 0, 1), 0.0026, 0.0, 0.015, segs=10, mat=1)
    small = mb.to_object("WHL__cal_small", mats, col)
    _bevel_apply(small, 0.0008, segments=2, angle_deg=40.0)
    _merge_into(body, small)

    drop, rise = 0.0045, 0.0085

    def warp(co):
        a, b, c = co[:, 0], co[:, 1], co[:, 2]
        t = np.clip(np.abs(a) / La, 0.0, 1.2)
        rt = c2 - drop * t ** 3
        rbm = c0 + rise * t ** 3
        cc = rbm + (c - c0) / (c2 - c0) * (rt - rbm)
        th = PI + a / rmid
        return np.column_stack([cc * np.cos(th), b, cc * np.sin(th)])

    _transform_verts(body, warp)
    return _finish(body, sharp_deg=35.0)


def _build_carrier(P, col):
    """Simple upright: bearing housing, vertical arm and caliper bracket.  Top/bottom symmetric."""
    yd = P["y_disc"]
    mb = _MB()
    ya, yb = yd - 0.110, yd - 0.064
    n = 8
    zs = np.linspace(-0.185, 0.185, n + 1)
    _voxel_cage(mb, [-0.042, 0.042], [ya, yb], zs, np.ones((1, 1, n), bool), 0)
    xs = np.linspace(-0.205, -0.030, 7)
    _voxel_cage(mb, xs, [yd - 0.100, yd - 0.0605], [-0.032, 0.032], np.ones((6, 1, 1), bool), 0)
    obj = mb.to_object("WHL__carrier", ["alu_dark"], col)
    _bevel_apply(obj, 0.006, segments=3, angle_deg=30.0)
    mb = _MB()
    prof = [(0.0, yd - 0.026), (0.058, yd - 0.026), (0.066, yd - 0.031), (0.066, yd - 0.090),
            (0.074, yd - 0.096), (0.074, yd - 0.122), (0.070, yd - 0.126), (0.0, yd - 0.126)]
    mb.lathe(prof, np.arange(40) * TAU / 40, mats=0)
    # thin dust shield behind the disc
    rs = P["disc_r"] - 0.012
    mb.lathe([(0.060, yd - 0.0275), (rs, yd - 0.0275), (rs, yd - 0.0295), (0.060, yd - 0.0295)],
             np.arange(48) * TAU / 48, mats=0)
    hub = mb.to_object("WHL__carrier_hub", ["alu_dark"], col)
    _merge_into(obj, hub)
    return _finish(obj, sharp_deg=40.0)


# ====================================================================== small parts
def _build_cap(P, col):
    dish = _Dish(P)
    y0 = float(dish.F(0.0))
    yb = y0 - P["bore_depth"]
    yt = y0 + 0.0008
    rc = P["r_bore"] - 0.0011
    prof = [(rc, yb + 0.0003), (rc, yt - 0.0010), (rc - 0.0009, yt), (0.0282, yt + 0.0002),
            (0.0274, yt - 0.0010), (0.0256, yt - 0.0010), (0.0248, yt + 0.0002)]
    rd = 0.0248
    for f in (0.85, 0.68, 0.50, 0.32, 0.15, 0.0):
        prof.append((rd * f, yt + 0.0002 + 0.0034 * (1.0 - f * f)))
    mb = _MB()
    mb.lathe(prof, np.arange(48) * TAU / 48, mats=0)
    obj = mb.to_object("WHL__cap", ["alu_polished"], col)
    return _finish(obj, sharp_deg=None)


def _build_lugs(P, col):
    """Five wheel bolts in the stem pockets plus the tyre valve stem."""
    dish = _Dish(P)
    mb = _MB()
    for c in _lug_positions(P):
        yf = float(dish.F(np.hypot(c[0], c[1]))) - P["pocket_depth"]
        cen = (c[0], yf, c[1])
        mb.cylinder(cen, (0, 1, 0), 0.0118, -0.001, 0.0018, segs=18, mat=0)
        mb.cylinder(cen, (0, 1, 0), 0.0092, 0.0, 0.0072, segs=6, mat=0)
        mb.cylinder(cen, (0, 1, 0), 0.0050, 0.0, 0.0080, segs=10, mat=0)
    # valve stem in the bottom window
    yB = float(dish.B(P["R_b"]))
    p0 = np.array([0.0, yB - 0.018, -(P["R_b"] + 0.002)])
    p1 = np.array([0.0, yB + 0.006, -(P["R_b"] - 0.022)])
    ax = (p1 - p0) / np.linalg.norm(p1 - p0)
    ln = float(np.linalg.norm(p1 - p0))
    mb.cylinder(p0, ax, 0.0032, 0.0, ln, segs=10, mat=0)
    mb.cylinder(p0, ax, 0.0044, ln - 0.009, ln + 0.001, segs=12, mat=0, cap0=True)
    obj = mb.to_object("WHL__lugs", ["steel_dark"], col)
    _bevel_apply(obj, 0.0007, segments=2, angle_deg=50.0)
    return _finish(obj, sharp_deg=45.0)


# ====================================================================== assembly
_SPIN_PARTS = (("Rim", _build_rim), ("Tyre", _build_tyre), ("Disc", _build_disc),
               ("Cap", _build_cap), ("Lugs", _build_lugs))
_STATIC_PARTS = (("Caliper", _build_caliper), ("Carrier", _build_carrier))


def _collection(collection):
    if collection is None:
        return util.get_collection(spec.COLLECTIONS["wheels"])
    if isinstance(collection, str):
        return util.get_collection(collection)
    return collection


def _full_params(front):
    P = _params(front)
    P["y_mount"] = float(_Dish(P).B(0.0))                  # hub mounting face
    return P


def _mesh(part, P, builder, col):
    """Mesh datablock for one part of one axle, built once and shared left/right."""
    name = "%s%s_%s" % (PREFIX, part, P["tag"])
    me = bpy.data.meshes.get(name)
    if me is None:
        obj = builder(P, col)
        me = obj.data
        me.name = name
        bpy.data.objects.remove(obj, do_unlink=True)
    return me


def build_single(position="FL", collection=None):
    """Build one corner; returns its root empty WHL_<position>."""
    col = _collection(collection)
    w = spec.WHEELS[position]
    front, side = bool(w["front"]), int(w["side"])
    P = _full_params(front)
    root = util.empty(PREFIX + position, (w["x"], w["y"], w["z"]), col, size=0.30)
    spin = util.empty("%s%s_Spin" % (PREFIX, position), (0, 0, 0), col, size=0.22, kind='ARROWS')
    spin.parent = root
    rot_spin = (0.0, 0.0, 0.0) if side > 0 else (0.0, 0.0, PI)
    for part, builder in _SPIN_PARTS:
        ob = bpy.data.objects.new("%s%s_%s" % (PREFIX, position, part), _mesh(part, P, builder, col))
        col.objects.link(ob)
        ob.parent = spin
        ob.rotation_euler = rot_spin
    # static parts are built at 9 o'clock (-X), outboard +Y, symmetric top/bottom
    rot_static = {(True, 1): (0.0, 0.0, 0.0), (True, -1): (PI, 0.0, 0.0),
                  (False, 1): (0.0, PI, 0.0), (False, -1): (0.0, 0.0, PI)}[(front, side)]
    for part, builder in _STATIC_PARTS:
        ob = bpy.data.objects.new("%s%s_%s" % (PREFIX, position, part), _mesh(part, P, builder, col))
        col.objects.link(ob)
        ob.parent = root
        ob.rotation_euler = rot_static
    bpy.context.view_layer.update()
    return root


def build(collection=None):
    """Build all four wheels -> {"FL": WHL_FL, "FR": WHL_FR, "RL": WHL_RL, "RR": WHL_RR}."""
    col = _collection(collection)
    return {p: build_single(p, col) for p in ("FL", "FR", "RL", "RR")}
