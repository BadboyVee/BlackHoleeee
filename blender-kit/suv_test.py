"""Turntable-style check of the 4x4 with the cast aboard: python3 suv_test.py out_prefix"""
import sys, math
import bpy, kit, mh, cast, suv
kit.reset()
c = kit.coll("Scene")
mb = kit.MB(); mb.box(-30, -30, -0.05, 30, 30, 0, kit.mat_pbr("sand", "sand_01", size=2.0)); mb.build("floor")
lib = suv.build("truck")
t = suv.instance(lib, (0, 0, 0), 0.0, c)
if "--empty" not in sys.argv:
    ppl = {"driver": cast.make("tunde", "car_drive", c), "front": cast.make("amina", "car_look_r", c),
           "rear_l": cast.make("chidi", "car_look_l", c), "rear_c": cast.make("zainab", "car", c),
           "rear_r": cast.make("emeka", "car_look_r", c)}
    suv.seat_people(t, ppl)
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=300)
kit.render_setup(1280, 720, samples=40)
cams = {"fq": ((6.2, -5.2, 1.7), (0.2, 0, 1.0)), "side": ((0.3, -7.5, 1.4), (0.0, 0, 1.0)), "rq": ((-6.0, 4.6, 2.3), (-0.3, 0, 1.0)),
        "in": ((3.6, -1.6, 1.55), (0.0, 0.0, 1.25))}
for n in sys.argv[2].split(","):
    loc, tg = cams[n]
    kit.render(kit.camera(n, loc, tg, lens=45 if n != "in" else 60), f"{sys.argv[1]}_{n}.png")
