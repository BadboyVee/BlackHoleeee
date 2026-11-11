"""Shared PBR material library (Cycles, procedural — no image textures).

    from tb import materials
    mat = materials.get("paint_light")

Every material is created once and cached by name ("TB_<name>").
Emissive materials expose a Value node called "Strength" (0 = off) which the rig
drives from the control object, so lights can be switched from one place.
"""
import bpy
from . import spec

PREFIX = "TB_"
_BUILDERS = {}


def register(fn):
    _BUILDERS[fn.__name__] = fn
    return fn


def get(name):
    """Return the shared material `name`, building it on first use."""
    mat = bpy.data.materials.get(PREFIX + name)
    if mat is not None:
        return mat
    if name not in _BUILDERS:
        raise KeyError("unknown material %r; available: %s" % (name, ", ".join(sorted(_BUILDERS))))
    mat = bpy.data.materials.new(PREFIX + name)
    _BUILDERS[name](mat)
    return mat


def names():
    return sorted(_BUILDERS)


# ------------------------------------------------------------------ node helpers
class N:
    """Tiny helper around a material node tree."""

    def __init__(self, mat):
        self.mat = mat
        self.nt = mat.node_tree
        self.nodes = self.nt.nodes
        self.links = self.nt.links
        self.bsdf = next(n for n in self.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
        self.out = next(n for n in self.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
        self._x = -300

    def new(self, kind, **props):
        n = self.nodes.new(kind)
        n.location = (self._x, 300 - 40 * (len(self.nodes) % 12))
        self._x -= 40
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.links.new(a, b)

    def set(self, **inputs):
        """Set Principled inputs by name, e.g. set(Base_Color=(...), Roughness=0.3)."""
        for k, v in inputs.items():
            sock = self.bsdf.inputs[k.replace('_', ' ')]
            if isinstance(v, (tuple, list)) and len(v) == 3:
                v = (*v, 1.0)
            sock.default_value = v

    def coords(self, kind='Object', scale=(1, 1, 1), rotation=(0, 0, 0)):
        tc = self.new('ShaderNodeTexCoord')
        mp = self.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = scale
        mp.inputs['Rotation'].default_value = rotation
        self.link(tc.outputs[kind], mp.inputs['Vector'])
        return mp.outputs['Vector']

    def bump(self, height_socket, strength=0.2, distance=0.001, normal=None):
        b = self.new('ShaderNodeBump')
        b.inputs['Strength'].default_value = strength
        b.inputs['Distance'].default_value = distance
        self.link(height_socket, b.inputs['Height'])
        if normal is not None:
            self.link(normal, b.inputs['Normal'])
        return b.outputs['Normal']

    def ramp(self, fac, stops):
        r = self.new('ShaderNodeValToRGB')
        els = r.color_ramp.elements
        while len(els) < len(stops):
            els.new(0.5)
        for e, (pos, col) in zip(els, stops):
            e.position = pos
            e.color = (*col, 1.0) if len(col) == 3 else col
        self.link(fac, r.inputs['Factor'] if 'Factor' in r.inputs else r.inputs[0])
        return r.outputs['Color']

    def math(self, op, a, b=None, clamp=False):
        m = self.new('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                self.link(v, m.inputs[i])
        return m.outputs[0]

    def mix_val(self, fac, a, b):
        """Scalar mix: a*(1-fac) + b*fac."""
        m = self.new('ShaderNodeMix', data_type='FLOAT')
        for sock, v in ((m.inputs[0], fac), (m.inputs[2], a), (m.inputs[3], b)):
            if isinstance(v, (int, float)):
                sock.default_value = float(v)
            else:
                self.link(v, sock)
        return m.outputs[0]

    def mix_rgb(self, fac, a, b, blend='MIX'):
        m = self.new('ShaderNodeMix', data_type='RGBA', blend_type=blend)
        for sock, v in ((m.inputs[0], fac), (m.inputs[6], a), (m.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, (tuple, list)):
                sock.default_value = (*v, 1.0) if len(v) == 3 else v
            else:
                self.link(v, sock)
        return m.outputs[2]


def _noise(n, vec, scale, detail=2.0, rough=0.5):
    t = n.new('ShaderNodeTexNoise')
    t.inputs['Scale'].default_value = scale
    t.inputs['Detail'].default_value = detail
    t.inputs['Roughness'].default_value = rough
    n.link(vec, t.inputs['Vector'])
    return t.outputs['Factor']


# ------------------------------------------------------------------ paint
def _paint(mat, colour, metallic, rough, flake=0.012, coat=1.0, coat_rough=0.025):
    n = N(mat)
    n.set(Base_Color=colour, Metallic=metallic, Roughness=rough,
          Coat_Weight=coat, Coat_Roughness=coat_rough, Coat_IOR=1.5)
    # fine metallic-flake sparkle in the base layer only (the clearcoat stays mirror smooth)
    vec = n.coords('Object', scale=(1, 1, 1))
    v = n.new('ShaderNodeTexVoronoi')
    v.inputs['Scale'].default_value = 9000.0
    n.link(vec, v.inputs['Vector'])
    nrm = n.bump(v.outputs['Distance'], strength=flake * 8, distance=0.0002)
    n.link(nrm, n.bsdf.inputs['Normal'])


@register
def paint_light(mat):
    """Pale glacier-blue pearl paint with clearcoat (front / lower body)."""
    _paint(mat, spec.COLOURS['paint_light'], metallic=0.30, rough=0.42)


@register
def paint_dark(mat):
    """Deep navy metallic with clearcoat (roof, rear body)."""
    _paint(mat, spec.COLOURS['paint_dark'], metallic=0.75, rough=0.34)


@register
def paint_black(mat):
    """Gloss black paint (pillars, trim panels)."""
    _paint(mat, (0.004, 0.004, 0.005), metallic=0.0, rough=0.30, flake=0.0)


# ------------------------------------------------------------------ carbon fibre
def _carbon(mat, gloss=True, tint=(0.010, 0.011, 0.013), scale=380.0):
    """2x2 twill weave from two crossed wave bands, object-space mapped."""
    n = N(mat)
    vec = n.coords('Object', scale=(scale, scale, scale), rotation=(0, 0, 0.785398))
    sep = n.new('ShaderNodeSeparateXYZ')
    n.link(vec, sep.inputs[0])
    # diagonal twill: fract(x + floor(y)) style stripes
    fy = n.math('FLOOR', sep.outputs['Y'])
    sx = n.math('ADD', sep.outputs['X'], fy)
    fr = n.math('FRACT', n.math('MULTIPLY', sx, 0.5))
    tow = n.math('GREATER_THAN', fr, 0.5)
    # rounding of each tow for bump
    fx = n.math('FRACT', sep.outputs['X'])
    fyy = n.math('FRACT', sep.outputs['Y'])
    warp = n.math('SINE', n.math('MULTIPLY', fx, 3.14159))
    weft = n.math('SINE', n.math('MULTIPLY', fyy, 3.14159))
    h = n.mix_val(tow, warp, weft)
    col = n.mix_rgb(tow, tuple(c * 0.55 for c in tint), tuple(c * 1.9 for c in tint))
    n.link(col, n.bsdf.inputs['Base Color'])
    n.set(Metallic=0.35, Roughness=0.34 if gloss else 0.5,
          Coat_Weight=1.0 if gloss else 0.15, Coat_Roughness=0.03 if gloss else 0.35)
    aniso = n.mix_val(tow, 0.0, 0.25)
    n.link(aniso, n.bsdf.inputs['Anisotropic Rotation'])
    n.bsdf.inputs['Anisotropic'].default_value = 0.6
    n.link(n.bump(h, strength=0.12, distance=0.0003), n.bsdf.inputs['Normal'])


@register
def carbon_gloss(mat):
    """Lacquered exposed carbon fibre (splitter, diffuser, sills, tub)."""
    _carbon(mat, gloss=True)


@register
def carbon_matte(mat):
    """Satin carbon fibre (underbody, inner structures)."""
    _carbon(mat, gloss=False)


@register
def carbon_blue(mat):
    """Blue-tinted lacquered carbon (dark body panels)."""
    _carbon(mat, gloss=True, tint=(0.008, 0.016, 0.034))


# ------------------------------------------------------------------ glass
def _glass(mat, tint, rough=0.0, ior=1.50, shadow_pass=0.85):
    """Glass that lets light through for shadow rays (keeps cabins lit, renders clean)."""
    n = N(mat)
    n.set(Base_Color=tint, Roughness=rough, IOR=ior, Transmission_Weight=1.0, Metallic=0.0)
    tr = n.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (*[min(1.0, c * shadow_pass + (1 - shadow_pass) * 0.2) for c in tint], 1.0)
    lp = n.new('ShaderNodeLightPath')
    mx = n.new('ShaderNodeMixShader')
    n.link(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    n.link(n.bsdf.outputs[0], mx.inputs[1])
    n.link(tr.outputs[0], mx.inputs[2])
    n.link(mx.outputs[0], n.out.inputs['Surface'])
    mat.use_transparent_shadow = True


@register
def glass_clear(mat):
    """Clear laminated glass (lamp covers, instrument crystals)."""
    _glass(mat, (0.97, 0.985, 0.98))


@register
def glass_tint(mat):
    """Lightly smoked automotive glazing (windshield, side glass)."""
    _glass(mat, (0.30, 0.36, 0.38))


@register
def glass_dark(mat):
    """Privacy-dark glazing (roof panels, rear deck glass)."""
    _glass(mat, (0.06, 0.075, 0.085))


@register
def glass_red(mat):
    """Red lamp lens."""
    _glass(mat, (0.55, 0.01, 0.01))


@register
def crystal(mat):
    """Cut crystal glass (console dials)."""
    _glass(mat, (0.96, 0.98, 1.0), ior=1.62)


# ------------------------------------------------------------------ metals
@register
def chrome(mat):
    N(mat).set(Base_Color=(0.92, 0.92, 0.93), Metallic=1.0, Roughness=0.03)


@register
def alu_polished(mat):
    """Polished aluminium (C-line strip, console blade, trim)."""
    N(mat).set(Base_Color=(0.86, 0.87, 0.88), Metallic=1.0, Roughness=0.10)


@register
def alu_brushed(mat):
    """Brushed / anodised aluminium."""
    n = N(mat)
    n.set(Base_Color=(0.72, 0.73, 0.75), Metallic=1.0, Roughness=0.28, Anisotropic=0.7)
    vec = n.coords('Object', scale=(4, 900, 900))
    n.link(n.bump(_noise(n, vec, 60.0, 3.0), strength=0.08, distance=0.0002), n.bsdf.inputs['Normal'])


@register
def alu_knurled(mat):
    """Diamond-knurled aluminium (dial rims, switch caps)."""
    n = N(mat)
    n.set(Base_Color=(0.80, 0.81, 0.83), Metallic=1.0, Roughness=0.22)
    vec = n.coords('Object', scale=(1400, 1400, 1400), rotation=(0, 0, 0.785398))
    sep = n.new('ShaderNodeSeparateXYZ')
    n.link(vec, sep.inputs[0])
    a = n.math('ABSOLUTE', n.math('SINE', sep.outputs['X']))
    b = n.math('ABSOLUTE', n.math('SINE', sep.outputs['Z']))
    n.link(n.bump(n.math('MULTIPLY', a, b), strength=0.9, distance=0.0006), n.bsdf.inputs['Normal'])


@register
def alu_dark(mat):
    """Dark anodised / gunmetal (wheel inner faces, brackets)."""
    N(mat).set(Base_Color=(0.045, 0.047, 0.052), Metallic=1.0, Roughness=0.32)


@register
def alu_machined(mat):
    """Diamond-cut machined wheel face."""
    n = N(mat)
    n.set(Base_Color=(0.80, 0.81, 0.83), Metallic=1.0, Roughness=0.16, Anisotropic=0.5,
          Coat_Weight=0.6, Coat_Roughness=0.04)


@register
def titanium(mat):
    """Heat-tinted titanium (exhaust)."""
    n = N(mat)
    vec = n.coords('Object')
    col = n.ramp(_noise(n, vec, 6.0, 2.0), [(0.25, (0.50, 0.46, 0.42)), (0.55, (0.36, 0.34, 0.42)),
                                            (0.8, (0.52, 0.42, 0.30))])
    n.link(col, n.bsdf.inputs['Base Color'])
    n.set(Metallic=1.0, Roughness=0.26)


@register
def steel_dark(mat):
    """Dark steel / fasteners."""
    N(mat).set(Base_Color=(0.14, 0.14, 0.15), Metallic=1.0, Roughness=0.38)


# ------------------------------------------------------------------ rubber / plastic
@register
def rubber_tyre(mat):
    n = N(mat)
    n.set(Base_Color=(0.012, 0.012, 0.013), Roughness=0.72, Specular_IOR_Level=0.35)
    vec = n.coords('Object')
    n.link(n.bump(_noise(n, vec, 900.0, 2.0), strength=0.15, distance=0.0002), n.bsdf.inputs['Normal'])


@register
def rubber_seal(mat):
    N(mat).set(Base_Color=(0.008, 0.008, 0.008), Roughness=0.6)


@register
def plastic_black(mat):
    """Satin black plastic (grille frames, liners, housings)."""
    N(mat).set(Base_Color=(0.010, 0.010, 0.011), Roughness=0.45)


@register
def plastic_gloss(mat):
    """Piano black."""
    N(mat).set(Base_Color=(0.004, 0.004, 0.004), Roughness=0.06, Coat_Weight=1.0, Coat_Roughness=0.02)


@register
def mesh_black(mat):
    """Black grille mesh wire."""
    N(mat).set(Base_Color=(0.006, 0.006, 0.007), Roughness=0.38, Metallic=0.6)


@register
def void_black(mat):
    """Near-zero reflectance for the depths behind grilles and ducts."""
    N(mat).set(Base_Color=(0.001, 0.001, 0.001), Roughness=0.9, Specular_IOR_Level=0.0)


# ------------------------------------------------------------------ interior
def _leather(mat, colour, grain=0.35, rough=0.52, sheen=0.12):
    n = N(mat)
    n.set(Base_Color=colour, Roughness=rough, Sheen_Weight=sheen, Sheen_Roughness=0.4,
          Specular_IOR_Level=0.4, Sheen_Tint=tuple(min(1.0, c * 2.2 + 0.05) for c in colour))
    vec = n.coords('Object')
    v = n.new('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE')
    v.inputs['Scale'].default_value = 1400.0
    n.link(vec, v.inputs['Vector'])
    fine = _noise(n, vec, 500.0, 3.0)
    h = n.math('ADD', n.math('MULTIPLY', v.outputs['Distance'], 2.0), n.math('MULTIPLY', fine, 0.3))
    n.link(n.bump(h, strength=grain, distance=0.0003), n.bsdf.inputs['Normal'])


@register
def leather_light(mat):
    """Pale blue full-grain leather."""
    _leather(mat, spec.COLOURS['leather_light'])


@register
def leather_dark(mat):
    """Dark navy leather."""
    _leather(mat, spec.COLOURS['leather_dark'])


@register
def leather_perforated(mat):
    """Pale blue leather with a woven / perforated texture (seat + door inserts)."""
    n = N(mat)
    c = spec.COLOURS['leather_light']
    n.set(Roughness=0.6, Sheen_Weight=0.12, Specular_IOR_Level=0.35)
    vec = n.coords('Object', scale=(260, 260, 260), rotation=(0, 0, 0.785398))
    sep = n.new('ShaderNodeSeparateXYZ')
    n.link(vec, sep.inputs[0])
    a = n.math('SINE', n.math('MULTIPLY', sep.outputs['X'], 6.2832))
    b = n.math('SINE', n.math('MULTIPLY', sep.outputs['Z'], 6.2832))
    c2 = n.math('SINE', n.math('MULTIPLY', sep.outputs['Y'], 6.2832))
    h = n.math('MULTIPLY', n.math('MULTIPLY', a, b), c2)
    col = n.mix_rgb(n.math('MULTIPLY', n.math('ADD', h, 1.0), 0.5), tuple(x * 0.72 for x in c), tuple(x * 1.06 for x in c))
    n.link(col, n.bsdf.inputs['Base Color'])
    n.link(n.bump(h, strength=0.5, distance=0.0008), n.bsdf.inputs['Normal'])


@register
def alcantara_dark(mat):
    n = N(mat)
    n.set(Base_Color=(0.020, 0.024, 0.030), Roughness=0.95, Sheen_Weight=0.35, Sheen_Roughness=0.6,
          Sheen_Tint=(0.10, 0.13, 0.17), Specular_IOR_Level=0.1)


@register
def carpet_dark(mat):
    n = N(mat)
    n.set(Base_Color=(0.016, 0.022, 0.030), Roughness=1.0, Sheen_Weight=0.25,
          Sheen_Tint=(0.08, 0.11, 0.15), Specular_IOR_Level=0.05)
    vec = n.coords('Object')
    n.link(n.bump(_noise(n, vec, 2500.0, 2.0), strength=0.6, distance=0.001), n.bsdf.inputs['Normal'])


@register
def dial_face(mat):
    """Instrument dial face (off-white enamel)."""
    N(mat).set(Base_Color=(0.78, 0.78, 0.74), Roughness=0.35)


@register
def dial_black(mat):
    N(mat).set(Base_Color=(0.006, 0.006, 0.007), Roughness=0.28)


@register
def needle_red(mat):
    n = N(mat)
    n.set(Base_Color=spec.COLOURS['accent_red'], Roughness=0.3,
          Emission_Color=(1.0, 0.05, 0.03, 1.0), Emission_Strength=0.6)


# ------------------------------------------------------------------ brakes / badge
@register
def brake_disc(mat):
    """Carbon-ceramic disc."""
    n = N(mat)
    vec = n.coords('Object')
    col = n.ramp(_noise(n, vec, 350.0, 4.0), [(0.3, (0.035, 0.035, 0.038)), (0.7, (0.075, 0.075, 0.08))])
    n.link(col, n.bsdf.inputs['Base Color'])
    n.set(Metallic=0.2, Roughness=0.55)


@register
def caliper(mat):
    """Painted brake caliper (pale blue to match the body)."""
    N(mat).set(Base_Color=spec.COLOURS['paint_light'], Roughness=0.3, Coat_Weight=1.0, Coat_Roughness=0.05)


@register
def badge_red(mat):
    """Red enamel (grille badge)."""
    N(mat).set(Base_Color=(0.55, 0.012, 0.012), Roughness=0.12, Coat_Weight=1.0, Coat_Roughness=0.02)


@register
def flag_blue(mat):
    N(mat).set(Base_Color=(0.01, 0.06, 0.40), Roughness=0.2, Coat_Weight=1.0)


@register
def flag_white(mat):
    N(mat).set(Base_Color=(0.85, 0.85, 0.85), Roughness=0.2, Coat_Weight=1.0)


@register
def flag_red(mat):
    N(mat).set(Base_Color=(0.60, 0.015, 0.02), Roughness=0.2, Coat_Weight=1.0)


# ------------------------------------------------------------------ emissive (drivable)
def _emit(mat, colour, strength_on, base=(0.02, 0.02, 0.02), default_on=True):
    """Emission whose power = 'Strength' value node (0 = off). Rig drives that node."""
    n = N(mat)
    n.set(Base_Color=base, Roughness=0.25)
    val = n.new('ShaderNodeValue')
    val.name = "Strength"
    val.label = "Strength (driven)"
    val.outputs[0].default_value = strength_on if default_on else 0.0
    mat["strength_on"] = float(strength_on)
    n.bsdf.inputs['Emission Color'].default_value = (*colour, 1.0)
    n.link(val.outputs[0], n.bsdf.inputs['Emission Strength'])


@register
def emit_headlight(mat):
    """Main LED projector elements (cool white)."""
    _emit(mat, (0.86, 0.93, 1.0), 60.0, base=(0.6, 0.6, 0.62))


@register
def emit_drl(mat):
    """Daytime running light signature."""
    _emit(mat, (0.90, 0.95, 1.0), 22.0, base=(0.5, 0.5, 0.5))


@register
def emit_tail(mat):
    """Rear light bar (red)."""
    _emit(mat, (1.0, 0.035, 0.02), 26.0, base=(0.25, 0.0, 0.0))


@register
def emit_amber(mat):
    _emit(mat, (1.0, 0.42, 0.04), 18.0, base=(0.3, 0.12, 0.0), default_on=False)


@register
def emit_reverse(mat):
    _emit(mat, (1.0, 1.0, 1.0), 14.0, base=(0.5, 0.5, 0.5), default_on=False)


@register
def emit_interior(mat):
    """Cabin ambient light strips (ice white)."""
    _emit(mat, (0.72, 0.88, 1.0), 6.0, base=(0.3, 0.35, 0.4))


@register
def emit_dial(mat):
    """Instrument back-lighting."""
    _emit(mat, (0.85, 0.93, 1.0), 2.5, base=(0.5, 0.5, 0.5))


@register
def emit_screen(mat):
    """Small display glow (console start button / screen)."""
    _emit(mat, (0.25, 0.65, 1.0), 4.0, base=(0.02, 0.05, 0.1))


EMISSIVE_GROUPS = {
    # control property -> materials it switches
    "headlights": ["emit_headlight", "emit_drl"],
    "taillights": ["emit_tail"],
    "interior_lights": ["emit_interior", "emit_dial", "emit_screen"],
    "indicators": ["emit_amber"],
    "reverse_lights": ["emit_reverse"],
}
