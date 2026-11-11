"""Original soundtrack, fully synthesised (numpy / scipy), locked to tb/timeline.py.

    python3 tb/audio.py out.wav        or        audio.render(path) -> stats dict

Idea: watch-escapement ticks + sub drone + mechanical 'lock' accents through the assembly,
an original four-chord theme in D minor (Dm - Bb - F - C) when the lights come on, a thinner
glassy passage for the cabin, and a final resolving chord.  120 BPM, 48 kHz stereo.
"""
import os, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

try:
    from . import timeline as TL
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tb import timeline as TL

SR = 48000
rng = np.random.default_rng(7)
midi = lambda n: 440.0 * 2 ** ((n - 69) / 12.0)
CHORDS = [(38, [62, 65, 69]), (34, [58, 62, 65]), (41, [60, 65, 69]), (36, [60, 64, 67])]   # Dm Bb F C


def _t(n):
    return np.arange(n) / SR


def env_ad(n, a, d, curve=4.0):
    t = _t(n)
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) * curve / max(d, 1e-4))
    return e


def saw(f, n, detune=0.0, harm=None):
    t = _t(n)
    f = f * 2 ** (detune / 1200.0)
    H = harm or int(min(40, 9000 // f))
    out = np.zeros(n)
    ph = rng.uniform(0, 6.28)
    for k in range(1, H + 1):
        out += np.sin(2 * np.pi * f * k * t + ph * k) / k
    return out * 0.6


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, min(fc, SR * 0.45), 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, 'high', fs=SR, output='sos'), x)


def bp(x, f0, f1):
    return signal.sosfilt(signal.butter(2, [f0, f1], 'band', fs=SR, output='sos'), x)


class Mix:
    def __init__(self, dur):
        self.n = int(round(dur * SR))
        self.L = np.zeros(self.n); self.R = np.zeros(self.n)
        self.wetL = np.zeros(self.n); self.wetR = np.zeros(self.n)

    def add(self, x, t, gain=1.0, pan=0.0, wet=0.0):
        i = int(round(t * SR))
        if i >= self.n or i + len(x) <= 0:
            return
        x = x[max(0, -i):]; i = max(i, 0)
        x = x[:self.n - i] * gain
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.L[i:i + len(x)] += x * l; self.R[i:i + len(x)] += x * r
        if wet:
            self.wetL[i:i + len(x)] += x * l * wet; self.wetR[i:i + len(x)] += x * r * wet


# ------------------------------------------------------------------ instruments
def tick(bright=1.0):
    n = int(0.03 * SR)
    x = bp(rng.standard_normal(n), 3500, 9000 * min(bright, 1.2)) * env_ad(n, 0.0005, 0.012, 5)
    x += 0.5 * np.sin(2 * np.pi * 2400 * bright * _t(n)) * env_ad(n, 0.0003, 0.006, 6)
    return x


def tock():
    n = int(0.05 * SR)
    return bp(rng.standard_normal(n), 900, 2600) * env_ad(n, 0.0005, 0.02, 5) * 0.9


def kick(amp=1.0):
    n = int(0.36 * SR); t = _t(n)
    f = 46 + 95 * np.exp(-t * 34)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.002, 0.30, 4.5) * amp


def bell(note, dur=1.6, bright=1.0):
    n = int(dur * SR); t = _t(n); f = midi(note)
    mod = np.sin(2 * np.pi * f * 3.51 * t) * 2.2 * bright * np.exp(-t * 6)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 3.2)
    x += 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 7)
    return x * env_ad(n, 0.002, dur, 0.0001) * 0.5


def pluck(note, dur=0.22):
    n = int(dur * SR); f = midi(note)
    x = saw(f, n) + 0.6 * saw(f, n, 9)
    cut = signal.sosfilt(signal.butter(2, 2600, 'low', fs=SR, output='sos'), x)
    return cut * env_ad(n, 0.003, dur * 0.6, 5) * 0.5


def pad(notes, dur, cutoff=1400, soft=False):
    n = int(dur * SR)
    out = np.zeros(n)
    for nt in notes:
        f = midi(nt)
        if soft:
            t = _t(n)
            out += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 1.0) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t)
        else:
            out += saw(f, n, -7) + saw(f, n, 8) + 0.5 * saw(f * 0.5, n, 3)
    out = lp(out, cutoff, 2) / max(len(notes), 1)
    a = int(0.25 * SR); r = int(0.5 * SR)
    e = np.ones(n); e[:a] = np.linspace(0, 1, a) ** 1.5; e[-r:] *= np.linspace(1, 0, r)
    return out * e


def bass(note, dur=0.2):
    n = int(dur * SR); f = midi(note)
    x = lp(saw(f, n, harm=10), 520) + 0.8 * np.sin(2 * np.pi * f * _t(n))
    return x * env_ad(n, 0.004, dur * 0.8, 3.2) * 0.6


def lock(strength, var=0):
    """Mechanical lock accent: transient click + pitched metal ping + sub thump."""
    n = int(0.9 * SR); t = _t(n)
    click = hp(rng.standard_normal(n), 1800) * env_ad(n, 0.0004, 0.02, 6) * 0.9
    clank = bp(rng.standard_normal(n), 500, 3200) * env_ad(n, 0.001, 0.09, 5) * 0.6
    f0 = (1180, 1570, 1320, 1760, 990, 1480)[var % 6]
    ping = (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.41 * t + 0.4) + 0.3 * np.sin(2 * np.pi * f0 * 3.9 * t)) * np.exp(-t * 9) * 0.22
    fsub = 48 + 70 * np.exp(-t * 22)
    sub = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env_ad(n, 0.002, 0.45, 4) * 1.0
    return (click + clank + ping) * (0.5 + 0.5 * strength), sub * strength


def riser(dur):
    n = int(dur * SR); t = _t(n); u = t / dur
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    seg = 2048
    for i in range(0, n, seg):                      # time-varying band-pass sweep
        fc = 300 * (40 ** (i / n))
        out[i:i + seg] = bp(nz[max(0, i - seg):i + seg], fc, min(fc * 2.2, 20000))[-len(nz[i:i + seg]):]
    tone = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (u * 2.0)) / SR) * 0.25
    return (out * 0.5 + tone) * u ** 2.2


def render(path, duration=None, sr=SR):
    dur = duration or TL.DURATION
    m = Mix(dur)
    beat, bar = TL.BEAT, TL.BAR
    sec = {n: (a, b) for n, a, b, _ in TL.SECTIONS}

    # ---- drone (intro -> lights on), with slow filter opening
    n = int(12.6 * SR); t = _t(n)
    d = saw(midi(26), n, harm=14) + saw(midi(26), n, 11, harm=14) + 0.8 * np.sin(2 * np.pi * midi(26) * t)
    cut = np.zeros(n)
    for i in range(0, n, 4096):
        cut[i:i + 4096] = lp(d[max(0, i - 4096):i + 4096], 90 + 520 * (i / n) ** 2)[-len(d[i:i + 4096]):]
    e = np.minimum(t / 2.2, 1.0) ** 1.5 * np.minimum((12.6 - t) / 0.5, 1.0)
    m.add(cut * e, 0.0, 0.20, 0.0, 0.2)

    # ---- escapement ticks: sparse intro, full pulse in the assembly, delicate in the cabin
    k = 0
    tt = 0.5
    while tt < dur - 1.0:
        s = next((nm for nm, (a, b) in sec.items() if a <= tt < b), "finale")
        on = {"intro": k % 4 == 0, "assembly": True, "exterior": k % 2 == 1, "details": True,
              "interior": True, "finale": k % 2 == 1}[s]
        g = {"intro": 0.10, "assembly": 0.11 + 0.012 * (tt - 2), "exterior": 0.07, "details": 0.16,
             "interior": 0.07, "finale": 0.06}[s]
        if on:
            x = tick(1.0 if k % 2 == 0 else 0.8) if k % 4 != 2 else tock()
            m.add(x, tt, g * (1.25 if k % 4 == 0 else 1.0), 0.45 * (-1) ** k, 0.25)
        tt += beat / 2; k += 1

    # ---- lock accents on every timeline hit
    for i, (th, st, label) in enumerate(TL.HITS):
        hi, sub = lock(st, i)
        g = 0.40 if th < 12.0 else 0.30
        m.add(hi, th, g, 0.25 * (-1) ** i, 0.5)
        m.add(sub, th, g * 1.15, 0.0, 0.05)
    m.add(riser(2.0), 10.0, 0.5, 0.0, 0.4)
    big, bsub = lock(1.0, 3)
    m.add(kick(1.2), 12.0, 0.9); m.add(bell(74, 3.0, 1.4), 12.0, 0.5, 0.0, 0.8)

    # ---- theme sections
    motif = [0, 2, 1, 2, 0, 2, 1, 2]                      # arp shape over chord tones
    lead = {0: [(0, 81), (1.5, 77), (2.5, 74)], 1: [(0, 77), (1.5, 74), (3.0, 70)],
            2: [(0, 72), (1.5, 77), (2.5, 81)], 3: [(0, 79), (1.5, 76), (3.0, 72)]}

    def theme(t0, bars, level=1.0, drums=True, arp=True, melody=True):
        for b in range(bars):
            root, ch = CHORDS[b % 4]
            tb = t0 + b * bar
            m.add(pad(ch + [ch[0] + 12], bar + 0.4, 1500 + 500 * (b % 4 == 3)), tb - 0.05, 0.16 * level, -0.1, 0.5)
            m.add(pad([root + 12], bar + 0.2, 500), tb, 0.10 * level, 0.0, 0.1)
            for e8 in range(8):
                te = tb + e8 * beat / 2
                if e8 % 2 == 0 or b % 2 == 1:
                    m.add(bass(root if e8 % 4 else root - 0, beat / 2 * 0.95), te, 0.34 * level, 0.0, 0.0)
                if drums and e8 % 2 == 0:
                    m.add(kick(), te, 0.50 * level)
                if arp:
                    for s16 in range(2):
                        idx = (e8 * 2 + s16)
                        nt = ch[motif[idx % 8] % 3] + 12 + (12 if idx % 8 >= 6 and b % 2 else 0)
                        m.add(pluck(nt), te + s16 * beat / 4, 0.10 * level, 0.55 * (-1) ** idx, 0.35)
            if melody:
                for off, nt in lead[b % 4]:
                    m.add(bell(nt, 1.4, 0.9), tb + off * beat, 0.20 * level, 0.15, 0.7)

    theme(12.0, 2, 0.9)
    theme(16.0, 2, 1.0)
    theme(20.0, 2, 1.08)
    # details: stripped back
    for b in range(2):
        root, ch = CHORDS[b % 4]
        tb = 24.0 + b * bar
        for e8 in range(8):
            m.add(bass(root, 0.22), tb + e8 * beat / 2, 0.30 if e8 % 2 == 0 else 0.16)
        m.add(bell(ch[2] + 12, 1.6), tb, 0.22, -0.3, 0.8); m.add(bell(ch[0] + 24, 1.2), tb + 1.0, 0.14, 0.3, 0.8)
    # interior: airy pad, bells, rising gesture as the doors lift
    n = int(2.4 * SR); t = _t(n)
    up = np.sin(2 * np.pi * np.cumsum(midi(50) * 2 ** (t / 2.4 * 1.0)) / SR) * np.sin(np.pi * t / 2.4) ** 2
    m.add(up + 0.5 * lp(rng.standard_normal(n), 2500) * (t / 2.4) ** 2, 28.0, 0.12, 0.0, 0.8)
    pent = [74, 77, 81, 84, 86, 81, 77, 89]
    for b in range(4):
        root, ch = CHORDS[b % 4]
        tb = 28.0 + b * bar
        m.add(pad(ch + [ch[1] + 12], bar + 0.5, 900, soft=True), tb - 0.05, 0.075 if b < 2 else 0.10, 0.0, 0.7)
        m.add(pad([root + 12], bar + 0.3, 300, soft=True), tb, 0.07, 0.0, 0.1)
        for j, off in enumerate((0.0, 1.5, 2.5, 3.25)):
            m.add(bell(pent[(b * 3 + j) % 8], 1.8, 0.7), tb + off * beat, 0.15 if b >= 2 else 0.11, 0.5 * (-1) ** j, 0.9)
    m.add(bell(86, 3.0, 1.2), 32.0, 0.22, 0.0, 1.0)
    # finale
    theme(36.0, 1, 1.1)
    root, ch = CHORDS[0]
    m.add(pad([50, 57, 62, 65, 69, 74], 2.6, 1800), 38.0, 0.30, 0.0, 0.8)
    m.add(kick(1.3), 38.0, 0.9); m.add(bell(86, 2.4, 1.3), 38.0, 0.3, 0.0, 1.0); m.add(bell(74, 2.4), 38.0, 0.3, 0.0, 1.0)
    m.add(np.sin(2 * np.pi * midi(26) * _t(int(1.8 * SR))) * env_ad(int(1.8 * SR), 0.01, 1.6, 3), 38.0, 0.4)

    # ---- reverb (synthetic decaying-noise impulse response), master
    n_ir = int(2.2 * SR); t = _t(n_ir)
    irL = hp(lp(rng.standard_normal(n_ir), 7000), 250) * np.exp(-t * 3.1)
    irR = hp(lp(rng.standard_normal(n_ir), 7000), 250) * np.exp(-t * 3.1)
    wl = signal.fftconvolve(m.wetL, irL)[:m.n] * 0.03
    wr = signal.fftconvolve(m.wetR, irR)[:m.n] * 0.03
    Lc, Rc = hp(m.L + wl, 28), hp(m.R + wr, 28)
    mid_lo = lp((Lc + Rc) * 0.5, 120)                    # keep the low end mono
    Lc = hp(Lc, 120) + mid_lo; Rc = hp(Rc, 120) + mid_lo
    st = np.stack([Lc, Rc], axis=1)
    tt_ = _t(m.n)
    st *= (np.minimum(tt_ / 0.4, 1.0) * np.clip((dur - 0.05 - tt_) / 1.1, 0, 1) ** 1.5)[:, None]
    # loudness: target about -15 dB K-ish RMS over the theme, then soft limit to -1 dBFS
    ref = st[int(12 * SR):int(24 * SR)]
    rms = np.sqrt((hp(ref.mean(1), 100) ** 2).mean())
    st *= (10 ** (-18.5 / 20)) / max(rms, 1e-6)
    st = np.tanh(st * 1.15) / 1.15
    peak = np.abs(st).max()
    lim = 10 ** (-2.2 / 20)
    if peak > lim:
        st *= lim / peak
    st[-int(0.02 * SR):] = 0.0
    wavfile.write(path, SR, (st * 32767).astype(np.int16))
    stats = dict(samples=int(m.n), peak_dbfs=float(20 * np.log10(np.abs(st).max() + 1e-9)))
    for nm, (a, b) in sec.items():
        seg = st[int(a * SR):int(b * SR)]
        stats["rms_" + nm] = float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9))
    return stats


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "soundtrack.wav"
    print(render(out))
