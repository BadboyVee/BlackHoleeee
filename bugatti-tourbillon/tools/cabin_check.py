"""Render the film's cabin shots with the full car in the showroom, in the film's cabin state.

    python3 tools/cabin_check.py [out_dir] [--res 640x360] [--samples 16] [--threads 2]

Builds the whole car (body + details + wheels + interior + rig) and the showroom, opens both
doors, turns the cabin lights on, applies the 'cabin' lighting mood, and renders the midpoint
of each cabin camera move from tb/animation.py plus a reference-like passenger view.
Writes <out_dir>/sheet.png (2 x 2).
"""
import sys, os, time, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bpy
import build
from tb import environment, preview

a = sys.argv[1:]
out = a[0] if a and not a[0].startswith("--") else os.path.join(ROOT, "renders", "dev", "cabin")
opt = lambda n, d: a[a.index(n) + 1] if n in a else d
res = tuple(int(v) for v in opt("--res", "640x360").split("x"))
os.makedirs(out, exist_ok=True)

car = build.assemble(verbose=True)
scene = car["scene"]
env = environment.build()
environment.apply_mood(env, "cabin")
ctrl = car["rig"]["ctrl"]
for k, v in (("door_L", 1.0), ("door_R", 1.0), ("interior_lights", 1.0), ("headlights", 1.0), ("steer", 0.0)):
    ctrl[k] = v
ctrl.update_tag()
bpy.context.view_layer.update()
preview.setup_cycles(scene, samples=int(opt("--samples", "16")), res=res, threads=int(opt("--threads", "2")))

VIEWS = [  # name, camera, target, lens  (film shots s10, s11, s09 at mid-move)
    ("film_s10_wheel", (0.09, 1.44, 1.11), (0.55, 0.37, 0.74), 28),
    ("film_s11_console", (-0.355, 0.03, 0.98), (0.75, 0.0, 0.62), 20),
    ("film_s09_doors", (6.75, 2.05, 1.525), (0.3, 0.0, 0.95), 40),
    ("ref_B3_passenger", (0.0, -0.9, 0.85), (0.45, 0.3, 0.6), 24),
]
files = []
for name, pos, tgt, lens in VIEWS:
    t = time.time()
    files.append(preview.render_view(scene, os.path.join(out, name + ".png"), pos, tgt, lens))
    print("%-18s %.1f s" % (name, time.time() - t), flush=True)
subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet.py"), os.path.join(out, "sheet.png"), "2", "640"] + files)
print("sheet:", os.path.join(out, "sheet.png"))
