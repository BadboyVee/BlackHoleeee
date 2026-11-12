# Contact sheets of every frame: 8 x 6 thumbnails per sheet, labelled with frame number and time.
import sys, os
from PIL import Image, ImageDraw
d = sys.argv[1]; out = sys.argv[2]; fps = float(sys.argv[3]) if len(sys.argv) > 3 else 25
files = sorted(f for f in os.listdir(d) if f.endswith('.jpg'))
cols, rows, tw, th = 8, 6, 240, 135
per = cols * rows
os.makedirs(out, exist_ok=True)
for s in range(0, len(files), per):
    sheet = Image.new('RGB', (cols * tw, rows * th), 'black'); dr = ImageDraw.Draw(sheet)
    for j, f in enumerate(files[s:s + per]):
        n = int(f[1:5]) - 1
        im = Image.open(os.path.join(d, f)).convert('RGB').resize((tw, th), Image.BILINEAR)
        x, y = (j % cols) * tw, (j // cols) * th
        sheet.paste(im, (x, y)); dr.rectangle([x, y, x + 74, y + 12], fill='black'); dr.text((x + 2, y + 1), f'{n} {n / fps:.2f}s', fill='yellow')
    sheet.save(os.path.join(out, f'sheet_{s // per:02d}.jpg'), quality=88)
print('sheets', (len(files) + per - 1) // per)
