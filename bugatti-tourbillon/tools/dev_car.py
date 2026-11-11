"""Full-car dev render: python3 tools/dev_car.py [views...] [doors] [lights] [wing] [cmp]"""
import sys, os, time, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bpy
import build
from tb import util, preview, compare
OUT = os.path.join(ROOT, "renders", "dev", "car")
args = sys.argv[1:]
car = build.assemble()
scene = car["scene"]; ctrl = car["rig"]["ctrl"]
if "doors" in args: ctrl["door_L"] = 1.0; ctrl["door_R"] = 1.0
if "lights" in args: ctrl["interior_lights"] = 1.0
if "wing" in args: ctrl["wing"] = 1.0
if "steer" in args: ctrl["steer"] = 0.6
ctrl.update_tag(); bpy.context.view_layer.update()
if "cmp" in args:
    print("stats", compare.overlay(scene, OUT, hide=("LGT_",)))
views = [a for a in args if a in preview.VIEWS]
if views:
    preview.quick_studio(scene)
    preview.setup_cycles(scene, samples=24, res=(800, 450), threads=4)
    t = time.time()
    files = preview.render_views(scene, OUT, names=views, prefix="c_")
    print("render s %.1f" % (time.time() - t))
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet.py"), os.path.join(OUT, "sheet.png"), "2", "800"] + files)
