"""Shared Blender helpers used by every module (Blender 5.2 / bpy).

Conventions: metres, +X forward, +Y left, +Z up (see spec.py).
Nothing here depends on a UI context, so it all works headless.
"""
import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix


# ------------------------------------------------------------------ scene
def reset_scene():
    """Empty file: no objects, meshes, materials, lights, cameras, collections."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    return scene


def get_collection(name, parent=None):
    """Get or create a collection linked under `parent` (default: scene root)."""
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def link(obj, collection):
    """Link obj to `collection` only (name or Collection)."""
    if isinstance(collection, str):
        collection = get_collection(collection)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def parent(child, par, keep_world=True):
    """Parent without moving the child in world space."""
    if keep_world:
        bpy.context.view_layer.update()
        mw = child.matrix_world.copy()
        child.parent = par
        child.matrix_parent_inverse = par.matrix_world.inverted()
        child.matrix_world = mw
    else:
        child.parent = par
    return child


def empty(name, location=(0, 0, 0), collection=None, size=0.1, kind='PLAIN_AXES'):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    e.location = location
    (get_collection(collection) if isinstance(collection, str) else
     (collection or bpy.context.scene.collection)).objects.link(e)
    return e


# ------------------------------------------------------------------ mesh creation
def mesh_object(name, verts, faces, collection=None, material=None, smooth=True, edges=()):
    """Create a mesh object from python/numpy vert + face lists."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], list(edges), [tuple(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    obj = bpy.data.objects.new(name, me)
    (get_collection(collection) if isinstance(collection, str) else
     (collection or bpy.context.scene.collection)).objects.link(obj)
    if smooth:
        shade_smooth(obj)
    if material is not None:
        set_material(obj, material)
    return obj


def bmesh_object(name, bm, collection=None, material=None, smooth=True):
    """Create an object from a bmesh (frees the bmesh)."""
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    (get_collection(collection) if isinstance(collection, str) else
     (collection or bpy.context.scene.collection)).objects.link(obj)
    if smooth:
        shade_smooth(obj)
    if material is not None:
        set_material(obj, material)
    return obj


def shade_smooth(obj, angle_deg=None):
    """Smooth shading; with angle_deg, edges sharper than that stay hard."""
    me = obj.data
    me.shade_smooth()
    if angle_deg is not None:
        me.set_sharp_from_angle(angle=math.radians(angle_deg))
    return obj


def set_material(obj, mat, slot=None):
    """Assign material (Material or name). slot=None -> single material for all faces."""
    if isinstance(mat, str):
        from . import materials
        mat = materials.get(mat)
    mats = obj.data.materials
    if slot is None:
        mats.clear()
        mats.append(mat)
        return 0
    while len(mats) <= slot:
        mats.append(None)
    mats[slot] = mat
    return slot


def add_material_slot(obj, mat):
    """Append a material, return its slot index (reuses an existing slot)."""
    if isinstance(mat, str):
        from . import materials
        mat = materials.get(mat)
    for i, m in enumerate(obj.data.materials):
        if m == mat:
            return i
    obj.data.materials.append(mat)
    return len(obj.data.materials) - 1


def recalc_normals(obj, inside=False):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if inside:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def weld(obj, dist=1e-5):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def join(objs, name=None):
    """Join mesh objects into the first one (keeps materials)."""
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    if len(objs) == 1:
        if name:
            objs[0].name = name
        return objs[0]
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs,
                                   selected_objects=objs, object=objs[0]):
        bpy.ops.object.join()
    if name:
        objs[0].name = name
        objs[0].data.name = name
    return objs[0]


def duplicate(obj, name=None, linked=False, collection=None):
    new = obj.copy()
    if not linked and obj.data is not None:
        new.data = obj.data.copy()
    if name:
        new.name = name
    cols = [get_collection(collection)] if isinstance(collection, str) else (
        [collection] if collection else list(obj.users_collection))
    for c in cols:
        c.objects.link(new)
    return new


def delete(obj):
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and data.users == 0 and isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)


# ------------------------------------------------------------------ modifiers
def subsurf(obj, levels=2, render_levels=None, name="Subsurf"):
    m = obj.modifiers.new(name, 'SUBSURF')
    m.levels = levels
    m.render_levels = levels if render_levels is None else render_levels
    return m


def solidify(obj, thickness, offset=-1.0, even=True, name="Solidify"):
    m = obj.modifiers.new(name, 'SOLIDIFY')
    m.thickness = thickness
    m.offset = offset
    m.use_even_offset = even
    m.use_quality_normals = True
    return m


def bevel(obj, width, segments=2, angle_deg=30.0, name="Bevel", harden=True):
    m = obj.modifiers.new(name, 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle_deg)
    m.harden_normals = harden
    return m


def mirror_y(obj, name="Mirror", merge=True, merge_dist=1e-4):
    """Mirror across the car centre plane (Y=0) using the object's own origin (keep origin on Y=0)."""
    m = obj.modifiers.new(name, 'MIRROR')
    m.use_axis = (False, True, False)
    m.use_clip = True
    m.use_mirror_merge = merge
    m.merge_threshold = merge_dist
    return m


def weighted_normals(obj, name="WeightedNormal", keep_sharp=True):
    m = obj.modifiers.new(name, 'WEIGHTED_NORMAL')
    m.keep_sharp = keep_sharp
    m.weight = 50
    return m


def apply_modifiers(obj):
    """Bake the whole modifier stack into the mesh (headless safe)."""
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = obj.evaluated_get(dg)
    new_me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    old = obj.data
    obj.modifiers.clear()
    obj.data = new_me
    new_me.name = old.name
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj


def boolean(obj, cutter, op='DIFFERENCE', solver='EXACT', apply=True, hide_cutter=True, name="Bool"):
    """Boolean obj with cutter. op: DIFFERENCE | UNION | INTERSECT. solver: EXACT | FLOAT | MANIFOLD."""
    m = obj.modifiers.new(name, 'BOOLEAN')
    m.operation = op
    m.solver = solver
    m.object = cutter
    if apply:
        apply_modifiers(obj)
    if hide_cutter:
        cutter.hide_render = True
        cutter.hide_viewport = True
    return obj


# ------------------------------------------------------------------ curves / math
def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


class Curve1D:
    """Smooth 1-D guide curve y(x) through control points (monotone cubic / PCHIP, C1).

    PCHIP never overshoots between control points, which keeps body guide
    curves well behaved.  Call it with scalars or numpy arrays.
    """

    def __init__(self, pts):
        pts = sorted((float(a), float(b)) for a, b in pts)
        self.x = np.array([p[0] for p in pts])
        self.y = np.array([p[1] for p in pts])
        from scipy.interpolate import PchipInterpolator
        self._f = PchipInterpolator(self.x, self.y, extrapolate=True)

    def __call__(self, x):
        x = np.clip(x, self.x[0], self.x[-1])
        return self._f(x)

    def d(self, x):
        x = np.clip(x, self.x[0], self.x[-1])
        return self._f.derivative()(x)


def catmull_rom(points, samples_per_seg=12, closed=False):
    """Centripetal Catmull-Rom through 2D/3D points -> (N, dim) array."""
    P = [np.asarray(p, float) for p in points]
    n = len(P)
    if n < 2:
        return np.array(P)
    if closed:
        ext = [P[-1]] + P + [P[0], P[1]]
        segs = n
    else:
        ext = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
        segs = n - 1
    out = []
    for i in range(segs):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        t0 = 0.0
        t1 = t0 + max(np.linalg.norm(p1 - p0) ** 0.5, 1e-6)
        t2 = t1 + max(np.linalg.norm(p2 - p1) ** 0.5, 1e-6)
        t3 = t2 + max(np.linalg.norm(p3 - p2) ** 0.5, 1e-6)
        for t in np.linspace(t1, t2, samples_per_seg, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    if not closed:
        out.append(P[-1])
    return np.array(out)


def resample_polyline(pts, n, closed=False):
    """Resample a polyline to n points evenly spaced by arc length."""
    pts = np.asarray(pts, float)
    if closed:
        pts = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n, endpoint=not closed)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(pts.shape[1])], axis=1)


def superellipse(a, b, n=4.0, count=48):
    """Closed superellipse outline (count points) in 2D, CCW starting at +x."""
    t = np.linspace(0, 2 * math.pi, count, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    x = a * np.sign(c) * np.abs(c) ** (2.0 / n)
    y = b * np.sign(s) * np.abs(s) ** (2.0 / n)
    return np.stack([x, y], axis=1)


def rounded_rect(w, h, r, seg=6):
    """Closed rounded rectangle outline centred on origin, CCW."""
    r = min(r, w / 2 - 1e-6, h / 2 - 1e-6)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90.0 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


# ------------------------------------------------------------------ surface builders
def grid_faces(nu, nv, closed_u=False, closed_v=False, flip=False):
    """Quad faces for an (nu x nv) vertex grid stored row-major (index = u*nv + v)."""
    faces = []
    for u in range(nu if closed_u else nu - 1):
        u1 = (u + 1) % nu
        for v in range(nv if closed_v else nv - 1):
            v1 = (v + 1) % nv
            q = (u * nv + v, u1 * nv + v, u1 * nv + v1, u * nv + v1)
            faces.append(q[::-1] if flip else q)
    return faces


def loft(sections, closed_v=False, closed_u=False, cap_start=False, cap_end=False, flip=False):
    """Loft a list of equally-sized point rings/rows -> (verts, faces).

    sections: array-like (nu, nv, 3).  closed_v closes each section into a ring.
    Caps are n-gon fans built on the first/last section (needs closed_v).
    """
    S = np.asarray(sections, float)
    nu, nv, _ = S.shape
    verts = S.reshape(-1, 3).tolist()
    faces = grid_faces(nu, nv, closed_u=closed_u, closed_v=closed_v, flip=flip)
    if cap_start:
        ring = list(range(nv))
        faces.append(tuple(ring if flip else ring[::-1]))
    if cap_end:
        ring = list(range((nu - 1) * nv, nu * nv))
        faces.append(tuple(ring[::-1] if flip else ring))
    return verts, faces


def lathe(profile, segments=48, axis='Y', angle=2 * math.pi, origin=(0, 0, 0)):
    """Revolve a 2D profile [(radius, along_axis), ...] around an axis -> (verts, faces).

    axis 'Y' is the wheel-axle direction (lateral), 'X' longitudinal, 'Z' vertical.
    """
    prof = np.asarray(profile, float)
    full = abs(angle - 2 * math.pi) < 1e-6
    n = segments if full else segments + 1
    secs = []
    for i in range(n):
        a = angle * i / segments
        c, s = math.cos(a), math.sin(a)
        ring = []
        for r, h in prof:
            if axis == 'Y':
                ring.append((origin[0] + r * c, origin[1] + h, origin[2] + r * s))
            elif axis == 'X':
                ring.append((origin[0] + h, origin[1] + r * c, origin[2] + r * s))
            else:
                ring.append((origin[0] + r * c, origin[1] + r * s, origin[2] + h))
        secs.append(ring)
    return loft(secs, closed_u=full, closed_v=False)


def _frames_along(path, closed=False, up=(0, 0, 1)):
    """Rotation-minimising frames along a 3D polyline -> list of (T, N, B)."""
    P = np.asarray(path, float)
    n = len(P)
    T = np.zeros_like(P)
    for i in range(n):
        a = P[(i - 1) % n] if (closed or i > 0) else P[i]
        b = P[(i + 1) % n] if (closed or i < n - 1) else P[i]
        t = b - a
        T[i] = t / (np.linalg.norm(t) + 1e-12)
    upv = np.asarray(up, float)
    n0 = upv - T[0] * np.dot(upv, T[0])
    if np.linalg.norm(n0) < 1e-6:
        n0 = np.cross(T[0], (1, 0, 0))
    n0 /= np.linalg.norm(n0)
    N = [n0]
    for i in range(1, n):
        v = N[-1] - T[i] * np.dot(N[-1], T[i])
        N.append(v / (np.linalg.norm(v) + 1e-12))
    N = np.array(N)
    B = np.cross(T, N)
    return T, N, B


def sweep(profile2d, path, closed_path=False, closed_profile=True, up=(0, 0, 1),
          scales=None, caps=True):
    """Sweep a 2D profile (in the N,B plane) along a 3D path -> (verts, faces).

    profile2d: [(n, b), ...]; n is along the frame 'up' direction, b sideways.
    scales: optional per-path-point scale (scalar or (sn, sb)).
    """
    P = np.asarray(path, float)
    prof = np.asarray(profile2d, float)
    T, N, B = _frames_along(P, closed=closed_path, up=up)
    secs = []
    for i in range(len(P)):
        sc = (1.0, 1.0)
        if scales is not None:
            s = scales[i]
            sc = (s, s) if np.isscalar(s) else s
        secs.append([P[i] + N[i] * (pn * sc[0]) + B[i] * (pb * sc[1]) for pn, pb in prof])
    return loft(secs, closed_v=closed_profile, closed_u=closed_path,
                cap_start=caps and closed_profile and not closed_path,
                cap_end=caps and closed_profile and not closed_path)


def tube(path, radius, segments=12, closed_path=False, caps=True, radii=None):
    """Round tube along a path. radii: optional per-point radius."""
    circ = [(math.cos(2 * math.pi * i / segments), math.sin(2 * math.pi * i / segments))
            for i in range(segments)]
    sc = [radius] * len(path) if radii is None else list(radii)
    return sweep(circ, path, closed_path=closed_path, closed_profile=True, scales=sc, caps=caps)


def extrude_outline(outline2d, depth, plane='XZ', offset=0.0, both=False):
    """Extrude a closed 2D outline into a prism -> (verts, faces) (a closed boolean cutter).

    plane 'XZ': outline (x, z) extruded along Y from offset to offset+depth
    plane 'XY': outline (x, y) extruded along Z;  plane 'YZ': outline (y, z) along X.
    both=True centres the extrusion on `offset`.
    """
    O = np.asarray(outline2d, float)
    a, b = (offset - depth / 2, offset + depth / 2) if both else (offset, offset + depth)
    def pt(p, w):
        if plane == 'XZ':
            return (p[0], w, p[1])
        if plane == 'XY':
            return (p[0], p[1], w)
        return (w, p[0], p[1])
    n = len(O)
    verts = [pt(p, a) for p in O] + [pt(p, b) for p in O]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    faces.append(tuple(range(n))[::-1])
    faces.append(tuple(range(n, 2 * n)))
    return verts, faces


def prism_cutter(name, outline2d, depth, plane='XZ', offset=0.0, both=False, collection=None):
    """A closed prism object ready to use as a boolean cutter (normals fixed, hidden from render)."""
    v, f = extrude_outline(outline2d, depth, plane=plane, offset=offset, both=both)
    o = mesh_object(name, v, f, collection=collection, smooth=False)
    recalc_normals(o)
    o.hide_render = True
    o.display_type = 'WIRE'
    return o


def box(name, size, location=(0, 0, 0), collection=None, material=None, bevel_w=0.0, segs=2):
    """Axis-aligned box (optionally bevelled)."""
    sx, sy, sz = (s / 2 for s in size)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    if bevel_w > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel_w, segments=segs, affect='EDGES', profile=0.5)
    o = bmesh_object(name, bm, collection=collection, material=material, smooth=bevel_w > 0)
    if bevel_w > 0:
        shade_smooth(o, 40)
    o.location = location
    return o


def cylinder(name, radius, depth, axis='Y', location=(0, 0, 0), segments=48, collection=None,
             material=None, bevel_w=0.0, cap=True):
    """Cylinder along X/Y/Z, centred on `location`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    if axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    elif axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    if bevel_w > 0:
        sharp = [e for e in bm.edges if e.calc_face_angle(0) > math.radians(60)]
        bmesh.ops.bevel(bm, geom=sharp, offset=bevel_w, segments=2, affect='EDGES', profile=0.5)
    o = bmesh_object(name, bm, collection=collection, material=material)
    shade_smooth(o, 40)
    o.location = location
    return o


# ------------------------------------------------------------------ misc geometry
def bounds(objs):
    """World-space AABB (min, max) of one or many objects."""
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    bpy.context.view_layer.update()
    pts = []
    for o in objs:
        if o.type != 'MESH':
            continue
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    a = np.array([tuple(p) for p in pts])
    return a.min(0), a.max(0)


def look_at(obj, target, roll=0.0):
    """Point obj's -Z (camera/light direction) at target."""
    d = Vector(target) - obj.location
    q = d.to_track_quat('-Z', 'Y')
    obj.rotation_euler = (q.to_matrix().to_4x4() @ Matrix.Rotation(roll, 4, 'Z')).to_euler()
    return obj


def set_origin(obj, point):
    """Move the object's origin to a world point without moving the geometry."""
    bpy.context.view_layer.update()
    p = Vector(point)
    local = obj.matrix_world.inverted() @ p
    obj.data.transform(Matrix.Translation(-local))
    obj.matrix_world = obj.matrix_world @ Matrix.Translation(local)
    obj.data.update()
    return obj


def tri_count(objs=None):
    """Evaluated triangle count of objects (default: everything in the scene)."""
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in (objs or bpy.context.scene.objects):
        if o.type == 'MESH':
            me = o.evaluated_get(dg).data
            n += sum(len(p.vertices) - 2 for p in me.polygons)
    return n
