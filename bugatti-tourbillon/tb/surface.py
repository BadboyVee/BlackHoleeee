"""Analytic master surfaces of the body: the lower HULL and the teardrop CANOPY.

Both are lofts of cross-sections along X.  Every cross-section is a chain of
cubic Hermite spans between a few key points (crest, max-width, rocker ...);
the key points move along X on smooth guide curves measured from the blueprint
(refs/derived/blueprint_profiles.json, bias-corrected for line thickness).

The functions return control cages (nx, nring, 3).  body.py subdivides them
(Catmull-Clark = bicubic B-spline surface, curvature-continuous, which is what
keeps paint reflections clean) and cuts the panels out.
"""
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d

X_TAIL, X_NOSE = -2.255, 2.405


class G:
    """Guide curve: PCHIP through control points, then Gaussian smoothed.

    PCHIP never overshoots; the Gaussian makes it C-infinity so highlights do
    not kink at the control points.  sigma is in metres.
    """

    def __init__(self, pts, sigma=0.05, lo=-2.7, hi=2.8, step=0.002):
        pts = sorted(pts)
        xs = np.array([p[0] for p in pts], float)
        ys = np.array([p[1] for p in pts], float)
        f = PchipInterpolator(xs, ys)
        self.t = np.arange(lo, hi + step, step)
        v = f(np.clip(self.t, xs[0], xs[-1]))
        self.v = gaussian_filter1d(v, sigma / step, mode='nearest') if sigma > 0 else v

    def __call__(self, x):
        return np.interp(x, self.t, self.v)


def hermite(Pa, Pb, Ta, Tb, n, endpoint=False):
    """Cubic Hermite span, vectorised over stations.

    Pa, Pb, Ta, Tb: (nx, 2) arrays of (y, z).  Returns (nx, n, 2).
    """
    t = np.linspace(0.0, 1.0, n, endpoint=endpoint)[None, :, None]
    h00 = 2 * t ** 3 - 3 * t ** 2 + 1
    h10 = t ** 3 - 2 * t ** 2 + t
    h01 = -2 * t ** 3 + 3 * t ** 2
    h11 = t ** 3 - t ** 2
    return h00 * Pa[:, None, :] + h10 * Ta[:, None, :] + h01 * Pb[:, None, :] + h11 * Tb[:, None, :]


def _yz(y, z):
    return np.stack([np.asarray(y, float), np.asarray(z, float)], axis=1)


E = 1.657   # Hermite tangent factor that makes a span a quarter ellipse

# =====================================================================  HULL
# plan-view half width (max over z)
YW = G([(-2.255, 0.22), (-2.24, 0.34), (-2.20, 0.50), (-2.15, 0.640), (-2.10, 0.745), (-2.05, 0.810),
        (-1.95, 0.868), (-1.85, 0.925), (-1.75, 0.982), (-1.65, 1.016), (-1.50, 1.026), (-1.37, 1.027),
        (-1.10, 1.022), (-0.95, 1.006), (-0.80, 0.980), (-0.65, 0.945), (-0.45, 0.918), (-0.25, 0.944),
        (-0.05, 0.968), (0.20, 0.974), (0.60, 0.978), (0.90, 0.988), (1.05, 1.014), (1.20, 1.026),
        (1.37, 1.027), (1.60, 1.025), (1.75, 1.014), (1.85, 0.987), (1.95, 0.932), (2.05, 0.840),
        (2.15, 0.728), (2.25, 0.560), (2.33, 0.425), (2.38, 0.335), (2.405, 0.290)], sigma=0.035)

# shoulder / fender crest
ZC = G([(-2.255, 0.800), (-2.20, 0.830), (-2.10, 0.858), (-1.95, 0.886), (-1.75, 0.910), (-1.50, 0.924),
        (-1.37, 0.918), (-1.15, 0.898), (-0.95, 0.872), (-0.75, 0.852), (-0.50, 0.843), (0.00, 0.840),
        (0.60, 0.840), (1.00, 0.843), (1.20, 0.845), (1.37, 0.842), (1.50, 0.833), (1.65, 0.820),
        (1.75, 0.800), (1.85, 0.778), (1.95, 0.752), (2.05, 0.726), (2.15, 0.693), (2.25, 0.636),
        (2.33, 0.572), (2.405, 0.548)], sigma=0.04)
RC = G([(-2.255, 0.74), (-1.90, 0.78), (-1.37, 0.80), (-0.80, 0.86), (0.00, 0.885), (0.90, 0.87),
        (1.37, 0.775), (2.00, 0.74), (2.405, 0.72)], sigma=0.08)          # crest y as a fraction of YW

# inner side surface (door / quarter / intake duct floor): keeps narrowing behind the waist
YW_IN = G([(-2.255, 0.60), (-1.60, 0.64), (-1.30, 0.70), (-1.00, 0.775), (-0.73, 0.858), (-0.45, 0.916),
           (-0.25, 0.944), (-0.05, 0.968), (0.20, 0.974), (0.60, 0.978), (0.90, 0.988), (1.05, 1.014),
           (1.20, 1.026), (1.37, 1.027), (1.60, 1.025), (1.75, 1.014), (1.85, 0.987), (1.95, 0.932),
           (2.05, 0.840), (2.15, 0.728), (2.25, 0.560), (2.33, 0.425), (2.38, 0.335), (2.405, 0.290)],
          sigma=0.035)

ZW = G([(-2.255, 0.60), (-1.37, 0.60), (-0.60, 0.56), (0.30, 0.55), (1.37, 0.60), (2.10, 0.50),
        (2.405, 0.42)], sigma=0.10)                                       # height of max width

# underside
ZB = G([(-2.255, 0.340), (-2.20, 0.262), (-2.10, 0.212), (-1.90, 0.186), (-1.75, 0.175), (-1.00, 0.135),
        (-0.50, 0.128), (0.50, 0.128), (1.00, 0.135), (1.75, 0.160), (2.10, 0.160), (2.30, 0.175),
        (2.405, 0.190)], sigma=0.05)
TUCK = G([(-2.255, 0.08), (-1.37, 0.10), (-0.50, 0.12), (0.50, 0.12), (1.37, 0.10), (2.10, 0.07),
          (2.405, 0.05)], sigma=0.10)                                     # rocker tuck-under

# centre line of the deck (hood / hidden cabin deck / engine deck)
ZH0 = G([(2.405, 0.555), (2.36, 0.585), (2.30, 0.622), (2.20, 0.672), (2.05, 0.728), (1.90, 0.770),
         (1.75, 0.802), (1.60, 0.822), (1.45, 0.836), (1.30, 0.830), (1.00, 0.800), (-0.50, 0.800),
         (-0.80, 0.830), (-1.20, 0.868), (-1.60, 0.885), (-1.90, 0.872), (-2.10, 0.852), (-2.20, 0.828),
         (-2.255, 0.800)], sigma=0.04)
# raised hood plateau (the V that grows out of the horseshoe); elsewhere it is just a flat deck
YP = G([(2.405, 0.185), (2.30, 0.215), (2.05, 0.265), (1.75, 0.335), (1.50, 0.440), (1.30, 0.50),
        (1.00, 0.40), (-0.50, 0.40), (-0.80, 0.42), (-1.70, 0.40), (-2.255, 0.20)], sigma=0.05)
# valley between the plateau and the crest: lateral position (fraction of the way to the crest) and depth
FV = G([(2.405, 0.30), (2.00, 0.38), (1.50, 0.42), (1.00, 0.50), (-0.50, 0.50), (-0.80, 0.45),
        (-2.255, 0.45)], sigma=0.08)
DV = G([(2.405, 0.004), (2.30, 0.022), (2.10, 0.040), (1.80, 0.046), (1.55, 0.040), (1.35, 0.022),
        (1.10, 0.000), (-0.50, 0.000), (-0.75, 0.020), (-1.00, 0.050), (-1.40, 0.062), (-1.85, 0.050),
        (-2.10, 0.030), (-2.255, 0.010)], sigma=0.05)      # valley depth below the crest/plateau level

HULL_SPANS = (3, 3, 4, 7, 9, 4)  # samples per span: H0-Hp, Hp-H1, H1-H2, H2-H3, H3-H4, H4-H5


def hull_stations():
    mid = np.arange(-1.95, 1.951, 0.075)
    return np.concatenate([[-2.255, -2.245, -2.225, -2.195, -2.155, -2.10, -2.03], mid,
                           [2.03, 2.10, 2.16, 2.21, 2.255, 2.295, 2.33, 2.36, 2.385, 2.405]])


def hull_half(xs, inner=False):
    """Half cross-sections (y >= 0) from top centre to bottom centre: (nx, n, 2) of (y, z).

    inner=True gives the recessed side surface that lives inside the C-line (same crest,
    narrower below it behind the waist)."""
    xs = np.asarray(xs, float)
    yw, zc, zw, zb = YW(xs), ZC(xs), ZW(xs), ZB(xs)
    yc = yw * RC(xs)
    if inner:
        yw = YW_IN(xs)
        yc = np.minimum(yc, yw - 0.03)
    zh0 = ZH0(xs)
    yp = np.minimum(YP(xs), yc * 0.62)
    yv = yp + FV(xs) * (yc - yp)
    zv = np.minimum(zh0, zc) - DV(xs)
    y4 = yw - TUCK(xs)
    z0 = 0 * xs

    H0 = _yz(z0, zh0)
    Hp = _yz(yp, zh0 - 0.004)
    H1 = _yz(yv, zv)
    H2 = _yz(yc, zc)
    H3 = _yz(yw, zw)
    H4 = _yz(y4, zb)
    H5 = _yz(z0, zb)

    s0, s1, s2, s3, s4, s5 = HULL_SPANS
    d = Hp - H0
    p = hermite(H0, Hp, _yz(d[:, 0], z0), _yz(d[:, 0], z0), s0)
    d = H1 - Hp
    a = hermite(Hp, H1, _yz(d[:, 0], z0), _yz(d[:, 0], z0), s1)
    d = H2 - H1
    b = hermite(H1, H2, _yz(d[:, 0], z0), _yz(d[:, 0], z0), s2)
    d = H3 - H2
    c = hermite(H2, H3, _yz(E * d[:, 0], z0), _yz(z0, E * d[:, 1]), s3)
    d = H4 - H3
    k = 1.42
    e = hermite(H3, H4, _yz(z0, E * k * d[:, 1]), _yz(E * k * d[:, 0], z0), s4)
    d = H5 - H4
    f = hermite(H4, H5, d, d, s5, endpoint=True)
    return np.concatenate([p, a, b, c, e, f], axis=1)


def ring_from_half(xs, half):
    """Mirror half sections into closed rings: (nx, 2n-2, 3)."""
    nx, n, _ = half.shape
    X = np.repeat(xs[:, None], n, axis=1)
    left = np.stack([X, half[..., 0], half[..., 1]], axis=2)             # +Y side, top -> bottom
    right = np.stack([X, -half[..., 0], half[..., 1]], axis=2)[:, -2:0:-1, :]  # bottom -> top, -Y
    return np.concatenate([left, right], axis=1)


def hull_cage(inner=False):
    xs = hull_stations()
    return xs, ring_from_half(xs, hull_half(xs, inner=inner))


# =====================================================================  CANOPY
X_CAN0, X_CAN1 = -1.87, 1.46

ZR = G([(-1.87, 0.900), (-1.55, 0.948), (-1.35, 0.990), (-1.15, 1.038), (-0.95, 1.081), (-0.75, 1.121),
        (-0.55, 1.158), (-0.35, 1.178), (-0.15, 1.189), (0.05, 1.186), (0.25, 1.172), (0.45, 1.144),
        (0.62, 1.108), (0.85, 1.030), (1.05, 0.971), (1.25, 0.911), (1.36, 0.872), (1.42, 0.838),
        (1.46, 0.790)], sigma=0.045)
YRE = G([(-1.87, 0.36), (-1.50, 0.42), (-1.00, 0.47), (-0.50, 0.52), (0.00, 0.55), (0.60, 0.535),
         (0.90, 0.60), (1.15, 0.64), (1.46, 0.66)], sigma=0.06)            # cant rail / A-pillar line
CRE = G([(-1.87, 0.020), (-1.00, 0.035), (-0.50, 0.050), (0.00, 0.055), (0.60, 0.060), (0.90, 0.085),
         (1.15, 0.100), (1.46, 0.100)], sigma=0.06)                        # crown at the cant rail
YCB = G([(-1.87, 0.44), (-1.50, 0.50), (-1.00, 0.58), (-0.70, 0.70), (-0.40, 0.79), (0.00, 0.815),
         (0.50, 0.80), (0.90, 0.76), (1.15, 0.74), (1.46, 0.72)], sigma=0.06)   # base of the canopy
ZCB = G([(-1.87, 0.84), (-1.50, 0.86), (-1.00, 0.84), (-0.70, 0.81), (0.00, 0.80), (1.46, 0.78)],
        sigma=0.06)

CANOPY_SPANS = (7, 7)


def canopy_stations():
    return np.concatenate([[-1.87, -1.84], np.arange(-1.775, 1.401, 0.075), [1.44, 1.46]])


def canopy_half(xs):
    xs = np.asarray(xs, float)
    zr = ZR(xs)
    C0 = _yz(0 * xs, zr)
    C1 = _yz(YRE(xs), zr - CRE(xs))
    C2 = _yz(YCB(xs), ZCB(xs))
    s1, s2 = CANOPY_SPANS
    side = C2 - C1
    ln = np.linalg.norm(side, axis=1, keepdims=True) + 1e-9
    gdir = side / ln                                       # along the glass, pointing down/out
    # tangent at the cant rail: halfway between horizontal-out and the glass direction
    t1 = np.stack([np.ones_like(xs), 0 * xs], axis=1) + gdir
    t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
    d01 = np.linalg.norm(C1 - C0, axis=1, keepdims=True)
    a = hermite(C0, C1, _yz(1.15 * d01[:, 0], 0 * xs), t1 * d01 * 0.9, s1)
    b = hermite(C1, C2, t1 * ln * 0.9, gdir * ln * 1.0, s2, endpoint=True)
    return np.concatenate([a, b], axis=1)


def canopy_cage():
    """Open-bottom canopy cage: rows run +Y base -> roof centre -> -Y base. (nx, 2n-1, 3)."""
    xs = canopy_stations()
    half = canopy_half(xs)
    nx, n, _ = half.shape
    X = np.repeat(xs[:, None], n, axis=1)
    left = np.stack([X, half[..., 0], half[..., 1]], axis=2)[:, ::-1, :]     # base(+Y) -> centre
    right = np.stack([X, -half[..., 0], half[..., 1]], axis=2)[:, 1:, :]     # centre -> base(-Y)
    return xs, np.concatenate([left, right], axis=1)
