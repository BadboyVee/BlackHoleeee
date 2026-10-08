"""Shared helpers for the Blender asset scripts (run with the `bpy` module).

Everything here is headless: scenes are built from Python, rendered with
Cycles on the CPU, and the render passes are read back as numpy arrays
through the compositor's file output (32-bit EXR), then packed into the
game's textures with Pillow.
"""

import math
import os
import shutil
import tempfile

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ASSETS = os.path.join(ROOT, 'assets')


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.use_denoising = False
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('world')
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    return sc


def rng(seed):
    return np.random.default_rng(seed)


def mesh_object(name, verts, faces, uvs=None, colors=None, smooth=True, material=None, normals=None):
    """Mesh from numpy arrays. uvs: per-vertex (V,2); colors: per-vertex (V,4)."""
    verts = np.asarray(verts, np.float32)
    faces = [list(f) for f in faces]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces)
    me.validate()
    if uvs is not None:
        uvs = np.asarray(uvs, np.float32)
        layer = me.uv_layers.new(name='UVMap')
        loop_v = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get('vertex_index', loop_v)
        layer.data.foreach_set('uv', uvs[loop_v].ravel())
    if colors is not None:
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', np.asarray(colors, np.float32).ravel())
    me.polygons.foreach_set('use_smooth', np.full(len(me.polygons), smooth))
    if normals is not None:
        loop_v = np.zeros(len(me.loops), np.int32)
        me.loops.foreach_get('vertex_index', loop_v)
        me.normals_split_custom_set(np.asarray(normals, np.float32)[loop_v].tolist())
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if material is not None:
        ob.data.materials.append(material)
    return ob


def ortho_camera(center, size_x, size_y, res_x, res_y, height=50.0):
    """Orthographic camera looking straight down (-Z), image x = +X, image y = +Y."""
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = max(size_x, size_y)
    cam.clip_start = 0.01
    cam.clip_end = height * 2 + 100
    ob = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(ob)
    ob.location = (center[0], center[1], height)
    ob.rotation_euler = (0, 0, 0)
    sc.camera = ob
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.resolution_percentage = 100
    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1
    return ob


def render_passes(samples=16, passes=('Alpha', 'DiffCol', 'Normal', 'Depth', 'AO', 'Image'), ao_distance=0.1):
    """Render the scene; returns {pass: float32 array (H, W, C)} with row 0 at the TOP of the image."""
    sc = bpy.context.scene
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.max_bounces = 4
    sc.cycles.transparent_max_bounces = 64
    sc.world.light_settings.distance = ao_distance
    vl = sc.view_layers[0]
    vl.use_pass_diffuse_color = 'DiffCol' in passes
    vl.use_pass_normal = 'Normal' in passes
    vl.use_pass_z = 'Depth' in passes
    vl.use_pass_ambient_occlusion = 'AO' in passes
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers')
    tmp = tempfile.mkdtemp(prefix='blpass_')
    fo = nt.nodes.new('CompositorNodeOutputFile')
    fo.base_path = tmp
    fo.format.file_format = 'OPEN_EXR'
    fo.format.color_depth = '32'
    fo.format.exr_codec = 'ZIP'
    fo.file_slots.clear()
    for name in passes:
        fo.file_slots.new(name)
        nt.links.new(rl.outputs[name], fo.inputs[name])
    sc.render.use_compositing = True
    bpy.ops.render.render(write_still=False)
    out = {}
    W, H = sc.render.resolution_x, sc.render.resolution_y
    for name in passes:
        f = [x for x in os.listdir(tmp) if x.startswith(name)][0]
        im = bpy.data.images.load(os.path.join(tmp, f))
        px = np.empty(W * H * 4, np.float32)
        im.pixels.foreach_get(px)
        bpy.data.images.remove(im)
        # blender images are bottom-up
        out[name] = px.reshape(H, W, 4)[::-1].copy()
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def dilate(rgb, alpha, iterations=64):
    """Bleed colour from covered texels into empty ones (no dark mip fringes)."""
    rgb = rgb.copy()
    known = alpha > 0.02
    for _ in range(iterations):
        if known.all():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros(known.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            k = np.roll(np.roll(known, dy, 0), dx, 1)
            c = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += c * k[..., None]
            cnt += k
        grow = (~known) & (cnt > 0)
        rgb[grow] = acc[grow] / cnt[grow][:, None]
        known = known | grow
    # anything never reached: the mean colour
    if not known.all():
        rgb[~known] = rgb[known].mean(0)
    return rgb


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def to_u8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def save_image(path, arr_u8, lossless=False, quality=92):
    from PIL import Image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = 'RGBA' if arr_u8.shape[-1] == 4 else 'RGB'
    im = Image.fromarray(arr_u8, mode)
    if path.endswith('.webp'):
        im.save(path, 'WEBP', lossless=lossless, quality=quality if not lossless else 100, method=6, alpha_quality=100, exact=True)
    else:
        im.save(path)
    return os.path.getsize(path)


def principled(name, color=(0.5, 0.5, 0.5), roughness=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = roughness
    return m


def look_rotation(forward, up):
    """Rotation matrix whose -Z points along `forward` and +Y along `up` (blender camera convention)."""
    f = Vector(forward).normalized()
    r = f.cross(Vector(up)).normalized()
    u = r.cross(f).normalized()
    return Matrix((r, u, -f)).transposed()
