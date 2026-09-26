"""ARNAUD'S soundtrack: a warm 120 BPM jazz-pop groove in F, New Orleans by way of a phone, no samples.

Celesta lights the chandelier bulb by bulb, a brass chord lands the name, then Rhodes, brushes and a walking
bass carry the app. Every event on screen has its sound: keys, the send, the word punches, drops into the
bowl, cards flying past, the dining room swelling open, messages, the tap, the route, the last chord.
"""
import numpy as np

from engine import audio as A
from engine.audio import hz
from .score import (G, DURATION, T_BULBS, T_MORPH, T_NAME, T_SWEEP, T_WIPE, T_TYPE, PROMPT, T_SEND, T_GIANT, WORDS,
                    T_FIND, T_DROPS, T_RISE, T_LIME, T_CARDS, T_PICK, T_FULL, T_TO_CHAT, T_CHAT, T_MSG, T_TAP, T_MAP,
                    T_ROUTE, T_GO, T_CRAVE, T_ROLL, T_WAIT, T_END)

S16 = G.spb / 4
SWING = 0.022
# one chord per bar (bar 1 is the intro); voicings for Rhodes, a root for the bass
CHORDS = {
    1: ("F2", ["A3", "C4", "E4", "G4"]), 2: ("F2", ["A3", "C4", "E4", "G4"]),
    3: ("G2", ["Bb3", "D4", "F4", "A4"]), 4: ("C2", ["Bb3", "E4", "A4", "D5"]),
    5: ("F2", ["A3", "C4", "E4", "G4"]), 6: ("D2", ["C4", "F#4", "A4", "D5"]),
    7: ("G2", ["Bb3", "D4", "F4", "A4"]), 8: ("C2", ["Bb3", "E4", "A4", "D5"]),
    9: ("F2", ["A3", "C4", "E4", "G4"]), 10: ("D2", ["C4", "F4", "A4", "E5"]),
    11: ("Bb1", ["A3", "D4", "F4", "C5"]), 12: ("F2", ["A3", "C4", "E4", "G4"]), 13: ("F2", ["A3", "C4", "E4", "G4"]),
}
CELESTA = ["C6", "F6", "A6", "C7", "E7", "G6", "A6", "C7", "F7", "E7"]


def bar_of(t):
    return int(t // G.bar_len) + 1


def beats(t0, t1, every=1.0, offset=0.0):
    out, t = [], t0 + offset * G.spb
    while t < t1 - 1e-9:
        out.append(t)
        t += every * G.spb
    return out


def swing(t):
    return t + (SWING if round(t / S16) % 2 == 1 else 0.0)


def brass(notes, length, cutoff=2400.0, attack=0.04):
    return A.supersaw([hz(n) for n in notes], length, voices=3, detune=0.08, attack=attack, decay=0.25, sustain=0.75,
                      release=0.25, cutoff=cutoff, cut_env=1.4, cut_decay=0.18, width=0.5, q=0.9)


GROOVE = [(4.0, 8.0), (8.0, 10.0), (10.2, 11.25), (12.4, 16.0), (16.0, 20.0)]
LIGHT = [(20.0, 22.0)]


def in_groove(t):
    return any(a <= t < b for a, b in GROOVE)


def build():
    mix = A.Mix(DURATION, tail=1.5)
    put = mix.put
    rng = np.random.default_rng(9)

    # ------------------------------------------------------------ intro: the chandelier lights, the name lands
    put("pad", A.pad([hz(n) for n in ["F3", "A3", "C4", "E4", "G4"]], 4.2, attack=1.2, release=1.0, cutoff=1500,
                     voices=5), 0.0, 0.32)
    for k, t in enumerate(T_BULBS):
        n = CELESTA[k % len(CELESTA)]
        put("cel", A.bell(hz(n), 1.4, ratio=4.0, index=1.2, decay=0.6, bright=0.3), t, 0.2, p=-0.6 + 0.12 * k)
        put("cel", A.bell(hz(n) * 2, 0.6, ratio=2.0, index=0.5, decay=0.25), t + 0.01, 0.05, p=0.6 - 0.12 * k)
    # the crystals fly: a glassy glissando up
    for k in range(16):
        t = T_MORPH[0] + k * 0.04
        f = hz("C6") * 2 ** (k * 2 / 12)
        put("cel", A.bell(f, 0.5, ratio=3.0, index=0.8, decay=0.2), t, 0.06, p=float(np.sin(k)) * 0.6)
    put("fx", A.reverse(A.crash(1.4, seed=3)), T_NAME - 1.4, 0.18)
    last = ["A3", "C4", "E4", "G4"]
    put("brass", brass(["F3", "A3", "C4", "E4"], 1.8), T_NAME, 0.4)
    put("piano", sum(A.piano(hz(n), 2.6, vel=0.7) for n in ["F2", "C3"] + last) * 0.4, T_NAME, 0.6)
    put("fx", A.sub_drop(1.2, 70, 34), T_NAME, 0.35)
    for k, n in enumerate(["C7", "E7", "G7", "A7", "C8"]):
        put("cel", A.bell(hz(n), 0.8, ratio=2.0, index=0.4, decay=0.3), T_SWEEP + k * 0.07, 0.07, p=-0.5 + 0.25 * k)
    put("fx", A.riser(T_WIPE[0] - 2.9, lo=500, hi=9000, f0=200, f1=1200), 2.9, 0.2)
    put("sfx", A.whoosh(0.5, True, 1, 400, 8000, -0.8, 0.8), T_WIPE[0], 0.4)

    # ------------------------------------------------------------ the groove
    kick = A.kick(f_hi=170, f_lo=52, p_decay=0.03, a_decay=0.24, hold=0.02, drive=1.4, click=0.35, length=0.4)
    kicks = []
    for bar in range(3, 13):
        for b, g in ((0, 0.8), (1.75, 0.45), (2, 0.7)):
            t = G.at(bar) + b * G.spb
            if in_groove(t):
                put("kick", kick, t, g)
                kicks.append(t)
    for t in beats(0.0, DURATION, 2.0, 1.0):
        if in_groove(t) or any(a <= t < b for a, b in LIGHT):
            put("snare", A.rim(), t, 0.35, p=0.1)
            put("snare", A.clap(0.28, 1600, tail=0.07, seed=int(t * 10)), t, 0.22)
    for t in beats(0.0, DURATION, 0.25):
        if in_groove(t) or any(a <= t < b for a, b in LIGHT):
            k = round(t / S16) % 4
            put("hats", A.hat(0.03 if k != 2 else 0.05, bright=0.8, seed=int(t * 100) % 71), swing(t),
                (0.1, 0.05, 0.14, 0.06)[k], p=(-0.35, 0.35)[k % 2])
    # Rhodes comping and a walking bass
    for bar in range(3, 13):
        root, voicing = CHORDS[bar]
        for b in (0.0, 1.5, 2.5):
            t = swing(G.at(bar) + b * G.spb)
            if not (in_groove(t) or any(a <= t < c for a, c in LIGHT) or bar == 12):
                continue
            for n in voicing:
                put("keys", A.epiano(hz(n), 1.1, vel=0.62 if b else 0.75, decay=0.8), t + 0.004 * rng.random(), 0.12,
                    p=float(rng.uniform(-0.3, 0.3)))
        r = hz(root)
        walk = [r, r * 2 ** (4 / 12), r * 2 ** (7 / 12), r * 2 ** (9 / 12)]
        for b in range(4):
            t = G.at(bar) + b * G.spb
            if in_groove(t):
                n = A.n_of(0.42)
                put("bass", A.sine(walk[b], n) * A.adsr(n, 0.006, 0.18, 0.6, 0.08, 0.34), t, 0.5)
                put("bass", A.pluck(walk[b], 0.3, bright=900, decay=0.06, amp_decay=0.15), t, 0.25)
    # a brass stab on the downbeats of the big bars
    for t, notes in ((T_LIME, ["F4", "A4", "C5", "E5"]), (T_CHAT, ["Bb3", "D4", "F4", "A4"]),
                     (T_MAP, ["F4", "A4", "C5", "E5"])):
        put("brass", brass(notes, 0.5, cutoff=3000, attack=0.015), t, 0.26)

    # ------------------------------------------------------------ the ask
    n = len(PROMPT)
    for k in range(n):
        t = T_TYPE[0] + k * (T_TYPE[1] - T_TYPE[0]) / n
        put("sfx", A.key(seed=100 + k), t, 0.16, float(rng.uniform(-0.3, 0.3)))
    put("sfx", A.click(2400, 0.02, 0.003, 0.5), T_SEND, 0.5)
    put("sfx", A.whoosh(0.4, True, 5, 400, 9000, 0.0, 0.0), T_SEND + 0.02, 0.4)
    # the giant words: each lands with a punch
    for k, (t, word, fill) in enumerate(WORDS):
        put("sfx", A.whoosh(0.28, False, 20 + k, 300, 6000, 0.6, -0.6), t - 0.12, 0.25)
        put("kick", kick, t, 0.55)
        put("sfx", A.data_burst(0.14, 90, 30 + k, 2000, 8000), t, 0.12)
        if fill == "glow":
            for j, nn in enumerate(["F6", "A6", "C7", "E7", "G7"]):
                put("cel", A.bell(hz(nn), 0.9, ratio=2.0, index=0.5, decay=0.3), t + 0.05 * j, 0.1, p=-0.5 + 0.25 * j)

    # ------------------------------------------------------------ finding: the bowl
    put("sfx", A.whoosh(0.4, False, 40, 300, 7000, -0.5, 0.5), T_FIND - 0.05, 0.3)
    for k in range(12):
        t = T_FIND + 0.15 + k * 0.16
        put("sfx", A.blip(900 + 300 * (k % 3), 0.05), t, 0.08, p=-0.4 + 0.4 * (k % 3))
    for k, t in enumerate(T_DROPS):
        f = (330, 294, 262)[k]
        n2 = A.n_of(0.3)
        plop = A.sine(np.geomspace(f * 2, f * 0.7, n2), n2) * A.env_exp(n2, 0.08)
        put("sfx", plop, t, 0.45)
        put("sfx", A.data_burst(0.25, 60, 50 + k, 3000, 9000), t, 0.1)
    put("sfx", A.riser(0.5, lo=800, hi=10000, f0=400, f1=1800), T_RISE - 0.1, 0.18)
    for k, nn in enumerate(["C6", "F6", "A6", "C7"]):
        put("cel", A.bell(hz(nn), 1.0, ratio=3.0, index=0.9, decay=0.4), T_RISE + 0.06 * k, 0.12)

    # ------------------------------------------------------------ carousel and the dining room
    put("sfx", A.whoosh(0.35, True, 60, 400, 8000, 0.0, 0.0), T_LIME, 0.3)
    put("sfx", A.whoosh(0.9, False, 61, 300, 9000, 0.9, -0.9), T_CARDS, 0.45)
    for k in range(9):
        t = T_CARDS + 0.8 * (1 - (1 - (k + 1) / 10) ** 0.35)
        put("sfx", A.click(3500 - 150 * k, 0.012, 0.0015, 0.3), t, 0.2, p=0.6 - 0.12 * k)
    put("sfx", A.blip(1320, 0.08), T_PICK, 0.18)
    put("brass", brass(["F4", "A4", "C5", "E5", "G5"], 1.4, cutoff=3600), T_FULL, 0.3)
    put("pad", A.pad([hz(n) for n in ["F3", "C4", "E4", "A4", "G5"]], 1.4, attack=0.15, release=0.5, cutoff=2600,
                     voices=6), T_FULL, 0.4)
    for k in range(8):
        f = hz(["E7", "G7", "C7", "A6"][k % 4])
        put("cel", A.bell(f, 0.7, ratio=2.0, index=0.4, decay=0.3), T_FULL + 0.1 + 0.11 * k, 0.07, p=-0.7 + 0.2 * k)
    put("sfx", A.whoosh(0.45, True, 62, 300, 8000, 0.0, 0.0), T_TO_CHAT, 0.35)

    # ------------------------------------------------------------ chat
    for k, t in enumerate(T_MSG):
        put("sfx", A.blip(880 if k == 0 else 1180, 0.06), t, 0.16, p=0.3 if k == 0 else -0.3)
        put("sfx", A.click(4000, 0.01, 0.001), t, 0.12)
    for k in range(4):
        put("sfx", A.blip(1500, 0.03), T_MSG[1] - 0.38 + 0.1 * k, 0.05)
    put("sfx", A.click(2200, 0.025, 0.003, 0.5), T_TAP, 0.55)
    for k, nn in enumerate(["C6", "E6", "G6", "C7"]):
        put("cel", A.bell(hz(nn), 1.2, ratio=2.0, index=0.6, decay=0.45), T_TAP + 0.1 + 0.07 * k, 0.14)

    # ------------------------------------------------------------ the map
    put("sfx", A.whoosh(0.6, True, 70, 300, 9000, -0.5, 0.5), T_MAP - 0.25, 0.4)
    put("sfx", A.draw_tone(T_ROUTE[1] - T_ROUTE[0], 500, 2200), T_ROUTE[0], 0.14)
    put("sfx", A.blip(990, 0.08), T_MAP + 0.35, 0.18)
    for k in range(10):
        t = T_GO[0] + k * (T_GO[1] - T_GO[0]) / 10
        put("sfx", A.click(1800 + 200 * (k % 2), 0.012, 0.002, 0.2), t, 0.1, p=(-0.3, 0.3)[k % 2])
    for k, nn in enumerate(["F6", "A6", "C7"]):
        put("cel", A.bell(hz(nn), 1.2, ratio=2.0, index=0.6, decay=0.4), T_GO[1] + 0.06 * k, 0.14)

    # ------------------------------------------------------------ the closing words and the name
    put("sfx", A.whoosh(0.5, False, 80, 300, 7000, 0.0, 0.0), T_CRAVE - 0.3, 0.25)
    for k, t in enumerate(T_ROLL):
        put("sfx", A.data_burst(0.18, 100, 90 + k, 2000, 7000), t - 0.05, 0.14)
        put("sfx", A.blip(1000 + 200 * k, 0.05), t, 0.12)
    for k in range(5):
        put("sfx", A.click(3000, 0.01, 0.0012, 0.2), T_WAIT + 0.1 + 0.12 * k, 0.12)
    final = ["F2", "C3", "A3", "C4", "E4", "G4", "A4"]
    put("piano", sum(A.piano(hz(n), 3.4, vel=0.8) for n in final) * 0.35, T_END, 0.7)
    put("brass", brass(["F3", "A3", "C4", "E4", "G4"], 2.6, cutoff=2800, attack=0.08), T_END, 0.36)
    put("pad", A.pad([hz(n) for n in ["F3", "A3", "C4", "E4", "G4"]], 3.4, attack=0.1, release=1.4, cutoff=2200,
                     voices=6), T_END, 0.42)
    put("fx", A.sub_drop(1.4, 72, 30), T_END, 0.4)
    put("fx", A.crash(2.4, seed=90), T_END, 0.18)
    for k, nn in enumerate(["C6", "F6", "A6", "C7", "E7", "F7", "A7", "C8"]):
        put("cel", A.bell(hz(nn), 1.6, ratio=4.0, index=1.0, decay=0.6), T_END + 0.25 + 0.05 * k, 0.1,
            p=-0.7 + 0.2 * k)
    for k, nn in enumerate(["G7", "A7", "C8", "E8"]):
        put("cel", A.bell(hz(nn), 0.8, ratio=2.0, index=0.4, decay=0.3), T_END + 1.1 + 0.08 * k, 0.07, p=0.5 - 0.3 * k)
    return mix, kicks


def process(mix, kicks):
    b = mix.buses
    n = mix.n
    z = np.zeros((n, 2))
    g = lambda k: b.get(k, z)   # noqa: E731
    side = A.duck(n, kicks, depth=0.35, release=0.16)[:, None]
    out = g("kick") * 0.8 + g("snare") + A.reverb(g("snare"), t60=1.0, seed=2) * 0.25 + g("hats") * 0.7
    keys = g("keys") + A.reverb(g("keys"), t60=2.0, seed=3) * 0.35
    out += keys * side
    out += g("bass") * side
    out += g("brass") + A.reverb(g("brass"), t60=2.4, seed=4) * 0.4
    out += g("pad") * 0.9 + A.reverb(g("pad"), t60=3.0, seed=5) * 0.3
    out += g("piano") + A.reverb(g("piano"), t60=2.8, seed=6) * 0.45
    cel = g("cel")
    out += cel + A.delay(cel, G.spb * 0.75, 0.35) * 0.25 + A.reverb(cel, t60=2.6, seed=7) * 0.45
    out += g("fx")
    # the thinking bowl hears the groove through a wall
    t = np.arange(n) / A.SR
    muffle = np.clip((t - T_FIND) / 0.1, 0, 1) * np.clip((T_LIME - t) / 0.1, 0, 1)
    if muffle.max() > 0:
        low = A.filt(out, "lowpass", 900)
        out = out * (1 - muffle[:, None]) + low * muffle[:, None] * 1.2
    sfx = A.filt(g("sfx"), "highpass", 60)
    out += sfx * 1.2 + A.reverb(sfx, t60=0.8, seed=8) * 0.15
    return A.master(out, target=-12.0, ceiling=-1.0)


def render(path):
    mix, kicks = build()
    x = process(mix, kicks)[:A.n_of(DURATION)]
    A.write_wav(path, x)
    return x
