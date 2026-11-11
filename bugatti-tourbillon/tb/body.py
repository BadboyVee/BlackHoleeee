"""Body: master surfaces -> trimmed skins -> real panels, glass and doors.

Pipeline
    1. surface.py cages -> dense Catmull-Clark skins (hull outer, hull inner, canopy)
    2. hull and canopy are trimmed against each other (the canopy sits in a hole in the hull)
    3. wheel arches are cut
    4. every panel is the skin intersected with a prism drawn from the blueprint shut lines
       (regions are shrunk / grown by half a panel gap, so there are real 4 mm gaps)
    5. panels get thickness (solidify) and a small edge bevel that catches highlights

build() returns a dict of the objects; doors hang on hinge empties ready for the rig.
"""
import math
import numpy as np
import bpy
import bmesh
from shapely.geometry import Polygon
from . import spec, util, materials, surface

GAP = 0.004           # panel gap
PREFIX = "BODY_"
_TAG = "TB__CUT"


# ------------------------------------------------------------------ helpers
def _tag_mat():
    m = bpy.data.materials.get(_TAG)
    if m is None:
        m = bpy.data.materials.new(_TAG)
    return m


def _work():
    c = bpy.data.collections.get("TB__Work")
    if c is None:
        c = bpy.data.collections.new("TB__Work")
        bpy.context.scene.collection.children.link(c)
    return c


def _dense(name, verts, faces, levels=2):
    o = util.mesh_object(name, verts, faces, collection=_work(), smooth=True)
    util.recalc_normals(o)
    util.subsurf(o, levels)
    util.apply_modifiers(o)
    o.data.materials.clear()
    o.data.materials.append(materials.get("paint_light"))
    return o


def _all_tag(obj):
    """Copy of obj whose faces all carry the tag material (used as a cutter)."""
    c = util.duplicate(obj, obj.name + "_cut", collection=_work())
    c.data.materials.clear()
    c.data.materials.append(_tag_mat())
    for p in c.data.polygons:
        p.material_index = 0
    return c


def _drop_tagged(obj):
    """Delete faces that came from a cutter (tag material), then drop the slot."""
    me = obj.data
    idx = [i for i, m in enumerate(me.materials) if m is not None and m.name == _TAG]
    if idx:
        bm = bmesh.new()
        bm.from_mesh(me)
        dead = [f for f in bm.faces if f.material_index in idx]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context='FACES')
        bm.to_mesh(me)
        bm.free()
        # remove the tag slots (highest first) and re-index
        for i in sorted(idx, reverse=True):
            me.materials.pop(index=i)
        me.update()
    return obj


def _bool(obj, cutter, op, solver='EXACT'):
    m = obj.modifiers.new("b", 'BOOLEAN')
    m.operation = op
    m.solver = solver
    m.material_mode = 'TRANSFER'
    m.object = cutter
    util.apply_modifiers(obj)
    return _drop_tagged(obj)


def _piece(src, name, keep=(), drop=(), collection=None):
    """New object = src intersected with every cutter in `keep`, minus every cutter in `drop`."""
    o = util.duplicate(src, name, collection=collection or _work())
    for c in keep:
        _bool(o, c, 'INTERSECT')
    for c in drop:
        _bool(o, c, 'DIFFERENCE')
    o.data.name = name
    return o


def _offset(poly, d):
    """Offset a closed 2D outline by d (>0 grows) with round joins."""
    g = Polygon(poly).buffer(0)
    g = g.buffer(d, join_style=1, resolution=6)
    if g.geom_type == 'MultiPolygon':
        g = max(g.geoms, key=lambda a: a.area)
    return np.array(g.exterior.coords)[:-1]


def _prism(name, outline, plane, a, b, grow=0.0):
    """Closed tagged prism between coordinates a and b along the plane normal."""
    o2 = _offset(outline, grow) if abs(grow) > 1e-9 else np.asarray(outline, float)
    v, f = util.extrude_outline(o2, b - a, plane=plane, offset=a)
    o = util.mesh_object(name, v, f, collection=_work(), smooth=False)
    util.recalc_normals(o)
    o.data.materials.append(_tag_mat())
    o.hide_render = True
    return o


def _cyl(name, radius, y0, y1, centre, seg=96):
    """Tagged cylinder along Y (wheel-arch cutter)."""
    ang = np.linspace(0, 2 * math.pi, seg, endpoint=False)
    ring = np.stack([centre[0] + radius * np.cos(ang), centre[1] + radius * np.sin(ang)], axis=1)
    return _prism(name, ring, 'XZ', y0, y1)


def _finish(obj, mat, thickness=0.006, bevel=0.0012, collection=None, glass=False):
    """Material + thickness + edge bevel."""
    util.set_material(obj, mat)
    util.weld(obj, 1e-5)
    util.shade_smooth(obj)
    if thickness:
        util.solidify(obj, thickness, offset=-1.0)
    if bevel and not glass:
        util.bevel(obj, bevel, segments=2, angle_deg=40)
    if collection is not None:
        util.link(obj, collection)
    return obj


def _empty_ok(obj):
    return obj is not None and len(obj.data.polygons) > 0


# ------------------------------------------------------------------ blueprint lines (side view, x-z)
def _cr(pts, per=10):
    return util.catmull_rom(pts, per, closed=False)


def lines():
    """Shared shut lines as dense polylines (x, z) so neighbouring panels use identical edges."""
    c_up = _cr([(0.60, 1.045), (0.30, 1.095), (0.00, 1.108), (-0.30, 1.098), (-0.50, 1.070)])
    c_arc = _cr([(-0.50, 1.070), (-0.64, 1.020), (-0.715, 0.945), (-0.70, 0.860), (-0.61, 0.770),
                 (-0.45, 0.680), (-0.25, 0.590), (-0.05, 0.515)])
    c_low = _cr([(-0.05, 0.515), (0.20, 0.465), (0.50, 0.435), (0.80, 0.415), (0.955, 0.405)])
    front = _cr([(0.955, 0.405), (0.932, 0.50), (0.930, 0.62), (0.970, 0.74), (1.040, 0.82), (1.020, 0.875)])
    pillar = _cr([(1.020, 0.875), (0.85, 0.957), (0.70, 1.022), (0.60, 1.045)])
    rear_cut = _cr([(-0.50, 1.070), (-0.36, 0.86), (-0.20, 0.60), (-0.05, 0.515)])
    return dict(c_up=c_up, c_arc=c_arc, c_low=c_low, front=front, pillar=pillar, rear_cut=rear_cut)


def regions():
    """Closed side-view regions built from the shared lines."""
    L = lines()
    cat = lambda *a: np.concatenate([x[:-1] for x in a])
    # whole C interior: upper branch (front->rear), rear arc, lower branch, front cut, A-pillar
    c_reg = cat(L['c_up'], L['c_arc'], L['c_low'], L['front'], L['pillar'])
    # door: front cut + pillar, over the roof, down the rear cut, forward along the lower branch
    over = np.array([(0.60, 1.045), (0.56, 1.40), (-0.47, 1.40), (-0.50, 1.070)])
    door = cat(L['front'], L['pillar'], over, L['rear_cut'], L['c_low'])
    # everything forward of the door front cut
    fwd = np.concatenate([L['front'], [(1.02, 1.6), (3.2, 1.6), (3.2, -0.3), (0.955, -0.3)]])
    # sill: below the lower branch, between the wheel arches
    sill = np.concatenate([[(-0.93, 0.44), (-0.50, 0.47)], L['c_low'], [(0.955, -0.3), (-0.93, -0.3)]])
    # side glass (inside the door, set in from its edges)
    glass = np.array([(0.955, 0.70), (0.955, 0.870), (0.82, 0.935), (0.68, 0.998), (0.56, 1.045), (0.30, 1.078),
                      (0.00, 1.092), (-0.28, 1.082), (-0.43, 1.050), (-0.40, 0.97), (-0.335, 0.86), (-0.30, 0.70)])
    glass = util.catmull_rom(glass, 6, closed=True)
    return dict(c=c_reg, door=door, fwd=fwd, sill=sill, glass=glass)


def plan_regions():
    """Plan-view (x, y) outlines on the +Y side; mirrored for the other side."""
    def mir(h):
        h = np.asarray(h, float)
        return np.concatenate([h, h[::-1][1:-1] * np.array([1, -1])])
    ws = mir(_cr([(1.40, 0.0), (1.375, 0.20), (1.31, 0.40), (1.20, 0.545), (1.06, 0.605), (0.90, 0.585),
                  (0.74, 0.548), (0.635, 0.510), (0.615, 0.30), (0.615, 0.0)], 8))
    roof = util.catmull_rom([(0.545, 0.13), (0.545, 0.455), (0.30, 0.492), (-0.10, 0.492), (-0.40, 0.44),
                             (-0.425, 0.31), (-0.22, 0.13)], 6, closed=True)
    rear = util.catmull_rom([(-0.80, 0.07), (-0.80, 0.37), (-1.15, 0.385), (-1.62, 0.33), (-1.66, 0.20),
                             (-1.66, 0.07)], 6, closed=True)
    return dict(ws=ws, roof=roof, rear=rear)


# ------------------------------------------------------------------ masters
def masters():
    """Dense trimmed skins: (hull_outer, hull_inner, canopy)."""
    xs, cage = surface.hull_cage()
    v, f = util.loft(cage, closed_v=True, cap_start=True, cap_end=True)
    hull = _dense("M_HullOuter", v, f)
    xs, cage = surface.hull_cage(inner=True)
    v, f = util.loft(cage, closed_v=True, cap_start=True, cap_end=True)
    hull_in = _dense("M_HullInner", v, f)

    xs2, cc = surface.canopy_cage()
    v, f = util.loft(cc, closed_v=False)
    can = _dense("M_Canopy", v, f)
    # close the canopy into a solid with a keel reaching deep into the hull
    bm = bmesh.new()
    bm.from_mesh(can.data)
    be = [e for e in bm.edges if e.is_boundary]
    r = bmesh.ops.extrude_edge_only(bm, edges=be)
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    for vv in nv:
        vv.co.z = 0.45
    bm.edges.ensure_lookup_table()
    be2 = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=be2, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(can.data)
    bm.free()
    can.data.update()

    can_cut = _all_tag(can)
    hull_cut = _all_tag(hull)
    _bool(hull, can_cut, 'DIFFERENCE')
    _bool(hull_in, can_cut, 'DIFFERENCE')
    _bool(can, hull_cut, 'DIFFERENCE')
    for o in (can_cut, hull_cut):
        util.delete(o)
    return hull, hull_in, can


# ------------------------------------------------------------------ build
def build(collection=None, keep_work=False):
    col_body = collection or util.get_collection(spec.COLLECTIONS["body"])
    col_glass = util.get_collection(spec.COLLECTIONS["glass"])
    col_doors = util.get_collection(spec.COLLECTIONS["doors"])
    out = {}
    hull, hull_in, can = masters()

    # ---- wheel arches
    for key, w in spec.WHEELS.items():
        r = spec.FRONT_ARCH_RADIUS if w["front"] else spec.REAR_ARCH_RADIUS
        y0, y1 = (0.50, 1.4) if w["side"] > 0 else (-1.4, -0.50)
        c = _cyl("cut_arch_" + key, r, y0, y1, (w["x"], w["z"]))
        _bool(hull, c, 'DIFFERENCE')
        _bool(hull_in, c, 'DIFFERENCE')
        util.delete(c)

    R = regions()
    P = plan_regions()
    g = GAP / 2

    def side(name, outline, s, grow=0.0, y_in=0.30):
        a, b = (y_in, 1.5) if s > 0 else (-1.5, -y_in)
        return _prism(name, outline, 'XZ', a, b, grow=grow)

    def plan(name, outline, s=0, grow=0.0):
        o = np.asarray(outline, float)
        if s < 0:
            o = o * np.array([1, -1])
        return _prism(name, o, 'XY', 0.4, 1.6, grow=grow)

    doors = {}
    for s, sn in ((+1, "L"), (-1, "R")):
        c_in = side("c_in", R['c'], s, -g)
        c_out = side("c_out", R['c'], s, +g)
        d_in = side("d_in", R['door'], s, -g, y_in=0.13)
        d_out = side("d_out", R['door'], s, +g, y_in=0.13)
        gl_in = side("gl_in", R['glass'], s, 0.0, y_in=0.50)
        gl_out = side("gl_out", R['glass'], s, +g, y_in=0.50)
        rf_in = plan("rf_in", P['roof'], s, 0.0)
        rf_out = plan("rf_out", P['roof'], s, +g)

        # hull parts inside the C-line (recessed inner surface)
        door_skin = _piece(hull_in, PREFIX + "Door_%s_Skin" % sn, keep=(c_in, d_in))
        quarter = _piece(hull_in, PREFIX + "Quarter_%s" % sn, keep=(c_in,), drop=(d_out,))
        # canopy parts
        side_glass = _piece(can, PREFIX + "Door_%s_Glass" % sn, keep=(d_in, gl_in))
        roof_glass = _piece(can, PREFIX + "Door_%s_RoofGlass" % sn, keep=(d_in, rf_in))
        door_frame = _piece(can, PREFIX + "Door_%s_Frame" % sn, keep=(d_in,), drop=(gl_out, rf_out))
        island = _piece(can, PREFIX + "Island_%s" % sn, keep=(c_in,), drop=(d_out,))

        # everything else loses this side's C region and door
        _bool(hull, c_out, 'DIFFERENCE')
        _bool(can, d_out, 'DIFFERENCE')
        _bool(can, c_out, 'DIFFERENCE')

        _finish(door_skin, "paint_light", collection=col_doors)
        _finish(door_frame, "paint_dark", collection=col_doors)
        _finish(side_glass, "glass_tint", 0.004, collection=col_doors, glass=True)
        _finish(roof_glass, "glass_dark", 0.004, collection=col_doors, glass=True)
        _finish(quarter, "paint_light", collection=col_body)
        _finish(island, "paint_light", collection=col_body)
        doors[sn] = [door_skin, door_frame, side_glass, roof_glass]
        out["quarter_" + sn] = quarter
        out["island_" + sn] = island
        for c in (c_in, c_out, d_in, d_out, gl_in, gl_out, rf_in, rf_out):
            util.delete(c)

    # ---- canopy: windshield, engine-cover glass, frame
    ws_in = plan("ws_in", P['ws'])
    ws_out = plan("ws_out", P['ws'], grow=+g)
    windshield = _piece(can, PREFIX + "Windshield", keep=(ws_in,))
    _bool(can, ws_out, 'DIFFERENCE')
    _finish(windshield, "glass_tint", 0.005, collection=col_glass, glass=True)
    out["windshield"] = windshield
    for s, sn in ((+1, "L"), (-1, "R")):
        rg_in = plan("rg_in", P['rear'], s)
        rg_out = plan("rg_out", P['rear'], s, grow=+g)
        rg = _piece(can, PREFIX + "EngineGlass_%s" % sn, keep=(rg_in,))
        _bool(can, rg_out, 'DIFFERENCE')
        _finish(rg, "glass_dark", 0.004, collection=col_glass, glass=True)
        out["engine_glass_" + sn] = rg
        util.delete(rg_in); util.delete(rg_out)
    can.name = PREFIX + "CanopyFrame"
    _finish(can, "paint_dark", collection=col_body)
    out["canopy_frame"] = can
    util.delete(ws_in); util.delete(ws_out)

    # ---- hull: front clam / sills / rear clam
    fwd_in = _prism("fwd_in", R['fwd'], 'XZ', -1.5, 1.5, grow=-g)
    fwd_out = _prism("fwd_out", R['fwd'], 'XZ', -1.5, 1.5, grow=+g)
    front = _piece(hull, PREFIX + "FrontClam", keep=(fwd_in,))
    _bool(hull, fwd_out, 'DIFFERENCE')
    sills = []
    for s, sn in ((+1, "L"), (-1, "R")):
        s_in = side("s_in", R['sill'], s, -g, y_in=0.45)
        s_out = side("s_out", R['sill'], s, +g, y_in=0.45)
        sill = _piece(hull, PREFIX + "Sill_%s" % sn, keep=(s_in,))
        _bool(hull, s_out, 'DIFFERENCE')
        _finish(sill, "carbon_gloss", collection=col_body)
        out["sill_" + sn] = sill
        util.delete(s_in); util.delete(s_out)
    hull.name = PREFIX + "RearClam"
    _finish(front, "paint_light", collection=col_body)
    _finish(hull, "paint_dark", collection=col_body)
    out["front_clam"] = front
    out["rear_clam"] = hull
    util.delete(fwd_in); util.delete(fwd_out)

    # ---- doors on hinges
    for s, sn in ((+1, "L"), (-1, "R")):
        hx, hy, hz = spec.DOOR["hinge"]
        hinge = util.empty(PREFIX + "DoorHinge_" + sn, (hx, s * hy, hz), collection=col_doors, size=0.15)
        ax = np.array(spec.DOOR["hinge_axis"], float) * np.array([1, s, 1])
        hinge["axis"] = [float(a) for a in ax / np.linalg.norm(ax)]
        for o in doors[sn]:
            util.parent(o, hinge)
        out["door_hinge_" + sn] = hinge
        out["door_" + sn] = doors[sn]

    util.delete(hull_in)
    if not keep_work:
        w = bpy.data.collections.get("TB__Work")
        if w is not None and len(w.objects) == 0:
            bpy.data.collections.remove(w)
    return out
