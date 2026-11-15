"""Line-up of the cast: python3 people_test.py out.png name1,name2,... [pose1,pose2,...]"""
import sys, math
import bpy, kit, mh, cast
kit.reset()
c = kit.coll("People")
mb = kit.MB(); mb.box(-6, -6, -0.05, 30, 6, 0, kit.mat_plain("f", (0.5, 0.5, 0.5))); mb.build("floor")
names = sys.argv[2].split(",")
poses = sys.argv[3].split(",") if len(sys.argv) > 3 else ["stand"] * len(names)
for i, nm in enumerate(names):
    ob = cast.make(nm, poses[i % len(poses)], c)
    ob.location = (i * 0.95, 0, 0)
n = len(names)
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=250)
kit.render_setup(int(260 * n), 700, samples=32)
w = (n - 1) * 0.95
kit.render(kit.camera("c", (w / 2, -4.2 - 1.15 * n, 1.2), (w / 2, 0, 0.92), lens=50), sys.argv[1])
