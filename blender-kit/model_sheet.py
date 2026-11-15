"""Contact sheet of cached models: python3 model_sheet.py out.png name1 name2 ..."""
import sys, math
import bpy, kit
out, names = sys.argv[1], sys.argv[2:]
kit.reset()
mb = kit.MB(); mb.box(-5, -8, -0.05, 60, 8, 0, kit.mat_plain("f", (0.6, 0.6, 0.6))); mb.build("floor")
x = 0.0
for n in names:
    c = kit.lib(n)
    sx = c["size"][0]
    kit.place(n, (x + sx / 2, 0, 0))
    x += sx + 0.5
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=250)
cam = kit.camera("c", (x / 2, -x * 0.62 - 2, x * 0.28 + 1.2), (x / 2, 0, 0.5), lens=35)
kit.render_setup(1600, 600, samples=24)
kit.render(cam, out)
