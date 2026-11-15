"""Realistic clothed people from the CC0 MakeHuman data set, without the add-on.

Reads the base mesh, macro shape targets, standard rig + weights (shipped in the
MPFB extension's data folder) and the "system assets" pack (skins, clothes,
hair, eyes ...), fits the clothes, poses the figure with the rig and bakes the
result to a single static mesh.

    import mh
    ob = mh.human("amina", gender="female", race="african", clothes=["female_casualsuit01", "shoes02"],
                  hair="braid01", pose=mh.POSES["stand"], collection=c)
"""
import gzip
import json
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

MPFB = os.environ.get("MPFB_DATA", "/home/user/assets/mh/mpfb_ext/data")
SYS = os.environ.get("MH_ASSETS", "/home/user/assets/mh/sys")

_base = None


def _to_bl(a):
    """MakeHuman (x, y up, z front, decimetres) -> Blender (x, -z, y) metres."""
    a = np.asarray(a, dtype=np.float64)
    return np.stack([a[:, 0], -a[:, 2], a[:, 1]], axis=1) * 0.1


def _read_obj(path):
    v, vt, faces, fuv, groups, fgroup = [], [], [], [], {}, []
    g = "default"
    with open(path) as f:
        for ln in f:
            if ln.startswith("v "):
                p = ln.split()
                v.append((float(p[1]), float(p[2]), float(p[3])))
            elif ln.startswith("vt "):
                p = ln.split()
                vt.append((float(p[1]), float(p[2])))
            elif ln.startswith("g "):
                g = ln.split()[1]
            elif ln.startswith("f "):
                vi, ti = [], []
                for tok in ln.split()[1:]:
                    q = tok.split("/")
                    vi.append(int(q[0]) - 1)
                    ti.append(int(q[1]) - 1 if len(q) > 1 and q[1] else 0)
                faces.append(vi)
                fuv.append(ti)
                fgroup.append(g)
                groups.setdefault(g, set()).update(vi)
    return np.array(v), (np.array(vt) if vt else np.zeros((1, 2))), faces, fuv, groups, fgroup


def base():
    global _base
    if _base is None:
        v, vt, faces, fuv, groups, fgroup = _read_obj(os.path.join(MPFB, "3dobjs", "base.obj"))
        rig = json.load(open(os.path.join(MPFB, "rigs", "standard", "rig.default.json")))
        wts = json.load(open(os.path.join(MPFB, "rigs", "standard", "weights.default.json")))["weights"]
        _base = dict(v=v, vt=vt, faces=faces, fuv=fuv, groups=groups, fgroup=fgroup, rig=rig, wts=wts)
    return _base


def _target(rel):
    p = os.path.join(MPFB, "targets", rel + ".target.gz")
    idx, d = [], []
    with gzip.open(p, "rt") as f:
        for ln in f:
            q = ln.split()
            if len(q) == 4 and not ln.startswith("#"):
                idx.append(int(q[0]))
                d.append((float(q[1]), float(q[2]), float(q[3])))
    return np.array(idx, dtype=np.int64), np.array(d)


def shape(gender="male", race="african", age="young", muscle="average", weight="average", height=None,
          extra=()):
    """Morphed base-mesh coordinates in MakeHuman space."""
    b = base()
    v = b["v"].copy()
    tl = [(f"macrodetails/universal-{gender}-{age}-{muscle}muscle-{weight}weight", 1.0),
          (f"macrodetails/{race}-{gender}-{age}", 1.0)]
    if height in ("max", "min"):
        tl.append((f"macrodetails/height/{gender}-{age}-{muscle}muscle-{weight}weight-{height}height", 0.6))
    tl += list(extra)
    for rel, w in tl:
        try:
            i, d = _target(rel)
            if len(i):
                v[i] += d * w
        except FileNotFoundError:
            print("mh: missing target", rel)
    return v


def _mhclo(path):
    info, rows, delete = {}, [], set()
    mode = "head"
    with open(path) as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            p = s.split()
            if p[0] == "verts":
                mode = "verts"
                continue
            if p[0] == "delete_verts":
                mode = "delete"
                continue
            if mode == "verts":
                try:
                    nums = [float(x) for x in p]
                except ValueError:
                    pass            # a header line in the middle of the vertex block
                else:
                    rows.append(nums)
                    continue
            if mode == "delete":
                try:
                    k = 0
                    while k < len(p):
                        if k + 2 < len(p) and p[k + 1] == "-":
                            delete.update(range(int(p[k]), int(p[k + 2]) + 1))
                            k += 3
                        else:
                            delete.add(int(p[k]))
                            k += 1
                    continue
                except ValueError:
                    mode = "head"
            if p[0] in ("x_scale", "y_scale", "z_scale"):
                info[p[0]] = (int(p[1]), int(p[2]), float(p[3]))
            elif len(p) > 1:
                info[p[0]] = " ".join(p[1:])
    return info, rows, delete


def _fit(info, rows, bv):
    sc = []
    for ax, key in enumerate(("x_scale", "y_scale", "z_scale")):
        if key in info:
            a, b, den = info[key]
            sc.append(abs(bv[a, ax] - bv[b, ax]) / den)
        else:
            sc.append(1.0)
    sc = np.array(sc)
    out = np.zeros((len(rows), 3))
    bind = []
    for k, r in enumerate(rows):
        if len(r) < 9:
            i = int(r[0])
            out[k] = bv[i]
            bind.append(((i, i, i), (1.0, 0.0, 0.0)))
        else:
            i0, i1, i2 = int(r[0]), int(r[1]), int(r[2])
            out[k] = r[3] * bv[i0] + r[4] * bv[i1] + r[5] * bv[i2] + np.array(r[6:9]) * sc
            bind.append(((i0, i1, i2), (r[3], r[4], r[5])))
    return out, bind


def _mhmat(path):
    d = {}
    if not os.path.exists(path):
        return d
    for ln in open(path):
        p = ln.strip().split()
        if len(p) >= 2 and not ln.startswith("#"):
            d[p[0]] = " ".join(p[1:])
    return d


_matcache = {}

TOP_REGION = {   # where the shirt lives in each suit's texture (fractions, origin top-left)
    "female_casualsuit01": lambda x, y: (y < 0.47) | ((x > 0.735) & (y < 0.86)),
    "female_casualsuit02": lambda x, y: (y < 0.47) | ((x > 0.70) & (y < 0.86)),
    "male_casualsuit04": lambda x, y: y < 0.47,
    "male_casualsuit06": lambda x, y: y < 0.47,
    "male_casualsuit02": lambda x, y: y < 0.47,
}


def retint(asset, key, top=None, bottom=None, cache="/home/user/assets/mh/retint"):
    """Write a recoloured copy of a suit's diffuse texture: `top` = new shirt colour
    (also wipes the printed logo), `bottom` = new trouser colour. Returns the path."""
    from PIL import Image, ImageFilter
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, f"{asset}_{key}.png")
    if os.path.exists(out):
        return out
    src = os.path.join(SYS, "clothes", asset, asset + "_diffuse.png")
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32) / 255.0
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    reg = TOP_REGION.get(asset, lambda x, y: y < 0.47)(xx / w, yy / h)
    lum = a.mean(axis=2)
    if top is not None:
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        white_tee = float(np.median(lum[reg])) > 0.7
        cloth = (lum > 0.72) if white_tee else ((b > r + 0.08) & (b > g))     # plain fabric pixels
        ref = float(np.median(lum[reg & cloth])) if (reg & cloth).any() else 0.5
        shade = np.where(cloth, lum / ref, 1.0)
        sh = Image.fromarray((np.clip(shade, 0, 2) * 127).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
        shade = np.asarray(sh).astype(np.float32) / 127.0
        new = np.clip(shade[..., None] * np.array(top, dtype=np.float32)[None, None, :], 0, 1)
        a = np.where(reg[..., None], new, a)
    if bottom is not None:
        nb = np.clip((lum / 0.45)[..., None] * np.array(bottom, dtype=np.float32)[None, None, :], 0, 1)
        a = np.where(reg[..., None], a, nb)
    Image.fromarray((a * 255).astype(np.uint8)).save(out)
    return out


def _material(name, diffuse=None, normal=None, color=(0.8, 0.8, 0.8), rough=0.6, sss=0.0, alpha=False,
              hue=None, spec=0.4):
    key = (name, diffuse, hue)
    if key in _matcache:
        return _matcache[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Base Color"].default_value = tuple(color) + (1,)
    if diffuse and os.path.exists(diffuse):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(diffuse, check_existing=True)
        col = t.outputs[0]
        if hue is not None:
            h = nt.nodes.new("ShaderNodeHueSaturation")
            h.inputs["Hue"].default_value = hue[0]
            h.inputs["Saturation"].default_value = hue[1]
            h.inputs["Value"].default_value = hue[2]
            nt.links.new(col, h.inputs["Color"])
            col = h.outputs[0]
        nt.links.new(col, b.inputs["Base Color"])
        if alpha:
            nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    if normal and os.path.exists(normal):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(normal, check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(t.outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
    if sss > 0:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.012, 0.006, 0.004)
        b.inputs["Subsurface Scale"].default_value = 1.0
    _matcache[key] = m
    return m


def _asset_dir(name):
    for kind in ("clothes", "hair", "eyebrows", "eyelashes", "eyes", "teeth", "tongue"):
        d = os.path.join(SYS, kind, name)
        if os.path.isdir(d):
            return kind, d
    raise FileNotFoundError(name)


def _mesh_obj(name, co, faces, fuv, vt, mat, collection, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(c) for c in co], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    k = 0
    for ti in fuv:
        for t in ti:
            uvl.data[k].uv = vt[t] if t < len(vt) else (0, 0)
            k += 1
    me.materials.append(mat)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def human(name, gender="male", race="african", age="young", muscle="average", weight="average", height=None,
          skin=None, clothes=(), hair=None, eyes="brown", eyebrows="eyebrow001", pose=None, collection=None,
          tint=None, extra_targets=(), subdiv=1, shift=(0, 0, 0), textures=None):
    """Build a posed, clothed person as one mesh object standing on z=0 at the origin."""
    b = base()
    collection = collection or bpy.context.scene.collection
    tint = tint or {}
    mv = shape(gender, race, age, muscle, weight, height, extra_targets)
    bl = _to_bl(mv)
    ground = bl[sorted(b["groups"]["joint-ground"])].mean(axis=0)[2] if "joint-ground" in b["groups"] else bl[:, 2].min()
    bl[:, 2] -= ground
    mv_g = mv.copy()

    parts = []        # (object, bind) – bind None for the body itself
    # --- clothes / hair / face parts
    names = list(clothes) + [x for x in (hair, eyebrows, "eyelashes01", "high-poly", "teeth_base") if x]
    hidden = set()
    for an in names:
        try:
            kind, d = _asset_dir(an)
        except FileNotFoundError:
            print("mh: no asset", an)
            continue
        clo = [f for f in os.listdir(d) if f.endswith(".mhclo")][0]
        info, rows, delete = _mhclo(os.path.join(d, clo))
        if kind == "clothes":
            hidden |= delete
        co, bind = _fit(info, rows, mv_g)
        cb = _to_bl(co)
        cb[:, 2] -= ground
        _, vt, faces, fuv, _, _ = _read_obj(os.path.join(d, info.get("obj_file", an + ".obj")))
        mm = _mhmat(os.path.join(d, info.get("material", an + ".mhmat")))
        if kind == "eyes":
            mm = _mhmat(os.path.join(SYS, "eyes", "materials", eyes + ".mhmat"))
            dd = os.path.join(SYS, "eyes", "materials")
        else:
            dd = d
        dif = os.path.join(dd, mm["diffuseTexture"]) if "diffuseTexture" in mm else None
        if textures and an in textures:
            dif = textures[an]
        nor = os.path.join(dd, mm["normalmapTexture"]) if "normalmapTexture" in mm else None
        col = tuple(float(x) for x in mm.get("diffuseColor", "0.8 0.8 0.8").split()[:3])
        mat = _material(f"mh_{an}" + (f"_{name}" if (an in tint or (textures and an in textures)) else ""), dif, nor, color=col,
                        rough=0.35 if kind in ("eyes", "teeth") else (0.45 if kind == "hair" else 0.75),
                        alpha=kind in ("hair", "eyebrows", "eyelashes", "eyes"),
                        hue=tint.get(an, (0.5, 0.25, 0.16) if kind == "hair" else None),
                        spec=0.6 if kind == "eyes" else 0.3)
        parts.append((_mesh_obj(f"{name}_{an}", cb, faces, fuv, vt, mat, collection), bind))

    # --- body (only the 'body' group faces, minus what the clothes cover)
    if skin is None:
        skin = f"young_{race}_{gender}"
    sd = os.path.join(SYS, "skins", skin)
    sm = _mhmat(os.path.join(sd, [f for f in os.listdir(sd) if f.endswith(".mhmat")][0]))
    smat = _material(f"mh_skin_{skin}", os.path.join(sd, sm.get("diffuseTexture", "")), None, rough=0.48, sss=0.06,
                     spec=0.35)
    bf, bu = [], []
    for f, t, g in zip(b["faces"], b["fuv"], b["fgroup"]):
        if g != "body":
            continue
        if hidden and all(i in hidden for i in f):
            continue
        bf.append(f)
        bu.append(t)
    body = _mesh_obj(f"{name}_body", bl, bf, bu, b["vt"], smat, collection)
    parts.insert(0, (body, None))

    # --- armature from the standard rig
    def joint(spec):
        s = spec.get("strategy")
        if s == "CUBE":
            idx = sorted(b["groups"][spec["cube_name"]])
            return Vector(bl[idx].mean(axis=0))
        if s == "VERTEX":
            return Vector(bl[spec["vertex_index"]])
        if s == "MEAN":
            return Vector(bl[spec["vertex_indices"]].mean(axis=0))
        return Vector(spec["default_position"])

    ad = bpy.data.armatures.new(name + "_rig")
    arm = bpy.data.objects.new(name + "_rig", ad)
    collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    rig = b["rig"]
    for bn, spec in rig.items():
        eb = ad.edit_bones.new(bn)
        eb.head, eb.tail = joint(spec["head"]), joint(spec["tail"])
        if (eb.tail - eb.head).length < 1e-4:
            eb.tail = eb.head + Vector((0, 0, 0.01))
        eb.roll = spec.get("roll", 0.0)
    for bn, spec in rig.items():
        if spec.get("parent"):
            ad.edit_bones[bn].parent = ad.edit_bones[spec["parent"]]
    bpy.ops.object.mode_set(mode="OBJECT")

    # --- skinning
    wts = b["wts"]
    vw = {}
    for bn, lst in wts.items():
        for vi, w in lst:
            vw.setdefault(int(vi), []).append((bn, w))
    for ob, bind in parts:
        gr = {}
        if bind is None:
            for vi, lst in vw.items():
                for bn, w in lst:
                    g = gr.get(bn) or ob.vertex_groups.new(name=bn)
                    gr[bn] = g
                    g.add([vi], w, "REPLACE")
        else:
            for k, (ids, ws) in enumerate(bind):
                acc = {}
                tot = sum(abs(x) for x in ws) or 1.0
                for i, w in zip(ids, ws):
                    for bn, bw in vw.get(i, ()):
                        acc[bn] = acc.get(bn, 0.0) + bw * abs(w) / tot
                for bn, w in acc.items():
                    if w > 1e-4:
                        g = gr.get(bn) or ob.vertex_groups.new(name=bn)
                        gr[bn] = g
                        g.add([k], w, "REPLACE")
        md = ob.modifiers.new("arm", "ARMATURE")
        md.object = arm

    # --- pose: {bone: (rx, ry, rz)} in degrees about the WORLD axes, applied on top of
    # whatever the parent chain has already done (so "X -80" always means "pitch forward").
    if pose:
        total = {}

        def tot(bn):
            if bn in total:
                return total[bn]
            par = ad.bones[bn].parent
            P = tot(par.name) if par else Matrix.Identity(3)
            rot = pose.get(bn)
            if rot is None:
                total[bn] = P
                return P
            D = (Matrix.Rotation(math.radians(rot[2]), 3, "Z") @ Matrix.Rotation(math.radians(rot[1]), 3, "Y")
                 @ Matrix.Rotation(math.radians(rot[0]), 3, "X"))
            Rb = ad.bones[bn].matrix_local.to_3x3()
            pb = arm.pose.bones[bn]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (Rb.inverted() @ P.inverted() @ D @ P @ Rb).to_quaternion()
            total[bn] = D @ P
            return total[bn]

        for bn in pose:
            if not bn.startswith("_") and bn in ad.bones:
                tot(bn)
    bpy.context.view_layer.update()

    # --- bake and join
    dg = bpy.context.evaluated_depsgraph_get()
    baked = []
    for ob, _ in parts:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        nb = bpy.data.objects.new(ob.name, me)
        collection.objects.link(nb)
        baked.append(nb)
    for ob, _ in parts:
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.objects.remove(arm, do_unlink=True)
    # drop the helper vertices that carry no faces
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(baked[0].data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(baked[0].data)
    bm.free()
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in baked:
        o.select_set(True)
    bpy.context.view_layer.objects.active = baked[0]
    bpy.ops.object.join()
    res = bpy.context.view_layer.objects.active
    res.name = name
    zs = pose.get("_z") if pose else None
    lo = min((res.matrix_world @ v.co).z for v in res.data.vertices)
    for v in res.data.vertices:
        v.co.z -= lo if zs is None else zs
        v.co += Vector(shift)
    if subdiv:
        sm = res.modifiers.new("sub", "SUBSURF")
        sm.levels = 0
        sm.render_levels = subdiv
    return res


# Pose library. Angles in degrees about world axes (figure faces -Y, left side is +X):
#   X negative = pitch the limb forward, Y = swing a left limb down (+) / right limb down (-),
#   Z = twist about the vertical.
POSES = {
    "stand": {
        "upperarm01.L": (0, 40, 0), "upperarm01.R": (0, -40, 0),
        "lowerarm01.L": (-14, 4, 0), "lowerarm01.R": (-14, -4, 0),
    },
    "stand_relaxed": {
        "upperarm01.L": (6, 40, 0), "upperarm01.R": (-10, -38, 0),
        "lowerarm01.L": (-10, 4, 0), "lowerarm01.R": (-62, -4, 20),
        "spine03": (0, 0, 7), "head": (0, 0, -16), "upperleg01.L": (0, -4, 0), "upperleg01.R": (-6, 4, 0),
        "lowerleg01.R": (10, 0, 0),
    },
    "hands_hips": {
        "upperarm01.L": (14, 18, 0), "upperarm01.R": (14, -18, 0),
        "lowerarm01.L": (-20, 78, 0), "lowerarm01.R": (-20, -78, 0),
        "head": (0, 0, 12),
    },
    "point": {
        "upperarm01.L": (0, 40, 0), "lowerarm01.L": (-12, 4, 0),
        "upperarm01.R": (-70, -34, 0), "lowerarm01.R": (-8, 0, 0),
        "head": (-6, 0, 10), "spine03": (0, 0, 6),
    },
    "shade_eyes": {
        "upperarm01.L": (0, 40, 0), "lowerarm01.L": (-12, 4, 0),
        "upperarm01.R": (-58, -18, 0), "lowerarm01.R": (-88, 30, 62),
        "head": (-8, 0, 0),
    },
    "walk": {
        "upperleg01.L": (-26, 0, 0), "lowerleg01.L": (12, 0, 0),
        "upperleg01.R": (16, 0, 0), "lowerleg01.R": (30, 0, 0), "foot.R": (-16, 0, 0),
        "upperarm01.L": (18, 40, 0), "upperarm01.R": (-20, -40, 0),
        "lowerarm01.L": (-12, 4, 0), "lowerarm01.R": (-30, -4, 0),
        "spine03": (0, 0, -5),
    },
    "sit": {
        "upperleg01.L": (-84, 3, 0), "upperleg01.R": (-84, -3, 0),
        "lowerleg01.L": (80, 0, 0), "lowerleg01.R": (80, 0, 0),
        "upperarm01.L": (-12, 38, 0), "upperarm01.R": (-12, -38, 0),
        "lowerarm01.L": (-62, 10, 0), "lowerarm01.R": (-62, -10, 0),
    },
    "sit_window": {
        "upperleg01.L": (-84, 3, 0), "upperleg01.R": (-84, -3, 0),
        "lowerleg01.L": (80, 0, 0), "lowerleg01.R": (80, 0, 0),
        "upperarm01.L": (-12, 38, 0), "upperarm01.R": (-30, -70, 0),
        "lowerarm01.L": (-62, 10, 0), "lowerarm01.R": (-40, -30, 0),
        "head": (0, 0, -28), "spine03": (0, 0, -8),
    },
    "drive": {
        "upperleg01.L": (-78, 5, 0), "upperleg01.R": (-74, -5, 0),
        "lowerleg01.L": (58, 0, 0), "lowerleg01.R": (48, 0, 0),
        "upperarm01.L": (-48, 34, 0), "upperarm01.R": (-48, -34, 0),
        "lowerarm01.L": (-34, -14, 0), "lowerarm01.R": (-34, 14, 0),
        "spine05": (6, 0, 0),
    },
    "car": {
        "upperleg01.L": (-96, 4, 0), "upperleg01.R": (-96, -4, 0),
        "lowerleg01.L": (52, 0, 0), "lowerleg01.R": (52, 0, 0),
        "upperarm01.L": (2, 40, 0), "upperarm01.R": (2, -40, 0),
        "lowerarm01.L": (-48, 14, 0), "lowerarm01.R": (-48, -14, 0),
        "spine05": (-8, 0, 0),
    },
    "car_look_l": {
        "upperleg01.L": (-96, 4, 0), "upperleg01.R": (-96, -4, 0),
        "lowerleg01.L": (52, 0, 0), "lowerleg01.R": (52, 0, 0),
        "upperarm01.L": (-10, 60, 0), "upperarm01.R": (2, -40, 0),
        "lowerarm01.L": (-40, 20, 0), "lowerarm01.R": (-48, -14, 0),
        "spine05": (-8, 0, 0), "head": (0, 0, 34), "neck01": (0, 0, 10),
    },
    "car_look_r": {
        "upperleg01.L": (-96, 4, 0), "upperleg01.R": (-96, -4, 0),
        "lowerleg01.L": (52, 0, 0), "lowerleg01.R": (52, 0, 0),
        "upperarm01.L": (2, 40, 0), "upperarm01.R": (-10, -60, 0),
        "lowerarm01.L": (-48, 14, 0), "lowerarm01.R": (-40, -20, 0),
        "spine05": (-8, 0, 0), "head": (0, 0, -34), "neck01": (0, 0, -10),
    },
    "car_drive": {
        "upperleg01.L": (-94, 5, 0), "upperleg01.R": (-90, -5, 0),
        "lowerleg01.L": (50, 0, 0), "lowerleg01.R": (42, 0, 0),
        "upperarm01.L": (-50, 36, -16), "upperarm01.R": (-50, -36, 16),
        "lowerarm01.L": (-30, -6, 0), "lowerarm01.R": (-30, 6, 0),
        "spine05": (-8, 0, 0),
    },
    "lounge": {
        "spine05": (-28, 0, 0),
        "upperleg01.L": (-62, 4, 0), "upperleg01.R": (-70, -4, 0),
        "lowerleg01.L": (30, 0, 0), "lowerleg01.R": (70, 0, 0),
        "upperarm01.L": (10, 42, 0), "upperarm01.R": (10, -42, 0),
        "lowerarm01.L": (-30, 0, 0), "lowerarm01.R": (-30, 0, 0),
    },
}
