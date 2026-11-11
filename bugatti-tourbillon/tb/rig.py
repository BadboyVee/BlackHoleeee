"""Rig: one control object drives every working function.

    TB_CTRL["door_L"], ["door_R"]   0..1   dihedral doors (closed..open)
    TB_CTRL["headlights"]           0..1   LED modules, DRL and the two spot lamps
    TB_CTRL["taillights"]           0..1   rear light bar
    TB_CTRL["interior_lights"]      0..1   ambient strips, dials, cabin light
    TB_CTRL["wing"]                 0..1   active rear wing / airbrake
    TB_CTRL["steer"]               -1..1   front wheels + steering rim
    TB_CTRL["wheel_spin"]           radians, rolling of all four wheels

All drivers use simple expressions, so they evaluate without enabling Python auto-run.
"""
import math
import bpy
from . import spec, util, materials

PROPS = dict(door_L=0.0, door_R=0.0, headlights=1.0, taillights=1.0, interior_lights=0.0,
             wing=0.0, steer=0.0, wheel_spin=0.0)


def _drive(id_block, path, index, ctrl, prop, expr):
    fc = id_block.driver_add(path, index) if index is not None else id_block.driver_add(path)
    d = fc.driver
    d.type = 'SCRIPTED'
    v = d.variables.new()
    v.name = "v"
    v.type = 'SINGLE_PROP'
    v.targets[0].id = ctrl
    v.targets[0].data_path = '["%s"]' % prop
    d.expression = expr
    return fc


def build(body_parts, detail_parts=None, wheel_roots=None, interior_parts=None):
    col = util.get_collection(spec.COLLECTIONS["rig"])
    root = util.empty(spec.ROOT, (0, 0, 0), collection=col, size=0.5, kind='ARROWS')
    ctrl = util.empty(spec.CTRL, (0, 0, 1.6), collection=col, size=0.25, kind='SPHERE')
    for k, v in PROPS.items():
        ctrl[k] = float(v)
        lo, hi = (-1.0, 1.0) if k == "steer" else ((-1e4, 1e4) if k == "wheel_spin" else (0.0, 1.0))
        ctrl.id_properties_ui(k).update(min=lo, max=hi, soft_min=lo, soft_max=hi)
    util.parent(ctrl, root)

    # ---- doors
    ang = math.radians(spec.DOOR["open_angle_deg"])
    for s, sn in ((+1, "L"), (-1, "R")):
        h = body_parts["door_hinge_" + sn]
        if detail_parts:
            for o in detail_parts["door_children"][sn]:
                util.parent(o, h)
        ax = h["axis"]
        h.rotation_mode = 'AXIS_ANGLE'
        h.rotation_axis_angle = (0.0, ax[0], ax[1], ax[2])
        _drive(h, "rotation_axis_angle", 0, ctrl, "door_" + sn, "%.5f*v" % (-s * ang))

    # ---- lights: emissive materials
    for prop, names in materials.EMISSIVE_GROUPS.items():
        if prop not in PROPS:
            continue
        for n in names:
            m = bpy.data.materials.get(materials.PREFIX + n)
            if m is None:
                continue
            on = float(m.get("strength_on", 1.0))
            _drive(m.node_tree, 'nodes["Strength"].outputs[0].default_value', None, ctrl, prop, "%.4f*v" % on)
    # ---- lights: real lamps
    if detail_parts:
        for lo in detail_parts["head_spots"].values():
            _drive(lo.data, "energy", None, ctrl, "headlights", "%.3f*v" % lo["base_energy"])
        cab = detail_parts["cabin_light"]
        _drive(cab.data, "energy", None, ctrl, "interior_lights", "%.3f*v" % cab["base_energy"])
        piv = detail_parts["wing_pivot"]
        _drive(piv, "location", 2, ctrl, "wing", "%.4f+0.15*v" % piv["base_z"])
        _drive(piv, "rotation_euler", 1, ctrl, "wing", "0.38*v")

    # ---- wheels + steering
    if wheel_roots:
        bpy.context.view_layer.update()
        for key, wr in wheel_roots.items():
            spin = bpy.data.objects.get("WHL_%s_Spin" % key)
            if spin is not None:
                sign = 1.0 if (spin.matrix_world.to_3x3().col[1].y >= 0) else -1.0
                _drive(spin, "rotation_euler", 1, ctrl, "wheel_spin", "%.1f*v" % sign)
            if spec.WHEELS[key]["front"]:
                _drive(wr, "rotation_euler", 2, ctrl, "steer", "0.45*v")
    if interior_parts and interior_parts.get("steering_rim") is not None:
        _drive(interior_parts["steering_rim"], "rotation_euler", 2, ctrl, "steer", "2.4*v")

    # ---- everything hangs off the root
    env = spec.COLLECTIONS["env"]
    for o in bpy.context.scene.objects:
        if o.parent is None and o not in (root,) and not o.name.startswith(("ENV_", "PV_", "CAM_")) \
                and not any(c.name == env for c in o.users_collection):
            util.parent(o, root)
    return dict(root=root, ctrl=ctrl)
