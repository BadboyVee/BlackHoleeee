"""The 40 s showcase film: assembly, exterior shots, doors + cabin, finale (see tb/timeline.py)."""
import math
import bpy
from mathutils import Vector
from . import spec, util, preview, environment
from . import timeline as TL

F = TL.frame

# group -> (hit time, location offset, rotation offset)
ASSEMBLY = {
    "powertrain": (3.0, (0.0, 0.0, 2.6), (0.0, 0.0, 0.5)),
    "wheel_FL": (4.0, (0.4, 2.8, 0.0), (0, 0, 0)), "wheel_FR": (4.0, (0.4, -2.8, 0.0), (0, 0, 0)),
    "wheel_RL": (4.5, (-0.4, 2.8, 0.0), (0, 0, 0)), "wheel_RR": (4.5, (-0.4, -2.8, 0.0), (0, 0, 0)),
    "seats": (5.0, (-0.2, 0.0, 2.3), (0, 0, 0)),
    "dash": (5.5, (1.3, 0.0, 2.0), (0.0, -0.4, 0.0)),
    "rear": (6.5, (-3.2, 0.0, 1.6), (0.0, 0.35, 0.0)),
    "front": (7.5, (3.2, 0.0, 1.5), (0.0, -0.35, 0.0)),
    "door_L": (8.5, (0.0, 2.5, 0.9), (0.5, 0, 0)), "door_R": (8.5, (0.0, -2.5, 0.9), (-0.5, 0, 0)),
    "roof": (9.5, (0.0, 0.0, 2.4), (0, 0, 0)),
    "wing": (10.5, (-1.6, 0.0, 1.8), (0.0, 0.6, 0.0)),
}
FLY = 1.3     # seconds of flight before each hit


def classify(name):
    n = name
    if n.startswith("WHL_"):
        return "wheel_" + n[4:6]
    if n.startswith("PWR_"):
        return "powertrain"
    if n.startswith("INT_"):
        if "Seat" in n:
            return "seats"
        if any(k in n for k in ("Dash", "Console", "Steer", "Cluster", "Vent", "Mirror", "Dial", "Hub", "Pod",
                                "Paddle", "Switch", "Knob", "Selector", "Start", "Toggle", "Blade", "Spine")):
            return "dash"
        return "chassis"
    if "Door" in n or n.startswith(("BODY_Mirror", "BODY_CLineTop")):
        return "door_R" if ("_R" in n) else "door_L"
    if n.startswith(("BODY_Quarter", "BODY_Island")):
        return "door_R" if n.endswith("_R") else "door_L"
    if n.startswith(("BODY_CanopyFrame", "BODY_Windshield", "BODY_EngineGlass", "BODY_Wiper")):
        return "roof"
    if n.startswith(("AERO_Wing",)):
        return "wing"
    if n.startswith(("BODY_RearClam", "BODY_Tail", "LGT_TailBar", "BODY_CLine_")):
        return "rear"
    if n.startswith(("BODY_FrontClam", "BODY_Horseshoe", "BODY_Intake", "BODY_Headlight", "BODY_HoodVent",
                     "BODY_Badge", "LGT_Head", "LGT_DRL", "AERO_Splitter")):
        return "front"
    return "chassis"          # sills, liners, diffuser, tub, flags ...


def _descendants(o):
    out = [o]
    for c in o.children:
        out += _descendants(c)
    return out


def _fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out


def _linear(idb):
    for fc in _fcurves(idb):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


def _key(obj, path, value, t, index=-1):
    if path.startswith('['):
        obj[path[2:-2]] = value
    else:
        setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=F(t), index=index)


def assembly(root):
    """Carrier empties per group, keyed from an exploded pose to home; parts hidden before take-off."""
    col = util.get_collection(spec.COLLECTIONS["rig"])
    groups = {}
    for o in list(root.children):
        if o.name == spec.CTRL:
            continue
        groups.setdefault(classify(o.name), []).append(o)
    for g, (hit, off, rot) in ASSEMBLY.items():
        objs = groups.get(g, [])
        if not objs:
            continue
        car = util.empty("ASM_" + g, (0, 0, 0), collection=col, size=0.2)
        util.parent(car, root)
        for o in objs:
            util.parent(o, car)
        t0 = hit - FLY
        car.location = off; car.rotation_euler = rot
        car.keyframe_insert("location", frame=F(t0)); car.keyframe_insert("rotation_euler", frame=F(t0))
        car.location = tuple(-0.035 * a for a in off); car.rotation_euler = tuple(-0.05 * a for a in rot)
        car.keyframe_insert("location", frame=F(hit - 0.10)); car.keyframe_insert("rotation_euler", frame=F(hit - 0.10))
        car.location = (0, 0, 0); car.rotation_euler = (0, 0, 0)
        car.keyframe_insert("location", frame=F(hit)); car.keyframe_insert("rotation_euler", frame=F(hit))
        for o in objs:
            for d in _descendants(o):
                d.hide_render = True
                d.keyframe_insert("hide_render", frame=F(t0) - 1)
                d.hide_render = False
                d.keyframe_insert("hide_render", frame=F(t0))
    return {g: len(v) for g, v in groups.items()}


def controls(ctrl):
    K = lambda prop, pairs: [_key(ctrl, '["%s"]' % prop, v, t) for t, v in pairs]
    K("headlights", [(0, 0), (11.95, 0), (12.0, 1), (12.08, 0.2), (12.17, 1), (38.0, 1), (38.12, 0.25),
                     (38.3, 1), (39.3, 1), (39.8, 0)])
    K("taillights", [(0, 0), (10.5, 0), (10.6, 0.35), (11.95, 0.35), (12.0, 1), (19.9, 1), (19.95, 0), (20.0, 0),
                     (20.5, 1), (39.3, 1), (39.8, 0)])
    K("interior_lights", [(0, 0), (31.6, 0), (32.4, 1), (36.0, 1), (37.0, 0.25), (39.3, 0.25), (39.8, 0)])
    for p in ("door_L", "door_R"):
        K(p, [(0, 0), (28.0, 0), (30.4, 1), (36.0, 1), (37.8, 0)])
    K("wing", [(0, 0), (21.3, 0), (22.3, 1), (23.4, 1), (24.0, 0)])
    K("wheel_spin", [(0, 18.0), (2.7, 18.0), (4.6, 0.0)])
    K("steer", [(0, 0), (10.8, 0), (11.6, 0.42), (36.0, 0.42)])


def moods(env):
    for t, mood in ((0.0, "black"), (1.6, "dark"), (7.5, "dark"), (9.5, "reveal"), (11.9, "reveal"), (12.15, "hero"),
                    (31.4, "hero"), (32.2, "cabin"), (35.9, "cabin"), (36.2, "hero"), (39.0, "hero"), (39.9, "black")):
        environment.apply_mood(env, mood, frame=F(t))


# shot: name -> list of (time, camera position, target), lens, linear?
SHOTS = {
    "s01_reveal": ([(0.0, (7.6, 5.6, 1.7), (0, 0, 0.5)), (2.0, (7.2, 5.2, 1.6), (0, 0, 0.5))], 40),
    "s02_assembly_orbit": ([(2.0, (6.6, 4.9, 2.3), (0, 0, 0.6)), (3.5, (7.9, 2.3, 2.4), (0, 0, 0.6)),
                            (5.0, (8.1, -0.8, 2.5), (0, 0, 0.6)), (6.5, (7.2, -3.8, 2.5), (0, 0, 0.6)),
                            (8.0, (5.4, -6.0, 2.4), (0, 0, 0.6))], 38),
    "s03_assembly_close": ([(8.0, (-5.8, 4.6, 1.3), (-0.2, 0, 0.65)), (12.0, (-4.4, 5.3, 2.3), (-0.2, 0, 0.65))], 38),
    "s04_front34": ([(12.0, (6.5, 3.7, 0.78), (0.6, 0, 0.55)), (16.0, (5.3, 3.0, 0.72), (0.6, 0, 0.55))], 55),
    "s05_side_track": ([(16.0, (1.9, 7.6, 0.8), (1.5, 0, 0.6)), (20.0, (-1.5, 7.6, 0.8), (-1.2, 0, 0.6))], 70),
    "s06_rear34": ([(20.0, (-6.3, 3.5, 0.9), (-1.0, 0, 0.6)), (24.0, (-5.5, 2.5, 1.9), (-1.0, 0, 0.6))], 50),
    "s07_wheel_macro": ([(24.0, (2.3, 2.5, 0.45), (1.37, 0.85, 0.37)), (26.0, (1.95, 2.7, 0.52), (1.37, 0.85, 0.37))], 85),
    "s08_grille_macro": ([(26.0, (4.3, 0.7, 0.5), (2.3, 0, 0.43)), (28.0, (3.8, -0.4, 0.56), (2.3, 0, 0.43))], 85),
    "s09_doors_open": ([(28.0, (7.2, 1.4, 1.3), (0.3, 0, 0.95)), (32.0, (6.3, 2.7, 1.75), (0.3, 0, 0.95))], 40),
    "s10_cabin_wheel": ([(32.0, (0.20, 1.80, 1.18), (0.55, 0.37, 0.74)), (34.0, (-0.02, 1.08, 1.04), (0.55, 0.37, 0.74))], 28),
    "s11_cabin_console": ([(34.0, (-0.44, 0.06, 1.02), (0.75, 0.0, 0.62)), (36.0, (-0.27, 0.0, 0.94), (0.75, 0.0, 0.62))], 20),
    "s12_finale": ([(36.0, (5.1, 3.9, 1.1), (0.1, 0, 0.55)), (40.0, (7.7, 5.7, 1.75), (0.1, 0, 0.55))], 50),
}


def cameras(scene):
    col = util.get_collection("CAM_Shots")
    cams = {}
    for name, start, end in TL.SHOTS:
        keys, lens = SHOTS[name]
        cam = bpy.data.objects.new("CAM_" + name, bpy.data.cameras.new("CAM_" + name))
        tgt = bpy.data.objects.new("CAM_" + name + "_T", None)
        col.objects.link(cam); col.objects.link(tgt)
        cam.data.lens = lens; cam.data.clip_start = 0.03; cam.data.clip_end = 200; cam.data.sensor_width = 36
        c = cam.constraints.new('TRACK_TO')
        c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
        for t, pos, look in keys:
            cam.location = pos; cam.keyframe_insert("location", frame=F(t))
            tgt.location = look; tgt.keyframe_insert("location", frame=F(t))
        if len(keys) == 2:
            _linear(cam); _linear(tgt)
        mk = scene.timeline_markers.new(name, frame=F(start))
        mk.camera = cam
        cams[name] = cam
    scene.camera = cams[TL.SHOTS[0][0]]
    return cams


def setup_render(scene, res=(1280, 720), samples=32):
    preview.setup_cycles(scene, samples=samples, res=res, threads=0)
    scene.render.fps = TL.FPS
    scene.frame_start, scene.frame_end = 1, TL.FRAMES
    scene.render.use_persistent_data = True
    scene.render.use_motion_blur = False
    scene.cycles.adaptive_threshold = 0.04
    scene.cycles.light_sampling_threshold = 0.02
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.0


def build(car, env, res=(1280, 720), samples=32):
    scene = car["scene"]
    sizes = assembly(car["rig"]["root"])
    controls(car["rig"]["ctrl"])
    moods(env)
    cams = cameras(scene)
    setup_render(scene, res, samples)
    return dict(groups=sizes, cameras=cams)
