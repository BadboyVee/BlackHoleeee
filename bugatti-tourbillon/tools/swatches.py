"""Smoke test: one sphere per shared material, rendered as a contact sheet."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy, bmesh
from tb import util, materials, preview
scene = util.reset_scene()
names = materials.names()
cols = 9
rows = (len(names) + cols - 1) // cols
for i, n in enumerate(names):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.16)
    o = util.bmesh_object("S_" + n, bm, material=materials.get(n))
    o.location = ((i % cols) * 0.42, 0, 0.16 + (rows - 1 - i // cols) * 0.42)
rows = (len(names) + cols - 1) // cols
preview.quick_studio(scene, floor=False)
preview.setup_cycles(scene, samples=32, res=(1440, int(1440 * rows / cols) + 20), threads=4)
cx, cz = (cols - 1) * 0.21, rows * 0.21
preview.render_view(scene, sys.argv[-1], (cx, -6, cz), (cx, 0, cz), ortho_scale=cols * 0.44)
print("materials:", len(names), names)
