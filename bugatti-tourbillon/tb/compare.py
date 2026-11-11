"""Blueprint comparison: render orthographic views framed exactly like the blueprint
crops and overlay the blueprint strokes, plus silhouette error numbers."""
import json, os, math
import numpy as np
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES = os.path.join(ROOT, "refs", "derived", "blueprint_profiles.json")
SHEET = "/root/.claude/uploads/d8c69794-a7de-5046-84fd-f7d20a1fbe4a/2bb588bc-image.jpg"


def _frames():
    R = json.load(open(PROFILES))
    out = {}
    for name in ("side", "top", "front", "rear"):
        info = R[name]["img"]; box = info["box"]; S = info["S"]; ppm = info["ppm"]
        w, h = (box[2] - box[0]) * S, (box[3] - box[1]) * S
        if name == "side":
            cx, cz = (w / 2 - info["ox"]) / ppm, (info["gy"] - h / 2) / ppm
            cam = dict(loc=(cx, -30, cz), rot=(math.radians(90), 0, 0))
        elif name == "top":
            cx = (w / 2 - info["x_nose_px"]) / ppm + R["side"]["x_front"]
            cy = (info["cy"] - h / 2) / ppm
            cam = dict(loc=(cx, cy, 30), rot=(0, 0, 0))
        elif name == "front":
            cy, cz = (w / 2 - info["cx"]) / ppm, (info["gy"] - h / 2) / ppm
            cam = dict(loc=(30, cy, cz), rot=(math.radians(90), 0, math.radians(90)))
        else:
            cy, cz = (w / 2 - info["cx"]) / ppm, (info["gy"] - h / 2) / ppm
            cam = dict(loc=(-30, -cy, cz), rot=(math.radians(90), 0, math.radians(-90)))
        out[name] = dict(w=w, h=h, ppm=ppm, scale=w / ppm, cam=cam, box=box, S=S)
    return out


def overlay(scene, out_dir, views=("side", "top", "front", "rear"), prefix="cmp_", hide=()):
    """Workbench ortho renders with blueprint strokes on top. Returns dict of error stats."""
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    F = _frames()
    sheet = Image.open(SHEET).convert("RGB")
    prev = dict(engine=scene.render.engine, rx=scene.render.resolution_x, ry=scene.render.resolution_y,
                tr=scene.render.film_transparent, cam=scene.camera, path=scene.render.filepath)
    hidden = []
    for o in scene.objects:
        if any(o.name.startswith(p) for p in ("PV_", "ENV_") + tuple(hide)) and not o.hide_render:
            o.hide_render = True; hidden.append(o)
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.film_transparent = True
    sh = scene.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.62, 0.66, 0.70)
    sh.show_cavity = True; sh.show_object_outline = True; sh.object_outline_color = (0.05, 0.05, 0.05)
    cam = bpy.data.objects.new("CMP_Cam", bpy.data.cameras.new("CMP_Cam"))
    scene.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.clip_end = 100
    scene.camera = cam
    stats = {}
    for v in views:
        f = F[v]
        scene.render.resolution_x, scene.render.resolution_y = f["w"], f["h"]
        cam.data.ortho_scale = f["scale"]
        cam.location = f["cam"]["loc"]; cam.rotation_euler = f["cam"]["rot"]
        tmp = os.path.join(out_dir, f"_{v}.png")
        scene.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        img = Image.open(tmp).convert("RGBA")
        a = np.asarray(img)[..., 3] > 40
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        comp = Image.alpha_composite(bg, img).convert("RGB")
        box = f["box"]; S = f["S"]
        crop = sheet.crop(box).resize((f["w"], f["h"]), Image.BICUBIC)
        c = np.asarray(crop).astype(np.int32)
        m = ((c[..., 0] - c[..., 1]) > 28) & ((c[..., 2] - c[..., 1]) > 28)
        arr = np.asarray(comp).copy()
        arr[m] = (arr[m] * 0.25 + np.array([230, 0, 200]) * 0.75).astype(np.uint8)
        Image.fromarray(arr).save(os.path.join(out_dir, f"{prefix}{v}.png"))
        os.remove(tmp)
        ins = np.load(os.path.join(ROOT, "refs", "derived", f"{v}_inside.npy")).astype(bool)
        if ins.shape == a.shape:
            inter = (ins & a).sum(); union = (ins | a).sum()
            st = dict(iou=float(inter / max(union, 1)))
            if v == "side":
                cols = np.where(ins.any(0) & a.any(0))[0]
                tb = np.array([np.argmax(ins[:, c]) for c in cols]); tm = np.array([np.argmax(a[:, c]) for c in cols])
                e = (tb - tm) / f["ppm"]          # + = model higher than blueprint
                st.update(top_mean_err=float(e.mean()), top_rms=float(np.sqrt((e ** 2).mean())),
                          top_max=float(np.abs(e).max()))
            stats[v] = st
    bpy.data.objects.remove(cam, do_unlink=True)
    for o in hidden:
        o.hide_render = False
    scene.render.engine = prev["engine"]; scene.render.resolution_x = prev["rx"]; scene.render.resolution_y = prev["ry"]
    scene.render.film_transparent = prev["tr"]; scene.camera = prev["cam"]; scene.render.filepath = prev["path"]
    return stats
