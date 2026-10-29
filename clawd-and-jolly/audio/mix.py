# Sound design and mix for the film. Every sound is a real recording (see CREDITS.md); this
# script only cuts, places, pitches (by resampling), filters, pans and mixes them on the
# cue times exported from the animation (audio/cues_*.json).
# usage: python audio/mix.py out.wav
import json, os, sys, glob
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

SR = 48000
DUR = 60.0
N = int(SR * DUR)
SRC = os.environ.get('SOUND_SRC', '/opt/dl')
CACHE = os.environ.get('SOUND_CACHE', '/opt/film/audio/cache')
HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC = f'{SRC}/debs/x/wesnoth-1.16-music/usr/share/games/wesnoth/1.16/data/core/music/silvan_sanctuary.ogg'
MOOD = f'{SRC}/moodist/public/sounds'
SP = f'{SRC}/sonicpi/etc/samples'
rng = np.random.default_rng(7)

_cache = {}
def load(path):
    if path not in _cache:
        y, sr = librosa.load(path, sr=SR, mono=False)
        if y.ndim == 1: y = np.stack([y, y])
        _cache[path] = y.astype(np.float32)
    return _cache[path]

def db(x): return 10 ** (x / 20)

def filt(y, lp=None, hp=None):
    if lp: y = sosfilt(butter(2, lp, 'low', fs=SR, output='sos'), y, axis=-1)
    if hp: y = sosfilt(butter(2, hp, 'high', fs=SR, output='sos'), y, axis=-1)
    return y

def resamp(y, rate):
    if abs(rate - 1) < 1e-3: return y
    n = int(y.shape[1] / rate)
    x = np.linspace(0, y.shape[1] - 1, n)
    return np.stack([np.interp(x, np.arange(y.shape[1]), ch) for ch in y])

sfx = np.zeros((2, N), np.float32)
send = np.zeros((2, N), np.float32)
beds = np.zeros((2, N), np.float32)

def place(y, t, gain=0.0, pan=0.0, rate=1.0, lp=None, hp=None, rev=0.15, start=0.0, length=None, fade_in=0.0, fade_out=0.005, bus=None):
    y = y[:, int(start * SR):]
    if length is not None: y = y[:, :int(length * SR)]
    y = resamp(y, rate)
    y = filt(y, lp, hp)
    y = y * db(gain)
    if fade_in > 0: k = min(y.shape[1], int(fade_in * SR)); y[:, :k] *= np.linspace(0, 1, k)
    if fade_out > 0: k = min(y.shape[1], int(fade_out * SR)); y[:, -k:] *= np.linspace(1, 0, k)
    a = np.pi / 4 * (1 + np.clip(pan, -1, 1))
    y = np.stack([y[0] * np.cos(a) * 1.414, y[1] * np.sin(a) * 1.414])
    i0 = int(t * SR)
    if i0 >= N: return
    if i0 < 0: y = y[:, -i0:]; i0 = 0
    n = min(y.shape[1], N - i0)
    (bus if bus is not None else sfx)[:, i0:i0 + n] += y[:, :n]
    if rev > 0: send[:, i0:i0 + n] += y[:, :n] * rev

def bed(path, t0, t1, level, fade_in=1.0, fade_out=1.0, start=0.0, lp=None, hp=None, rev=0.0):
    # level is the target RMS (dBFS) of the filtered bed, so beds sit predictably under the music
    y = load(path)[:, int(start * SR):int((start + t1 - t0 + 0.1) * SR)]
    yf = filt(y, lp, hp)
    rms = np.sqrt(np.mean(yf ** 2)) + 1e-9
    place(y, t0, level - 20 * np.log10(rms), 0, 1.0, lp, hp, rev, fade_in=fade_in, fade_out=fade_out, bus=beds)

sel = json.load(open(f'{CACHE}/selected.json'))
KEYS = [load(os.path.join(CACHE, f)) for f in sel['keys']]
TW = [load(os.path.join(CACHE, f)) for f in sel['tw']]
SNOW = [load(os.path.join(CACHE, f)) for f in sel['snow']]
BUB = [load(os.path.join(CACHE, f)) for f in sel['bub']]
def sp(n): return load(f'{SP}/{n}.flac')
def snd(kit, n): return load(f'{CACHE}/snd{kit}/{n}.wav')
def pick(lst): return lst[rng.integers(len(lst))]

cues = []
for f in sorted(glob.glob(f'{HERE}/cues_*.json')):
    cues += json.load(open(f))
def at(kind): return sorted([c for c in cues if c['type'] == kind], key=lambda c: c['t'])

# ---------------------------------------------------------------- beds
bed(f'{MOOD}/animals/crickets.mp3', 0.0, 52.5, -41, fade_in=2.5, fade_out=2.5, start=12.0, hp=900)
bed(f'{MOOD}/things/clock.mp3', 0.0, 16.0, -43, fade_in=1.5, fade_out=3.0, lp=5000, rev=0.1)
bed(f'{MOOD}/animals/birds.mp3', 50.8, 60.0, -35, fade_in=2.8, fade_out=1.6, start=20.0, rev=0.05)
bed(f'{MOOD}/nature/wind.mp3', 43.0, 51.5, -40, fade_in=4.0, fade_out=1.5, start=5.0, lp=3000)
bed(f'{MOOD}/nature/wind-in-trees.mp3', 50.4, 60.0, -44, fade_in=1.0, fade_out=2.0, start=10.0)
# a soft cooling hiss while the voxels glow
place(sp('vinyl_hiss'), 12.4, -38, 0, 1.0, 6000, 1500, 0.0, length=3.4, fade_in=0.2, fade_out=2.6)

# ---------------------------------------------------------------- opening: cursor, pixels leave the screen
for c in at('cursor_on'):
    if c['t'] < 7.2: place(snd('01', 'tap_0%d' % (1 + int(c['t']) % 5)), c['t'], -27 - c['t'] * 0.6, 0.1, 1.0, None, 800, 0.25)
place(sp('ambi_swoosh'), 6.9, -17, -0.1, 1.15, None, 120, 0.3, fade_in=0.4)
place(load(f'{MOOD}/things/singing-bowl.mp3'), 7.6, -24, 0, 1.0, None, 200, 0.35, start=1.0, length=6.0, fade_in=0.3, fade_out=3.0)
for j, c in enumerate(at('vox_launch')):
    if c['z'] != 0 and j % 2: continue
    pan = (c['x'] - 8.5) / 9 * 0.5 - 0.15
    place(pick(KEYS), c['t'], -33 + rng.uniform(-3, 2), pan, rng.uniform(1.5, 2.1), None, 1500, 0.2)
    if rng.random() < 0.25: place(snd('01', 'type_0%d' % rng.integers(1, 6)), c['t'] + 0.01, -30, pan, 1.0, None, 600, 0.2)
for c in at('vox_arrive'):
    pan = (c['x'] - 8.5) / 9 * 0.45 - 0.1
    place(pick(KEYS), c['t'], -26 + rng.uniform(-3, 2), pan, rng.uniform(0.85, 1.15), None, 300, 0.2)
for c in at('eye_arrive'):
    place(sp('perc_snap'), c['t'], -15, 0, 1.0, None, 300, 0.25)
place(sp('elec_chime'), 12.63, -24, 0.05, 1.0, None, 400, 0.4)
for k in range(6): place(pick(KEYS), 12.58 + k * 0.012, -17, rng.uniform(-0.3, 0.3), 0.8, None, 150, 0.25)
for c in at('blink'): place(snd('01', 'tap_03'), c['t'], -24, -0.1, 1.0, None, 600, 0.2)
for c in at('drop'): place(sp('perc_swoosh'), c['t'] - 0.08, -17, -0.1, 0.9, None, 300, 0.2)

# ---------------------------------------------------------------- keyboard
for c in at('land_keys'):
    big = c.get('big', False)
    pan = np.clip(c['x'] / 18, -0.5, 0.5)
    for k in range(4 if big else 2):
        place(pick(KEYS), c['t'] + k * 0.007, (-10 if big else -14) - k * 2, pan, rng.uniform(0.8, 1.0), None, 120, 0.2)
    place(sp('drum_bass_soft'), c['t'], -13 if big else -21, pan, 1.0, 2500, 40, 0.15)
    if big: place(sp('bd_fat'), c['t'], -17, 0, 1.0, None, 30, 0.1)
for c in at('hop'): place(pick(KEYS), c['t'], -27, np.clip(c.get('x', 0) / 18, -0.5, 0.5), 1.35, None, 1200, 0.1)
for c in at('land_alu'): place(pick(TW), c['t'], -17, 0.4, 1.1, None, 500, 0.2)
for c in at('spin'): place(sp('perc_swash'), c['t'] + 0.05, -20, 0.1, 1.0, None, 300, 0.2)
for c in at('peek'): place(sp('elec_plip'), c['t'], -27, 0.3, 1.0, None, 300, 0.25)
for c in at('jump'): place(sp('perc_swoosh'), c['t'] - 0.05, -16, 0.3, 0.8, None, 200, 0.2)

# ---------------------------------------------------------------- desk and moss
for c in at('land_wood'):
    place(sp('drum_tom_lo_soft'), c['t'], -12, 0.2, 1.0, 3000, 50, 0.2)
    place(sp('elec_wood'), c['t'], -19, 0.2, 0.9, None, 200, 0.2)
for c in at('shake'):
    for k in range(14): place(pick(KEYS), c['t'] + k * c['dur'] / 14 + rng.uniform(0, 0.01), -24 + rng.uniform(-3, 2), rng.uniform(-0.2, 0.2), rng.uniform(1.3, 1.8), None, 1000, 0.1)
for c in at('scuttle'):
    n = int(c['dur'] * 11)
    for k in range(n):
        tt = c['t'] + k / 11 + rng.uniform(-0.02, 0.02)
        env = min(1, min(k, n - k) / 3)
        if c['surface'] == 'wood': place(pick(TW), tt, -33 + 6 * env - 6 + rng.uniform(-2, 2), rng.uniform(-0.1, 0.3), rng.uniform(1.6, 2.2), 7000, 900, 0.1)
        else: place(pick(SNOW), tt, -35 + 6 * env - 6 + rng.uniform(-2, 2), rng.uniform(-0.1, 0.2), rng.uniform(1.3, 1.7), 5000, 600, 0.1)
for c in at('land_moss'):
    place(pick(SNOW), c['t'], -18, 0.1, 1.0, 4000, 100, 0.15)
    place(sp('drum_bass_soft'), c['t'], -24, 0.1, 1.2, 1500, 40, 0.1)
for c in at('notice'): place(sp('elec_plip'), c['t'], -29, 0.0, 0.8, None, 300, 0.3)

# ---------------------------------------------------------------- the meeting
B = {c['type'][5:]: c['t'] for c in cues if c['type'].startswith('beat_')}
if B:
    place(load(f'{MOOD}/things/wind-chimes.mp3'), B['wake'] - 0.1, -30, 0.3, 1.0, None, 800, 0.4, start=12.0, length=1.6, fade_in=0.2, fade_out=1.0)
    place(sp('ambi_swoosh'), B['startle'] - 0.05, -20, 0.3, 1.6, None, 300, 0.2, length=0.8, fade_out=0.3)
    place(pick(SNOW), B['startle'], -22, 0.3, 0.8, 3000, 80, 0.1)
    place(pick(SNOW), B['startle'] + 0.42, -17, 0.3, 0.75, 3000, 80, 0.15)
    place(sp('drum_bass_soft'), B['startle'] + 0.42, -22, 0.3, 1.3, 1500, 40, 0.1)
    for k in range(24): place(pick(KEYS), B['burst'] + rng.uniform(0, 0.09), -21 + rng.uniform(-4, 2), rng.uniform(-0.6, 0.2), rng.uniform(1.0, 1.6), None, 300, 0.25)
    place(sp('perc_swash'), B['burst'], -20, -0.2, 1.0, None, 300, 0.2)
    for k in range(18): place(pick(KEYS), B['burst'] + 0.25 + 0.4 * (k / 18) ** 0.6 + rng.uniform(0, 0.01), -24 + rng.uniform(-3, 2), rng.uniform(-0.4, 0.1), rng.uniform(1.0, 1.3), None, 300, 0.2)
    place(pick(KEYS), B['burst'] + 0.68, -15, -0.2, 0.8, None, 200, 0.25)
    place(snd('01', 'toggle_on'), B['wave'] + 0.1, -27, -0.3, 1.0, None, 500, 0.25)
    place(load(f'{MOOD}/nature/walk-on-leaves.mp3'), B['waveBack'], -30, 0.3, 1.5, 3000, 400, 0.1, start=3.2, length=0.6, fade_in=0.05, fade_out=0.3)
    place(load(f'{MOOD}/things/wind-chimes.mp3'), B['waveBack'] + 0.35, -29, 0.3, 1.0, None, 1500, 0.4, start=30.0, length=1.4, fade_in=0.1, fade_out=0.9)
    place(pick(SNOW), 36.95, -21, 0.2, 0.9, 3000, 80, 0.15)
    place(BUB[0], B['boop'], -14, 0.1, 0.8, 5000, 150, 0.2)
    place(pick(SNOW), B['boop'] + 0.02, -24, 0.1, 0.7, 2500, 80, 0.1)
    # the gift
    place(pick(KEYS), B['gift'], -16, -0.1, 0.9, None, 200, 0.2)
    place(sp('elec_ping'), B['gift'] + 0.05, -25, -0.1, 0.5, None, 200, 0.4)
    place(sp('ambi_glass_rub'), B['gift'] + 0.2, -29, -0.1, 1.0, None, 300, 0.4, length=1.6, fade_in=0.4, fade_out=0.8)
    place(sp('perc_swash'), 38.6, -26, 0.0, 0.8, None, 300, 0.2)
    place(pick(SNOW), B['place'], -20, 0.0, 0.8, 3000, 80, 0.15)
    place(sp('perc_bell'), B['place'] + 0.02, -27, 0.0, 1.0, None, 400, 0.45, length=2.5, fade_out=1.5)
    place(load(f'{MOOD}/nature/wind.mp3'), B['puff'] + 0.1, -17, 0.2, 1.0, 2500, 200, 0.1, start=20.0, length=1.1, fade_in=0.25, fade_out=0.6)
    place(load(f'{MOOD}/things/wind-chimes.mp3'), B['puff'] + 0.5, -27, 0.1, 1.0, None, 1500, 0.4, start=44.0, length=2.0, fade_in=0.2, fade_out=1.2)
    place(load(f'{MOOD}/things/singing-bowl.mp3'), 40.0, -25, 0.0, 1.0, None, 200, 0.3, start=10.0, length=4.5, fade_in=0.8, fade_out=2.5)

# ---------------------------------------------------------------- the tree
tv = at('tree_vox')
last = -1
for c in tv:
    if c['t'] - last < 0.016: continue
    last = c['t']
    y = c.get('y', 0)
    place(pick(KEYS), c['t'], -26 + rng.uniform(-3, 2) + min(4, y * 0.08), rng.uniform(-0.35, 0.35), 0.85 + y * 0.012 + rng.uniform(0, 0.1), None, 400, 0.25)
if tv: place(sp('ambi_glass_hum'), 41.0, -30, 0, 1.0, None, 100, 0.3, length=6.0, fade_in=2.0, fade_out=2.0)
if tv: place(sp('ambi_lunar_land'), 41.2, -32, 0, 1.0, 6000, 300, 0.4, length=5.5, fade_in=1.5, fade_out=2.0)
for c in at('blossom'):
    place(pick(BUB), c['t'] + 0.05, -24 + rng.uniform(-3, 2), rng.uniform(-0.5, 0.5), rng.uniform(0.55, 0.75), 3500, 120, 0.3)
    place(pick(SNOW), c['t'] + 0.06, -31, rng.uniform(-0.5, 0.5), 0.6, 2000, 80, 0.2)
if B:
    c = B['climax']
    place(sp('misc_cineboom'), c - 0.05, -11, 0, 1.0, None, 25, 0.25, length=6.0, fade_out=3.0)
    place(sp('ambi_dark_woosh'), c - 1.1, -18, 0, 1.0, None, 60, 0.2, length=1.4, fade_in=0.6, fade_out=0.3)
    place(load(f'{MOOD}/things/wind-chimes.mp3'), c + 0.05, -20, 0.0, 1.0, None, 600, 0.45, start=60.0, length=4.0, fade_in=0.05, fade_out=2.5)
    place(sp('ambi_glass_rub'), c, -25, 0.0, 1.0, None, 300, 0.5, length=3.0, fade_out=2.0)
    place(load(f'{MOOD}/nature/walk-on-leaves.mp3'), B['lean'], -31, 0.1, 1.0, 2500, 300, 0.1, start=8.0, length=0.8, fade_in=0.1, fade_out=0.4)
    place(sp('elec_chime'), B['happy'] + 0.1, -31, 0.1, 1.0, None, 600, 0.45)
# outro: a single key press on the laptop
place(pick(KEYS), 57.6, -26, -0.2, 0.95, None, 200, 0.3)

# ---------------------------------------------------------------- reverb (Schroeder/Freeverb style) on the send
def reverb(x, room=0.82, damp=0.35, wet=1.0):
    combs = [1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116]
    aps = [225, 556, 441, 341]
    out = np.zeros_like(x)
    for ch in range(2):
        sig = x[ch].astype(np.float64)
        acc = np.zeros_like(sig)
        for d in combs:
            d = int(d * SR / 44100) + ch * 23
            buf = np.zeros(len(sig))
            lp = 0.0
            # vectorise in blocks of d (feedback distance) for speed
            for i0 in range(0, len(sig), d):
                seg = sig[i0:i0 + d]
                prev = buf[i0 - d:i0 - d + len(seg)] if i0 >= d else np.zeros(len(seg))
                y = seg + prev * room
                buf[i0:i0 + len(seg)] = y * (1 - damp) + np.concatenate([[lp], y[:-1]]) * damp
                lp = y[-1]
            acc += buf
        y = acc / len(combs)
        for d in aps:
            d = int(d * SR / 44100)
            b = np.zeros(len(y))
            for i0 in range(0, len(y), d):
                seg = y[i0:i0 + d]
                prev = b[i0 - d:i0 - d + len(seg)] if i0 >= d else np.zeros(len(seg))
                b[i0:i0 + len(seg)] = seg + prev * 0.5
            y = np.concatenate([np.zeros(d), b])[:len(y)] - 0.5 * b
        out[ch] = y
    return (out * wet).astype(np.float32)

wet = reverb(filt(send, lp=6000, hp=150))

# ---------------------------------------------------------------- music edit
mus = load(MUSIC)
def seg(a, b): return mus[:, int(a * SR):int(b * SR)].copy()
music = np.zeros((2, N), np.float32)
A = seg(4.18, 21.50)                           # intro shimmer + two chord stabs
gA = np.ones(A.shape[1], np.float32)
kk = int((7.87 - 0.4) * SR); gA[:kk] = db(11); gA[kk:kk + int(0.4 * SR)] = np.linspace(db(11), 1, int(0.4 * SR))
A *= gA
fo = int(0.10 * SR); A[:, -fo:] *= np.linspace(1, 0, fo)
music[:, :A.shape[1]] += A
Bs = 39.30
Bseg = seg(Bs, Bs + (DUR - 17.40) + 0.32)       # second section, phrase start lands on the keyboard
fi = int(0.30 * SR); Bseg[:, :fi] *= np.linspace(0, 1, fi)
i0 = int((17.40 - (39.62 - Bs)) * SR)
n = min(Bseg.shape[1], N - i0); music[:, i0:i0 + n] += Bseg[:, :n]
# fade the ending with the picture
k0, k1 = int(57.2 * SR), N
music[:, k0:k1] *= np.linspace(1, 0, k1 - k0) ** 1.5
music *= db(-2.0)
# gentle duck of the music under the biggest hits
duck = np.ones(N, np.float32)
for t, d, amt in [(17.40, 0.35, -3), (B.get('climax', 50.4) if B else 50.4, 0.6, -2)]:
    a, b = int(t * SR), int((t + d) * SR)
    duck[a:b] = np.minimum(duck[a:b], db(amt))
duck = sosfilt(butter(1, 8, 'low', fs=SR, output='sos'), duck)
music *= duck

mix = music + sfx + beds + wet * 0.55
if os.environ.get('STEMS'):
    for name, st in [('music', music), ('sfx', sfx), ('beds', beds), ('wet', wet * 0.55)]:
        sf.write(f'{os.environ["STEMS"]}/stem_{name}.wav', st.T, SR, subtype='FLOAT')
# master: soft-knee compression on peaks, then a clean ceiling
peak = np.abs(mix).max()
mix = np.tanh(mix / 0.9) * 0.9
mix = filt(mix, hp=25)
# loudness to about -15 LUFS (approximate, via RMS after K-ish high-pass)
k = filt(mix, hp=150)
rms = np.sqrt(np.mean(k ** 2))
target = db(-17.5)
mix *= target / max(rms, 1e-6)
mx = np.abs(mix).max()
if mx > db(-1.0): mix *= db(-1.0) / mx
sf.write(sys.argv[1] if len(sys.argv) > 1 else 'mix.wav', mix.T, SR, subtype='PCM_24')
print('written', sys.argv[1] if len(sys.argv) > 1 else 'mix.wav', 'peak in', round(float(peak), 2), 'out peak', round(float(np.abs(mix).max()), 3))
