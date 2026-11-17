"""Line-up of every car model: python3 cars_test.py out.png"""
import sys, math
import bpy, kit, cars
kit.reset()
c = kit.coll("Cars")
mb = kit.MB(); mb.box(-10, -12, -0.05, 40, 12, 0, kit.mat_pbr("pv", "concrete_pavers", size=1.6)); mb.build("floor")
x = 0
for fn in (cars.bmw, cars.ferrari, cars.concept, lambda: cars.gz("suv"), lambda: cars.gz("prius_hybrid"), lambda: cars.gz("hatchback")):
    try:
        cc = fn()
        cars.put(cc, (x, 0, 0), -90, c)
    except Exception as e:
        import traceback; traceback.print_exc()
    x += 3.0
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=250)
kit.render_setup(1800, 640, samples=40)
kit.render(kit.camera("c", (7.5, -22, 4.2), (7.5, 0, 0.6), lens=50), sys.argv[1])
