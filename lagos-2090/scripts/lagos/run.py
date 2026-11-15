"""Shared CLI for shot scripts:

    blender -b -P scripts/shotN.py -- --preview 1,45,90 [--pct 50] [--samples 24]
    blender -b -P scripts/shotN.py -- --render 1-90
    blender -b -P scripts/shotN.py -- --save
"""
import argparse, sys, time
from pathlib import Path
import bpy
from . import core


def main(shot, build, animate=None, samples=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview"); ap.add_argument("--pct", type=int, default=50)
    ap.add_argument("--samples", type=int); ap.add_argument("--render"); ap.add_argument("--save", action="store_true")
    ap.add_argument("--tag", default="")
    a = ap.parse_args(core.argv())
    t = time.time()
    build()
    print(f"BUILD shot{shot} {time.time() - t:.1f}s objects={len(bpy.context.scene.objects)}", flush=True)
    if a.save:
        core.save_blend(f"shot{shot}")
    if a.preview:
        sys.path.insert(0, str(core.ROOT / "scripts"))
        import post
        frames = [int(x) for x in a.preview.split(",")]
        out = core.RENDERS / "preview"
        core.render_frames(f"shot{shot}", frames, animate, a.pct, a.samples, out_dir=out / f"shot{shot}{a.tag}", overwrite=True)
        for f in frames:
            print(post.process(shot, f, out / f"shot{shot}{a.tag}" / f"f{f:04d}.exr", out / f"shot{shot}{a.tag}_f{f:04d}.png"))
    if a.render:
        lo, hi = (a.render.split("-") + [a.render])[:2]
        core.render_frames(f"shot{shot}", range(int(lo), int(hi) + 1), animate, 100, a.samples or samples)
