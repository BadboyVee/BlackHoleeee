"""Combine images into one contact sheet: sheet.py out.png cols cell_w img1 img2 ..."""
import sys
from PIL import Image
out, cols, cw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ims = [Image.open(p).convert("RGB") for p in sys.argv[4:]]
ims = [im.resize((cw, int(im.height * cw / im.width)), Image.LANCZOS) for im in ims]
rows = (len(ims) + cols - 1) // cols
rh = [max(im.height for im in ims[r*cols:(r+1)*cols]) for r in range(rows)]
sheet = Image.new("RGB", (cols * cw, sum(rh)), (20, 20, 22))
y = 0
for r in range(rows):
    for c, im in enumerate(ims[r*cols:(r+1)*cols]):
        sheet.paste(im, (c * cw, y))
    y += rh[r]
sheet.save(out)
