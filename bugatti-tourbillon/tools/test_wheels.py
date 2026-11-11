"""Self-test for tb/wheels.py: builds the four wheels in a fresh scene and renders previews.

    python3 tools/test_wheels.py                 # all views
    python3 tools/test_wheels.py front_face tread   # only the named views
    python3 tools/test_wheels.py --none          # build + triangle count only

Renders go to renders/dev/wheels/.
"""
import os
import sys
import time

P = "/home/user/BlackHoleeee/bugatti-tourbillon"
sys.path.insert(0, P)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from tb import spec, util, preview, wheels  # noqa: E402

OUT = os.path.join(P, "renders", "dev", "wheels")
RES = (800, 450)


def views():
    fl = Vector((spec.WHEELS["FL"]["x"], spec.WHEELS["FL"]["y"], spec.WHEELS["FL"]["z"]))
    rl = Vector((spec.WHEELS["RL"]["x"], spec.WHEELS["RL"]["y"], spec.WHEELS["RL"]["z"]))
    return {
        # name: (camera position, target, lens)
        "front_face": (fl + Vector((0.0, 2.6, 0.0)), fl, 105),
        "front_34": (fl + Vector((0.95, 1.20, 0.22)), fl + Vector((0.0, 0.05, -0.01)), 78),
        "rear_34": (rl + Vector((-1.00, 1.25, 0.26)), rl + Vector((0.0, 0.05, -0.01)), 78),
        "tread": (fl + Vector((0.62, 0.36, 0.36)), fl + Vector((0.20, 0.07, 0.24)), 70),
        "all_four": (Vector((4.9, 3.9, 3.1)), Vector((0.0, 0.0, 0.25)), 52),
    }


def main(argv):
    t0 = time.time()
    scene = util.reset_scene()
    roots = wheels.build()
    bpy.context.view_layer.update()
    col = bpy.data.collections[spec.COLLECTIONS["wheels"]]
    objs = [o for o in col.objects if o.type == 'MESH']
    print("build time %.1f s" % (time.time() - t0))
    print("roots:", {k: v.name for k, v in roots.items()})
    for part in ("Rim", "Tyre", "Disc", "Caliper", "Carrier", "Cap", "Lugs"):
        print("  %-8s FL %6d   RL %6d" % (part, util.tri_count([bpy.data.objects["WHL_FL_" + part]]),
                                         util.tri_count([bpy.data.objects["WHL_RL_" + part]])))
    print("TRIANGLES (all four wheels): %d" % util.tri_count(objs))
    lo, hi = util.bounds(objs)
    print("bounds min", [round(float(v), 3) for v in lo], "max", [round(float(v), 3) for v in hi])
    if "--none" in argv:
        return
    preview.quick_studio(scene)
    preview.setup_cycles(scene, samples=24, res=RES, threads=2)
    os.makedirs(OUT, exist_ok=True)
    V = views()
    names = [a for a in argv if a in V] or list(V)
    for name in names:
        pos, tgt, lens = V[name]
        t1 = time.time()
        preview.render_view(scene, os.path.join(OUT, name + ".png"), tuple(pos), tuple(tgt), lens)
        print("rendered %s in %.1f s" % (name, time.time() - t1))


if __name__ == "__main__":
    main(sys.argv[1:])
