import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender-kit"))
import bpy, kit, house
kit.reset()
c = kit.coll("House")
H = house.House(c); H.build()
mb = kit.MB(); mb.box(-60, -60, -0.1, 80, 80, 0, kit.mat_pbr("g", "concrete_pavement", size=2)); mb.build("ground")
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, rot_z=math.radians(float(os.environ.get("ROT", "200"))))
kit.render_setup(1280, 720, samples=32)
cams = {
 "front": kit.camera("front", (-4, -17, 1.7), (7, 3, 3.6), lens=26),
 "fr": kit.camera("fr", (24, -14, 4.5), (8, 4, 3.4), lens=28),
 "back": kit.camera("back", (22, 26, 9), (7, 6, 3), lens=28),
 "top": kit.camera("top", (7.5, 5.4, 40), (7.5, 5.5, 0), lens=35),
}
for n in sys.argv[1:]:
    kit.render(cams[n], f"/home/user/out/shell_{n}.png")
