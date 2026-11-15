"""Build blender/assets_lib.blend: every HD Poly Haven glTF (pack + extras) and the
Kenney / loose meshes this film uses, normalised to metres, Z-up, origin at base centre.
Each asset is one collection named after its folder; multi-piece modular sets keep
their pieces as separate objects.

    blender -b -P scripts/build_asset_library.py
"""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "blender" / "assets_lib.blend"

LOOSE = [  # Kenney / loose pack meshes that get restyled or used at distance
    "models/vehicles/van.glb", "models/vehicles/motorcycle.glb", "models/vehicles/bicycle.glb",
    "models/animals/bird.glb", "models/animals/butterfly.glb", "models/boats/canoe.glb",
    "models/boats/boat-row-small.glb", "models/boats/boat-fishing-small.glb",
    "models/vehicles/sedan.glb", "models/vehicles/taxi.glb", "models/vehicles/suv.glb",
    "models/vehicles/truck.glb", "models/vehicles/delivery-van.glb",
]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
report = {}


def bbox(objs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx


def import_asset(path, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    bpy.context.view_layer.update()
    # bake world transforms into mesh data, drop hierarchy / armatures / empties
    for o in meshes:
        mw = o.matrix_world.copy()
        if o.data.users > 1:
            o.data = o.data.copy()
        o.parent = None
        for m in list(o.modifiers):
            o.modifiers.remove(m)
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    coll = bpy.data.collections.new(name)
    scene.collection.children.link(coll)
    mn, mx = bbox(meshes)
    single = len(meshes) == 1
    pieces = []
    for o in meshes:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
        if single:
            pivot = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
        else:
            omn, omx = bbox([o])
            pivot = Vector(((omn.x + omx.x) / 2, (omn.y + omx.y) / 2, omn.z))
        o.data.transform(Matrix.Translation(-pivot))
        o.location = (0, 0, 0)
        o.name = f"{name}__{o.name}"
        o.data.name = o.name
        o["src_offset"] = list(pivot)
        o.data.update()
        pieces.append({"name": o.name, "dims": [round(v, 3) for v in o.dimensions],
                       "tris": sum(len(p.vertices) - 2 for p in o.data.polygons),
                       "mats": [m.name for m in o.data.materials if m]})
    report[name] = {"path": str(path.relative_to(ROOT)), "size": [round(v, 3) for v in (mx - mn)], "pieces": pieces}
    print("LIB", name, report[name]["size"], len(pieces), sum(p["tris"] for p in pieces), flush=True)


for hd in sorted(ROOT.joinpath("models").rglob("hd-*")):
    g = list(hd.glob("*.gltf"))
    if hd.is_dir() and g:
        try:
            import_asset(g[0], hd.name[3:])
        except Exception as e:
            print("FAIL", hd, e)
for rel in LOOSE:
    p = ROOT / rel
    try:
        import_asset(p, "k-" + p.stem)
    except Exception as e:
        print("FAIL", rel, e)

for img in bpy.data.images:  # keep textures external + relative
    if img.filepath:
        img.filepath = bpy.path.relpath(img.filepath, start=str(OUT.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
(ROOT / "blender" / "assets_lib.json").write_text(json.dumps(report, indent=1))
print("SAVED", OUT, OUT.stat().st_size // 1024, "KB")
