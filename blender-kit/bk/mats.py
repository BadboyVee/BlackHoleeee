"""bk.mats -- procedural Cycles material library (no image textures required).

All materials are cached by name.  Texture space conventions:
  * 'UV'     -- real-world UVs written by bk.core (1 unit = 1 m, U along the grain / length)
  * 'Object' -- object space, for isotropic 3D noise
"""
import math

import bpy

_CACHE = {}


def srgb(c):
    """sRGB 0-1 float -> linear."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexc(h, a=1.0):
    """'#rrggbb' -> linear RGBA tuple."""
    h = h.lstrip('#')
    return (srgb(int(h[0:2], 16) / 255), srgb(int(h[2:4], 16) / 255), srgb(int(h[4:6], 16) / 255), a)


def col(c):
    if isinstance(c, str):
        return hexc(c)
    if len(c) == 3:
        return (c[0], c[1], c[2], 1.0)
    return tuple(c)


def scale_col(c, k):
    c = col(c)
    return (c[0] * k, c[1] * k, c[2] * k, c[3])


def mix_col(a, b, t):
    a, b = col(a), col(b)
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


# --------------------------------------------------------------------------
# node builder
# --------------------------------------------------------------------------
class NB:
    def __init__(self, name):
        self.mat = bpy.data.materials.new(name)
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self._x = 0
        self.output = self.node('ShaderNodeOutputMaterial')

    # -- generic -----------------------------------------------------------
    def node(self, idname, **attrs):
        n = self.nt.nodes.new(idname)
        self._x += 1
        n.location = (self._x * 40 % 2400, -(self._x // 60) * 300)
        for k, v in attrs.items():
            setattr(n, k, v)
        return n

    def put(self, n, key, v):
        """Set input *key* (name or index) of node n to a value or link it to a socket."""
        if v is None:
            return
        sock = n.inputs[key]
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sock)
        elif isinstance(v, bpy.types.Node):
            self.nt.links.new(v.outputs[0], sock)
        else:
            if sock.type == 'RGBA':
                v = col(v) if not isinstance(v, (int, float)) else (v, v, v, 1.0)
            elif sock.type == 'VECTOR' and isinstance(v, (int, float)):
                v = (v, v, v)
            sock.default_value = v

    def N(self, idname, attrs=None, **inputs):
        n = self.node(idname, **(attrs or {}))
        for k, v in inputs.items():
            self.put(n, k.replace('_', ' '), v)
        return n

    # -- inputs ------------------------------------------------------------
    def tc(self, kind='Object'):
        return self.node('ShaderNodeTexCoord').outputs[kind]

    def geo(self, out='Position'):
        return self.node('ShaderNodeNewGeometry').outputs[out]

    def obj_random(self):
        return self.node('ShaderNodeObjectInfo').outputs['Random']

    def light_path(self, out='Is Shadow Ray'):
        return self.node('ShaderNodeLightPath').outputs[out]

    def mapping(self, v, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), kind='POINT'):
        n = self.node('ShaderNodeMapping', vector_type=kind)
        self.put(n, 'Vector', v)
        self.put(n, 'Location', loc)
        self.put(n, 'Rotation', rot)
        self.put(n, 'Scale', scale)
        return n.outputs[0]

    def val(self, x):
        n = self.node('ShaderNodeValue')
        n.outputs[0].default_value = x
        return n.outputs[0]

    def rgb(self, c):
        n = self.node('ShaderNodeRGB')
        n.outputs[0].default_value = col(c)
        return n.outputs[0]

    def attr(self, name, out='Color', kind='GEOMETRY'):
        n = self.node('ShaderNodeAttribute', attribute_name=name, attribute_type=kind)
        return n.outputs[out]

    # -- textures ----------------------------------------------------------
    def noise(self, v=None, scale=5.0, detail=2.0, rough=0.5, dist=0.0, lac=2.0, out='Factor', dim='3D', w=None,
              kind='FBM'):
        n = self.node('ShaderNodeTexNoise', noise_dimensions=dim, noise_type=kind)
        self.put(n, 'Vector', v)
        if w is not None:
            self.put(n, 'W', w)
        self.put(n, 'Scale', scale)
        self.put(n, 'Detail', detail)
        self.put(n, 'Roughness', rough)
        self.put(n, 'Lacunarity', lac)
        self.put(n, 'Distortion', dist)
        return n.outputs[out]

    def voronoi(self, v=None, scale=5.0, feature='F1', out='Distance', rand=1.0, dist='EUCLIDEAN', smooth=None,
                dim='3D'):
        n = self.node('ShaderNodeTexVoronoi', feature=feature, distance=dist, voronoi_dimensions=dim)
        self.put(n, 'Vector', v)
        self.put(n, 'Scale', scale)
        self.put(n, 'Randomness', rand)
        if smooth is not None and feature == 'SMOOTH_F1':
            self.put(n, 'Smoothness', smooth)
        return n.outputs[out]

    def wave(self, v=None, scale=5.0, dist=0.0, detail=0.0, dscale=1.0, drough=0.5, kind='BANDS', direction='X',
             profile='SIN', phase=0.0, out='Factor'):
        n = self.node('ShaderNodeTexWave', wave_type=kind, wave_profile=profile)
        if kind == 'BANDS':
            n.bands_direction = direction
        else:
            n.rings_direction = direction
        self.put(n, 'Vector', v)
        self.put(n, 'Scale', scale)
        self.put(n, 'Distortion', dist)
        self.put(n, 'Detail', detail)
        self.put(n, 'Detail Scale', dscale)
        self.put(n, 'Detail Roughness', drough)
        self.put(n, 'Phase Offset', phase)
        return n.outputs[out]

    def brick(self, v=None, c1=(0, 0, 0, 1), c2=(1, 1, 1, 1), mortar=(0, 0, 0, 1), scale=1.0, msize=0.004,
              msmooth=0.1, bias=0.0, bw=0.6, rh=0.6, offset=0.0, freq=2, squash=1.0, sfreq=2):
        """Returns the node (outputs 'Color' = per-brick random mix, 'Factor' = mortar mask)."""
        n = self.node('ShaderNodeTexBrick', offset=offset, offset_frequency=freq, squash=squash,
                      squash_frequency=sfreq)
        self.put(n, 'Vector', v)
        self.put(n, 'Color1', c1)
        self.put(n, 'Color2', c2)
        self.put(n, 'Mortar', mortar)
        self.put(n, 'Scale', scale)
        self.put(n, 'Mortar Size', msize)
        self.put(n, 'Mortar Smooth', msmooth)
        self.put(n, 'Bias', bias)
        self.put(n, 'Brick Width', bw)
        self.put(n, 'Row Height', rh)
        return n

    def image(self, img, v=None, interp='Cubic', ext='REPEAT'):
        n = self.node('ShaderNodeTexImage', image=img, interpolation=interp, extension=ext)
        self.put(n, 'Vector', v)
        return n

    # -- maths -------------------------------------------------------------
    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.put(n, 0, a)
        if b is not None:
            self.put(n, 1, b)
        if c is not None:
            self.put(n, 2, c)
        return n.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        n = self.node('ShaderNodeVectorMath', operation=op)
        self.put(n, 0, a)
        if b is not None:
            self.put(n, 1, b)
        if scale is not None:
            self.put(n, 'Scale', scale)
        return n.outputs['Value' if op in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else 'Vector']

    def sep(self, v):
        n = self.node('ShaderNodeSeparateXYZ')
        self.put(n, 0, v)
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def comb(self, x=0.0, y=0.0, z=0.0):
        n = self.node('ShaderNodeCombineXYZ')
        self.put(n, 0, x)
        self.put(n, 1, y)
        self.put(n, 2, z)
        return n.outputs[0]

    def maprange(self, v, fmin=0.0, fmax=1.0, tmin=0.0, tmax=1.0, clamp=True, interp='LINEAR'):
        n = self.node('ShaderNodeMapRange', clamp=clamp, interpolation_type=interp)
        self.put(n, 0, v)
        self.put(n, 1, fmin)
        self.put(n, 2, fmax)
        self.put(n, 3, tmin)
        self.put(n, 4, tmax)
        return n.outputs[0]

    def ramp(self, fac, stops, interp='LINEAR'):
        n = self.node('ShaderNodeValToRGB')
        cr = n.color_ramp
        cr.interpolation = interp
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for e, (p, c) in zip(cr.elements, stops):
            e.position = p
            e.color = col(c) if not isinstance(c, (int, float)) else (c, c, c, 1.0)
        self.put(n, 0, fac)
        return n.outputs[0]

    def mix(self, fac, a, b, blend='MIX', clamp=True):
        n = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_factor=clamp)
        self.put(n, 0, fac)
        self.put(n, 6, a)
        self.put(n, 7, b)
        return n.outputs[2]

    def mixf(self, fac, a, b):
        n = self.node('ShaderNodeMix', data_type='FLOAT')
        self.put(n, 0, fac)
        self.put(n, 2, a)
        self.put(n, 3, b)
        return n.outputs[0]

    def hsv(self, c, h=0.5, s=1.0, v=1.0, fac=1.0):
        n = self.node('ShaderNodeHueSaturation')
        self.put(n, 'Hue', h)
        self.put(n, 'Saturation', s)
        self.put(n, 'Value', v)
        self.put(n, 'Factor', fac)
        self.put(n, 'Color', c)
        return n.outputs[0]

    def bump(self, height, strength=0.3, dist=0.002, normal=None, invert=False):
        n = self.node('ShaderNodeBump', invert=invert)
        self.put(n, 'Strength', strength)
        self.put(n, 'Distance', dist)
        self.put(n, 'Height', height)
        self.put(n, 'Normal', normal)
        return n.outputs[0]

    def fresnel(self, ior=1.45):
        n = self.node('ShaderNodeFresnel')
        self.put(n, 'IOR', ior)
        return n.outputs[0]

    def layer_weight(self, blend=0.5, out='Facing'):
        n = self.node('ShaderNodeLayerWeight')
        self.put(n, 'Blend', blend)
        return n.outputs[out]

    # -- shaders -----------------------------------------------------------
    def principled(self, **kw):
        n = self.node('ShaderNodeBsdfPrincipled')
        names = {'color': 'Base Color', 'metallic': 'Metallic', 'rough': 'Roughness', 'ior': 'IOR', 'alpha': 'Alpha',
                 'normal': 'Normal', 'sss': 'Subsurface Weight', 'sss_radius': 'Subsurface Radius',
                 'sss_scale': 'Subsurface Scale', 'spec': 'Specular IOR Level', 'spec_tint': 'Specular Tint',
                 'aniso': 'Anisotropic', 'aniso_rot': 'Anisotropic Rotation', 'tangent': 'Tangent',
                 'trans': 'Transmission Weight', 'coat': 'Coat Weight', 'coat_rough': 'Coat Roughness',
                 'coat_ior': 'Coat IOR', 'coat_tint': 'Coat Tint', 'coat_normal': 'Coat Normal',
                 'sheen': 'Sheen Weight', 'sheen_rough': 'Sheen Roughness', 'sheen_tint': 'Sheen Tint',
                 'emit': 'Emission Color', 'emit_strength': 'Emission Strength', 'thin': 'Thin Wall',
                 'diffuse_rough': 'Diffuse Roughness', 'sss_aniso': 'Subsurface Anisotropy',
                 'sss_ior': 'Subsurface IOR', 'film': 'Thin Film Thickness'}
        for k, v in kw.items():
            self.put(n, names[k], v)
        return n.outputs[0]

    def shader(self, idname, **inputs):
        return self.N(idname, **inputs).outputs[0]

    def mix_shader(self, fac, a, b):
        n = self.node('ShaderNodeMixShader')
        self.put(n, 0, fac)
        self.put(n, 1, a)
        self.put(n, 2, b)
        return n.outputs[0]

    def add_shader(self, a, b):
        n = self.node('ShaderNodeAddShader')
        self.put(n, 0, a)
        self.put(n, 1, b)
        return n.outputs[0]

    def out(self, surface=None, volume=None, disp=None):
        if surface is not None:
            self.put(self.output, 'Surface', surface)
        if volume is not None:
            self.put(self.output, 'Volume', volume)
        if disp is not None:
            self.put(self.output, 'Displacement', disp)
        return self.mat


def cached(fn):
    def wrap(*a, **k):
        key = (fn.__name__,) + tuple(str(x) for x in a) + tuple(sorted((kk, str(v)) for kk, v in k.items()))
        m = _CACHE.get(key)
        if m is None or m.name not in bpy.data.materials:
            m = fn(*a, **k)
            _CACHE[key] = m
        return m
    wrap.__name__ = fn.__name__
    return wrap


def clear_cache():
    _CACHE.clear()


# --------------------------------------------------------------------------
# basic surfaces
# --------------------------------------------------------------------------
@cached
def plain(name, color, rough=0.5, metallic=0.0, coat=0.0, spec=0.5, sheen=0.0, emit=None, emit_strength=0.0,
          alpha=1.0, trans=0.0, ior=1.45, coat_rough=0.03):
    b = NB(name)
    kw = dict(color=color, rough=rough, metallic=metallic, coat=coat, coat_rough=coat_rough, spec=spec, sheen=sheen,
              alpha=alpha, trans=trans, ior=ior)
    if emit is not None:
        kw.update(emit=emit, emit_strength=emit_strength)
    return b.out(b.principled(**kw))


@cached
def paint(name, color, rough=0.6, texture=0.25):
    """Interior emulsion paint: flat colour, faint roller stipple."""
    b = NB(name)
    oc = b.tc('Object')
    n1 = b.noise(oc, scale=900, detail=2, rough=0.6)
    n2 = b.noise(oc, scale=1.3, detail=3, rough=0.5)
    c = b.mix(b.maprange(n2, 0.3, 0.7, 0.0, 0.05), color, scale_col(color, 0.9))
    return b.out(b.principled(color=c, rough=rough, normal=b.bump(n1, texture * 0.12, 0.0006)))


@cached
def stucco(name, color, rough=0.88, grain=1.0, dirt=0.06):
    """Exterior sand-finish render with slight weathering."""
    b = NB(name)
    oc = b.tc('Object')
    fine = b.noise(oc, scale=260, detail=5, rough=0.65)
    med = b.noise(oc, scale=28, detail=4, rough=0.55)
    big = b.noise(oc, scale=0.6, detail=5, rough=0.6, dist=0.4)
    c = b.mix(b.maprange(big, 0.3, 0.75, 0.0, dirt), color, scale_col(color, 0.6))
    c = b.mix(b.maprange(med, 0.35, 0.65, 0.0, 0.035), c, scale_col(color, 1.12))
    h = b.math('ADD', b.math('MULTIPLY', fine, 0.7), b.math('MULTIPLY', med, 0.5))
    return b.out(b.principled(color=c, rough=rough, normal=b.bump(h, 0.22 * grain, 0.0015)))


@cached
def concrete(name, color='#8d8c88', rough=0.78, scale=1.0, bump=0.3):
    b = NB(name)
    oc = b.mapping(b.tc('Object'), scale=(scale,) * 3)
    big = b.noise(oc, scale=1.2, detail=6, rough=0.62, dist=0.5)
    med = b.noise(oc, scale=14, detail=5, rough=0.6)
    fine = b.noise(oc, scale=180, detail=4, rough=0.6)
    pits = b.voronoi(oc, scale=95, feature='F1')
    pm = b.maprange(pits, 0.0, 0.16, 1.0, 0.0)
    c = b.mix(b.maprange(big, 0.3, 0.7, 0.0, 1.0), scale_col(color, 0.78), scale_col(color, 1.1))
    c = b.mix(b.maprange(med, 0.4, 0.75, 0.0, 0.2), c, scale_col(color, 0.6))
    h = b.math('SUBTRACT', b.math('ADD', b.math('MULTIPLY', med, 0.6), b.math('MULTIPLY', fine, 0.3)),
               b.math('MULTIPLY', pm, 0.6))
    r = b.maprange(med, 0.3, 0.7, rough - 0.12, rough + 0.08)
    return b.out(b.principled(color=c, rough=r, normal=b.bump(h, bump, 0.002)))


@cached
def asphalt(name="asphalt"):
    b = NB(name)
    oc = b.tc('Object')
    agg = b.voronoi(oc, scale=180, feature='F1')
    big = b.noise(oc, scale=0.35, detail=5, rough=0.6)
    fine = b.noise(oc, scale=400, detail=3)
    c = b.mix(b.maprange(agg, 0.0, 0.5, 0.0, 1.0), '#141414', '#2b2a29')
    c = b.mix(b.maprange(big, 0.35, 0.7, 0.0, 0.5), c, '#3a3835')
    h = b.math('ADD', agg, b.math('MULTIPLY', fine, 0.4))
    return b.out(b.principled(color=c, rough=b.maprange(big, 0.3, 0.7, 0.62, 0.9), normal=b.bump(h, 0.5, 0.003)))


# --------------------------------------------------------------------------
# wood
# --------------------------------------------------------------------------
WOODS = {
    'oak': ('#b48a5a', '#8a6238', 0.42),
    'oak_light': ('#d9bd92', '#b89468', 0.45),
    'walnut': ('#5d3d27', '#33200f', 0.38),
    'walnut_dark': ('#3d2718', '#1f1309', 0.36),
    'teak': ('#a56a35', '#6e411c', 0.4),
    'mahogany': ('#6b2f1b', '#3c170c', 0.33),
    'wenge': ('#2a1d16', '#120c08', 0.35),
    'ash': ('#dccdb2', '#bda782', 0.5),
    'ebony': ('#1a1613', '#090807', 0.3),
    'pine': ('#dcb57a', '#b98a4a', 0.5),
    'iroko': ('#96673a', '#5e3b1b', 0.4),
}


def _wood_color(b, uv, light, dark, grain=1.0, contrast=1.0, seed_w=None):
    """Streaky grain along U.  Returns (colour, height)."""
    g1 = b.noise(b.mapping(uv, scale=(1.6 * grain, 22 * grain, 1)), scale=1.0, detail=7, rough=0.62, dist=1.6,
                 dim='3D' if seed_w is None else '4D', w=seed_w)
    g2 = b.noise(b.mapping(uv, scale=(4 * grain, 260 * grain, 1)), scale=1.0, detail=3, rough=0.7,
                 dim='3D' if seed_w is None else '4D', w=seed_w)
    g3 = b.noise(b.mapping(uv, scale=(0.5, 2.5, 1)), scale=1.0, detail=3, rough=0.5,
                 dim='3D' if seed_w is None else '4D', w=seed_w)
    t = b.maprange(g1, 0.28, 0.72, 0.0, 1.0)
    c = b.mix(t, dark, light)
    c = b.mix(b.maprange(g2, 0.35, 0.8, 0.0, 0.42 * contrast), c, scale_col(dark, 0.55))
    c = b.mix(b.maprange(g3, 0.25, 0.75, 0.0, 0.22), c, scale_col(light, 1.12))
    h = b.math('ADD', b.math('MULTIPLY', g1, 0.5), b.math('MULTIPLY', g2, 0.5))
    return c, h, g2


@cached
def wood(kind='oak', gloss=0.3, grain=1.0, name=None, rough=None, bump=0.06):
    """Solid timber / veneer; grain follows the UV U axis."""
    light, dark, r = WOODS[kind]
    b = NB(name or f"wood_{kind}_{gloss}")
    c, h, g2 = _wood_color(b, b.tc('UV'), light, dark, grain)
    r = rough if rough is not None else r
    rr = b.maprange(g2, 0.3, 0.8, r - 0.06, r + 0.1)
    return b.out(b.principled(color=c, rough=rr, coat=gloss, coat_rough=0.06, normal=b.bump(h, bump, 0.0006)))


@cached
def wood_planks(kind='oak', plank=(1.4, 0.14), gap=0.0018, gloss=0.25, name=None, rot=0.0, variation=0.35,
                rough=None, herringbone=False):
    """Plank floor / decking / slat cladding.  UV must be world-scale; planks run along U."""
    light, dark, r = WOODS[kind]
    b = NB(name or f"planks_{kind}_{plank}_{gloss}_{rot}")
    uv = b.tc('UV')
    if rot:
        uv = b.mapping(uv, rot=(0, 0, math.radians(rot)))
    bk = b.brick(uv, c1=(0, 0, 0, 1), c2=(1, 1, 1, 1), mortar=(0.5, 0.5, 0.5, 1), scale=1.0, msize=gap, msmooth=0.3,
                 bias=0.0, bw=plank[0], rh=plank[1], offset=0.37, freq=2)
    rndv = bk.outputs['Color']
    gapm = bk.outputs['Factor']
    c, h, g2 = _wood_color(b, uv, light, dark, 1.0, seed_w=b.math('MULTIPLY', rndv, 53.0))
    c = b.hsv(c, 0.5, 1.0, b.maprange(rndv, 0.0, 1.0, 1.0 - variation, 1.0 + variation * 0.6))
    c = b.mix(gapm, c, scale_col(dark, 0.18))
    r = rough if rough is not None else r
    rr = b.mixf(gapm, b.maprange(g2, 0.3, 0.8, r - 0.06, r + 0.08), 0.9)
    hh = b.math('SUBTRACT', b.math('MULTIPLY', h, 0.25), b.math('MULTIPLY', gapm, 4.0))
    return b.out(b.principled(color=c, rough=rr, coat=gloss, coat_rough=0.08, normal=b.bump(hh, 0.25, 0.0008)))


# --------------------------------------------------------------------------
# stone / tile
# --------------------------------------------------------------------------
MARBLES = {
    'carrara': ('#ecebe8', '#8f9296', '#c9cacb', 1.0),
    'calacatta': ('#f1eee8', '#8c7a5c', '#b9b3a8', 1.25),
    'statuario': ('#f3f2f0', '#5f6266', '#b5b7ba', 1.4),
    'nero': ('#0d0d0e', '#e8e6e0', '#3a3a3c', 1.2),
    'emperador': ('#4a3020', '#c9b08c', '#7a5438', 1.0),
    'travertine': ('#d8c7a8', '#a8916a', '#c4b08c', 0.6),
    'crema': ('#e6d9c0', '#b39a72', '#d3c3a4', 0.8),
    'grey': ('#8f9092', '#e5e5e5', '#6c6d70', 0.9),
    'green': ('#12332b', '#d5e5dc', '#1d5446', 1.1),
}


def _marble(b, v, kind, scale=1.0, seed_w=None, cloud_amt=0.55, vein_amt=1.0):
    base, vein, cloud, k = MARBLES[kind]
    dim = '3D' if seed_w is None else '4D'
    warp = b.noise(v, scale=0.9 * scale, detail=4, rough=0.6, out='Color', dim=dim, w=seed_w)
    vv = b.vmath('ADD', v, b.vmath('SCALE', warp, scale=0.9))
    n1 = b.noise(vv, scale=1.1 * scale, detail=8, rough=0.68, dim=dim, w=seed_w)
    n2 = b.noise(vv, scale=3.4 * scale, detail=6, rough=0.62, dim=dim, w=seed_w)
    n3 = b.noise(v, scale=0.5 * scale, detail=3, rough=0.5, dim=dim, w=seed_w)
    w1 = 0.035 * k
    v1 = b.ramp(n1, [(0.5 - w1, 0.0), (0.5, 1.0), (0.5 + w1, 0.0)], 'EASE')
    v2 = b.ramp(n2, [(0.5 - w1 * 0.45, 0.0), (0.5, 0.55), (0.5 + w1 * 0.45, 0.0)], 'EASE')
    veins = b.math('MAXIMUM', v1, v2)
    veins = b.math('MULTIPLY', veins, b.maprange(n3, 0.3, 0.7, 0.25 * vein_amt, vein_amt))
    c = b.mix(b.maprange(n2, 0.25, 0.8, 0.0, cloud_amt), base, cloud)
    c = b.mix(veins, c, vein)
    return c, veins


@cached
def marble(kind='carrara', rough=0.07, scale=1.0, name=None, coords='Object', cloud=0.55, veins=1.0):
    b = NB(name or f"marble_{kind}_{rough}_{scale}_{coords}_{cloud}_{veins}")
    c, veins = _marble(b, b.tc(coords), kind, scale, cloud_amt=cloud, vein_amt=veins)
    return b.out(b.principled(color=c, rough=b.mixf(veins, rough, rough + 0.05), spec=0.6))


@cached
def tiles(kind='crema', size=(0.6, 0.6), grout='#b5aea2', gw=0.0025, rough=0.1, name=None, pattern='marble',
          color=None, offset=0.0, variation=0.04, bump=0.6, scale=0.6, coords='UV', lip=1.0, cloud=0.55, veins=1.0):
    """Floor / wall tiles.  pattern: 'marble' (veined), 'plain' (solid colour), 'speckle' (terrazzo)."""
    b = NB(name or f"tiles_{kind}_{size}_{rough}_{pattern}_{color}_{offset}_{grout}")
    uv = b.tc(coords)
    bk = b.brick(uv, c1=(0, 0, 0, 1), c2=(1, 1, 1, 1), mortar=(0.5, 0.5, 0.5, 1), scale=1.0, msize=gw, msmooth=0.25,
                 bias=0.0, bw=size[0], rh=size[1], offset=offset, freq=2)
    rndv = bk.outputs['Color']
    g = bk.outputs['Factor']
    if pattern == 'marble':
        c, veins = _marble(b, uv, kind, scale, seed_w=b.math('MULTIPLY', rndv, 31.0), cloud_amt=cloud, vein_amt=veins)
    elif pattern == 'speckle':
        base = col(color or '#d9d5cc')
        chips = b.voronoi(uv, scale=140, feature='F1', out='Color')
        cd = b.voronoi(uv, scale=140, feature='F1')
        cm = b.maprange(cd, 0.18, 0.26, 1.0, 0.0)
        cc = b.ramp(b.sep(chips)[0], [(0.0, '#3a3a3a'), (0.35, '#8a8580'), (0.6, '#c9b9a0'), (0.85, '#7d5a48'), (1.0, '#e9e6e0')])
        c = b.mix(cm, base, cc)
    else:
        base = col(color or '#d8d4cc')
        n = b.noise(uv, scale=7, detail=4, rough=0.6, dim='4D', w=b.math('MULTIPLY', rndv, 17.0))
        c = b.mix(b.maprange(n, 0.3, 0.75, 0.0, 0.35), base, scale_col(base, 0.82))
    c = b.hsv(c, 0.5, 1.0, b.maprange(rndv, 0, 1, 1 - variation, 1 + variation))
    c = b.mix(g, c, grout)
    r = b.mixf(g, rough, 0.85)
    h = b.math('MULTIPLY', g, -1.0 * lip)
    return b.out(b.principled(color=c, rough=r, spec=0.55, normal=b.bump(h, bump, 0.0012)))


@cached
def mosaic(name="mosaic", c1='#1f8fb0', c2='#5fd0de', size=0.025, grout='#dfe9ea', rough=0.12):
    """Small glass mosaic (pool lining)."""
    b = NB(name)
    uv = b.tc('UV')
    bk = b.brick(uv, c1=c1, c2=c2, mortar=grout, scale=1.0, msize=0.002, msmooth=0.2, bias=0.0, bw=size, rh=size,
                 offset=0.0)
    return b.out(b.principled(color=bk.outputs['Color'], rough=b.mixf(bk.outputs['Factor'], rough, 0.7),
                              normal=b.bump(b.math('MULTIPLY', bk.outputs['Factor'], -1.0), 0.5, 0.0008)))


@cached
def stone_cladding(name="ledgestone", colors=('#6f6a63', '#9a9288', '#b8ad9c', '#57534e'), rows=0.075, width=0.42,
                   mortar='#2a2826', depth=1.0):
    """Stacked ledgestone strips with strong relief (facade feature walls)."""
    b = NB(name)
    uv = b.tc('UV')
    bk = b.brick(uv, c1=(0, 0, 0, 1), c2=(1, 1, 1, 1), mortar=(0.5, 0.5, 0.5, 1), scale=1.0, msize=0.006, msmooth=0.35,
                 bias=0.0, bw=width, rh=rows, offset=0.43, freq=2, squash=0.62, sfreq=3)
    rndv = bk.outputs['Color']
    rv = b.sep(rndv)[0]
    g = bk.outputs['Factor']
    n = b.noise(uv, scale=22, detail=6, rough=0.7, dim='4D', w=b.math('MULTIPLY', rv, 41.0))
    fine = b.noise(uv, scale=160, detail=4, rough=0.65)
    c = b.ramp(rv, [(0.0, colors[3]), (0.3, colors[0]), (0.62, colors[1]), (1.0, colors[2])])
    c = b.mix(b.maprange(n, 0.3, 0.8, 0.0, 0.45), c, scale_col(colors[3], 0.7))
    c = b.mix(g, c, mortar)
    h = b.math('ADD', b.math('MULTIPLY', rv, 1.6), b.math('ADD', b.math('MULTIPLY', n, 0.9), b.math('MULTIPLY', fine, 0.25)))
    h = b.mixf(g, h, -1.2)
    return b.out(b.principled(color=c, rough=b.mixf(g, 0.82, 0.95), normal=b.bump(h, 1.0, 0.012 * depth)))


@cached
def pavers(name="pavers", colors=('#8e8d8a', '#777673', '#a09e99'), size=(0.2, 0.1), joint='#4a4640', rot=0.0,
           wear=0.5):
    """Concrete interlocking pavers (running bond)."""
    b = NB(name)
    uv = b.tc('UV')
    if rot:
        uv = b.mapping(uv, rot=(0, 0, math.radians(rot)))
    bk = b.brick(uv, c1=(0, 0, 0, 1), c2=(1, 1, 1, 1), mortar=(0.5, 0.5, 0.5, 1), scale=1.0, msize=0.004, msmooth=0.45,
                 bias=0.0, bw=size[0], rh=size[1], offset=0.5)
    rv = b.sep(bk.outputs['Color'])[0]
    g = bk.outputs['Factor']
    big = b.noise(uv, scale=0.35, detail=5, rough=0.6, dist=0.4)
    fine = b.noise(uv, scale=320, detail=4, rough=0.7)
    c = b.ramp(rv, [(0.0, colors[1]), (0.5, colors[0]), (1.0, colors[2])])
    c = b.mix(b.maprange(big, 0.35, 0.75, 0.0, 0.35 * wear), c, scale_col(colors[1], 0.55))
    c = b.mix(g, c, joint)
    h = b.math('ADD', b.math('MULTIPLY', fine, 0.25), b.math('MULTIPLY', rv, 0.3))
    h = b.mixf(g, h, -1.0)
    return b.out(b.principled(color=c, rough=b.mixf(g, 0.8, 0.95), normal=b.bump(h, 0.8, 0.004)))


@cached
def granite(name="granite", base='#2b2b2d', flecks=('#8a8a8c', '#151516', '#5a5754'), rough=0.12):
    b = NB(name)
    oc = b.tc('Object')
    v1 = b.voronoi(oc, scale=420, feature='F1', out='Color')
    r1 = b.sep(v1)[0]
    c = b.ramp(r1, [(0.0, base), (0.55, base), (0.7, flecks[2]), (0.86, flecks[1]), (1.0, flecks[0])], 'CONSTANT')
    n = b.noise(oc, scale=3, detail=4)
    c = b.mix(b.maprange(n, 0.3, 0.7, 0.0, 0.25), c, scale_col(base, 1.6))
    return b.out(b.principled(color=c, rough=rough, spec=0.6))


@cached
def quartz(name="quartz_white", base='#eceae6', rough=0.12):
    b = NB(name)
    oc = b.tc('Object')
    v1 = b.voronoi(oc, scale=900, feature='F1', out='Color')
    c = b.mix(b.maprange(b.sep(v1)[0], 0.7, 1.0, 0.0, 0.12), base, scale_col(base, 0.7))
    return b.out(b.principled(color=c, rough=rough, spec=0.55))


# --------------------------------------------------------------------------
# metals / glass
# --------------------------------------------------------------------------
@cached
def metal(name, color='#c9c9cc', rough=0.25, brushed=0.0, aniso=0.0, coords='Object', axis='Z'):
    b = NB(name)
    kw = dict(color=color, metallic=1.0, rough=rough)
    if brushed:
        oc = b.tc(coords)
        sc = {'X': (2, 300, 300), 'Y': (300, 2, 300), 'Z': (300, 300, 2)}[axis]
        n = b.noise(b.mapping(oc, scale=sc), scale=1.0, detail=3, rough=0.6)
        kw['rough'] = b.maprange(n, 0.2, 0.8, rough * 0.75, rough * 1.3)
        kw['normal'] = b.bump(n, brushed * 0.05, 0.0002)
        kw['aniso'] = aniso
    return b.out(b.principled(**kw))


def chrome():
    return metal("chrome", '#e6e6e8', 0.04)


def steel():
    return metal("steel_brushed", '#b8b9bc', 0.28, brushed=1.0, aniso=0.4)


def brass():
    return metal("brass_brushed", '#d4a857', 0.22, brushed=0.6, aniso=0.3)


def gold():
    return metal("gold_polished", '#e3b455', 0.12)


def black_metal():
    return plain("black_powdercoat", '#0c0c0d', rough=0.42, spec=0.4)


def alu_dark():
    return plain("alu_frame_black", '#101112', rough=0.33, spec=0.5)


def alu_bronze():
    return metal("alu_bronze", '#2a2420', 0.36)


@cached
def glass(name="glass_clear", tint=(0.94, 0.97, 0.96), rough=0.0, ior=1.5, shadow=True):
    """Architectural glass: real refraction for camera rays, plain transparency for shadow rays so
    sunlight and sky light reach interiors without caustic noise."""
    b = NB(name)
    g = b.shader('ShaderNodeBsdfGlass', Color=col(tint), Roughness=rough, IOR=ior)
    if not shadow:
        return b.out(g)
    t = b.shader('ShaderNodeBsdfTransparent', Color=col(tint))
    return b.out(b.mix_shader(b.light_path('Is Shadow Ray'), g, t))


@cached
def glass_frosted(name="glass_frosted", tint=(0.92, 0.95, 0.95), rough=0.35):
    b = NB(name)
    g = b.shader('ShaderNodeBsdfGlass', Color=col(tint), Roughness=rough, IOR=1.5)
    t = b.shader('ShaderNodeBsdfTranslucent', Color=col(tint))
    tr = b.shader('ShaderNodeBsdfTransparent', Color=col(tint))
    sh = b.mix_shader(0.6, t, tr)
    return b.out(b.mix_shader(b.light_path('Is Shadow Ray'), g, sh))


@cached
def mirror(name="mirror"):
    return plain(name, '#f2f2f2', rough=0.0, metallic=1.0)


# --------------------------------------------------------------------------
# fabrics / soft goods
# --------------------------------------------------------------------------
@cached
def fabric(name, color, weave=700.0, rough=0.92, sheen=0.35, bump=0.35, hue_var=0.06, wrinkle=0.0, coords='UV',
           color2=None, pattern=None, pscale=6.0):
    """Woven upholstery / bedding / curtain cloth with thread-level bump."""
    b = NB(name)
    uv = b.tc(coords)
    wx = b.wave(uv, scale=weave / 6.283, direction='X')
    wy = b.wave(uv, scale=weave / 6.283, direction='Y')
    chk = b.math('GREATER_THAN', b.math('SINE', b.math('MULTIPLY', b.sep(uv)[0], weave)), 0.0)
    th = b.mixf(chk, wx, wy)
    slub = b.noise(b.mapping(uv, scale=(40, 900, 1)), scale=1.0, detail=2)
    hv = b.noise(uv, scale=3.0, detail=3)
    c = col(color)
    cc = b.mix(b.maprange(slub, 0.3, 0.8, 0.0, hue_var * 2.2), c, scale_col(c, 1.3))
    cc = b.mix(b.maprange(hv, 0.3, 0.7, 0.0, hue_var), cc, scale_col(c, 0.82))
    if color2 is not None and pattern:
        if pattern == 'stripe':
            pm = b.math('GREATER_THAN', b.math('SINE', b.math('MULTIPLY', b.sep(uv)[1], pscale * 6.283)), 0.2)
        elif pattern == 'check':
            s1 = b.math('GREATER_THAN', b.math('SINE', b.math('MULTIPLY', b.sep(uv)[0], pscale * 6.283)), 0.0)
            s2 = b.math('GREATER_THAN', b.math('SINE', b.math('MULTIPLY', b.sep(uv)[1], pscale * 6.283)), 0.0)
            pm = b.math('ABSOLUTE', b.math('SUBTRACT', s1, s2))
        else:
            pm = b.maprange(b.noise(uv, scale=pscale, detail=4, rough=0.6, dist=1.0), 0.45, 0.55, 0, 1)
        cc = b.mix(pm, cc, color2)
    h = th
    if wrinkle:
        wr = b.noise(uv, scale=5.5, detail=4, rough=0.55, dist=0.8)
        nrm = b.bump(wr, wrinkle, 0.02)
        nrm = b.bump(h, bump, 0.0004, normal=nrm)
    else:
        nrm = b.bump(h, bump, 0.0004)
    return b.out(b.principled(color=cc, rough=rough, sheen=sheen, sheen_rough=0.5, spec=0.25, normal=nrm))


@cached
def velvet(name, color, sheen=1.0):
    b = NB(name)
    oc = b.tc('Object')
    n = b.noise(oc, scale=6, detail=4, rough=0.6, dist=0.6)
    fine = b.noise(oc, scale=1400, detail=2)
    c = b.mix(b.maprange(n, 0.3, 0.7, 0.0, 0.35), scale_col(color, 0.75), scale_col(color, 1.2))
    return b.out(b.principled(color=c, rough=1.0, sheen=sheen, sheen_rough=0.32, sheen_tint=scale_col(color, 2.5),
                              spec=0.1, normal=b.bump(fine, 0.25, 0.0003)))


@cached
def boucle(name, color='#e8e2d6'):
    b = NB(name)
    oc = b.tc('Object')
    v1 = b.voronoi(oc, scale=420, feature='SMOOTH_F1', smooth=0.6)
    v2 = b.noise(oc, scale=900, detail=3, rough=0.7)
    h = b.math('ADD', b.math('MULTIPLY', v1, -1.0), b.math('MULTIPLY', v2, 0.35))
    c = b.mix(b.maprange(v1, 0.0, 0.5, 0.0, 0.3), scale_col(color, 1.05), scale_col(color, 0.72))
    return b.out(b.principled(color=c, rough=0.95, sheen=0.6, sheen_rough=0.6, spec=0.2,
                              normal=b.bump(h, 0.9, 0.0018)))


@cached
def leather(name, color='#3b2416', rough=0.42, grain=1.0, coat=0.15):
    b = NB(name)
    oc = b.tc('Object')
    cr = b.voronoi(oc, scale=380 * grain, feature='DISTANCE_TO_EDGE')
    crm = b.maprange(cr, 0.0, 0.09, 0.0, 1.0)
    wr = b.noise(oc, scale=9, detail=5, rough=0.6, dist=0.9)
    fine = b.noise(oc, scale=700, detail=2)
    c = b.mix(b.maprange(wr, 0.3, 0.75, 0.0, 0.4), color, scale_col(color, 0.6))
    c = b.mix(crm, scale_col(color, 0.55), c)
    h = b.math('ADD', b.math('MULTIPLY', crm, 0.6), b.math('ADD', b.math('MULTIPLY', wr, 0.5), b.math('MULTIPLY', fine, 0.1)))
    return b.out(b.principled(color=c, rough=b.maprange(wr, 0.3, 0.7, rough - 0.08, rough + 0.1), coat=coat,
                              coat_rough=0.25, spec=0.5, normal=b.bump(h, 0.35, 0.0012)))


@cached
def sheer(name="sheer_white", color='#f4f1ea', alpha=0.42):
    """Voile curtain: light passes, shapes behind stay visible but soft."""
    b = NB(name)
    uv = b.tc('UV')
    wx = b.wave(uv, scale=900 / 6.283, direction='X')
    wy = b.wave(uv, scale=900 / 6.283, direction='Y')
    th = b.math('MAXIMUM', wx, wy)
    d = b.shader('ShaderNodeBsdfDiffuse', Color=col(color))
    tl = b.shader('ShaderNodeBsdfTranslucent', Color=col(color))
    s = b.mix_shader(0.55, d, tl)
    tr = b.shader('ShaderNodeBsdfTransparent')
    a = b.maprange(th, 0.0, 1.0, alpha * 0.7, min(1.0, alpha * 1.5))
    return b.out(b.mix_shader(a, tr, s))


@cached
def rug(name, c1='#b9ae9c', c2='#6d6a66', c3='#2f3438', style='abstract', scale=1.0, pile=1.0):
    b = NB(name)
    uv = b.tc('UV')
    if style == 'abstract':
        w = b.noise(uv, scale=0.9 * scale, detail=5, rough=0.6, dist=1.4)
        w2 = b.noise(b.mapping(uv, loc=(3, 7, 0)), scale=2.3 * scale, detail=6, rough=0.7, dist=0.6)
        c = b.ramp(w, [(0.0, c3), (0.38, c2), (0.5, c1), (0.66, c1), (1.0, c2)])
        c = b.mix(b.maprange(w2, 0.45, 0.62, 0.0, 0.75), c, c1)
    elif style == 'lines':
        ww = b.wave(uv, scale=3.5 * scale, dist=2.5, detail=2, dscale=0.8, direction='DIAGONAL')
        c = b.mix(b.maprange(ww, 0.42, 0.5, 0.0, 1.0), c1, c2)
    elif style == 'border':
        u, v, _ = b.sep(uv)
        c = b.rgb(c1)
    else:
        c = b.rgb(c1)
    fz = b.noise(uv, scale=2600, detail=2, rough=0.8)
    tuft = b.voronoi(uv, scale=520, feature='F1')
    h = b.math('ADD', b.math('MULTIPLY', fz, 0.5), b.math('MULTIPLY', tuft, -0.8))
    cc = b.mix(b.maprange(fz, 0.3, 0.7, 0.0, 0.25), c, scale_col(c1, 0.6))
    return b.out(b.principled(color=cc, rough=1.0, sheen=0.8 * pile, sheen_rough=0.7, spec=0.1,
                              normal=b.bump(h, 0.9 * pile, 0.003)))


# --------------------------------------------------------------------------
# misc
# --------------------------------------------------------------------------
@cached
def ceramic(name="ceramic_white", color='#f1efec', rough=0.06):
    return plain(name, color, rough=rough, coat=0.6, coat_rough=0.03, spec=0.6)


@cached
def plastic(name, color, rough=0.35):
    return plain(name, color, rough=rough, spec=0.45)


@cached
def rubber(name="rubber_black", color='#0b0b0b', rough=0.75):
    b = NB(name)
    n = b.noise(b.tc('Object'), scale=600, detail=2)
    return b.out(b.principled(color=color, rough=rough, spec=0.3, normal=b.bump(n, 0.15, 0.0004)))


@cached
def emit(name, color='#fff1d6', strength=10.0):
    b = NB(name)
    return b.out(b.shader('ShaderNodeEmission', Color=col(color), Strength=strength))


@cached
def lampshade(name="lampshade", color='#efe6d2', glow=4.0, tint='#ffd9a0'):
    """Fabric shade lit from inside (emission stands in for transmitted bulb light)."""
    b = NB(name)
    uv = b.tc('UV')
    w = b.wave(uv, scale=500 / 6.283, direction='X')
    d = b.principled(color=color, rough=0.9, sheen=0.3, normal=b.bump(w, 0.2, 0.0004))
    e = b.shader('ShaderNodeEmission', Color=col(tint), Strength=glow)
    back = b.geo('Backfacing')
    return b.out(b.add_shader(d, e))


@cached
def water(name="water_pool", tint=(0.72, 0.93, 0.95), ripple=1.0, scale=1.0):
    b = NB(name)
    oc = b.tc('Object')
    n1 = b.noise(oc, scale=3.2 * scale, detail=3, rough=0.55, dist=0.6)
    n2 = b.noise(b.mapping(oc, loc=(4, 9, 0)), scale=9 * scale, detail=2, rough=0.5)
    h = b.math('ADD', n1, b.math('MULTIPLY', n2, 0.3))
    nrm = b.bump(h, 0.22 * ripple, 0.03)
    g = b.shader('ShaderNodeBsdfGlass', Color=col(tint), Roughness=0.0, IOR=1.33, Normal=nrm)
    t = b.shader('ShaderNodeBsdfTransparent', Color=col(tint))
    return b.out(b.mix_shader(b.light_path('Is Shadow Ray'), g, t))


@cached
def leaf(name, c1='#2f5a1f', c2='#4f7f2a', trans=0.35, rough=0.45, vein=True, coords='UV'):
    b = NB(name)
    uv = b.tc(coords)
    rnd_ = b.obj_random()
    n = b.noise(uv, scale=9, detail=3, rough=0.6)
    c = b.mix(b.maprange(n, 0.3, 0.7, 0.0, 1.0), c1, c2)
    c = b.hsv(c, b.maprange(rnd_, 0, 1, 0.485, 0.515), 1.0, b.maprange(rnd_, 0, 1, 0.8, 1.15))
    d = b.principled(color=c, rough=rough, spec=0.4, coat=0.15, coat_rough=0.3,
                     normal=b.bump(n, 0.2, 0.001))
    tl = b.shader('ShaderNodeBsdfTranslucent', Color=b.hsv(c, 0.5, 1.2, 1.6))
    return b.out(b.mix_shader(trans, d, tl))


@cached
def bark(name="bark", c1='#5a4a3a', c2='#2e241b', scale=1.0, rings=0.0):
    b = NB(name)
    oc = b.tc('Object')
    v = b.voronoi(b.mapping(oc, scale=(14 * scale, 14 * scale, 3 * scale)), scale=1.0, feature='DISTANCE_TO_EDGE')
    n = b.noise(oc, scale=18 * scale, detail=6, rough=0.65)
    h = b.math('ADD', b.maprange(v, 0.0, 0.25, 0.0, 1.0), b.math('MULTIPLY', n, 0.5))
    if rings:
        z = b.sep(oc)[2]
        rg = b.math('SINE', b.math('MULTIPLY', z, rings))
        h = b.math('ADD', h, b.math('MULTIPLY', rg, 0.8))
    c = b.mix(b.maprange(h, 0.2, 1.2, 0.0, 1.0), c2, c1)
    return b.out(b.principled(color=c, rough=0.9, normal=b.bump(h, 0.8, 0.01)))


@cached
def soil(name="soil", c1='#3a2a1c', c2='#1f1610'):
    b = NB(name)
    oc = b.tc('Object')
    n = b.noise(oc, scale=40, detail=6, rough=0.7)
    v = b.voronoi(oc, scale=120, feature='F1')
    c = b.mix(n, c2, c1)
    return b.out(b.principled(color=c, rough=0.95, normal=b.bump(b.math('ADD', n, v), 0.9, 0.008)))


@cached
def pebbles(name="pebbles", c1='#e8e4dc', c2='#9a958c', scale=55.0):
    b = NB(name)
    oc = b.tc('Object')
    d = b.voronoi(oc, scale=scale, feature='F1')
    cc = b.voronoi(oc, scale=scale, feature='F1', out='Color')
    c = b.mix(b.sep(cc)[0], c2, c1)
    c = b.mix(b.maprange(d, 0.35, 0.6, 0.0, 1.0), c, '#1b1a18')
    h = b.math('SUBTRACT', 1.0, b.math('POWER', d, 2.0))
    return b.out(b.principled(color=c, rough=0.55, normal=b.bump(h, 1.0, 0.012)))


@cached
def grass_strand(name="grass_strand", root='#1c3a0f', tip='#6e9a35', dry='#9a9450', dry_amt=0.12):
    b = NB(name)
    hi = b.node('ShaderNodeHairInfo')
    t = hi.outputs['Intercept']
    r = hi.outputs['Random']
    c = b.mix(t, root, tip)
    c = b.mix(b.maprange(r, 1.0 - dry_amt, 1.0, 0.0, 0.8), c, dry)
    c = b.hsv(c, b.maprange(r, 0, 1, 0.48, 0.52), 1.0, b.maprange(r, 0, 1, 0.75, 1.15))
    d = b.principled(color=c, rough=0.5, spec=0.3)
    tl = b.shader('ShaderNodeBsdfTranslucent', Color=c)
    return b.out(b.mix_shader(0.35, d, tl))


@cached
def lawn(name="lawn_base", c1='#2c4a17', c2='#47692a'):
    """Ground under the grass strands (also reads as mown turf from a distance)."""
    b = NB(name)
    oc = b.tc('Object')
    n = b.noise(oc, scale=1.2, detail=5, rough=0.6)
    f = b.noise(oc, scale=260, detail=3, rough=0.7)
    c = b.mix(b.maprange(n, 0.3, 0.7, 0, 1), c1, c2)
    c = b.mix(b.maprange(f, 0.4, 0.7, 0.0, 0.5), c, scale_col(c1, 0.5))
    return b.out(b.principled(color=c, rough=0.95, normal=b.bump(f, 0.8, 0.01)))


@cached
def car_paint(name, color, metallic=0.75, rough=0.32, flake=0.6, coat=1.0, dust=0.0, dust_col='#b89468'):
    b = NB(name)
    oc = b.tc('Object')
    fl = b.voronoi(oc, scale=4200, feature='F1', out='Color')
    fn = b.vmath('SUBTRACT', fl, (0.5, 0.5, 0.5))
    geo_n = b.geo('Normal')
    pn = b.vmath('NORMALIZE', b.vmath('ADD', geo_n, b.vmath('SCALE', fn, scale=0.07 * flake)))
    kw = dict(color=color, metallic=metallic, rough=rough, normal=pn, coat=coat, coat_rough=0.025, coat_ior=1.5)
    if dust > 0:
        z = b.sep(oc)[2]
        dn = b.noise(oc, scale=3.5, detail=6, rough=0.65)
        dm = b.math('MULTIPLY', b.maprange(z, 0.25, 1.3, 1.0, 0.25), b.maprange(dn, 0.3, 0.75, 0.2, 1.0))
        dm = b.math('MULTIPLY', dm, dust, clamp=True)
        kw['color'] = b.mix(dm, color, dust_col)
        kw['rough'] = b.mixf(dm, rough, 0.9)
        kw['metallic'] = b.mixf(dm, metallic, 0.0)
        kw['coat'] = b.mixf(dm, coat, 0.0)
    return b.out(b.principled(**kw))


@cached
def picture(name, img, emit_strength=0.0, rough=0.5):
    """Image on the first UV unit square (prints, canvases, screens)."""
    b = NB(name)
    t = b.image(img, b.tc('UV'), ext='EXTEND')
    if emit_strength:
        return b.out(b.principled(color=t.outputs['Color'], rough=0.15, emit=t.outputs['Color'],
                                  emit_strength=emit_strength, spec=0.5))
    return b.out(b.principled(color=t.outputs['Color'], rough=rough))
