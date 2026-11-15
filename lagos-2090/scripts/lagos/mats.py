"""Lagos 2090 - material library (Cycles node materials).

PBR sets come from ./textures (ambientCG, CC0, 4K). Procedural meshes have no UVs,
so texture sets are box-projected from object coordinates.
"""
import bpy, math
from pathlib import Path
from .core import ROOT

_cache = {}

TEX = {
    "asphalt": ("textures/asphalt", "Asphalt033"),
    "concrete": ("textures/concrete", "Concrete034"),
    "plaster": ("textures/plaster-wall", "Plaster001"),
    "grass": ("textures/grass", "Grass001"),
    "wood": ("textures/wood", "Wood051"),
    "corrugated": ("textures/corrugated-metal", "CorrugatedSteel007A"),
    "facade": ("textures/facade", "Facade001"),
    "rust": ("textures/rust", "Rust001"),
    "metal": ("textures/painted-metal", "Metal032"),
    "tiles": ("textures/tiles", "Tiles015"),
}


def img(path, colorspace="sRGB"):
    im = bpy.data.images.load(str(path), check_existing=True)
    try:
        im.colorspace_settings.name = colorspace
    except Exception:
        pass
    return im


def tex_path(key, m):
    folder, prefix = TEX[key]
    p = ROOT / folder / f"{prefix}_4K-JPG_{m}.jpg"
    return p if p.exists() else None


class NT:
    """Tiny helper around a node tree."""

    def __init__(self, name):
        self.mat = bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.out = self.n("ShaderNodeOutputMaterial")

    def n(self, kind, **props):
        node = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(node, k, v)
        return node

    def l(self, a, b):
        self.nt.links.new(a, b)

    def val(self, node, **inputs):
        for k, v in inputs.items():
            node.inputs[k.replace("_", " ")].default_value = v
        return node

    def math(self, op, a, b=None, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                self.l(x, m.inputs[i])
        return m.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        m = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        for sock, x in ((m.inputs["Factor"], fac), (m.inputs["A"], a), (m.inputs["B"], b)):
            if isinstance(x, (int, float)):
                sock.default_value = x if sock.name == "Factor" else (x, x, x, 1.0)
            elif isinstance(x, (tuple, list)):
                sock.default_value = (*x[:3], 1.0)
            else:
                self.l(x, sock)
        return m.outputs["Result"]

    def coords(self, kind="object", scale=1.0, rot=(0, 0, 0), loc=(0, 0, 0)):
        tc = self.n("ShaderNodeTexCoord")
        mp = self.n("ShaderNodeMapping")
        sock = {"object": "Object", "uv": "UV", "generated": "Generated"}.get(kind)
        if kind == "world":
            g = self.n("ShaderNodeNewGeometry")
            self.l(g.outputs["Position"], mp.inputs["Vector"])
        else:
            self.l(tc.outputs[sock], mp.inputs["Vector"])
        s = (scale,) * 3 if isinstance(scale, (int, float)) else scale
        mp.inputs["Scale"].default_value = s
        mp.inputs["Rotation"].default_value = rot
        mp.inputs["Location"].default_value = loc
        return mp.outputs["Vector"]

    def image(self, path, vec, colorspace="sRGB", box=True, blend=0.25):
        t = self.n("ShaderNodeTexImage")
        t.image = img(path, colorspace)
        if box:
            t.projection = "BOX"
            t.projection_blend = blend
        self.l(vec, t.inputs["Vector"])
        return t

    def noise(self, vec, scale=5.0, detail=4.0, rough=0.55, dim="3D", w=None):
        t = self.n("ShaderNodeTexNoise", noise_dimensions=dim)
        self.val(t, Scale=scale, Detail=detail, Roughness=rough)
        if vec is not None:
            self.l(vec, t.inputs["Vector"])
        if w is not None:
            self.l(w, t.inputs["W"])
        return t

    def ramp(self, fac, stops):
        r = self.n("ShaderNodeValToRGB")
        el = r.color_ramp.elements
        while len(el) < len(stops):
            el.new(0.5)
        for e, (p, c) in zip(el, stops):
            e.position = p
            e.color = (*c[:3], 1.0) if len(c) >= 3 else (c[0],) * 3 + (1.0,)
        self.l(fac, r.inputs["Fac"])
        return r.outputs["Color"]

    def bsdf(self, **inputs):
        b = self.n("ShaderNodeBsdfPrincipled")
        for k, v in inputs.items():
            sock = b.inputs[k.replace("_", " ")]
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, (tuple, list)):
                sock.default_value = (*v[:3], 1.0) if len(sock.default_value) == 4 else v
            else:
                self.l(v, sock)
        self.l(b.outputs[0], self.out.inputs["Surface"])
        return b

    def bump(self, height, strength=0.3, distance=0.01):
        b = self.n("ShaderNodeBump")
        self.val(b, Strength=strength, Distance=distance)
        self.l(height, b.inputs["Height"])
        return b.outputs["Normal"]


def _get(key, fn):
    try:
        ok = key in _cache and _cache[key].name in bpy.data.materials
    except ReferenceError:
        ok = False
    if not ok:
        _cache[key] = fn()
    return _cache[key]


def clear_cache():
    _cache.clear()


# ----------------------------------------------------------------------------- generic
def plain(name, color, rough=0.5, metallic=0.0, emit=None, emit_strength=1.0, alpha=1.0, **kw):
    def make():
        t = NT(name)
        args = dict(Base_Color=color, Roughness=rough, Metallic=metallic, Alpha=alpha, **kw)
        if emit is not None:
            args.update(Emission_Color=emit, Emission_Strength=emit_strength)
        t.bsdf(**args)
        return t.mat
    return _get(("plain", name), make)


def emission(name, color, strength=5.0):
    def make():
        t = NT(name)
        e = t.n("ShaderNodeEmission")
        e.inputs["Color"].default_value = (*color[:3], 1)
        e.inputs["Strength"].default_value = strength
        t.l(e.outputs[0], t.out.inputs["Surface"])
        return t.mat
    return _get(("emit", name), make)


def pbr(key, name=None, scale=0.5, tint=None, tint_fac=1.0, bump=0.35, rough_mul=1.0, rough_add=0.0,
        coords="object", box=True, rot=(0, 0, 0), ao=0.6, dirt=0.0, dirt_color=(0.05, 0.04, 0.03),
        wet=0.0, sat=1.0, val=1.0, object_color=False):
    """Box-projected ambientCG set. scale = tiles per metre."""
    name = name or f"pbr_{key}"

    def make():
        t = NT(name)
        vec = t.coords(coords, scale, rot)
        col = t.image(tex_path(key, "Color"), vec, "sRGB", box).outputs["Color"]
        if tex_path(key, "AmbientOcclusion") and ao > 0:
            aon = t.image(tex_path(key, "AmbientOcclusion"), vec, "Non-Color", box).outputs["Color"]
            col = t.mix(ao, col, aon, "MULTIPLY")
        if sat != 1.0 or val != 1.0:
            hsv = t.n("ShaderNodeHueSaturation")
            t.val(hsv, Saturation=sat, Value=val)
            t.l(col, hsv.inputs["Color"])
            col = hsv.outputs["Color"]
        if object_color:
            oi = t.n("ShaderNodeObjectInfo")
            col = t.mix(tint_fac, col, oi.outputs["Color"], "MULTIPLY")
        elif tint is not None:
            col = t.mix(tint_fac, col, tint, "MULTIPLY")
        rgh = t.image(tex_path(key, "Roughness"), vec, "Non-Color", box).outputs["Color"]
        rgh = t.math("MULTIPLY_ADD", rgh, rough_mul)
        t.nt.nodes[-1].inputs[2].default_value = rough_add
        if dirt > 0:
            nv = t.coords("world", 1.0)
            big = t.noise(nv, 0.35, 5.0, 0.6).outputs["Fac"]
            m = t.ramp(big, [(0.42, (0, 0, 0)), (0.75, (1, 1, 1))])
            col = t.mix(t.math("MULTIPLY", m, dirt), col, dirt_color, "MIX")
        args = dict(Base_Color=col, Roughness=rgh)
        if tex_path(key, "Metalness"):
            args["Metallic"] = t.image(tex_path(key, "Metalness"), vec, "Non-Color", box).outputs["Color"]
        if bump > 0:
            lum = t.n("ShaderNodeRGBToBW")
            t.l(t.image(tex_path(key, "Color"), vec, "sRGB", box).outputs["Color"], lum.inputs[0])
            args["Normal"] = t.bump(lum.outputs[0], bump, 0.02)
        t.bsdf(**args)
        return t.mat
    return _get(("pbr", name), make)


def ground(key, name=None, scale=0.25, tint=None, rough_mul=1.0, puddles=0.0, normal=1.0, dirt=0.3,
           dirt_color=(0.16, 0.11, 0.07), val=1.0):
    """Flat ground: world-XY mapped, real normal map, optional puddles / dust drift."""
    name = name or f"ground_{key}"

    def make():
        t = NT(name)
        vec = t.coords("world", scale)
        col = t.image(tex_path(key, "Color"), vec, "sRGB", False).outputs["Color"]
        if tex_path(key, "AmbientOcclusion"):
            col = t.mix(0.7, col, t.image(tex_path(key, "AmbientOcclusion"), vec, "Non-Color", False).outputs["Color"], "MULTIPLY")
        if val != 1.0:
            col = t.mix(1.0, col, (val, val, val), "MULTIPLY")
        if tint is not None:
            col = t.mix(1.0, col, tint, "MULTIPLY")
        big = t.noise(t.coords("world", 1.0), 0.18, 6.0, 0.62).outputs["Fac"]
        if dirt > 0:
            m = t.ramp(big, [(0.40, (0, 0, 0)), (0.72, (1, 1, 1))])
            col = t.mix(t.math("MULTIPLY", m, dirt), col, dirt_color)
        rgh = t.image(tex_path(key, "Roughness"), vec, "Non-Color", False).outputs["Color"]
        rgh = t.math("MULTIPLY", rgh, rough_mul)
        nm = t.n("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        t.l(t.image(tex_path(key, "NormalGL"), vec, "Non-Color", False).outputs["Color"], nm.inputs["Color"])
        nrm = nm.outputs["Normal"]
        if puddles > 0:
            pn = t.noise(t.coords("world", 1.0, loc=(13.1, 7.7, 0)), 0.22, 3.0, 0.5).outputs["Fac"]
            pm = t.ramp(pn, [(1.0 - 0.52 * puddles - 0.06, (0, 0, 0)), (1.0 - 0.52 * puddles, (1, 1, 1))])
            col = t.mix(pm, col, t.mix(1.0, col, (0.35, 0.33, 0.3), "MULTIPLY"))
            rgh = t.mix(pm, rgh, 0.03)
            geo = t.n("ShaderNodeNewGeometry")
            mixn = t.n("ShaderNodeMix", data_type="VECTOR")
            t.l(pm, mixn.inputs["Factor"]); t.l(nrm, mixn.inputs["A"]); t.l(geo.outputs["Normal"], mixn.inputs["B"])
            nrm = mixn.outputs["Result"]
        t.bsdf(Base_Color=col, Roughness=rgh, Normal=nrm)
        return t.mat
    return _get(("ground", name), make)


def painted(name, color=None, grime=0.6, scale=0.35, streaks=0.8, rough=0.82, object_color=False, base_h=0.0, top_h=None,
            peel=0.25, peel_color=(0.5, 0.48, 0.45)):
    """Painted plaster / concrete wall with rain streaks, patchy repaint, peeling and splash
    dirt near the ground - the typical weathering of Lagos facades."""
    def make():
        t = NT(name)
        vec = t.coords("object", scale)
        pl = t.image(tex_path("plaster", "Color"), vec, "sRGB", True, blend=0.0).outputs["Color"]
        bw = t.n("ShaderNodeRGBToBW"); t.l(pl, bw.inputs[0])
        lum = t.ramp(bw.outputs[0], [(0.2, (0.55, 0.55, 0.55)), (0.85, (1.1, 1.1, 1.1))])
        if object_color:
            paint = t.n("ShaderNodeObjectInfo").outputs["Color"]
        else:
            paint = t.n("ShaderNodeRGB"); paint.outputs[0].default_value = (*color, 1); paint = paint.outputs[0]
        wv = t.coords("world", 1.0)
        big = t.noise(wv, 0.22, 3.0, 0.6).outputs["Fac"]
        # sun-bleached / repainted patches shift the paint value
        fade = t.ramp(big, [(0.3, (0.78, 0.8, 0.82)), (0.7, (1.12, 1.08, 1.02))])
        col = t.mix(1.0, t.mix(1.0, paint, fade, "MULTIPLY"), lum, "MULTIPLY")
        if peel > 0:
            pn = t.noise(wv, 1.3, 5.0, 0.72).outputs["Fac"]
            pm = t.ramp(pn, [(0.66 - 0.12 * peel, (0, 0, 0)), (0.70, (1, 1, 1))])
            col = t.mix(pm, col, t.mix(1.0, pl, peel_color, "MULTIPLY"))
        # vertical rain streaks / mould: noise stretched along Z
        sv = t.coords("world", (2.4, 2.4, 0.05))
        sn = t.noise(sv, 2.0, 3.0, 0.65).outputs["Fac"]
        sm = t.ramp(sn, [(0.42, (0, 0, 0)), (0.72, (1, 1, 1))])
        bm = t.ramp(big, [(0.3, (0.15, 0.15, 0.15)), (0.65, (1, 1, 1))])
        st = t.math("MULTIPLY", t.math("MULTIPLY", sm, bm), streaks * grime * 1.3, clamp=True)
        col = t.mix(st, col, (0.03, 0.028, 0.024))
        # splash-back dirt band near the ground (world Z)
        sep = t.n("ShaderNodeSeparateXYZ"); t.l(wv, sep.inputs[0])
        gr = t.n("ShaderNodeMapRange")
        t.l(sep.outputs["Z"], gr.inputs["Value"])
        gr.inputs["From Min"].default_value = base_h + 1.6; gr.inputs["From Max"].default_value = base_h
        g2 = t.math("MULTIPLY", t.math("POWER", gr.outputs[0], 1.6), t.math("ADD", 0.45, big))
        col = t.mix(t.math("MULTIPLY", g2, 0.85 * grime, clamp=True), col, (0.14, 0.095, 0.06))
        t.bsdf(Base_Color=col, Roughness=rough, Normal=t.bump(bw.outputs[0], 0.2, 0.02))
        return t.mat
    return _get(("painted", name), make)


def glass(name="glass_window", tint=(0.03, 0.045, 0.05), rough=0.08, lit=0.0, lit_color=(1.0, 0.72, 0.38)):
    """Window glass as an opaque dark mirror (cheap, reads right at distance); 'lit'
    adds a share of warm lit windows keyed on object-space noise cells."""
    def make():
        t = NT(name)
        args = dict(Base_Color=tint, Roughness=rough, Metallic=0.0, Specular_IOR_Level=1.0, IOR=1.52, Coat_Weight=1.0, Coat_Roughness=0.03)
        if lit > 0:
            g = t.n("ShaderNodeNewGeometry")
            wn = t.n("ShaderNodeTexWhiteNoise", noise_dimensions="3D")
            snap = t.n("ShaderNodeVectorMath", operation="SNAP")
            t.l(g.outputs["Position"], snap.inputs[0]); snap.inputs[1].default_value = (3.2, 3.2, 3.0)
            t.l(snap.outputs[0], wn.inputs["Vector"])
            on = t.math("GREATER_THAN", wn.outputs["Value"], 1.0 - lit)
            args["Emission_Color"] = lit_color
            args["Emission_Strength"] = t.math("MULTIPLY", on, 0.9)
        t.bsdf(**args)
        return t.mat
    return _get(("glass", name), make)


def clear_glass(name="glass_clear", tint=(0.9, 0.95, 0.93), rough=0.02, dirt=0.25):
    def make():
        t = NT(name)
        g = t.n("ShaderNodeBsdfGlossy"); g.inputs["Roughness"].default_value = rough
        tr = t.n("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (*tint, 1)
        fr = t.n("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5
        fac = fr.outputs[0]
        if dirt > 0:
            n = t.noise(t.coords("object", 1.0), 2.5, 6.0, 0.7).outputs["Fac"]
            d = t.ramp(n, [(0.45, (0, 0, 0)), (0.9, (1, 1, 1))])
            df = t.n("ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (0.5, 0.42, 0.33, 1)
            m0 = t.n("ShaderNodeMixShader"); t.l(fac, m0.inputs[0]); t.l(tr.outputs[0], m0.inputs[1]); t.l(g.outputs[0], m0.inputs[2])
            m1 = t.n("ShaderNodeMixShader"); t.l(t.math("MULTIPLY", d, dirt), m1.inputs[0]); t.l(m0.outputs[0], m1.inputs[1]); t.l(df.outputs[0], m1.inputs[2])
            t.l(m1.outputs[0], t.out.inputs["Surface"])
        else:
            m0 = t.n("ShaderNodeMixShader"); t.l(fac, m0.inputs[0]); t.l(tr.outputs[0], m0.inputs[1]); t.l(g.outputs[0], m0.inputs[2])
            t.l(m0.outputs[0], t.out.inputs["Surface"])
        return t.mat
    return _get(("cglass", name), make)


def leaf(name, color=(0.09, 0.22, 0.04), color2=(0.2, 0.33, 0.06), rough=0.45, translucency=0.45, vary=0.6):
    """Two-sided foliage: diffuse + translucent back-lighting, per-object / per-island hue variation."""
    def make():
        t = NT(name)
        oi = t.n("ShaderNodeObjectInfo")
        g = t.n("ShaderNodeNewGeometry")
        n = t.noise(t.coords("object", 1.0), 3.0, 2.0, 0.5).outputs["Fac"]
        f = t.math("ADD", t.math("MULTIPLY", oi.outputs["Random"], vary), t.math("MULTIPLY", n, 1.0 - vary), clamp=True)
        col = t.mix(f, color, color2)
        b = t.n("ShaderNodeBsdfPrincipled")
        t.l(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
        b.inputs["Specular IOR Level"].default_value = 0.6
        tl = t.n("ShaderNodeBsdfTranslucent")
        t.l(t.mix(1.0, col, (1.6, 1.9, 0.6), "MULTIPLY"), tl.inputs["Color"])
        m = t.n("ShaderNodeMixShader"); m.inputs[0].default_value = translucency
        t.l(b.outputs[0], m.inputs[1]); t.l(tl.outputs[0], m.inputs[2])
        t.l(m.outputs[0], t.out.inputs["Surface"])
        return t.mat
    return _get(("leaf", name), make)


def cloth(name, color, color2=None, pattern="plain", scale=8.0, rough=0.85, translucency=0.3):
    """Woven cloth; optional stripes / ankara-like wax-print pattern, light passes through."""
    def make():
        t = NT(name)
        vec = t.coords("uv", 1.0)
        col = None
        if pattern == "stripes":
            w = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
            t.val(w, Scale=scale, Distortion=0.0); t.l(vec, w.inputs["Vector"])
            col = t.mix(t.ramp(w.outputs["Fac"], [(0.48, (0, 0, 0)), (0.52, (1, 1, 1))]), color, color2)
        elif pattern == "ankara":
            v = t.n("ShaderNodeTexVoronoi", feature="F1", distance="CHEBYCHEV")
            t.val(v, Scale=scale); t.l(vec, v.inputs["Vector"])
            rings = t.math("FRACT", t.math("MULTIPLY", v.outputs["Distance"], 4.0))
            m = t.ramp(rings, [(0.45, (0, 0, 0)), (0.5, (1, 1, 1))])
            c3 = t.mix(1.0, v.outputs["Color"], color2, "OVERLAY")
            col = t.mix(m, color, t.mix(0.35, color2, c3))
        elif pattern == "check":
            c = t.n("ShaderNodeTexChecker"); t.val(c, Scale=scale); t.l(vec, c.inputs["Vector"])
            c.inputs["Color1"].default_value = (*color, 1); c.inputs["Color2"].default_value = (*color2, 1)
            col = c.outputs["Color"]
        else:
            rgb = t.n("ShaderNodeRGB"); rgb.outputs[0].default_value = (*color, 1); col = rgb.outputs[0]
        weave = t.n("ShaderNodeTexWave", wave_type="BANDS"); t.val(weave, Scale=220.0, Distortion=1.5)
        t.l(vec, weave.inputs["Vector"])
        b = t.n("ShaderNodeBsdfPrincipled")
        t.l(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
        b.inputs["Sheen Weight"].default_value = 0.4
        t.l(t.bump(weave.outputs["Fac"], 0.08, 0.001), b.inputs["Normal"])
        tl = t.n("ShaderNodeBsdfTranslucent"); t.l(col, tl.inputs["Color"])
        m = t.n("ShaderNodeMixShader"); m.inputs[0].default_value = translucency
        t.l(b.outputs[0], m.inputs[1]); t.l(tl.outputs[0], m.inputs[2])
        t.l(m.outputs[0], t.out.inputs["Surface"])
        return t.mat
    return _get(("cloth", name), make)


def water(name="lagoon", deep=(0.012, 0.045, 0.06), scale=1.0, chop=1.0, speed=1.0, rough=0.035):
    """Lagoon surface: glossy with two layers of animated ripples (4D noise, W driven by
    frame) + long swell. Sun glitter comes from the perturbed normals."""
    def make():
        t = NT(name)
        tval = t.n("ShaderNodeValue"); tval.label = "time"; tval.name = "time"
        d = tval.outputs[0].driver_add("default_value").driver
        d.expression = f"frame/24.0*{speed}"
        wv = t.coords("world", (1.0 * scale, 1.7 * scale, 1.0))
        n1 = t.noise(wv, 1.3, 3.0, 0.55, "4D", t.math("MULTIPLY", tval.outputs[0], 0.55)).outputs["Fac"]
        wv2 = t.coords("world", (3.1 * scale, 4.4 * scale, 1.0), rot=(0, 0, 0.6))
        n2 = t.noise(wv2, 2.2, 2.0, 0.5, "4D", t.math("MULTIPLY", tval.outputs[0], 1.1)).outputs["Fac"]
        wv3 = t.coords("world", (0.12 * scale, 0.3 * scale, 1.0), rot=(0, 0, -0.3))
        n3 = t.noise(wv3, 1.0, 1.0, 0.5, "4D", t.math("MULTIPLY", tval.outputs[0], 0.2)).outputs["Fac"]
        h = t.math("ADD", t.math("ADD", t.math("MULTIPLY", n1, 0.55), t.math("MULTIPLY", n2, 0.25)), t.math("MULTIPLY", n3, 0.9))
        nrm = t.bump(h, 0.55 * chop, 0.25)
        lw = t.n("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
        col = t.mix(lw.outputs["Facing"], (0.03, 0.07, 0.07), deep)
        t.bsdf(Base_Color=col, Roughness=rough, Normal=nrm, Specular_IOR_Level=0.5, IOR=1.33, Metallic=0.0,
               Coat_Weight=1.0, Coat_Roughness=rough, Coat_Normal=nrm)
        return t.mat
    return _get(("water", name), make)


def sign(name, image_path, emit=0.0, rough=0.6, alpha=False, flicker=None):
    """UV-mapped painted / illuminated sign from a generated image."""
    def make():
        t = NT(name)
        vec = t.coords("uv", 1.0)
        tx = t.image(image_path, vec, "sRGB", False)
        args = dict(Base_Color=tx.outputs["Color"], Roughness=rough)
        if emit > 0:
            args["Emission_Color"] = tx.outputs["Color"]
            if flicker is not None:
                v = t.n("ShaderNodeValue"); v.name = "flicker"; v.outputs[0].default_value = 1.0
                args["Emission_Strength"] = t.math("MULTIPLY", v.outputs[0], emit)
            else:
                args["Emission_Strength"] = emit
        if alpha:
            args["Alpha"] = tx.outputs["Alpha"]
        t.bsdf(**args)
        return t.mat
    return _get(("sign", name), make)


def solar_panel(name="solar_panel"):
    def make():
        t = NT(name)
        vec = t.coords("uv", 1.0)
        br = t.n("ShaderNodeTexBrick")
        br.offset = 0.0
        t.val(br, Scale=1.0, Mortar_Size=0.012, Brick_Width=0.165, Row_Height=0.165, Bias=0.0)
        br.inputs["Color1"].default_value = (0.012, 0.02, 0.055, 1); br.inputs["Color2"].default_value = (0.016, 0.028, 0.07, 1)
        br.inputs["Mortar"].default_value = (0.55, 0.57, 0.6, 1)
        t.l(vec, br.inputs["Vector"])
        t.bsdf(Base_Color=br.outputs["Color"], Roughness=0.12, Metallic=0.0, Coat_Weight=1.0, Coat_Roughness=0.03, Specular_IOR_Level=0.8)
        return t.mat
    return _get(("solar", name), make)


def striped(name, c1, c2, period=0.5, axis="X", coords="object", rough=0.6):
    """Hard two-colour stripes (kerbs, barriers) in object space."""
    def make():
        t = NT(name)
        sep = t.n("ShaderNodeSeparateXYZ"); t.l(t.coords(coords, 1.0), sep.inputs[0])
        f = t.math("FRACT", t.math("DIVIDE", sep.outputs[axis], period * 2))
        m = t.math("GREATER_THAN", f, 0.5)
        col = t.mix(m, c1, c2)
        n = t.noise(t.coords("object", 1.0), 6.0, 5.0, 0.7).outputs["Fac"]
        col = t.mix(t.ramp(n, [(0.5, (0, 0, 0)), (0.85, (0.7, 0.7, 0.7))]), col, (0.2, 0.18, 0.16))
        t.bsdf(Base_Color=col, Roughness=rough)
        return t.mat
    return _get(("striped", name), make)


def car_paint(name, color, rough=0.35, wear=0.5, dust=0.4):
    """Worn vehicle paint: clearcoat, scratches/chips showing primer, dust on lower panels."""
    def make():
        t = NT(name)
        ov = t.coords("object", 1.0)
        n = t.noise(ov, 9.0, 8.0, 0.75).outputs["Fac"]
        chips = t.ramp(n, [(0.66 - 0.08 * wear, (0, 0, 0)), (0.70, (1, 1, 1))])
        rgb = t.n("ShaderNodeRGB"); rgb.outputs[0].default_value = (*color, 1)
        col = t.mix(t.math("MULTIPLY", chips, wear), rgb.outputs[0], (0.22, 0.17, 0.13))
        sep = t.n("ShaderNodeSeparateXYZ"); t.l(t.n("ShaderNodeTexCoord").outputs["Generated"], sep.inputs[0])
        low = t.n("ShaderNodeMapRange"); t.l(sep.outputs["Z"], low.inputs["Value"])
        low.inputs["From Min"].default_value = 0.45; low.inputs["From Max"].default_value = 0.0
        big = t.noise(ov, 1.5, 4.0, 0.6).outputs["Fac"]
        dm = t.math("MULTIPLY", t.math("MULTIPLY", low.outputs[0], t.math("ADD", big, 0.3)), dust, clamp=True)
        col = t.mix(dm, col, (0.32, 0.24, 0.16))
        rg = t.mix(dm, t.mix(chips, rough, 0.8), 0.9)
        t.bsdf(Base_Color=col, Roughness=rg, Metallic=0.0, Coat_Weight=0.6, Coat_Roughness=0.15)
        return t.mat
    return _get(("carpaint", name), make)
