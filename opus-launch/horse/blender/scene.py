# The realistic horses shot: a bay horse galloping along the crest of a grassy hill at golden
# hour, the camera tracking it from the side, fields and a tree line far behind.
# 15 frames at 25 fps (film 8.12 - 8.72 s).
#   python scene.py <out_dir> <width> <height> <samples> [frames...]   (after rig.py; bpy 4.5)
# Look knobs (environment): SUN_A sun azimuth in degrees from the camera side toward the horse's
# head, SUN_E its elevation, SUN_W its strength, SKY_W the sky strength, FSTOP.
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Vector, Matrix, noise as mnoise
from mathutils.kdtree import KDTree
sys.path.insert(0, '.')
import gait, posehorse

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
OUT, RW, RH, SAMPLES = args[0], int(args[1]), int(args[2]), int(args[3])
FRAMES = [int(a) for a in args[4:]] or list(range(1, 16))
def knob(k, d): return float(os.environ.get(k, d))
SUN_A, SUN_E, SUN_W, SKY_W = knob('SUN_A', 62), knob('SUN_E', 11), knob('SUN_W', 4.5), knob('SKY_W', 0.4)
FSTOP = knob('FSTOP', 2.4)

S, MID = 14.2, 0.015
def P(x, y, z): return Vector(((x - MID) * S, y * S, (z + 0.0765) * S))
FPS = 25
PHI0 = 0.62                      # stride phase at frame 1
R = 16.0                         # hill radius
REF = 8                          # the frame the hair and eyes are built on
rng = random.Random(7)

bpy.ops.wm.open_mainfile(filepath='horse_rig.blend')
sc = bpy.context.scene
arm = bpy.data.objects['HorseRig']; horse = bpy.data.objects['Horse']
sc.render.fps = FPS

def node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k.startswith('in_'): n.inputs[k[3:].replace('_', ' ')].default_value = v
        else: setattr(n, k, v)
    return n

def math_node(nt, op, a=None, b=None, c=None):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op
    for i, v in enumerate((a, b, c)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: nt.links.new(v, n.inputs[i])
    return n.outputs[0]

# the sun, as a direction toward it
sun_dir = Vector((math.cos(math.radians(SUN_A)) * math.cos(math.radians(SUN_E)),
                  math.sin(math.radians(SUN_A)) * math.cos(math.radians(SUN_E)), math.sin(math.radians(SUN_E))))

def sky_node(nt):
    """The same Nishita sky as the world, for the haze on far objects."""
    sk = nt.nodes.new('ShaderNodeTexSky'); sk.sky_type = 'NISHITA'
    sk.sun_elevation = math.radians(SUN_E); sk.sun_rotation = math.radians(SUN_A - 90)
    sk.sun_disc = False; sk.air_density = 1.2; sk.dust_density = 2.0
    return sk

def add_haze(mat, dist):
    """Aerial perspective: blend the surface toward the sky behind it with the distance from the camera."""
    nt = mat.node_tree; out = nt.nodes['Material Output']
    surf = out.inputs['Surface'].links[0].from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    view = nt.nodes.new('ShaderNodeVectorMath'); view.operation = 'SCALE'
    nt.links.new(geo.outputs['Incoming'], view.inputs[0]); view.inputs['Scale'].default_value = -1.0
    sk = sky_node(nt); nt.links.new(view.outputs[0], sk.inputs['Vector'])
    cam = nt.nodes.new('ShaderNodeCameraData')
    f = math_node(nt, 'DIVIDE', cam.outputs['View Distance'], -dist)
    f = math_node(nt, 'EXPONENT', f)
    f = math_node(nt, 'SUBTRACT', 1.0, f)
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(sk.outputs['Color'], em.inputs['Color'])
    em.inputs['Strength'].default_value = SKY_W
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(f, mix.inputs[0]); nt.links.new(surf, mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])

# ------------------------------------------------------------------ coat: a bay, black points
coat = bpy.data.materials.new('Coat'); coat.use_nodes = True
nt = coat.node_tree; bsdf = nt.nodes['Principled BSDF']
tc = node(nt, 'ShaderNodeTexCoord'); gen = tc.outputs['Generated']
sep = node(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(gen, sep.inputs[0])
n1 = node(nt, 'ShaderNodeTexNoise', in_Scale=4.0, in_Detail=3.0, in_Roughness=0.5); nt.links.new(gen, n1.inputs['Vector'])
body = node(nt, 'ShaderNodeValToRGB'); c = body.color_ramp
c.elements[0].position = 0.3; c.elements[0].color = (0.085, 0.024, 0.008, 1)
c.elements[1].position = 0.72; c.elements[1].color = (0.165, 0.05, 0.016, 1)
nt.links.new(n1.outputs['Fac'], body.inputs['Fac'])
# black from the knees and hocks down, with a ragged edge
n2 = node(nt, 'ShaderNodeTexNoise', in_Scale=14.0, in_Detail=2.0); nt.links.new(gen, n2.inputs['Vector'])
zj = math_node(nt, 'MULTIPLY_ADD', n2.outputs['Fac'], 0.05, sep.outputs['Z'])
pts = node(nt, 'ShaderNodeMapRange', in_From_Min=0.285, in_From_Max=0.36, in_To_Min=1.0, in_To_Max=0.0)
nt.links.new(zj, pts.inputs['Value'])
mix_pts = node(nt, 'ShaderNodeMix', data_type='RGBA'); mix_pts.inputs[7].default_value = (0.02, 0.015, 0.012, 1)
nt.links.new(pts.outputs['Result'], mix_pts.inputs['Factor']); nt.links.new(body.outputs['Color'], mix_pts.inputs[6])
# dark muzzle: distance (metres) from the muzzle tip in the rest pose
mz = node(nt, 'ShaderNodeVectorMath', operation='SUBTRACT'); nt.links.new(gen, mz.inputs[0])
mz.inputs[1].default_value = ((-0.030 + 0.042) / 0.084, (0.090 + 0.0917) / 0.1834, (0.040 + 0.0764) / 0.1528)
mzs = node(nt, 'ShaderNodeVectorMath', operation='MULTIPLY'); nt.links.new(mz.outputs[0], mzs.inputs[0])
mzs.inputs[1].default_value = (0.084 * S, 0.1834 * S, 0.1528 * S)
mzl = node(nt, 'ShaderNodeVectorMath', operation='LENGTH'); nt.links.new(mzs.outputs[0], mzl.inputs[0])
muz = node(nt, 'ShaderNodeMapRange', in_From_Min=0.11, in_From_Max=0.22, in_To_Min=0.85, in_To_Max=0.0)
nt.links.new(mzl.outputs['Value'], muz.inputs['Value'])
mix_muz = node(nt, 'ShaderNodeMix', data_type='RGBA'); mix_muz.inputs[7].default_value = (0.03, 0.017, 0.011, 1)
nt.links.new(muz.outputs['Result'], mix_muz.inputs['Factor']); nt.links.new(mix_pts.outputs[2], mix_muz.inputs[6])
# hooves: slate grey horn
hoof = node(nt, 'ShaderNodeMapRange', in_From_Min=0.052, in_From_Max=0.044, in_To_Min=0.0, in_To_Max=1.0)
nt.links.new(sep.outputs['Z'], hoof.inputs['Value'])
mix_hoof = node(nt, 'ShaderNodeMix', data_type='RGBA'); mix_hoof.inputs[7].default_value = (0.045, 0.04, 0.036, 1)
nt.links.new(hoof.outputs['Result'], mix_hoof.inputs['Factor']); nt.links.new(mix_muz.outputs[2], mix_hoof.inputs[6])
nt.links.new(mix_hoof.outputs[2], bsdf.inputs['Base Color'])
rough = node(nt, 'ShaderNodeMapRange', in_To_Min=0.5, in_To_Max=0.32); nt.links.new(hoof.outputs['Result'], rough.inputs['Value'])
nt.links.new(rough.outputs['Result'], bsdf.inputs['Roughness'])
# a groomed coat: sheen, and highlights drawn out across the lie of the hair
bsdf.inputs['Specular IOR Level'].default_value = 0.38
bsdf.inputs['Anisotropic'].default_value = 0.6
tan = node(nt, 'ShaderNodeTangent', direction_type='RADIAL', axis='Y'); nt.links.new(tan.outputs[0], bsdf.inputs['Tangent'])
bsdf.inputs['Sheen Weight'].default_value = 0.25
bsdf.inputs['Sheen Roughness'].default_value = 0.35
bsdf.inputs['Sheen Tint'].default_value = (1.0, 0.8, 0.62, 1)
bsdf.inputs['Subsurface Weight'].default_value = 0.03
bsdf.inputs['Subsurface Radius'].default_value = (0.5, 0.2, 0.1)
bsdf.inputs['Subsurface Scale'].default_value = 0.03
# hair grain: fine streaks along the body
mp = node(nt, 'ShaderNodeMapping'); nt.links.new(gen, mp.inputs['Vector']); mp.inputs['Scale'].default_value = (520, 60, 520)
grain = node(nt, 'ShaderNodeTexNoise', in_Scale=1.0, in_Detail=3.0); nt.links.new(mp.outputs[0], grain.inputs['Vector'])
bump = node(nt, 'ShaderNodeBump', in_Strength=0.16, in_Distance=0.001)
nt.links.new(grain.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
horse.data.materials.clear(); horse.data.materials.append(coat)

# ------------------------------------------------------------------ the hill and its grass
bpy.ops.mesh.primitive_uv_sphere_add(segments=720, ring_count=360, radius=R, location=(0, 0, -R), rotation=(0, math.pi / 2, 0))
hill = bpy.context.active_object; hill.name = 'Hill'; hill.rotation_mode = 'YXZ'
bpy.ops.object.shade_smooth()
vg = hill.vertex_groups.new(name='grass')
mw = hill.matrix_world
for v in hill.data.vertices:
    w = mw @ v.co
    if w.z > -3.2 and abs(w.x) < 7.5:
        vg.add([v.index], 1.0, 'REPLACE')
soil = bpy.data.materials.new('Soil'); soil.use_nodes = True
sb = soil.node_tree.nodes['Principled BSDF']
sb.inputs['Base Color'].default_value = (0.035, 0.05, 0.012, 1); sb.inputs['Roughness'].default_value = 0.95
grass_mat = bpy.data.materials.new('Grass'); grass_mat.use_nodes = True
gt = grass_mat.node_tree; gb = gt.nodes['Principled BSDF']
hi = gt.nodes.new('ShaderNodeHairInfo')
gr = gt.nodes.new('ShaderNodeValToRGB')
gr.color_ramp.elements[0].color = (0.05, 0.12, 0.02, 1)
gr.color_ramp.elements[1].color = (0.28, 0.33, 0.08, 1)
e = gr.color_ramp.elements.new(0.5); e.color = (0.12, 0.22, 0.04, 1)
gt.links.new(hi.outputs['Random'], gr.inputs['Fac'])
tipmix = gt.nodes.new('ShaderNodeMix'); tipmix.data_type = 'RGBA'
tipmix.inputs[7].default_value = (0.42, 0.4, 0.16, 1)
gt.links.new(hi.outputs['Intercept'], tipmix.inputs['Factor'])
gt.links.new(gr.outputs['Color'], tipmix.inputs[6])
gt.links.new(tipmix.outputs[2], gb.inputs['Base Color'])
gb.inputs['Roughness'].default_value = 0.6
gb.inputs['Transmission Weight'].default_value = 0.15
hill.data.materials.append(soil); hill.data.materials.append(grass_mat)
mod = hill.modifiers.new('grass', 'PARTICLE_SYSTEM')
ps = mod.particle_system.settings
ps.type = 'HAIR'; ps.count = 70000; ps.hair_length = 0.055
ps.use_advanced_hair = True
ps.factor_random = 0.3
ps.child_type = 'INTERPOLATED'; ps.child_percent = 4; ps.rendered_child_count = 4
ps.child_length = 1.0; ps.child_length_threshold = 0.4
ps.roughness_1 = 0.02; ps.roughness_2 = 0.06; ps.roughness_endpoint = 0.02
ps.use_hair_bspline = True
ps.material = 2
ps.radius_scale = 1.0; ps.root_radius = 0.0025; ps.tip_radius = 0.0003
ps.display_step = 3; ps.render_step = 3
mod.particle_system.vertex_group_density = 'grass'
mod.particle_system.seed = 3

# ------------------------------------------------------------------ far away: fields and trees
far = bpy.data.objects.new('Far', None); sc.collection.objects.link(far)
def ground_h(x, y):
    q = Vector((x / 260.0, y / 260.0, 0.3))
    h = 10.0 * mnoise.fractal(q, 1.0, 2.0, 4) + 3.0 * mnoise.noise(Vector((x / 60.0, y / 60.0, 1.7)))
    h += max(0.0, (-x - 1100.0) / 600.0) ** 1.5 * 45.0          # far hills rise to meet the sky
    return -14.0 + h
NX, NY = 220, 150
bm = bmesh.new()
verts = []
for i in range(NX + 1):
    u = i / NX; x = -70.0 - 1830.0 * u * u
    row = []
    for j in range(NY + 1):
        y = -650.0 + 1300.0 * j / NY
        row.append(bm.verts.new((x, y, ground_h(x, y))))
    verts.append(row)
for i in range(NX):
    for j in range(NY):
        f = bm.faces.new((verts[i][j], verts[i][j + 1], verts[i + 1][j + 1], verts[i + 1][j])); f.smooth = True
me = bpy.data.meshes.new('Fields'); bm.normal_update(); bm.to_mesh(me); bm.free()
fields = bpy.data.objects.new('Fields', me); sc.collection.objects.link(fields); fields.parent = far
fm = bpy.data.materials.new('Fields'); fm.use_nodes = True
ft = fm.node_tree; fb = ft.nodes['Principled BSDF']
ftc = node(ft, 'ShaderNodeTexCoord')
fn = node(ft, 'ShaderNodeTexNoise', in_Scale=0.006, in_Detail=2.0); ft.links.new(ftc.outputs['Object'], fn.inputs['Vector'])
fr = node(ft, 'ShaderNodeValToRGB'); c = fr.color_ramp
c.elements[0].position = 0.42; c.elements[0].color = (0.05, 0.085, 0.02, 1)
c.elements[1].position = 0.58; c.elements[1].color = (0.24, 0.17, 0.06, 1)
ft.links.new(fn.outputs['Fac'], fr.inputs['Fac']); ft.links.new(fr.outputs['Color'], fb.inputs['Base Color'])
fb.inputs['Roughness'].default_value = 0.9
fields.data.materials.append(fm); add_haze(fm, 800.0)

def tree_mesh(seed, h):
    r = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=8, radius1=0.022 * h, radius2=0.012 * h, depth=0.45 * h,
                          matrix=Matrix.Translation((0, 0, 0.225 * h)))
    n_trunk = len(bm.faces)
    for k in range(18):
        a = r.uniform(0, 6.28); rr = 0.2 * h * math.sqrt(r.random())
        c = Vector((rr * math.cos(a), rr * math.sin(a), h * (0.35 + 0.5 * r.random() ** 0.8)))
        rad = h * r.uniform(0.09, 0.17) * (1.25 - 0.5 * (c.z / h - 0.35))
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rad, matrix=Matrix.Translation(c))
        for v in res['verts']:
            d = (v.co - c).normalized()
            v.co += d * rad * (0.4 * mnoise.noise(v.co * (1.6 / rad) + Vector((seed, 0, 0))) + 0.18 * mnoise.noise(v.co * (4.5 / rad)))
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.smooth = True; f.material_index = 1 if f.index >= n_trunk else 0
    me = bpy.data.meshes.new(f'Tree{seed}'); bm.normal_update(); bm.to_mesh(me); bm.free()
    return me
bark = bpy.data.materials.new('Bark'); bark.use_nodes = True
bark.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.03, 0.024, 0.017, 1)
leaves = bpy.data.materials.new('Leaves'); leaves.use_nodes = True
lt = leaves.node_tree; lb = lt.nodes['Principled BSDF']
oi = node(lt, 'ShaderNodeObjectInfo')
lr = node(lt, 'ShaderNodeValToRGB'); c = lr.color_ramp
c.elements[0].color = (0.012, 0.024, 0.008, 1); c.elements[1].color = (0.04, 0.05, 0.016, 1)
ltc = node(lt, 'ShaderNodeTexCoord')
ln = node(lt, 'ShaderNodeTexNoise', in_Scale=0.35, in_Detail=4.0); lt.links.new(ltc.outputs['Object'], ln.inputs['Vector'])
lsum = math_node(lt, 'MULTIPLY_ADD', ln.outputs['Fac'], 0.6, oi.outputs['Random'])
lsum = math_node(lt, 'MULTIPLY', lsum, 0.62)
lt.links.new(lsum, lr.inputs['Fac']); lt.links.new(lr.outputs['Color'], lb.inputs['Base Color'])
lb.inputs['Roughness'].default_value = 0.75
lb.inputs['Subsurface Weight'].default_value = 0.2
lbump = node(lt, 'ShaderNodeBump', in_Strength=0.6)
ln2 = node(lt, 'ShaderNodeTexNoise', in_Scale=3.0, in_Detail=3.0); lt.links.new(ltc.outputs['Object'], ln2.inputs['Vector'])
lt.links.new(ln2.outputs['Fac'], lbump.inputs['Height']); lt.links.new(lbump.outputs['Normal'], lb.inputs['Normal'])
add_haze(bark, 800.0); add_haze(leaves, 800.0)
tree_meshes = []
for k in range(4):
    m = tree_mesh(11 + k, 1.0)
    m.materials.append(bark); m.materials.append(leaves)
    tree_meshes.append(m)
trng = random.Random(21)
def plant(x, y, h):
    ob = bpy.data.objects.new('Tree', trng.choice(tree_meshes)); sc.collection.objects.link(ob)
    ob.location = (x, y, ground_h(x, y) - 0.5); ob.scale = (h * trng.uniform(0.85, 1.2), h * trng.uniform(0.85, 1.2), h)
    ob.rotation_euler = (0, 0, trng.uniform(0, 6.28)); ob.parent = far
y = -160.0
while y < 180.0:                                    # a hedgerow with trees across the middle distance
    plant(-430.0 + trng.gauss(0, 8), y, trng.uniform(10, 17)); y += trng.uniform(3, 9)
for _ in range(220):                                # copses and single trees further off
    cx, cy = -trng.uniform(600, 1500), trng.uniform(-330, 330)
    for _ in range(trng.randint(1, 6)):
        plant(cx + trng.gauss(0, 14), cy + trng.gauss(0, 14), trng.uniform(9, 20))

# ------------------------------------------------------------------ light, sky, camera
world = bpy.data.worlds.new('Sky'); sc.world = world; world.use_nodes = True
wt = world.node_tree; bg = wt.nodes['Background']
sky = sky_node(wt)
wt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = SKY_W
sun_d = bpy.data.lights.new('Sun', 'SUN'); sun_d.energy = SUN_W; sun_d.angle = math.radians(1.2)
sun_d.color = (1.0, 0.8, 0.6)
sun = bpy.data.objects.new('Sun', sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (-sun_dir).to_track_quat('-Z', 'Y').to_euler()

cam_d = bpy.data.cameras.new('Cam'); cam_d.lens = 75; cam_d.sensor_width = 36
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = FSTOP
cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
target = Vector((0.0, -0.2, 1.12))
cam.location = Vector((12.5, -0.2, 1.1))
d = (target - cam.location).normalized()
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam_d.dof.focus_distance = (target - cam.location).length

# ------------------------------------------------------------------ animation
sc.frame_start, sc.frame_end = 0, 16
for f in range(0, 17):
    phi = (PHI0 + (f - 1) / 10.0) % 1.0        # a stride every 10 frames (0.4 s)
    posehorse.pose_at(arm, phi, head_turn=math.radians(-52))
    # tail swings with the stride
    tb = arm.pose.bones['tail']
    m = tb.matrix.copy(); piv = m.to_translation()
    tb.matrix = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(8) * math.sin(2 * math.pi * (phi - 0.2)), 4, 'X') @ Matrix.Translation(-piv) @ m
    bpy.context.view_layer.update()
    posehorse.key_all(arm, f)
    hill.rotation_euler = ((f - 1) / FPS * gait.SPEED / R, math.pi / 2, 0)   # rolls under the horse at its speed
    hill.keyframe_insert('rotation_euler', frame=f)
    far.location = (0, -gait.SPEED * (f - 1) / FPS, 0)                        # the land goes by
    far.keyframe_insert('location', frame=f)
for ob in (arm, hill, far):
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ------------------------------------------------------------------ hair and eyes, built on the posed horse
sc.frame_set(REF)
dg = bpy.context.evaluated_depsgraph_get()
ev = horse.evaluated_get(dg); emesh = ev.to_mesh()
EV = [horse.matrix_world @ v.co for v in emesh.vertices]
EN = [(horse.matrix_world.to_3x3() @ v.normal).normalized() for v in emesh.vertices]
ev.to_mesh_clear()
kd = KDTree(len(horse.data.vertices))
for v in horse.data.vertices: kd.insert(v.co, v.index)
kd.balance()
def main_bone(vi):
    g = max(horse.data.vertices[vi].groups, key=lambda g: g.weight)
    return horse.vertex_groups[g.group].name

def wave_group():
    """Geometry nodes: a travelling wave along each strand, growing toward the tip."""
    ng = bpy.data.node_groups.new('HairWave', 'GeometryNodeTree')
    it = ng.interface
    it.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    it.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    for nm in ('Amp', 'Waves', 'Hz', 'Power'): it.new_socket(nm, in_out='INPUT', socket_type='NodeSocketFloat')
    for nm in ('DirA', 'DirB'): it.new_socket(nm, in_out='INPUT', socket_type='NodeSocketVector')
    N, Lk = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    sp = N.new('GeometryNodeSplineParameter'); st = N.new('GeometryNodeInputSceneTime')
    idx = N.new('GeometryNodeInputIndex')
    fod = N.new('GeometryNodeFieldOnDomain'); fod.domain = 'CURVE'; fod.data_type = 'INT'
    Lk.new(idx.outputs[0], [s for s in fod.inputs if s.enabled][0])
    rnd = N.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT'
    ins = [s for s in rnd.inputs if s.enabled]
    ins[0].default_value = 0.0; ins[1].default_value = 6.2832
    Lk.new([s for s in fod.outputs if s.enabled][0], [s for s in ins if s.name == 'ID'][0])
    phase = [s for s in rnd.outputs if s.enabled][0]
    def m(op, a, b=None, c=None):
        n = N.new('ShaderNodeMath'); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: Lk.new(v, n.inputs[i])
        return n.outputs[0]
    u = sp.outputs['Factor']
    arg = m('MULTIPLY_ADD', m('SUBTRACT', m('MULTIPLY', u, gi.outputs['Waves']), m('MULTIPLY', st.outputs['Seconds'], gi.outputs['Hz'])), 2 * math.pi, phase)
    env = m('MULTIPLY', m('POWER', u, gi.outputs['Power']), gi.outputs['Amp'])
    ka = m('MULTIPLY', m('SINE', arg), env)
    kb = m('MULTIPLY', m('SINE', m('MULTIPLY_ADD', arg, 1.37, 1.1)), m('MULTIPLY', env, 0.6))
    va = N.new('ShaderNodeVectorMath'); va.operation = 'SCALE'; Lk.new(gi.outputs['DirA'], va.inputs[0]); Lk.new(ka, va.inputs['Scale'])
    vb = N.new('ShaderNodeVectorMath'); vb.operation = 'SCALE'; Lk.new(gi.outputs['DirB'], vb.inputs[0]); Lk.new(kb, vb.inputs['Scale'])
    vs = N.new('ShaderNodeVectorMath'); vs.operation = 'ADD'; Lk.new(va.outputs[0], vs.inputs[0]); Lk.new(vb.outputs[0], vs.inputs[1])
    setp = N.new('GeometryNodeSetPosition')
    Lk.new(gi.outputs['Geometry'], setp.inputs['Geometry']); Lk.new(vs.outputs[0], setp.inputs['Offset'])
    Lk.new(setp.outputs['Geometry'], go.inputs['Geometry'])
    return ng
WAVE = wave_group()

def hair_material(name, melanin, redness, rough=0.32):
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = m.node_tree; t.nodes.remove(t.nodes['Principled BSDF'])
    h = t.nodes.new('ShaderNodeBsdfHairPrincipled')
    h.parametrization = 'MELANIN'
    h.inputs['Melanin'].default_value = melanin
    h.inputs['Melanin Redness'].default_value = redness
    h.inputs['Roughness'].default_value = rough
    h.inputs['Radial Roughness'].default_value = 0.4
    h.inputs['Random Roughness'].default_value = 0.3
    h.inputs['Random Color'].default_value = 0.15
    t.links.new(h.outputs[0], t.nodes['Material Output'].inputs['Surface'])
    return m

def make_curves(name, strands, radius_root, radius_tip, mat, bone, wave):
    """Hair from world-space strands on the posed horse, carried by a bone from here on."""
    hc = bpy.data.hair_curves.new(name)
    n = len(strands[0])
    hc.add_curves([n] * len(strands))
    pos = np.array([p[:] for s in strands for p in s], dtype=np.float32).ravel()
    hc.attributes['position'].data.foreach_set('vector', pos)
    rad = hc.attributes.get('radius') or hc.attributes.new('radius', 'FLOAT', 'POINT')
    rv = np.tile(np.linspace(radius_root, radius_tip, n), len(strands)).astype(np.float32)
    rad.data.foreach_set('value', rv)
    ob = bpy.data.objects.new(name, hc)
    sc.collection.objects.link(ob)
    hc.materials.append(mat)
    ob.parent = arm; ob.parent_type = 'BONE'; ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = Matrix.Identity(4)
    md = ob.modifiers.new('wave', 'NODES'); md.node_group = WAVE
    for item in WAVE.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name in wave:
            md[item.identifier] = wave[item.name]
    return ob

BACK, UP, SIDE = Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))

# mane: a pulled racing mane on the off side (toward the camera), lifted and streaming in the wind
mane_mat = hair_material('ManeHair', 0.95, 0.6, 0.3)
crest = [(0.0106, 0.0170, 0.0379), (0.0129, 0.0206, 0.0410), (0.0136, 0.0249, 0.0444), (0.0115, 0.0288, 0.0481),
         (0.0112, 0.0324, 0.0517), (0.0108, 0.0365, 0.0553), (0.0097, 0.0405, 0.0589), (0.0081, 0.0447, 0.0619),
         (0.0072, 0.0487, 0.0647), (0.0062, 0.0527, 0.0669), (0.0041, 0.0568, 0.0688), (0.0010, 0.0605, 0.0701), (-0.0015, 0.0648, 0.0709)]
crest_i = [kd.find(P(*c))[1] for c in crest]
crest_p = [EV[i] for i in crest_i]; crest_n = [EN[i] for i in crest_i]; crest_b = [main_bone(i) for i in crest_i]
by_bone = {}
clumps = [dict(t=rng.uniform(0, 1), lift=(rng.uniform(0.1, 0.45) if rng.random() < 0.3 else 0.0), off=Vector((rng.gauss(0, 0.025), 0, rng.gauss(0, 0.03))),
               L=rng.uniform(0.16, 0.28)) for _ in range(110)]
for _ in range(7000):
    cl = rng.choice(clumps)
    t = min(max(cl['t'] + rng.gauss(0, 0.012), 0.0), 1.0)
    x = t * (len(crest) - 1); i = min(int(x), len(crest) - 2); fr_ = x - i
    root = crest_p[i].lerp(crest_p[i + 1], fr_); nrm = crest_n[i].lerp(crest_n[i + 1], fr_).normalized()
    root = root - nrm * 0.008 + Vector((rng.gauss(0, 0.006), rng.gauss(0, 0.006), 0))
    L = cl['L'] * rng.uniform(0.85, 1.1) * (0.6 + 0.4 * math.sin(math.pi * min(1.0, 0.15 + t)))
    lift = cl['lift']
    pts_ = []
    for k in range(9):
        u = k / 8
        d = nrm * (0.12 * u) + SIDE * (0.55 * u) + BACK * (0.55 * u) + UP * ((lift - 0.5) * u * u)
        pts_.append(root + d * L + cl['off'] * u * u + Vector((rng.gauss(0, 0.004), 0, rng.gauss(0, 0.004))) * u)
    by_bone.setdefault(crest_b[i if fr_ < 0.5 else i + 1], []).append(pts_)
for bone, strands in by_bone.items():
    make_curves('Mane_' + bone, strands, 0.0004, 0.00012, mane_mat, bone,
                dict(Amp=0.03, Waves=1.1, Hz=4.5, Power=1.5, DirA=(0, 0, 1), DirB=(1, 0, 0)))

# tail: long black hair from the dock, streaming back
tail_mat = hair_material('TailHair', 0.86, 0.7, 0.28)
tb = arm.pose.bones['tail']
H = arm.matrix_world @ tb.head; T = arm.matrix_world @ tb.tail
dock = (T - H).normalized(); a1 = dock.cross(SIDE).normalized(); a2 = dock.cross(a1).normalized()
tclumps = [dict(off=Vector((rng.gauss(0, 0.1), rng.gauss(0, 0.06), rng.gauss(0, 0.1))), ph=rng.uniform(0, 6.28),
                w=rng.uniform(0.03, 0.07), Lc=rng.uniform(0.75, 1.1)) for _ in range(60)]
tail = []
for _ in range(6500):
    cl = rng.choice(tclumps)
    s_ = rng.uniform(0.0, 1.0) ** 0.8                  # along the dock, which tapers
    a = rng.uniform(0, 2 * math.pi); r = 0.045 * (1.0 - 0.4 * s_) * (0.55 + 0.45 * rng.random())
    root = H.lerp(T, 0.05 + 0.9 * s_) + a1 * (r * math.cos(a)) + a2 * (r * math.sin(a))
    L = cl['Lc'] * rng.uniform(0.7, 1.0) * (0.85 + 0.15 * (1.0 - s_))
    jit = Vector((rng.gauss(0, 0.015), rng.gauss(0, 0.01), rng.gauss(0, 0.015)))
    # leaves the dock along it, then streams back and falls away (a quadratic Bezier)
    p1 = root + dock * (0.3 * L)
    p2 = root + (BACK * 0.85 + UP * -0.3) * L + cl['off'] + jit
    pts_ = []
    for k in range(14):
        u = k / 13
        p = root * (1 - u) ** 2 + p1 * (2 * u * (1 - u)) + p2 * (u * u)
        p += Vector((0.5 * cl['w'] * math.sin(u * 4.0 + cl['ph'] + 1.0), 0, cl['w'] * math.sin(u * 5.5 + cl['ph']))) * u
        pts_.append(p)
    tail.append(pts_)
make_curves('Tail', tail, 0.0004, 0.0001, tail_mat, 'tail',
            dict(Amp=0.1, Waves=0.8, Hz=2.5, Power=1.7, DirA=(0, 0, 1), DirB=(1, 0, 0)))

def add_eyes():
    """Dark, wet eyes in the orbits, placed on the posed head and then carried by the head bone."""
    eye_mat = bpy.data.materials.new('Eye'); eye_mat.use_nodes = True
    eb = eye_mat.node_tree.nodes['Principled BSDF']
    eb.inputs['Base Color'].default_value = (0.012, 0.008, 0.006, 1); eb.inputs['Roughness'].default_value = 0.08
    eb.inputs['Coat Weight'].default_value = 1.0; eb.inputs['Coat Roughness'].default_value = 0.02
    hb = arm.data.bones['head']; pb = arm.pose.bones['head']
    h0 = hb.head_local; fwd = (hb.tail_local - h0).normalized(); Lh = (hb.tail_local - h0).length
    lat = fwd.cross(Vector((0, 0, 1))).normalized(); upv = lat.cross(fwd)
    deform = arm.matrix_world @ pb.matrix @ hb.matrix_local.inverted()
    for name, w in (('EyeR', 0.149 - 0.014), ('EyeL', -0.182 + 0.014)):
        c = deform @ (h0 + fwd * (0.34 * Lh) + lat * w + upv * 0.25) + Vector((0, 0.155, -0.141))   # measured off a close-up
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.026, location=c)
        eye = bpy.context.active_object; eye.name = name
        eye.scale = (0.8, 1.0, 0.85)
        bpy.ops.object.shade_smooth()
        eye.data.materials.append(eye_mat)
        mw = eye.matrix_world.copy()
        eye.parent = arm; eye.parent_type = 'BONE'; eye.parent_bone = 'head'
        bpy.context.view_layer.update(); eye.matrix_world = mw
add_eyes()

sub = horse.modifiers.new('Smooth', 'SUBSURF'); sub.levels = 0; sub.render_levels = 1

# ------------------------------------------------------------------ render
r = sc.render
r.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 2; sc.cycles.transparent_max_bounces = 4
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = RW, RH, 100
r.use_motion_blur = True; r.motion_blur_shutter = 0.3
r.film_transparent = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
r.image_settings.file_format = 'PNG'
for f in FRAMES:
    if os.path.exists(f'{OUT}/h{f:02d}.png'): continue       # finished in an earlier run
    sc.frame_set(f)
    r.filepath = f'{OUT}/h{f:02d}.png'
    bpy.ops.render.render(write_still=True)
    print('rendered frame', f, flush=True)
