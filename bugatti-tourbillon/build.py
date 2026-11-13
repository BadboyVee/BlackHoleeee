"""Assemble the complete car:  python3 build.py [--showroom] [--save path.blend] [--no-interior] [--no-wheels]"""
import sys, os, time
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import bpy
from tb import util, body, details, rig


def assemble(wheels_on=True, interior_on=True, verbose=True):
    """Build the car into the current (reset) scene. Returns dict of part dicts."""
    scene = util.reset_scene()
    t = time.time()
    bp = body.build()
    dp = details.build(bp)
    wp = ip = None
    if wheels_on:
        from tb import wheels
        wp = wheels.build()
    if interior_on:
        from tb import interior
        ip = interior.build()
    rg = rig.build(bp, dp, wp, ip)
    if verbose:
        print("assembled in %.1f s, %d objects, %d tris" % (time.time() - t, len(scene.objects), util.tri_count()))
    return dict(scene=scene, body=bp, details=dp, wheels=wp, interior=ip, rig=rg)


if __name__ == "__main__":
    a = sys.argv[1:]
    car = assemble("--no-wheels" not in a, "--no-interior" not in a)
    if "--showroom" in a:
        # stage the car: showroom, hero lighting, a camera and final render settings (F12 ready)
        from tb import environment, preview, util as U
        env = environment.build()
        environment.apply_mood(env, "hero")
        scene = car["scene"]
        cam = bpy.data.objects.new("CAM_Hero", bpy.data.cameras.new("CAM_Hero"))
        scene.collection.objects.link(cam)
        cam.location = (6.0, 3.1, 1.05)
        cam.data.lens = 55
        U.look_at(cam, (0.35, 0.0, 0.52))
        scene.camera = cam
        preview.setup_cycles(scene, samples=128, res=(1920, 1080))
    if "--save" in a:
        path = os.path.abspath(a[a.index("--save") + 1])
        bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
        print("saved", path, "%.1f MB" % (os.path.getsize(path) / 1e6))
