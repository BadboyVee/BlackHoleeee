"""Lagos 2090 - shared Blender scene plumbing (scene reset, asset library access,
world / sun / camera, Cycles settings, frame rendering).

Everything is metres, Z-up. Works with Blender 4.2+ (developed on 5.3, headless).
"""
import bpy, math, os, random, sys, time
from pathlib import Path
from mathutils import Vector, Matrix, Euler

ROOT = Path(__file__).resolve().parent.parent.parent
LIB = ROOT / "blender" / "assets_lib.blend"
RENDERS = ROOT / "renders"
FPS = 24
SHOT_FRAMES = 90
W, H = 1920, 1080

_templates = {}


# ----------------------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _templates.clear(); _centres.clear()
    from . import mats
    mats.clear_cache()
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, SHOT_FRAMES
    return sc


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def link(obj, collection=None):
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


# ----------------------------------------------------------------------------- assets
def lib_names():
    with bpy.data.libraries.load(str(LIB)) as (src, dst):
        return list(src.objects)


_lib_index = None


def asset(name, piece=None):
    """Return template mesh objects (not linked to the scene) for a library asset.
    name = collection name in assets_lib.blend, e.g. 'old-tyre' or 'k-van'."""
    global _lib_index
    key = name
    if key not in _templates:
        if _lib_index is None:
            _lib_index = lib_names()
        want = [n for n in _lib_index if n.startswith(name + "__")]
        if not want:
            raise KeyError(f"asset {name} not in library")
        with bpy.data.libraries.load(str(LIB), link=False) as (src, dst):
            dst.objects = want
        _templates[key] = [o for o in dst.objects if o is not None]
        for img in bpy.data.images:  # appended relative paths resolve against the lib
            if img.filepath.startswith("//") and img.library is None and not img.get("_fixed"):
                img.filepath = str((LIB.parent / img.filepath[2:]).resolve())
                img["_fixed"] = 1
    objs = _templates[key]
    if piece is not None:
        if isinstance(piece, int):
            return [objs[piece % len(objs)]]
        return [o for o in objs if piece in o.name]
    return objs


def inst(tmpl, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, collection=None, name=None):
    """Instance a template object (shares mesh data)."""
    o = bpy.data.objects.new(name or tmpl.name.split("__")[-1], tmpl.data)
    o.location = loc
    o.rotation_euler = rot
    o.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale
    link(o, collection)
    return o


def place(name, loc=(0, 0, 0), rz=0.0, scale=1.0, collection=None, piece=None, rot=None):
    """Instance all pieces of an asset as one group (single-piece assets mostly)."""
    out = []
    for t in asset(name, piece):
        off = Vector(t.get("src_offset", (0, 0, 0))) if piece is None and len(asset(name)) > 1 else Vector()
        if piece is None and len(asset(name)) > 1:
            # keep the authored arrangement of multi-part props relative to the set centre
            c = _set_centre(name)
            off = (off - c)
            m = Matrix.Rotation(rz, 4, "Z")
            p = Vector(loc) + m @ (off * (scale if isinstance(scale, (int, float)) else 1.0))
        else:
            p = Vector(loc)
        out.append(inst(t, p, rot or (0, 0, rz), scale, collection))
    return out


_centres = {}


def _set_centre(name):
    if name not in _centres:
        objs = asset(name)
        mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
        for t in objs:
            off = Vector(t.get("src_offset", (0, 0, 0)))
            for c in t.bound_box:
                w = off + Vector(c)
                mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
        _centres[name] = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    return _centres[name]


def join(objs, name):
    """Join real objects into one mesh object."""
    objs = [o for o in objs if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        if o.data.users > 1:
            o.data = o.data.copy()
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


# ----------------------------------------------------------------------------- world
HDRI = {
    "fire": ("hdri/the_sky_is_on_fire_4k.exr", 0.667),   # u of the bright glow
    "sunrise": ("hdri/spruit_sunrise_4k.exr", 0.599),
}


def sun_dir(az_deg, el_deg):
    """Unit vector pointing from the scene towards the sun. az: 0=+X, 90=+Y."""
    a, e = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def world(hdri="fire", sun_az=90.0, sun_el=8.0, sky_strength=1.0, sun_strength=4.0,
          sun_color=(1.0, 0.62, 0.33), sun_size_deg=1.2, haze_color=(1.0, 0.66, 0.42),
          haze_top_deg=10.0, disc_strength=60.0, sky_tint=(1.0, 1.0, 1.0), horizon_deg=None):
    """HDRI sky (lighting + visible upper sky), haze gradient that hides the HDRI's own
    horizon from the camera, an emissive sun disc for camera rays, and a real sun lamp."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    path, u_glow = HDRI[hdri]
    tc = N("ShaderNodeTexCoord")
    mp = N("ShaderNodeMapping")
    # Blender equirect: u = atan2(y, -x)/(2pi) + 0.5  ->  azimuth of column u:
    glow_az = math.degrees(math.pi - (u_glow - 0.5) * 2 * math.pi)
    mp.inputs["Rotation"].default_value = (0, 0, -math.radians(sun_az - glow_az))
    env = N("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(ROOT / path), check_existing=True)
    L(tc.outputs["Generated"], mp.inputs["Vector"]); L(mp.outputs["Vector"], env.inputs["Vector"])
    tint = N("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    L(env.outputs["Color"], tint.inputs["A"]); tint.inputs["B"].default_value = (*sky_tint, 1)
    # elevation of the view ray
    sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Generated"], sep.inputs[0])
    elev = N("ShaderNodeMath"); elev.operation = "ARCSINE"; L(sep.outputs["Z"], elev.inputs[0])
    ramp = N("ShaderNodeMapRange"); ramp.interpolation_type = "SMOOTHERSTEP"
    L(elev.outputs[0], ramp.inputs["Value"])
    ramp.inputs["From Min"].default_value = math.radians(haze_top_deg)
    ramp.inputs["From Max"].default_value = math.radians(0.5)
    ramp.inputs["To Min"].default_value = 0.0; ramp.inputs["To Max"].default_value = 1.0
    lp = N("ShaderNodeLightPath")
    camfac = N("ShaderNodeMath"); camfac.operation = "MULTIPLY"
    L(ramp.outputs[0], camfac.inputs[0]); L(lp.outputs["Is Camera Ray"], camfac.inputs[1])
    # haze colour brightens towards the sun azimuth
    sd = sun_dir(sun_az, 0)
    dot = N("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    nrm = N("ShaderNodeVectorMath"); nrm.operation = "NORMALIZE"; L(tc.outputs["Generated"], nrm.inputs[0])
    L(nrm.outputs[0], dot.inputs[0]); dot.inputs[1].default_value = sd
    toward = N("ShaderNodeMapRange"); L(dot.outputs["Value"], toward.inputs["Value"])
    toward.inputs["From Min"].default_value = -0.2; toward.inputs["From Max"].default_value = 1.0
    toward.inputs["To Min"].default_value = 0.35; toward.inputs["To Max"].default_value = 1.6
    hz = N("ShaderNodeMix"); hz.data_type = "RGBA"; hz.blend_type = "MULTIPLY"; hz.inputs["Factor"].default_value = 1.0
    hz.inputs["A"].default_value = (*haze_color, 1); L(toward.outputs[0], hz.inputs["B"])
    hzs = N("ShaderNodeVectorMath"); hzs.operation = "SCALE"
    L(toward.outputs[0], hzs.inputs["Scale"]); hzs.inputs[0].default_value = haze_color
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
    L(camfac.outputs[0], mix.inputs["Factor"]); L(tint.outputs["Result"], mix.inputs["A"]); L(hzs.outputs[0], mix.inputs["B"])
    # sun disc + halo for camera rays
    sdir = sun_dir(sun_az, sun_el)
    dot2 = N("ShaderNodeVectorMath"); dot2.operation = "DOT_PRODUCT"
    L(nrm.outputs[0], dot2.inputs[0]); dot2.inputs[1].default_value = sdir
    ang = N("ShaderNodeMath"); ang.operation = "ARCCOSINE"; L(dot2.outputs["Value"], ang.inputs[0])
    disc = N("ShaderNodeMapRange"); disc.interpolation_type = "SMOOTHSTEP"; L(ang.outputs[0], disc.inputs["Value"])
    disc.inputs["From Min"].default_value = math.radians(sun_size_deg * 0.5 * 1.25)
    disc.inputs["From Max"].default_value = math.radians(sun_size_deg * 0.5 * 0.85)
    halo = N("ShaderNodeMapRange"); halo.interpolation_type = "SMOOTHERSTEP"; L(ang.outputs[0], halo.inputs["Value"])
    halo.inputs["From Min"].default_value = math.radians(22.0); halo.inputs["From Max"].default_value = 0.0
    hpow = N("ShaderNodeMath"); hpow.operation = "POWER"; L(halo.outputs[0], hpow.inputs[0]); hpow.inputs[1].default_value = 3.0
    hmul = N("ShaderNodeMath"); hmul.operation = "MULTIPLY"; L(hpow.outputs[0], hmul.inputs[0]); hmul.inputs[1].default_value = disc_strength * 0.012
    dmul = N("ShaderNodeMath"); dmul.operation = "MULTIPLY"; L(disc.outputs[0], dmul.inputs[0]); dmul.inputs[1].default_value = disc_strength
    dsum = N("ShaderNodeMath"); L(hmul.outputs[0], dsum.inputs[0]); L(dmul.outputs[0], dsum.inputs[1])
    dcam = N("ShaderNodeMath"); dcam.operation = "MULTIPLY"; L(dsum.outputs[0], dcam.inputs[0]); L(lp.outputs["Is Camera Ray"], dcam.inputs[1])
    dcol = N("ShaderNodeVectorMath"); dcol.operation = "SCALE"
    dcol.inputs[0].default_value = (1.0, 0.72, 0.42); L(dcam.outputs[0], dcol.inputs["Scale"])
    add = N("ShaderNodeVectorMath"); add.operation = "ADD"
    L(mix.outputs["Result"], add.inputs[0]); L(dcol.outputs[0], add.inputs[1])
    bg = N("ShaderNodeBackground"); bg.inputs["Strength"].default_value = sky_strength
    L(add.outputs[0], bg.inputs["Color"])
    out = N("ShaderNodeOutputWorld"); L(bg.outputs[0], out.inputs["Surface"])
    # sun lamp
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = sun_strength
    sun.color = sun_color
    sun.angle = math.radians(sun_size_deg)
    so = link(bpy.data.objects.new("Sun", sun))
    so.rotation_euler = (-sdir).to_track_quat("-Z", "Y").to_euler()
    ms = w.mist_settings
    ms.start = 0.0; ms.depth = 1000.0; ms.falloff = "LINEAR"
    return w, so


# ----------------------------------------------------------------------------- camera
def camera(loc, look_at, lens=35.0, fstop=2.8, focus=None, sensor=36.0, roll=0.0):
    cam = bpy.data.cameras.new("Cam")
    cam.lens = lens
    cam.sensor_width = sensor
    cam.clip_start, cam.clip_end = 0.05, 20000
    co = link(bpy.data.objects.new("Cam", cam))
    co.location = loc
    d = Vector(look_at) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if roll:
        co.rotation_euler.rotate_axis("Z", math.radians(roll))
    cam.dof.use_dof = fstop is not None
    if fstop is not None:
        cam.dof.aperture_fstop = fstop
        cam.dof.focus_distance = focus if focus is not None else d.length
        cam.dof.aperture_blades = 0
        cam.dof.aperture_ratio = 1.0
    bpy.context.scene.camera = co
    return co


# ----------------------------------------------------------------------------- render
def render_settings(samples=8, motion_blur=False, res_pct=100, bounces=4, diffuse=2, glossy=2, transparent=8,
                    clamp_indirect=4.0, fast_gi=1, ao_distance=5.0):
    """Cycles on CPU. The machine this was built on has 4 slow cores and no GPU, so the
    budget is ~8 spp + OpenImageDenoise per frame with an animated seed; scripts/post.py
    then runs a temporal bilateral filter (static camera), which converges everything
    that does not move and leaves moving foliage / water / cloth untouched."""
    sc = bpy.context.scene
    r = sc.render
    r.engine = "CYCLES"
    c = sc.cycles
    c.device = "CPU"
    c.samples = samples
    c.use_adaptive_sampling = False
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.denoising_prefilter = "FAST"
    c.seed = 2090
    c.use_animated_seed = True
    c.max_bounces = bounces
    c.diffuse_bounces = diffuse
    c.glossy_bounces = glossy
    c.transmission_bounces = 4
    c.transparent_max_bounces = transparent
    c.volume_bounces = 0
    c.sample_clamp_indirect = clamp_indirect
    c.sample_clamp_direct = 0.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 0.8
    c.use_light_tree = False
    if fast_gi:
        c.use_fast_gi = True
        c.fast_gi_method = "REPLACE"
        c.ao_bounces_render = fast_gi
        c.ao_bounces = fast_gi
        if sc.world:
            sc.world.light_settings.distance = ao_distance
            sc.world.light_settings.ao_factor = 1.0
    c.pixel_filter_type = "BLACKMAN_HARRIS"
    c.filter_width = 1.5
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, res_pct
    r.use_persistent_data = True
    r.threads_mode = "AUTO"
    r.use_motion_blur = motion_blur
    r.motion_blur_shutter = 0.5
    r.film_transparent = False
    r.use_file_extension = True
    vl = sc.view_layers[0]
    vl.use_pass_mist = True
    ims = r.image_settings
    try:
        ims.media_type = "MULTI_LAYER_IMAGE"
    except Exception:
        pass
    ims.file_format = "OPEN_EXR_MULTILAYER"
    ims.color_depth = "16"
    ims.exr_codec = "DWAA"
    sc.view_settings.view_transform = "Standard"
    sc.display_settings.display_device = "sRGB"
    return sc


def save_blend(name):
    p = ROOT / "blender" / f"{name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(p), compress=True)
    return p


def render_frames(shot, frames, animate=None, res_pct=100, samples=None, out_dir=None, overwrite=False):
    """Render frames (1-based, shot-local) to renders/<shot>/f####.exr, skipping
    frames already on disk so an interrupted render resumes."""
    sc = bpy.context.scene
    sc.render.resolution_percentage = res_pct
    if samples:
        sc.cycles.samples = samples
    out = Path(out_dir) if out_dir else RENDERS / shot
    out.mkdir(parents=True, exist_ok=True)
    for f in frames:
        fp = out / f"f{f:04d}.exr"
        if fp.exists() and fp.stat().st_size > 1000 and not overwrite:
            continue
        t = time.time()
        sc.frame_set(f)
        if animate:
            animate(sc, f)
        sc.render.filepath = str(fp)
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {shot} {f} {time.time() - t:.1f}s", flush=True)


def argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
