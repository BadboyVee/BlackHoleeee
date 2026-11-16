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
    if isinstance(age, (int, float)):        # 0 = young adult (25) .. 1 = old (90); 0.3 is about 45
        ages = [("young", 1.0 - age), ("old", age)]
    else:
        ages = [(age, 1.0)]
    tl = []
    for ag, aw in ages:
        if aw <= 0:
            continue
        tl += [(f"macrodetails/universal-{gender}-{ag}-{muscle}muscle-{weight}weight", aw),
               (f"macrodetails/{race}-{gender}-{ag}", aw)]
        if height in ("max", "min"):
            tl.append((f"macrodetails/height/{gender}-{ag}-{muscle}muscle-{weight}weight-{height}height", 0.6 * aw))
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


def retint(asset, key, top=None, bottom=None, whole=None, cache="/home/user/assets/mh/retint"):
    """Write a recoloured copy of a garment's diffuse texture and return its path.
    top / bottom: new shirt / trouser colours for the two-piece system suits (also wipes
    the printed logo). whole: recolour the entire garment, keeping its shading."""
    from PIL import Image, ImageFilter
    os.makedirs(cache, exist_ok=True)
    out = os.path.join(cache, f"{asset}_{key}.png")
    if os.path.exists(out):
        return out
    kind, d = _asset_dir(asset)
    clo = [f for f in os.listdir(d) if f.endswith(".mhclo")][0]
    info, _, _ = _mhclo(os.path.join(d, clo))
    mm = _mhmat(os.path.join(d, info.get("material", asset + ".mhmat")))
    src = os.path.join(d, mm["diffuseTexture"])
    im0 = Image.open(src)
    alpha = im0.getchannel("A") if im0.mode == "RGBA" else None
    im = im0.convert("RGB")
    a = np.asarray(im).astype(np.float32) / 255.0
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    reg = TOP_REGION.get(asset, lambda x, y: y < 0.47)(xx / w, yy / h)
    lum = a.mean(axis=2)
    if whole is not None:
        used = lum > 0.02
        ref = float(np.percentile(lum[used], 70)) if used.any() else 0.5
        a = np.clip((lum / max(ref, 1e-3))[..., None] * np.array(whole, dtype=np.float32)[None, None, :], 0, 1)
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
    res = Image.fromarray((a * 255).astype(np.uint8))
    if alpha is not None:
        res.putalpha(alpha)
    res.save(out)
    return out


TEX_MAX = int(os.environ.get("MH_TEX_MAX", "1024"))


def _small(path):
    """A copy of a texture no larger than TEX_MAX pixels (cached). Twenty people with
    full-size maps each do not fit in memory at render time."""
    if not path or not os.path.exists(path):
        return path
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(path)
        if max(im.size) <= TEX_MAX:
            return path
        d = os.path.join(os.path.dirname(SYS), "small", str(TEX_MAX))
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, os.path.basename(os.path.dirname(path)) + "__" + os.path.basename(path))
        if not os.path.exists(out):
            f = TEX_MAX / max(im.size)
            im.resize((max(1, int(im.size[0] * f)), max(1, int(im.size[1] * f))), Image.LANCZOS).save(out)
        return out
    except Exception:
        return path


def _material(name, diffuse=None, normal=None, color=(0.8, 0.8, 0.8), rough=0.6, sss=0.0, alpha=False,
              hue=None, spec=0.4):
    key = (name, diffuse, hue)
    if key in _matcache:
        return _matcache[key]
    diffuse, normal = _small(diffuse), _small(normal)
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
        if hue is not None and len(hue) == 4 and hue[0] == "rgb":
            # recolour to a natural shade: texture luminance (normalised to its own mean) x target colour
            mean = 0.5
            try:
                from PIL import Image
                im = Image.open(diffuse).convert("RGBA").resize((128, 128))
                a = np.asarray(im).astype(np.float32) / 255.0
                w = a[..., 3] > 0.5
                if w.any():
                    mean = float(a[..., :3].mean(axis=2)[w].mean())
            except Exception:
                pass
            bw = nt.nodes.new("ShaderNodeRGBToBW")
            nt.links.new(col, bw.inputs[0])
            dv = nt.nodes.new("ShaderNodeMath")
            dv.operation = "DIVIDE"
            nt.links.new(bw.outputs[0], dv.inputs[0])
            dv.inputs[1].default_value = max(mean, 0.05)
            pw = nt.nodes.new("ShaderNodeMath")            # keep some strand contrast, avoid blow-outs
            pw.operation = "POWER"
            nt.links.new(dv.outputs[0], pw.inputs[0])
            pw.inputs[1].default_value = 0.8
            mx = nt.nodes.new("ShaderNodeMix")
            mx.data_type = "RGBA"
            mx.blend_type = "MULTIPLY"
            mx.inputs["Factor"].default_value = 1.0
            nt.links.new(pw.outputs[0], mx.inputs["A"])
            mx.inputs["B"].default_value = tuple(hue[1:]) + (1,)
            col = mx.outputs["Result"]
            # darker roots, lighter and slightly sun-faded tips
            atn = nt.nodes.new("ShaderNodeAttribute")
            atn.attribute_name = "tip"
            rt = nt.nodes.new("ShaderNodeMapRange")
            rt.inputs["To Min"].default_value = 0.55
            rt.inputs["To Max"].default_value = 1.18
            nt.links.new(atn.outputs["Fac"], rt.inputs["Value"])
            m2 = nt.nodes.new("ShaderNodeMix")
            m2.data_type = "RGBA"
            m2.blend_type = "MULTIPLY"
            m2.inputs["Factor"].default_value = 1.0
            nt.links.new(col, m2.inputs["A"])
            nt.links.new(rt.outputs[0], m2.inputs["B"])
            col = m2.outputs["Result"]
            # strand-direction highlight: anisotropic sheen along the hair (cards hang roughly vertically)
            tg = nt.nodes.new("ShaderNodeTangent")
            tg.direction_type = "RADIAL"
            tg.axis = "Z"
            b.inputs["Anisotropic"].default_value = 0.6
            nt.links.new(tg.outputs[0], b.inputs["Tangent"])
            b.inputs["Roughness"].default_value = 0.46
            b.inputs["Specular IOR Level"].default_value = 0.45
            b.inputs["Sheen Weight"].default_value = 0.12
            b.inputs["Sheen Roughness"].default_value = 0.35
            # fine strands broken into the card surface
            sn = nt.nodes.new("ShaderNodeTexWave")
            sn.wave_type = "BANDS"
            sn.bands_direction = "Z"
            sn.inputs["Scale"].default_value = 160.0
            sn.inputs["Distortion"].default_value = 6.0
            tco = nt.nodes.new("ShaderNodeTexCoord")
            nt.links.new(tco.outputs["Object"], sn.inputs["Vector"])
            bpn = nt.nodes.new("ShaderNodeBump")
            bpn.inputs["Strength"].default_value = 0.35
            bpn.inputs["Distance"].default_value = 0.0004
            nt.links.new(sn.outputs[0], bpn.inputs["Height"])
            nt.links.new(bpn.outputs[0], b.inputs["Normal"])
        elif hue is not None:
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


def skin_material(name, diffuse, race="caucasian"):
    """Skin that reads as skin: subsurface scattering with a red-shifted radius, roughness that varies
    over the face and body, fine pore and wrinkle bump, a thin oily coat."""
    if name in _matcache:
        return _matcache[name]
    diffuse = _small(diffuse)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = [n for n in N if n.type == "BSDF_PRINCIPLED"][0]
    t = N.new("ShaderNodeTexImage")
    if diffuse and os.path.exists(diffuse):
        t.image = bpy.data.images.load(diffuse, check_existing=True)
    # the MakeHuman maps are flat and slightly grey: a touch more saturation and warmth
    hs = N.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 1.12
    hs.inputs["Value"].default_value = 0.97
    L.new(t.outputs[0], hs.inputs["Color"])
    tc = N.new("ShaderNodeTexCoord")
    blot = N.new("ShaderNodeTexNoise")           # uneven skin tone: faint redness and blotches
    blot.inputs["Scale"].default_value = 18.0
    blot.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], blot.inputs["Vector"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.45
    mr.inputs["From Max"].default_value = 0.75
    mr.inputs["To Max"].default_value = 0.10 if race == "caucasian" else 0.05
    L.new(blot.outputs[0], mr.inputs["Value"])
    L.new(mr.outputs[0], mix.inputs["Factor"])
    L.new(hs.outputs[0], mix.inputs["A"])
    mix.inputs["B"].default_value = (0.85, 0.55, 0.5, 1)
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    # subsurface: light travels further in red than in blue
    b.inputs["Subsurface Weight"].default_value = 0.22 if race == "caucasian" else 0.14
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.36, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.012
    try:
        b.subsurface_method = "RANDOM_WALK_SKIN"
    except Exception:
        pass
    # roughness: 0.38..0.58 drifting over the skin (T-zone shinier)
    rn = N.new("ShaderNodeTexNoise")
    rn.inputs["Scale"].default_value = 9.0
    L.new(tc.outputs["Object"], rn.inputs["Vector"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.38
    rr.inputs["To Max"].default_value = 0.58
    L.new(rn.outputs[0], rr.inputs["Value"])
    L.new(rr.outputs[0], b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.42
    b.inputs["Coat Weight"].default_value = 0.08
    b.inputs["Coat Roughness"].default_value = 0.32
    b.inputs["Sheen Weight"].default_value = 0.18             # the fine vellus fuzz that catches grazing light
    b.inputs["Sheen Roughness"].default_value = 0.45
    # pores (fine voronoi) + creases (stretched noise)
    pores = N.new("ShaderNodeTexVoronoi")
    pores.inputs["Scale"].default_value = 900.0
    L.new(tc.outputs["Object"], pores.inputs["Vector"])
    fine = N.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 260.0
    fine.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Object"], fine.inputs["Vector"])
    add = N.new("ShaderNodeMath")
    add.operation = "ADD"
    L.new(pores.outputs["Distance"], add.inputs[0])
    L.new(fine.outputs[0], add.inputs[1])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.12
    bp.inputs["Distance"].default_value = 0.0006
    L.new(add.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    _matcache[name] = m
    return m


def _roots():
    """The system asset pack plus any extra community packs unpacked beside it (ext_*)."""
    base_dir = os.path.dirname(SYS)
    extra = sorted(os.path.join(base_dir, d) for d in os.listdir(base_dir) if d.startswith("ext_"))
    return [SYS] + extra


def _asset_dir(name):
    for root in _roots():
        for kind in ("clothes", "hair", "eyebrows", "eyelashes", "eyes", "teeth", "tongue"):
            d = os.path.join(root, kind, name)
            if os.path.isdir(d):
                return kind, d
    raise FileNotFoundError(name)


def _skin_dir(name):
    for root in _roots():
        d = os.path.join(root, "skins", name)
        if os.path.isdir(d):
            return d
    raise FileNotFoundError(name)


FACE_TARGETS = {
    "nose": ["nose-hump-incr", "nose-hump-decr", "nose-greek-incr", "nose-flaring-incr", "nose-flaring-decr",
             "nose-base-up", "nose-base-down", "nose-curve-convex", "nose-curve-concave", "nose-compression-compress"],
    "chin": ["chin-prominent-incr", "chin-prominent-decr", "chin-width-incr", "chin-width-decr", "chin-height-incr",
             "chin-height-decr", "chin-cleft-incr", "chin-jaw-drop-incr", "chin-bones-incr", "chin-bones-decr"],
    "head": ["head-oval", "head-square", "head-round", "head-rectangular", "head-diamond", "head-triangular",
             "head-fat-incr", "head-fat-decr", "head-scale-vert-incr", "head-scale-horiz-incr"],
    "mouth": ["mouth-upperlip-volume-incr", "mouth-upperlip-volume-decr", "mouth-lowerlip-volume-incr",
              "mouth-lowerlip-volume-decr", "mouth-scale-horiz-incr", "mouth-scale-horiz-decr", "mouth-cupidsbow-incr",
              "mouth-laugh-lines-in", "mouth-dimples-in", "mouth-angles-up"],
    "forehead": ["forehead-scale-vert-incr", "forehead-scale-vert-decr", "forehead-temple-incr", "forehead-trans-backward"],
}
PAIRED = {   # left/right target families that must move together
    "cheek": ["cheek-bones-incr", "cheek-bones-decr", "cheek-volume-incr", "cheek-volume-decr", "cheek-inner-incr"],
    "eye": ["eye-bag-incr", "eye-scale-incr", "eye-scale-decr", "eye-height2-incr", "eye-height2-decr",
            "eye-corner1-up", "eye-corner1-down", "eye-eyefold-down", "eye-trans-in", "eye-trans-out"],
    "ear": ["ear-scale-incr", "ear-scale-decr", "ear-flap-incr", "ear-lobe-incr", "ear-rot-backward"],
}


def face_targets(seed, strength=1.0):
    """A distinct but natural face: a handful of small, seeded shape changes."""
    import random as _r
    r = _r.Random(seed)
    out = []
    for fam, names in FACE_TARGETS.items():
        for n in r.sample(names, 2):
            out.append((f"{fam}/{n}", r.uniform(0.15, 0.55) * strength))
    folder = {"cheek": "cheek", "eye": "eyes", "ear": "ears"}
    for fam, names in PAIRED.items():
        for n in r.sample(names, 2 if fam != "ear" else 1):
            w = r.uniform(0.15, 0.5) * strength
            for side in ("l", "r"):
                out.append((f"{folder[fam]}/{side}-{n}", w))
    return out


HAIR = {
    "black": (0.022, 0.018, 0.016), "dark_brown": (0.075, 0.045, 0.03), "brown": (0.21, 0.13, 0.075),
    "light_brown": (0.3, 0.19, 0.11), "blond": (0.86, 0.66, 0.38), "ash_blond": (0.5, 0.43, 0.33),
    "auburn": (0.3, 0.1, 0.045), "red": (0.42, 0.13, 0.05), "grey": (0.42, 0.41, 0.4), "white": (0.72, 0.7, 0.68),
}
HAIR_DEFAULT = {"african": HAIR["black"], "caucasian": HAIR["brown"], "asian": HAIR["black"]}

EXPRESSIONS = {
    "neutral": {},
    "smile": {"mouth-corner-puller": 0.55, "mouth-elevation": 0.15, "eye-left-slit": 0.2, "eye-right-slit": 0.2},
    "grin": {"mouth-corner-puller": 0.75, "mouth-elevation": 0.2, "eye-left-slit": 0.3, "eye-right-slit": 0.3},
    "soft": {"mouth-corner-puller": 0.3, "eyebrows-left-up": 0.2, "eyebrows-right-up": 0.2},
    "laugh": {"mouth-corner-puller": 0.9, "mouth-elevation": 0.25, "eye-left-slit": 0.5, "eye-right-slit": 0.5},
    "squint": {"eye-left-slit": 0.55, "eye-right-slit": 0.55, "eyebrows-left-down": 0.4, "eyebrows-right-down": 0.4, "mouth-corner-puller": 0.2},
}


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
          tint=None, extra_targets=(), subdiv=0, shift=(0, 0, 0), textures=None, expression="soft", bake=True,
          face_seed=None):
    """Build a posed, clothed person as one mesh object standing on z=0 at the origin.
    With bake=False the live rig is returned instead: (armature object, [mesh objects])."""
    b = base()
    collection = collection or bpy.context.scene.collection
    tint = tint or {}
    ex = list(extra_targets) + (face_targets(face_seed if face_seed is not None else name) if face_seed is not False else [])
    for unit, wgt in (EXPRESSIONS.get(expression, {}) if isinstance(expression, str) else (expression or {})).items():
        ex.append((f"expression/units/{race}/{unit}", wgt))
    mv = shape(gender, race, age, muscle, weight, height, ex)
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
                        rough=0.04 if kind == "eyes" else (0.3 if kind == "teeth" else (0.6 if kind == "hair" else 0.75)),
                        alpha=kind in ("hair", "eyebrows", "eyelashes", "eyes"),
                        hue=(("rgb",) + tuple(tint.get(an, HAIR_DEFAULT.get(race, HAIR_DEFAULT["african"])))) if kind in ("hair", "eyebrows")
                        else tint.get(an),
                        spec=0.6 if kind == "eyes" else (0.12 if kind == "hair" else 0.3))
        pobj = _mesh_obj(f"{name}_{an}", cb, faces, fuv, vt, mat, collection)
        if kind == "hair":
            # 0 at the roots (close to the scalp, high on the head) .. 1 at the tips
            off = np.linalg.norm(co - np.array([r[3] * mv_g[int(r[0])] + r[4] * mv_g[int(r[1])] + r[5] * mv_g[int(r[2])]
                                                if len(r) >= 9 else mv_g[int(r[0])] for r in rows]), axis=1)
            off = off / max(np.percentile(off, 95), 1e-6)
            zz = cb[:, 2]
            drop = (zz.max() - zz) / max(zz.max() - zz.min(), 1e-6)
            tip = np.clip(0.55 * off + 0.65 * drop, 0.0, 1.0)
            at = pobj.data.attributes.new("tip", "FLOAT", "POINT")
            at.data.foreach_set("value", tip.astype(np.float32))
        parts.append((pobj, bind))

    # --- body (only the 'body' group faces, minus what the clothes cover)
    if skin is None:
        skin = f"young_{race}_{gender}"
    sd = _skin_dir(skin)
    sm = _mhmat(os.path.join(sd, [f for f in os.listdir(sd) if f.endswith(".mhmat")][0]))
    smat = skin_material(f"mh_skin_{skin}", os.path.join(sd, sm.get("diffuseTexture", "")), race)
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

    if not bake:
        for ob, _ in parts:
            ob.parent = arm
            if subdiv:
                sm = ob.modifiers.new("sub", "SUBSURF")
                sm.levels = 0
                sm.render_levels = subdiv
        import bmesh as _bm
        bmx = _bm.new()
        bmx.from_mesh(parts[0][0].data)
        _bm.ops.delete(bmx, geom=[v for v in bmx.verts if not v.link_faces], context="VERTS")
        bmx.to_mesh(parts[0][0].data)
        bmx.free()
        return arm, [ob for ob, _ in parts]

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
        "lowerarm01.L": (38, 4, 0), "lowerarm01.R": (38, -4, 0),
    },
    "stand_relaxed": {
        "upperarm01.L": (6, 40, 0), "upperarm01.R": (-10, -38, 0),
        "lowerarm01.L": (36, 4, 0), "lowerarm01.R": (-10, -4, 20),
        "spine03": (0, 0, 7), "head": (0, 0, -16), "upperleg01.L": (0, -4, 0), "upperleg01.R": (-6, 4, 0),
        "lowerleg01.R": (10, 0, 0),
    },
    "hands_hips": {
        "upperarm01.L": (14, 18, 0), "upperarm01.R": (14, -18, 0),
        "lowerarm01.L": (-20, 78, 0), "lowerarm01.R": (-20, -78, 0),
        "head": (0, 0, 12),
    },
    "point": {
        "upperarm01.L": (0, 40, 0), "lowerarm01.L": (36, 4, 0),
        "upperarm01.R": (-70, -34, 0), "lowerarm01.R": (40, 0, 0),
        "head": (-6, 0, 10), "spine03": (0, 0, 6),
    },
    "shade_eyes": {
        "upperarm01.L": (0, 40, 0), "lowerarm01.L": (36, 4, 0),
        "upperarm01.R": (-58, -18, 0), "lowerarm01.R": (-88, 30, 62),
        "head": (-8, 0, 0),
    },
    "walk": {
        "upperleg01.L": (-26, 0, 0), "lowerleg01.L": (12, 0, 0),
        "upperleg01.R": (16, 0, 0), "lowerleg01.R": (30, 0, 0), "foot.R": (-16, 0, 0),
        "upperarm01.L": (18, 40, 0), "upperarm01.R": (-20, -40, 0),
        "lowerarm01.L": (34, 4, 0), "lowerarm01.R": (20, -4, 0),
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


class Actor:
    """A live, riggable person: pose it with world-axis rotations, reach for targets with the
    arms (two-bone IK), curl the fingers, and keyframe the result for animation."""

    FINGERS = [f"finger{i}-{j}" for i in (2, 3, 4, 5) for j in (1, 2, 3)]

    def __init__(self, name, collection=None, **spec):
        self.arm, self.parts = human(name, collection=collection, bake=False, **spec)
        self.ad = self.arm.data
        self.own = {}
        self.touched = set()

    # -- low level
    def _apply(self, update=True):
        ad, arm = self.ad, self.arm
        total = {}
        self._tot = total

        def tot(bn):
            if bn in total:
                return total[bn]
            par = ad.bones[bn].parent
            P = tot(par.name) if par else Matrix.Identity(3)
            D = self.own.get(bn)
            if D is None:
                total[bn] = P
                return P
            Rb = ad.bones[bn].matrix_local.to_3x3()
            pb = arm.pose.bones[bn]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (Rb.inverted() @ P.inverted() @ D @ P @ Rb).to_quaternion()
            total[bn] = D @ P
            return total[bn]

        for bn in list(self.touched):
            if bn not in self.own:
                pb = arm.pose.bones[bn]
                pb.rotation_mode = "QUATERNION"
                pb.rotation_quaternion = (1, 0, 0, 0)
        for bn in self.own:
            tot(bn)
        for bn in ("foot.L", "foot.R", "toe1-1.L", "toe1-1.R", "head"):
            if bn in ad.bones:
                tot(bn)
        self.touched |= set(self.own)
        if update:
            bpy.context.view_layer.update()

    def fk_point(self, bn, p):
        """Where rest-pose point p (armature space) attached to bone bn ends up, computed directly from
        the rotations just set (no scene update needed)."""
        ad = self.ad
        chain = []
        b = ad.bones[bn]
        while b is not None:
            chain.append(b)
            b = b.parent
        chain.reverse()
        tot = self._tot
        pos = None                                      # posed position of the current bone head
        prev_tot, prev_head_rest = None, None
        for b in chain:
            T = tot.get(b.name)
            if T is None:
                T = prev_tot if prev_tot is not None else Matrix.Identity(3)
                tot[b.name] = T
            h = b.head_local
            if pos is None:
                pos = h.copy()
            else:
                pos = pos + prev_tot @ (h - prev_head_rest)
            prev_tot, prev_head_rest = T, h
        return pos + prev_tot @ (Vector(p) - prev_head_rest)

    def ground_fast(self):
        ad = self.ad
        zs = []
        for bn in ("foot.L", "foot.R", "toe1-1.L", "toe1-1.R"):
            if bn in ad.bones:
                zs.append(self.fk_point(bn, ad.bones[bn].tail_local).z)
                zs.append(self.fk_point(bn, ad.bones[bn].head_local).z - 0.06)
        return min(zs) - 0.03

    @staticmethod
    def _mat(rot):
        if isinstance(rot, Matrix):
            return rot
        return (Matrix.Rotation(math.radians(rot[2]), 3, "Z") @ Matrix.Rotation(math.radians(rot[1]), 3, "Y")
                @ Matrix.Rotation(math.radians(rot[0]), 3, "X"))

    # -- posing
    def pose(self, fk, ik=None, grip=None, update=True):
        """fk: {bone: (rx, ry, rz) degrees about world axes}. ik: {"L"/"R": target in the figure's own
        frame} for the wrists. grip: {"L"/"R": 0..1} finger curl."""
        self.own = {bn: self._mat(r) for bn, r in fk.items() if not bn.startswith("_") and bn in self.ad.bones}
        self._apply(update=update or bool(ik) or bool(grip))
        for side, tgt in (ik or {}).items():
            self._reach(side, Vector(tgt))
        for side, amt in (grip or {}).items():
            self._curl(side, amt)

    def _reach(self, side, T):
        pb = self.arm.pose.bones
        ua, la, wr = f"upperarm01.{side}", f"lowerarm01.{side}", f"wrist.{side}"
        for _ in range(2):                               # second pass cleans up the twist bones' drift
            S, E0, W0 = pb[ua].head.copy(), pb[la].head.copy(), pb[wr].head.copy()
            L1, L2 = (E0 - S).length, (W0 - E0).length
            d = T - S
            dist = max(0.05, min(d.length, L1 + L2 - 0.004))
            dn = d.normalized()
            a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
            h = math.sqrt(max(L1 * L1 - a * a, 0.0))
            pole = Vector((0.45 if side == "L" else -0.45, 0.25, -1.0)).normalized()
            p = pole - dn * pole.dot(dn)
            p = p.normalized() if p.length > 1e-6 else Vector((0, 0, -1))
            E = S + dn * a + p * h
            R1 = (E0 - S).rotation_difference(E - S).to_matrix()
            self.own[ua] = R1 @ self.own.get(ua, Matrix.Identity(3))
            self._apply()
            E1, W1 = pb[la].head.copy(), pb[wr].head.copy()
            R2 = (W1 - E1).rotation_difference(S + dn * dist - E1).to_matrix()
            self.own[la] = R2 @ self.own.get(la, Matrix.Identity(3))
            self._apply()

    def _curl(self, side, amt, sign=None):
        pb = self.arm.pose.bones
        k2, k5 = pb[f"finger2-1.{side}"].head, pb[f"finger5-1.{side}"].head
        axis = (k2 - k5).normalized()                    # across the knuckles
        tip = pb[f"finger3-3.{side}"].tail - pb[f"finger3-1.{side}"].head
        palm = pb[f"finger3-1.{side}"].head - pb[f"wrist.{side}"].head
        normal = axis.cross(palm.normalized())           # out of the back of the hand (or the palm)
        sgn = sign if sign is not None else (1.0 if side == "L" else 1.0)
        for i in (2, 3, 4, 5):
            for j, f in ((1, 0.9), (2, 1.0), (3, 0.7)):
                bn = f"finger{i}-{j}.{side}"
                self.own[bn] = Matrix.Rotation(sgn * amt * f * math.radians(62), 3, axis)
        self._apply()
        # make sure the fingers closed toward the palm, not away from it: flip once if they opened
        tip2 = pb[f"finger3-3.{side}"].tail - pb[f"finger3-1.{side}"].head
        wr = pb[f"wrist.{side}"].head
        if sign is None and amt > 0.05:
            before = (pb[f"finger3-1.{side}"].head + tip - wr).length
            after = (pb[f"finger3-3.{side}"].tail - wr).length
            if after > before - 0.005:
                self._curl(side, amt, sign=-sgn)

    def ground(self):
        """Lowest point of the feet (figure frame, z) in the current pose."""
        pb = self.arm.pose.bones
        zs = [pb[b].tail.z for b in ("foot.L", "foot.R", "toe1-1.L", "toe1-1.R") if b in pb]
        return min(zs) - 0.035

    def key(self, frame):
        for bn in self.touched:
            self.arm.pose.bones[bn].keyframe_insert("rotation_quaternion", frame=frame)
