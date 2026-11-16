"""Shared Blender (bpy) helpers: scene reset, PBR materials from Poly Haven
textures, a UV-aware mesh builder, asset library instancing, world and render
setup.  Units are metres, Z up.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ph  # noqa: E402

TEX_RES = os.environ.get("TEX_RES", "2k")
MODEL_RES = os.environ.get("MODEL_RES", "1k")


# ----------------------------------------------------------------- scene ---
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    return s


def coll(name, parent=None, hide=False):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    if hide:
        c.hide_render = True
        c.hide_viewport = True
    return c


def link(obj, c):
    for u in list(obj.users_collection):
        u.objects.unlink(obj)
    c.objects.link(obj)
    return obj


# ------------------------------------------------------------- materials ---
_mats = {}


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    return m, nt, b, out


def _img(path, colorspace="sRGB"):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = colorspace
    return im


def mat_plain(name, color, rough=0.5, metal=0.0, spec=0.5, emit=None, emit_strength=0.0,
              coat=0.0, alpha=1.0, transmission=0.0, ior=1.45):
    if name in _mats:
        return _mats[name]
    m, nt, b, _ = _new(name)
    c = tuple(color) + (1.0,) if len(color) == 3 else tuple(color)
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.03
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["IOR"].default_value = ior
    if emit is not None:
        b.inputs["Emission Color"].default_value = tuple(emit) + (1.0,)
        b.inputs["Emission Strength"].default_value = emit_strength
    m.diffuse_color = c
    _mats[name] = m
    return m


def mat_pbr(name, tex, size=1.0, tint=None, sat=1.0, val=1.0, rough_mul=1.0, rough_add=0.0,
            normal=1.0, metal=0.0, res=None, rot=0.0, size_y=None, coat=0.0, hue=0.5,
            use_alpha=False, ramp=None):
    """Material from a Poly Haven texture set. `size` = metres covered by one tile
    (UVs made by the mesh builder are in metres)."""
    if name in _mats:
        return _mats[name]
    t = ph.texture(tex, res or TEX_RES)
    m, nt, b, _ = _new(name)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / size, 1.0 / (size_y or size), 1.0)
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    L.new(tc.outputs["UV"], mp.inputs[0])
    if "diff" in t:
        d = N.new("ShaderNodeTexImage")
        d.image = _img(t["diff"])
        L.new(mp.outputs[0], d.inputs[0])
        col = d.outputs[0]
    else:
        d = N.new("ShaderNodeRGB")
        d.outputs[0].default_value = (0.8, 0.8, 0.8, 1)
        col = d.outputs[0]
    if sat != 1.0 or val != 1.0 or hue != 0.5:
        h = N.new("ShaderNodeHueSaturation")
        h.inputs["Hue"].default_value = hue
        h.inputs["Saturation"].default_value = sat
        h.inputs["Value"].default_value = val
        L.new(col, h.inputs["Color"])
        col = h.outputs[0]
    if ramp is not None:
        bw = N.new("ShaderNodeRGBToBW")
        L.new(col, bw.inputs[0])
        cr = N.new("ShaderNodeValToRGB")
        n = len(ramp)
        while len(cr.color_ramp.elements) < n:
            cr.color_ramp.elements.new(0.5)
        for i, (pos, c) in enumerate(ramp):
            cr.color_ramp.elements[i].position = pos
            cr.color_ramp.elements[i].color = tuple(c) + (1,)
        L.new(bw.outputs[0], cr.inputs[0])
        col = cr.outputs[0]
    if tint is not None:
        mx = N.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        L.new(col, mx.inputs["A"])
        mx.inputs["B"].default_value = tuple(tint) + (1.0,)
        col = mx.outputs["Result"]
    L.new(col, b.inputs["Base Color"])
    if "rough" in t:
        r = N.new("ShaderNodeTexImage")
        r.image = _img(t["rough"], "Non-Color")
        L.new(mp.outputs[0], r.inputs[0])
        ma = N.new("ShaderNodeMath")
        ma.operation = "MULTIPLY_ADD"
        ma.use_clamp = True
        L.new(r.outputs[0], ma.inputs[0])
        ma.inputs[1].default_value = rough_mul
        ma.inputs[2].default_value = rough_add
        L.new(ma.outputs[0], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = min(1.0, 0.6 * rough_mul + rough_add)
    if "nor" in t and normal > 0:
        n = N.new("ShaderNodeTexImage")
        n.image = _img(t["nor"], "Non-Color")
        L.new(mp.outputs[0], n.inputs[0])
        nm = N.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        L.new(n.outputs[0], nm.inputs["Color"])
        L.new(nm.outputs[0], b.inputs["Normal"])
    if use_alpha and "alpha" in t:
        a = N.new("ShaderNodeTexImage")
        a.image = _img(t["alpha"], "Non-Color")
        L.new(mp.outputs[0], a.inputs[0])
        L.new(a.outputs[0], b.inputs["Alpha"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    _mats[name] = m
    return m


def mat_glass(name, tint=(0.9, 0.95, 0.95), rough=0.0, darkness=1.0, reflect=1.0):
    """Architectural glass: real refraction for camera rays, plain tinted
    transparency for shadow/diffuse rays so daylight gets indoors cheaply."""
    if name in _mats:
        return _mats[name]
    m, nt, b, out = _new(name)
    N, L = nt.nodes, nt.links
    b.inputs["Base Color"].default_value = tuple(tint) + (1,)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.5
    b.inputs["Specular IOR Level"].default_value = 0.5 * reflect
    tr = N.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = tuple(c * darkness for c in tint) + (1,)
    lp = N.new("ShaderNodeLightPath")
    mx = N.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    L.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    L.new(lp.outputs["Is Diffuse Ray"], mx.inputs[1])
    ms = N.new("ShaderNodeMixShader")
    L.new(mx.outputs[0], ms.inputs[0])
    L.new(b.outputs[0], ms.inputs[1])
    L.new(tr.outputs[0], ms.inputs[2])
    L.new(ms.outputs[0], out.inputs[0])
    _mats[name] = m
    return m


def mat_water(name="water", color=(0.55, 0.85, 0.9), scale=3.0, strength=0.25):
    if name in _mats:
        return _mats[name]
    m, nt, b, out = _new(name)
    N, L = nt.nodes, nt.links
    b.inputs["Base Color"].default_value = tuple(color) + (1,)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.33
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 3.0
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    L.new(nz.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    tr = N.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = tuple(color) + (1,)
    lp = N.new("ShaderNodeLightPath")
    ms = N.new("ShaderNodeMixShader")
    L.new(lp.outputs["Is Shadow Ray"], ms.inputs[0])
    L.new(b.outputs[0], ms.inputs[1])
    L.new(tr.outputs[0], ms.inputs[2])
    L.new(ms.outputs[0], out.inputs[0])
    _mats[name] = m
    return m


def mat_emit(name, color, strength):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = tuple(color) + (1,)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    _mats[name] = m
    return m


# ----------------------------------------------------------- mesh builder ---
class MB:
    """Accumulates quads/boxes with metre-scale planar UVs, then builds one object."""

    def __init__(self):
        self.v, self.f, self.uv, self.fm, self.mats, self.smooth = [], [], [], [], [], []

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def face(self, pts, mat, uvs=None, smooth=False):
        pts = [Vector(p) for p in pts]
        i0 = len(self.v)
        self.v += [tuple(p) for p in pts]
        self.f.append(list(range(i0, i0 + len(pts))))
        if uvs is None:
            n = Vector((0, 0, 0))
            for i in range(len(pts)):
                a, b = pts[i], pts[(i + 1) % len(pts)]
                n += Vector(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            if az >= ax and az >= ay:
                uvs = [(p.x, p.y) for p in pts]
            elif ax >= ay:
                uvs = [(p.y, p.z) for p in pts]
            else:
                uvs = [(p.x, p.z) for p in pts]
        self.uv.append(uvs)
        self.fm.append(self._mi(mat))
        self.smooth.append(smooth)

    def box(self, x0, y0, z0, x1, y1, z1, mat, mats=None, skip=""):
        """Axis box. `mats` may override per side: keys '+x','-x','+y','-y','+z','-z'.
        `skip` lists sides to omit, e.g. '-z+z'."""
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        if z1 < z0:
            z0, z1 = z1, z0
        mats = mats or {}
        sides = {
            "-x": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
            "+x": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "+y": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
            "-z": [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
            "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        }
        for k, pts in sides.items():
            if k in skip:
                continue
            self.face(pts, mats.get(k, mat))

    def obox(self, m, sx, sy, sz, mat):
        """Box of size sx,sy,sz centred at origin, transformed by matrix m."""
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        c = [m @ Vector(p) for p in [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
                                     (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]]
        for q in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
            self.face([c[i] for i in q], mat)

    def cyl(self, p0, p1, r, mat, seg=16, r1=None, caps=True, smooth=True):
        p0, p1 = Vector(p0), Vector(p1)
        r1 = r if r1 is None else r1
        d = (p1 - p0).normalized()
        a = d.orthogonal().normalized()
        b = d.cross(a)
        ring0 = [p0 + r * (math.cos(t) * a + math.sin(t) * b) for t in [2 * math.pi * i / seg for i in range(seg)]]
        ring1 = [p1 + r1 * (math.cos(t) * a + math.sin(t) * b) for t in [2 * math.pi * i / seg for i in range(seg)]]
        ln = (p1 - p0).length
        for i in range(seg):
            j = (i + 1) % seg
            u0, u1 = 2 * math.pi * r * i / seg, 2 * math.pi * r * (i + 1) / seg
            self.face([ring0[i], ring0[j], ring1[j], ring1[i]], mat,
                      uvs=[(u0, 0), (u1, 0), (u1, ln), (u0, ln)], smooth=smooth)
        if caps:
            self.face(list(reversed(ring0)), mat)
            self.face(ring1, mat)

    def build(self, name, collection=None, bevel=0.0, weld=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        uvl = me.uv_layers.new(name="UVMap")
        k = 0
        for uvs in self.uv:
            for uv in uvs:
                uvl.data[k].uv = uv
                k += 1
        for m in self.mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", self.fm)
        me.polygons.foreach_set("use_smooth", self.smooth)
        me.update()
        if weld:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
            bm.to_mesh(me)
            bm.free()
        ob = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        if bevel > 0:
            ob.modifiers.new("weld", "WELD").merge_threshold = 0.0005
            bv = ob.modifiers.new("bevel", "BEVEL")
            bv.width = bevel
            bv.segments = 2
            bv.limit_method = "ANGLE"
            bv.harden_normals = True
        return ob


def shade_auto(ob, angle=40):
    for p in ob.data.polygons:
        p.use_smooth = True
    try:
        m = ob.modifiers.new("ws", "WEIGHTED_NORMAL")
        m.keep_sharp = True
    except Exception:
        pass
    return ob


def subsurf(ob, levels=2):
    m = ob.modifiers.new("sub", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


# ------------------------------------------------------------- asset lib ---
_lib = {}


def _bbox(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    bpy.context.view_layer.update()
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return lo, hi


def import_gltf(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def lib(name, path=None, pick=None, center=True, fix=None):
    """Load an asset once into a hidden library collection. `pick` filters objects
    by substring (for packs holding several variants)."""
    key = name if pick is None else f"{name}:{pick}"
    if key in _lib:
        return _lib[key]
    root = coll("LIB", hide=True)
    c = bpy.data.collections.new("LIB_" + key)
    root.children.link(c)
    objs = import_gltf(path or ph.model(name, MODEL_RES))
    if pick is not None:
        keep = [o for o in objs if pick in o.name]
        for o in objs:
            if o not in keep:
                bpy.data.objects.remove(o, do_unlink=True)
        objs = keep
    for o in objs:
        link(o, c)
    if center:
        lo, hi = _bbox(objs)
        off = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
        for o in objs:
            if o.parent is None:
                o.location += off
    if fix:
        fix(objs)
    lo, hi = _bbox(objs)
    c["size"] = tuple(hi - lo)
    _lib[key] = c
    return c


def place(name, loc, rz=0.0, scale=1.0, collection=None, pick=None, path=None, rx=0.0, ry=0.0, fix=None,
          center=True):
    c = lib(name, path=path, pick=pick, fix=fix, center=center)
    e = bpy.data.objects.new("i_" + name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = c
    e.location = loc
    e.rotation_euler = Euler((rx, ry, rz))
    e.scale = (scale,) * 3 if not isinstance(scale, (tuple, list)) else scale
    e.empty_display_size = 0.2
    (collection or bpy.context.scene.collection).objects.link(e)
    return e


def scatter(name, points, collection=None, pick=None, smin=0.8, smax=1.2, seed=0, path=None):
    rnd = random.Random(seed)
    return [place(name, p, rz=rnd.uniform(0, 6.283), scale=rnd.uniform(smin, smax),
                  collection=collection, pick=pick, path=path) for p in points]


def face_instancer(name, child_collection_obj, pts, sizes, collection=None, seed=0):
    """Instance `child_collection_obj` (a mesh object) on many points using face
    instancing: one tiny triangle per point, random yaw, scaled by `sizes`."""
    rnd = random.Random(seed)
    v, f = [], []
    for p, s in zip(pts, sizes):
        a = rnd.uniform(0, 6.283)
        r = s * 0.877
        base = len(v)
        for k in range(3):
            t = a + k * 2.0944
            v.append((p[0] + r * math.cos(t), p[1] + r * math.sin(t), p[2]))
        f.append((base, base + 1, base + 2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.instance_type = "FACES"
    ob.use_instance_faces_scale = True
    ob.show_instancer_for_render = False
    ob.show_instancer_for_viewport = False
    child_collection_obj.parent = ob
    return ob


# ------------------------------------------------------- world and render ---
def hdri_sun_azimuth(path):
    """World-space azimuth (radians, from +X toward +Y) of the brightest spot of an
    equirectangular HDRI as Blender maps it with zero rotation, plus its elevation."""
    import numpy as np
    im = bpy.data.images.load(path, check_existing=True)
    w, h = im.size
    px = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[:, :, :3].sum(axis=2)
    f = max(1, w // 512)
    lum = lum[: h // f * f, : w // f * f].reshape(h // f, f, w // f, f).mean(axis=(1, 3))
    iy, ix = np.unravel_index(int(lum.argmax()), lum.shape)
    u, v = (ix + 0.5) / lum.shape[1], (iy + 0.5) / lum.shape[0]
    # Blender: u = atan2(dir.y, -dir.x) / (2 pi) + 0.5
    ang = (u - 0.5) * 2 * math.pi
    az = -ang          # verified with a shadow test: world azimuth = az - rot_z
    return az, (v - 0.5) * math.pi


def world_hdri(asset, res="4k", strength=1.0, rot_z=0.0, sun=None, sun_az=None):
    """`sun_az` (degrees from +X toward +Y): rotate the sky so its sun sits there."""
    if sun_az is not None:
        az, el = hdri_sun_azimuth(ph.hdri(asset, res))
        rot_z = az - math.radians(sun_az)
        print(f"HDRI sun: native az {math.degrees(az):.1f} el {math.degrees(el):.1f} -> rot {math.degrees(rot_z):.1f}")
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputWorld")
    bg = N.new("ShaderNodeBackground")
    env = N.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(ph.hdri(asset, res), check_existing=True)
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, rot_z)
    L.new(tc.outputs["Generated"], mp.inputs[0])
    L.new(mp.outputs[0], env.inputs[0])
    L.new(env.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = strength
    L.new(bg.outputs[0], out.inputs[0])
    return w


def sun(direction_deg=(50, 0, 135), strength=4.0, angle=0.8, color=(1, 0.96, 0.9), collection=None):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = strength
    d.angle = math.radians(angle)
    d.color = color
    o = bpy.data.objects.new("Sun", d)
    o.rotation_euler = Euler([math.radians(a) for a in direction_deg])
    (collection or bpy.context.scene.collection).objects.link(o)
    return o


def area_light(loc, size, power, color=(1, 0.9, 0.8), rot=(0, 0, 0), collection=None, size_y=None, name="Area"):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = power
    d.color = color
    d.size = size
    if size_y:
        d.shape = "RECTANGLE"
        d.size_y = size_y
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = Euler(rot)
    (collection or bpy.context.scene.collection).objects.link(o)
    return o


def point_light(loc, power, color=(1, 0.85, 0.65), radius=0.05, collection=None, name="Point"):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = power
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    o.location = loc
    (collection or bpy.context.scene.collection).objects.link(o)
    return o


def camera(name, loc, target, lens=28, collection=None, dof=None, fstop=4.0, shift_y=0.0, sensor=36):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    d.sensor_width = sensor
    d.shift_y = shift_y
    d.clip_start = 0.05
    d.clip_end = 5000
    o = bpy.data.objects.new(name, d)
    o.location = loc
    v = Vector(target) - Vector(loc)
    o.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()
    if dof:
        d.dof.use_dof = True
        d.dof.focus_distance = dof
        d.dof.aperture_fstop = fstop
    (collection or bpy.context.scene.collection).objects.link(o)
    return o


def render_setup(w=1920, h=1080, samples=96, exposure=0.0, look="AgX - Medium High Contrast",
                 denoise=True, threads=0, noise=0.03):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    c = s.cycles
    c.device = "CPU"
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = noise
    c.use_denoising = denoise
    try:
        c.denoiser = "OPENIMAGEDENOISE"
        c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    except Exception:
        pass
    c.max_bounces = 8
    c.diffuse_bounces = 3
    c.glossy_bounces = 4
    c.transmission_bounces = 8
    c.transparent_max_bounces = 12
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    c.blur_glossy = 0.5
    s.render.resolution_x = w
    s.render.resolution_y = h
    s.render.resolution_percentage = 100
    s.render.use_persistent_data = True
    s.render.image_settings.file_format = "PNG"
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = look
    except Exception:
        pass
    s.view_settings.exposure = exposure
    if threads:
        s.render.threads_mode = "FIXED"
        s.render.threads = threads
    return s


def render(cam, path, **over):
    s = bpy.context.scene
    s.camera = cam
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def anim_camera(name, keys, lens=24, collection=None, target_parent=None):
    """Camera that flies through keys = [(frame, location, target)], always looking at
    an animated target empty. Returns (camera, target)."""
    c = collection or bpy.context.scene.collection
    d = bpy.data.cameras.new(name)
    d.lens = lens
    d.clip_start = 0.05
    d.clip_end = 5000
    cam = bpy.data.objects.new(name, d)
    tgt = bpy.data.objects.new(name + "_target", None)
    c.objects.link(cam)
    c.objects.link(tgt)
    if target_parent is not None:
        tgt.parent = target_parent
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    for (f, loc, t) in keys:
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
        if t is not None:
            tgt.location = t
            tgt.keyframe_insert("location", frame=f)
    return cam, tgt


def render_frames(cam, out_dir, f0, f1):
    """Render frames f0..f1 as PNGs (skipping ones already on disk, so a run can resume)."""
    s = bpy.context.scene
    s.camera = cam
    os.makedirs(out_dir, exist_ok=True)
    for f in range(f0, f1 + 1):
        p = os.path.join(out_dir, f"f_{f:04d}.png")
        if os.path.exists(p):
            continue
        s.frame_set(f)
        s.render.filepath = p
        bpy.ops.render.render(write_still=True)


# ------------------------------------------------------- camera paths ---
def _catmull(pts, n_per=24):
    """Centripetal Catmull-Rom through pts (Vectors); returns a dense polyline."""
    P = [pts[0] + (pts[0] - pts[1])] + list(pts) + [pts[-1] + (pts[-1] - pts[-2])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]

        def tj(ti, a, b):
            return ti + max((b - a).length, 1e-4) ** 0.5

        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        for k in range(n_per):
            t = t1 + (t2 - t1) * k / n_per
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(Vector(pts[-1]))
    return out


def path_camera(name, waypoints, fps=12.0, lens=24, collection=None, f0=1, bob=0.0, ease=1.5, lens_keys=None):
    """A camera that travels a smooth spline through waypoints = [(position, look_at, speed m/s)],
    looking at a target that glides along its own spline. Speed is blended between waypoints and
    eased in at the start and out at the end. bob = walking head-bob amplitude (m).
    Returns (camera, last_frame)."""
    pos = [Vector(w[0]) for w in waypoints]
    look = [Vector(w[1]) for w in waypoints]
    spd = [float(w[2]) for w in waypoints]
    dense = _catmull(pos)
    dl = _catmull(look)
    # arc length of the position spline, and the waypoint index each sample belongs to
    seg = len(dense) - 1
    acc = [0.0]
    for i in range(seg):
        acc.append(acc[-1] + (dense[i + 1] - dense[i]).length)
    total = acc[-1]
    per = (len(dense) - 1) / max(1, len(pos) - 1)

    def at(d):
        d = max(0.0, min(total, d))
        lo, hi = 0, seg
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if acc[mid] <= d:
                lo = mid
            else:
                hi = mid
        f = (d - acc[lo]) / max(1e-9, acc[lo + 1] - acc[lo])
        p = dense[lo].lerp(dense[lo + 1], f)
        u = (lo + f) / per                        # waypoint parameter
        il = min(len(dl) - 2, int((lo + f)))
        lf = (lo + f) - il
        t = dl[il].lerp(dl[il + 1], lf)
        i0 = min(len(spd) - 2, int(u))
        s = spd[i0] + (spd[i0 + 1] - spd[i0]) * (u - i0)
        return p, t, s

    d = cam = None
    dcam = bpy.data.cameras.new(name)
    dcam.lens = lens
    dcam.clip_start = 0.05
    dcam.clip_end = 5000
    cam = bpy.data.objects.new(name, dcam)
    (collection or bpy.context.scene.collection).objects.link(cam)
    dist, fr, step_phase = 0.0, f0, 0.0
    ramp = ease * max(spd[0], 0.5)                # metres over which to ease in / out
    while True:
        p, t, s = at(dist)
        k_in = min(1.0, 0.25 + 0.75 * dist / max(ramp, 1e-3))
        k_out = min(1.0, 0.2 + 0.8 * (total - dist) / max(ramp, 1e-3))
        v = max(0.05, s * min(k_in, k_out))
        if bob > 0:
            step_phase += v / fps / 0.75 * math.pi          # one step every ~0.75 m
            p = p + Vector((0, 0, bob * abs(math.sin(step_phase)) - bob * 0.5))
        cam.location = p
        cam.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=fr)
        cam.keyframe_insert("rotation_euler", frame=fr)
        if lens_keys:
            for (dd, ll) in lens_keys:
                pass
        if dist >= total - 1e-6:
            break
        dist = min(total, dist + v / fps)
        fr += 1
    return cam, fr


def path_check(cam, f0, f1, step=1):
    """Ray-cast between consecutive camera positions; returns frames where the camera passes
    through geometry (walls, doors, glass...)."""
    s = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    bad = []
    prev = None
    for f in range(f0, f1 + 1, step):
        s.frame_set(f)
        p = cam.matrix_world.translation.copy()
        if prev is not None:
            d = p - prev
            if d.length > 1e-4:
                hit, loc, nrm, idx, ob, mtx = s.ray_cast(dg, prev, d.normalized(), distance=d.length)
                if hit:
                    bad.append((f, ob.name if ob else "?"))
        prev = p
    return bad
