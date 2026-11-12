# Soundtrack analysis: onset envelope, tempo, beat grid, band energies, loudness, spectrogram image.
import sys, json, wave
import numpy as np
from scipy import signal
from PIL import Image, ImageDraw
wav, outdir = sys.argv[1], sys.argv[2]
w = wave.open(wav); SR = w.getframerate(); ch = w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, ch).astype(np.float64) / 32768
mono = x.mean(1); side = (x[:, 0] - x[:, 1]) / 2 if ch == 2 else np.zeros_like(mono)
dur = len(mono) / SR
hop = 441; nfft = 2048                                   # 10 ms hop
f, t, Z = signal.stft(mono, SR, nperseg=nfft, noverlap=nfft - hop, boundary=None)
S = np.abs(Z); t = t
logS = np.log1p(S * 50)
# onset strength: half-wave rectified spectral flux
flux = np.maximum(np.diff(logS, axis=1), 0).sum(0); flux = np.concatenate([[0], flux])
flux = (flux - flux.mean()) / (flux.std() + 1e-9)
# tempo via autocorrelation of the onset envelope (60-200 BPM)
env = flux - np.convolve(flux, np.ones(40) / 40, mode='same')
ac = np.correlate(env, env, mode='full')[len(env) - 1:]
lags = np.arange(len(ac)) * hop / SR
bpm_c = 60 / lags[1:]; m = (bpm_c >= 60) & (bpm_c <= 200)
cand = sorted(((ac[1:][m][i], bpm_c[m][i]) for i in range(m.sum())), reverse=True)[:8]
# fine tempo by comb scoring
def comb(bpm):
    period = 60 / bpm / (hop / SR); score = 0
    best = 0
    for ph in np.linspace(0, period, 40, endpoint=False):
        idx = np.arange(ph, len(env), period).astype(int); s = env[idx].sum()
        best = max(best, s)
    return best
grid = np.arange(70, 180, 0.1); scores = np.array([comb(b) for b in grid])
bpm = grid[scores.argmax()]
# beat tracking (Ellis DP) with that tempo
period = 60 / bpm / (hop / SR)
N = len(env); D = env.copy(); back = -np.ones(N, int)
for i in range(N):
    lo, hi = int(i - 2 * period), int(i - period / 2)
    if hi <= 0: continue
    lo = max(lo, 0); js = np.arange(lo, hi)
    pen = -100 * (np.log((i - js) / period)) ** 2
    k = np.argmax(D[js] + pen); D[i] = env[i] + D[js][k] + pen[k]; back[i] = js[k]
i = int(np.argmax(D[-int(period):])) + N - int(period); beats = []
while i >= 0: beats.append(i); i = back[i]
beats = np.array(beats[::-1]) * hop / SR
# band energies (dB) per 10 ms
def band(lo, hi):
    mm = (f >= lo) & (f < hi); return 10 * np.log10((S[mm] ** 2).sum(0) + 1e-12)
bands = {'sub': band(20, 60), 'bass': band(60, 250), 'lowmid': band(250, 2000), 'himid': band(2000, 6000), 'air': band(6000, 16000)}
rms = 20 * np.log10(np.sqrt(np.convolve(mono ** 2, np.ones(hop * 5) / (hop * 5), mode='same')[::hop]) + 1e-9)[:len(t)]
centroid = (f[:, None] * S).sum(0) / (S.sum(0) + 1e-9)
flat = np.exp(np.log(S + 1e-9).mean(0)) / (S.mean(0) + 1e-9)
width = 20 * np.log10(np.sqrt(np.convolve(side ** 2, np.ones(hop * 5) / (hop * 5), mode='same')[::hop]) + 1e-9)[:len(t)] - rms
json.dump({'sr': SR, 'dur': dur, 'hop': hop / SR, 'bpm': float(bpm), 'ac_candidates': [[float(a), float(b)] for a, b in cand],
           'beats': beats.tolist(), 'flux': flux.tolist(), 'rms': rms.tolist(), 'centroid': centroid.tolist(), 'flatness': flat.tolist(),
           'width': width.tolist(), 'bands': {k: v.tolist() for k, v in bands.items()}}, open(f'{outdir}/audio.json', 'w'))
# spectrogram image: log-frequency rows 30 Hz - 16 kHz, 100 px per second
W = int(dur * 100); Hh = 420
fr = np.geomspace(30, 16000, Hh)
rowsI = np.searchsorted(f, fr)
img = logS[rowsI][::-1]; img = img[:, :W]
img = (255 * (img - img.min()) / (np.percentile(img, 99.7) - img.min())).clip(0, 255).astype(np.uint8)
im = Image.fromarray(img).convert('RGB')
canvas = Image.new('RGB', (W, Hh + 140), 'white'); canvas.paste(im, (0, 0)); dr = ImageDraw.Draw(canvas)
for s in range(int(dur) + 1):
    dr.line([(s * 100, 0), (s * 100, Hh + 20)], fill=(255, 255, 0) if s % 5 else (255, 80, 80)); dr.text((s * 100 + 2, Hh + 2), f'{s}s', fill='black')
for b in beats: dr.line([(b * 100, Hh + 20), (b * 100, Hh + 40)], fill='blue')
r = np.array(rms[:W]); rr = (r - r.max() + 40).clip(0, 40) / 40
for xx in range(1, len(rr)): dr.line([(xx - 1, Hh + 138 - 90 * rr[xx - 1]), (xx, Hh + 138 - 90 * rr[xx])], fill='black')
for hz, lab in ((60, '60'), (250, '250'), (1000, '1k'), (4000, '4k'), (10000, '10k')):
    y = Hh - 1 - int(np.searchsorted(fr, hz)); dr.line([(0, y), (12, y)], fill='cyan'); dr.text((14, y - 6), lab, fill='cyan')
canvas.save(f'{outdir}/spectrogram.png')
for k in range(0, W, 1600): canvas.crop((k, 0, min(W, k + 1600), Hh + 140)).save(f'{outdir}/spec_{k // 1600}.png')
print('dur', round(dur, 3), 'bpm', round(bpm, 2), 'ac top', [(round(b, 1)) for a, b in cand[:5]], 'beats', len(beats))
print('beats:', [round(b, 3) for b in beats])
