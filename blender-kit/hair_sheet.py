"""Hairstyle comparison: python3 hair_sheet.py out.png female|male colour_name style1,style2,..."""
import sys, math
import bpy, kit, mh
from PIL import Image
out, gender, col, styles = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")
kit.reset()
c = kit.coll("P")
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=235)
tiles = []
for i, st in enumerate(styles):
    ob = mh.human(f"h{i}", gender=gender, race="caucasian", clothes=["toigo_basic_tucked_t-shirt" if gender == "female" else "namuhekam_male_polo_shirt"],
                  hair=st, pose=mh.POSES["stand"], collection=c, tint={st: mh.HAIR[col]}, expression="smile", face_seed=7)
    ob.location = (i * 1.0, 0, 0)
    bpy.context.view_layer.update()
    hz = max((ob.matrix_world @ v.co).z for v in ob.data.vertices) - 0.16
    for k, (dx, dy) in enumerate(((0.0, -1.2), (0.85, -0.85))):
        cam = kit.camera(f"c{i}{k}", (i * 1.0 + dx, dy, hz + 0.05), (i * 1.0, 0, hz - 0.02), lens=80)
        kit.render_setup(300, 360, samples=32, exposure=0.2)
        p = f"/tmp/claude-0/hair_{i}_{k}.png"
        kit.render(cam, p)
        tiles.append((i, k, p))
sh = Image.new("RGB", (300 * len(styles), 720))
for (i, k, p) in tiles:
    sh.paste(Image.open(p).convert("RGB"), (i * 300, k * 360))
sh.save(out)
print("ORDER", styles)
