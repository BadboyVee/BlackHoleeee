"""Time, easing, interpolation and noise: the maths every scene shares."""
import math

import numpy as np

FPS = 60
W, H = 1920, 1080
CX, CY = W / 2, H / 2


# ---------------------------------------------------------------- scalars

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def invlerp(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    return clamp((x - a) / (b - a))


def remap(x, a, b, c, d, ease=None):
    t = invlerp(a, b, x)
    if ease is not None:
        t = ease(t)
    return c + (d - c) * t


def smoothstep(a, b, x):
    t = invlerp(a, b, x)
    return t * t * (3 - 2 * t)


def fract(x):
    return x - math.floor(x)


def window(t, t0, t1, fade_in=0.0, fade_out=0.0):
    """1 inside [t0, t1], ramping linearly over the fade lengths, 0 outside."""
    if t < t0 or t > t1:
        return 0.0
    a = 1.0 if fade_in <= 0 else clamp((t - t0) / fade_in)
    b = 1.0 if fade_out <= 0 else clamp((t1 - t) / fade_out)
    return min(a, b)


# ---------------------------------------------------------------- easing
# Penner's set plus a CSS-style cubic bezier and an analytic spring.

def linear(t): return t
def in_quad(t): return t * t
def out_quad(t): return 1 - (1 - t) * (1 - t)
def in_out_quad(t): return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
def in_cubic(t): return t ** 3
def out_cubic(t): return 1 - (1 - t) ** 3
def in_out_cubic(t): return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
def in_quart(t): return t ** 4
def out_quart(t): return 1 - (1 - t) ** 4
def in_out_quart(t): return 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2
def in_quint(t): return t ** 5
def out_quint(t): return 1 - (1 - t) ** 5
def in_out_quint(t): return 16 * t ** 5 if t < 0.5 else 1 - (-2 * t + 2) ** 5 / 2
def in_sine(t): return 1 - math.cos(t * math.pi / 2)
def out_sine(t): return math.sin(t * math.pi / 2)
def in_out_sine(t): return -(math.cos(math.pi * t) - 1) / 2
def in_expo(t): return 0.0 if t <= 0 else 2 ** (10 * t - 10)
def out_expo(t): return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def in_out_expo(t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def in_circ(t): return 1 - math.sqrt(max(0.0, 1 - t * t))
def out_circ(t): return math.sqrt(max(0.0, 1 - (t - 1) ** 2))


def in_back(t, s=1.70158):
    return (s + 1) * t ** 3 - s * t * t


def out_back(t, s=1.70158):
    t -= 1
    return 1 + (s + 1) * t ** 3 + s * t * t


def in_out_back(t, s=1.70158):
    s2 = s * 1.525
    if t < 0.5:
        return ((2 * t) ** 2 * ((s2 + 1) * 2 * t - s2)) / 2
    return ((2 * t - 2) ** 2 * ((s2 + 1) * (t * 2 - 2) + s2) + 2) / 2


def out_elastic(t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def out_bounce(t):
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


def bezier(x1, y1, x2, y2):
    """CSS cubic-bezier(x1, y1, x2, y2) as an easing function."""
    def bx(u): return 3 * x1 * u * (1 - u) ** 2 + 3 * x2 * u * u * (1 - u) + u ** 3
    def by(u): return 3 * y1 * u * (1 - u) ** 2 + 3 * y2 * u * u * (1 - u) + u ** 3
    def dbx(u): return 3 * x1 * (1 - u) ** 2 + 6 * (x2 - x1) * u * (1 - u) + 3 * (1 - x2) * u * u

    def f(x):
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        u = x
        for _ in range(8):
            d = dbx(u)
            if abs(d) < 1e-6:
                break
            u -= (bx(u) - x) / d
            u = clamp(u)
        lo, hi = 0.0, 1.0
        for _ in range(20):  # bisection polish, robust where Newton stalls
            if abs(bx(u) - x) < 1e-5:
                break
            if bx(u) < x:
                lo = u
            else:
                hi = u
            u = (lo + hi) / 2
        return by(u)
    return f


# Designer curves used throughout.
snap = bezier(0.16, 1.0, 0.3, 1.0)        # fast out, long settle ("expo-ish")
glide = bezier(0.65, 0.0, 0.35, 1.0)      # symmetric, heavier than in_out_cubic
whip = bezier(0.9, 0.0, 0.1, 1.0)         # hard in-out used for wipes
anticip = bezier(0.36, -0.4, 0.3, 1.0)    # little pull-back before the move


def spring(t, freq=2.2, damping=0.35):
    """Unit step response of a damped spring; t in seconds since release."""
    if t <= 0:
        return 0.0
    w = 2 * math.pi * freq
    if damping >= 1:
        return 1 - math.exp(-w * t) * (1 + w * t)
    wd = w * math.sqrt(1 - damping * damping)
    return 1 - math.exp(-damping * w * t) * (math.cos(wd * t) + damping * w / wd * math.sin(wd * t))


def anim(t, t0, dur, a=0.0, b=1.0, ease=out_cubic):
    """Value of a single tween from a to b starting at t0 lasting dur seconds."""
    if dur <= 0:
        return b if t >= t0 else a
    return a + (b - a) * ease(clamp((t - t0) / dur))


def keys(t, frames):
    """Piecewise tween through [(time, value, ease_into_this_key), ...]."""
    if t <= frames[0][0]:
        return frames[0][1]
    for (t0, v0, _), (t1, v1, e) in zip(frames, frames[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
            return v0 + (v1 - v0) * (e or linear)(u)
    return frames[-1][1]


# ---------------------------------------------------------------- music time

class Grid:
    """Musical time. Bars and beats are 1-indexed like a DAW."""

    def __init__(self, bpm, bpb=4):
        self.bpm = bpm
        self.bpb = bpb
        self.spb = 60.0 / bpm
        self.bar_len = self.spb * bpb

    def at(self, bar, beat=1, sixteenth=0.0):
        return ((bar - 1) * self.bpb + (beat - 1) + sixteenth / 4.0) * self.spb

    def dur(self, beats):
        return beats * self.spb

    def beats(self, t):
        return t / self.spb

    def bar_of(self, t):
        return int(math.floor(t / self.bar_len)) + 1

    def beat_of(self, t):
        return int(math.floor(t / self.spb)) % self.bpb + 1

    def pulse(self, t, decay=0.12, every=1.0, offset=0.0):
        """Exponential flash that fires every `every` beats."""
        ph = ((t / self.spb) - offset) % every
        return math.exp(-ph * self.spb / decay)


# ---------------------------------------------------------------- noise

_rng = np.random.default_rng(1337)
_PERM = np.concatenate([_rng.permutation(256)] * 2).astype(np.int64)


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _grad(h, x, y, z):
    h = h & 15
    u = np.where(h < 8, x, y)
    v = np.where(h < 4, y, np.where((h == 12) | (h == 14), x, z))
    return np.where(h & 1, -u, u) + np.where(h & 2, -v, v)


def pnoise3(x, y, z):
    """Improved Perlin noise, vectorised; returns roughly [-1, 1]."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    xi = np.floor(x).astype(np.int64) & 255
    yi = np.floor(y).astype(np.int64) & 255
    zi = np.floor(z).astype(np.int64) & 255
    xf, yf, zf = x - np.floor(x), y - np.floor(y), z - np.floor(z)
    u, v, w = _fade(xf), _fade(yf), _fade(zf)
    P = _PERM
    a = P[xi] + yi
    aa, ab = P[a] + zi, P[a + 1] + zi
    b = P[xi + 1] + yi
    ba, bb = P[b] + zi, P[b + 1] + zi
    x1 = _grad(P[aa], xf, yf, zf) + u * (_grad(P[ba], xf - 1, yf, zf) - _grad(P[aa], xf, yf, zf))
    x2 = _grad(P[ab], xf, yf - 1, zf) + u * (_grad(P[bb], xf - 1, yf - 1, zf) - _grad(P[ab], xf, yf - 1, zf))
    y1 = x1 + v * (x2 - x1)
    x3 = _grad(P[aa + 1], xf, yf, zf - 1) + u * (_grad(P[ba + 1], xf - 1, yf, zf - 1) - _grad(P[aa + 1], xf, yf, zf - 1))
    x4 = _grad(P[ab + 1], xf, yf - 1, zf - 1) + u * (_grad(P[bb + 1], xf - 1, yf - 1, zf - 1) - _grad(P[ab + 1], xf, yf - 1, zf - 1))
    y2 = x3 + v * (x4 - x3)
    return y1 + w * (y2 - y1)


def noise1(x, seed=0.0):
    return float(pnoise3(x, seed * 7.31 + 0.5, seed * 3.17 + 0.25))


def fbm3(x, y, z, octaves=4, lac=2.0, gain=0.5):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for _ in range(octaves):
        total = total + amp * pnoise3(x * freq, y * freq, z * freq)
        norm += amp
        amp *= gain
        freq *= lac
    return total / norm


def hash01(i, seed=0):
    """Deterministic pseudo-random in [0, 1) for integer ids (scalar or array)."""
    i = np.asarray(i, dtype=np.float64)
    v = np.sin(i * 12.9898 + seed * 78.233 + 0.1) * 43758.5453
    return v - np.floor(v)


def rng(seed):
    return np.random.default_rng(seed)
