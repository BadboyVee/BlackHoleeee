"""Dev loop for the body: build, overlay on blueprint, quick renders -> one contact sheet."""
import sys, os, time, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bpy, numpy as np
from tb import util, materials, preview, surface, compare, body
OUT = os.path.join(ROOT, "renders", "dev", "body")
args = sys.argv[1:]
scene = util.reset_scene()
t = time.time()
parts = body.build()
print("build s %.1f" % (time.time() - t), "tris", util.tri_count())
if "door" in args:
    import math
    from mathutils import Matrix, Vector
    for sn in ("L",):
        h = parts["door_hinge_" + sn]
        h.rotation_mode = 'AXIS_ANGLE'
        ax = h["axis"]; h.rotation_axis_angle = (math.radians(-60), ax[0], ax[1], ax[2])
if "cmp" in args:
    print("stats", compare.overlay(scene, OUT))
views = [a for a in args if a in preview.VIEWS]
if views:
    preview.quick_studio(scene)
    preview.setup_cycles(scene, samples=20, res=(800, 450), threads=3)
    t = time.time()
    files = preview.render_views(scene, OUT, names=views, prefix="b_")
    print("render s %.1f" % (time.time() - t))
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet.py"), os.path.join(OUT, "sheet.png"),
                    "2", "800"] + files)
if "save" in args:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "renders", "dev", "body", "body.blend"))
