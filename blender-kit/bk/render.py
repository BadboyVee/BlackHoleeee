"""bk.render -- Cycles setup, physical sky, cameras, compositor glare, still rendering."""
import math
import os
import time

import bpy
from mathutils import Vector

from .core import link, rad


def setup(sc=None, res=(1920, 1080), samples=256, noise=0.03, exposure=0.0, look='AgX - Medium High Contrast',
          bounces=(8, 4, 4, 8), clamp=8.0, threads=0, min_samples=24):
    sc = sc or bpy.context.scene
    sc.render.engine = 'CYCLES'
    c = sc.cycles
    c.device = 'CPU'
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = noise
    c.adaptive_min_samples = min_samples
    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    c.denoising_prefilter = 'ACCURATE'
    try:
        c.denoising_quality = 'HIGH'
    except Exception:
        pass
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces = bounces
    c.transparent_max_bounces = 16
    c.volume_bounces = 1
    c.sample_clamp_indirect = clamp
    c.sample_clamp_direct = 0.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 0.6
    c.use_light_tree = True
    c.filter_width = 1.5
    r = sc.render
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.use_persistent_data = True
    if threads:
        r.threads_mode = 'FIXED'
        r.threads = threads
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGB'
    r.image_settings.compression = 30
    vs = sc.view_settings
    vs.view_transform = 'AgX'
    try:
        vs.look = look
    except Exception:
        vs.look = 'None'
    vs.exposure = exposure
    vs.gamma = 1.0
    return sc


def sky(sc=None, elev=35.0, az=200.0, strength=1.0, sun_intensity=1.0, sun_size=0.545, air=1.0, aerosol=1.0,
        ozone=1.0, altitude=0.0, sun_disc=True, name="Sky"):
    """Physical multiple-scattering sky.  az: compass bearing of the sun in degrees
    (0 = +Y / north, 90 = +X / east), elev: degrees above the horizon."""
    sc = sc or bpy.context.scene
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    sc.world = w
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    s = nt.nodes.new('ShaderNodeTexSky')
    s.sky_type = 'MULTIPLE_SCATTERING'
    s.sun_disc = sun_disc
    s.sun_size = rad(sun_size)
    s.sun_intensity = sun_intensity
    s.sun_elevation = rad(elev)
    s.sun_rotation = rad(az)
    s.altitude = altitude
    s.air_density = air
    s.aerosol_density = aerosol
    s.ozone_density = ozone
    bg.inputs['Strength'].default_value = strength
    nt.links.new(s.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    w["sky_node"] = s.name
    return w


def sun_dir(elev, az):
    """Unit vector pointing from the ground toward the sun for the same convention as sky()."""
    e, a = rad(elev), rad(az)
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))


def sun_lamp(elev=35.0, az=200.0, strength=4.0, angle=0.6, color=(1.0, 0.95, 0.88), name="Sun", c=None):
    l = bpy.data.lights.new(name, 'SUN')
    l.energy = strength
    l.angle = rad(angle)
    l.color = color
    o = bpy.data.objects.new(name, l)
    d = sun_dir(elev, az)
    o.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    o.location = d * 60
    link(o, c)
    return o


def camera(name, loc, target, lens=24.0, sensor=36.0, arch=False, dof=None, fstop=2.8, clip=(0.05, 3000.0),
           c=None, roll=0.0, shift=(0.0, 0.0)):
    """arch=True keeps the camera level and frames the target with lens shift, so verticals stay vertical."""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start, cd.clip_end = clip
    o = bpy.data.objects.new(name, cd)
    loc = Vector(loc)
    tgt = Vector(target)
    d = tgt - loc
    if arch:
        flat = Vector((d.x, d.y, 0.0))
        o.rotation_euler = (-flat).to_track_quat('Z', 'Y').to_euler()
        pitch = math.atan2(d.z, flat.length)
        cd.shift_y = lens * math.tan(pitch) / sensor + shift[1]
        cd.shift_x = shift[0]
    else:
        o.rotation_euler = (-d).to_track_quat('Z', 'Y').to_euler()
        cd.shift_x, cd.shift_y = shift
    if roll:
        o.rotation_euler.rotate_axis('Z', rad(roll))
    o.location = loc
    if dof is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = dof if isinstance(dof, (int, float)) else (Vector(dof) - loc).length
        cd.dof.aperture_fstop = fstop
    link(o, c)
    return o


def compositor(sc=None, bloom=0.25, threshold=1.5, size=0.5, vignette=0.0):
    """Soft bloom on highlights (lamps, sun glints).  Silently skipped if the API differs."""
    sc = sc or bpy.context.scene
    try:
        ng = bpy.data.node_groups.new("bk_comp", "CompositorNodeTree")
        ng.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new("CompositorNodeRLayers")
        go = ng.nodes.new("NodeGroupOutput")
        cur = rl.outputs['Image']
        if bloom > 0:
            gl = ng.nodes.new("CompositorNodeGlare")
            gl.inputs['Type'].default_value = 'Bloom'
            gl.inputs['Quality'].default_value = 'High'
            gl.inputs['Threshold'].default_value = threshold
            gl.inputs['Strength'].default_value = bloom
            gl.inputs['Size'].default_value = size
            ng.links.new(cur, gl.inputs['Image'])
            cur = gl.outputs[0]
        ng.links.new(cur, go.inputs[0])
        sc.compositing_node_group = ng
        sc.render.use_compositing = True
        return ng
    except Exception as e:  # pragma: no cover
        print("compositor setup skipped:", e)
        return None


def render(path, cam=None, sc=None, res=None, samples=None, exposure=None, noise=None, quality=93, look=None,
           seed=None):
    """Render a still.  Extension decides the format (.png / .jpg)."""
    sc = sc or bpy.context.scene
    if cam is not None:
        sc.camera = cam
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    if samples:
        sc.cycles.samples = samples
    if noise:
        sc.cycles.adaptive_threshold = noise
    if exposure is not None:
        sc.view_settings.exposure = exposure
    if look:
        sc.view_settings.look = look
    if seed is not None:
        sc.cycles.seed = seed
    ext = os.path.splitext(path)[1].lower()
    ims = sc.render.image_settings
    if ext in ('.jpg', '.jpeg'):
        ims.file_format = 'JPEG'
        ims.quality = quality
    else:
        ims.file_format = 'PNG'
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    print(f"[render] {os.path.basename(path)}  {sc.render.resolution_x}x{sc.render.resolution_y}  "
          f"{sc.cycles.samples}spp  {dt:.1f}s", flush=True)
    return dt


def hide_collections(names, hide=True):
    """Exclude heavy collections from a render (e.g. exterior greenery for interior shots)."""
    for n in names:
        c = bpy.data.collections.get(n)
        if c:
            c.hide_render = hide
