"""Search for a dihedral-door hinge (point + axis) that opens the door without touching the
fixed body: samples the door skin / glass / roof, rotates it, and scores clearance."""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from shapely.geometry import Polygon, Point
from tb import surface as S, body

R = body.regions()
door = Polygon(R['door']).buffer(0)
pts = []
for x in np.arange(-0.5, 1.05, 0.06):
    for z in np.arange(0.40, 1.12, 0.05):
        if not door.contains(Point(x, z)):
            continue
        if z < 0.84:
            y = float(S.YW_IN(x)) - 0.02 * (abs(z - 0.55) / 0.3) ** 2
        else:
            t = (z - 0.84) / max(float(S.ZR(x) - S.CRE(x)) - 0.84, 0.05)
            y = float(S.YCB(x)) + (float(S.YRE(x)) - float(S.YCB(x))) * min(t, 1.0)
        pts.append((x, y, z)); pts.append((x, y - 0.045, z))          # outer + inner skin
for x in np.arange(-0.45, 0.56, 0.08):                               # roof part
    for y in np.arange(0.13, 0.52, 0.06):
        pts.append((x, y, float(S.ZR(x)) - 0.03 * (y / 0.5) ** 2))
P = np.array(pts)


def inside_fixed(Q):
    """True where a point is inside the fixed body (hull or canopy) -> collision."""
    x, y, z = Q[:, 0], np.abs(Q[:, 1]), Q[:, 2]
    yw = S.YW(x); top = S.ZC(x); bot = S.ZB(x)
    hull = (x > S.X_TAIL) & (x < S.X_NOSE) & (y < yw - 0.012) & (z < top - 0.012) & (z > bot)
    zr = S.ZR(x); zre = zr - S.CRE(x)
    t = np.clip((z - S.ZCB(x)) / np.maximum(zre - S.ZCB(x), 0.05), 0, 1)
    ycan = S.YCB(x) + (S.YRE(x) - S.YCB(x)) * t
    ycan = np.where(z > zre, S.YRE(x) * np.sqrt(np.clip((zr - z) / np.maximum(S.CRE(x), 1e-3), 0, 1)), ycan)
    can = (x > S.X_CAN0) & (x < 1.40) & (y < ycan - 0.012) & (z < zr - 0.008) & (z > 0.84)
    return hull | can


def rot(P, c, a, th):
    a = a / np.linalg.norm(a); v = P - c
    return c + v * np.cos(th) + np.cross(a, v) * np.sin(th) + np.outer(v @ a, a) * (1 - np.cos(th))

closed_in = inside_fixed(P)           # points that already read as 'inside' when closed (ignore them)
best = []
for hx, hy, hz in itertools.product((0.85, 0.95, 1.02), (0.55, 0.70, 0.82), (0.86, 0.95, 1.05)):
    c = np.array([hx, hy, hz])
    for az in np.arange(-180, 180, 15):
        for el in np.arange(-45, 91, 15):
            a = np.array([np.cos(np.radians(el)) * np.cos(np.radians(az)), np.cos(np.radians(el)) * np.sin(np.radians(az)), np.sin(np.radians(el))])
            for full in (60, 70):
                bad = 0
                for th in np.radians(np.linspace(8, full, 6)):
                    Q = rot(P, c, a, th)
                    bad += int((inside_fixed(Q) & ~closed_in).sum()) + int((Q[:, 2] < 0.2).sum()) * 3
                Q = rot(P, c, a, np.radians(full))
                # want: opening cleared (door low rear corner lifted and moved out), limited height
                lift = Q[:, 2].min(); out = Q[:, 1].mean() - P[:, 1].mean(); high = Q[:, 2].max()
                fwd = Q[:, 0].max()
                score = -bad * 1.0 + 60 * min(lift, 0.75) + 25 * out - 25 * max(high - 2.0, 0) - 30 * max(fwd - 1.25, 0)
                best.append((score, bad, hx, hy, hz, az, el, full, lift, out, high, fwd, tuple(np.round(a, 3))))
best.sort(reverse=True)
print("npts", len(P))
for b in best[:8]:
    print("score %.1f bad %d hinge (%.2f %.2f %.2f) az %d el %d open %d  minz %.2f out %.2f maxz %.2f maxx %.2f axis %s" % b)
