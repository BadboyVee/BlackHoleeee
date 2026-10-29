# Cut single hits out of longer real recordings (keyboard, typewriter, footsteps) by onset detection.
# usage: python slice.py input.mp3 outdir prefix [maxlen_s]
import sys, os, numpy as np, librosa, soundfile as sf
src, out, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
maxlen = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
os.makedirs(out, exist_ok=True)
y, sr = librosa.load(src, sr=48000, mono=True)
on = librosa.onset.onset_detect(y=y, sr=sr, units='samples', backtrack=True, hop_length=256, delta=0.08)
peaks = []
for i, s0 in enumerate(on):
    e = on[i + 1] if i + 1 < len(on) else len(y)
    e = min(e, s0 + int(maxlen * sr))
    seg = y[s0:e].copy()
    if len(seg) < 0.03 * sr: continue
    pk = np.abs(seg).max()
    if pk < 0.02: continue
    fade = int(0.01 * sr); seg[-fade:] *= np.linspace(1, 0, fade)
    seg[:64] *= np.linspace(0, 1, 64)
    peaks.append((pk, seg))
for k, (pk, seg) in enumerate(peaks):
    sf.write(os.path.join(out, f'{prefix}_{k:03d}.wav'), seg / max(pk, 1e-6) * 0.9, sr)
print(len(peaks), 'hits from', src)
