"""THE FRONTIER soundtrack: 150 BPM hard techno in F minor, 26.4 seconds, no samples.

Each contender brings a motif: ASTRA a star arpeggio, GEMINI twin arps mirrored left and right,
FABLE a music-box melody. The finale plays all three at once.
"""
import numpy as np

from engine import audio as A
from engine.audio import hz
from .score import (G, DURATION, KICKS, CLAPS, T_DROP_A, T_DROP_B, T_DROP_C, T_CLASH, T_BUILD,
                    T_FINALE, T_LAST, BREATH, WORDS, STABS_CLASH, beats)

S16 = G.spb / 4
CHORDS = {
    "Fm": ["F3", "Ab3", "C4"], "Db": ["Db3", "F3", "Ab3"], "Eb": ["Eb3", "G3", "Bb3"],
    "C": ["C3", "E3", "G3"], "Ab": ["Ab2", "C3", "Eb3"], "Bbm": ["Bb2", "Db3", "F3"],
}


def chord(name, octave_up=0):
    return [hz(n) * 2 ** octave_up for n in CHORDS[name]]


def build():
    mix = A.Mix(DURATION, tail=1.5)
    put = mix.put

    # ------------------------------------------------------------ cold open
    put("drone", A.pad(chord("Fm", -1), 3.1, attack=0.25, release=0.1, cutoff=700, seed=1), 0.0, 0.55)
    put("braam", A.braam(hz("F1")), 0.0, 0.9)
    put("braam", A.braam(hz("F1"), 2.0, seed=3), G.at(2), 0.8)
    put("fx", A.impact(2.0), 0.0, 0.5)
    for (t, word), f in zip(WORDS, (110, 98, 110, 82, 73, 65)):
        put("hits", A.tom(f, 0.5), t, 0.9)
        put("hits", A.clap(0.35, 1100, tail=0.09, seed=int(f)), t, 0.35)
        put("hits", A.sub_drop(0.6, f * 0.8, 38), t, 0.55)
    for i, t in enumerate(beats(1, 3, 0.5)):
        if t < G.at(2, 3):
            put("tick", A.tick(4200 if i % 2 == 0 else 3100), t, 0.35, p=0.3 if i % 2 else -0.3)
    roll = [G.at(2, 3) + k * G.spb / 2 for k in range(2)]
    roll += [G.at(2, 4) + k * S16 for k in range(3)]
    roll += [G.at(2, 4) + 3 * S16 + k * S16 / 2 for k in range(1)]
    for k, t in enumerate(roll):
        put("snare", A.snare(200, 0.2, seed=40 + k), t, 0.35 + 0.1 * k)
    rz = A.riser(G.at(3) - BREATH - G.at(2), lo=300, hi=10000, f0=90, f1=720)
    put("fx", rz, G.at(2), 0.55)

    # ------------------------------------------------------------ the groove, shared by all drops
    kick = A.kick(f_hi=290, f_lo=46.5, p_decay=0.038, a_decay=0.26, hold=0.025, drive=3.2, click=0.55, length=0.42)
    for t in KICKS:
        put("kick", kick, t, 0.95)
    for t in CLAPS:
        put("clap", A.clap(0.4, 1250, seed=int(t * 10)), t, 0.55)
    for t in beats(3, 12, 0.25) + beats(14, 16, 0.25):
        k = round((t - T_DROP_A) / S16) % 4
        vel = (0.22, 0.12, 0.5, 0.14)[k]
        put("hats", A.hat(0.03 if k != 2 else 0.05, seed=int(t * 100) % 97), t, vel, p=0.25)
    for t in beats(3, 12, 1.0, 0.5) + beats(14, 16, 1.0, 0.5):
        put("hats", A.hat(0.2, seed=7), t, 0.22, p=-0.2)

    # rolling offbeat bass: three sixteenths after every kick
    def rolling(bar0, bar1, roots):
        for bi, bar in enumerate(range(bar0, bar1)):
            root = roots[bi % len(roots)]
            for b in range(4):
                for s in (1, 2, 3):
                    t = G.at(bar, b + 1, s)
                    n = root if s != 3 else root * 2
                    put("bass", A.pluck(n, 0.12, bright=1400, decay=0.05, amp_decay=0.07, q=1.6), t, 0.62)
                    put("bass", A.sine(n / 2 if n > 60 else n, A.n_of(0.1)) * A.env_exp(A.n_of(0.1), 0.05), t, 0.4)

    rolling(3, 6, [hz("F2"), hz("F2"), hz("Db2")])

    # ------------------------------------------------------------ ASTRA: the star arpeggio
    star = ["F5", "Ab5", "C6", "Eb6", "C6", "Ab5", "G5", "C6"]

    def star_arp(bar0, bar1, gain=0.26):
        for i, t in enumerate(beats(bar0, bar1, 0.25)):
            put("arp", A.pluck(hz(star[i % 8]), 0.22, bright=6500, decay=0.05, amp_decay=0.12, wave="square"),
                t, gain, p=0.35 * np.sin(i * 0.7))

    star_arp(3, 6)
    put("stab", A.supersaw(chord("Fm", 1), 0.7, cut_env=1.5, cut_decay=0.12, cutoff=4200, release=0.3), T_DROP_A, 0.55)
    for t in IMPACTS_SOFT():
        put("fx", A.crash(2.2, seed=int(t)), t, 0.45)
    put("fx", A.reverse(A.crash(1.2, seed=9)), T_DROP_B - 1.2, 0.3)
    put("fx", A.downlifter(1.0), G.at(5, 4), 0.35)

    # ------------------------------------------------------------ GEMINI: twin arps, mirrored
    rolls_b = {6: "Db", 7: "Eb", 8: "Fm"}
    for bar, ch in rolls_b.items():
        root = chord(ch)[0] / 2
        for s in (0, 3, 6, 10, 12):
            t = G.at(bar, 1, s)
            put("bass", A.reese(root, 0.26, cutoff=900, sub=0.7), t, 0.5)
        put("stab", A.supersaw(chord(ch, 1), 0.55, cut_env=1.2, cut_decay=0.1, cutoff=3800), G.at(bar), 0.42)
    twin = ["Ab5", "C6", "Eb6", "F6", "Eb6", "C6", "Bb5", "G5"]
    for i, t in enumerate(beats(6, 9, 0.5)):
        n = hz(twin[i % 8])
        put("twins", A.epiano(n, 0.35, vel=0.9, decay=0.25), t, 0.3, p=-0.85)
        put("twins", A.epiano(n * 1.5, 0.35, vel=0.9, decay=0.25), t + S16, 0.24, p=0.85)

    # ------------------------------------------------------------ FABLE: chords open, the music box
    fable_chords = [(9, ["Db3", "F3", "Ab3", "C4"]), (10, ["Ab2", "C3", "Eb3", "G3"]), (11, ["Eb3", "G3", "Bb3", "Db4"])]
    for bar, notes in fable_chords:
        put("pad", A.pad([hz(n) for n in notes], G.bar_len + 0.4, attack=0.08, release=0.35, cutoff=2600, voices=6), G.at(bar), 0.5)
        put("sub", A.sine(hz(notes[0]) / 2, A.n_of(G.bar_len)) * A.adsr(A.n_of(G.bar_len), 0.01, 0.2, 0.9, 0.05, G.bar_len - 0.05), G.at(bar), 0.5)
    melody = [(9, 0, "C6", 1), (9, 1, "Eb6", .5), (9, 1.5, "Db6", .5), (9, 2, "C6", 1), (9, 3, "Ab5", 1),
              (10, 0, "Bb5", 1), (10, 1, "C6", .5), (10, 1.5, "Ab5", .5), (10, 2, "F5", 2),
              (11, 0, "G5", 1), (11, 1, "Ab5", 1), (11, 2, "Bb5", 1), (11, 3, "C6", 1)]
    for bar, b, n, d in melody:
        t = G.at(bar) + b * G.spb
        put("bells", A.bell(hz(n), 1.6, ratio=3.5, index=1.6, decay=0.7), t, 0.34, p=0.1)
        put("bells", A.bell(hz(n) * 2, 0.8, ratio=2.0, index=0.8, decay=0.3), t, 0.08, p=-0.2)
    for i, t in enumerate(beats(9, 10, 0.25)[8:]):
        put("tick", A.rim(), t, 0.12, p=0.4)

    # ------------------------------------------------------------ CLASH: four chord hits, then the build
    for t, ch in STABS_CLASH:
        put("stab", A.supersaw(chord(ch, 1), 0.36, cut_env=2.0, cut_decay=0.08, cutoff=5000, release=0.15), t, 0.7)
        put("stab", A.supersaw(chord(ch), 0.36, cut_env=1.0, cut_decay=0.08, cutoff=2000, release=0.15), t, 0.4)
        put("bass", A.reese(chord(ch)[0] / 2, 0.36, cutoff=1200), t, 0.55)
    for k, f in enumerate((180, 150, 125, 100)):
        put("hits", A.tom(f, 0.3), G.at(12, 4, k), 0.7)
    roll = [T_BUILD + k * G.spb / 2 for k in range(4)] + [G.at(13, 3) + k * S16 for k in range(4)]
    roll += [G.at(13, 4) + k * S16 / 2 for k in range(7)]
    for k, t in enumerate(roll):
        put("snare", A.snare(210, 0.18, seed=60 + k), t, 0.25 + 0.035 * k)
    put("fx", A.riser(T_FINALE - BREATH - T_BUILD, lo=250, hi=12000, f0=110, f1=1760, tone=0.5), T_BUILD, 0.6)

    # ------------------------------------------------------------ FINALE: everything at once
    put("fx", A.impact(3.2), T_FINALE, 0.95)
    put("braam", A.braam(hz("F1"), 2.8, seed=5), T_FINALE, 0.9)
    put("stab", A.supersaw([hz("F3"), hz("Ab3"), hz("C4"), hz("F4")], 1.6, attack=0.005, decay=0.8, sustain=0.4,
                           release=0.5, cutoff=5200, cut_env=1.0, cut_decay=0.3), T_FINALE, 0.6)
    rolling(14, 16, [hz("F2"), hz("Db2")])
    star_arp(14, 16, 0.18)
    for i, t in enumerate(beats(14, 16, 0.5)):
        n = hz(twin[i % 8])
        put("twins", A.epiano(n, 0.3, vel=0.8, decay=0.2), t, 0.18, p=-0.85)
        put("twins", A.epiano(n * 1.5, 0.3, vel=0.8, decay=0.2), t + S16, 0.14, p=0.85)
    for bar, b, n, d in melody[:9]:
        t = G.at(bar + 5) + b * G.spb
        if t < T_LAST:
            put("bells", A.bell(hz(n), 1.4, ratio=3.5, index=1.5, decay=0.6), t, 0.26)
    put("fx", A.impact(3.0, seed=31), T_LAST, 0.8)
    put("stab", A.supersaw([hz("F3"), hz("C4"), hz("G4"), hz("Ab4")], 2.4, attack=0.004, decay=1.5, sustain=0.3,
                           release=0.8, cutoff=4200, cut_env=1.2, cut_decay=0.4), T_LAST, 0.7)
    put("drone", A.pad(chord("Fm", -1), DURATION - T_LAST, attack=0.02, release=1.2, cutoff=900, seed=4), T_LAST, 0.5)

    sound_design(mix)
    return mix


def IMPACTS_SOFT():
    return [T_DROP_A, T_DROP_B, T_DROP_C, T_CLASH]


def process(mix):
    b = mix.buses
    n = mix.n
    k_times = np.array(KICKS)
    side = A.duck(n, k_times, depth=0.8, attack=0.002, release=0.12)
    side_soft = A.duck(n, k_times, depth=0.45, attack=0.002, release=0.1)

    kick = b["kick"]
    rumble = A.reverb(kick, t60=1.2, predelay=0.0, bright=1200, dark=400, seed=2)
    rumble = A.sat(A.filt(rumble, "lowpass", 170) * 6.0, 1.8) * side[:, None]
    # keep the rumble out of the FABLE drop and the build, let it back in for the finale
    gate = np.ones(n)
    for t0, t1 in ((T_DROP_C, T_CLASH), (T_BUILD, T_FINALE)):
        gate[A.n_of(t0):A.n_of(t1)] = 0.25
    gate = np.convolve(gate, np.ones(2400) / 2400, mode="same")
    rumble *= gate[:, None]

    rumble = A.filt(rumble, "highpass", 38)
    out = kick * 0.72 + rumble * 0.38
    out += b["clap"] + A.reverb(b["clap"], t60=1.1, seed=3) * 0.5
    out += b["hats"] * 0.8
    out += (b["bass"] * 0.9) * side[:, None]
    out += A.sat(b.get("sub", np.zeros((n, 2))), 1.3) * side[:, None] * 0.8
    for name, verb, dly in (("arp", 0.35, 0.3), ("twins", 0.3, 0.25), ("bells", 0.5, 0.35)):
        gain = {"arp": 1.5, "twins": 1.5, "bells": 1.35}[name]
        x = b.get(name)
        if x is None:
            continue
        wet = A.reverb(x, t60=1.8, seed=5) * verb + A.delay(x, G.spb * 0.75, fb=0.4) * dly
        out += (x + wet) * side_soft[:, None] * gain
    for name, verb in (("stab", 0.55), ("pad", 0.4), ("drone", 0.5), ("braam", 0.45)):
        x = b.get(name)
        if x is None:
            continue
        y = (x + A.reverb(x, t60=2.6, seed=7) * verb) * (1.6 if name in ("stab", "pad") else 1.0)
        out += y * (side_soft if name in ("stab", "pad") else np.ones(n))[:, None]
    for name in ("hits", "snare", "tick"):
        x = b.get(name)
        if x is not None:
            out += x + A.reverb(x, t60=1.6, seed=11) * 0.45
    out += b["fx"] * 0.9
    sfx = A.filt(b["sfx"], "highpass", 40)
    out += sfx * 1.35 + A.reverb(sfx, t60=1.2, seed=13) * 0.3
    out += A.filt(b["clicks"], "highpass", 3000) * 1.3

    # the breath: a hard silence before each drop and the finale
    for t in (T_DROP_A, T_FINALE):
        i0, i1 = A.n_of(t - BREATH), A.n_of(t)
        out[i0:i1] *= np.linspace(1, 0, i1 - i0)[:, None] ** 8
    return A.master(out, target=-10.0, ceiling=-1.0)


def render(path):
    mix = build()
    x = process(mix)
    x = x[:A.n_of(DURATION)]
    A.write_wav(path, x)
    return x


# ---------------------------------------------------------------- sound design: a click for every event

def euclid(k, n, rot=0):
    """Bjorklund-style even spread of k hits over n steps."""
    return [((i + rot) * k) % n < k for i in range(n)]


def sound_design(mix):
    from . import scenes_a as SA, scenes_b as SB, scenes_c as SC
    put = mix.put
    rng = np.random.default_rng(99)

    # cold open
    put("sfx", A.whoosh(0.55, True, 1, 150, 7000, -0.4, 0.4), 0.0, 0.5)
    for k, (t, _) in enumerate(WORDS):
        put("sfx", A.click(3200 + 400 * k, 0.012, 0.0016), t, 0.5)
        put("sfx", A.blip(95, 0.05), t, 0.45)
    t0 = G.at(2, 3)
    put("sfx", A.draw_tone(0.4, 500, 2200), t0 + 0.1, 0.35)
    for n, (f, p) in enumerate(((880, 0.0), (1320, -0.6), (1760, 0.6))):
        put("sfx", A.blip(f, 0.06), t0 + 0.05 + n * 0.06, 0.4, p=p)
        put("sfx", A.data_burst(0.2, 120, 10 + n), t0 + 0.15 + n * 0.06, 0.35, p=p)

    # ASTRA: every letter lands with a click and a thud
    for i in range(5):
        t = T_DROP_A + i * S16
        put("sfx", A.click(2600 + 350 * i, 0.012, 0.0015), t, 0.55, p=-0.5 + 0.25 * i)
        put("sfx", A.blip(70, 0.06), t, 0.5)
    put("sfx", A.draw_tone(0.5, 350, 1500), G.at(3, 3), 0.35, p=0.5)
    put("sfx", A.data_burst(0.3, 110, 21), G.at(3, 3), 0.35, p=-0.3)
    put("sfx", A.whoosh(0.42, True, 22, 150, 9000, 0.0, 0.0), SA.T_ZOOM, 0.75)
    put("sfx", A.bell(3520, 1.2, ratio=2.76, index=0.6, decay=0.5), SA.T_SPHERE - 0.15, 0.22)
    for r in range(4):
        put("sfx", A.data_burst(0.3, 120, 30 + r), SA.T_SPHERE + 0.05 + (0 if r == 0 else 0.16 + (r - 1) * 0.2), 0.3, p=-0.6)
    for i, t in enumerate(beats(4, 5, 0.25)):
        put("sfx", A.click(7000 + 3000 * rng.random(), 0.01, 0.001), t + S16 / 2, 0.18, p=rng.uniform(-0.8, 0.8))
    put("sfx", A.whoosh(1.2, True, 23, 200, 9000, -0.2, 0.2), SA.T_WARP, 0.5)
    for k, t in enumerate((6.8, 7.1, 7.3, 7.45)):
        put("sfx", A.whoosh(0.25, False, 24 + k, 300, 5000, 0.6, -0.6), t, 0.35)
    for sgn, f in ((-1, 1200), (1, 1800)):
        put("sfx", A.blip(f, 0.08), SA.T_COLLAPSE + 0.28, 0.4, p=0.8 * sgn)

    # GEMINI: twins arrive from both sides and lock with one clack
    put("sfx", A.whoosh(0.8, True, 40, 200, 6000, -1.0, -0.1), T_DROP_B, 0.5)
    put("sfx", A.whoosh(0.8, True, 41, 220, 6400, 1.0, 0.1), T_DROP_B, 0.5)
    put("sfx", A.click(2400, 0.02, 0.003), T_DROP_B + 0.8, 0.6)
    put("sfx", A.blip(110, 0.08), T_DROP_B + 0.8, 0.5)
    put("sfx", A.bell(2637, 1.0, ratio=2.76, index=0.7, decay=0.45), G.at(6, 3, 2), 0.2, p=0.4)
    put("sfx", A.data_burst(0.3, 110, 42), G.at(6, 3), 0.3)
    for k, t in enumerate(beats(6, 7, 1.0)):
        put("sfx", A.blip(660 if k % 2 else 990, 0.05), t, 0.18, p=0.7 if k % 2 else -0.7)
    put("sfx", A.whoosh(0.5, True, 43, 200, 5000, 0.8, -0.2), SB.T_HELIX, 0.4)
    put("sfx", A.bell(3136, 1.0, ratio=2.76, index=0.6, decay=0.45), SB.T_HELIX + 0.05, 0.2, p=0.6)
    for r in range(4):
        put("sfx", A.data_burst(0.28, 120, 44 + r), SB.T_HELIX + 0.05 + (0 if r == 0 else 0.16 + (r - 1) * 0.2), 0.3, p=-0.6)
    for k, t in enumerate(beats(8, 9, 1.0)[:3]):
        put("sfx", A.click(1800, 0.03, 0.004), t, 0.5, p=-0.5 if k % 2 else 0.5)
        put("sfx", A.blip(140, 0.06), t, 0.4)
    for k in range(10):
        put("sfx", A.click(5000 + 300 * k, 0.01, 0.0012), SB.T_WIPE + k * 0.018, 0.3, p=0.8 - 0.16 * k)
    put("sfx", A.whoosh(0.4, True, 48, 300, 7000, 0.9, -0.9), SB.T_WIPE, 0.45)

    # FABLE: the flaps clatter, then the typewriter, then the pages
    for i in range(5):
        lock = T_DROP_C + S16 * (i + 1)
        p = -0.6 + 0.3 * i
        k = 0
        while T_DROP_C + k * 0.05 < lock - 0.01:
            put("sfx", A.flap(seed=100 + 13 * i + k), T_DROP_C + k * 0.05 + 0.004 * i, 0.5, p=p)
            k += 1
        put("sfx", A.flap(seed=200 + i, lock=True), lock, 0.85, p=p)
    put("sfx", A.whoosh(0.35, True, 50, 400, 6000, -0.6, 0.6), T_DROP_C + 0.2, 0.3)
    put("sfx", A.draw_tone(0.4, 450, 1800), T_DROP_C + 0.45, 0.3, p=0.6)
    put("sfx", A.data_burst(0.3, 110, 51), T_DROP_C + 0.35, 0.3)
    n = len(SB.STORY)
    for k, ch in enumerate(SB.STORY):
        t = SB.T_TYPE + 0.02 + k * 0.62 / n
        put("sfx", A.key(seed=300 + k), t, 0.4 if ch == " " else 0.62, p=-0.5 + k / n)
    put("sfx", A.ding(), SB.T_TYPE + 0.68, 0.28, p=0.5)
    put("sfx", A.whoosh(0.4, True, 52, 200, 4000, 0.0, 0.0), SB.T_BOOK, 0.35)
    for k, tf in enumerate(SB.FLIPS):
        put("sfx", A.swish(0.4, seed=60 + k), tf + 0.12, 0.55, p=0.4 - 0.25 * k)
    for r in range(4):
        put("sfx", A.data_burst(0.28, 120, 64 + r), SB.T_BOOK + 0.05 + (0 if r == 0 else 0.16 + (r - 1) * 0.2), 0.28, p=0.6)
    for k in range(6):
        put("sfx", A.bell(2093 * 2 ** (k / 12 * 2), 0.9, ratio=2.76, index=0.5, decay=0.35), SB.T_RIBBON + k * 0.05, 0.1, p=-0.6 + 0.24 * k)

    # CLASH: panels whip in on the beat, the build stamps a letter on every kick
    for k in range(3):
        put("sfx", A.whoosh(0.3, True, 70 + k, 250, 6000, -0.6 + 0.6 * k, -0.6 + 0.6 * k), T_CLASH - 0.12 + 0.04 * k, 0.4)
    for k, t in enumerate(beats(12, 13, 1.0)):
        put("sfx", A.whoosh(0.22, False, 74 + k, 400, 6000, -0.5 + 0.5 * min(k, 2), 0.0), t, 0.3)
        put("sfx", A.click(2200, 0.02, 0.003), t, 0.45)
    for k, t in enumerate(SC.BUILD_KICKS):
        put("sfx", A.click(4200 + 250 * k, 0.012, 0.0015), t, 0.5, p=(-1) ** k * 0.4)
        put("sfx", A.blip(1320 * 2 ** (k / 12), 0.05), t, 0.2)

    # FINALE: three slabs rise and land; the title prints itself
    for k in range(3):
        t = T_FINALE + 0.02 + k * S16
        put("sfx", A.whoosh(0.42, True, 80 + k, 60, 1800, -0.6 + 0.6 * k, -0.6 + 0.6 * k), t, 0.45)
        put("sfx", A.sub_drop(0.5, 70, 38), t + 0.4, 0.35, p=-0.6 + 0.6 * k)
    for i in range(12):
        put("sfx", A.click(3000 + 120 * i, 0.012, 0.0014), T_FINALE + 0.25 + i * 0.045, 0.22, p=-0.6 + 0.11 * i)
    put("sfx", A.data_burst(0.4, 110, 90), T_FINALE + 1.05, 0.3)
    for k in range(3):
        t = G.at(15) + k * G.spb / 2
        put("sfx", A.click(2000, 0.02, 0.003), t, 0.4, p=-0.6 + 0.6 * k)
        put("sfx", A.data_burst(0.25, 120, 91 + k), t + 0.02, 0.25, p=-0.6 + 0.6 * k)
    put("sfx", A.data_burst(0.4, 110, 95), T_LAST + 0.1, 0.25)

    # the click beat: an Ikeda-style euclidean pattern of hard digital clicks under the drops
    pat = euclid(11, 32)
    for bar in list(range(3, 12)) + [14, 15]:
        for s, on in enumerate(pat):
            if on:
                t = G.at(bar) + s * S16 / 2
                f = (9000, 6000, 12000, 7500)[s % 4]
                put("clicks", A.click(f, 0.008, 0.0009, 0.1), t, 0.34, p=(-0.7, 0.7)[s % 2])
