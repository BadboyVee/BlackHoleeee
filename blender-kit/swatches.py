"""Render a contact sheet of cached texture sets: python3 swatches.py out.png tex1 tex2 ..."""
import sys, math
import bpy
import kit
out, names = sys.argv[1], sys.argv[2:]
kit.reset()
cols = 7
for i, n in enumerate(names):
    mb = kit.MB()
    x, y = (i % cols) * 2.2, -(i // cols) * 2.2
    mb.box(x, y, 0, x + 2, y + 2, 0.1, kit.mat_pbr(n, n, size=2.0))
    mb.build(n)
rows = (len(names) - 1) // cols + 1
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0)
d = bpy.data.cameras.new("c"); d.type = "ORTHO"; d.ortho_scale = cols * 2.2
cam = bpy.data.objects.new("c", d); bpy.context.scene.collection.objects.link(cam)
cam.location = (cols * 1.1 - 0.1, -(rows - 1) * 1.1 + 1, 10)
kit.render_setup(cols * 220, rows * 220 + 20, samples=24)
kit.render(cam, out)
