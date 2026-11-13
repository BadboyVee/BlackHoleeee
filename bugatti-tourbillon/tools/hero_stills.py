"""Final stills for the README:  python3 tools/hero_stills.py [--res 1600x900] [--samples 64] [--only name,...]

Builds the car and the showroom fresh (no animation), sets the controls and lighting mood for
each shot, renders with Cycles and writes JPEGs to renders/stills/.
"""
import sys, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bpy
from PIL import Image
import build
from tb import environment, preview

a = sys.argv[1:]
opt = lambda n, d: a[a.index(n) + 1] if n in a else d
res = tuple(int(v) for v in opt("--res", "1600x900").split("x"))
only = set(opt("--only", "").split(",")) - {""}
OUT = os.path.join(ROOT, "renders", "stills")
os.makedirs(OUT, exist_ok=True)

PARKED = dict(door_L=0, door_R=0, headlights=1, taillights=1, interior_lights=0, wing=0, steer=0.42)
OPEN = dict(door_L=1, door_R=1, headlights=1, taillights=1, interior_lights=1, wing=0, steer=0.0)
SHOTS = [  # name, mood, controls, camera, target, lens
    ("01_front34", "hero", PARKED, (5.4, 3.3, 0.95), (0.35, 0.0, 0.50), 55),
    ("02_rear34", "hero", dict(PARKED, wing=1), (-5.4, 3.7, 1.35), (-0.30, 0.0, 0.55), 55),
    ("03_side", "hero", dict(PARKED, steer=0.0), (0.0, 9.2, 0.70), (0.0, 0.0, 0.58), 85),
    ("04_doors_open", "hero", OPEN, (5.6, 4.0, 1.60), (0.20, 0.0, 0.75), 45),
    ("05_cabin", "cabin", OPEN, (-0.40, 0.0, 1.00), (0.75, 0.0, 0.62), 20),
    ("06_cluster", "cabin", OPEN, (0.12, 0.30, 0.90), (0.52, 0.375, 0.74), 45),
]

car = build.assemble(verbose=True)
scene = car["scene"]
env = environment.build()
ctrl = car["rig"]["ctrl"]
preview.setup_cycles(scene, samples=int(opt("--samples", "64")), res=res)
scene.cycles.adaptive_threshold = 0.02
for name, mood, controls, pos, tgt, lens in SHOTS:
    if only and name not in only:
        continue
    environment.apply_mood(env, mood)
    for k, v in controls.items():
        ctrl[k] = float(v)
    ctrl.update_tag()
    bpy.context.view_layer.update()
    t = time.time()
    png = preview.render_view(scene, os.path.join(OUT, name + ".png"), pos, tgt, lens)
    Image.open(png).convert("RGB").save(os.path.join(OUT, name + ".jpg"), quality=90, optimize=True)
    os.remove(png)
    print("%-14s %.0f s" % (name, time.time() - t), flush=True)
