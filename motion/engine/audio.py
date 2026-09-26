"""Sound from scratch: oscillators, drum and synth voices, effects, a mixer and a mastering chain.

No samples. Every kick, clap and chord is computed here from sine waves and noise.
"""
import math
import re
import wave

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 48000


def n_of(d):
    return max(0, int(round(d * SR)))


def tl(n):
    return np.arange(n) / SR


_NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
         "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def midi(s):
    if not isinstance(s, str):
        return s
    m = re.fullmatch(r"([A-G][#b]?)(-?\d)", s)
    return 12 * (int(m.group(2)) + 1) + _NOTE[m.group(1)]


def hz(s):
    return 440.0 * 2 ** ((midi(s) - 69) / 12)


# ---------------------------------------------------------------- oscillators

def phase(freq, n, ph0=0.0):
    if np.isscalar(freq):
        return (ph0 + np.arange(n) * (freq / SR)) % 1.0
    return (ph0 + np.cumsum(freq) / SR) % 1.0


def _blep(ph, dt):
    out = np.zeros_like(ph)
    dt = np.broadcast_to(np.asarray(dt, np.float64), ph.shape)
    m = ph < dt
    t = ph[m] / dt[m]
    out[m] = t + t - t * t - 1.0
    m = ph > 1.0 - dt
    t = (ph[m] - 1.0) / dt[m]
    out[m] = t * t + t + t + 1.0
    return out


def saw(freq, n, ph0=0.0):
    ph = phase(freq, n, ph0)
    dt = np.abs(np.asarray(freq, np.float64)) / SR
    return 2.0 * ph - 1.0 - _blep(ph, dt)


def square(freq, n, ph0=0.0, pw=0.5):
    ph = phase(freq, n, ph0)
    dt = np.abs(np.asarray(freq, np.float64)) / SR
    s = np.where(ph < pw, 1.0, -1.0)
    return s + _blep(ph, dt) - _blep((ph + 1.0 - pw) % 1.0, dt)


def sine(freq, n, ph0=0.0):
    return np.sin(2 * np.pi * phase(freq, n, ph0))


def tri(freq, n, ph0=0.0):
    return 2.0 * np.abs(2.0 * phase(freq, n, ph0) - 1.0) - 1.0


def noise(n, seed=None):
    return np.random.default_rng(seed).standard_normal(n) * 0.5


# ---------------------------------------------------------------- envelopes

def env_exp(n, decay, attack=0.0008, hold=0.0):
    t = tl(n)
    e = np.exp(-np.maximum(t - attack - hold, 0.0) / max(decay, 1e-5))
    if attack > 0:
        e *= np.clip(t / attack, 0.0, 1.0)
    return e


def adsr(n, a, d, s, r, gate):
    t = tl(n)
    e = np.where(t < a, t / max(a, 1e-5), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-5)))
    lvl = (gate / max(a, 1e-5)) if gate < a else s + (1 - s) * math.exp(-(gate - a) / max(d, 1e-5))
    rel = lvl * np.exp(-(t - gate) / max(r, 1e-5))
    return np.where(t < gate, e, rel)


def fade(x, fin=0.002, fout=0.005):
    n = len(x)
    a, b = min(n_of(fin), n), min(n_of(fout), n)
    y = x.copy()
    if a > 0:
        y[:a] *= np.linspace(0, 1, a)[:, None] if y.ndim == 2 else np.linspace(0, 1, a)
    if b > 0:
        y[n - b:] *= np.linspace(1, 0, b)[:, None] if y.ndim == 2 else np.linspace(1, 0, b)
    return y


# ---------------------------------------------------------------- filters

def filt(x, kind, fc, order=2):
    if kind == "bandpass":
        lo, hi = fc
        fc = (max(lo, 10.0), min(hi, SR / 2 * 0.98))
    else:
        fc = min(max(fc, 10.0), SR / 2 * 0.98)
    sos = signal.butter(order, fc, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def _biquad(kind, fc, q, gain_db=0.0):
    fc = min(max(fc, 15.0), SR * 0.45)
    w0 = 2 * math.pi * fc / SR
    cw, sw = math.cos(w0), math.sin(w0)
    al = sw / (2 * q)
    A = 10 ** (gain_db / 40)
    if kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "highpass":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "bandpass":
        b = [al, 0.0, -al]
        a = [1 + al, -2 * cw, 1 - al]
    elif kind == "peak":
        b = [1 + al * A, -2 * cw, 1 - al * A]
        a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind == "lowshelf":
        sq = 2 * math.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sq)]
        a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sq]
    elif kind == "highshelf":
        sq = 2 * math.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sq)]
        a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sq]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return b, a


def eq(x, kind, fc, q=0.707, gain_db=0.0):
    b, a = _biquad(kind, fc, q, gain_db)
    return signal.lfilter(b, a, x, axis=0)


def vfilt(x, kind, fc, q=0.707, block=64):
    """Time-varying biquad; fc is a per-sample array (or scalar). Works on mono or stereo."""
    if x.ndim == 2:
        return np.stack([vfilt(x[:, i], kind, fc, q, block) for i in range(x.shape[1])], 1)
    n = len(x)
    fcs = np.broadcast_to(np.asarray(fc, np.float64), (n,))
    y = np.empty(n)
    zi = np.zeros(2)
    for i in range(0, n, block):
        b, a = _biquad(kind, float(fcs[i]), q)
        y[i:i + block], zi = signal.lfilter(b, a, x[i:i + block], zi=zi)
    return y


# ---------------------------------------------------------------- stereo + effects

def pan(x, p=0.0):
    a = (max(-1.0, min(1.0, p)) + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], 1)


def st(x):
    return x if x.ndim == 2 else pan(x, 0.0)


def sat(x, drive=1.0):
    if drive <= 0:
        return x
    return np.tanh(x * drive) / math.tanh(drive)


def make_ir(t60=2.2, predelay=0.012, bright=9000, dark=2200, seed=5, er=0.35):
    n = n_of(t60 * 1.15)
    t = tl(n)
    rng = np.random.default_rng(seed)
    env = 10 ** (-3 * t / t60)
    ir = np.zeros((n, 2))
    k = np.clip(t / t60, 0, 1)
    for ch in range(2):
        w = rng.standard_normal(n)
        ir[:, ch] = (filt(w, "lowpass", bright) * (1 - k) + filt(w, "lowpass", dark) * k) * env
    ir *= np.clip(t / 0.03, 0, 1)[:, None]
    if er > 0:
        for i, (d, g) in enumerate([(0.0071, 1.0), (0.0113, 0.8), (0.0167, 0.7), (0.0231, 0.55),
                                    (0.0297, 0.45), (0.0373, 0.35), (0.0449, 0.3)]):
            ir[n_of(d), i % 2] += g * er * 6
    ir = np.vstack([np.zeros((n_of(predelay), 2)), ir])
    ir /= math.sqrt((ir ** 2).sum() / 2)
    return ir


_IR_CACHE = {}


def reverb(x, t60=2.2, predelay=0.012, bright=9000, dark=2200, seed=5, er=0.35):
    key = (t60, predelay, bright, dark, seed, er)
    if key not in _IR_CACHE:
        _IR_CACHE[key] = make_ir(*key)
    ir = _IR_CACHE[key]
    mono = st(x).mean(axis=1)
    wet = np.stack([signal.fftconvolve(mono, ir[:, 0])[:len(mono)],
                    signal.fftconvolve(mono, ir[:, 1])[:len(mono)]], 1)
    return wet * 0.25


def delay(x, dt, fb=0.45, taps=7, pingpong=True, lo=250, hi=6500):
    x = st(x)
    n = len(x)
    src = filt(x.mean(axis=1), "bandpass", (lo, hi))
    out = np.zeros((n, 2))
    d = n_of(dt)
    for k in range(1, taps + 1):
        s = k * d
        if s >= n:
            break
        g = fb ** (k - 1)
        if pingpong:
            out[s:, (k + 1) % 2] += src[:n - s] * g
        else:
            out[s:] += (src[:n - s] * g)[:, None] * 0.7
    return out


def duck(n, times, depth=0.75, attack=0.003, release=0.14):
    g = np.ones(n)
    L = n_of(attack + release * 5)
    tt = tl(L)
    env = np.where(tt < attack, tt / attack, np.exp(-(tt - attack) / release))
    for t in times:
        i = n_of(t)
        if i >= n:
            continue
        j = min(n, i + L)
        g[i:j] = np.minimum(g[i:j], 1 - depth * env[:j - i])
    return g


def compress(x, thresh_db=-16.0, ratio=3.0, tau=0.02, release=0.12, knee=6.0, makeup_db=0.0):
    x = st(x)
    pw = (x ** 2).mean(axis=1)
    a1 = math.exp(-1 / (tau * SR))
    lvl = signal.lfilter([1 - a1], [1, -a1], pw)
    db = 10 * np.log10(lvl + 1e-12)
    over = db - thresh_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    a2 = math.exp(-1 / (release * SR))
    gr = signal.lfilter([1 - a2], [1, -a2], gr)
    g = 10 ** ((makeup_db - gr) / 20)
    return x * g[:, None]


def limit(x, ceiling_db=-1.0, lookahead=0.003, release=0.08):
    c = 10 ** (ceiling_db / 20)
    peak = np.abs(x).max(axis=1)
    need = np.minimum(1.0, c / np.maximum(peak, 1e-9))
    L = max(1, n_of(lookahead))
    g = minimum_filter1d(need, size=2 * L + 1)
    g = uniform_filter1d(g, size=2 * L + 1)
    a = math.exp(-1 / (release * SR))
    # slow release: follow drops instantly, recover along a one-pole
    sm = signal.lfilter([1 - a], [1, -a], g - 1.0) + 1.0
    g = np.minimum(g, sm)
    return np.clip(x * g[:, None], -c, c)


# ---------------------------------------------------------------- drums

def kick(f_hi=230.0, f_lo=47.0, p_decay=0.04, a_decay=0.32, hold=0.03, drive=2.2, click=0.5,
         length=0.6, seed=0):
    n = n_of(length)
    t = tl(n)
    f = f_lo + (f_hi - f_lo) * np.exp(-t / p_decay)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    amp = np.where(t < hold, 1.0, np.exp(-(t - hold) / a_decay))
    body = sat(body * amp, drive)
    ck = filt(noise(n, seed), "highpass", 1800) * np.exp(-t / 0.0035)
    tick = np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.002)
    return fade(body + click * (0.9 * ck + 0.35 * tick), 0.0003, 0.01)


def clap(length=0.4, tone=1300.0, tail=0.13, seed=1):
    n = n_of(length)
    t = tl(n)
    w = noise(n, seed)
    e = np.zeros(n)
    for o in (0.0, 0.0105, 0.0205, 0.031):
        e += np.where(t >= o, np.exp(-(t - o) / 0.0055), 0.0)
    e += 0.85 * np.where(t >= 0.031, np.exp(-(t - 0.031) / tail), 0.0)
    x = filt(w, "bandpass", (tone * 0.62, tone * 3.4)) * e
    x += 0.25 * filt(w, "highpass", 6000) * np.exp(-t / 0.045)
    return fade(x * 2.2, 0.0002, 0.01)


def snare(f=185.0, length=0.32, tone=0.55, snappy=0.16, seed=2):
    n = n_of(length)
    t = tl(n)
    body = (np.sin(2 * np.pi * f * t) + 0.55 * np.sin(2 * np.pi * f * 1.78 * t)) * np.exp(-t / 0.075)
    nz = filt(noise(n, seed), "bandpass", (1800, 11000)) * np.exp(-t / snappy)
    return fade(tone * body + 1.4 * nz, 0.0002, 0.01)


_METAL = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)


def hat(decay=0.035, length=None, bright=1.0, seed=3):
    length = length or min(1.4, decay * 7 + 0.02)
    n = n_of(length)
    t = tl(n)
    m = sum(square(f * 1.47, n, ph0=(i * 0.137) % 1) for i, f in enumerate(_METAL))
    m = filt(m, "bandpass", (6800 * bright, 15500))
    nz = filt(noise(n, seed), "highpass", 7500 * bright)
    x = (0.55 * m / 6 + 0.9 * nz) * np.exp(-t / decay)
    return fade(x * 1.6, 0.0004, 0.004)


def ride(length=1.2, seed=4):
    n = n_of(length)
    t = tl(n)
    m = sum(square(f * 2.13, n, ph0=(i * 0.21) % 1) for i, f in enumerate(_METAL))
    m = filt(m, "bandpass", (4200, 13000))
    ping = np.sin(2 * np.pi * 3170 * t) * np.exp(-t / 0.25) * 0.08
    nz = filt(noise(n, seed), "highpass", 6000)
    x = (0.5 * m / 6 + 0.45 * nz) * np.exp(-t / 0.33) + ping
    return fade(x, 0.0005, 0.02)


def crash(length=2.4, seed=6):
    n = n_of(length)
    t = tl(n)
    m = sum(square(f * 3.1, n, ph0=(i * 0.31) % 1) for i, f in enumerate(_METAL))
    m = filt(m, "bandpass", (3000, 14000))
    nz = filt(noise(n, seed), "highpass", 3500)
    e = np.exp(-t / 0.65) * (0.3 + 0.7 * np.exp(-t / 0.06))
    x = (0.45 * m / 6 + 0.9 * nz) * e
    return fade(x, 0.001, 0.05)


def tom(f=110.0, length=0.45, seed=7):
    n = n_of(length)
    t = tl(n)
    fr = f * (1 + 0.6 * np.exp(-t / 0.04))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.2)
    x += 0.2 * filt(noise(n, seed), "bandpass", (400, 3000)) * np.exp(-t / 0.02)
    return fade(sat(x, 1.5), 0.0003, 0.01)


def rim(length=0.08, seed=8):
    n = n_of(length)
    t = tl(n)
    x = (np.sin(2 * np.pi * 1700 * t) + 0.6 * np.sin(2 * np.pi * 480 * t)) * np.exp(-t / 0.011)
    x += 0.4 * filt(noise(n, seed), "highpass", 3000) * np.exp(-t / 0.004)
    return fade(x, 0.0002, 0.005)


def tick(f=4200.0, length=0.03):
    n = n_of(length)
    t = tl(n)
    return fade(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.004), 0.0001, 0.003)


# ---------------------------------------------------------------- synth voices

def supersaw(freqs, length, voices=7, detune=0.22, attack=0.005, decay=0.35, sustain=0.6,
             release=0.25, gate=None, cutoff=5200.0, cut_env=0.0, cut_decay=0.2, width=0.9, seed=9, q=0.8):
    """Chord of detuned saws spread across the stereo field. Returns stereo."""
    gate = length - release if gate is None else gate
    n = n_of(length)
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    for f in np.atleast_1d(freqs):
        for v in range(voices):
            d = (v / (voices - 1) - 0.5) * 2 * detune if voices > 1 else 0.0
            s = saw(f * 2 ** (d / 12), n, rng.random())
            p = (v / (voices - 1) - 0.5) * 2 * width if voices > 1 else 0.0
            out += pan(s, p)
    out /= voices * math.sqrt(len(np.atleast_1d(freqs)))
    fc = cutoff * (1 + cut_env * np.exp(-tl(n) / cut_decay))
    out = vfilt(out, "lowpass", fc, q) if (cut_env or q != 0.707) else filt(out, "lowpass", cutoff)
    return out * adsr(n, attack, decay, sustain, release, gate)[:, None]


def reese(f, length, detune=0.16, cutoff=700.0, lfo=0.35, sub=0.8, drive=1.8, attack=0.004,
          release=0.05, seed=10):
    n = n_of(length)
    rng = np.random.default_rng(seed)
    x = sum(saw(f * 2 ** (d / 12), n, rng.random()) for d in (-detune, 0.0, detune * 0.63))
    fc = cutoff * (1 + 0.45 * np.sin(2 * np.pi * lfo * tl(n) + rng.random() * 6))
    x = vfilt(x / 3, "lowpass", fc, 1.1)
    x = sat(x * 1.3, drive) + sub * np.sin(2 * np.pi * f * tl(n))
    e = adsr(n, attack, 0.3, 0.9, release, length - release)
    return fade(x * e, 0.001, 0.005)


def acid(f, length, cutoff=450.0, env=2600.0, decay=0.16, q=7.0, accent=False, drive=2.4, slide=None):
    n = n_of(length)
    t = tl(n)
    fr = f if slide is None else f * (slide / f) ** np.exp(-t / 0.03)
    x = saw(fr, n)
    e = env * (1.8 if accent else 1.0)
    fc = cutoff + e * np.exp(-t / (decay * (0.7 if accent else 1.0)))
    y = sat(vfilt(x, "lowpass", fc, q), drive)
    amp = adsr(n, 0.003, 0.2, 0.85, 0.02, length - 0.02) * (1.25 if accent else 1.0)
    return fade(y * amp * 0.5, 0.001, 0.004)


def pluck(f, length=0.4, bright=5200.0, decay=0.09, amp_decay=0.25, wave="saw", q=1.2, ph0=0.0):
    n = n_of(length)
    t = tl(n)
    x = saw(f, n, ph0) if wave == "saw" else square(f, n, ph0, 0.35)
    fc = 180 + bright * np.exp(-t / decay)
    y = vfilt(x, "lowpass", fc, q, block=32)
    return fade(y * env_exp(n, amp_decay, 0.001), 0.0005, 0.01)


def bell(f, length=1.8, ratio=3.5, index=2.2, decay=0.9, bright=0.25):
    n = n_of(length)
    t = tl(n)
    mod = np.sin(2 * np.pi * f * ratio * t) * index * np.exp(-t / 0.22)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / decay)
    x += bright * np.sin(2 * np.pi * f * 4.07 * t) * np.exp(-t / 0.18)
    return fade(x * np.clip(t / 0.002, 0, 1), 0.0005, 0.02)


def epiano(f, length=1.6, vel=0.8, decay=1.1):
    n = n_of(length)
    t = tl(n)
    mod = np.sin(2 * np.pi * f * t) * (0.9 * vel) * np.exp(-t / 0.35)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / decay)
    x += 0.12 * vel * np.sin(2 * np.pi * f * 14.0 * t) * np.exp(-t / 0.018)
    return fade(x * np.clip(t / 0.0015, 0, 1), 0.0003, 0.03)


def piano(f, length=2.4, vel=0.75, decay=1.6, felt=0.6, seed=12):
    """Additive piano-ish tone with slightly stretched partials and a soft felt hammer."""
    n = n_of(length)
    t = tl(n)
    B = 0.00022
    x = np.zeros(n)
    for k in range(1, 11):
        fk = f * k * math.sqrt(1 + B * k * k)
        if fk > SR * 0.45:
            break
        amp = (1.0 / k ** (1.35 - 0.4 * vel)) * (1.0 if k == 1 else 0.8)
        x += amp * np.sin(2 * np.pi * fk * t + k * 0.7) * np.exp(-t / (decay / (1 + 0.35 * (k - 1))))
    ham = filt(noise(n, seed), "bandpass", (300, 2500 + 3000 * vel)) * np.exp(-t / 0.012) * 0.25
    x = x + ham
    x = filt(x, "lowpass", 1800 + 5200 * vel * (1 - felt * 0.5))
    return fade(x * np.clip(t / 0.003, 0, 1) * 0.5, 0.0005, 0.05)


def pad(freqs, length, attack=0.6, release=1.2, cutoff=1800.0, voices=5, detune=0.14, seed=13, width=1.0):
    return supersaw(freqs, length, voices=voices, detune=detune, attack=attack, decay=1.0, sustain=0.9,
                    release=release, cutoff=cutoff, width=width, seed=seed)


def braam(f, length=2.6, seed=14):
    n = n_of(length)
    t = tl(n)
    rng = np.random.default_rng(seed)
    x = saw(f, n, rng.random()) + saw(f * 1.006, n, rng.random()) + 0.7 * saw(f * 0.5, n, rng.random())
    x += 0.35 * square(f * 1.498, n, rng.random())
    fc = 180 + 2600 * np.clip(t / 0.12, 0, 1) * np.exp(-t / 0.9)
    y = sat(vfilt(x / 3, "lowpass", fc, 1.4), 3.0)
    y += 0.9 * np.sin(2 * np.pi * f * 0.5 * t)
    e = np.clip(t / 0.015, 0, 1) * np.exp(-t / 1.1)
    return fade(y * e, 0.001, 0.2)


def sub_drop(length=1.6, f0=72.0, f1=26.0):
    n = n_of(length)
    t = tl(n)
    fr = f1 + (f0 - f1) * np.exp(-t / 0.35)
    return fade(sat(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.7), 1.4), 0.0005, 0.1)


def riser(length, lo=350.0, hi=9000.0, tone=0.35, f0=110.0, f1=880.0, seed=15, curve=2.2):
    n = n_of(length)
    t = tl(n)
    k = (t / length) ** curve
    out = np.zeros((n, 2))
    for ch in range(2):
        w = noise(n, seed + ch)
        out[:, ch] = vfilt(w, "bandpass", lo * (hi / lo) ** k, 1.4)
    fr = f0 * (f1 / f0) ** k
    s = saw(fr, n) + saw(fr * 1.01, n)
    out += pan(filt(s, "lowpass", 5000) * tone * 0.4, 0.0)
    return fade(out * (0.08 + 0.92 * k)[:, None] * 1.4, 0.01, 0.004)


def downlifter(length=1.2, seed=16):
    n = n_of(length)
    t = tl(n)
    k = t / length
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = vfilt(noise(n, seed + ch), "bandpass", 8000 * (150 / 8000) ** k, 1.2)
    return fade(out * np.exp(-3 * k)[:, None] * 1.6, 0.001, 0.02)


def impact(length=2.8, seed=17):
    n = n_of(length)
    t = tl(n)
    boom = np.zeros(n)
    b = sub_drop(min(length, 2.0), 90, 28)
    boom[:len(b)] += b
    nz = vfilt(noise(n, seed), "lowpass", 200 + 9000 * np.exp(-t / 0.12), 0.9) * np.exp(-t / 0.35)
    body = st(boom * 1.1 + nz * 0.9)
    body += st(crash(length, seed + 1)) * 0.5
    return fade(body, 0.0002, 0.1)


def spike(length=0.012, seed=18):
    """An extracellular action potential as you'd hear it on a lab monitor: a sharp pop."""
    n = n_of(length)
    t = tl(n)
    x = -np.exp(-((t - 0.0012) / 0.00035) ** 2) + 0.45 * np.exp(-((t - 0.0022) / 0.0007) ** 2)
    return filt(x * 3.0, "bandpass", (300, 6000))


def reverse(x):
    return x[::-1].copy()


# ---------------------------------------------------------------- mixer

class Mix:
    def __init__(self, duration, tail=4.0):
        self.duration = duration
        self.n = n_of(duration + tail)
        self.buses = {}

    def bus(self, name):
        b = self.buses.get(name)
        if b is None:
            b = self.buses[name] = np.zeros((self.n, 2))
        return b

    def put(self, name, sig, t, gain=1.0, p=0.0):
        b = self.bus(name)
        s = sig if sig.ndim == 2 else pan(sig, p)
        i = n_of(t)
        if i < 0:
            s = s[-i:]
            i = 0
        j = min(self.n, i + len(s))
        if j > i:
            b[i:j] += s[:j - i] * gain


def lufs(x):
    import pyloudnorm as pyln
    return pyln.Meter(SR).integrated_loudness(x)


def master(x, target=-10.5, ceiling=-1.0, glue=True):
    x = filt(x, "highpass", 24, order=2)
    if glue:
        x = compress(x, thresh_db=-14, ratio=2.0, tau=0.015, release=0.15, knee=8)
    g = target - lufs(x)
    x = x * 10 ** ((g + 0.8) / 20)
    x = limit(x, ceiling)
    g2 = target - lufs(x)
    if abs(g2) > 0.3:
        x = limit(x * 10 ** (g2 / 20), ceiling)
    return x


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def frame_levels(x, fps=60, bands=10, duration=None):
    """Per-video-frame loudness in `bands` log-spaced bands, 0..1, for audio-reactive visuals."""
    mono = st(x).mean(axis=1)
    hop = SR // fps
    nfr = int(math.ceil((duration or len(mono) / SR) * fps))
    win = 2048
    pad_ = np.concatenate([np.zeros(win // 2), mono, np.zeros(win)])
    edges = np.geomspace(40, 16000, bands + 1)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    idx = [(freqs >= edges[i]) & (freqs < edges[i + 1]) for i in range(bands)]
    hann = np.hanning(win)
    out = np.zeros((nfr, bands))
    rms = np.zeros(nfr)
    for f in range(nfr):
        seg = pad_[f * hop: f * hop + win]
        if len(seg) < win:
            break
        spec = np.abs(np.fft.rfft(seg * hann))
        out[f] = [spec[m].mean() if m.any() else 0 for m in idx]
        rms[f] = math.sqrt(np.mean(seg[win // 4: 3 * win // 4] ** 2))
    out = 20 * np.log10(out + 1e-9)
    out = np.clip((out - out.max() + 60) / 60, 0, 1)
    rms = rms / (rms.max() + 1e-9)
    return out, rms


# ---------------------------------------------------------------- sound design: clicks and foley
# Every on-screen event gets a sound. These are the small ones.

def click(freq=2400.0, length=0.012, decay=0.0018, grit=0.3, seed=0):
    """A digital click: a sine burst a couple of milliseconds long with a tiny noise edge."""
    n = n_of(length)
    t = tl(n)
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t / decay) + grit * noise(n, seed) * np.exp(-t / 0.0007)
    return fade(x, 0.00004, 0.001)


def blip(freq=1000.0, length=0.05):
    """A pure sine blip with a smooth envelope: the sound of a data point."""
    n = n_of(length)
    t = tl(n)
    return np.sin(2 * np.pi * freq * t) * np.sin(np.pi * t / length) ** 2


def data_burst(length=0.25, rate=110.0, seed=0, lo=1400.0, hi=9500.0, decay_out=True):
    """Rapid random clicks, like characters decoding."""
    rng = np.random.default_rng(seed)
    n = n_of(length)
    out = np.zeros(n)
    t = 0.0
    while True:
        t += rng.exponential(1.0 / rate)
        if t >= length:
            break
        f = lo * (hi / lo) ** rng.random()
        c = click(f, 0.01, 0.0012 + 0.002 * rng.random(), 0.2, int(rng.integers(1e6)))
        i = n_of(t)
        j = min(n, i + len(c))
        out[i:j] += c[:j - i] * (0.4 + 0.6 * rng.random())
    if decay_out:
        out *= np.linspace(1.0, 0.35, n)
    return out


def flap(seed=0, lock=False):
    """One split-flap leaf falling: a papery clack with a small plastic body."""
    n = n_of(0.05 if not lock else 0.09)
    t = tl(n)
    rng = np.random.default_rng(seed)
    body = np.sin(2 * np.pi * (170 + 60 * rng.random()) * t) * np.exp(-t / (0.012 if not lock else 0.03))
    tick_ = filt(noise(n, seed), "bandpass", (1600, 7000)) * np.exp(-t / (0.004 if not lock else 0.007))
    return fade(0.5 * body + 1.3 * tick_ * (1.6 if lock else 1.0), 0.00005, 0.004)


def key(seed=0):
    """A typewriter key: sharp strike, a short thump from the carriage."""
    n = n_of(0.07)
    t = tl(n)
    rng = np.random.default_rng(seed)
    strike = filt(noise(n, seed), "bandpass", (2000, 8000)) * np.exp(-t / 0.0035)
    thump = np.sin(2 * np.pi * (110 + 50 * rng.random()) * t) * np.exp(-t / 0.012)
    return fade(1.2 * strike + 0.6 * thump, 0.00005, 0.004)


def whoosh(length=0.5, rise=True, seed=0, lo=250.0, hi=6000.0, pan_from=-0.6, pan_to=0.6):
    """Air moving past the camera: band-passed noise swept up or down, panned across."""
    n = n_of(length)
    t = tl(n)
    k = t / length
    fc = lo * (hi / lo) ** (k if rise else 1 - k)
    x = vfilt(noise(n, seed), "bandpass", fc, 1.1)
    env = np.sin(np.pi * np.clip(k, 0, 1)) ** 2 * (0.4 + 0.6 * (k if rise else 1 - k))
    x = x * env * 2.2
    p = pan_from + (pan_to - pan_from) * k
    ang = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return fade(np.stack([x * np.cos(ang), x * np.sin(ang)], 1), 0.002, 0.01)


def swish(length=0.32, seed=0):
    """A page turning."""
    n = n_of(length)
    t = tl(n)
    k = t / length
    x = vfilt(noise(n, seed), "bandpass", 900 + 3500 * np.sin(np.pi * k), 0.9)
    return fade(x * np.sin(np.pi * k) ** 1.5 * 1.6, 0.002, 0.01)


def ding(freq=2637.0, length=1.4):
    """The carriage-return bell."""
    return bell(freq, length, ratio=2.76, index=0.9, decay=0.55, bright=0.15)


def draw_tone(length=0.45, f0=600.0, f1=2400.0):
    """A thin rising sine that follows a line being drawn on."""
    n = n_of(length)
    t = tl(n)
    k = t / length
    fr = f0 * (f1 / f0) ** (k ** 0.7)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * k) ** 2 * 0.5
