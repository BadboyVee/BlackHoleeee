"""AGI WEEK soundtrack: 128 BPM future house in A minor, synthesised, no samples.

A filtered open with a hit on every word and a big one on "AGI."; the kick comes in with the cards; each lab gets
its own colour over the groove (warm bells, a clean pluck, a bright arp, a growling reese); a two-bar build under
DevDay drops on "(AGI?)"; the IPO lifts to G and the end resolves to C major. Every click, key, card, flip and
wipe on screen has its sound on the grid."""
import numpy as np

from engine import audio as A
from engine.audio import hz
from .score import (G, DURATION, OPEN_WORDS, T_AGI, T_TICK, T_SLATE, T_DROPS, T_STACKED, T_FAN, T_DIVE, T_ANT,
                    T_PICKER, T_PICK, T_ANT_FOUNDERS, T_FABLE, T_OAI, T_OAI_TYPE, T_OAI_SEND, T_AGENT,
                    T_OAI_FOUNDER, T_RACE, T_RACE_FOUNDERS, T_XAI, T_ROLL, T_XAI_FOUNDER,
                    T_DEV, T_TOMORROW, T_BUILD, T_MYSTERY, T_DROP, T_IPO, T_RISE, T_ON_TOP, T_END)

SPB = G.spb
S16 = SPB / 4
AM = ("A1", ["A3", "E4", "A4", "C5"])
FM = ("F1", ["F3", "C4", "F4", "A4"])
CM = ("C2", ["G3", "C4", "E4", "G4"])
GM = ("G1", ["G3", "B3", "D4", "G4"])
PROG = [AM, FM, CM, GM]


def chord(bar):
    if bar == 17:
        return GM
    if bar >= 18:
        return CM
    return PROG[(bar - 1) % 4]


def bar_t(bar, beat=1, six=0.0):
    return G.at(bar, beat, six)


# where the full groove plays; bar 14 is the build, bar 18 the end
GROOVE_BARS = set(range(3, 14)) | {15, 16, 17}
FULL_BARS = set(range(5, 14)) | {15, 16, 17}      # claps and 16ths from the first lab on


def brass(notes, length, cutoff=3200.0, attack=0.01):
    return A.supersaw([hz(n) for n in notes], length, voices=5, detune=0.14, attack=attack, decay=0.3,
                      sustain=0.7, release=0.3, cutoff=cutoff, cut_env=1.2, cut_decay=0.2, width=0.9)


def build():
    mix = A.Mix(DURATION, tail=1.5)
    put = mix.put
    rng = np.random.default_rng(3)
    kicks = []

    # ------------------------------------------------------------ the open
    put("pad", A.pad([hz(n) for n in AM[1]], G.bar_len * 1.02, attack=0.4, release=0.3, cutoff=900), 0.0, 0.3)
    put("pad", A.pad([hz(n) for n in FM[1]], G.bar_len, attack=0.2, release=0.6, cutoff=1400), G.bar_len, 0.3)
    put("sfx", A.data_burst(0.5, 70, 1, 2500, 9000), 0.05, 0.1)
    for k, (t, w) in enumerate(OPEN_WORDS[:-1]):                 # a thump and a click for every word
        put("kick", A.kick(f_hi=120, f_lo=48, a_decay=0.18, click=0.25, length=0.3), t, 0.45)
        put("sfx", A.click(2600 + 300 * k, 0.012, 0.002, 0.3), t, 0.2, p=-0.3 + 0.2 * k)
    put("fx", A.reverse(A.crash(1.6, seed=2)), T_AGI - 1.6, 0.22)
    put("fx", A.riser(1.4, lo=300, hi=7000, tone=0.25, f0=110, f1=660), T_AGI - 1.4, 0.2)
    put("fx", A.impact(2.2, seed=3), T_AGI, 0.35)
    put("fx", A.sub_drop(1.4, 70, 30), T_AGI, 0.5)
    put("lead", brass(["A3", "E4", "A4", "C5", "E5"], 1.6, cutoff=4200), T_AGI, 0.32)
    for k, n in enumerate(["E6", "A6", "C7", "E7"]):
        put("bell", A.bell(hz(n), 1.4, ratio=3.0, index=0.8, decay=0.5), T_AGI + 0.05 * k, 0.1, p=-0.4 + 0.25 * k)
    put("sfx", A.blip(1320, 0.07), T_TICK, 0.2)
    put("sfx", A.click(4000, 0.01, 0.0015, 0.2), T_TICK + 0.08, 0.15)
    put("sfx", A.whoosh(0.35, True, 4, 300, 8000, 0.0, 0.0), T_SLATE - 0.3, 0.45)

    # ------------------------------------------------------------ the groove
    kick = A.kick(f_hi=190, f_lo=50, p_decay=0.03, a_decay=0.26, hold=0.02, drive=1.8, click=0.4, length=0.42)
    for bar in range(1, 21):
        root, voicing = chord(bar)
        t0 = bar_t(bar)
        if bar in GROOVE_BARS:
            for b in range(4):
                t = t0 + b * SPB
                put("kick", kick, t, 0.85)
                kicks.append(t)
            for b in range(4):                                    # open hat on the off-beats
                put("hats", A.hat(0.09, bright=0.9, seed=bar * 7 + b), t0 + (b + 0.5) * SPB, 0.16, p=0.25)
            # the bass: a pumping pluck on the off-beat eighths
            for b in range(4):
                t = t0 + (b + 0.5) * SPB
                put("bass", A.pluck(hz(root) * 2, 0.26, bright=1400, decay=0.05, amp_decay=0.16), t, 0.45)
                n = A.n_of(0.25)
                put("bass", A.sine(hz(root), n) * A.adsr(n, 0.004, 0.1, 0.7, 0.05, 0.2), t, 0.55)
            # the chord bed, pumped by the kick
            put("chords", A.supersaw([hz(n) for n in voicing], G.bar_len, voices=7, detune=0.2, attack=0.01,
                                     decay=0.4, sustain=0.75, release=0.1, cutoff=2600, width=1.0), t0, 0.2)
        if bar in FULL_BARS:
            for b in (1, 3):
                put("snare", A.clap(0.3, 1500, tail=0.1, seed=bar + b), t0 + b * SPB, 0.35, p=0.05)
            for s in range(16):
                if s % 2 == 1:
                    put("hats", A.hat(0.025, bright=1.1, seed=bar * 31 + s), t0 + s * S16, 0.07,
                        p=(-0.3, 0.3)[s % 4 == 1])
    # the slate: every card lands with a thud and a flap
    for k, t in enumerate(T_DROPS):
        put("sfx", A.whoosh(0.26, False, 20 + k, 400, 6000, 0.6, 0.2), t - 0.24, 0.22)
        put("sfx", A.tom(95 + 8 * k, 0.3, seed=30 + k), t, 0.3, p=0.3)
        put("sfx", A.flap(seed=40 + k, lock=True), t, 0.25, p=0.3)
    put("snare", A.clap(0.4, 1300, tail=0.16, seed=9), T_STACKED, 0.5)
    put("fx", A.crash(1.8, seed=10), T_STACKED, 0.16)
    put("sfx", A.swish(0.4, seed=11), T_FAN, 0.3)
    put("sfx", A.whoosh(0.35, True, 12, 300, 9000, -0.6, 0.0), T_DIVE - 0.05, 0.4)

    # ------------------------------------------------------------ Anthropic: warm bells
    put("sfx", A.whoosh(0.4, False, 50, 300, 5000, 0.4, 0.0), T_ANT + 0.2, 0.18)
    put("sfx", A.click(2200, 0.02, 0.003, 0.4), T_PICKER, 0.45)
    for k in range(5):                                           # the menu rows tick past the pointer
        put("sfx", A.click(3200, 0.01, 0.0015, 0.2), T_PICKER + 0.1 + 0.07 * k, 0.1)
    put("sfx", A.click(1900, 0.02, 0.003, 0.5), T_PICK, 0.55)
    for k, n in enumerate(["A5", "C6", "E6", "A6", "C7"]):
        put("bell", A.bell(hz(n), 1.2, ratio=2.0, index=0.6, decay=0.45), T_PICK + 0.06 * k, 0.13, p=-0.5 + 0.25 * k)
    put("sfx", A.whoosh(0.45, True, 51, 300, 7000, -0.5, -0.1), T_ANT_FOUNDERS - 0.1, 0.22)
    for k, n in enumerate(["E6", "G6", "C7"]):
        put("bell", A.bell(hz(n), 1.0, ratio=3.5, index=0.9, decay=0.4), T_FABLE + 0.08 * k, 0.09)
    put("sfx", A.whoosh(0.3, True, 52, 400, 9000, 0.3, 0.0), T_OAI - 0.26, 0.35)

    # ------------------------------------------------------------ OpenAI: keys and a clean pluck
    prompt_len = len("What are you launching at DevDay?")
    for k in range(prompt_len):
        t = T_OAI_TYPE[0] + (T_OAI_TYPE[1] - T_OAI_TYPE[0]) * k / prompt_len
        put("sfx", A.key(seed=100 + k), t, 0.11, p=float(rng.uniform(-0.3, 0.3)))
    put("sfx", A.click(2400, 0.02, 0.003, 0.5), T_OAI_SEND, 0.45)
    put("sfx", A.whoosh(0.35, True, 60, 500, 9000, 0.0, 0.4), T_OAI_SEND + 0.02, 0.3)
    put("sfx", A.data_burst(0.3, 90, 61, 2000, 8000), T_AGENT, 0.14)
    put("sfx", A.blip(988, 0.07), T_AGENT, 0.18)
    put("sfx", A.whoosh(0.45, True, 62, 300, 7000, -0.5, -0.1), T_OAI_FOUNDER - 0.1, 0.2)
    for s in range(16):                                          # a clean arp over bar 8
        root, voicing = chord(8)
        n = voicing[[0, 1, 2, 3, 2, 1][s % 6]]
        put("lead", A.pluck(hz(n) * 2, 0.22, bright=4200, decay=0.06, amp_decay=0.12), bar_t(8) + s * S16, 0.1,
            p=(-0.35, 0.35)[s % 2])

    # ------------------------------------------------------------ the race: a bright arp
    put("sfx", A.whoosh(0.4, True, 70, 400, 8000, 0.8, 0.2), T_RACE - 0.22, 0.4)
    for k, t in enumerate((T_RACE + 0.15, T_RACE + 0.3)):
        put("sfx", A.blip((880, 1175)[k], 0.08), t, 0.2, p=(-0.5, 0.5)[k])
    put("sfx", A.whoosh(0.45, True, 71, 300, 7000, 0.0, 0.0), T_RACE_FOUNDERS - 0.1, 0.22)
    for bar in (9, 10):
        root, voicing = chord(bar)
        for s in range(16):
            n = (voicing + [voicing[1]])[[0, 2, 1, 3, 4, 2][s % 6]]
            put("lead", A.pluck(hz(n) * 2, 0.2, bright=6000, decay=0.05, amp_decay=0.1), bar_t(bar) + s * S16,
                0.1, p=(-0.4, 0.4)[s % 2])

    # ------------------------------------------------------------ xAI: a growl and a glitch
    put("sfx", A.whoosh(0.4, False, 80, 300, 6000, 0.0, 0.0), T_XAI - 0.25, 0.35)
    for bar in (11, 12):
        root, _ = chord(bar)
        put("bass", A.reese(hz(root), G.bar_len * 0.95, cutoff=520, lfo=0.5), bar_t(bar), 0.3)
    for k in range(6):
        put("sfx", A.click(1800 + 250 * k, 0.012, 0.002, 0.3), T_ROLL - 0.12 + 0.04 * k, 0.12)
    put("sfx", A.data_burst(0.22, 140, 81, 1500, 9000, decay_out=False), T_ROLL, 0.22)
    put("fx", A.impact(1.2, seed=82), T_ROLL, 0.15)
    for k in range(len("Is 4.8 dropping this week?")):
        put("sfx", A.key(seed=200 + k), T_XAI + 0.9 + 1.0 * k / 26, 0.08, p=0.3)
    put("sfx", A.whoosh(0.45, True, 83, 300, 7000, -0.5, -0.1), T_XAI_FOUNDER - 0.1, 0.2)

    # ------------------------------------------------------------ DevDay: the build
    put("sfx", A.whoosh(0.35, True, 90, 400, 9000, -0.8, 0.8), T_DEV - 0.22, 0.45)
    put("fx", A.impact(1.6, seed=91), T_DEV, 0.2)
    put("sfx", A.data_burst(0.45, 80, 92, 2000, 8000), T_DEV + 0.02, 0.1)
    put("sfx", A.whoosh(0.5, True, 93, 300, 6000, 0.0, 0.0), T_DEV + 0.1, 0.2)
    put("sfx", A.blip(1568, 0.09), T_TOMORROW, 0.22)
    put("bell", A.bell(hz("E6"), 1.2, ratio=2.0, index=0.6, decay=0.4), T_TOMORROW, 0.1)
    for k, t in enumerate(T_MYSTERY):                            # the question marks climb
        put("sfx", A.blip(660 * 2 ** (k / 6), 0.07), t, 0.18, p=(-0.5, 0.5)[k % 2])
    put("fx", A.riser(T_DROP - T_BUILD + 0.9, lo=250, hi=11000, tone=0.35, f0=110, f1=1320),
        T_BUILD - 0.9, 0.3)
    roll = []                                                    # the snare roll speeds up into the drop
    t = T_BUILD
    step = SPB / 2
    while t < T_DROP - 1e-6:
        roll.append(t)
        frac = (t - T_BUILD) / (T_DROP - T_BUILD)
        step = SPB / (2 if frac < 0.5 else 4 if frac < 0.75 else 8)
        t += step
    for k, t in enumerate(roll):
        frac = (t - T_BUILD) / (T_DROP - T_BUILD)
        put("snare", A.snare(200 + 120 * frac, 0.18, seed=100 + k), t, 0.12 + 0.3 * frac)
    put("fx", A.reverse(A.crash(1.2, seed=99)), T_DROP - 1.2, 0.25)
    put("pad", A.pad([hz(n) for n in GM[1]], G.bar_len, attack=0.3, release=0.2, cutoff=1800), T_BUILD, 0.3)

    # ------------------------------------------------------------ the drop: (AGI?)
    put("fx", A.impact(2.6, seed=110), T_DROP, 0.5)
    put("fx", A.sub_drop(1.8, 75, 28), T_DROP, 0.6)
    put("fx", A.crash(2.4, seed=111), T_DROP, 0.25)
    put("fx", A.braam(hz("A1"), 1.8, seed=112), T_DROP, 0.3)
    put("lead", brass(["A3", "E4", "A4", "C5", "E5", "A5"], G.bar_len * 0.95, cutoff=6000), T_DROP, 0.34)
    for k in range(8):                                           # stutters on the off-beats
        t = T_DROP + (k + 0.5) * SPB / 2
        put("sfx", A.data_burst(0.06, 220, 120 + k, 3000, 10000, decay_out=False), t, 0.1 + 0.03 * (k % 2))
    put("snare", A.clap(0.4, 1200, tail=0.2, seed=121), T_DROP + 0.47, 0.5)

    # ------------------------------------------------------------ the IPO: up to G
    put("sfx", A.whoosh(0.35, True, 130, 400, 8000, 0.0, 0.0), T_IPO - 0.25, 0.4)
    for k, t in enumerate((T_IPO + 0.35, T_IPO + 0.75)):
        put("sfx", A.flap(seed=131 + k, lock=True), t, 0.45)
        put("sfx", A.flap(seed=133 + k), t + 0.05, 0.3)
    for i in range(5):
        put("sfx", A.click(2600 + 200 * i, 0.012, 0.002, 0.3), T_IPO + 0.2 + 0.06 * i, 0.14, p=0.5)
    put("sfx", A.whoosh(0.55, True, 135, 300, 9000, 0.4, 0.4), T_RISE - 0.05, 0.3)
    put("bell", A.ding(hz("E7")), T_RISE + 0.4, 0.14)
    for k, n in enumerate(["C6", "E6", "G6", "C7", "E7"]):
        put("bell", A.bell(hz(n), 1.4, ratio=2.0, index=0.6, decay=0.5), T_ON_TOP + 0.05 * k, 0.1, p=-0.5 + 0.25 * k)
    put("lead", brass(["G3", "D4", "G4", "B4", "D5"], G.bar_len * 0.95, cutoff=4200), T_ON_TOP, 0.26)

    # ------------------------------------------------------------ the end: C major
    put("sfx", A.whoosh(0.35, False, 140, 300, 6000, 0.0, 0.0), T_END - 0.22, 0.35)
    final = ["C2", "G2", "C3", "E3", "G3", "C4", "E4", "G4"]
    put("piano", sum(A.piano(hz(n), 3.4, vel=0.8) for n in final) * 0.3, T_END, 0.7)
    put("pad", A.pad([hz(n) for n in ["C3", "G3", "C4", "E4", "G4"]], 3.2, attack=0.05, release=1.2, cutoff=2600),
        T_END, 0.5)
    put("fx", A.crash(3.0, seed=141), T_END, 0.2)
    put("fx", A.sub_drop(1.4, 65, 30), T_END, 0.4)
    for k, n in enumerate(["G6", "C7", "E7", "G7", "C8"]):
        put("bell", A.bell(hz(n), 1.4, ratio=2.0, index=0.5, decay=0.5), T_END + 0.08 + 0.06 * k, 0.09)
    for i in range(7):
        put("sfx", A.click(2200 + 180 * i, 0.012, 0.002, 0.25), T_END + 1.3 + 0.07 * i, 0.1, p=-0.6 + 0.2 * i)
    return mix, kicks


def process(mix, kicks):
    b = mix.buses
    n = mix.n
    z = np.zeros((n, 2))
    g = lambda k: b.get(k, z)   # noqa: E731
    pump = A.duck(n, kicks, depth=0.55, release=0.2)[:, None]
    out = g("kick") * 0.9 + g("snare") + A.reverb(g("snare"), t60=1.2, seed=2) * 0.25 + g("hats") * 0.8
    out += g("bass") * pump
    out += (g("chords") + A.reverb(g("chords"), t60=2.0, seed=3) * 0.25) * pump
    out += g("lead") + A.delay(g("lead"), SPB * 0.75, 0.3) * 0.18 + A.reverb(g("lead"), t60=2.2, seed=4) * 0.3
    out += g("pad") + A.reverb(g("pad"), t60=3.0, seed=5) * 0.35
    out += g("piano") + A.reverb(g("piano"), t60=2.8, seed=6) * 0.4
    bell = g("bell")
    out += bell + A.delay(bell, SPB * 0.75, 0.35) * 0.22 + A.reverb(bell, t60=2.6, seed=7) * 0.4
    # the build: the music closes behind a sweeping low-pass until the drop opens it (the effects stay bright)
    t = np.arange(n) / A.SR
    sweep = np.clip((t - T_DEV) / (T_DROP - T_DEV), 0, 1) * (t < T_DROP)
    if sweep.max() > 0:
        low = A.filt(out, "lowpass", 700)
        m = (sweep ** 1.5)[:, None] * 0.7
        out = out * (1 - m) + low * m
    out += g("fx")
    sfx = A.filt(g("sfx"), "highpass", 80)
    out += sfx * 1.1 + A.reverb(sfx, t60=0.8, seed=8) * 0.12
    return A.master(out, target=-11.0, ceiling=-1.0)


def render(path):
    mix, kicks = build()
    x = process(mix, kicks)[:A.n_of(DURATION)]
    A.write_wav(path, x)
    return x
