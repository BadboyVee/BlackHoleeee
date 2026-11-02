"""THE UNKNOWN GENERAL — Blender version.

Builds the trailer as a real 3D scene (castle, courtyard, gate, banners, lanterns,
sakura, mountains, fog) with the NFT characters standing in it as lit cut-out
cards, then renders every shot to PNG frames.

    python tools/blender/build.py --sprites <dir> --out <dir> [--shots s1a,s1b] [--samples 64] [--pct 100]

<dir> for --sprites comes from `node tools/render.cjs sprites <dir>`.
Frames are numbered on the trailer's global 30 fps clock, so
`node tools/render.cjs compose <out> blender.mp4` can cross-fade the shots,
add the subtitles and lay the same score underneath.
"""
import argparse, json, math, os, sys, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

ap = argparse.ArgumentParser()
ap.add_argument('--sprites', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--shots', default='all')
ap.add_argument('--samples', type=int, default=64)
ap.add_argument('--pct', type=int, default=100)
ap.add_argument('--engine', default='EEVEE')
ap.add_argument('--still', type=int, default=None, help='render one global frame of each shot instead')
ap.add_argument('--save', default=None, help='also save the .blend here')
ap.add_argument('--rt', type=int, default=0, help='EEVEE raytracing on/off')
ap.add_argument('--vtile', default='8')
ap.add_argument('--nofog', action='store_true')
ap.add_argument('--lite', type=int, default=1)
A = ap.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:])
SP = os.path.abspath(A.sprites)
META = json.load(open(os.path.join(SP, 'meta.json')))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FPS = 30
K = 0.0038                      # metres per canvas unit (a general is ~1.7 m)
R = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.render.fps = FPS
S.frame_start, S.frame_end = 0, 449

# ---------------------------------------------------------------- materials
def hexrgb(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4) for x in c) + (a,)

def mat(name, col, rough=.6, metal=0., emit=None, es=0., coat=0., spec=.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexrgb(col)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Coat Weight' in b.inputs: b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = hexrgb(emit); b.inputs['Emission Strength'].default_value = es
    return m

def node(m, kind, **kw):
    n = m.node_tree.nodes.new(kind)
    for k, v in kw.items(): setattr(n, k, v)
    return n

def link(m, a, b): m.node_tree.links.new(a, b)

M = {
    'lacquer': mat('lacquer', '#0b080a', .22, coat=1.),
    'gold': mat('gold', '#d9a94e', .28, 1.),
    'wall': mat('wall', '#2e2428', .85),
    'wood': mat('wood', '#2a1b16', .7),
    'roof': mat('roof', '#151014', .45, coat=.4),
    'win': mat('win', '#ffb45a', .5, emit='#ff9a3c', es=9.),
    'crimson': mat('crimson', '#7a1220', .55),
    'black': mat('black', '#050304', .8),
    'stoneLamp': mat('stoneLamp', '#3a3134', .9),
    'flame': mat('flame', '#ffcf80', .5, emit='#ffb050', es=25.),
    'trunk': mat('trunk', '#140a0b', .9),
    'blossom': mat('blossom', '#f2a9bd', .55),
    'mtn': mat('mtn', '#1b0c13', .95),
    'gateLight': mat('gateLight', '#fff0d8', .5, emit='#ffe2b0', es=0.),
}
# blossoms glow a touch in the dusk
bb = M['blossom'].node_tree.nodes['Principled BSDF']
bb.inputs['Emission Color'].default_value = hexrgb('#ff9fb8'); bb.inputs['Emission Strength'].default_value = .25
if 'Subsurface Weight' in bb.inputs: bb.inputs['Subsurface Weight'].default_value = .4
_m = M['blossom']; _n = node(_m, 'ShaderNodeTexNoise'); _n.inputs['Scale'].default_value = 9.; _n.inputs['Detail'].default_value = 8.
_r = node(_m, 'ShaderNodeValToRGB'); _r.color_ramp.elements[0].color = hexrgb('#b8566f'); _r.color_ramp.elements[1].color = hexrgb('#ffd6e0')
link(_m, _n.outputs['Fac'], _r.inputs['Fac']); link(_m, _r.outputs['Color'], bb.inputs['Base Color'])
_b = node(_m, 'ShaderNodeBump'); _b.inputs['Strength'].default_value = .8; link(_m, _n.outputs['Fac'], _b.inputs['Height']); link(_m, _b.outputs['Normal'], bb.inputs['Normal'])

def stone_mat(name, col1, col2, scale):
    m = mat(name, col1, .85)
    b = m.node_tree.nodes['Principled BSDF']
    br = node(m, 'ShaderNodeTexBrick'); br.inputs['Scale'].default_value = scale
    br.inputs['Color1'].default_value = hexrgb(col1); br.inputs['Color2'].default_value = hexrgb(col2)
    br.inputs['Mortar'].default_value = hexrgb('#0a0607'); br.inputs['Mortar Size'].default_value = .012
    br.offset = .5; br.squash = 1.
    tc = node(m, 'ShaderNodeTexCoord'); link(m, tc.outputs['Object'], br.inputs['Vector'])
    nz = node(m, 'ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 40.
    mix = node(m, 'ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = .5
    link(m, br.outputs['Color'], mix.inputs['A']); link(m, nz.outputs['Color'], mix.inputs['B'])
    link(m, mix.outputs['Result'], b.inputs['Base Color'])
    bump = node(m, 'ShaderNodeBump'); bump.inputs['Strength'].default_value = .5
    link(m, br.outputs['Fac'], bump.inputs['Height']); link(m, bump.outputs['Normal'], b.inputs['Normal'])
    return m

M['stone'] = stone_mat('stone', '#4a3a38', '#2d2224', 6.)
M['pave'] = stone_mat('pave', '#2c2023', '#1e1618', 1.2)
M['pave'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .38

def image_mat(name, path, emit=.35, rough=.8, alpha=True):
    m = bpy.data.materials.new(name); m.use_nodes = True
    if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(path, check_existing=True)
    tx.interpolation = 'Closest' if 'pixel' in name else 'Linear'
    tx.extension = 'CLIP'
    link(m, tx.outputs['Color'], b.inputs['Base Color'])
    if alpha: link(m, tx.outputs['Alpha'], b.inputs['Alpha'])
    link(m, tx.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit
    b.inputs['Roughness'].default_value = rough
    m['tex'] = tx.name
    return m, tx

# ---------------------------------------------------------------- mesh helpers
def obj_from_bm(name, bm, m=None, coll=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); (coll or S.collection).objects.link(o)
    if m: o.data.materials.append(m)
    return o

def box(name, sx, sy, sz, loc, m, bevel=0., coll=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    o = obj_from_bm(name, bm, m, coll); o.location = loc
    if bevel:
        md = o.modifiers.new('bev', 'BEVEL'); md.width = bevel; md.segments = 2
    return o

def cyl(name, r, h, loc, m, n=16, r2=None, coll=None):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=h)
    o = obj_from_bm(name, bm, m, coll); o.location = loc; return o

def frustum(name, w0, d0, w1, d1, h, loc, m, coll=None, lift=0., n=12, sag=0.):
    """Rectangular frustum; with lift the eave corners curl up (sori)."""
    bm = bmesh.new()
    def ring(w, d, z, curl):
        pts = []
        for side in range(4):
            for i in range(n):
                u = i / n * 2 - 1
                if side == 0: x, y = u * w / 2, -d / 2
                elif side == 1: x, y = w / 2, u * d / 2
                elif side == 2: x, y = -u * w / 2, d / 2
                else: x, y = -w / 2, -u * d / 2
                ex = max(abs(x) / (w / 2), abs(y) / (d / 2))
                cu = min(abs(x) / (w / 2), abs(y) / (d / 2))
                pts.append(bm.verts.new((x, y, z + (curl * cu ** 6 if curl else 0) - (sag * (1 - cu ** 2) if curl else 0))))
        return pts
    a = ring(w0, d0, 0, lift); b = ring(w1, d1, h, 0)
    N = len(a)
    for i in range(N):
        bm.faces.new((a[i], a[(i + 1) % N], b[(i + 1) % N], b[i]))
    bm.faces.new(b)
    bm.faces.new(list(reversed(a)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from_bm(name, bm, m, coll); o.location = loc
    return o, a

def eave_trim(name, verts_world, m, coll=None, r=.05):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(verts_world)); sp.use_cyclic_u = True
    for i, v in enumerate(verts_world + [verts_world[0]]): sp.points[i].co = (*v, 1)
    o = bpy.data.objects.new(name, cu); (coll or S.collection).objects.link(o); o.data.materials.append(m)
    return o

def roof(name, cx, cy, z, w, d, ov, h, tw, td, coll=None, lift=.9):
    o, ring = frustum(name, w + 2 * ov, d + 2 * ov, tw, td, h, (cx, cy, z), M['roof'], coll, lift=lift, sag=.12)
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = .22
    eave_trim(name + '_trim', [(cx + v.co.x, cy + v.co.y, z + v.co.z - .05) for v in o.data.vertices[:len(ring)]], M['gold'], coll)
    return o

def coll(name):
    c = bpy.data.collections.new(name); S.collection.children.link(c); return c

# ---------------------------------------------------------------- the world
W = S.world = bpy.data.worlds.new('dusk'); W.use_nodes = True
wn = W.node_tree; bg = wn.nodes['Background']
tc = wn.nodes.new('ShaderNodeTexCoord'); sep = wn.nodes.new('ShaderNodeSeparateXYZ'); wn.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
mr = wn.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.04; mr.inputs['From Max'].default_value = .7
wn.links.new(sep.outputs['Z'], mr.inputs['Value'])
ramp = wn.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
for i, (pos, col) in enumerate(((0, '#1a0a0c'), (.055, '#f08a44'), (.11, '#c2402e'), (.24, '#5a1222'), (.5, '#1c0716'), (1, '#050309'))):
    e = cr.elements[i] if i < 2 else cr.elements.new(pos); e.position = pos; e.color = hexrgb(col)
wn.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
SUN_DIR = Vector((-.62, .78, .05)).normalized()
dot = wn.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = SUN_DIR
wn.links.new(tc.outputs['Generated'], dot.inputs[0])
sg = wn.nodes.new('ShaderNodeMapRange'); sg.inputs['From Min'].default_value = .9; sg.inputs['From Max'].default_value = 1.
wn.links.new(dot.outputs['Value'], sg.inputs['Value'])
pw = wn.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 6.
wn.links.new(sg.outputs['Result'], pw.inputs[0])
add = wn.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs['B'].default_value = (6., 2.2, .7, 1)
wn.links.new(pw.outputs['Value'], add.inputs['Factor']); wn.links.new(ramp.outputs['Color'], add.inputs['A'])
wn.links.new(add.outputs['Result'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.

def set_sky(strength, factor=None):
    bg.inputs['Strength'].default_value = strength * 1.8

# fog volume (EEVEE volumetrics)
FOG = coll('fog')
fogbox = box('fogbox', 900, 900, 60, (0, 0, 22), None, coll=FOG)
fm = bpy.data.materials.new('fog'); fm.use_nodes = True; fnt = fm.node_tree
fnt.nodes.remove(fnt.nodes['Principled BSDF'])
vs = fnt.nodes.new('ShaderNodeVolumePrincipled'); vs.inputs['Density'].default_value = .0025
vs.inputs['Color'].default_value = hexrgb('#e8c4b8'); vs.inputs['Anisotropy'].default_value = .55
fnt.links.new(vs.outputs['Volume'], fnt.nodes['Material Output'].inputs['Volume'])
fogbox.data.materials.append(fm)
if A.nofog: FOG.hide_render = True

# ---------------------------------------------------------------- ground and mountains
ENV = coll('env')
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=300)
ground = obj_from_bm('ground', bm, M['pave'], ENV)

def mountains(name, cy, width, base, amp, seed, m, rot=0.):
    rng = np.random.default_rng(seed); nx = 220
    xs = np.linspace(-width / 2, width / 2, nx)
    h = np.zeros(nx)
    for o in range(5):
        f = (2 ** o) * 3 / width; ph = rng.uniform(0, 100)
        h += np.sin(xs * f * 2 * math.pi + ph) * amp / (1.9 ** o) + np.sin(xs * f * 4.3 + ph * 2) * amp * .4 / (2 ** o)
    h = base + np.abs(h)
    bm = bmesh.new(); top = []; bot = []
    for x, z in zip(xs, h):
        top.append(bm.verts.new((x, 0, z))); bot.append(bm.verts.new((x, 0, -5)))
    for i in range(nx - 1): bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
    o = obj_from_bm(name, bm, m, ENV); o.rotation_euler.z = rot
    o.location = (-math.sin(rot) * cy, math.cos(rot) * cy, 0) if rot not in (0., math.pi) else (0, cy, 0)
    return o

mountains('mtn_n1', 420, 1600, 30, 70, 3, M['mtn'])
mountains('mtn_n2', 260, 1200, 12, 38, 4, M['mtn'])
mountains('mtn_s1', -420, 1600, 30, 60, 5, M['mtn'])
mountains('mtn_e', 380, 1600, 20, 50, 6, M['mtn'], -math.pi / 2)
mountains('mtn_w', 380, 1600, 20, 50, 7, M['mtn'], math.pi / 2)

# ---------------------------------------------------------------- the castle keep
CAST = coll('castle')
CY = 30.
base, _ = frustum('ishigaki', 30, 24, 22, 17, 7., (0, CY, 0), M['stone'], CAST)
tiers = [(19, 14, 4.2), (16, 12, 3.6), (13, 10, 3.2), (10.5, 8, 3.), (8, 6.2, 3.4)]
z = 7.
for i, (w, d, h) in enumerate(tiers):
    last = i == len(tiers) - 1
    box(f'tier{i}', w, d, h, (0, CY, z + h / 2), M['wall'], coll=CAST)
    box(f'band{i}', w + .05, d + .05, .25, (0, CY, z + h - .4), M['lacquer'], coll=CAST)
    # lit windows on all four faces
    nw = max(2, int(w / 2.6))
    for k in range(nw):
        x = -w / 2 + (k + .5) * w / nw
        for s in (-1, 1):
            if R.random() < .82:
                box(f'win{i}_{k}_{s}', .7, .06, .9, (x, CY + s * (d / 2 + .02), z + h * .52), M['win'], coll=CAST)
    nd = max(2, int(d / 2.6))
    for k in range(nd):
        y = -d / 2 + (k + .5) * d / nd
        for s in (-1, 1):
            if R.random() < .7:
                box(f'wins{i}_{k}_{s}', .06, .7, .9, (s * (w / 2 + .02), CY + y, z + h * .52), M['win'], coll=CAST)
    nxt = tiers[i + 1] if not last else (4, 2.5, 0)
    rh = 2.6 if last else 1.6
    roof(f'roof{i}', 0, CY, z + h - .2, w, d, 2.2 if not last else 2.6, rh, nxt[0] + (0 if last else .6), nxt[1] + (0 if last else .6), CAST)
    if i in (0, 2):     # chidori gable on the front
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in ((-3.2, 0, 0), (3.2, 0, 0), (0, 0, 2.6), (-3.2, 2.4, 0), (3.2, 2.4, 0), (0, 2.4, 2.6))]
        for f in ((0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)): bm.faces.new([v[j] for j in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        g = obj_from_bm(f'gable{i}', bm, M['roof'], CAST); g.location = (0, CY - d / 2 - 2.4, z + h + .1)
        eave_trim(f'gable{i}_trim', [(-3.3, CY - d / 2 - 2.45, z + h + .05), (0, CY - d / 2 - 2.45, z + h + 2.75), (3.3, CY - d / 2 - 2.45, z + h + .05)], M['gold'], CAST, .06)
    z += h + rh - .2
# ridge and shachihoko
box('ridge', 4.6, .5, .5, (0, CY, z + .1), M['lacquer'], coll=CAST)
for s in (-1, 1):
    sh = cyl(f'shachi{s}', .35, 1.5, (s * 2.3, CY, z + .9), M['gold'], 8, .05, CAST); sh.rotation_euler.y = s * .45
    tl = cyl(f'shachiT{s}', .25, .8, (s * 2.55, CY, z + 1.6), M['gold'], 8, .02, CAST); tl.rotation_euler.y = -s * .8
KEEP_TOP = z
cl = bpy.data.lights.new('keepGlow', 'POINT'); cl.energy = 9000; cl.color = (1, .55, .25); cl.shadow_soft_size = 6
o = bpy.data.objects.new('keepGlow', cl); o.location = (0, CY - 14, 12); CAST.objects.link(o)

# ---------------------------------------------------------------- courtyard walls and the gate
YARD = coll('yard')
GY = -30.
for name, sx, sy, loc in (('wallS_l', 26, 1.2, (-17, GY, 2.4)), ('wallS_r', 26, 1.2, (17, GY, 2.4)),
                          ('wallE', 1.2, 70, (30, 2, 2.4)), ('wallW', 1.2, 70, (-30, 2, 2.4))):
    box(name, sx, sy, 4.8, loc, M['wall'], coll=YARD)
    box(name + '_cap', sx + .9 if sx > sy else sx + .9, sy + .9 if sy > sx else sy + .9, .5, (loc[0], loc[1], 5.05), M['roof'], coll=YARD)
    box(name + '_base', sx + .1, sy + .1, 1.2, (loc[0], loc[1], .6), M['stone'], coll=YARD)
    box(name + '_gold', sx + .12 if sx > sy else sx + .12, sy + .12 if sy > sx else sy + .12, .06, (loc[0], loc[1], 4.6), M['gold'], coll=YARD)
for s in (-1, 1):
    box(f'post{s}', 1.0, 1.0, 7.5, (s * 4.3, GY, 3.75), M['wood'], bevel=.04, coll=YARD)
    for zz in (1.0, 6.4): box(f'postband{s}{zz}', 1.06, 1.06, .2, (s * 4.3, GY, zz), M['gold'], coll=YARD)
box('lintel', 10.5, 1.2, .9, (0, GY, 7.6), M['wood'], coll=YARD)
box('lintel_gold', 10.6, 1.25, .08, (0, GY, 7.18), M['gold'], coll=YARD)
roof('gateRoof', 0, GY, 8.0, 10.5, 2.6, 1.8, 1.8, 5.5, .6, YARD, lift=.6)
# doors: hinged on the posts, swing away from the courtyard
doors = []
for s in (-1, 1):
    piv = bpy.data.objects.new(f'hinge{s}', None); piv.location = (s * 3.8, GY - .1, 0); YARD.objects.link(piv)
    d = box(f'door{s}', 3.8, .3, 7.0, (-s * 1.9, 0, 3.5), M['wood'], coll=YARD); d.parent = piv
    for zz in (1.2, 3.5, 5.8):
        band = box(f'dband{s}{zz}', 3.8, .36, .35, (-s * 1.9, 0, zz), M['lacquer'], coll=YARD); band.parent = piv
        for k in range(8):
            st = cyl(f'stud{s}{zz}{k}', .07, .1, (-s * (.25 + k * .47), .2, zz), M['gold'], 8, coll=YARD); st.rotation_euler.x = math.pi / 2; st.parent = piv
    doors.append((piv, s))
# the light beyond the gate
gl = box('gateLight', 9, .2, 8, (0, GY - 8, 4), M['gateLight'], coll=YARD)
gsun = bpy.data.lights.new('gateSpot', 'SPOT'); gsun.energy = 0; gsun.color = (1, .82, .6); gsun.spot_size = math.radians(55); gsun.shadow_soft_size = 1.5
gso = bpy.data.objects.new('gateSpot', gsun); gso.location = (0, GY - 10, 5); gso.rotation_euler = (math.radians(-80), 0, 0); YARD.objects.link(gso)
gso.rotation_euler = Vector((0, 1, -.08)).to_track_quat('-Z', 'Y').to_euler()

# lanterns
def lantern(x, y, s=1.):
    c = YARD
    box(f'lb{x}{y}', .6 * s, .6 * s, .2 * s, (x, y, .1 * s), M['stoneLamp'], coll=c)
    cyl(f'lc{x}{y}', .14 * s, 1.0 * s, (x, y, .7 * s), M['stoneLamp'], 10, coll=c)
    box(f'lp{x}{y}', .7 * s, .7 * s, .18 * s, (x, y, 1.27 * s), M['stoneLamp'], coll=c)
    box(f'lf{x}{y}', .32 * s, .32 * s, .36 * s, (x, y, 1.55 * s), M['flame'], coll=c)
    frustum(f'lr{x}{y}', 1.0 * s, 1.0 * s, .1, .1, .45 * s, (x, y, 1.74 * s), M['stoneLamp'], c, lift=.08 * s)
    li = bpy.data.lights.new(f'll{x}{y}', 'POINT'); li.energy = 160 * s; li.color = (1, .58, .25); li.shadow_soft_size = .3; li.use_shadow = not A.lite
    lo = bpy.data.objects.new(f'll{x}{y}', li); lo.location = (x, y, 1.55 * s); c.objects.link(lo)
for x, y in ((-6.5, 2.5), (6.5, 2.5), (-5, -12), (5, -12), (-5, -22), (5, -22), (-9, 12), (9, 12)): lantern(x, y)

# banners (nobori) with a flutter
BAN = {k: bpy.data.images.load(os.path.join(SP, f'banner-{k}.png')) for k in ('crimson', 'dark', 'black')}
ban_mats = {}
for k, img in BAN.items():
    m = bpy.data.materials.new('ban_' + k); m.use_nodes = True
    if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
    b = m.node_tree.nodes['Principled BSDF']; tx = m.node_tree.nodes.new('ShaderNodeTexImage'); tx.image = img
    link(m, tx.outputs['Color'], b.inputs['Base Color']); link(m, tx.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Roughness'].default_value = .7
    if 'Transmission Weight' in b.inputs: pass
    link(m, tx.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = .12
    ban_mats[k] = m

def banner(x, y, rotz, kind='crimson', h=3.4):
    w = h * 256 / 1024
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=6, y_segments=18, size=.5)
    for v in bm.verts: v.co = Vector(((v.co.x + .5) * w, 0, (v.co.y + .5) * h))
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        for l in f.loops: l[uv].uv = (l.vert.co.x / w, l.vert.co.z / h)
    o = obj_from_bm(f'ban{x:.1f}_{y:.1f}', bm, ban_mats[kind], YARD); o.location = (x, y, 1.4); o.rotation_euler.z = rotz
    wv = o.modifiers.new('wave', 'WAVE'); wv.use_x = False; wv.use_y = True; wv.use_normal = False
    wv.height = .09; wv.width = .9; wv.speed = .05; wv.narrowness = 1.2; wv.start_position_x = R.uniform(-2, 2)
    wv.falloff_radius = 0; wv.time_offset = R.uniform(-60, 0)
    o.modifiers.new('ss', 'SUBSURF')
    cyl(f'pole{x:.1f}_{y:.1f}', .035, h + 1.6, (x, y, (h + 1.6) / 2), M['wood'], 8, coll=YARD)
    return o

for y in (-26, -21, -16, -11, -6):
    banner(-7.5, y, 0, 'crimson'); banner(7.5, y, math.pi, 'crimson')
for x in (-14, -10.5, 10.5, 14): banner(x, 6, 0, 'dark', 4.2)
for y in (-4, 0, 4, 8): banner(26, y, math.pi / 2, 'crimson')

# sakura trees
def tree(x, y, s, seed):
    rr = random.Random(seed)
    cu = bpy.data.curves.new(f'trunk{seed}', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .14 * s; cu.bevel_resolution = 3
    tips = []
    def br(p, d, ln, depth, rad):
        q = p + d * ln
        sp = cu.splines.new('POLY'); sp.points.add(1)
        sp.points[0].co = (*p, 1); sp.points[1].co = (*q, 1); sp.points[0].radius = rad; sp.points[1].radius = rad * .65
        if depth == 0: tips.append(q); return
        for _ in range(2 + (rr.random() < .4)):
            nd = (d + Vector((rr.uniform(-.8, .8), rr.uniform(-.8, .8), rr.uniform(-.1, .4)))).normalized()
            br(q, nd, ln * .7, depth - 1, rad * .65)
    br(Vector((0, 0, 0)), Vector((0, 0, 1)), 2.0 * s, 4, 1.)
    o = bpy.data.objects.new(f'trunk{seed}', cu); o.data.materials.append(M['trunk']); YARD.objects.link(o); o.location = (x, y, 0)
    bm = bmesh.new()
    for tp in tips:
        for _ in range(7):
            c = tp + Vector((rr.uniform(-.8, .8), rr.uniform(-.8, .8), rr.uniform(-.35, .45))) * s
            bmesh.ops.create_icosphere(bm, subdivisions=2 if A.lite else 3, radius=rr.uniform(.28, .55) * s, matrix=Matrix.Translation(c))
    cn = obj_from_bm(f'canopy{seed}', bm, M['blossom'], YARD); cn.location = (x, y, 0)
    d = cn.modifiers.new('disp', 'DISPLACE'); tx = bpy.data.textures.new(f'cl{seed}', 'CLOUDS'); tx.noise_scale = .12; tx.noise_depth = 3; d.texture = tx; d.strength = .22
for i, (x, y) in enumerate(((-13, -3), (13, -3), (-18, 10), (18, 10), (-12, -18), (12, -18), (22, -10), (-22, -10))):
    tree(x, y, 1.15, 40 + i)

# key and fill lights
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 2.2; sun.color = (1, .45, .28); sun.angle = math.radians(3)
so = bpy.data.objects.new('sun', sun); S.collection.objects.link(so); so.rotation_euler = Vector((.55, .75, -.36)).to_track_quat('-Z', 'Y').to_euler()
moon = bpy.data.lights.new('fill', 'SUN'); moon.energy = .25; moon.color = (.55, .5, .9)
mo = bpy.data.objects.new('fill', moon); S.collection.objects.link(mo); mo.rotation_euler = (math.radians(50), 0, math.radians(40))

# ---------------------------------------------------------------- the cast (cut-out cards)
CAST_C = coll('cast')
def card(name, path, w, h, ax, ay, scale, m=None, coll_=None):
    """A vertical card, origin at pixel (ax, ay) (feet), facing -Y."""
    if m is None: m, _ = image_mat(name, path)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new(((px - ax) * scale, 0, (ay - py) * scale)) for px, py in ((0, h), (w, h), (w, 0), (0, 0))]
    f = bm.faces.new(vs)
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = c
    return obj_from_bm(name, bm, m, coll_ or CAST_C)

GEN = {}
ORDER = [('fish', -2.5), ('bear', -.85), ('bucket', .85), ('pixel', 2.5)]
for v in ('warm', 'green', 'sil'):
    c = coll('gen_' + v)
    for n, x in ORDER:
        fb = META['figures'][f'{n}-{v}-back']
        sc = K * (1.05 if n == 'pixel' else 1.)
        root = bpy.data.objects.new(f'{n}_{v}', None); c.objects.link(root); root.location = (x, 0, 0)
        b = card(f'{n}_{v}_back', os.path.join(SP, f'fig-{n}-{v}-back.png'), fb['w'], fb['h'], fb['feetX'], fb['feetY'], sc, coll_=c)
        b.parent = root; b.location.y = .01
        piv = None
        if v != 'sil':
            ff = META['figures'][f'{n}-{v}-front']
            piv = bpy.data.objects.new(f'{n}_{v}_piv', None); c.objects.link(piv); piv.parent = root
            piv.location = (0, 0, (ff['feetY'] - ff['pivotY']) * sc)
            fr = card(f'{n}_{v}_front', os.path.join(SP, f'fig-{n}-{v}-front.png'), ff['w'], ff['h'], ff['feetX'], ff['pivotY'], sc, coll_=c)
            fr.parent = piv
        GEN[(n, v)] = (root, piv)

# nods in the courtyard (S1b) and the recoil when he halts (S3a)
def bump_keys(obj, path, idx, t0, t1, amount):
    base = getattr(obj, path)[idx]
    for f, v in ((t0 * FPS, 0), ((t0 + t1) / 2 * FPS, amount), (t1 * FPS, 0)):
        getattr(obj, path)[idx] = base + v; obj.keyframe_insert(path, index=idx, frame=f)
    getattr(obj, path)[idx] = base
nods = {'fish': (3.0, 3.5, .05, -.035), 'bear': (3.25, 3.75, -.05, -.04), 'bucket': (3.7, 4.2, .06, -.045), 'pixel': (3.95, 4.3, -.05, .05)}
for n, (a, b, rot, dz) in nods.items():
    _, piv = GEN[(n, 'warm')]
    bump_keys(piv, 'rotation_euler', 1, a, b, rot); bump_keys(piv, 'location', 2, a, b, dz)
    bump_keys(piv, 'rotation_euler', 1, 10.75, 11.25, -.05 - .01 * 'fish bear bucket pixel'.split().index(n))
for n, (a, b, rot) in {'bear': (11.6, 12.4, .04), 'fish': (11.75, 12.45, -.04), 'bucket': (12.5, 13.5, -.06), 'pixel': (12.6, 13.4, .035)}.items():
    _, piv = GEN[(n, 'green')]; bump_keys(piv, 'rotation_euler', 1, a, b, rot)

# ---------------------------------------------------------------- the stranger
def gait_phase(t):
    if t < 5: return 0.
    tA, T = 10.35, .6
    if t <= tA: return (t - 5) / .8
    u = min(t - tA, T); return (tA - 5) / .8 + (u - u * u / (2 * T)) / .8
STRIDE = 180 / .62

rm = META['rider']; RS = K / rm['unit']
rider_mat, rider_tex = image_mat('rider', os.path.join(SP, 'rider', '0240.png'), emit=.55, rough=.5)
rider = card('rider', None, rm['w'], rm['h'], rm['feetX'], rm['feetY'], RS, rider_mat)
rider.scale.x = -1                                           # sprite faces +x; he rides toward -x
rider_light = bpy.data.lights.new('riderGreen', 'POINT'); rider_light.energy = 60; rider_light.color = (.3, 1, .4); rider_light.shadow_soft_size = .2
rlo = bpy.data.objects.new('riderGreen', rider_light); CAST_C.objects.link(rlo); rlo.parent = rider; rlo.location = (94 * K, -.3, 654 * K)

fm_ = META['front']; FS = K / fm_['unit']
front_mat, front_tex = image_mat('front', os.path.join(SP, 'front', '0200.png'), emit=.3, rough=.6)
front = card('front', None, fm_['w'], fm_['h'], fm_['feetX'], fm_['feetY'], FS, front_mat)
front.rotation_euler.z = math.pi                             # faces +y, toward the courtyard

# ---------------------------------------------------------------- the close-up rig (built away from the yard)
CU = coll('closeup')
CUX = 400.
hood_m = mat('hood', '#0d0a0d', .8); hood_in = mat('hoodIn', '#2a060c', .8)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.)
cut = [f for f in bm.faces if f.calc_center_median().y < -.25 and (f.calc_center_median().x ** 2 / .55 + (f.calc_center_median().z + .15) ** 2 / .9) < 1]
bmesh.ops.delete(bm, geom=cut, context='FACES')
hood = obj_from_bm('hood', bm, hood_m, CU); hood.data.materials.append(hood_in)
hood.scale = (1.35, 1.3, 1.6); hood.location = (CUX, 0, 1.75)
sol = hood.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = .06; sol.material_offset = 1
hood.modifiers.new('ss', 'SUBSURF').levels = 1
# peak of the hood
pk, _ = frustum('hoodPeak', .9, .9, .02, .02, 1.0, (CUX, .25, 3.3), hood_m, CU); pk.rotation_euler.x = -.35
# gold trim round the opening
pts = []
for i in range(80):
    a = i / 80 * 2 * math.pi
    pts.append((CUX + math.sin(a) * .741 * 1.35 * 1.0, -.62 * 1.3, 1.75 + (-.15 + math.cos(a) * .949) * 1.6))
eave_trim('hoodTrim', pts, M['gold'], CU, .035)
# void face, eyes, katana — placed as in the NFT
void = bpy.data.materials.new('void'); void.use_nodes = True
_vn = void.node_tree; _vn.nodes.remove(_vn.nodes['Principled BSDF']); _em = _vn.nodes.new('ShaderNodeEmission'); _em.inputs['Color'].default_value = (0, 0, 0, 1)
_vn.links.new(_em.outputs['Emission'], _vn.nodes['Material Output'].inputs['Surface'])
face = box('face', 2.0, .05, 2.6, (CUX, .1, 1.6), void, coll=CU)
EK = 1.25 / 874 * 1.15    # metres per NFT px (eyes ~1.15 m wide)
def nft_card(name, file, nx, ny, w, h, y, emit):
    m, tx = image_mat(name, os.path.join(ROOT, 'assets', 'cut', file), emit=emit, rough=.5)
    o = card(name, None, w, h, 0, 0, EK, m, CU)
    o.location = (CUX + (nx - 680) * EK, y, 1.75 - (ny - 560) * EK)
    return o
eyes = nft_card('eyes', 'green-eyes-eyes.png', 288, 443, 874, 307, -.4, 1.4)
kat = nft_card('katana', 'green-eyes-katana.png', 373, 687, 899, 306, -.9, 1.2)
eg = bpy.data.lights.new('eyeGlow', 'POINT'); eg.energy = 120; eg.color = (.35, 1, .4); eg.shadow_soft_size = .4
ego = bpy.data.objects.new('eyeGlow', eg); ego.location = (CUX, -.7, 1.85); CU.objects.link(ego)
kg = bpy.data.lights.new('kataGlow', 'AREA'); kg.energy = 150; kg.color = (.4, 1, .45); kg.size = 1.2
kgo = bpy.data.objects.new('kataGlow', kg); kgo.location = (CUX + .6, -1.2, 1.15); CU.objects.link(kgo)
for s, col in ((-1, (1, .35, .2)), (1, (1, .2, .25))):
    rl = bpy.data.lights.new(f'cuRim{s}', 'AREA'); rl.energy = 350; rl.color = col; rl.size = 3
    rlo2 = bpy.data.objects.new(f'cuRim{s}', rl); rlo2.location = (CUX + s * 3, 3, 3.5); CU.objects.link(rlo2)
    rlo2.rotation_euler = (Vector((CUX, 0, 1.8)) - rlo2.location).to_track_quat('-Z', 'Y').to_euler()
# horse ears low in frame
for s in (-1, 1):
    e, _ = frustum(f'ear{s}', .22, .1, .02, .02, .5, (CUX - .5 + s * .3, -1.5, .15), M['black'], CU); e.rotation_euler.y = s * .2

# ---------------------------------------------------------------- petals (deterministic, driven by the frame)
NP = 2600
rng = np.random.default_rng(11)
P0 = np.c_[rng.uniform(-40, 40, NP), rng.uniform(-40, 40, NP), rng.uniform(0, 16, NP)]
PV = rng.uniform(.5, 1.0, NP); PF = rng.uniform(.6, 2., NP); PPH = rng.uniform(0, 6.28, NP); PSZ = rng.uniform(.035, .06, NP)
PAX = rng.normal(size=(NP, 3)); PAX /= np.linalg.norm(PAX, axis=1)[:, None]; PSP = rng.uniform(2, 6, NP)
pimg = bpy.data.images.new('petal', 64, 64, alpha=True)
yy, xx = np.mgrid[0:64, 0:64] / 63 * 2 - 1
inside = ((xx / .75) ** 2 + ((yy + .05) / 1.) ** 2 < 1) & ~((np.abs(xx) < .12) & (yy > .8))
px = np.zeros((64, 64, 4), np.float32); px[..., 0] = 1; px[..., 1] = .72 - .25 * (yy + 1) / 2; px[..., 2] = .8 - .2 * (yy + 1) / 2; px[..., 3] = inside
pimg.pixels = px.ravel(); pimg.pack()
pm = bpy.data.materials.new('petal'); pm.use_nodes = True
if hasattr(pm, 'surface_render_method'): pm.surface_render_method = 'DITHERED'
pb = pm.node_tree.nodes['Principled BSDF']; ptx = pm.node_tree.nodes.new('ShaderNodeTexImage'); ptx.image = pimg
link(pm, ptx.outputs['Color'], pb.inputs['Base Color']); link(pm, ptx.outputs['Alpha'], pb.inputs['Alpha'])
link(pm, ptx.outputs['Color'], pb.inputs['Emission Color']); pb.inputs['Emission Strength'].default_value = .5
me = bpy.data.meshes.new('petals')
me.from_pydata(np.zeros((NP * 4, 3)).tolist(), [], [(i * 4, i * 4 + 1, i * 4 + 2, i * 4 + 3) for i in range(NP)])
uvl = me.uv_layers.new(); uvl.data.foreach_set('uv', np.tile([0, 0, 1, 0, 1, 1, 0, 1], NP).astype(np.float32))
me.materials.append(pm)
petals = bpy.data.objects.new('petals', me); S.collection.objects.link(petals)
PET = {'center': np.array([0, 0, 0.]), 'wind': 1., 'swirl': None}

def rot_mats(ax, ang):
    c, s = np.cos(ang), np.sin(ang); x, y, z = ax[:, 0], ax[:, 1], ax[:, 2]; C = 1 - c
    return np.stack([np.stack([c + x * x * C, x * y * C - z * s, x * z * C + y * s], -1),
                     np.stack([y * x * C + z * s, c + y * y * C, y * z * C - x * s], -1),
                     np.stack([z * x * C - y * s, z * y * C + x * s, c + z * z * C], -1)], -2)

def update_petals(t):
    c, wnd = PET['center'], PET['wind']
    pos = P0.copy()
    pos[:, 2] = (P0[:, 2] - PV * t * 1.1) % 16
    pos[:, 0] = (P0[:, 0] - wnd * PV * t * 1.4 + np.sin(PF * t + PPH) * .6 + 40) % 80 - 40
    pos[:, 1] = (P0[:, 1] + np.cos(PF * t * .7 + PPH) * .5 + 40) % 80 - 40
    sw = PET['swirl']
    if sw:
        a = PPH + t * sw['spin'] * (1 + PF * .3); r = sw['r'] * (.3 + .7 * (np.arange(NP) * .618 % 1))
        tgt = np.c_[sw['c'][0] + np.cos(a) * r, sw['c'][1] + np.sin(a) * r, sw['c'][2] + ((P0[:, 2] - t * 1.5) % 5) - 1]
        pos = pos + (tgt - pos) * sw['k']
    pos += c
    R3 = rot_mats(PAX, PSP * t + PPH)
    quad = np.array([[-1, 0, -1], [1, 0, -1], [1, 0, 1], [-1, 0, 1]], np.float64)
    co = np.einsum('nij,kj->nki', R3, quad) * PSZ[:, None, None] + pos[:, None, :]
    me.vertices.foreach_set('co', co.ravel().astype(np.float32)); me.update()

# ---------------------------------------------------------------- cameras and shots
def camera(name, lens=35, fstop=None, focus=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 2000; cd.sensor_width = 36
    if fstop: cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop; cd.dof.focus_distance = focus or 10
    o = bpy.data.objects.new(name, cd); S.collection.objects.link(o); return o

def look(cam, pos, tgt, roll=0.):
    cam.location = pos
    q = (Vector(tgt) - Vector(pos)).to_track_quat('-Z', 'Y'); cam.rotation_euler = q.to_euler()
    cam.rotation_euler.rotate_axis('Z', roll)

def ease(u): u = max(0., min(1., u)); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def lerpv(a, b, u): return [x + (y - x) * u for x, y in zip(a, b)]
def sstep(a, b, x): u = max(0., min(1., (x - a) / (b - a))); return u * u * (3 - 2 * u)

SHOTS = {}
def shot(name, f0, f1, lens, fstop, setup):
    SHOTS[name] = dict(f0=f0, f1=f1, cam=camera('cam_' + name, lens, fstop), setup=setup)

GENV = {'warm': 1, 'green': 0, 'sil': 0}
def show(*names):
    vis = set(names)
    for c in bpy.data.collections:
        c.hide_render = (c.name not in vis and c.name not in ('env',)) or (A.nofog and c.name == 'fog')
def pose_doors(open_):
    for piv, s in doors: piv.rotation_euler.z = s * open_ * 1.35
def set_rider_frame(f, show_=True):
    rider.hide_render = not show_; rlo.hide_render = not show_
    f = max(240, min(340, f)); rider_tex_node().image.filepath = os.path.join(SP, 'rider', f'{f:04d}.png')
def rider_tex_node(): return rider_mat.node_tree.nodes[rider_mat['tex']]
def front_tex_node(): return front_mat.node_tree.nodes[front_mat['tex']]

def s1a(f, t, cam):            # the castle in the mist
    show('castle', 'yard', 'gen_warm', 'fog', 'env')
    u = ease(t / 2.85)
    look(cam, lerpv((-15, -50, 15.5), (-9, -37, 12.5), u), (0, CY, 9 - u))
    set_sky(.55, .85); PET.update(center=np.array([0, -30, 0.]), wind=1., swirl=None)
    vs.inputs['Density'].default_value = .0028
def s1b(f, t, cam):            # the generals in the courtyard
    show('castle', 'yard', 'gen_warm', 'fog', 'env')
    u = ease((t - 2.55) / 2.6)
    look(cam, (lerpv((1.4, -7.6, 1.5), (-1.4, -7.4, 1.55), u)), (lerpv((.6, 0, 1.25), (-.6, 0, 1.25), u)))
    cam.data.dof.focus_distance = 7.5
    dim = sstep(4.55, 5.1, t); set_sky(.55 - .3 * dim, .85); sun.energy = 2.2 * (1 - .6 * dim)
    PET.update(center=np.array([0, -6, 0.]), wind=1. + 2 * dim, swirl=None)
def s2a(f, t, cam):            # the gate opens
    show('yard', 'gen_sil', 'fog', 'env', 'cast')
    rider.hide_render = True; rlo.hide_render = True
    u = ease((t - 4.85) / 3.45)
    look(cam, lerpv((0, 4.2, 1.75), (0, 1.0, 1.85), u), (0, GY, 3.2))
    cam.data.dof.focus_distance = 30
    op = ease((t - 6.25) / 1.15); pose_doors(op)
    M['gateLight'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 25 * op
    gsun.energy = 60000 * op
    set_sky(.22, .95); sun.energy = .5
    front.hide_render = t < 6.7
    k = ease((t - 6.85) / 1.45); front.location = (0, GY - 2 + k * 14, 0)
    front_tex_node().image.filepath = os.path.join(SP, 'front', f'{max(200, min(250, f)):04d}.png')
    PET.update(center=np.array([0, -14, 0.]), wind=1.4, swirl=None)
    vs.inputs['Density'].default_value = .005
def s2b(f, t, cam):            # low angle, the slow reveal
    show('castle', 'yard', 'fog', 'env', 'cast')
    front.hide_render = True
    x = 16 - STRIDE * K * gait_phase(t) + STRIDE * K * gait_phase(8.1)
    rider.location = (x, -1.5, 0); set_rider_frame(f)
    tilt = ease((t - 8.2) / 1.45)
    cx = x - .35 + .0 * tilt
    look(cam, (cx + .6, -5.2, .18), (cx - .1, -1.5, lerpv((.45,), (2.45,), tilt)[0]))
    cam.data.dof.focus_distance = 3.9
    set_sky(.6, .85); sun.energy = 2.2; vs.inputs['Density'].default_value = .0025
    PET.update(center=np.array([x, -2, 0.]), wind=1., swirl=dict(c=(x - .3, -1.6, 2.4), r=2.2, k=.7, spin=1.4))
def s3a(f, t, cam):            # he halts before them
    show('castle', 'yard', 'gen_warm', 'fog', 'env', 'cast')
    front.hide_render = True
    x = 7.6 - STRIDE * K * (gait_phase(t) - gait_phase(10.))
    rider.location = (x, .35, 0); set_rider_frame(f)
    u = ease((t - 10.) / 1.25)
    look(cam, lerpv((1.6, -11.5, 1.6), (1.6, -10.6, 1.62), u), (1.6, 0, 1.35))
    cam.data.dof.focus_distance = 11
    set_sky(.55, .85); sun.energy = 2.2
    PET.update(center=np.array([2, -4, 0.]), wind=1., swirl=dict(c=(x, .2, 2.2), r=2.6, k=.4 * sstep(10.4, 11, t), spin=1.2))
def s3b(f, t, cam):            # "Who is that man?"
    show('castle', 'yard', 'gen_green', 'fog', 'env')
    u = ease((t - 11.25) / 1.2)
    look(cam, lerpv((-1.7, -3.3, 1.5), (-1.7, -3.0, 1.5), u), (-1.65, 0, 1.38))
    cam.data.dof.focus_distance = 3.2
    set_sky(.4, .9); sun.energy = 1.4
    PET.update(center=np.array([-1.7, -2, 0.]), wind=.7, swirl=None)
def s3c(f, t, cam):            # "What an overwhelming presence…"
    show('castle', 'yard', 'gen_green', 'fog', 'env')
    u = ease((t - 12.45) / 1.1)
    look(cam, lerpv((1.75, -3.1, 1.3), (1.75, -2.8, 1.32), u), (1.7, 0, 1.2))
    cam.data.dof.focus_distance = 3.0
    set_sky(.4, .9); sun.energy = 1.4
    PET.update(center=np.array([1.7, -2, 0.]), wind=.7, swirl=None)
def s3d(f, t, cam):            # the close-up
    show('closeup', 'env'); rlo.hide_render = True
    u = ease((t - 13.55) / .85)
    look(cam, lerpv((CUX - .08, -3.25, .95), (CUX - .04, -2.9, 1.0), u), (CUX, 0, 1.72), roll=-.01 + .015 * u)
    cam.data.dof.focus_distance = 3.6
    fl = sstep(14.02, 14.32, t)
    eyes.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.4 + 5 * fl
    rider_light.energy = 0; eg.energy = 120 + 500 * fl
    set_sky(.35, .9)
    PET.update(center=np.array([CUX, -2.5, -1.]), wind=1.2, swirl=dict(c=(CUX, -2.4, 1.7), r=2.6, k=.5, spin=1.1))

shot('s1a', 0, 85, 32, 5.6, s1a)
shot('s1b', 76, 154, 42, 2.4, s1b)
shot('s2a', 145, 249, 30, 6., s2a)
shot('s2b', 243, 300, 20, 2.8, s2b)
shot('s3a', 300, 337, 30, 5., s3a)
shot('s3b', 337, 373, 45, 2.0, s3b)
shot('s3c', 373, 406, 55, 1.8, s3c)
shot('s3d', 406, 432, 28, 2.8, s3d)
# a pure-black shot so the composer has a frame for the tail
bpy.data.collections['closeup'].hide_render = True
for c in ('gen_green', 'gen_sil'): bpy.data.collections[c].hide_render = True

# ---------------------------------------------------------------- render settings
r = S.render
eng = {'EEVEE': 'BLENDER_EEVEE', 'CYCLES': 'CYCLES'}[A.engine.upper()]
try: r.engine = eng
except TypeError: r.engine = 'BLENDER_EEVEE_NEXT'
r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, A.pct
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'
r.film_transparent = False
S.view_settings.view_transform = 'Standard'
try: S.view_settings.look = 'Medium High Contrast'
except Exception: pass
S.view_settings.exposure = .25
if r.engine.startswith('BLENDER_EEVEE'):
    e = S.eevee; e.taa_render_samples = A.samples
    for k, v in (('use_shadows', True), ('use_volumetric_shadows', True), ('volumetric_tile_size', A.vtile), ('volumetric_samples', 32),
                 ('volumetric_end', 300.), ('use_raytracing', bool(A.rt)), ('use_gtao', True), ('volumetric_light_clamp', 0.)):
        try: setattr(e, k, v)
        except Exception as ex: print('eevee', k, ex)
else:
    S.cycles.samples = A.samples; S.cycles.use_denoising = True; S.cycles.device = 'CPU'
    S.cycles.max_bounces = 3; S.cycles.volume_bounces = 0; S.cycles.use_adaptive_sampling = True
    S.cycles.adaptive_threshold = .05; S.cycles.denoiser = 'OPENIMAGEDENOISE'; S.cycles.use_light_tree = True
    S.cycles.volume_step_rate = 4.; S.cycles.blur_glossy = 2.

if A.save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(A.save))

# ---------------------------------------------------------------- render
os.makedirs(A.out, exist_ok=True)
json.dump([dict(name=k, f0=v['f0'], f1=v['f1']) for k, v in SHOTS.items()], open(os.path.join(A.out, 'shots.json'), 'w'))
want = list(SHOTS) if A.shots == 'all' else A.shots.split(',')
for name in want:
    sh = SHOTS[name]; S.camera = sh['cam']
    frames = [A.still] if A.still is not None else range(sh['f0'], sh['f1'] + 1)
    if A.still is not None and not (sh['f0'] <= A.still <= sh['f1']): frames = [(sh['f0'] + sh['f1']) // 2]
    if A.still is not None and A.still < 0: frames = range(sh['f0'], sh['f0'] + 3)
    os.makedirs(os.path.join(A.out, name), exist_ok=True)
    for f in frames:
        if A.still is None and os.path.exists(os.path.join(A.out, name, f'{f:04d}.png')): continue
        S.frame_set(f)
        t = f / FPS
        sh['setup'](f, t, sh['cam'])
        update_petals(t)
        r.filepath = os.path.join(A.out, name, f'{f:04d}.png')
        bpy.ops.render.render(write_still=True)
        print(f'{name} {f}', flush=True)
