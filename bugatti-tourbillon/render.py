"""Film pipeline.
    python3 render.py build                       assemble car + showroom + animation -> renders/film.blend
    python3 render.py probe 36 130 400 ...        low-res check frames -> renders/dev/probe/sheet.png
    python3 render.py frames [--start a --end b --res 1280x720 --samples 32]   resumable PNG frames
    python3 render.py encode [--out video/tourbillon_showcase.mp4]              frames + soundtrack -> MP4
"""
import sys, os, time, subprocess, glob
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
FILM = os.path.join(ROOT, "renders", "film.blend")
FRAMES = os.path.join(ROOT, "renders", "frames")


def frames_dir(a):
    return os.path.join(ROOT, "renders", opt(a, "--dir", "frames"))
AUDIO = os.path.join(ROOT, "renders", "audio", "soundtrack.wav")


def opt(a, name, default):
    return a[a.index(name) + 1] if name in a else default


def main():
    global FILM
    a = sys.argv[1:]
    cmd = a[0] if a else "help"
    FILM = os.path.join(ROOT, opt(a, "--film", os.path.relpath(FILM, ROOT)))
    if cmd == "encode":
        out = os.path.join(ROOT, opt(a, "--out", "video/tourbillon_showcase.mp4"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if not os.path.exists(AUDIO):
            from tb import audio
            os.makedirs(os.path.dirname(AUDIO), exist_ok=True); audio.render(AUDIO)
        subprocess.check_call(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", "24", "-start_number", "1",
                               "-i", os.path.join(frames_dir(a), "f_%04d.png"), "-i", AUDIO, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                               "-crf", opt(a, "--crf", "17"), "-preset", "slow", "-c:a", "aac", "-b:a", "192k", "-shortest",
                               "-movflags", "+faststart", out])
        print("wrote", out, "%.1f MB" % (os.path.getsize(out) / 1e6))
        return
    import bpy
    if cmd == "build":
        import build as B
        from tb import environment, animation
        car = B.assemble()
        env = environment.build()
        info = animation.build(car, env)
        print("groups", info["groups"])
        os.makedirs(os.path.dirname(FILM), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=FILM, compress=True)
        print("saved", FILM, "%.1f MB" % (os.path.getsize(FILM) / 1e6))
        return
    bpy.ops.wm.open_mainfile(filepath=FILM)
    scene = bpy.context.scene
    from tb import animation
    if cmd == "probe":
        frames = []
        for x in a[1:]:
            if x.startswith('--'):
                break
            frames.append(int(x))
        res = tuple(int(v) for v in opt(a, "--res", "640x360").split("x"))
        animation.setup_render(scene, res, int(opt(a, "--samples", "16")))
        out = os.path.join(ROOT, opt(a, "--out", "renders/dev/probe")); os.makedirs(out, exist_ok=True)
        files = []
        for f in frames:
            scene.frame_set(f)
            scene.render.filepath = os.path.join(out, "p_%04d.png" % f)
            t = time.time(); bpy.ops.render.render(write_still=True)
            print("frame %d  %.1f s" % (f, time.time() - t), flush=True)
            files.append(scene.render.filepath)
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet.py"), os.path.join(out, "sheet.png"),
                        opt(a, "--cols", "3"), opt(a, "--cell", "640")] + files)
        return
    if cmd == "frames":
        res = tuple(int(v) for v in opt(a, "--res", "1280x720").split("x"))
        animation.setup_render(scene, res, int(opt(a, "--samples", "32")))
        s, e, step = int(opt(a, "--start", "1")), int(opt(a, "--end", str(scene.frame_end))), int(opt(a, "--step", "1"))
        FR = frames_dir(a)
        os.makedirs(FR, exist_ok=True)
        t_all = time.time(); n = 0
        for f in range(s, e + 1, step):
            path = os.path.join(FR, "f_%04d.png" % f)
            if os.path.exists(path):
                continue
            scene.frame_set(f)
            scene.render.filepath = path
            t = time.time(); bpy.ops.render.render(write_still=True); n += 1
            print("frame %d  %.1f s  (avg %.1f)" % (f, time.time() - t, (time.time() - t_all) / n), flush=True)
        print("done", n, "frames")


if __name__ == "__main__":
    main()
