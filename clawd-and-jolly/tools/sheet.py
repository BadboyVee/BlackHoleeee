# contact sheet: python tools/sheet.py out_dir sheet.png [cols] [width]
import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
W = int(sys.argv[4]) if len(sys.argv) > 4 else 480
files = [f for dd in d.split(',') for f in sorted(glob.glob(os.path.join(dd, '*.png')))]
ims = [Image.open(f).convert('RGB') for f in files]
h = int(W * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * W, rows * (h + 14)), (20, 20, 20))
dr = ImageDraw.Draw(sheet)
for k, (f, im) in enumerate(zip(files, ims)):
    x, y = (k % cols) * W, (k // cols) * (h + 14)
    sheet.paste(im.resize((W, h), Image.LANCZOS), (x, y + 14))
    dr.text((x + 4, y + 1), os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f), fill=(200, 200, 200))
sheet.save(out)
