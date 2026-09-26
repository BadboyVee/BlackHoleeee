"""DARIO AMODEI soundtrack: 120 BPM, B minor resolving to D major, 32.8 seconds, no samples.

It opens with the pops of single neurons on a lab monitor, lets them fall into the sixteenth-note
grid, and builds from felt piano to a full chorus on "Machines of Loving Grace".
"""
import numpy as np

from engine import audio as A
from engine.audio import hz, midi
from .score import (G, DURATION, KICKS, CLAPS, SPIKES, CHORD_OF_BAR, T_PHYS, T_SAFE, T_SCALE, T_ANTH,
                    T_GRACE, T_CENTURY, T_DOMAINS, T_FIN, T_LAST, BREATH, beats)

S16 = G.spb / 4
ROOTS = {"Bm": ("B2", 3), "G": ("G2", 4), "D": ("D3", 4), "A": ("A2", 4)}


def triad(name, octave=0):
    root, third = ROOTS[name]
    r = midi(root) + 12 * octave
    return [hz(r), hz(r + third), hz(r + 7)]


def arp_notes(name):
    root, third = ROOTS[name]
    r = midi(root) + 12
    return [r, r + 7, r + 12, r + 12 + third, r + 19, r + 12, r + 7, r + third]


MELODY = [(11, 0, "B4", .5), (11, .5, "D5", .5), (11, 1, "F#5", 1), (11, 2, "E5", .5), (11, 2.5, "D5", .5), (11, 3, "E5", 1),
          (12, 0, "D5", .5), (12, .5, "B4", .5), (12, 1, "G5", 1), (12, 2, "F#5", .5), (12, 2.5, "E5", .5), (12, 3, "D5", 1),
          (13, 0, "A4", .5), (13, .5, "D5", .5), (13, 1, "F#5", 1), (13, 2, "A5", 1.5), (13, 3.5, "F#5", .5),
          (14, 0, "G5", 2), (14, 2, "F#5", 1), (14, 3, "E5", 1),
          (15, 0, "E5", 1), (15, 1, "F#5", 1), (15, 2, "E5", 1), (15, 3, "C#5", 1),
          (16, 0, "D5", 4)]


def build():
    mix = A.Mix(DURATION, tail=1.5)
    put = mix.put
    rng = np.random.default_rng(7)

    # ------------------------------------------------------------ prologue: neurons
    put("drone", A.pad([hz("B1"), hz("F#2"), hz("B2")], T_PHYS, attack=1.2, release=0.3, cutoff=520, seed=2), 0.0, 0.6)
    for k, t in enumerate(SPIKES):
        put("spikes", A.spike(seed=k), t, 0.9 if t < G.at(2) else 0.75, p=float(rng.uniform(-0.6, 0.6)))
    put("fx", A.reverse(A.crash(1.6, seed=3)), T_PHYS - 1.6, 0.35)

    # ------------------------------------------------------------ felt piano ostinato, bars 3-10
    for bar in range(3, 11):
        ch = CHORD_OF_BAR[bar]
        notes = arp_notes(ch)
        per = 0.5 if bar < 7 else 0.25          # eighths, then sixteenths from SCALE on
        n_steps = int(4 / per)
        for s in range(n_steps):
            m = notes[s % 8] + (12 * (s // 8) if bar >= 7 else 0)
            vel = 0.55 + 0.25 * (s % 4 == 0)
            put("piano", A.piano(hz(m), 1.6, vel=vel, decay=1.2), G.at(bar) + s * per * G.spb, 0.34 if bar < 7 else 0.26,
                p=0.25 * np.sin(s * 0.9))
        # the spikes keep time as a soft click on the sixteenths in PHYSICS
        if bar < 5:
            for s in range(16):
                if s % 4 in (1, 3) or s % 8 == 6:
                    put("spikes", A.spike(seed=500 + bar * 16 + s), G.at(bar) + s * S16, 0.5, p=0.5 if s % 2 else -0.5)

    # ------------------------------------------------------------ drums
    kick = A.kick(f_hi=200, f_lo=52, p_decay=0.045, a_decay=0.34, hold=0.03, drive=1.8, click=0.7, length=0.55)
    for t in KICKS:
        put("kick", kick, t, 0.9)
    for t in beats(5, 7, 4.0, 2.0):
        put("snare", A.clap(0.45, 1100, tail=0.16, seed=int(t * 10)), t, 0.5)
    for t in CLAPS:
        put("snare", A.clap(0.4, 1300, seed=int(t * 10)), t, 0.55)
    for t in beats(7, 11, 1.0, 0.5):
        put("hats", A.hat(0.05, seed=int(t * 100) % 91), t, 0.3, p=0.2)
    for t in beats(11, 16, 0.25):
        k = round(t / S16) % 4
        put("hats", A.hat(0.03, seed=int(t * 100) % 89), t, (0.12, 0.08, 0.3, 0.1)[k], p=0.25)
    for t in beats(11, 16, 1.0, 0.5):
        put("hats", A.hat(0.22, seed=5), t, 0.2, p=-0.2)
    for t in beats(9, 11, 1.0):
        put("hats", A.ride(1.0, seed=int(t)), t, 0.18, p=0.3)

    # ------------------------------------------------------------ bass
    for bar in (5, 6):
        root = triad(CHORD_OF_BAR[bar], -1)[0]
        n = A.n_of(G.bar_len)
        put("bass", A.sine(root, n) * A.adsr(n, 0.08, 0.3, 0.8, 0.2, G.bar_len - 0.2), G.at(bar), 0.55)
    for bar in (7, 8):
        root = triad(CHORD_OF_BAR[bar], -1)[0]
        for s in range(8):
            f = root * (2 if s % 2 else 1)
            put("bass", A.pluck(f, 0.22, bright=900, decay=0.06, amp_decay=0.16, q=1.2), G.at(bar) + s * G.spb / 2, 0.55)
    for bar in range(9, 16):
        root = triad(CHORD_OF_BAR[bar], -1)[0]
        for b in range(4):
            put("bass", A.reese(root, 0.24, detune=0.1, cutoff=700, sub=0.9, drive=1.4), G.at(bar, b + 1) + G.spb / 2, 0.5)

    # ------------------------------------------------------------ pads and chords
    for bar in range(5, 11):
        ch = CHORD_OF_BAR[bar]
        put("pad", A.pad(triad(ch) + [triad(ch)[0] * 2], G.bar_len + 0.5, attack=0.3, release=0.5,
                         cutoff=1300 + 180 * (bar - 5), voices=5), G.at(bar), 0.45)
    for bar in range(11, 16):
        ch = CHORD_OF_BAR[bar]
        for b in range(4):
            put("chords", A.supersaw(triad(ch, 1), G.spb * 0.95, attack=0.004, decay=0.2, sustain=0.55,
                                     release=0.12, cutoff=5200, cut_env=0.8, cut_decay=0.15), G.at(bar, b + 1), 0.4)
        put("pad", A.pad(triad(ch) + [triad(ch)[0] * 2], G.bar_len + 0.3, attack=0.05, release=0.4, cutoff=2400), G.at(bar), 0.35)
    put("chords", A.supersaw([hz("D3"), hz("F#3"), hz("A3"), hz("D4"), hz("F#4")], DURATION - T_LAST, attack=0.005,
                             decay=1.6, sustain=0.35, release=1.0, cutoff=4200, cut_env=1.0, cut_decay=0.4), T_LAST, 0.6)

    # ------------------------------------------------------------ melody
    for bar, b, n, d in MELODY:
        t = G.at(bar) + b * G.spb
        put("bells", A.bell(hz(n), 1.8, ratio=3.5, index=1.4, decay=0.8), t, 0.32, p=0.15)
        put("bells", A.piano(hz(n), 1.8, vel=0.8), t, 0.3, p=-0.15)

    # ------------------------------------------------------------ transitions
    put("fx", A.riser(G.bar_len - BREATH, lo=300, hi=9000, f0=123, f1=988, tone=0.3), G.at(10), 0.5)
    for k in range(8):
        put("snare", A.snare(210, 0.18, seed=70 + k), G.at(10, 3) + k * S16, 0.2 + 0.04 * k)
    put("fx", A.riser(G.bar_len - BREATH, lo=300, hi=10000, f0=147, f1=1175, tone=0.3), G.at(13), 0.45)
    for t in (T_GRACE, T_FIN, T_LAST):
        put("fx", A.impact(3.0, seed=int(t)), t, 0.75 if t != T_LAST else 0.6)
    put("fx", A.reverse(A.crash(1.4, seed=11)), T_ANTH - 1.4, 0.3)
    put("fx", A.crash(2.0, seed=12), T_ANTH, 0.35)
    put("fx", A.crash(2.0, seed=13), T_SCALE, 0.25)

    sound_design(mix)
    return mix


def sound_design(mix):
    from . import scenes_a as SA, scenes_b as SB
    put = mix.put
    rng = np.random.default_rng(17)
    # prologue words
    for t in SA.WORD_TIMES:
        put("sfx", A.blip(880, 0.06), t, 0.3)
        put("sfx", A.click(3000, 0.012, 0.0016), t, 0.4)
    put("sfx", A.whoosh(0.5, False, 3, 200, 5000, 0.0, 0.0), SA.COLLAPSE_T - 0.1, 0.35)
    # chapter markers
    for t in (T_PHYS, T_SAFE, T_SCALE, T_ANTH, T_GRACE, T_FIN):
        put("sfx", A.whoosh(0.45, True, int(t * 10), 200, 7000, -0.7, 0.7), t, 0.35)
        put("sfx", A.click(2200, 0.02, 0.003), t + 0.02, 0.4)
    for k, t in enumerate(SA.PHYS_ENTRY):
        put("sfx", A.data_burst(0.3, 110, 20 + k), t, 0.35, p=-0.5)
        put("sfx", A.blip(660 * (k + 1), 0.06), t, 0.25, p=-0.5)
    # the paper types itself; the name gets highlighted; the five problems tick in
    n = len(SA.PAPER_TITLE)
    for k, ch in enumerate(SA.PAPER_TITLE):
        put("sfx", A.key(seed=600 + k), SA.SAFE_TYPE0 + k * SA.SAFE_TYPE_DUR / n, 0.35 if ch == " " else 0.55, p=-0.3 + 0.6 * k / n)
    put("sfx", A.swish(0.35, seed=31), SA.SAFE_HILITE, 0.55, p=-0.2)
    for k, t in enumerate(SA.PROBLEMS_T):
        put("sfx", A.click(1800, 0.03, 0.004), t, 0.5, p=0.4)
        put("sfx", A.blip(1320 * 2 ** (k * 2 / 12), 0.07), t + 0.08, 0.25, p=0.4)
    put("sfx", A.whoosh(0.4, True, 33, 300, 5000, 0.8, 0.0), SA.SAFE_CARD2 - 0.1, 0.45)
    put("sfx", A.swish(0.3, seed=34), SA.SAFE_CARD2 + 0.1, 0.4)
    # the network doubles on every beat; then the points of the scaling plot land on thirty-seconds
    for k, t in enumerate(SA.NET_STEPS):
        put("sfx", A.blip(440 * 2 ** k, 0.09), t, 0.3)
        put("sfx", A.data_burst(0.18 + 0.05 * k, 90 + 40 * k, 40 + k), t, 0.3)
    for k, t in enumerate(SA.POINT_T):
        put("sfx", A.click(1500 * 2 ** (k / 12), 0.012, 0.0016), t, 0.4, p=-0.6 + 1.2 * k / len(SA.POINT_T))
    put("sfx", A.draw_tone(0.6, 300, 2400), SA.FIT_T, 0.35)
    # ANTHROPIC: the odometer rolls; the mark draws; the spark
    for k, t in enumerate(SB.ODO_T):
        put("sfx", A.flap(seed=700 + k, lock=(k == len(SB.ODO_T) - 1)), t, 0.6 if k < len(SB.ODO_T) - 1 else 0.85)
    put("sfx", A.draw_tone(0.6, 250, 1200), SB.LOGO_T, 0.35, p=0.4)
    for k, t in enumerate(SB.ANTH_TEXT_T):
        put("sfx", A.data_burst(0.25, 110, 50 + k), t, 0.3, p=-0.4)
    put("sfx", A.whoosh(0.45, True, 55, 200, 6000, 0.9, 0.2), SB.CLAUDE_T - 0.15, 0.45)
    put("sfx", A.bell(2349, 1.3, ratio=2.76, index=0.6, decay=0.5), SB.CLAUDE_T + 0.1, 0.25, p=0.5)
    # LOVING GRACE
    for i in range(24):
        put("sfx", A.click(2600 + 60 * i, 0.012, 0.0013), SB.ESSAY_T + i * 0.03, 0.14, p=-0.5 + i / 24)
    put("sfx", A.bell(2960, 1.4, ratio=2.76, index=0.5, decay=0.6), SB.QUOTE_T, 0.22)
    put("sfx", A.whoosh(0.7, False, 60, 200, 7000, 0.9, -0.9), SB.RULER_SQUEEZE, 0.5)
    for k in range(18):
        put("sfx", A.click(4000 + 150 * k, 0.01, 0.001), SB.RULER_SQUEEZE + k * 0.035, 0.2, p=0.8 - 0.09 * k)
    for k, t in enumerate(SB.DOMAIN_T):
        put("sfx", A.click(2000, 0.02, 0.003), t, 0.45, p=-0.6 + 0.3 * k)
        put("sfx", A.bell(hz("D6") * 2 ** ([0, 2, 4, 7, 9][k] / 12), 1.0, ratio=2.76, index=0.5, decay=0.4), t, 0.16, p=-0.6 + 0.3 * k)
    # FINALE
    for i, t in enumerate(SB.NAME_T):
        put("sfx", A.click(2400 + 90 * i, 0.012, 0.0015), t, 0.3, p=-0.5 + i / len(SB.NAME_T))
    put("sfx", A.bell(2349, 1.6, ratio=2.76, index=0.5, decay=0.6), SB.ROLE_T, 0.2)
    for k, t in enumerate(SB.RECAP_T):
        put("sfx", A.click(3000 + 200 * k, 0.012, 0.0015), t, 0.3, p=-0.6 + 0.3 * k)
    put("sfx", A.draw_tone(1.9, 200, 900), SB.TRACE_T, 0.18)
    put("sfx", A.spike(seed=999), T_LAST, 1.0)
    put("sfx", A.data_burst(0.35, 110, 70), T_LAST + 0.3, 0.2)
    # the click beat: euclidean ticks under the drops
    pat = [((i * 9) % 32) < 9 for i in range(32)]
    for bar in list(range(9, 16)):
        for s, on in enumerate(pat):
            if on:
                put("clicks", A.click((8500, 6000, 11000, 7000)[s % 4], 0.008, 0.0009, 0.1), G.at(bar) + s * S16 / 2,
                    0.3, p=(-0.7, 0.7)[s % 2])


def process(mix):
    b = mix.buses
    n = mix.n
    k_times = np.array(KICKS)
    side = A.duck(n, k_times, depth=0.7, attack=0.003, release=0.15)
    soft = A.duck(n, k_times, depth=0.4, attack=0.003, release=0.12)
    out = b["kick"] * 0.8
    out += b["snare"] + A.reverb(b["snare"], t60=1.4, seed=3) * 0.45
    out += b["hats"] * 0.8
    out += b["bass"] * side[:, None] * 0.9
    out += b["spikes"] * 1.1 + A.reverb(b["spikes"], t60=1.6, seed=4) * 0.35
    out += (b["piano"] + A.reverb(b["piano"], t60=2.4, seed=5) * 0.5 + A.delay(b["piano"], G.spb * 0.75, 0.3) * 0.2) * soft[:, None] * 1.3
    out += (b["pad"] + A.reverb(b["pad"], t60=3.0, seed=6) * 0.5) * soft[:, None] * 1.4
    out += (b["chords"] + A.reverb(b["chords"], t60=2.6, seed=7) * 0.45) * side[:, None] * 1.5
    out += (b["bells"] + A.reverb(b["bells"], t60=2.4, seed=8) * 0.55 + A.delay(b["bells"], G.spb * 0.75, 0.35) * 0.3) * 1.3
    out += b["drone"] + A.reverb(b["drone"], t60=3.0, seed=9) * 0.6
    out += b["fx"] * 0.9
    sfx = A.filt(b["sfx"], "highpass", 40)
    out += sfx * 1.3 + A.reverb(sfx, t60=1.3, seed=10) * 0.3
    out += A.filt(b["clicks"], "highpass", 3000) * 1.2
    for t in (T_GRACE, T_FIN):
        i0, i1 = A.n_of(t - BREATH), A.n_of(t)
        out[i0:i1] *= np.linspace(1, 0, i1 - i0)[:, None] ** 8
    return A.master(out, target=-11.0, ceiling=-1.0)


def render(path):
    x = process(build())[:A.n_of(DURATION)]
    A.write_wav(path, x)
    return x
