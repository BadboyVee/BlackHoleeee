"""Rewrite a Draco-compressed .glb as a plain .glb (Blender's bpy wheel cannot
load the Draco decoder). Needs `pip install DracoPy numpy`.
    python3 undraco.py in.glb out.glb
"""
import json, struct, sys
import numpy as np
import DracoPy

src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
jl = struct.unpack("<I", b[12:16])[0]
j = json.loads(b[20:20 + jl])
bo = 20 + jl
bl = struct.unpack("<I", b[bo:bo + 4])[0]
bin_ = bytearray(b[bo + 8: bo + 8 + bl])
EXT = "KHR_draco_mesh_compression"


def add(arr, comp, typ, target=None, minmax=False):
    while len(bin_) % 4:
        bin_.append(0)
    off = len(bin_)
    data = arr.tobytes()
    bin_.extend(data)
    bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
    if target:
        bv["target"] = target
    j["bufferViews"].append(bv)
    acc = {"bufferView": len(j["bufferViews"]) - 1, "componentType": comp, "count": int(arr.shape[0]) if arr.ndim > 1 else int(arr.size), "type": typ}
    if minmax:
        acc["min"] = [float(x) for x in arr.min(axis=0)]
        acc["max"] = [float(x) for x in arr.max(axis=0)]
    j["accessors"].append(acc)
    return len(j["accessors"]) - 1


n = 0
for m in j["meshes"]:
    for p in m["primitives"]:
        e = p.get("extensions", {}).get(EXT)
        if not e:
            continue
        bv = j["bufferViews"][e["bufferView"]]
        o = bv.get("byteOffset", 0)
        d = DracoPy.decode(bytes(bin_[o:o + bv["byteLength"]]))
        pts = np.asarray(d.points, dtype=np.float32).reshape(-1, 3)
        attrs = {"POSITION": add(pts, 5126, "VEC3", 34962, True)}
        nor = getattr(d, "normals", None)
        if nor is not None and len(nor):
            attrs["NORMAL"] = add(np.asarray(nor, dtype=np.float32).reshape(-1, 3), 5126, "VEC3", 34962)
        uv = getattr(d, "tex_coord", None)
        if uv is not None and len(uv):
            uv = np.asarray(uv, dtype=np.float32)
            uv = uv.reshape(len(pts), -1)[:, :2].copy()
            attrs["TEXCOORD_0"] = add(uv, 5126, "VEC2", 34962)
        p["attributes"] = attrs
        p["indices"] = add(np.asarray(d.faces, dtype=np.uint32).reshape(-1), 5125, "SCALAR", 34963)
        del p["extensions"][EXT]
        if not p["extensions"]:
            del p["extensions"]
        n += 1
for k in ("extensionsUsed", "extensionsRequired"):
    if k in j:
        j[k] = [x for x in j[k] if x != EXT]
        if not j[k]:
            del j[k]
while len(bin_) % 4:
    bin_.append(0)
j["buffers"][0]["byteLength"] = len(bin_)
js = json.dumps(j, separators=(",", ":")).encode()
js += b" " * ((4 - len(js) % 4) % 4)
out = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(bin_), b"BIN\0") + bytes(bin_)
open(dst, "wb").write(out)
print("decoded", n, "primitives ->", dst)
