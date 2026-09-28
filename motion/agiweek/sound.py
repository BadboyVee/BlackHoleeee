"""AGI WEEK sound: the reference clip's own soundtrack, supplied with it (photos/agiweek/sound.wav, not in the
repository). It is eased out over its own last moments, then trimmed or padded with silence to the film (whose
last second holds the maker's mark), and kept just under full scale so the delivery encode has room."""
import wave

import numpy as np

from engine import audio as A
from .score import DURATION


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
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(sr, A.SR)
        x = resample_poly(x, A.SR // g, sr // g, axis=0)
    return x[:, :2]


def prepare(src, dst, fade=0.35, peak=0.94):
    x = read_wav(src)
    n = A.n_of(DURATION)
    x = x[:n].copy()
    m = min(len(x), A.n_of(fade))
    x[-m:] *= np.linspace(1.0, 0.0, m)[:, None] ** 1.5
    if len(x) < n:
        x = np.vstack([x, np.zeros((n - len(x), 2))])
    top = np.abs(x).max()
    if top > peak:
        x *= peak / top
    A.write_wav(dst, x)
    return x
