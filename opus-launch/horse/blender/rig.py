# Build a rigged horse from the Cyberware horse scan and save horse_rig.blend.
# Needs the scan next to it: https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data/horse.obj
# Run with Blender's Python module (pip install bpy==4.5.*):  python rig.py
import bpy, math
from mathutils import Vector

S = 14.2            # scan units -> metres (withers ~1.58 m)
MID_X = 0.015       # the scan's midline
def P(x, y, z):
    return Vector(((x - MID_X) * S, y * S, (z + 0.0765) * S))

# Joints, in scan coordinates, read off the mesh (leg centre lines, back line, neck)
J = {
    # spine
    'root_h': (0.015, -0.005, 0.012), 'root_t': (0.015, 0.012, 0.012),
    'pelvis_t': (0.015, -0.066, 0.022),
    'tail_h': (0.015, -0.074, 0.026), 'tail_t': (0.015, -0.086, 0.012),
    'chest_t': (0.015, 0.034, 0.018),
    'neck1_t': (0.012, 0.050, 0.038),
    'neck2_t': (0.004, 0.064, 0.057),
    'head_t': (-0.030, 0.090, 0.040),
    # near fore (x ~ +0.03)
    'nf_scap': (0.028, 0.020, 0.030), 'nf_shoulder': (0.030, 0.040, 0.000), 'nf_elbow': (0.026, 0.0225, -0.021),
    'nf_knee': (0.0277, 0.0179, -0.0405), 'nf_fet': (0.0302, 0.0122, -0.0605), 'nf_cor': (0.0307, 0.0147, -0.0690), 'nf_toe': (0.0300, 0.0220, -0.0765),
    # far fore (x ~ 0.0)
    'ff_scap': (0.002, 0.020, 0.030), 'ff_shoulder': (0.000, 0.040, 0.000), 'ff_elbow': (-0.0006, 0.0290, -0.0225),
    'ff_knee': (-0.0019, 0.0293, -0.0405), 'ff_fet': (-0.0021, 0.0330, -0.0605), 'ff_cor': (-0.0029, 0.0378, -0.0690), 'ff_toe': (-0.0036, 0.0460, -0.0765),
    # near hind
    'nh_hip': (0.030, -0.058, 0.012), 'nh_stifle': (0.033, -0.047, -0.010), 'nh_hock': (0.0325, -0.0625, -0.035),
    'nh_fet': (0.0333, -0.0680, -0.0595), 'nh_cor': (0.0330, -0.0655, -0.0690), 'nh_toe': (0.0330, -0.0565, -0.0765),
    # far hind
    'fh_hip': (0.000, -0.058, 0.012), 'fh_stifle': (-0.002, -0.060, -0.010), 'fh_hock': (-0.0021, -0.0800, -0.035),
    'fh_fet': (-0.0023, -0.0864, -0.0590), 'fh_cor': (-0.0030, -0.0845, -0.0690), 'fh_toe': (-0.0035, -0.0775, -0.0765),
}

BONES = [  # name, head, tail, parent, connected
    ('root', 'root_h', 'root_t', None, False),
    ('pelvis', 'root_h', 'pelvis_t', 'root', False),
    ('tail', 'tail_h', 'tail_t', 'pelvis', False),
    ('chest', 'root_h', 'chest_t', 'root', False),
    ('neck1', 'chest_t', 'neck1_t', 'chest', True),
    ('neck2', 'neck1_t', 'neck2_t', 'neck1', True),
    ('head', 'neck2_t', 'head_t', 'neck2', True),
]
for side in ('n', 'f'):
    fo, hi = side + 'f_', side + 'h_'
    BONES += [
        (fo + 'scapula', fo + 'scap', fo + 'shoulder', 'chest', False),
        (fo + 'humerus', fo + 'shoulder', fo + 'elbow', fo + 'scapula', True),
        (fo + 'forearm', fo + 'elbow', fo + 'knee', fo + 'humerus', True),
        (fo + 'cannon', fo + 'knee', fo + 'fet', fo + 'forearm', True),
        (fo + 'pastern', fo + 'fet', fo + 'cor', fo + 'cannon', True),
        (fo + 'hoof', fo + 'cor', fo + 'toe', fo + 'pastern', True),
        (hi + 'femur', hi + 'hip', hi + 'stifle', 'pelvis', False),
        (hi + 'tibia', hi + 'stifle', hi + 'hock', hi + 'femur', True),
        (hi + 'cannon', hi + 'hock', hi + 'fet', hi + 'tibia', True),
        (hi + 'pastern', hi + 'fet', hi + 'cor', hi + 'cannon', True),
        (hi + 'hoof', hi + 'cor', hi + 'toe', hi + 'pastern', True),
    ]

def build():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    bpy.ops.wm.obj_import(filepath='horse.obj', forward_axis='Y', up_axis='Z')
    horse = bpy.context.selected_objects[0]
    horse.name = 'Horse'
    horse.rotation_euler = (0, 0, 0)
    me = horse.data
    for v in me.vertices:
        v.co = P(*v.co)
    me.update()
    for p in me.polygons:
        p.use_smooth = True

    arm_data = bpy.data.armatures.new('HorseRig')
    arm = bpy.data.objects.new('HorseRig', arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    for name, h, t, parent, conn in BONES:
        b = eb.new(name)
        b.head = P(*J[h]); b.tail = P(*J[t])
        if parent:
            b.parent = eb[parent]; b.use_connect = conn
    bpy.ops.object.mode_set(mode='OBJECT')

    # skin: bone-heat weights
    bpy.ops.object.select_all(action='DESELECT')
    horse.select_set(True); arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    print('groups', len(horse.vertex_groups))
    bpy.ops.wm.save_as_mainfile(filepath='horse_rig.blend')
    return horse, arm

if __name__ == '__main__':
    build()
    print('saved horse_rig.blend')
