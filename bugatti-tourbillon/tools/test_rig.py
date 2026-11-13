"""Exercise every control on TB_CTRL and check that it moves or switches what it should.

    python3 tools/test_rig.py            (builds the full car, no rendering; exit code 1 on failure)
"""
import sys, os, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bpy
import numpy as np
import build
from tb import util, materials

car = build.assemble(verbose=True)
ctrl = car["rig"]["ctrl"]
O = bpy.data.objects
results = []


def settle():
    ctrl.update_tag()
    bpy.context.view_layer.update()
    bpy.context.evaluated_depsgraph_get().update()


def set_(**kw):
    for k, v in kw.items():
        ctrl[k] = float(v)
    settle()


def world_bounds(name):
    mn, mx = util.bounds(O[name])
    return np.array(mn), np.array(mx)


def strength(mat_name):
    m = bpy.data.materials[materials.PREFIX + mat_name]
    return m.node_tree.nodes["Strength"].outputs[0].default_value


def check(name, ok, detail):
    results.append((name, bool(ok)))
    print("%-4s %-34s %s" % ("PASS" if ok else "FAIL", name, detail))


set_(door_L=0, door_R=0, headlights=0, taillights=0, interior_lights=0, wing=0, steer=0, wheel_spin=0)

# ---- doors: closed -> open lifts each door up and out, symmetric left/right
closed = {s: world_bounds("BODY_Door_%s_Skin" % s) for s in "LR"}
set_(door_L=1, door_R=1)
opened = {s: world_bounds("BODY_Door_%s_Skin" % s) for s in "LR"}
for s, sign in (("L", 1), ("R", -1)):
    lift = opened[s][1][2] - closed[s][1][2]
    out = sign * ((opened[s][0][1] + opened[s][1][1]) - (closed[s][0][1] + closed[s][1][1])) / 2
    check("door_%s opens up and out" % s, lift > 0.5 and out > 0.3, "top +%.2f m, centre outward +%.2f m" % (lift, out))
check("doors open symmetrically", abs(opened["L"][1][2] - opened["R"][1][2]) < 0.01,
      "open top z L %.3f / R %.3f" % (opened["L"][1][2], opened["R"][1][2]))
set_(door_L=0, door_R=0)
back = world_bounds("BODY_Door_L_Skin")
check("door closes back to rest", np.abs(back[0] - closed["L"][0]).max() < 1e-4, "max error %.1e m" % np.abs(back[0] - closed["L"][0]).max())

# ---- lights
for prop, mats, lamps in (("headlights", ["emit_headlight", "emit_drl"], ["LGT_HeadSpot_L", "LGT_HeadSpot_R"]),
                          ("taillights", ["emit_tail"], []),
                          ("interior_lights", ["emit_interior", "emit_dial", "emit_screen"], ["LGT_Cabin"])):
    off = [strength(m) for m in mats] + [O[l].data.energy for l in lamps]
    set_(**{prop: 1})
    on = [strength(m) for m in mats] + [O[l].data.energy for l in lamps]
    set_(**{prop: 0})
    check("%s switch" % prop, all(a == 0 for a in off) and all(b > 0 for b in on),
          "off %s -> on %s" % ([round(v, 1) for v in off], [round(v, 1) for v in on]))

# ---- wing
z0 = O["AERO_WingPivot"].matrix_world.translation.z
set_(wing=1)
z1 = O["AERO_WingPivot"].matrix_world.translation.z
tilt = O["AERO_WingPivot"].rotation_euler.y
set_(wing=0)
check("wing rises and tilts", z1 - z0 > 0.1 and tilt > 0.2, "+%.2f m, %.0f deg" % (z1 - z0, math.degrees(tilt)))

# ---- steering
set_(steer=1)
fl = O["WHL_FL"].rotation_euler.z
fr = O["WHL_FR"].rotation_euler.z
rl = O["WHL_RL"].rotation_euler.z
rim = O["INT_SteeringRim"].rotation_euler.z if "INT_SteeringRim" in O else None
set_(steer=0)
check("steer turns front wheels only", abs(fl) > 0.3 and abs(fl - fr) < 1e-6 and abs(rl) < 1e-6,
      "FL %.0f deg, FR %.0f deg, RL %.0f deg" % tuple(math.degrees(v) for v in (fl, fr, rl)))
if rim is not None:
    check("steer turns the steering rim", abs(rim) > 1.0, "rim %.0f deg at full lock" % math.degrees(rim))

# ---- wheel spin: all four roll the same way (forward) for a positive value
set_(wheel_spin=1.0)
spins = {}
for k in ("FL", "FR", "RL", "RR"):
    sp = O["WHL_%s_Spin" % k]
    # forward roll = the top of the wheel moves toward +X: check where the local up axis went
    top = sp.matrix_world.to_3x3() @ __import__("mathutils").Vector((0, 0, 1))
    spins[k] = top.x
set_(wheel_spin=0)
same = all(np.sign(v) == np.sign(spins["FL"]) and abs(v) > 0.5 for v in spins.values())
check("wheel_spin rolls all wheels alike", same, " ".join("%s %+.2f" % kv for kv in spins.items()))

n_fail = sum(1 for _, ok in results if not ok)
print("\n%d checks, %d failed" % (len(results), n_fail))
sys.exit(1 if n_fail else 0)
