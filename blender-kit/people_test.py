"""Line-up test of the desert cast: python3 people_test.py out.png [cam]"""
import sys, math
import bpy, kit, mh
import cast
kit.reset()
c = kit.coll("People")
mb = kit.MB(); mb.box(-6, -6, -0.05, 12, 6, 0, kit.mat_plain("f", (0.55, 0.55, 0.55))); mb.build("floor")
poses = sys.argv[3].split(",") if len(sys.argv) > 3 else ["stand", "stand_relaxed", "walk", "sit", "drive"]
for i, (nm, p) in enumerate(zip(["tunde", "amina", "chidi", "zainab", "emeka"], poses)):
    ob = cast.make(nm, p, c)
    ob.location = (i * 1.15, 0, 0)
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=250)
cam = kit.camera("c", (6.5, -5.5, 1.5), (2.3, 0, 0.9), lens=50) if len(sys.argv) > 2 else kit.camera("c", (2.3, -6.6, 1.3), (2.3, 0, 0.9), lens=50)
kit.render_setup(1500, 760, samples=32)
kit.render(cam, sys.argv[1])
