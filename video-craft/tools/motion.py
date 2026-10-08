# Global camera motion per frame pair: tracked corners (LK) -> partial affine (scale, rotation, shift).
# Also per-frame text box on white frames (dark pixels) and a 5-colour palette per frame.
import sys, os, json
import numpy as np, cv2
d, out = sys.argv[1], sys.argv[2]
files = sorted(f for f in os.listdir(d) if f.endswith('.jpg'))
rows = []; prev = None
for i, f in enumerate(files):
    im = cv2.imread(os.path.join(d, f)); g = cv2.cvtColor(cv2.resize(im, (640, 360), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    r = {'n': i}
    if prev is not None:
        p0 = cv2.goodFeaturesToTrack(prev, 400, 0.01, 6)
        if p0 is not None and len(p0) >= 8:
            p1, st, err = cv2.calcOpticalFlowPyrLK(prev, g, p0, None, winSize=(21, 21), maxLevel=3)
            ok = st.ravel() == 1
            if ok.sum() >= 8:
                M, inl = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if M is not None:
                    s = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
                    r.update(scale=s, rot=rot, tx=float(M[0, 2]) * 2, ty=float(M[1, 2]) * 2, inliers=int(inl.sum()), tracked=int(ok.sum()),
                             flow=float(np.median(np.linalg.norm((p1[ok] - p0[ok]).reshape(-1, 2), axis=1))) * 2)
    # text / dark-ink box on light frames
    full = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    if full.mean() > 200:
        ink = full < 140
        ys, xs = np.nonzero(ink)
        if len(xs) > 30:
            r['ink'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), int(len(xs))]
    # palette (k-means on 64x36)
    sm = cv2.resize(im, (64, 36), interpolation=cv2.INTER_AREA).reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, lab, cen = cv2.kmeans(sm, 5, None, crit, 2, cv2.KMEANS_PP_CENTERS)
    cnt = np.bincount(lab.ravel(), minlength=5)
    order = np.argsort(cnt)[::-1]
    r['palette'] = ['#%02x%02x%02x' % tuple(int(v) for v in cen[k][::-1]) for k in order]; r['share'] = [round(float(cnt[k] / cnt.sum()), 3) for k in order]
    rows.append(r); prev = g
json.dump(rows, open(out, 'w'))
print('done', len(rows))
