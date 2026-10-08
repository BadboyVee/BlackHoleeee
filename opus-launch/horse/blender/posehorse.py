# Apply the gallop (gait.py) to the rigged horse in Blender.
import bpy, math
from mathutils import Vector, Matrix, Quaternion
import numpy as np
import gait

CHAINS = {  # leg -> bones from the proximal joint down, matched to gait joints [prox, elbow, knee, fet, cor, toe]
    'nf': ['nf_humerus', 'nf_forearm', 'nf_cannon', 'nf_pastern', 'nf_hoof'],
    'ff': ['ff_humerus', 'ff_forearm', 'ff_cannon', 'ff_pastern', 'ff_hoof'],
    'nh': ['nh_femur', 'nh_tibia', 'nh_cannon', 'nh_pastern', 'nh_hoof'],
    'fh': ['fh_femur', 'fh_tibia', 'fh_cannon', 'fh_pastern', 'fh_hoof'],
}

def reset(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion()
        pb.location = Vector()
        pb.scale = Vector((1, 1, 1))

def pose_at(arm, phi, head_turn=math.radians(48), neck_nod=0.0):
    """Pose the rig for stride phase phi (0..1)."""
    reset(arm)
    pbs = arm.pose.bones
    bob, pitch = gait.body(phi)
    root = pbs['root']
    # root: rotate about the lateral axis through its head and lift. In the bone's local space
    # the rest orientation matters, so build the armature-space matrix directly.
    rest = root.bone.matrix_local.copy()
    R = Matrix.Rotation(pitch, 4, 'X')
    head = rest.to_translation()
    root.matrix = Matrix.Translation(head + Vector((0, 0, bob))) @ R @ Matrix.Translation(-head) @ rest
    bpy.context.view_layer.update()
    # straighten the scan's head (it is turned ~48 degrees to the far side) and nod with the stride
    nod = neck_nod + math.radians(6) * math.sin(2 * math.pi * (phi - 0.35))
    for name, turn, n in (('neck1', 0.25, 0.4), ('neck2', 0.35, 0.3), ('head', 0.4, 0.3)):
        pb = pbs[name]
        m = pb.matrix.copy()
        piv = m.to_translation()
        Rt = Matrix.Rotation(head_turn * turn, 4, 'Z') @ Matrix.Rotation(-nod * n, 4, 'X')
        pb.matrix = Matrix.Translation(piv) @ Rt @ Matrix.Translation(-piv) @ m
        bpy.context.view_layer.update()
    # legs
    P = gait.pose(phi)
    for leg, bones in CHAINS.items():
        joints = P[leg]
        for i, name in enumerate(bones):
            pb = pbs[name]
            a = Vector((0, joints[i][0], joints[i][1])); b = Vector((0, joints[i + 1][0], joints[i + 1][1]))
            want = (b - a).normalized()
            cur = pb.matrix.copy()
            have = (cur.to_3x3() @ Vector((0, 1, 0))).normalized()
            # keep the joint's lateral position: rotate in the side plane only
            want = Vector((0, want.y, want.z)).normalized()
            have_p = Vector((0, have.y, have.z)).normalized()
            q = have_p.rotation_difference(want)
            piv = cur.to_translation()
            pb.matrix = Matrix.Translation(piv) @ q.to_matrix().to_4x4() @ Matrix.Translation(-piv) @ cur
            bpy.context.view_layer.update()

def key_all(arm, frame):
    for pb in arm.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('location', frame=frame)
