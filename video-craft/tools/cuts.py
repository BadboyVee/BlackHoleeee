# Per-frame change metrics for shot detection: luma mean-abs-diff, HSV histogram distance,
# edge change ratio, plus each frame's brightness / saturation / dominant hue.
import sys, os, json
import numpy as np, cv2
d = sys.argv[1]; out = sys.argv[2]
files = sorted(f for f in os.listdir(d) if f.endswith('.jpg'))
prev = None; rows = []
for i, f in enumerate(files):
    im = cv2.imread(os.path.join(d, f))
    sm = cv2.resize(im, (320, 180), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
    y = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hist = cv2.calcHist([hsv], [0, 1, 2], None, [12, 4, 8], [0, 180, 0, 256, 0, 256]).ravel(); hist /= hist.sum() + 1e-9
    edges = cv2.Canny(cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    r = dict(n=i, t=i / 25, luma=float(y.mean()), lstd=float(y.std()), sat=float(hsv[..., 1].mean()),
             hue=float(np.median(hsv[..., 0][hsv[..., 1] > 40])) if (hsv[..., 1] > 40).any() else -1)
    if prev is not None:
        r['mad'] = float(np.abs(y - prev['y']).mean())
        r['hd'] = float(0.5 * np.abs(hist - prev['hist']).sum())
        dil_p = cv2.dilate(prev['e'].astype(np.uint8), np.ones((5, 5))) > 0; dil_c = cv2.dilate(edges.astype(np.uint8), np.ones((5, 5))) > 0
        ein = (edges & ~dil_p).sum() / max(1, edges.sum()); eout = (prev['e'] & ~dil_c).sum() / max(1, prev['e'].sum())
        r['ecr'] = float(max(ein, eout))
    else:
        r['mad'] = r['hd'] = r['ecr'] = 0.0
    rows.append(r); prev = dict(y=y, hist=hist, e=edges)
json.dump(rows, open(out, 'w'))
print(len(rows), 'frames')
