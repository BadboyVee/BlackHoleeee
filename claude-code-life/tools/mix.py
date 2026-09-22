#!/usr/bin/env python3
"""Build the 30-second soundtrack for "A Day in the Life of Claude Code".

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
LENGTH = 30.0
SOUNDS = os.environ.get("SOUNDS", "/usr/lib/libreoffice/share/gallery/sounds")
OUT = sys.argv[1] if len(sys.argv) > 1 else "soundtrack.wav"

WALK_HZ = 2.6          # leg cycles per second; one footfall every half cycle
WALKS = [(7.5, 12.0), (22.6, 26.4)]
TYPING = [(13.3, 15.0, 7.0), (15.0, 16.0, 10.0), (16.0, 18.35, 13.0)]   # start, end, keys/s


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
    "sparcle", "roll", "nature1", "nature2", "kling", "pluck", "train", "strom",
    "wallewal", "kongas", "gong", "romans", "applause", "falling", "untie",
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

# night → sunrise
place("sparcle", 0.25, 0.28, pan=-0.3)
place("roll", 3.0, 0.26, fade_in=0.4, fade_out=0.8)
place("nature1", 3.9, 0.5, pan=0.4, fade_out=0.4)
place("kling", 5.0 - 0.81, 0.5, fade_out=0.3)                  # the bell strike lands at 5.0 s
place("nature2", 6.4, 0.35, pan=0.5)
place("pluck", 5.95, 0.38, rate=1.6)                             # hop off the bed

# commute: pitter-patter feet made from one conga hit
for a, b in WALKS:
    k = 0
    step = 1 / (2 * WALK_HZ)
    while a + k * step < b:
        place("kongas", a + k * step, 0.26 + 0.04 * (k % 2), rate=1.25 + 0.1 * (k % 2),
              start=0.15, dur=0.09, fade_out=0.03, pan=-0.15 if k % 2 else 0.15)
        k += 1
place("train", 8.5, 0.3, fade_in=0.6, fade_out=0.8, pan=0.6)

# work
place("pluck", 12.05, 0.38, rate=1.8)                            # hop onto the chair
place("strom", 12.55, 0.16, dur=1.2, fade_out=0.4)               # computer powers on
for a, b, rate in TYPING:
    t = a
    while t < b:
        place("kongas", t, 0.34 + 0.12 * rng.random(), rate=2.1 + 0.5 * rng.random(),
              start=0.15, dur=0.05, fade_out=0.02, pan=rng.uniform(-0.25, 0.25), highpass=True)
        t += (1 / rate) * rng.uniform(0.55, 1.45)
place("wallewal", 16.0, 0.22, dur=2.6, fade_in=0.3, fade_out=0.4)   # GO BRAZY frenzy
for k in range(3):                                               # dance beat
    place("kongas", 16.0 + k * 2.486, 0.5 if k else 0.4, fade_out=0.3 if k == 2 else 0.02)

# ship it
place("gong", 18.45, 0.28, dur=3.5, fade_out=1.5)
place("pluck", 18.85, 0.38, rate=1.6)                            # hop down
place("romans", 18.9, 0.42)
place("applause", 19.8, 0.22, fade_in=0.3, fade_out=1.2, pan=-0.2)

# evening
place("falling", 22.2, 0.26, fade_out=0.8)
place("sparcle", 25.6, 0.26, pan=0.3)
place("pluck", 26.55, 0.34, rate=1.5)                            # hop into bed
place("untie", 27.1, 0.42, dur=2.8, fade_out=0.6)                # lullaby

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
