"""Extract numeric silhouette curves (metres, car coordinates) from the blueprint sheet.

Car coordinates: +X forward (nose), +Y left, +Z up, origin on the ground at mid-wheelbase.
Side + plan views in the sheet face RIGHT (nose at +x image).
Known dims: L=4.67, W=2.05, H=1.19, WB=2.74.
Writes refs/derived/blueprint_profiles.json + debug PNGs.
"""
import json, sys
import numpy as np, cv2
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "/root/.claude/uploads/d8c69794-a7de-5046-84fd-f7d20a1fbe4a/2bb588bc-image.jpg"
OUT = "refs/derived"
S = 4
L, W, H, WB = 4.67, 2.05, 1.19, 2.74
A = Image.open(SRC).convert("RGB")

def crop(box):
    c = A.crop(box); c = c.resize((c.width*S, c.height*S), Image.BICUBIC)
    return np.asarray(c).astype(np.int32)

def magenta_mask(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return (((r - g) > 28) & ((b - g) > 28) & (r > 150) & (b > 150)).astype(np.uint8)

def interior(mask, close=5):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close))
    m = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    h, w = m.shape
    canvas = (1 - m).astype(np.uint8)
    ff = np.zeros((h+2, w+2), np.uint8)
    for x in range(0, w, 7):
        for y in (0, h-1):
            if canvas[y, x] == 1: cv2.floodFill(canvas, ff, (x, y), 2)
    for y in range(0, h, 7):
        for x in (0, w-1):
            if canvas[y, x] == 1: cv2.floodFill(canvas, ff, (x, y), 2)
    ins = (canvas != 2).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(ins, connectivity=8)
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        ins = (lab == big).astype(np.uint8)
    return ins

def ground_row(m, box, y_orig):
    """Dashed ground line: refine a hand-read original-image row within +-3 px."""
    g0 = int(round((y_orig - box[1]) * S)); r = 3*S
    lo, hi = max(0, g0-r), min(m.shape[0]-1, g0+r)
    rows = m[lo:hi+1].sum(1).astype(float)
    k = np.ones(S)/S
    rs = np.convolve(rows, k, mode='same')
    return int(lo + np.argmax(rs))

def smooth(a, k=9):
    a = np.asarray(a, float); pad = k//2
    ap = np.pad(a, pad, mode='edge')
    return np.convolve(ap, np.ones(k)/k, mode='valid')

res = {}

# ------------------------------------------------------------------ SIDE
box = (100, 552, 532, 676)
img = crop(box); m = magenta_mask(img)
h, w = m.shape
# dashed ground line: the row (lower third) with the most magenta that also spans beyond the car
gy = ground_row(m, box, 670.7)
m2 = m.copy(); m2[gy-5:, :] = 0            # drop ground line + below
ins = interior(m2)
cols = np.where(ins.sum(0) > 0)[0]
x0, x1 = cols.min(), cols.max()
ppm = (x1 - x0) / L                         # px per metre
top = np.array([np.where(ins[:, c])[0].min() if ins[:, c].any() else gy for c in range(w)], float)
bot = np.array([np.where(ins[:, c])[0].max() if ins[:, c].any() else gy for c in range(w)], float)
# wheel contact intervals: bottom within 2.5cm of ground
has = ins.sum(0) > 0
near = ((gy - bot) < 0.05*ppm) & has
idx = np.where(near)[0]
splits = np.where(np.diff(idx) > 20)[0]
groups = np.split(idx, splits+1)
groups = [g for g in groups if len(g) > 10]
print("wheel contact groups:", [(int(g.min()), int(g.max())) for g in groups], "x0,x1", x0, x1, "gy", gy)
wc = [0.5*(g.min()+g.max()) for g in groups]
rear_cx, front_cx = wc[0], wc[-1]
wb_px = front_cx - rear_cx
ppm_wb = wb_px / WB
print("side: ppm(from L)=%.1f ppm(from WB)=%.1f  height=%.3f m" % (ppm, ppm_wb, (gy - top.min())/ppm))
ox = 0.5*(rear_cx + front_cx)               # origin x (mid wheelbase)
xs = (np.arange(w) - ox) / ppm
ztop = (gy - top) / ppm
zbot = (gy - bot) / ppm
sel = (np.arange(w) >= x0) & (np.arange(w) <= x1)
res['side'] = dict(x=xs[sel].round(4).tolist(), z_top=smooth(ztop[sel]).round(4).tolist(),
                   z_bot=smooth(zbot[sel]).round(4).tolist(),
                   x_rear=float(xs[x0]), x_front=float(xs[x1]),
                   rear_axle_x=float((rear_cx-ox)/ppm), front_axle_x=float((front_cx-ox)/ppm),
                   ppm=float(ppm), ppm_wb=float(ppm_wb), height=float((gy - top.min())/ppm))
dbg = cv2.cvtColor((ins*255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
dbg[m2 > 0] = (255, 0, 255)
cv2.line(dbg, (0, gy), (w-1, gy), (0, 255, 0), 1)
for c in wc: cv2.line(dbg, (int(c), 0), (int(c), h-1), (0, 255, 255), 1)
cv2.imwrite(f"{OUT}/side_debug.png", dbg)
np.save(f"{OUT}/side_inside.npy", ins)
res['side']['img'] = dict(box=box, S=S, gy=int(gy), ox=float(ox), ppm=float(ppm))

# ------------------------------------------------------------------ TOP (plan)
box = (100, 726, 532, 930)
img = crop(box); m = magenta_mask(img)
h, w = m.shape
ins = interior(m)
cols = np.where(ins.sum(0) > 0)[0]
x0, x1 = cols.min(), cols.max()
ppm_t = (x1 - x0) / L
ymin = np.array([np.where(ins[:, c])[0].min() if ins[:, c].any() else np.nan for c in range(w)], float)
ymax = np.array([np.where(ins[:, c])[0].max() if ins[:, c].any() else np.nan for c in range(w)], float)
cy = 0.5*(np.nanmin(ymin) + np.nanmax(ymax))
# NOTE mirrors inflate min/max; centre from the median of mid-lines instead
mid = 0.5*(ymin + ymax); cy = float(np.nanmedian(mid[x0:x1]))
half = 0.5*(ymax - ymin) / ppm_t
# same axle offsets as side view: nose at x_front
xs_t = (np.arange(w) - x1) / ppm_t + res['side']['x_front']
sel = (np.arange(w) >= x0) & (np.arange(w) <= x1)
res['top'] = dict(x=xs_t[sel].round(4).tolist(), half_width=smooth(half[sel], 7).round(4).tolist(),
                  ppm=float(ppm_t), max_half=float(np.nanmax(half[sel])))
res['top']['img'] = dict(box=box, S=S, cy=cy, x_nose_px=int(x1), ppm=float(ppm_t))
print("top: ppm=%.1f  max half width (incl mirrors)=%.3f" % (ppm_t, np.nanmax(half[sel])))
dbg = cv2.cvtColor((ins*255).astype(np.uint8), cv2.COLOR_GRAY2BGR); dbg[m > 0] = (255, 0, 255)
cv2.line(dbg, (0, int(cy)), (w-1, int(cy)), (0, 255, 0), 1)
cv2.imwrite(f"{OUT}/top_debug.png", dbg)
np.save(f"{OUT}/top_inside.npy", ins)

# ------------------------------------------------------------------ FRONT / REAR
for name, box, gyo in (('front', (548, 556, 756, 680), 670.7), ('rear', (548, 726, 756, 850), 840.0)):
    img = crop(box); m = magenta_mask(img)
    h, w = m.shape
    gy = ground_row(m, box, gyo)
    m2 = m.copy(); m2[gy-5:, :] = 0
    ins = interior(m2)
    # body width (exclude mirrors): use rows in the lower 55% of the car
    rws = np.where(ins.sum(1) > 0)[0]
    ytop = rws.min()
    xmin = np.array([np.where(ins[r, :])[0].min() if ins[r, :].any() else np.nan for r in range(h)], float)
    xmax = np.array([np.where(ins[r, :])[0].max() if ins[r, :].any() else np.nan for r in range(h)], float)
    lower = slice(int(ytop + 0.45*(gy-ytop)), gy-8)
    wpx = np.nanmax(xmax[lower]) - np.nanmin(xmin[lower])
    ppm_f = wpx / W
    cx = 0.5*(np.nanmax(xmax[lower]) + np.nanmin(xmin[lower]))
    zz = (gy - np.arange(h)) / ppm_f
    hw = 0.5*(xmax - xmin) / ppm_f
    sel = (np.arange(h) >= ytop) & (np.arange(h) < gy-6)
    res[name] = dict(z=zz[sel].round(4).tolist(), half_width=np.nan_to_num(smooth(np.nan_to_num(hw[sel]), 5)).round(4).tolist(),
                     ppm=float(ppm_f), height=float((gy-ytop)/ppm_f))
    res[name]['img'] = dict(box=box, S=S, gy=int(gy), cx=float(cx), ppm=float(ppm_f))
    print("%s: ppm=%.1f height=%.3f" % (name, ppm_f, (gy-ytop)/ppm_f))
    dbg = cv2.cvtColor((ins*255).astype(np.uint8), cv2.COLOR_GRAY2BGR); dbg[m2 > 0] = (255, 0, 255)
    cv2.line(dbg, (0, gy), (w-1, gy), (0, 255, 0), 1); cv2.line(dbg, (int(cx), 0), (int(cx), h-1), (0, 255, 0), 1)
    cv2.imwrite(f"{OUT}/{name}_debug.png", dbg)
    np.save(f"{OUT}/{name}_inside.npy", ins)

json.dump(res, open(f"{OUT}/blueprint_profiles.json", "w"))
s = res['side']
print("x_rear=%.3f x_front=%.3f  rear_axle=%.3f front_axle=%.3f" % (s['x_rear'], s['x_front'], s['rear_axle_x'], s['front_axle_x']))
print("front overhang=%.3f rear overhang=%.3f" % (s['x_front']-s['front_axle_x'], s['rear_axle_x']-s['x_rear']))
