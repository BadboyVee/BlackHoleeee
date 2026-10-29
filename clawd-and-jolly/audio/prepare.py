# Unpacks the SND UI sound sprites and picks the cleanest sliced hits (sharp attack, quick decay)
# usage: python prepare.py SOUND_SRC SOUND_CACHE
import sys, os, glob, json
import numpy as np, soundfile as sf, librosa

src, cache = sys.argv[1], sys.argv[2]
for kit in ['01', '03']:
    base = f'{src}/npm/package/assets/sounds/sprite/{kit}'
    d = json.load(open(f'{base}/audioSprite.json'))
    y, sr = librosa.load(f'{base}/audioSprite.ogg', sr=48000, mono=False)
    if y.ndim == 1: y = np.stack([y, y])
    os.makedirs(f'{cache}/snd{kit}', exist_ok=True)
    for n, v in d['spritemap'].items():
        sf.write(f'{cache}/snd{kit}/{n}.wav', y[:, int(v['start'] * sr):int(v['end'] * sr)].T, sr)

res = {}
for kind in ['keys', 'tw', 'snow', 'bub']:
    good = []
    for f in sorted(glob.glob(f'{cache}/{kind}/*.wav')):
        y, sr = sf.read(f)
        if y.ndim > 1: y = y.mean(1)
        env = np.abs(y)
        tail = env[int(0.12 * sr):].mean() if len(y) > 0.12 * sr else 0
        head = env[:int(0.03 * sr)].mean()
        good.append((head / (tail + 1e-4), np.argmax(env) / sr, len(y) / sr, os.path.relpath(f, cache)))
    good.sort(reverse=True)
    res[kind] = [g[3] for g in good if g[1] < 0.02 and g[2] > 0.06][:24]
json.dump(res, open(f'{cache}/selected.json', 'w'), indent=1)
print({k: len(v) for k, v in res.items()})
