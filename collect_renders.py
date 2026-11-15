"""Copy finished renders from the output folder into the two projects as JPEGs (and clips as MP4)."""
import glob, os, shutil, sys
from PIL import Image
src = sys.argv[1] if len(sys.argv) > 1 else "/home/user/out/final"
here = os.path.dirname(os.path.abspath(__file__))
for p in sorted(glob.glob(os.path.join(src, "*.png"))):
    name = os.path.basename(p)
    proj = "duplex-house" if name.startswith("duplex_") else "sahara-voyage"
    dst = os.path.join(here, proj, "renders", name.replace(".png", ".jpg"))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(p):
        Image.open(p).convert("RGB").save(dst, quality=92)
        print("saved", dst)
for p, proj in (("sahara.mp4", "sahara-voyage"), ("exterior.mp4", "duplex-house"), ("interior.mp4", "duplex-house")):
    s = os.path.join(src, p)
    if os.path.exists(s) and os.path.getsize(s) > 0:
        d = os.path.join(here, proj, "renders", p)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
        print("saved", d)
