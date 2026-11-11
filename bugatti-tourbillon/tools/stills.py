"""Review stills from the film scene (hero lighting) + blueprint overlays + numeric checks."""
import sys, os, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bpy, numpy as np
from mathutils import Vector
from tb import util, preview, compare, animation, spec
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "renders", "film.blend"))
scene = bpy.context.scene
for m in list(scene.timeline_markers):
    scene.timeline_markers.remove(m)
OUT = os.path.join(ROOT, "renders", "review"); os.makedirs(OUT, exist_ok=True)
res = (960, 540)
animation.setup_render(scene, res, 28)
scene.render.threads_mode = 'FIXED'; scene.render.threads = 4

def shot(name, frame, pos, tgt, lens):
    scene.frame_set(frame)
    return preview.render_view(scene, os.path.join(OUT, name + ".png"), pos, tgt, lens)

if "check" in sys.argv:
    root = bpy.data.objects[spec.ROOT]
    print("root children:", sorted(o.name for o in root.children)[:80])
    scene.frame_set(760)
    bpy.context.view_layer.update()
    for sn in "LR":
        o = bpy.data.objects["BODY_Door_%s_Skin" % sn]
        mn, mx = util.bounds(o)
        print("door", sn, "open bounds", np.round(mn, 2), np.round(mx, 2))
    ints = [o.name for o in bpy.data.objects if o.name.startswith("INT_") and (o.parent is None or not o.parent.name.startswith("INT_"))]
    print("INT top-level:", ints[:60])
ext = [("front34", 600, (5.2, 4.6, 2.3), (0.3, 0, 0.45), 50), ("front34_low", 600, (6.0, 3.0, 1.1), (0.4, 0, 0.5), 55),
       ("side", 600, (0.0, 9.5, 0.75), (0.0, 0, 0.6), 85), ("rear34", 600, (-5.6, 4.4, 1.9), (-0.15, 0, 0.52), 60),
       ("front", 600, (9.0, 0, 0.75), (0, 0, 0.58), 85), ("rear", 600, (-9.0, 0, 0.8), (0, 0, 0.58), 85),
       ("high34", 600, (4.6, 3.6, 3.6), (0, 0, 0.45), 55), ("rear_low", 600, (-5.2, -2.2, 0.7), (-1.2, 0, 0.55), 55),
       ("doors_open", 760, (5.6, 4.6, 2.0), (0.2, 0, 0.7), 45)]
inte = [("int_forward", 800, (-0.45, 0, 1.05), (0.9, 0, 0.55), 18), ("int_through_door", 800, (-0.35, 1.3, 1.25), (0.6, 0.2, 0.55), 24),
        ("int_passenger", 800, (0.0, -0.9, 0.85), (0.45, 0.3, 0.6), 24), ("int_cluster", 800, (0.08, 0.375, 0.86), (0.55, 0.375, 0.75), 50)]
if "ext" in sys.argv:
    files = [shot(*s) for s in ext]
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet.py"), os.path.join(OUT, "sheet_exterior.png"), "3", "640"] + files)
if "int" in sys.argv:
    files = [shot(*s) for s in inte]
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet.py"), os.path.join(OUT, "sheet_interior.png"), "2", "800"] + files)
if "cmp" in sys.argv:
    scene.frame_set(600)
    st = compare.overlay(scene, OUT, hide=("LGT_", "CAM_"))
    print("blueprint stats", {k: {a: round(b, 3) for a, b in v.items()} for k, v in st.items()})
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet.py"), os.path.join(OUT, "sheet_blueprint.png"), "2", "860"] +
                   [os.path.join(OUT, "cmp_%s.png" % v) for v in ("side", "top", "front", "rear")])
