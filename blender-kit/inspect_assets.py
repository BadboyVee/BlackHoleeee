"""Print object names, sizes and triangle counts for cached Poly Haven models
(and any .glb paths given as arguments)."""
import glob, os, sys
import bpy
from mathutils import Vector
import kit
paths = sys.argv[1:] or sorted(glob.glob("/home/user/assets/ph/model/*/*.gltf"))
for p in paths:
    kit.reset()
    objs = kit.import_gltf(p)
    lo, hi = kit._bbox(objs)
    tris = sum(len(o.data.polygons) for o in objs if o.type == "MESH")
    print(f"## {os.path.basename(p)} size={tuple(round(x,2) for x in (hi-lo))} lo={tuple(round(x,2) for x in lo)} faces={tris} n={len(objs)}")
    if len(objs) > 1:
        for o in objs[:40]:
            if o.type == "MESH":
                l2, h2 = kit._bbox([o])
                print(f"   {o.name} size={tuple(round(x,2) for x in (h2-l2))} at={tuple(round(x,2) for x in (l2+h2)/2)} f={len(o.data.polygons)} mats={[m.name for m in o.data.materials][:3]}")
            else:
                print("   ", o.type, o.name, o.parent.name if o.parent else None)
