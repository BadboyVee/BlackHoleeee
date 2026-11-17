"""Poly Haven (CC0) asset fetcher with a local cache.

    from ph import hdri, texture, model
    hdri("kloofendal_48d_partly_cloudy_puresky", "4k")  -> path to .hdr
    texture("white_plaster_02", "2k") -> {"diff": path, "rough": path, "nor": path, "disp": path}
    model("Sofa_01", "1k")            -> path to .gltf (textures alongside)

Cache dir: $PH_CACHE or /home/user/assets/ph.  Also usable as a CLI to pre-fetch:
    python3 ph.py texture white_plaster_02 2k
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

CACHE = os.environ.get("PH_CACHE", "/home/user/assets/ph")
UA = "blender-scene-builder"


def _curl(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    for _ in range(4):
        r = subprocess.run(["curl", "-sfL", "--http1.1", "-A", UA, "-o", tmp, url])
        if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            os.replace(tmp, dest)
            return dest
    raise RuntimeError("download failed: " + url)


def _files(asset):
    p = os.path.join(CACHE, "_api", asset + ".json")
    _curl("https://api.polyhaven.com/files/" + asset, p)
    with open(p) as f:
        return json.load(f)


def hdri(asset, res="4k"):
    f = _files(asset)["hdri"][res]["hdr"]
    return _curl(f["url"], os.path.join(CACHE, "hdri", f"{asset}_{res}.hdr"))


def texture(asset, res="2k"):
    f = _files(asset)
    want = {"diff": ["Diffuse", "diff", "col_1", "col_01", "coll1", "col1"], "rough": ["Rough", "rough"], "nor": ["nor_gl"],
            "disp": ["Displacement", "disp"], "ao": ["AO"], "alpha": ["Mask", "Opacity", "Alpha"],
            "trans": ["Translucent", "translucent"]}
    out, jobs = {}, []
    for key, names in want.items():
        for n in names:
            if n in f and res in f[n]:
                fmt = "jpg" if "jpg" in f[n][res] else ("png" if "png" in f[n][res] else None)
                if not fmt:
                    continue
                dest = os.path.join(CACHE, "tex", asset, f"{asset}_{key}_{res}.{fmt}")
                out[key] = dest
                jobs.append((f[n][res][fmt]["url"], dest))
                break
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda j: _curl(*j), jobs))
    return out


def model(asset, res="1k"):
    f = _files(asset)["gltf"][res]["gltf"]
    d = os.path.join(CACHE, "model", f"{asset}_{res}")
    main = os.path.join(d, asset + ".gltf")
    jobs = [(f["url"], main)] + [(v["url"], os.path.join(d, k)) for k, v in f.get("include", {}).items()]
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda j: _curl(*j), jobs))
    return main


if __name__ == "__main__":
    kind, names = sys.argv[1], sys.argv[2:]
    res = names.pop() if names and names[-1][-1] == "k" and names[-1][0].isdigit() else None
    fn = {"hdri": hdri, "texture": texture, "model": model}[kind]
    for n in names:
        try:
            print(n, "->", fn(n, res) if res else fn(n))
        except Exception as e:  # noqa
            print(n, "FAILED", e)
