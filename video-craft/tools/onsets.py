# Sample-accurate onsets: band-pass (kick 40-120 Hz, clap/snare 1.5-5 kHz, hats 8k+), 2 ms envelopes,
# onset = where the envelope rise crosses half its local peak. Fit one beat grid to kicks and claps.
import sys, json, wave
import numpy as np
from scipy import signal
from PIL import Image, ImageDraw
wav, outdir = sys.argv[1], sys.argv[2]
w = wave.open(wav); SR = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2).astype(np.float64).mean(1) / 32768
def bp(lo, hi):
    sos = signal.butter(4, [lo, hi], btype='band', fs=SR, output='sos'); return signal.sosfiltfilt(sos, x)
def env(y, ms=2):
    n = int(SR * ms / 1000); return np.sqrt(np.convolve(y * y, np.ones(n) / n, mode='same'))
bands = {'kick': env(bp(40, 120), 4), 'clap': env(bp(1500, 5000), 2), 'hat': env(bp(8000, 16000), 1)}
def onsets(e, min_gap, k=4.0):
    d = np.maximum(np.diff(e, prepend=e[0]), 0)
    d = np.convolve(d, np.ones(int(SR * .003)) / int(SR * .003), mode='same')
    thr = np.median(d) + k * np.std(d)
    p, _ = signal.find_peaks(d, height=thr, distance=int(min_gap * SR))
    out = []
    for i in p:
        a = max(0, i - int(.03 * SR)); pk = e[i:i + int(.03 * SR)].max(); base = e[a:i].min()
        half = base + .5 * (pk - base); j = i
        while j > a and e[j] > half: j -= 1
        out.append(j / SR)
    return np.array(out)
K = onsets(bands['kick'], 0.3, 3.0); C = onsets(bands['clap'], 0.2, 4.0); Hh = onsets(bands['hat'], 0.08, 4.0)
print('kick onsets', len(K), np.round(K[:12], 3))
print('clap onsets', len(C), np.round(C[:12], 3))
import os
au = os.path.join(outdir, 'audio.json')                     # tempo guess from audio.py when present
per0 = float(np.median(np.diff(json.load(open(au))['beats']))) if os.path.exists(au) else 0.5
def fit(times, start):
    tt = times[times > start]; idx = np.round((tt - tt[0]) / per0)
    for _ in range(4):
        A = np.vstack([idx, np.ones_like(idx)]).T; (per, t0), *_ = np.linalg.lstsq(A, tt, rcond=None)
        r = tt - (t0 + per * idx); keep = np.abs(r) < max(0.008, 2.5 * r.std()); tt, idx = tt[keep], idx[keep]
    r = tt - (t0 + per * idx); return per, t0, r, tt
pk, tk, rk, kk = fit(K, K[0] - 0.01)
print(f'kick-only grid: {60 / pk:.3f} BPM, t0 {tk:.4f}, residual rms {1000 * rk.std():.2f} ms (n={len(kk)})')
# claps relative to the kick grid (beats 2 & 4?)
ph = ((C - tk) / pk) % 1
print('clap phase rel. kick grid (0 = on beat):', np.round(np.sort(ph)[:5], 3), '... median', round(float(np.median(((C[C > 4] - tk) / pk + .5) % 1 - .5)), 3))
# the beat index (mod 4) of claps
bi = np.round((C[C > 4] - tk) / pk).astype(int) % 4
print('clap beat-in-bar histogram (rel. first kick):', np.bincount(bi, minlength=4))
json.dump({'kick': K.tolist(), 'clap': C.tolist(), 'hat': Hh.tolist(), 'period': pk, 't0': tk}, open(f'{outdir}/onsets.json', 'w'))
# picture: a 4 s window (default 3.6-7.6 s, or argv 3-4), three band envelopes with the kick grid
W, Hh2 = 1600, 360; im = Image.new('RGB', (W, Hh2), 'white'); dr = ImageDraw.Draw(im)
a, b = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (3.6, 7.6)
for row, (name, e) in enumerate(bands.items()):
    seg = e[int(a * SR):int(b * SR)]; seg = seg / seg.max(); n = len(seg)
    for px in range(W):
        v = seg[int(px * n / W):int((px + 1) * n / W)].max(); y0 = 110 + row * 120
        dr.line([(px, y0), (px, y0 - 100 * v)], fill=(60, 60, 60))
    dr.text((4, row * 120 + 2), name, fill='red')
for g in tk + pk * np.arange(-10, 40):
    if a <= g <= b: X = (g - a) / (b - a) * W; dr.line([(X, 0), (X, Hh2)], fill=(0, 120, 255))
for s in np.arange(np.ceil(a * 10) / 10, b, .1):
    X = (s - a) / (b - a) * W; dr.line([(X, Hh2 - 8), (X, Hh2)], fill='black')
im.save(f'{outdir}/envelopes.png')
