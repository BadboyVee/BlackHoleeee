# The film's grain and vignette pass (index.html, `grain`), applied to frames rendered outside
# it, so the Blender horse matches the rest of the video: python grain.py <in_dir> <out_dir>
import os, sys
import numpy as np
from PIL import Image

src, dst = sys.argv[1:3]
os.makedirs(dst, exist_ok=True)
rng = np.random.default_rng(5)
for name in sorted(os.listdir(src)):
    if not name.endswith('.png'): continue
    img = np.asarray(Image.open(os.path.join(src, name)).convert('RGB')).astype(np.float32) / 255
    h, w = img.shape[:2]
    x = (np.arange(w) + .5) / w * 2 - 1; y = (np.arange(h) + .5) / h * 2 - 1
    r = np.hypot(x[None, :] * (w / h) * .62, y[:, None])
    t = np.clip((r - .55) / .9, 0, 1); vig = t * t * (3 - 2 * t)
    a = (.028 + vig * .07)[..., None]
    g = rng.random((h, w, 1), dtype=np.float32) * (1 - vig)[..., None]
    out = img * (1 - a) + g * a
    Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(dst, name))
    print(name)
