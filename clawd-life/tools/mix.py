#!/usr/bin/env python3
"""Build the 64-second soundtrack for "A Day in the Life of Clawd".

Everything here is a recorded sample from the LibreOffice sound gallery
(/usr/lib/libreoffice/share/gallery/sounds). Nothing is synthesized: the
footsteps and keyboard clicks are single conga hits cut out of kongas.wav and
re-pitched.

Writes soundtrack.wav (44.1 kHz stereo). tools/build-audio.sh turns it into the
MP3/AAC versions used by the page and the video.

The timings mirror the animation in index.html (WALK_HZ, the walk windows,
the hop times), so keep the two in sync.
"""
import os
import sys
import wave

import numpy as np

SR = 44100
LENGTH = 64.0
SOUNDS = os.environ.get("SOUNDS", "/usr/lib/libreoffice/share/gallery/sounds")
OUT = sys.argv[1] if len(sys.argv) > 1 else "soundtrack.wav"

WALK_HZ = 2.6          # leg cycles per second; one footfall every half cycle
WALKS = [(8.8, 12.8), (19.8, 23.8), (32.6, 36.6), (44.3, 47.8), (55.0, 58.6)]
TYPING = [(24.9, 26.8, 7.0), (26.8, 27.8, 10.0), (27.8, 30.7, 13.0)]   # start, end, keys/s


def load(name):
    w = wave.open(os.path.join(SOUNDS, name + ".wav"))
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if w.getnchannels() == 2:
        x = x.reshape(-1, 2).mean(axis=1)
    x = x - x.mean()
    peak = np.abs(x).max() or 1
    return x / peak, sr


def resample(x, sr, rate=1.0):
    """Resample to SR, playing `rate` times faster (and higher)."""
    n_out = int(len(x) * SR / sr / rate)
    src = np.linspace(0, len(x) - 1, n_out)
    return np.interp(src, np.arange(len(x)), x).astype(np.float32)


CACHE = {n: load(n) for n in [
    "sparcle", "roll", "nature1", "nature2", "kling", "pluck", "train", "strom", "glasses", "soft",
    "wallewal", "kongas", "gong", "romans", "applause", "falling", "untie", "theetone",
]}

mix = np.zeros((int(SR * LENGTH), 2), dtype=np.float32)


def place(name, t, gain=1.0, rate=1.0, start=0.0, dur=None, fade_in=0.0, fade_out=0.05, pan=0.0, highpass=False):
    x, sr = CACHE[name]
    x = x[int(start * sr):]
    if dur is not None:
        x = x[:int(dur * sr)]
    y = resample(x, sr, rate)
    if highpass:
        y = np.append(y[0], np.diff(y)) * 3.0
    n = len(y)
    env = np.ones(n, dtype=np.float32)
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi:
        env[:fi] = np.linspace(0, 1, fi)
    fo = min(fo, n)
    if fo:
        env[-fo:] *= np.linspace(1, 0, fo)
    y = y * env * gain
    i0 = int(t * SR)
    i1 = min(i0 + n, len(mix))
    if i1 <= i0:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i0:i1, 0] += y[:i1 - i0] * l * 1.41
    mix[i0:i1, 1] += y[:i1 - i0] * r * 1.41


rng = np.random.default_rng(7)


def hop(t, rate=1.6, gain=0.36):
    place("pluck", t, gain, rate=rate)


# night → sunrise → wake up
place("sparcle", 0.25, 0.28, pan=-0.3)
place("sparcle", 2.7, 0.2, pan=0.35)
place("roll", 4.3, 0.26, fade_in=0.4, fade_out=0.8)
place("nature1", 5.0, 0.5, pan=0.4, fade_out=0.4)
place("kling", 6.5 - 0.81, 0.5, fade_out=0.3)                  # the alarm's bell strike lands at 6.5 s
hop(7.45)
place("nature2", 8.2, 0.35, pan=0.5)

# every walk: pitter-patter feet made from one conga hit
for a, b in WALKS:
    k = 0
    step = 1 / (2 * WALK_HZ)
    while a + k * step < b:
        place("kongas", a + k * step, 0.26 + 0.04 * (k % 2), rate=1.25 + 0.1 * (k % 2),
              start=0.15, dur=0.09, fade_out=0.03, pan=-0.15 if k % 2 else 0.15)
        k += 1

# gym: barbell clanks (a wine-glass clink played slow), "+1" dings, treadmill, flex
REPS, REP = 13.45, 0.68
for r in range(4):
    top = REPS + r * REP + REP * 0.45
    place("kling", top - 0.81, 0.18, rate=1.6, dur=1.3, fade_out=0.4)
    place("glasses", REPS + (r + 1) * REP - 0.05, 0.22, rate=0.45, dur=0.8, fade_out=0.3)
place("glasses", 16.2, 0.42, rate=0.4, dur=1.0, fade_out=0.5)   # barbell down
hop(16.35)
t = 16.6
while t < 18.55:                                                 # running on the treadmill
    place("kongas", t, 0.2, rate=1.5, start=0.15, dur=0.07, fade_out=0.03)
    t += 1 / 5.2
hop(18.6)
place("gong", 18.85, 0.2, dur=1.6, fade_out=0.9)
place("sparcle", 19.0, 0.26)
place("train", 20.2, 0.3, fade_in=0.6, fade_out=0.8, pan=0.6)

# Claude Code HQ
hop(23.85, 1.8)
place("strom", 24.3, 0.16, dur=1.2, fade_out=0.4)               # computer powers on
for a, b, rate in TYPING:
    t = a
    while t < b:
        place("kongas", t, 0.34 + 0.12 * rng.random(), rate=2.1 + 0.5 * rng.random(),
              start=0.15, dur=0.05, fade_out=0.02, pan=rng.uniform(-0.25, 0.25), highpass=True)
        t += (1 / rate) * rng.uniform(0.55, 1.45)
place("wallewal", 27.8, 0.22, dur=2.9, fade_in=0.3, fade_out=0.4)   # GO BRAZY frenzy
place("gong", 30.8, 0.28, dur=2.5, fade_out=1.2)                  # shipped
place("sparcle", 30.9, 0.3)
hop(31.95)

# Anthropic HQ
place("soft", 35.9, 0.3, dur=1.4, fade_out=0.5)                  # sliding doors
place("untie", 36.8, 0.3, dur=1.6, fade_out=0.5)                 # "WELCOME, CLAWD!"
hop(38.05, 1.9)
place("romans", 38.55, 0.45)                                     # employee of the month
place("applause", 39.0, 0.24, fade_in=0.2, fade_out=1.2, pan=-0.2)
for k in range(2):                                               # dance beat, six hops a bar
    place("kongas", 39.4 + k * 2.486, 0.5, fade_out=0.3 if k else 0.02)
hop(43.55)

# the park with ChatGPT
place("nature2", 46.2, 0.3, pan=-0.4)
place("kongas", 48.35, 0.5, rate=0.9, start=0.15, dur=0.12, fade_out=0.05)   # high five
place("sparcle", 48.4, 0.3)
hop(48.55, 1.7)
for k in range(4):                                               # seesaw bumps
    place("pluck", 48.9 + 0.3125 + k * 0.625 * 1.0, 0.3, rate=1.3 if k % 2 else 1.7)
hop(52.75, 1.5)
place("theetone", 53.2, 0.22, fade_in=0.4, fade_out=0.9)         # sunset
place("falling", 54.0, 0.2, fade_out=0.8)

# evening
place("sparcle", 57.0, 0.26, pan=0.3)
hop(58.65, 1.5)
place("untie", 59.3, 0.42, dur=4.3, fade_out=0.8)                # lullaby

peak = np.abs(mix).max()
mix *= 0.89 / peak
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
w = wave.open(OUT, "wb")
w.setnchannels(2)
w.setsampwidth(2)
w.setframerate(SR)
w.writeframes(pcm.tobytes())
w.close()
print(f"wrote {OUT}: {LENGTH:.1f}s, pre-normalize peak {peak:.2f}")
