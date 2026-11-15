#!/usr/bin/env python3
"""Convert downloaded Poly Haven glTF packages in models/*/hd-*/ to Unreal-ready FBX.

Unreal settings: centimetres, Z-up, -Y forward, origin at the base, transforms applied.
Textures stay in the sibling textures/ folder (not embedded).

Run via:
  blender --background --python convert_hd_to_fbx.py -- [optional hd-folder or --root PATH]
"""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

def argv_after_double_dash():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def parse_args(args):
    root = None
    only = []
    i = 0
    while i < len(args):
        if args[i] == "--root" and i + 1 < len(args):
            root = Path(args[i + 1])
            i += 2
        else:
            only.append(Path(args[i]))
            i += 1
    return root, only


def script_dir():
    # When Blender runs this, __file__ is set.
    return Path(__file__).resolve().parent


def cleanup_import_artifacts():
    for o in list(bpy.data.objects):
        if o.name.startswith("tmpParent"):
            bpy.data.objects.remove(o, do_unlink=True)


def in_view_layer(objs):
    present = set(bpy.context.view_layer.objects)
    return [o for o in objs if o in present]


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    # 1 Blender unit = 1 cm. The glTF importer converts metres automatically.
    scene.unit_settings.scale_length = 0.01
    scene.unit_settings.length_unit = "CENTIMETERS"


def apply_transform(objs, location=False, rotation=True, scale=True):
    bpy.ops.object.select_all(action="DESELECT")
    selectable = in_view_layer(objs)
    for o in selectable:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
    if any(o.select_get() for o in bpy.context.view_layer.objects):
        bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)


def world_bbox():
    mins = Vector((1e18, 1e18, 1e18))
    maxs = Vector((-1e18, -1e18, -1e18))
    count = 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            mins.x, mins.y, mins.z = min(mins.x, w.x), min(mins.y, w.y), min(mins.z, w.z)
            maxs.x, maxs.y, maxs.z = max(maxs.x, w.x), max(maxs.y, w.y), max(maxs.z, w.z)
            count += 1
    if count == 0:
        return None, None
    return mins, maxs


def set_origin_to_base():
    mins, maxs = world_bbox()
    if mins is None:
        raise RuntimeError("no mesh to place origin")
    pivot = Vector(((mins.x + maxs.x) * 0.5, (mins.y + maxs.y) * 0.5, mins.z))
    bpy.context.scene.cursor.location = pivot
    bpy.ops.object.select_all(action="DESELECT")
    selectable = in_view_layer(list(bpy.context.scene.objects))
    for o in selectable:
        o.select_set(True)
    if selectable:
        bpy.context.view_layer.objects.active = selectable[0]
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    for o in selectable:
        if o.parent is None:
            o.location -= pivot
    apply_transform(selectable, location=True, rotation=False, scale=False)


def convert_one(src: Path, dest_fbx: Path):
    reset_scene()
    dest_fbx.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.import_scene.gltf(filepath=str(src))
    cleanup_import_artifacts()
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("no mesh objects imported")
    apply_transform(list(bpy.context.scene.objects), location=False, rotation=True, scale=True)
    set_origin_to_base()
    has_anim = bool(bpy.data.actions)
    bpy.ops.object.select_all(action="DESELECT")
    for o in in_view_layer(list(bpy.context.scene.objects)):
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=str(dest_fbx),
        use_selection=False,
        object_types={"MESH", "ARMATURE", "EMPTY", "OTHER"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        add_leaf_bones=False,
        bake_anim=has_anim,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=True,
        bake_anim_use_all_actions=True,
        bake_anim_force_startend_keying=True,
        armature_nodetype="NULL",
        axis_forward="-Y",
        axis_up="Z",
        apply_scale_options="FBX_SCALE_ALL",
        apply_unit_scale=True,
        global_scale=1.0,
        path_mode="RELATIVE",
        embed_textures=False,
        bake_space_transform=True,
        batch_mode="OFF",
    )
    if not dest_fbx.exists() or dest_fbx.stat().st_size < 64:
        raise RuntimeError("FBX was not written")


def iter_targets(root: Path, only):
    if only:
        for p in only:
            folder = p if p.is_dir() else p.parent
            if not folder.is_absolute():
                folder = root / folder
            yield folder
        return
    for hd in sorted(root.joinpath("models").rglob("hd-*")):
        if hd.is_dir():
            yield hd


def main():
    args = argv_after_double_dash()
    root, only = parse_args(args)
    if root is None:
        root = script_dir()
    failures = 0
    count = 0
    for folder in iter_targets(root, only):
        gltfs = list(folder.glob("*.gltf"))
        if not gltfs:
            print(f"SKIP no gltf in {folder}")
            continue
        dest = folder / (folder.name + ".fbx")
        src = gltfs[0]
        print(f"CONVERT {src} -> {dest}")
        try:
            convert_one(src, dest)
            print(f"  OK {dest.stat().st_size / 1024:.1f} KB")
            count += 1
        except Exception as e:
            print(f"  FAIL {e}")
            failures += 1
    print(f"DONE converted={count} failed={failures}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
