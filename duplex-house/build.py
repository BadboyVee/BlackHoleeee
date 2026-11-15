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
    K("hero", (-7.0, -11.4, 1.5), (6.4, 2.0, 3.3), 24)
    K("front", (8.5, -12.0, 1.6), (7.3, 3.0, 3.6), 22)
    K("drive", (23.0, -11.0, 1.6), (9.0, 3.0, 3.0), 24)
    K("street", (20.0, -25.0, 1.7), (13.0, 0.0, 3.6), 22)
    K("gate", (22.5, -21.0, 1.6), (11.0, 1.0, 3.4), 24)
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
    ap.add_argument("--export", default="", help="write the scene as .glb or .fbx for Unreal / other engines")
    ap.add_argument("--no-veg", action="store_true")
    ap.add_argument("--no-interior", action="store_true")
    ap.add_argument("--no-people", action="store_true")
    ap.add_argument("--anim", default="", help="exterior | interior: render an animated camera move as frames")
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--gate", type=float, default=0.75)
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
    # restyled copies of the duplex for the neighbouring plots
    import cars
    lib = kit.coll("LIB", hide=True)
    variants = []
    styles = [
        dict(white=kit.mat_pbr("v1_wall", "painted_plaster_wall", size=3.0, tint=(1.0, 0.93, 0.8), val=1.4, sat=0.2),
             wood=kit.mat_pbr("v1_clad", "stacked_stone_wall", size=1.6, val=2.0, sat=0.3, tint=(0.75, 0.68, 0.6)),
             grey=kit.mat_pbr("v1_frame", "painted_plaster_wall", size=3.0, tint=(0.36, 0.25, 0.18), sat=0.3),
             stone=kit.mat_pbr("v1_base", "painted_plaster_wall", size=3.0, tint=(0.55, 0.42, 0.32), sat=0.3)),
        dict(white=kit.mat_pbr("v2_wall", "painted_plaster_wall", size=3.0, tint=(0.8, 0.82, 0.84), val=1.35, sat=0.2),
             wood=kit.mat_pbr("v2_clad", "painted_plaster_wall", size=3.0, tint=(0.95, 0.95, 0.93), val=1.4, sat=0.1),
             grey=kit.mat_pbr("v2_frame", "painted_plaster_wall", size=3.0, tint=(0.1, 0.11, 0.13), sat=0.3),
             stone=kit.mat_pbr("v2_base", "concrete_floor_02", size=3.0, val=0.9)),
        dict(white=kit.mat_pbr("v3_wall", "painted_plaster_wall", size=3.0, tint=(0.98, 0.86, 0.72), val=1.3, sat=0.2),
             wood=kit.mat_pbr("v3_clad", "oak_wood_planks", size=1.6, rot=math.pi / 2, tint=(0.5, 0.36, 0.26)),
             grey=kit.mat_pbr("v3_frame", "painted_plaster_wall", size=3.0, tint=(0.9, 0.9, 0.88), val=1.3, sat=0.1)),
    ]
    for i, pal in enumerate(styles):
        vc = bpy.data.collections.new(f"LIB_duplex_v{i}")
        lib.children.link(vc)
        house.House(vc, palette=pal, name=f"duplex_v{i}").build()
        variants.append(vc)

    cs = kit.coll("Site")
    S = site_mod.Site(cs, H.M)
    S.variants = variants
    S.street_cars = [cars.gz("suv"), cars.gz("prius_hybrid"), cars.gz("hatchback"), cars.gz("prius_hybrid")]
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
    for (lc, x, y, hd) in S.cars_placed:
        cars.put(lc, (x, y, 0.0 if y > -14 else -0.06), hd, cc)
    cars.put(cars.bmw(), (12.2, -6.0, 0.03), 118, cc, "bmw_court")                 # in front of the porch
    cars.put(cars.ferrari(), (18.4, 4.4, 0.03), -90, cc, "ferrari_carport")
    cars.put(cars.concept(), (21.4, 4.3, 0.03), -90, cc, "concept_carport")
    cars.put(cars.bmw(color=(0.75, 0.76, 0.78)), (18.6, -11.4, 0.03), 92, cc, "bmw_arriving")   # coming in through the gate

    if not a.no_people:
        import cast
        from house import Z0, Z1
        cp = kit.coll("People")

        def put(name, pose, loc, rz=0.0, **kw):
            o = cast.make(name, pose, cp, **kw)
            o.location, o.rotation_euler = loc, (0, 0, rz)
            return o

        put("ngozi", "stand_relaxed", (3.2, -1.5, 0.42), math.radians(25))          # on the terrace
        put("bayo", "walk", (10.4, -3.4, 0.03), math.radians(-140))                 # walking to the car
        put("kunle", "stand", (-9.6, -10.4, 0.0), math.radians(-60))                # gardener by the beds
        put("guard", "stand", (20.4, -10.2, 0.03), math.radians(120))               # security at the gate
        put("zainab", "sit", (-7.2, 5.56, 0.155 - 0.47), 0.0)                       # feet in the pool
        put("claire", "stand_relaxed", (-5.4, 6.3, 0.12), math.radians(40))         # by the loungers
        put("mark", "hands_hips", (3.4, -0.45, Z1), math.radians(10))               # on the master balcony
        put("lena", "stand", (1.6, 0.9, Z1), math.radians(-30))
        if not a.no_interior:
            put("amina", "sit", (3.3, 4.2, Z0 + 0.4 - 0.47), math.radians(-90))     # on the living-room sofa
            put("jack", "stand_relaxed", (6.9, 8.6, Z0), math.radians(100))         # in the kitchen
            put("sophie", "sit", (2.7, 9.27 - 0.25, Z0 + 0.47 - 0.47), math.pi)     # at the dining table
            put("emeka", "stand", (5.6, 2.0, Z0), math.radians(60))                 # living room, by the window

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
    if a.export:
        p = os.path.abspath(a.export)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if p.lower().endswith(".fbx"):
            bpy.ops.export_scene.fbx(filepath=p, path_mode="COPY", embed_textures=True, use_mesh_modifiers=True,
                                     object_types={"MESH", "EMPTY"}, axis_forward="-Y", axis_up="Z")
        else:
            bpy.ops.export_scene.gltf(filepath=p, export_format="GLB", export_apply=True, export_cameras=False,
                                      export_lights=False, export_image_format="JPEG", export_jpeg_quality=85)
        print("exported", p, os.path.getsize(p) // (1024 * 1024), "MB")
        return
    os.makedirs(a.out, exist_ok=True)
    if a.anim:
        from house import Z0
        n = a.frames
        ez = Z0 + 1.5
        if a.anim == "exterior":      # drone glides down from above the street to the lawn
            keys = [(1, (-27.0, -39.0, 21.0), (6.0, 3.0, 3.0)), (int(n * 0.5), (-17.0, -25.0, 8.0), (6.0, 3.0, 3.0)),
                    (n, (-7.0, -11.4, 1.6), (6.4, 2.0, 3.3))]
            lens, ex = 24, 0.0
        elif a.anim == "orbit":       # slow arc round the front of the house at eye level
            keys = [(1, (-9.0, -9.0, 1.7), (6.5, 2.5, 3.2)), (int(n * 0.5), (5.0, -12.0, 1.7), (7.0, 2.5, 3.2)),
                    (n, (19.0, -10.5, 1.8), (8.0, 2.5, 3.2))]
            lens, ex = 22, 0.0
        else:                         # walk from the front door through the living room to the dining room
            keys = [(1, (9.1, 1.9, ez), (7.0, 3.0, Z0 + 1.3)), (int(n * 0.3), (6.4, 2.7, ez), (3.0, 4.4, Z0 + 1.0)),
                    (int(n * 0.65), (5.8, 4.9, ez), (2.6, 8.0, Z0 + 1.0)), (n, (4.0, 5.8, ez), (2.6, 9.2, Z0 + 0.95))]
            lens, ex = 17, 1.3
        cam, _ = kit.anim_camera("anim_" + a.anim, keys, lens=lens, collection=kit.coll("Cameras"))
        bpy.context.scene.view_settings.exposure = a.exposure + ex
        kit.render_frames(cam, os.path.join(a.out, "anim_" + a.anim), 1, n)
        return
    for n in [x for x in a.cams.split(",") if x]:
        bpy.context.scene.view_settings.exposure = a.exposure + EXPOSURE.get(n, 0.0)
        kit.render(cams[n], os.path.join(a.out, f"duplex_{n}.png"))


if __name__ == "__main__":
    main()
