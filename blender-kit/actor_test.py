"""Driver-at-the-wheel check: python3 actor_test.py out.png"""
import sys, math
import bpy, kit, mh, cast, suv
from mathutils import Vector, Matrix
kit.reset()
c = kit.coll("Scene")
mb = kit.MB(); mb.box(-30, -30, -0.05, 30, 30, 0, kit.mat_plain("f", (0.5, 0.45, 0.35))); mb.build("floor")
lib = suv.build("truck")
t = suv.instance(lib, (0, 0, 0), 0.0, c)
import crew
crew.seat(t, c, time=1.0)
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=300)
kit.render_setup(1280, 720, samples=32)
kit.render(kit.camera("a", (2.6, 2.2, 1.75), (0.45, 0.35, 1.2), lens=50), sys.argv[1] + "_a.png")
kit.render(kit.camera("b", (3.6, -1.5, 1.6), (0.0, 0.0, 1.25), lens=55), sys.argv[1] + "_b.png")
