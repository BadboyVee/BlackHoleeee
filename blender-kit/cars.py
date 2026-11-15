"""Real-world car models as instancable library collections.

bmw()                     Blender Foundation's BMW 1M benchmark car (CC0, Mike Pan)
gz("suv"|"hatchback"|"prius_hybrid"|"bus")   OSRF Gazebo models (photo-textured, low poly:
                          for street and background use)
ferrari(), concept()      three.js Ferrari 458 (CC-BY) and Khronos CarConcept (CC-BY)
Each returns a collection whose origin is under the car's centre, wheels on z=0,
nose toward +X.
"""
import glob
import math
import os

import bpy
from mathutils import Matrix, Vector

import kit

CARS = os.environ.get("CARS_DIR", "/home/user/assets/cars")
_cache = {}


def _lib(name):
    root = kit.coll("LIB", hide=True)
    c = bpy.data.collections.new("LIB_" + name)
    root.children.link(c)
    return c


def _wrap(name, objs, length, yaw=0.0, colls=()):
    """Parent the imported roots to one empty, turn the nose to +X, scale to a real
    length, drop the wheels onto z=0."""
    c = _lib(name)
    for o in objs:                      # measure while the objects are in the live scene
        kit.link(o, bpy.context.scene.collection)
        for attr in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_shadow"):
            try:
                setattr(o, attr, True)
            except Exception:
                pass
        o.hide_render = False
    bpy.context.view_layer.update()
    meshes = [o for o in objs if o.type == "MESH"]
    lo, hi = kit._bbox(meshes)
    size = hi - lo
    if size.z > max(size.x, size.y):          # model lying on its nose: stand it up
        for o in objs:
            if o.parent is None:
                o.matrix_world = Matrix.Rotation(math.pi / 2, 4, "X") @ o.matrix_world
        bpy.context.view_layer.update()
        lo, hi = kit._bbox(meshes)
        size = hi - lo
    L = max(size.x, size.y)
    s = length / L
    root = bpy.data.objects.new(name + "_root", None)
    bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    root.matrix_world = (Matrix.Rotation(yaw, 4, "Z") @ Matrix.Scale(s, 4) @ Matrix.Translation((-cx, -cy, -lo.z)))
    for o in objs + [root]:
        kit.link(o, c)
    c["size"] = (length, min(size.x, size.y) * s, size.z * s)
    return c


def bmw(color=None):
    key = "bmw" + ("" if color is None else "_" + "_".join(f"{v:.2f}" for v in color))
    if key in _cache:
        return _cache[key]
    path = os.path.join(CARS, "bmw", "bmw27", "bmw27_cpu.blend")
    skip = ("Light", "Floor", "Cube", "carRig", "carController", "Camera")
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects if not n.startswith(skip)]
    objs = [o for o in dst.objects if o is not None]
    # the wheels are collection instances; keep only the body-side objects as roots to move
    whole = [o for o in objs if o.type == "EMPTY" and o.instance_collection and o.parent is None]
    for o in whole:                      # the "1M" empty re-instances the entire car: not needed
        objs.remove(o)
        bpy.data.objects.remove(o)
    inst_members = set()
    for o in objs:
        if o.instance_collection:
            inst_members.update(o.instance_collection.all_objects)
    body = [o for o in objs if o not in inst_members]
    lib = kit.coll("LIB", hide=True)
    for col in {o.instance_collection for o in objs if o.instance_collection}:
        if col.name not in lib.children:
            try:
                lib.children.link(col)
            except Exception:
                pass
    if color is not None:
        for o in body:
            if o.type == "MESH":
                for i, m in enumerate(o.data.materials):
                    if m and m.name.startswith("CarShell"):
                        m2 = m.copy()
                        for n in m2.node_tree.nodes:
                            for inp in n.inputs:
                                if inp.name in ("Base Color", "Color") and not inp.is_linked and hasattr(inp, "default_value"):
                                    try:
                                        inp.default_value = tuple(color) + (1,)
                                    except Exception:
                                        pass
                        o.data.materials[i] = m2
    c = _wrap(key, body, 4.38, yaw=math.pi)
    _cache[key] = c
    return c


def gz(model, length=None):
    if model in _cache:
        return _cache[model]
    d = os.path.join(CARS, "gz", model)
    obj = glob.glob(os.path.join(d, "meshes", "*.obj"))[0]
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=obj, forward_axis="Y", up_axis="Z")
    objs = [o for o in bpy.data.objects if o not in before]
    tex = {os.path.splitext(os.path.basename(p))[0].lower(): p for p in glob.glob(os.path.join(d, "materials", "textures", "*.png"))}
    mtl = glob.glob(os.path.join(d, "meshes", "*.mtl"))
    want = {}
    if mtl:
        cur = None
        for ln in open(mtl[0], errors="ignore"):
            p = ln.strip().split()
            if len(p) >= 2 and p[0] == "newmtl":
                cur = p[1]
            elif len(p) >= 2 and p[0] == "map_Kd" and cur:
                want[cur] = os.path.splitext(os.path.basename(p[-1]))[0].lower()
    for o in objs:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            if m is None:
                continue
            base = m.name.split(".")[0]
            t = tex.get(want.get(base, ""), None) or tex.get(base.lower())
            m.use_nodes = True
            nt = m.node_tree
            b = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]
            if not b:
                continue
            b = b[0]
            for l in list(nt.links):
                if l.to_node == b and l.to_socket.name in ("Base Color", "Alpha"):
                    nt.links.remove(l)
            if t:
                im = nt.nodes.new("ShaderNodeTexImage")
                im.image = bpy.data.images.load(t, check_existing=True)
                nt.links.new(im.outputs[0], b.inputs["Base Color"])
            wheel = "wheel" in base.lower()
            glass = "window" in base.lower()
            b.inputs["Roughness"].default_value = 0.75 if wheel else (0.05 if glass else 0.22)
            b.inputs["Coat Weight"].default_value = 0.0 if wheel else 0.6
            b.inputs["Alpha"].default_value = 1.0
            b.inputs["Metallic"].default_value = 0.0
            b.inputs["Specular IOR Level"].default_value = 0.5
            for l in list(nt.links):
                if l.to_node == b and l.to_socket.name not in ("Base Color",):
                    nt.links.remove(l)
            if glass:
                b.inputs["Base Color"].default_value = (0.02, 0.025, 0.03, 1)
        for p in o.data.polygons:
            p.use_smooth = True
    lengths = {"suv": 4.9, "hatchback": 4.1, "prius_hybrid": 4.5, "bus": 11.5}
    bpy.context.view_layer.update()
    lo, hi = kit._bbox([o for o in objs if o.type == "MESH"])
    yaw = 0.0 if (hi.x - lo.x) > (hi.y - lo.y) else math.pi / 2
    yaw += {"suv": math.pi}.get(model, 0.0)
    c = _wrap(model, objs, length or lengths.get(model, 4.5), yaw=yaw)
    _cache[model] = c
    return c


def _gltf(name, fname, length, yaw):
    if name in _cache:
        return _cache[name]
    objs = kit.import_gltf(os.path.join(CARS, fname))
    c = _wrap(name, objs, length, yaw=yaw)
    _cache[name] = c
    return c


def ferrari():
    return _gltf("ferrari", "ferrari_plain.glb", 4.53, -math.pi / 2)


def concept():
    return _gltf("carconcept", "CarConcept_plain.glb", 4.4, math.pi / 2)


def put(c, loc, heading_deg=0.0, collection=None, name=None):
    e = bpy.data.objects.new(name or c.name.replace("LIB_", ""), None)
    e.instance_type = "COLLECTION"
    e.instance_collection = c
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(heading_deg))
    (collection or bpy.context.scene.collection).objects.link(e)
    return e
