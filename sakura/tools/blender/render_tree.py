"""Open the tree the page exports ("Export tree for Blender") and render it with Cycles.

The page writes sakura-tree.glb: the wood, every spray of blossom, the fallen petals, the knoll, the lantern and
the stones, as plain meshes with ordinary materials. This script imports it, gives the petals the translucency
they have on the page, puts the sun where it stands at the hour asked for, and sets the camera on the page's
opening view.

    python tools/blender/render_tree.py sakura-tree.glb render.png [--hour 16.9] [--samples 96] [--size 1280 720]
    blender --python tools/blender/render_tree.py -- sakura-tree.glb          (opens it in Blender, ready to look at)
"""

import math
import os
import sys

import bpy
from mathutils import Vector


def args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    opt = {'hour': 16.9, 'samples': 96, 'size': (1280, 720), 'files': []}
    i = 0
    while i < len(a):
        if a[i] == '--hour':
            opt['hour'] = float(a[i + 1]); i += 2
        elif a[i] == '--samples':
            opt['samples'] = int(a[i + 1]); i += 2
        elif a[i] == '--size':
            opt['size'] = (int(a[i + 1]), int(a[i + 2])); i += 3
        else:
            opt['files'].append(a[i]); i += 1
    return opt


def to_blender(x, y, z):
    """three.js is y-up, Blender z-up: the glTF importer turns (x, y, z) into (x, -z, y)."""
    return Vector((x, -z, y))


def sun_direction(hours):
    """The same sun as the page: up at 06:00 in the east, 58 degrees high at noon."""
    ang, tilt = (hours - 6) / 12 * math.pi, math.radians(32)
    return to_blender(math.cos(ang), math.sin(ang) * math.cos(tilt), math.sin(ang) * math.sin(tilt))


def translucent_petals(mat):
    """Thin petals pass light: mix a translucent lobe into the imported material, and keep its cut-out."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    colour = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
    alpha = bsdf.inputs['Alpha'].links[0].from_socket if bsdf.inputs['Alpha'].links else None
    if alpha is not None:
        nt.links.remove(bsdf.inputs['Alpha'].links[0])
        bsdf.inputs['Alpha'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.6
    thin = nt.nodes.new('ShaderNodeBsdfTranslucent')
    if colour is not None:
        nt.links.new(colour, thin.inputs['Color'])
    both = nt.nodes.new('ShaderNodeMixShader')
    both.inputs[0].default_value = 0.45
    nt.links.new(bsdf.outputs[0], both.inputs[1])
    nt.links.new(thin.outputs[0], both.inputs[2])
    surface = both.outputs[0]
    if alpha is not None:
        clear = nt.nodes.new('ShaderNodeBsdfTransparent')
        cut = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(alpha, cut.inputs[0])
        nt.links.new(clear.outputs[0], cut.inputs[1])
        nt.links.new(surface, cut.inputs[2])
        surface = cut.outputs[0]
    nt.links.new(surface, out.inputs['Surface'])


def lift_bark(mat, value=1.25):
    """Cherry bark is dark, and under the crown it is in shade: lift it as the page does, so it keeps its detail."""
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    if not bsdf.inputs['Base Color'].links:
        return
    colour = bsdf.inputs['Base Color'].links[0].from_socket
    hsv = nt.nodes.new('ShaderNodeHueSaturation')
    hsv.inputs['Value'].default_value = value
    nt.links.new(colour, hsv.inputs['Color'])
    nt.links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])


def main():
    opt = args()
    if not opt['files']:
        raise SystemExit(__doc__)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(opt['files'][0]))
    sc = bpy.context.scene
    for mat in bpy.data.materials:
        if mat.name.startswith('Blossom') and mat.node_tree:
            translucent_petals(mat)
        elif mat.name.startswith('Bark') and mat.node_tree:
            lift_bark(mat)

    # the sun, and the sky it lights
    sun_dir = sun_direction(opt['hour'])
    sun_dir.z = max(sun_dir.z, 0.03)
    sun_dir.normalize()
    elevation = math.degrees(math.asin(sun_dir.z))
    warm = max(0.0, min(1.0, (elevation - 2) / 28))
    light = bpy.data.lights.new('Sun', 'SUN')
    light.energy = 4.0 + 12.0 * warm
    light.color = (1.0, 0.55 + 0.4 * warm, 0.3 + 0.62 * warm)
    light.angle = math.radians(0.6)
    lamp = bpy.data.objects.new('Sun', light)
    sc.collection.objects.link(lamp)
    lamp.rotation_euler = sun_dir.to_track_quat('Z', 'Y').to_euler()

    world = bpy.data.worlds.new('Sky')
    sc.world = world
    if world.node_tree is None:
        world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky')
    kinds = [e.identifier for e in sky.bl_rna.properties['sky_type'].enum_items]
    sky.sky_type = next(k for k in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING', 'HOSEK_WILKIE') if k in kinds)
    if hasattr(sky, 'sun_disc'):
        sky.sun_disc = False                                   # the lamp is the sun; the sky is only the sky
        sky.sun_elevation = math.radians(elevation)
        sky.sun_rotation = math.atan2(sun_dir.x, sun_dir.y)
    nt.links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.22

    # the page's opening view
    base = 1.7845                                              # the height of the knoll under the trunk
    cam = bpy.data.cameras.new('Camera')
    cam.sensor_fit = 'VERTICAL'
    cam.sensor_height = 24
    cam.lens = 12 / math.tan(math.radians(38) / 2)
    cam.clip_start, cam.clip_end = 0.1, 4000
    eye = bpy.data.objects.new('Camera', cam)
    sc.collection.objects.link(eye)
    eye.location = to_blender(21.0, base + 1.9, 7.4)
    eye.rotation_euler = (to_blender(0.2, base + 4.7, 0) - eye.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = eye

    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = opt['samples']
    sc.cycles.transparent_max_bounces = 256                    # a ray may cross a great many petals' empty corners
    sc.cycles.max_bounces = 16
    sc.cycles.diffuse_bounces = 8
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = opt['size']
    sc.render.resolution_percentage = 100
    if len(opt['files']) > 1:
        sc.render.image_settings.file_format = 'PNG'
        sc.render.filepath = os.path.abspath(opt['files'][1])
        bpy.ops.render.render(write_still=True)
        print('rendered', sc.render.filepath)


if __name__ == '__main__':
    main()
