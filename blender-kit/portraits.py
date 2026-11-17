"""Head-and-shoulders portraits of cast members: python3 portraits.py out.png name1,name2,..."""
import sys, math
import bpy, kit, cast
kit.reset()
c = kit.coll("People")
names = sys.argv[2].split(",")
for i, nm in enumerate(names):
    ob = cast.make(nm, "stand", c, subdiv=1)
    ob.location = (i * 0.75, 0, 0)
n = len(names)
kit.world_hdri("kloofendal_48d_partly_cloudy_puresky", "4k", 1.0, sun_az=235)
s = kit.sun(strength=2.0, angle=1.5)
from mathutils import Vector
d = Vector((math.cos(math.radians(235)), math.sin(math.radians(235)), 0.7)).normalized()
s.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
kit.render_setup(420 * n, 560, samples=48, exposure=0.2)
for i, nm in enumerate(names):
    pass
# one camera per person, rendered side by side via border crops would be complex: use a long lens per figure
import os
outs = []
for i, nm in enumerate(names):
    ob = bpy.data.objects[nm]
    bpy.context.view_layer.update()
    hz = max((ob.matrix_world @ v.co).z for v in ob.data.vertices) - 0.13
    cam = kit.camera(f"c{i}", (i * 0.75, -1.25, hz + 0.02), (i * 0.75, 0, hz - 0.08), lens=85, dof=1.25, fstop=2.8)
    kit.render_setup(420, 560, samples=48, exposure=0.2)
    p = f"/tmp/claude-0/portrait_{i}.png"
    kit.render(cam, p)
    outs.append(p)
from PIL import Image
sh = Image.new("RGB", (420 * n, 560))
for i, p in enumerate(outs):
    sh.paste(Image.open(p).convert("RGB"), (i * 420, 0))
sh.save(sys.argv[1])
