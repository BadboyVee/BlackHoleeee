"""Assemble and render the duplex scene.

    python3 build.py --cams hero,aerial --res 1920x1080 --samples 128
    python3 build.py --save duplex.blend           # write the .blend
Options: --no-veg (skip heavy trees), --no-interior, --out DIR
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blender-kit"))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import kit  # noqa: E402
import house  # noqa: E402
import compound as site_mod  # noqa: E402

CARS = os.environ.get("CARS_DIR", "/home/user/assets/cars")


EXPOSURE = {"living": 1.3, "dining": 1.7, "kitchen": 0.9, "master": 1.3, "hall": 1.9, "bath": 2.0, "bed2": 1.8}


def cameras(c):
    from house import Z0, Z1
    cam = {}
    K = lambda n, loc, tgt, lens: cam.__setitem__(n, kit.camera(n, loc, tgt, lens=lens, collection=c))
    K("hero", (-7.5, -11.6, 1.5), (6.2, 2.0, 3.2), 24)
    K("front", (8.5, -12.0, 1.6), (7.3, 3.0, 3.6), 22)
    K("drive", (23.0, -11.0, 1.6), (9.0, 3.0, 3.0), 24)
    K("street", (31.0, -19.8, 1.65), (10.0, -2.0, 3.8), 26)
    K("gate", (18.0, -20.5, 1.6), (12.0, 2.0, 3.2), 24)
    K("aerial", (-22.0, -34.0, 24.0), (6.0, 3.0, 2.0), 30)
    K("aerial2", (40.0, -30.0, 20.0), (6.0, 4.0, 2.0), 32)
    K("pool", (-12.0, -1.0, 1.5), (2.0, 4.0, 2.7), 20)
    K("back", (-6.0, 21.0, 2.2), (8.0, 8.0, 3.2), 24)
    K("top", (6.0, 5.0, 75.0), (6.0, 5.01, 0.0), 40)
    K("living", (0.6, 0.65, Z0 + 1.45), (6.2, 4.9, Z0 + 0.95), 17)
    K("dining", (4.8, 6.75, Z0 + 1.5), (1.6, 9.6, Z0 + 0.9), 17)
    K("kitchen", (9.55, 6.75, Z0 + 1.55), (6.6, 10.0, Z0 + 0.9), 17)
    K("hall", (8.15, 1.6, Z0 + 1.5), (10.3, 5.0, Z0 + 1.9), 16)
    K("master", (7.05, 5.75, Z1 + 1.5), (1.8, 3.2, Z1 + 0.8), 17)
    K("bath", (3.0, 6.6, Z1 + 1.55), (1.2, 10.2, Z1 + 0.7), 16)
    K("bed2", (11.6, 1.45, Z1 + 1.5), (13.6, 4.4, Z1 + 0.7), 17)
    return cam


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cams", default="hero")
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--out", default="/home/user/out")
    ap.add_argument("--save", default="")
    ap.add_argument("--no-veg", action="store_true")
    ap.add_argument("--no-interior", action="store_true")
    ap.add_argument("--gate", type=float, default=0.55)
    ap.add_argument("--sun", type=float, default=215.0, help="sun azimuth, degrees from +X toward +Y")
    ap.add_argument("--sun-lamp", type=float, default=2.5)
    ap.add_argument("--sun-el", type=float, default=48.0)
    ap.add_argument("--sky", default="kloofendal_48d_partly_cloudy_puresky")
    ap.add_argument("--sky-strength", type=float, default=1.0)
    ap.add_argument("--exposure", type=float, default=0.25)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

    kit.reset()
    ch = kit.coll("House")
    H = house.House(ch)
    H.build()
    cs = kit.coll("Site")
    S = site_mod.Site(cs, H.M)
    if a.no_veg:
        S.vegetation = lambda: None
    S.build(gate_open=a.gate)

    if not a.no_interior:
        try:
            import interior
            interior.build(kit.coll("Interior"), H, S)
        except ImportError:
            pass

    cc = kit.coll("Cars")
    kit.place("ferrari", (18.3, 4.4, 0.03), rz=math.pi, collection=cc, path=os.path.join(CARS, "ferrari_plain.glb"))
    kit.place("carconcept", (13.2, -5.6, 0.03), rz=math.radians(200), collection=cc,
              path=os.path.join(CARS, "CarConcept_plain.glb"), center=False)

    kit.world_hdri(a.sky, "4k", a.sky_strength, sun_az=a.sun)
    if a.sun_lamp > 0:      # a crisp sun on top of the sky's own soft one
        from mathutils import Vector
        el, az = math.radians(a.sun_el), math.radians(a.sun)
        d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        s = kit.sun(strength=a.sun_lamp, angle=0.6)
        s.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    w, h = [int(v) for v in a.res.split("x")]
    kit.render_setup(w, h, samples=a.samples, exposure=a.exposure)
    cams = cameras(kit.coll("Cameras"))
    if a.save:
        bpy.context.scene.camera = cams["hero"]
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
    os.makedirs(a.out, exist_ok=True)
    for n in [x for x in a.cams.split(",") if x]:
        bpy.context.scene.view_settings.exposure = a.exposure + EXPOSURE.get(n, 0.0)
        kit.render(cams[n], os.path.join(a.out, f"duplex_{n}.png"))


if __name__ == "__main__":
    main()
