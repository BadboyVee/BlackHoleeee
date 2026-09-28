"""DevDay 2026 sound: the teaser's own soundtrack (photos/devday/sound.wav, not in the repository) and nothing else,
cut on its bar lines. The teaser runs at 120 BPM with its first downbeat at 1.3 s. Its first two beats of clicks
play twice under "Introducing…" (two beats, so the clicks stay on the grid), then its opening plays as it is up to
the drop, its four bars loop under the launches (two launches a bar), and its last bar and long low note end the
film. The low note is held a little longer by looping one steady stretch of it (a whole number of its cycles, so
the joins are seamless) under the maker's mark."""
import wave

import numpy as np

from engine import audio as A
from .score import DURATION, T_OPEN, T_LIST, BAR, LIST_BARS, T_ENDING, OPEN_LOOP

ENDING = (7.29, 12.16)          # the teaser's last bar, its quiet, and its long low note
HOLD_AT = 11.60                 # where the low note is still steady...
HOLD_LOOP = 0.98275             # ...and one stretch of it that loops cleanly (34 cycles of its 34.6 Hz)
HOLD_TIMES = 2


def read_wav(path):
    with wave.open(path, "rb") as w:
        n, ch, sr, width = w.getnframes(), w.getnchannels(), w.getframerate(), w.getsampwidth()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError(f"{path}: expected 16-bit PCM")
    x = np.frombuffer(raw, "<i2").astype(np.float64).reshape(-1, ch) / 32768.0
    if ch == 1:
        x = np.repeat(x, 2, axis=1)
    if sr != A.SR:
        from math import gcd
        from scipy.signal import resample_poly
        g = gcd(sr, A.SR)
        x = resample_poly(x, A.SR // g, sr // g, axis=0)
    return x[:, :2]


def join(x, spans, h=0.02):
    """Source spans (seconds) played back to back, each join crossfaded over 2h."""
    hn = A.n_of(h)
    total = sum(A.n_of(e) - A.n_of(s) for s, e in spans)
    out = np.zeros((total + 2 * hn, 2))
    pos = 0
    for i, (s, e) in enumerate(spans):
        i0, i1 = A.n_of(s), A.n_of(e)
        a = i0 - hn if i > 0 else i0
        b = min(i1 + hn, len(x)) if i < len(spans) - 1 else i1
        seg = x[a:b].copy()
        if i > 0:
            seg[:2 * hn] *= np.linspace(0, 1, 2 * hn)[:, None]
        if i < len(spans) - 1:
            k = min(2 * hn, len(seg))
            seg[-k:] *= np.linspace(1, 0, k)[:, None]
        at = pos - (hn if i > 0 else 0)
        out[at:at + len(seg)] += seg
        pos += i1 - i0
    return out[:total]


def piece(x, a, b, fade_in=0.004, tail=0.012):
    """x from a to b, with a short fade in and a tail that fades out just past b."""
    seg = x[A.n_of(a):A.n_of(b + tail)].copy()
    fi, ft = A.n_of(fade_in), A.n_of(tail)
    if fi > 0:
        seg[:fi] *= np.linspace(0, 1, fi)[:, None]
    if ft > 0:
        seg[-ft:] *= np.linspace(1, 0, ft)[:, None]
    return seg


def add(out, t, seg):
    i = A.n_of(t)
    n = min(len(seg), len(out) - i)
    out[i:i + n] += seg[:n]


def prepare(src, dst, peak=0.94):
    x = read_wav(src)
    out = np.zeros((A.n_of(DURATION), 2))
    a, b = OPEN_LOOP
    loops = int(round(T_OPEN / (b - a)))
    for k in range(loops):
        add(out, k * (b - a), piece(x, a, b, fade_in=0.0 if k == 0 else 0.004))
    add(out, T_OPEN, piece(x, 0.0, T_LIST - T_OPEN - 0.01))
    for k, b in enumerate(LIST_BARS):
        add(out, T_LIST - 0.01 + BAR * k, piece(x, b, b + BAR))
    spans = [(ENDING[0], HOLD_AT)] + [(HOLD_AT - HOLD_LOOP, HOLD_AT)] * HOLD_TIMES + [(HOLD_AT, ENDING[1])]
    ending = join(x, spans)
    ending[:A.n_of(0.004)] *= np.linspace(0, 1, A.n_of(0.004))[:, None]
    add(out, T_ENDING, ending)
    top = np.abs(out).max()
    if top > peak:
        out *= peak / top
    A.write_wav(dst, out)
    return out
