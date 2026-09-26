"""INTERFACE soundtrack: 120 BPM garage-flavoured house in F# minor under a dense UI foley track, no samples.

The groove drops when Send is pressed and rides the stream while Fable 5.1 answers. When the player starts,
the music steps back and THE FRONTIER plays through the player's little speaker: its real soundtrack,
band-passed, and scrubbed at varispeed when the cursor drags the playhead. Dark mode turns the groove dark,
the overview opens everything up, and Enter lands the last chord. Every interaction has a sound on the grid.
"""
import os
import wave

import numpy as np

from engine import audio as A
from engine.audio import hz
from engine.core import in_out_cubic
from .score import (G, DURATION, T_PICKER_IN, T_PICK, T_CARD, T_TO_COMPOSER, T_TYPE, PROMPT, T_CHIPS, T_SEND,
                    T_RESP, T_THINK, T_THINK_LINES, T_THOUGHT, T_LIST, T_CODE, T_CODE_LINES, T_COPY, T_TOOL,
                    T_PROG, T_DONE, T_TOAST, T_OPEN, T_TO_PLAYER, T_PLAY, T_GRAB, T_DROP, FILM_AT_PLAY,
                    FILM_AT_DROP, T_TO_SETTINGS, T_TOG, T_WIPE, T_SLIDE, T_TO_STATS, T_SWITCH, T_HOVER, T_OVER,
                    T_PATH, T_FLY, T_CMDK, T_KEYS, T_ENTER, END, T_LOGOS, T_CREDIT)
from . import stream as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")

S16 = G.spb / 4
SWING = 0.018            # the off sixteenths lean back: the garage shuffle
CHORDS = [["F#2", "A3", "C#4", "E4", "G#4"],     # F#m9
          ["D2", "F#3", "A3", "C#4", "E4"],      # Dmaj9
          ["A1", "C#4", "E4", "G#4", "B4"],      # Amaj9
          ["E2", "G#3", "B3", "C#4", "F#4"]]     # E6/9
SPARKLE = ["F#6", "A6", "B6", "C#7", "E7", "F#7"]


def chord(bar):
    return CHORDS[(bar - 1) % 4]


def beats(t0, t1, every=1.0, offset=0.0):
    """Times every `every` beats in [t0, t1), on the grid."""
    out, t = [], t0 + offset * G.spb
    while t < t1 - 1e-9:
        out.append(t)
        t += every * G.spb
    return out


def swing(t):
    k = round(t / S16) % 2
    return t + (SWING if k == 1 else 0.0)


GROOVE = [(G.at(3), T_PLAY), (G.at(8), T_OVER + 3.0)]     # where the full kit plays
PLAYING = (T_PLAY, T_TO_SETTINGS + 0.3)


def in_groove(t):
    return any(a <= t < b for a, b in GROOVE)


def load_film_audio():
    p = os.path.join(OUT, "frontier.wav")
    if not os.path.exists(p):
        return None
    with wave.open(p, "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
        return x.reshape(-1, w.getnchannels())


def film_through_player():
    """THE FRONTIER as the player plays it: real time, then a varispeed scrub, then real time again."""
    src = load_film_audio()
    if src is None:
        return None
    t0, t1 = PLAYING
    n = A.n_of(t1 - t0)
    t = t0 + np.arange(n) / A.SR
    pos = np.where(t < T_GRAB, FILM_AT_PLAY + (t - T_PLAY), 0.0)
    u = np.clip((t - T_GRAB) / (T_DROP - T_GRAB), 0, 1)
    e = np.where(u < 0.5, 4 * u ** 3, 1 - (-2 * u + 2) ** 3 / 2)
    p0 = FILM_AT_PLAY + (T_GRAB - T_PLAY)
    pos = np.where((t >= T_GRAB) & (t < T_DROP), p0 + (FILM_AT_DROP - p0) * e, pos)
    pos = np.where(t >= T_DROP, FILM_AT_DROP + (t - T_DROP), pos)
    idx = pos * A.SR
    i0 = np.clip(idx.astype(int), 0, len(src) - 2)
    fr = (idx - i0)[:, None]
    out = src[i0] * (1 - fr) + src[i0 + 1] * fr
    # a laptop-sized speaker, and a fade as the camera leaves
    out = A.filt(A.filt(out, "highpass", 170), "lowpass", 7500)
    env = np.clip((t - T_PLAY) / 0.02, 0, 1) * np.clip((t1 - t) / 0.45, 0, 1)
    scrub = (t >= T_GRAB) & (t < T_DROP)
    env = env * np.where(scrub, 0.55, 1.0)
    return out * env[:, None]


def marker_times():
    """When the overview's click path reaches each numbered click (same maths as the picture)."""
    from .film import path_points
    pts = path_points()
    lens = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        lens.append(lens[-1] + float(np.hypot(x1 - x0, y1 - y0)))
    out = []
    for L in lens:
        r = L / max(lens[-1], 1.0)
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if in_out_cubic(mid) < r:
                lo = mid
            else:
                hi = mid
        out.append(T_PATH[0] + (T_PATH[1] - T_PATH[0]) * lo)
    return out


def build():
    mix = A.Mix(DURATION, tail=1.2)
    put = mix.put
    rng = np.random.default_rng(5)

    # ------------------------------------------------------------ drums
    kick = A.kick(f_hi=210, f_lo=50, p_decay=0.034, a_decay=0.24, hold=0.02, drive=1.9, click=0.5, length=0.42)
    kick_dark = A.kick(f_hi=260, f_lo=46, p_decay=0.04, a_decay=0.3, hold=0.03, drive=2.8, click=0.6, length=0.5)
    kicks = []
    for bar_t in beats(G.at(2), G.at(3), 2.0):                 # bar 2: a heartbeat under the typing
        put("kick", kick, bar_t, 0.5)
        kicks.append(bar_t)
    for t in beats(0.0, DURATION, 1.0):
        if in_groove(t):
            put("kick", kick_dark if t >= T_WIPE else kick, t, 0.92)
            kicks.append(t)
    for t in [T_ENTER]:
        put("kick", kick_dark, t, 1.0)
        kicks.append(t)
    for t in beats(0.0, DURATION, 2.0, 1.0):
        if in_groove(t):
            put("clap", A.clap(0.36, 1350, tail=0.1, seed=int(t * 10)), t, 0.5)
            put("clap", A.rim(), t, 0.3, p=0.15)
    for t in beats(0.0, DURATION, 0.25):
        if not in_groove(t):
            continue
        k = round(t / S16) % 4
        vel = (0.12, 0.06, 0.2, 0.07)[k]
        put("hats", A.hat(0.022 if k != 2 else 0.04, seed=int(t * 100) % 89), swing(t), vel, p=(-0.3, 0.3)[k % 2])
    for t in beats(0.0, DURATION, 1.0, 0.5):
        if in_groove(t):
            put("hats", A.hat(0.16, seed=11), t, 0.12, p=-0.2)
    # the click beat: an eleven-over-thirty-two euclid of tiny digital ticks
    pat = [((i * 11) % 32) < 11 for i in range(32)]
    for bar in range(3, 12):
        for s, on in enumerate(pat):
            t = G.at(bar) + s * S16 / 2
            if on and in_groove(t):
                put("clicks", A.click((9500, 7000, 12000, 8000)[s % 4], 0.008, 0.0009, 0.1), t, 0.16,
                    p=(-0.6, 0.6)[s % 2])
    # garage skip: ghost kicks
    for bar in range(3, 11):
        t = G.at(bar, 2, 3)
        if in_groove(t):
            put("kick", kick, t, 0.32)

    # ------------------------------------------------------------ intro keys (filtered, opening)
    for bar in (1, 2):
        notes = chord(bar)
        for b in (0, 1.5, 3):
            for nt in notes[1:]:
                put("intro", A.epiano(hz(nt), 1.3, vel=0.6, decay=0.9), G.at(bar) + b * G.spb, 0.12,
                    p=float(rng.uniform(-0.3, 0.3)))
        put("intro", A.sine(hz(notes[0]), A.n_of(1.9)) * A.adsr(A.n_of(1.9), 0.01, 0.3, 0.8, 0.2, 1.7), G.at(bar), 0.35)
    put("fx", A.riser(1.15, lo=400, hi=9000, f0=180, f1=900), G.at(3) - 1.15, 0.34)

    # ------------------------------------------------------------ groove A: while Fable answers
    garage = [0, 3, 6, 8, 11, 14]
    for bar in range(3, 7):
        root = hz(chord(bar)[0])
        for s in garage:
            t = G.at(bar, 1, s)
            if t >= T_PLAY:
                break
            n = root * (2 if s in (6, 14) else 1)
            put("bass", A.pluck(n, 0.2, bright=1200, decay=0.06, amp_decay=0.12, q=1.4), t, 0.5)
            put("bass", A.sine(root, A.n_of(0.18)) * A.env_exp(A.n_of(0.18), 0.12), t, 0.55)
        for s in (2, 7, 10):
            t = G.at(bar, 1, s)
            if t >= T_PLAY:
                break
            put("stab", A.supersaw([hz(x) for x in chord(bar)[1:]], 0.22, cutoff=3200, cut_env=1.2, cut_decay=0.06,
                                   release=0.08, voices=5), swing(t), 0.26)
        put("keys", A.pad([hz(x) for x in chord(bar)[1:]], 2.1, attack=0.08, release=0.5, cutoff=1600, voices=4),
            G.at(bar), 0.2)

    # ------------------------------------------------------------ the player: music steps back, a soft bed
    put("keys", A.pad([hz(x) for x in chord(6)[1:]], 2.6, attack=0.3, release=0.8, cutoff=900, voices=4), T_PLAY, 0.22)
    film = film_through_player()
    if film is not None:
        put("film", film, PLAYING[0], 1.5)
    # build back in: snare roll + riser into the dark
    roll = [G.at(7, 3) + k * S16 * 2 for k in range(4)] + [G.at(7, 4) + k * S16 for k in range(4)]
    for k, t in enumerate(roll):
        put("snare", A.snare(210, 0.18, seed=60 + k), t, 0.16 + 0.05 * k)
    put("fx", A.riser(T_WIPE - T_TO_SETTINGS, lo=300, hi=10000, f0=120, f1=900), T_TO_SETTINGS, 0.4)
    put("fx", A.reverse(A.crash(0.9, seed=21)), T_WIPE - 0.9, 0.3)

    # ------------------------------------------------------------ dark mode: reese and a lower sky
    for bar in (8, 9):
        root = hz(chord(bar)[0])
        for s, d in ((0, 0.34), (6, 0.2), (10, 0.34)):
            put("bass", A.reese(root, d, cutoff=780, sub=0.8, drive=2.2), G.at(bar, 1, s), 0.55)
        put("keys", A.pad([hz(x) / 2 for x in chord(bar)[1:]] + [hz(chord(bar)[2])], 2.1, attack=0.02, release=0.4,
                          cutoff=1100, voices=5, seed=bar), G.at(bar), 0.3)
        for s in (2, 10):
            put("stab", A.supersaw([hz(x) / 2 for x in chord(bar)[1:]], 0.18, cutoff=2400, cut_env=1.4,
                                   cut_decay=0.05, release=0.06, voices=5), G.at(bar, 1, s), 0.3)
    put("fx", A.riser(1.2, lo=500, hi=12000, f0=200, f1=1200), T_OVER - 1.2, 0.36)
    put("fx", A.reverse(A.crash(1.0, seed=22)), T_OVER - 1.0, 0.34)

    # ------------------------------------------------------------ overview: everything opens up
    for bar in (10, 11):
        t0 = G.at(bar)
        if t0 >= T_FLY + 0.1:
            break
        notes = [hz(x) for x in chord(bar)[1:]]
        put("stab", A.supersaw(notes, 1.9 if bar == 10 else 1.0, cutoff=5200, cut_env=0.8, cut_decay=0.3,
                               release=0.4, voices=7), t0, 0.34)
        put("stab", A.supersaw([f * 2 for f in notes[:3]], 1.6, cutoff=7000, release=0.5, voices=5, seed=3), t0, 0.14)
        root = hz(chord(bar)[0])
        for b in range(4):
            for s in (1, 2, 3):
                t = G.at(bar, b + 1, s)
                if t >= T_FLY:
                    break
                n = root * (2 if s == 3 else 1)
                put("bass", A.pluck(n, 0.12, bright=1500, decay=0.05, amp_decay=0.07, q=1.5), t, 0.5)
                put("bass", A.sine(root, A.n_of(0.1)) * A.env_exp(A.n_of(0.1), 0.05), t, 0.42)
    arp_notes = ["F#5", "A5", "C#6", "E6", "G#6", "E6", "C#6", "A5"]
    for i, t in enumerate(beats(T_OVER, T_FLY, 0.25)):
        put("arp", A.pluck(hz(arp_notes[i % 8]), 0.22, bright=6500, decay=0.05, amp_decay=0.12, wave="square"),
            t, 0.18, p=0.4 * np.sin(i * 0.8))

    # ------------------------------------------------------------ break, Enter, the last chord
    put("fx", A.riser(T_ENTER - T_FLY, lo=300, hi=9000, f0=150, f1=1100), T_FLY, 0.3)
    put("keys", A.pad([hz(x) for x in chord(11)[1:]], T_ENTER - T_FLY + 0.2, attack=0.2, release=0.1, cutoff=1400,
                      voices=4), T_FLY, 0.3)
    roll = [T_FLY + 0.1 + k * S16 * 2 for k in range(4)] + [G.at(11, 3) + k * S16 for k in range(8)]
    for k, t in enumerate(sorted(set(roll))):
        if t < T_ENTER - 0.02:
            put("snare", A.snare(220, 0.16, seed=90 + k), t, 0.1 + 0.035 * k)
    last = [hz(x) for x in chord(1)]
    put("keys", A.pad(last[1:] + [last[1] * 2], 3.2, attack=0.02, release=1.6, cutoff=2600, voices=6), T_ENTER, 0.42)
    for k, f in enumerate(last):
        put("piano", A.piano(f * (2 if k else 1), 3.0, vel=0.85), T_ENTER + 0.012 * k, 0.26, p=-0.3 + 0.15 * k)
    put("bass", A.sine(last[0] / 2, A.n_of(2.6)) * A.adsr(A.n_of(2.6), 0.005, 0.4, 0.7, 1.0, 1.4), T_ENTER, 0.6)

    # ------------------------------------------------------------ impacts
    put("fx", A.impact(1.6, seed=31), G.at(3), 0.3)
    put("fx", A.crash(1.8, seed=32), G.at(3), 0.22)
    put("fx", A.impact(2.4, seed=33), T_WIPE, 0.55)
    put("fx", A.sub_drop(1.2, 70, 30), T_WIPE, 0.55)
    put("fx", A.braam(hz("F#1"), 2.6, seed=34), T_OVER, 0.55)
    put("fx", A.crash(2.4, seed=35), T_OVER, 0.4)
    put("fx", A.sub_drop(1.6, 72, 28), T_OVER, 0.55)
    put("fx", A.impact(2.6, seed=36), T_ENTER, 0.5)
    put("fx", A.crash(2.6, seed=37), T_ENTER, 0.36)

    # ------------------------------------------------------------ foley: every event on screen
    sfx = lambda sig, t, g, p=0.0: put("sfx", sig, t, g, p)   # noqa: E731
    sfx(A.whoosh(0.4, True, 1, 500, 7000, -0.2, 0.2), T_PICKER_IN, 0.14)
    for k, tc in enumerate(T_PICK):
        sfx(A.click(2600, 0.018, 0.0025, 0.5), tc, 0.5)
        sfx(A.blip(180, 0.03), tc, 0.22)
        sfx(A.swish(0.3, seed=2 + k), tc + 0.02, 0.16, 0.3)
    sfx(A.blip(880, 0.07), T_CARD, 0.18)
    sfx(A.blip(1320, 0.07), T_CARD + 0.06, 0.14)
    for k, t in enumerate([T_TO_COMPOSER, T_TO_PLAYER, T_TO_SETTINGS, T_TO_STATS, T_FLY]):
        sfx(A.whoosh(0.42, k % 2 == 0, 10 + k, 300, 6500, (-0.7, 0.7)[k % 2], (0.7, -0.7)[k % 2]), t - 0.06, 0.34)
    n = len(PROMPT[0]) + len(PROMPT[1])
    for k in range(n):
        t = T_TYPE[0] + k * (T_TYPE[1] - T_TYPE[0]) / n
        sfx(A.key(seed=900 + k), t, 0.2, float(rng.uniform(-0.3, 0.3)))
    for k, t in enumerate(T_CHIPS):
        sfx(A.blip(1320 * 2 ** (k * 3 / 12), 0.06), t, 0.18)
    sfx(A.click(2200, 0.02, 0.003, 0.5), T_SEND, 0.55)
    sfx(A.whoosh(0.5, True, 40, 400, 8000, 0.0, 0.0), T_SEND + 0.02, 0.26)
    sfx(A.blip(660, 0.08), T_RESP, 0.16)
    # thinking: a sparkle of small bells while the spark turns
    t = T_THINK[0]
    k = 0
    while t < T_THOUGHT:
        f = hz(SPARKLE[int(rng.integers(len(SPARKLE)))])
        sfx(A.bell(f, 0.5, ratio=2.0, index=0.5, decay=0.25), t, 0.05 + 0.03 * rng.random(), float(rng.uniform(-0.7, 0.7)))
        t += 0.07 + 0.06 * rng.random()
        k += 1
    for k, tl in enumerate(T_THINK_LINES):
        sfx(A.data_burst(0.26, 60, 50 + k, 3000, 9000), tl, 0.08)
    sfx(A.click(1400, 0.02, 0.004, 0.3), T_THOUGHT, 0.3)
    sfx(A.blip(520, 0.06), T_THOUGHT + 0.02, 0.14)
    # the stream: one soft tick per burst of tokens
    for k, t in enumerate(S.CHUNK_T):
        sfx(A.click(3000 + 2500 * rng.random(), 0.01, 0.0012, 0.15, seed=300 + k), t, 0.16, float(rng.uniform(-0.4, 0.4)))
    for k, t in enumerate(T_LIST):
        sfx(A.blip(990 * 2 ** (k * 4 / 12), 0.06), t, 0.16)
        sfx(A.click(4000, 0.01, 0.001), t, 0.2)
    sfx(A.swish(0.3, seed=41), T_CODE, 0.2)
    for k, t in enumerate(T_CODE_LINES):
        sfx(A.data_burst(0.18, 120, 60 + k, 1800, 6000, decay_out=False), t, 0.14)
    sfx(A.click(2800, 0.015, 0.002, 0.4), T_COPY, 0.45)
    sfx(A.blip(1760, 0.05), T_COPY + 0.03, 0.12)
    sfx(A.blip(740, 0.07), T_TOOL, 0.16)
    sfx(A.data_burst(T_PROG[1] - T_PROG[0], 55, 70, 1500, 7000, decay_out=False), T_PROG[0], 0.12)
    for k in range(len(S.THUMB_TIMES)):
        tk = T_PROG[0] + (T_PROG[1] - T_PROG[0]) * (k + 0.6) / len(S.THUMB_TIMES)
        sfx(A.blip(880 * 2 ** (k * 2 / 12), 0.05), tk, 0.14, -0.5 + k / 6)
    for f, dt in ((hz("C#6"), 0.0), (hz("F#6"), 0.08), (hz("A6"), 0.16)):
        sfx(A.bell(f, 1.2, ratio=2.0, index=0.6, decay=0.5), T_DONE + dt, 0.16)
    sfx(A.whoosh(0.35, False, 80, 400, 6000, 0.0, 0.0), T_TOAST[0], 0.18)
    sfx(A.ding(hz("E7"), 0.9), T_TOAST[0] + 0.12, 0.08)
    sfx(A.whoosh(0.3, True, 81, 400, 6000, 0.0, 0.0), T_TOAST[1], 0.12)
    for t in (T_OPEN, T_PLAY):
        sfx(A.click(2400, 0.02, 0.003, 0.5), t, 0.5)
        sfx(A.blip(200, 0.03), t, 0.2)
    sfx(A.click(3000, 0.015, 0.002, 0.4), T_GRAB, 0.4)
    sfx(A.swish(T_DROP - T_GRAB, seed=82), T_GRAB, 0.22)
    sfx(A.click(2000, 0.015, 0.002, 0.4), T_DROP, 0.4)
    for k, t in enumerate(T_TOG):
        sfx(A.flap(seed=83 + k, lock=True), t + 0.02, 0.5)
        sfx(A.click(2600, 0.018, 0.0025, 0.5), t, 0.4)
    for k in range(14):
        sfx(A.click(3200 + 180 * k, 0.008, 0.0009), T_SLIDE[0] + k * (T_SLIDE[1] - T_SLIDE[0]) / 14, 0.18, -0.6 + 0.09 * k)
    sfx(A.blip(1480, 0.08), T_SLIDE[1], 0.14)
    for k, t in enumerate(T_SWITCH):
        sfx(A.click(2600, 0.018, 0.0025, 0.5), t, 0.45)
        sfx(A.data_burst(0.5, 90, 84 + k), t + 0.05, 0.18)
    sfx(A.blip(1760, 0.08), T_HOVER[0], 0.14)
    sfx(A.whoosh(0.9, False, 90, 200, 7000, 0.0, 0.0), T_OVER - 0.05, 0.4)
    sfx(A.draw_tone(T_PATH[1] - T_PATH[0], 400, 2400), T_PATH[0], 0.16)
    for k, t in enumerate(marker_times()):
        sfx(A.blip(740 * 2 ** ((k % 6) * 2 / 12), 0.05), t, 0.16, -0.6 + 1.2 * k / 11)
    sfx(A.data_burst(0.8, 70, 91), T_OVER + 0.45, 0.14)
    sfx(A.key(seed=990), T_CMDK, 0.4)
    sfx(A.blip(1100, 0.06), T_CMDK + 0.02, 0.18)
    for k, t in enumerate(T_KEYS):
        sfx(A.key(seed=950 + k), t, 0.4)
    sfx(A.click(2000, 0.03, 0.004, 0.4), T_ENTER, 0.55)
    sfx(A.whoosh(0.4, False, 92, 300, 5000, 0.0, 0.0), END[0], 0.22)
    sfx(A.ding(hz("C#7"), 1.2), END[0] + 0.25, 0.1)
    for f, t in zip((hz("F#5"), hz("A5"), hz("C#6")), T_LOGOS):
        sfx(A.bell(f, 1.6, ratio=2.0, index=0.6, decay=0.6), t, 0.18)
    sfx(A.blip(2200, 0.05), T_CREDIT, 0.08)
    return mix, sorted(kicks)


def process(mix, kicks):
    b = mix.buses
    n = mix.n
    side = A.duck(n, kicks, depth=0.5, release=0.16)[:, None]
    z = np.zeros((n, 2))
    g = lambda k: b.get(k, z)   # noqa: E731
    out = g("kick") * 0.85 + g("clap") + A.reverb(g("clap"), t60=1.1, seed=2) * 0.25
    out += g("hats") * 0.8 + A.filt(g("clicks"), "highpass", 3000) * 1.1
    intro = g("intro")
    k = np.clip(np.arange(n) / A.SR / G.at(3), 0, 1)
    intro = A.vfilt(intro, "lowpass", 600 * (12000 / 600) ** k, 0.8)
    out += (intro + A.reverb(intro, t60=2.0, seed=4) * 0.4) * 1.2
    keys = g("keys") + A.reverb(g("keys"), t60=2.2, seed=6) * 0.4
    out += keys * side * 1.1
    out += g("bass") * side
    out += g("stab") * side * 1.1 + A.delay(g("stab"), G.spb * 0.75, 0.35) * 0.18
    out += g("arp") + A.delay(g("arp"), G.spb * 0.75, 0.4) * 0.35
    out += g("snare") + A.reverb(g("snare"), t60=1.0, seed=7) * 0.3
    out += g("piano") + A.reverb(g("piano"), t60=2.6, seed=8) * 0.5
    out += g("fx")
    # the music steps back while the player plays the film
    t = np.arange(n) / A.SR
    step_back = 1 - 0.72 * np.clip((t - T_PLAY) / 0.08, 0, 1) * np.clip((PLAYING[1] - 0.2 - t) / 0.3, 0, 1)
    out *= step_back[:, None]
    out += g("film") * 1.0
    sfx = A.filt(g("sfx"), "highpass", 60)
    out += sfx * 1.3 + A.reverb(sfx, t60=0.9, seed=9) * 0.18
    return A.master(out, target=-11.5, ceiling=-1.0)


def render(path):
    mix, kicks = build()
    x = process(mix, kicks)[:A.n_of(DURATION)]
    A.write_wav(path, x)
    return x
