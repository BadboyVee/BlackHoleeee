"""Self-test for tb/interior.py: builds only the cabin in a fresh scene and renders it.

    python3 tools/test_interior.py                      # all six views, 800x450, 24 samples
    python3 tools/test_interior.py forward cluster      # only the named views
    python3 tools/test_interior.py --res 960x540 --samples 32
    python3 tools/test_interior.py --no-render          # build + triangle count + envelope check

Renders go to renders/dev/interior/<view>.png.  Preview limits of the brief are enforced
(<= 960x540, <= 32 samples, 2 threads).
"""
import sys, os, time, math
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
import bpy
from mathutils import Vector
from tb import spec, util, materials, preview, interior

OUT = os.path.join(P, "renders", "dev", "interior")

_c = Vector(spec.CABIN["steering_centre"])
_rake = math.radians(spec.CABIN["steering_rake_deg"])
_zl = Vector((-math.cos(_rake), 0.0, math.sin(_rake)))      # column axis, towards the driver
_yl = Vector((math.sin(_rake), 0.0, math.cos(_rake)))       # 12 o'clock of the wheel

VIEWS = {
    # name: (camera position, target, lens mm)
    "forward": ((-0.45, 0.0, 1.05), (0.9, 0.0, 0.55), 18),            # like ref B1
    "from_passenger": ((0.0, -0.9, 0.85), (0.45, 0.3, 0.6), 24),      # like ref B3
    "through_door": ((-0.35, 1.3, 1.25), (0.6, 0.2, 0.55), 24),       # like ref B4
    "overview": ((-1.6, 1.9, 2.4), (0.2, 0.0, 0.5), 35),
    "cluster": (tuple(_c + _zl * 0.36 + _yl * 0.035 + Vector((0, 0.03, 0))), tuple(_c + _yl * 0.022), 50),
    "console": ((0.20, -0.17, 0.97), (0.51, 0.0, 0.615), 45),
}


def main(argv):
    res, samples, render = (800, 450), 24, True
    names = []
    it = iter(argv)
    for a in it:
        if a == "--res":
            res = tuple(int(v) for v in next(it).lower().split("x"))
        elif a == "--samples":
            samples = int(next(it))
        elif a == "--no-render":
            render = False
        elif a in VIEWS:
            names.append(a)
        else:
            raise SystemExit("unknown argument %r (views: %s)" % (a, ", ".join(VIEWS)))
    res = (min(res[0], 960), min(res[1], 540))
    samples = min(samples, 32)
    names = names or list(VIEWS)

    scene = util.reset_scene()
    t0 = time.time()
    parts = interior.build()
    print("build time: %.1f s" % (time.time() - t0))
    col = bpy.data.collections[spec.COLLECTIONS["interior"]]
    objs = list(col.all_objects)
    for k, v in parts.items():
        print("  %-16s -> %s" % (k, [o.name for o in v] if isinstance(v, list) else v.name))
    bad = [o.name for o in objs if not o.name.startswith("INT_")]
    nomat = [o.name for o in objs if o.type == 'MESH' and (not o.data.materials or None in list(o.data.materials))]
    print("objects: %d   not INT_-prefixed: %s   without material: %s" % (len(objs), bad, nomat))
    interior.envelope_report(objs, verbose=True)
    print("triangles (evaluated): %d" % util.tri_count(objs))
    if not render:
        return

    preview.setup_cycles(scene, samples=samples, res=res, threads=2)
    preview.quick_studio(scene, floor=True)
    # test-only fill light inside the cabin so the footwells and console read
    l = bpy.data.lights.new("TEST_CabinFill", 'AREA')
    l.shape = 'RECTANGLE'
    l.size, l.size_y = 0.9, 0.6
    l.energy = 55
    lo = bpy.data.objects.new("TEST_CabinFill", l)
    scene.collection.objects.link(lo)
    lo.location = (0.10, 0.0, 1.12)
    util.look_at(lo, (0.35, 0.0, 0.3))
    os.makedirs(OUT, exist_ok=True)
    for n in names:
        pos, tgt, lens = VIEWS[n]
        t0 = time.time()
        preview.render_view(scene, os.path.join(OUT, n + ".png"), pos, tgt, lens)
        print("rendered %s in %.1f s" % (n, time.time() - t0))


if __name__ == "__main__":
    main(sys.argv[1:])
