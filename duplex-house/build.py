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
from mathutils import Vector  # noqa: E402

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
    K("front", (5.2, -12.4, 1.6), (7.3, 3.0, 3.6), 22)
    K("drive", (23.0, -11.0, 1.6), (9.0, 3.0, 3.0), 24)
    K("street", (20.0, -25.0, 1.7), (13.0, 0.0, 3.6), 22)
    K("gate", (22.5, -21.0, 1.6), (11.0, 1.0, 3.4), 24)
    K("aerial", (-22.0, -34.0, 24.0), (6.0, 3.0, 2.0), 30)
    K("aerial2", (40.0, -30.0, 20.0), (6.0, 4.0, 2.0), 32)
    K("pool", (-12.0, -1.0, 1.5), (2.0, 4.0, 2.7), 20)
    K("back", (-6.0, 21.0, 2.2), (8.0, 8.0, 3.2), 24)
    K("top", (6.0, 5.0, 75.0), (6.0, 5.01, 0.0), 40)
    K("street_w", (-40.0, -17.4, 1.6), (0.0, -16.0, 3.0), 26)        # looking east down the street
    K("street_e", (40.0, -18.4, 1.6), (8.0, -15.0, 3.2), 26)        # looking west, our gate on the right
    K("street_air", (-30.0, -40.0, 16.0), (12.0, -14.0, 1.0), 26)    # the street from a low drone
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
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=0)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated frame numbers to render")
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
    H = house.House(ch, front_open=95.0 if a.anim == "interior" else 0.0)
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
    S.street_cars = [cars.bmw(color=(0.02, 0.02, 0.025)), cars.bmw(color=(0.75, 0.76, 0.78)), cars.bmw(color=(0.85, 0.85, 0.83)),
                     cars.bmw(color=(0.05, 0.12, 0.3)), cars.bmw(color=(0.35, 0.03, 0.04)), cars.bmw(color=(0.3, 0.31, 0.33)),
                     cars.concept()]
    if a.no_veg:
        S.vegetation = lambda: None
    S.build(gate_open=1.0 if a.anim == "street" else a.gate)

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
    cars.put(cars.bmw(color=(0.75, 0.76, 0.78)), (21.9, -3.4, 0.03), 92, cc, "bmw_silver")       # parked beside the carport
    cars.put(cars.bmw(color=(0.02, 0.02, 0.025)), (-12.0, -16.3, -0.06), 0, cc, "bmw_on_street")  # parked at the kerb
    cars.put(cars.concept(), (58.0, -19.9, -0.06), 180, cc, "concept_on_street")

    P = {}
    if not a.no_people:
        import life
        from house import Z0, Z1
        cp = kit.coll("People")
        CLOSE = {"olivia", "claire", "kate", "ryan", "jack", "sophie", "daniel"}
        floors = {"walker1": 0.02, "walker2": 0.02, "walker3": 0.02, "walker4": 0.02, "walker5": 0.02, "walker6": 0.02,
                  "guard": 0.03, "tom": 0.0, "daniel": 0.03, "olivia": 0.42, "claire": 0.42, "emma": 0.155,
                  "mark": Z1, "lena": Z1}
        if not a.no_interior:
            floors.update({"kate": Z0, "ryan": Z0, "jack": Z0, "sophie": Z0})
        for nm, fz in floors.items():
            P[nm] = life.Performer(nm, cp, [{"until": 999, "stand": (0, 0)}], (lambda z: (lambda x, y: z))(fz),
                                   subdiv=1 if nm in CLOSE else 0, style=0.6 if nm in ("olivia", "claire", "walker1", "walker4") else 0.0)

    def stage(cam_xy=None, cam_t=None):
        """Everyone's script. cam_t(x, y, r): first time the film camera comes within r of (x, y)."""
        if not P:
            return
        ct = cam_t or (lambda x, y, r: None)
        near = lambda name: (lambda t: cam_xy(t) if cam_xy and cam_xy(t) and (cam_xy(t) - P[name]._pos).length < 9 else None)
        partner = lambda q: (lambda t: tuple(P[q]._pos))

        def other_or_cam(me, q):
            def f(t):
                c = near(me)(t)
                return c if c is not None else tuple(P[q]._pos)
            return f
        # the street
        tc = ct(-18.0, -18.4, 3.0) or 9.0
        P["walker1"].actions = [{"until": 999, "walk": [(-18 - 1.25 * tc, -14.15), (80, -14.15)], "speed": 1.25}]
        P["walker2"].actions = [{"until": 999, "walk": [(-18.6 - 1.25 * tc, -14.62), (80, -14.62)], "speed": 1.25}]
        P["walker1"].look_at = lambda t: tuple(P["walker2"]._pos + Vector((3.0, 0)))
        P["walker2"].look_at = lambda t: tuple(P["walker1"]._pos + Vector((3.0, 0)))
        P["walker3"].actions = [{"until": 999, "walk": [(26, -23.45), (-90, -23.45)], "speed": 1.3}]
        P["walker5"].actions = [{"until": 999, "walk": [(44, -14.35), (-60, -14.35)], "speed": 0.85}]
        P["walker4"].actions = [{"until": 999, "stand": (-6.3, -14.2), "face": (-5.4, -14.5), "talk": 0.8, "hand": "R"}]
        P["walker6"].actions = [{"until": 999, "stand": (-5.4, -14.5), "face": (-6.3, -14.2), "talk": 0.5, "hand": "L"}]
        P["walker4"].look_at = other_or_cam("walker4", "walker6")
        P["walker6"].look_at = other_or_cam("walker6", "walker4")
        # the gate: the guard steps out of the shade and waves the car in
        tg = ct(18.0, -14.0, 9.0) or 30.0
        P["guard"].actions = [{"until": tg, "stand": (20.9, -10.9), "face": (18.0, -14.0)},
                              {"until": tg + 3.5, "stand": (20.9, -10.9), "face": (18.0, -12.5), "wave": True},
                              {"until": 999, "stand": (20.9, -10.9), "face": (18.0, -9.0)}]
        P["guard"].look_at = near("guard")
        P["tom"].actions = [{"until": 22, "walk": [(-9.5, -11.0), (3.5, -11.0)], "speed": 0.6},
                            {"until": 30, "stand": (3.5, -11.0), "face": -90},
                            {"until": 999, "walk": [(3.5, -11.0), (-9.5, -11.0)], "speed": 0.6}]
        ti = ct(17.5, -11.0, 2.0) or 34.0
        P["daniel"].actions = [{"until": ti - 1.0, "stand": (10.6, -2.4), "face": (2.0, -0.8), "talk": 0.6},
                               {"until": 999, "walk": [(10.6, -2.4), (10.6, -3.4), (10.55, -4.7)], "speed": 1.2}]
        P["daniel"].look_at = near("daniel")
        P["olivia"].actions = [{"until": 999, "stand": (0.6, -1.0), "face": (1.5, -0.45), "talk": 0.9}]
        P["claire"].actions = [{"until": 999, "stand": (1.5, -0.45), "face": (0.6, -1.0), "talk": 0.5, "hand": "L"}]
        P["olivia"].look_at = other_or_cam("olivia", "claire")
        P["claire"].look_at = other_or_cam("claire", "olivia")
        P["emma"].actions = [{"until": 999, "sit": (-7.2, 5.66), "face": -90}]
        P["mark"].actions = [{"until": 999, "stand": (3.7, -0.35), "face": (2.7, 0.35), "talk": 0.7}]
        P["lena"].actions = [{"until": 999, "stand": (2.7, 0.35), "face": (3.7, -0.35), "talk": 0.5, "hand": "L"}]
        P["mark"].look_at = partner("lena")
        P["lena"].look_at = partner("mark")
        if "kate" in P:
            P["kate"].actions = [{"until": 999, "stand": (5.55, 5.3), "face": (6.4, 4.6), "talk": 0.8}]
            P["ryan"].actions = [{"until": 999, "stand": (6.4, 4.6), "face": (5.55, 5.3), "talk": 0.5, "hand": "L"}]
            P["jack"].actions = [{"until": 999, "stand": (7.4, 9.62), "face": (5.9, 8.6), "talk": 0.8}]
            P["sophie"].actions = [{"until": 999, "stand": (5.85, 9.7), "face": (7.4, 9.62), "talk": 0.5, "hand": "L"}]
            for (x, y) in (("kate", "ryan"), ("ryan", "kate"), ("jack", "sophie"), ("sophie", "jack")):
                P[x].look_at = other_or_cam(x, y)

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
        from house import Z0, Z1, RISE
        fps = 12.0
        C = kit.coll("Cameras")
        s_ = bpy.context.scene
        shots = []                                   # (camera, first frame, last frame)
        if a.anim == "street":
            # a car's-eye drive down the estate street, in through the gate, then out and on foot to the terrace
            y, z = -18.45, 1.25
            drive = [((-72, y, z), (-45, -18.2, 1.5), 5.8), ((-56, y, z), (-30, -17.0, 1.7), 5.8),
                     ((-40, y, z), (-15, -16.0, 1.9), 2.6), ((-33, y, z), (-10, -14.5, 2.3), 2.6),
                     ((-20, y, z), (0, -12.0, 2.6), 5.6), ((-4, y, z), (14, -11.0, 2.6), 4.6),
                     ((9.5, -18.7, z), (19, -9.0, 2.4), 2.6), ((15.8, -17.2, z), (18.5, -6.0, 2.2), 1.7),
                     ((18.1, -14.2, z), (16.0, -3.0, 2.6), 1.6), ((18.0, -10.8, z), (12.0, -1.0, 2.9), 1.5),
                     ((16.4, -8.0, z), (9.0, 1.5, 3.2), 0.6)]
            cam1, f1 = kit.path_camera("anim_street_drive", drive, fps=fps, lens=24, collection=C, f0=1)
            walk = [((16.4, -8.0, 1.25), (9.0, 1.5, 3.2), 0.8), ((15.6, -7.6, 1.62), (8.0, 2.0, 3.6), 1.1),
                    ((14.3, -5.4, 1.65), (6.5, 2.5, 3.8), 1.3), ((12.6, -3.0, 1.65), (5.0, 3.0, 3.5), 1.3),
                    ((9.2, -2.3, 1.65), (3.0, 2.5, 3.2), 1.3), ((7.2, -3.5, 1.65), (2.0, 3.0, 2.8), 1.2),
                    ((5.2, -3.1, 1.86), (0.5, 3.0, 2.6), 1.0), ((4.6, -2.3, 2.07), (0.0, 3.0, 2.6), 1.0),
                    ((1.4, -2.2, 2.07), (-6.0, 3.5, 1.2), 1.0), ((-1.2, -1.6, 2.07), (-8.0, 4.5, 0.4), 0.6)]
            cam2, f2 = kit.path_camera("anim_street_walk", walk, fps=fps, lens=24, collection=C, f0=f1 + 1, bob=0.012)
            shots = [(cam1, 1, f1), (cam2, f1 + 1, f2)]
            s_.view_settings.exposure = a.exposure
        elif a.anim == "interior":
            # a walk-through: up the porch, in the front door, living, dining, kitchen, up the stairs to the master suite
            ez, uz = Z0 + 1.6, Z1 + 1.6
            zl = Z0 + 10 * RISE

            def up(yy):                               # eye height on the east flight
                return Z0 + ((yy - 2.8) / 0.27 + 1) * RISE + 1.6

            def up2(yy):                              # eye height on the west flight
                return zl + (5.23 - yy) / 0.27 * RISE + 1.6

            wp = [((9.05, -3.2, 1.45), (9.05, 2.0, 2.0), 1.22), ((9.05, -0.7, 1.45), (9.05, 3.0, 2.1), 1.10),
                  ((9.05, 0.9, ez), (8.9, 4.0, 2.0), 1.10), ((8.9, 2.2, ez), (5.0, 3.0, 1.45), 1.22),
                  ((6.8, 1.6, ez), (3.5, 4.2, 1.45), 1.22), ((4.2, 1.45, ez), (2.0, 4.6, 1.45), 1.22),
                  ((2.7, 1.95, ez), (1.8, 6.5, 1.45), 1.22), ((1.7, 3.0, ez), (2.0, 8.5, 1.45), 1.22),
                  ((1.6, 5.4, ez), (2.6, 9.0, 1.45), 1.22), ((1.95, 6.9, ez), (3.2, 9.0, 1.45), 1.10),
                  ((4.3, 7.25, ez), (8.0, 8.8, 1.45), 1.22), ((5.6, 7.38, ez), (8.6, 9.6, 1.45), 1.22),
                  ((7.2, 7.35, ez), (8.4, 5.5, 1.45), 1.10), ((8.2, 6.8, ez), (8.2, 3.0, 1.45), 1.22),
                  ((8.2, 5.0, ez), (10.4, 3.6, 2.6), 1.34), ((8.45, 3.0, ez), (10.6, 4.6, 3.0), 1.22),
                  ((9.4, 2.78, ez), (10.6, 5.0, 3.5), 1.10), ((10.6, 2.6, ez), (10.6, 6.0, 3.8), 0.92),
                  ((10.6, 3.5, up(3.5)), (10.6, 6.0, zl + 1.7), 0.85), ((10.6, 4.8, up(4.8)), (10.2, 6.5, zl + 1.8), 0.85),
                  ((10.45, 5.7, zl + 1.6), (9.0, 4.0, zl + 2.3), 0.79), ((9.45, 5.5, zl + 1.6), (9.45, 2.5, uz), 0.85),
                  ((9.45, 4.2, up2(4.2)), (8.5, 2.0, uz - 0.1), 0.85), ((9.45, 3.0, uz), (7.0, 2.2, uz - 0.2), 0.98),
                  ((8.2, 2.22, uz), (5.0, 2.6, Z1 + 1.0), 1.10), ((6.8, 2.25, uz), (3.2, 4.8, Z1 + 0.8), 1.22),
                  ((5.0, 3.4, uz), (2.6, 5.2, Z1 + 0.7), 1.10), ((4.2, 2.9, uz), (3.0, 0.0, Z1 + 1.2), 0.98),
                  ((3.6, 2.2, uz), (3.2, -3.0, Z1 + 0.6), 0.61)]
            cam1, f1 = kit.path_camera("anim_interior", wp, fps=fps, lens=17, collection=C, f0=1, bob=0.01)
            shots = [(cam1, 1, f1)]
            # auto-exposure: outdoors, then brighter once through the front door
            for f in range(1, f1 + 1):
                s_.frame_set(f)
                yy = cam1.matrix_world.translation.y
                k = max(0.0, min(1.0, (yy - 0.4) / 1.2))
                s_.view_settings.exposure = a.exposure + 0.2 + 1.15 * k
                s_.view_settings.keyframe_insert("exposure", frame=f)
        else:
            raise SystemExit("unknown --anim " + a.anim)
        if P:
            import life
            track = []
            for (cam, fa, fb) in shots:
                track += kit.PATHS[cam.name]
            track.sort(key=lambda q: q[0])
            pos_at = {f: p for f, p in track}
            last = track[-1][0]

            def cam_xy(t):
                p = pos_at.get(min(last, max(1, int(round(t * fps)) + 1)))
                return Vector((p.x, p.y)) if p is not None else None

            def cam_t(x, y, r):
                for f, p in track:
                    if math.hypot(p.x - x, p.y - y) < r:
                        return (f - 1) / fps
                return None
            stage(cam_xy, cam_t)
            life.animate(list(P.values()), 1, last, fps)
            print("PEOPLE animated", len(P), "performers,", last, "frames")
        obstacles = [(x, y_, 0.55) for (x, y_, h) in S.palms] + [(x, y_, 0.9) for (k_, x, y_, sc) in S.trees]
        for o in bpy.data.objects:                          # cars as three overlapping discs along their length
            if o.instance_type == "COLLECTION" and o.users_collection and o.users_collection[0].name == "Cars":
                hx, hy = math.cos(o.rotation_euler.z), math.sin(o.rotation_euler.z)
                for k_ in (-1.5, 0.0, 1.5):
                    obstacles.append((o.location.x + hx * k_, o.location.y + hy * k_, 1.0))
        for (cam, fa, fb) in shots:
            near = []
            for (f, p) in kit.PATHS[cam.name]:
                obs = list(obstacles) + [(*pf.track[f], 0.35) for pf in P.values() if hasattr(pf, "track") and f in pf.track
                                          and abs(pf.floor(0, 0) - (p.z - 1.6)) < 1.5]
                for (ox, oy, rr) in obs:
                    dd = math.hypot(p.x - ox, p.y - oy) - rr
                    if dd < 0.35:
                        near.append((f, round(ox, 1), round(oy, 1), round(dd, 2)))
            print(f"NEAR {cam.name}: {near[:10]}")
        for (cam, fa, fb) in shots:
            bad = kit.path_check(cam, fa, fb)
            print(f"PATH {cam.name} frames {fa}-{fb} ({(fb - fa + 1) / fps:.1f} s) collisions: {bad[:12]}")
            for (bf, bo) in bad[:4]:
                s_.frame_set(bf)
                print("   at", bf, tuple(round(v, 2) for v in cam.matrix_world.translation), bo)
        if a.check_only:
            return
        out = os.path.join(a.out, "anim_" + a.anim)
        for (cam, fa, fb) in shots:
            lo = max(fa, a.first)
            hi = min(fb, a.last or fb)
            frames = [int(x) for x in a.only.split(",")] if a.only else range(lo, hi + 1, a.step)
            for f in frames:
                if fa <= f <= fb:
                    kit.render_frames(cam, out, f, f)
        return
    if P:
        import life
        stage()
        life.still(list(P.values()), 20.0)
    for n in [x for x in a.cams.split(",") if x]:
        bpy.context.scene.view_settings.exposure = a.exposure + EXPOSURE.get(n, 0.0)
        kit.render(cams[n], os.path.join(a.out, f"duplex_{n}.png"))


if __name__ == "__main__":
    main()
