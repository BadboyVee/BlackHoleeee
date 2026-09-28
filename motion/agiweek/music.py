"""AGI WEEK, cut as THE RACE TO AGI: the soundtrack. 128 BPM in A minor, synthesised, no samples.

The grid: an engine idling, a heavy relay clunk as each start light comes on, the revs climbing light by light and
bouncing off the limiter while the lights hold. Lights out is the drop: a launch up through the gears into a
driving sequencer groove with a brass hook. Every car that arrives brakes down through the gears; every car that
leaves goes up through them; the pit stop has its screech, wheel guns and jacks, the radio its beeps, race control
its chime. The build revs an engine against the shift lights to the limiter; the drop lands on a chequered flag, a
crowd and a car flying past; P1 lifts to G and the end resolves to C major."""
import numpy as np

from engine import audio as A
from engine.audio import hz
from .score import (G, DURATION, T_LIGHTS, T_STACKED, T_OUT, T_LINE1, T_LINE2, T_AGI_BOX, T_LAP, T_FLIP, T_BUG,
                    T_ANT, T_ANT_RADIO, T_ANT_LINE1, T_ANT_BOSS, T_ANT_LINE2, T_OAI, T_OAI_CAR2, T_OAI_BOSS, T_RC,
                    T_GRID2, T_STRAP, T_GDM_BOSS, T_MTA_BOSS, T_XAI, T_BOX, T_OFF, T_ON, T_JACK, T_XAI_BOSS,
                    T_LAUNCH, T_DEV, T_BUILD, T_LEDS, T_SHIFT, T_FLAG, T_CROSS, T_P1, T_BOARD_ROWS, T_IPO,
                    T_ON_TOP, T_END, STING)

SR = A.SR
SPB = G.spb
S16 = SPB / 4
AM = ("A1", ["A3", "E4", "A4", "C5"])
FM = ("F1", ["F3", "C4", "F4", "A4"])
CM = ("C2", ["G3", "C4", "E4", "G4"])
GM = ("G1", ["G3", "B3", "D4", "G4"])
FIXED = {1: AM, 2: AM, 14: GM, 15: AM, 16: FM, 17: GM, 18: CM}
GROOVE_BARS = set(range(3, 14)) | {15, 16, 17}
FULL_BARS = set(range(5, 14)) | {15, 16, 17}


def chord(bar):
    return FIXED.get(bar) or [AM, FM, CM, GM][(bar - 3) % 4]


# ---------------------------------------------------------------- the engines

def _curve(keys, t0, n):
    """A per-sample curve through (time, value) keys, starting at t0."""
    ks = np.array(sorted(keys), dtype=float)
    return np.interp(t0 + np.arange(n) / SR, ks[:, 0], ks[:, 1])


def engine(f, seed=0, rasp=0.35, whine=0.06):
    """A racing V6 from its firing frequency (Hz, per sample): a stack of harmonics, a rasp of noise on every
    firing, the turbo's whine, and saturation."""
    n = len(f)
    ph = np.cumsum(f) / SR
    x = np.zeros(n)
    for k in range(1, 13):
        x += (1.0 / k ** 0.75) * (1.25 if k % 2 else 0.8) * np.sin(2 * np.pi * k * ph + 0.9 * k)
    x += 0.5 * np.sin(np.pi * ph)                                   # cylinders never fire quite evenly
    gate = (0.5 + 0.5 * np.cos(2 * np.pi * ph)) ** 8
    x += rasp * 6.0 * A.filt(A.noise(n, seed) * gate, "bandpass", (900, 8000))
    x += whine * np.sin(2 * np.pi * np.cumsum(f * 7.3) / SR)
    x = A.sat(x * 0.35, 2.4)
    return A.filt(x, "lowpass", 9000) * 0.6


def car_sound(t0, t1, rpm, amp, pan, dop=None, seed=0):
    """An engine over [t0, t1): rpm, level, pan and Doppler as (time, value) keys. Stereo."""
    n = A.n_of(t1 - t0)
    r = _curve(rpm, t0, n)
    if dop is not None:
        r = r * _curve(dop, t0, n)
    x = engine(r / 60.0 * 3.0, seed) * _curve(amp, t0, n)
    p = np.clip(_curve(pan, t0, n), -1, 1)
    ang = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(ang), x * np.sin(ang)], 1)


def crack(seed=0):
    """A gearshift: a dry crack from the exhaust."""
    n = A.n_of(0.06)
    t = A.tl(n)
    x = A.filt(A.noise(n, seed), "bandpass", (700, 5200)) * np.exp(-t / 0.008) * 2.4
    x += np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.02)
    return A.fade(x, 0.0002, 0.005)


def visit(put, t_in, t_rest, t_out, pan_rest=0.2, gain=1.0, idle=0.2, seed=0):
    """A car that arrives braking down through the gears, idles in its spot, and launches away up through them."""
    s = t_in - 0.35
    rpm = [(s, 11900), (t_in + 0.22, 12100), (t_in + 0.26, 8400), (t_in + 0.3, 10400), (t_in + 0.38, 7800),
           (t_in + 0.42, 9600), (t_in + 0.52, 7000), (t_in + 0.56, 8600), (t_in + 0.7, 5800), (t_rest + 0.15, 4500),
           (t_out, 4600), (t_out + 0.06, 7400), (t_out + 0.46, 12000), (t_out + 0.5, 9400), (t_out + 1.0, 12100),
           (t_out + 1.04, 9800), (t_out + 1.6, 12000)]
    amp = [(s, 0.0), (t_in, 0.55), (t_in + 0.3, 1.0), (t_rest, 0.6), (t_rest + 0.35, idle), (t_out, idle),
           (t_out + 0.12, 1.0), (t_out + 0.7, 0.35), (t_out + 1.4, 0.0)]
    pan = [(s, -1.0), (t_rest, pan_rest), (t_out, pan_rest), (t_out + 0.7, 1.0)]
    dop = [(s, 1.1), (t_in + 0.3, 1.0), (t_out + 0.2, 1.0), (t_out + 1.0, 0.86)]
    put("engine", car_sound(s, t_out + 1.5, rpm, amp, pan, dop, seed), s, gain)
    for k, dt in enumerate((0.26, 0.38, 0.52)):
        put("engine", crack(seed * 10 + k), t_in + dt, 0.3 * gain, p=-0.5)
    for k, dt in enumerate((0.5, 1.04)):
        put("engine", crack(seed * 10 + 5 + k), t_out + dt, 0.35 * gain * (1 - 0.4 * k), p=0.6)


def pass_by(put, t_pass, length=2.2, rpm=11600, v=80.0, d=9.0, seed=0, gain=1.0):
    """A car flying past: the pitch falls through the Doppler shift as it goes, the air rushes, it pans across."""
    n = A.n_of(length)
    tt = np.arange(n) / SR - length / 2
    x = v * tt
    r = np.sqrt(x * x + d * d)
    f = rpm / 60 * 3 * 343.0 / (343.0 + v * x / r)
    amp = (d / r) ** 1.2
    mono = engine(f, seed) * amp + A.filt(A.noise(n, seed + 1), "bandpass", (400, 6000)) * amp ** 2 * 0.5
    ang = (np.clip(x / (2.5 * d), -1, 1) + 1) * np.pi / 4
    put("engine", np.stack([mono * np.cos(ang), mono * np.sin(ang)], 1), t_pass - length / 2, gain)


def screech(length=0.5, seed=0, f0=1700.0):
    """Tyres locking up, or spinning."""
    n = A.n_of(length)
    t = A.tl(n)
    rng = np.random.default_rng(seed)
    f = f0 + 140 * np.sin(2 * np.pi * 17 * t) + np.cumsum(rng.standard_normal(n)) * (60 / np.sqrt(n))
    tone = A.sat(np.sin(2 * np.pi * np.cumsum(f) / SR) * 1.5, 1.5)
    nz = A.filt(A.noise(n, seed), "bandpass", (1200, 5000))
    env = np.clip(t / 0.04, 0, 1) * np.clip((length - t) / 0.12, 0, 1)
    return (0.3 * tone + 0.8 * nz) * env


def wheel_gun(length=0.2, seed=0):
    """A pit crew's wheel gun: a pneumatic rattle over a rising whine."""
    n = A.n_of(length)
    t = A.tl(n)
    pulses = (np.sin(2 * np.pi * 105.0 * t) > 0.85).astype(float)
    rattle = A.filt(A.noise(n, seed) * pulses, "bandpass", (700, 7000)) * 3.0
    whine = np.sin(2 * np.pi * np.cumsum(1800 + 1400 * t / length) / SR) * 0.25
    env = np.clip(t / 0.004, 0, 1) * np.clip((length - t) / 0.02, 0, 1)
    return (rattle + whine) * env


def clunk(i):
    """A start light coming on: a heavy relay, the lamp's hum."""
    n = A.n_of(0.5)
    t = A.tl(n)
    x = np.zeros(n)
    k = A.kick(f_hi=95 + 6 * i, f_lo=42, a_decay=0.18, click=0.7, length=0.5)
    x[:len(k)] += k
    x += (np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)) * np.exp(-t / 0.25) * 0.12
    c = A.click(1600 + 150 * i, 0.02, 0.003, 0.7, seed=i)
    x[:len(c)] += c * 0.8
    return x


def radio_beep(f=1250.0):
    return np.concatenate([A.blip(f, 0.06), np.zeros(A.n_of(0.03)), A.blip(f, 0.06)])


def radio_static(length, seed=0):
    n = A.n_of(length)
    t = A.tl(n)
    x = A.filt(A.noise(n, seed), "bandpass", (500, 3200)) * 0.22
    x += A.data_burst(length, 40, seed, 800, 3000, decay_out=False) * 0.35
    return x * np.clip(t / 0.05, 0, 1) * np.clip((length - t) / 0.08, 0, 1)


def chime():
    """Race control has a message."""
    out = np.zeros(A.n_of(1.7))
    a = A.bell(hz("E6"), 1.4, ratio=2.0, index=0.5, decay=0.5)
    b = A.bell(hz("B5"), 1.3, ratio=2.0, index=0.5, decay=0.5)
    out[:len(a)] += a
    i = A.n_of(0.2)
    out[i:i + len(b)] += b[:len(out) - i]
    return out


def crowd(length, seed=0):
    """A grandstand: many voices as noise, swelling and breathing."""
    n = A.n_of(length)
    t = A.tl(n)
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    for ch in range(2):
        base = A.filt(A.noise(n, seed + ch), "bandpass", (300, 2800))
        mod = np.clip(1 + 3 * A.filt(rng.standard_normal(n), "lowpass", 6), 0.25, 2.5)
        out[:, ch] = base * mod
    env = np.clip(t / 0.35, 0, 1) * np.clip((length - t) / 0.9, 0, 1)
    return out * env[:, None]


def flag_flap(length=1.8, seed=0):
    """A big flag cracking in the wind."""
    n = A.n_of(length)
    t = A.tl(n)
    am = (0.5 + 0.5 * np.sin(2 * np.pi * 7.5 * t)) ** 3
    x = A.filt(A.noise(n, seed), "bandpass", (200, 2500)) * am
    return x * np.clip(t / 0.05, 0, 1) * np.exp(-t / 1.2) * 1.5


def brass(notes, length, cutoff=3400.0, attack=0.01):
    return A.supersaw([hz(n) for n in notes], length, voices=5, detune=0.14, attack=attack, decay=0.3,
                      sustain=0.7, release=0.25, cutoff=cutoff, cut_env=1.2, cut_decay=0.2, width=0.9)


HOOK_TITLE = [(3, 1, 0, "E5", 1), (3, 2, 0, "E5", 0.5), (3, 2, 2, "D5", 0.5), (3, 3, 0, "E5", 1), (3, 4, 0, "A5", 1),
              (4, 1, 0, "G5", 1.5), (4, 2, 2, "F5", 0.5), (4, 3, 0, "E5", 1), (4, 4, 0, "C5", 1)]
HOOK_P1 = [(16, 1, 0, "F5", 1), (16, 2, 0, "F5", 0.5), (16, 2, 2, "E5", 0.5), (16, 3, 0, "F5", 1), (16, 4, 0, "A5", 1),
           (17, 1, 0, "B5", 1.5), (17, 2, 2, "A5", 0.5), (17, 3, 0, "G5", 1), (17, 4, 0, "D5", 1)]


def build():
    mix = A.Mix(DURATION, tail=1.5)
    put = mix.put
    kicks = []

    # ------------------------------------------------------------ the grid
    idle = [(0.0, 4300), (0.25, 4500), (0.4, 4200)]
    for i, tl in enumerate(T_LIGHTS):
        target = 5200 + 1300 * i
        idle += [(tl + 0.03, target + 1800), (tl + 0.16, target)]
    hold = T_LIGHTS[-1] + 0.2
    k = 0
    tb = hold
    while tb < T_OUT - 0.02:                                     # launch control: bouncing off the limiter
        idle.append((tb, 10400 + (450 if k % 2 else -350)))
        tb += 0.045
        k += 1
    launch = [(T_OUT, 10500), (T_OUT + 0.07, 8600), (T_OUT + 0.7, 12200), (T_OUT + 0.73, 10000),
              (T_OUT + 1.4, 12200), (T_OUT + 1.43, 10300), (T_OUT + 2.3, 12000), (T_OUT + 2.33, 10400),
              (T_OUT + 3.2, 11900)]
    amp = [(0.0, 0.0), (0.12, 0.45), (T_LIGHTS[0], 0.5), (T_LIGHTS[-1], 0.85), (T_OUT - 0.02, 0.95),
           (T_OUT + 0.05, 1.0), (T_OUT + 0.9, 0.8), (T_OUT + 2.0, 0.3), (T_OUT + 3.1, 0.0)]
    put("engine", car_sound(0.0, T_OUT + 3.2, idle + launch, amp, [(0, 0.0), (T_OUT + 3.2, 0.0)], seed=1), 0.0, 0.9)
    for k, dt in enumerate((0.73, 1.43, 2.33)):
        put("engine", crack(70 + k), T_OUT + dt, 0.4 - 0.08 * k)
    for i, tl in enumerate(T_LIGHTS):
        put("sfx", clunk(i), tl, 0.7 + 0.06 * i)
        put("fx", A.sub_drop(0.5, 58 + 3 * i, 34), tl, 0.25 + 0.04 * i)
    put("pad", A.pad([hz(n) for n in ["A2", "E3", "A3"]], T_OUT + 0.2, attack=1.2, release=0.1, cutoff=520), 0.0,
        0.4)
    put("fx", A.riser(T_OUT - T_LIGHTS[-1], lo=300, hi=8000, tone=0.3, f0=110, f1=880), T_LIGHTS[-1], 0.22)
    put("fx", A.reverse(A.crash(1.4, seed=2)), T_OUT - 1.4, 0.2)
    put("sfx", A.whoosh(0.5, True, 3, 400, 7000, 0.0, 0.0), T_STACKED, 0.2)
    put("sfx", A.click(700, 0.04, 0.006, 0.5, seed=15), T_OUT - 0.1, 0.5)          # the lights go out

    # ------------------------------------------------------------ lights out: the drop, the title, the lap
    put("fx", A.impact(2.4, seed=4), T_OUT, 0.5)
    put("fx", A.sub_drop(1.6, 72, 28), T_OUT, 0.55)
    put("fx", A.braam(hz("A1"), 1.6, seed=5), T_OUT, 0.3)
    put("fx", A.crash(2.2, seed=6), T_OUT, 0.22)
    put("sfx", A.whoosh(0.5, True, 7, 300, 9000, -0.2, 0.2), T_OUT - 0.02, 0.4)
    for bar, beat, six, n, d in HOOK_TITLE:
        put("lead", brass([n], d * SPB * 0.95, cutoff=4200), G.at(bar, beat, six), 0.26)
    put("lead", brass(["A3", "E4", "A4", "C5", "E5"], SPB * 1.5, cutoff=5000), T_LINE1, 0.24)
    put("sfx", A.whoosh(0.45, True, 8, 300, 8000, -0.8, 0.2), T_LINE1 - 0.05, 0.35)
    put("sfx", A.whoosh(0.45, True, 9, 300, 8000, 0.8, -0.2), T_LINE2 - 0.05, 0.35)
    put("snare", A.clap(0.4, 1400, tail=0.14, seed=10), T_AGI_BOX, 0.45)
    put("sfx", A.blip(1568, 0.08), T_AGI_BOX, 0.2)
    put("sfx", A.whoosh(0.35, True, 11, 500, 9000, 0.0, 0.0), T_LAP - 0.05, 0.3)
    put("sfx", A.flap(seed=12, lock=True), T_FLIP, 0.5)
    put("sfx", A.flap(seed=13, lock=True), T_FLIP + 0.05, 0.4)
    put("bell", A.ding(hz("E7")), T_FLIP + 0.02, 0.14)
    put("sfx", A.whoosh(0.4, False, 14, 400, 7000, 0.0, -0.8), T_BUG, 0.3)

    # ------------------------------------------------------------ the groove
    kick = A.kick(f_hi=190, f_lo=50, p_decay=0.03, a_decay=0.26, hold=0.02, drive=1.8, click=0.4, length=0.42)
    for bar in range(1, 19):
        root, voicing = chord(bar)
        t0 = G.at(bar)
        if bar in GROOVE_BARS:
            for b in range(4):
                put("kick", kick, t0 + b * SPB, 0.85)
                kicks.append(t0 + b * SPB)
                put("hats", A.hat(0.09, bright=0.9, seed=bar * 7 + b), t0 + (b + 0.5) * SPB, 0.14, p=0.25)
            # the sequencer: sixteenths on the root, jumping the octave, driving
            for s in range(16):
                mul = (2, 2, 4, 2)[s % 4]
                acc = 1.0 if s % 4 == 0 else 0.7
                put("bass", A.pluck(hz(root) * mul, 0.13, bright=1300 + 900 * acc, decay=0.04, amp_decay=0.07),
                    t0 + s * S16, 0.36 * acc)
            for b in range(4):
                n = A.n_of(SPB * 0.9)
                put("bass", A.sine(hz(root), n) * A.adsr(n, 0.004, 0.1, 0.7, 0.05, SPB * 0.8), t0 + b * SPB, 0.4)
            put("chords", A.supersaw([hz(n) for n in voicing], G.bar_len, voices=7, detune=0.2, attack=0.01,
                                     decay=0.4, sustain=0.75, release=0.1, cutoff=2400, width=1.0), t0, 0.16)
        if bar in FULL_BARS:
            for b in (1, 3):
                put("snare", A.clap(0.3, 1500, tail=0.1, seed=bar + b), t0 + b * SPB, 0.34, p=0.05)
            for s in range(16):
                if s % 2 == 1:
                    put("hats", A.hat(0.025, bright=1.1, seed=bar * 31 + s), t0 + s * S16, 0.06,
                        p=(-0.3, 0.3)[s % 4 == 1])

    # ------------------------------------------------------------ the teams: stingers, arrivals, departures
    for tc in (T_ANT, T_OAI, T_GRID2, T_XAI, T_P1, T_END):
        put("sfx", A.whoosh(0.5, True, int(tc * 10), 300, 9000, -0.9, 0.9), tc - STING + 0.05, 0.36)
        put("fx", A.crash(1.2, seed=int(tc * 7)), tc, 0.08)
    visit(put, T_ANT - 0.42, T_ANT + 0.5, T_OAI - 0.62, pan_rest=0.25, gain=0.5, seed=2)
    visit(put, T_OAI - 0.45, T_OAI + 0.45, T_GRID2 - 0.66, pan_rest=-0.2, gain=0.4, seed=3)
    visit(put, T_OAI_CAR2 - 0.4, T_OAI_CAR2 + 0.45, T_GRID2 - 0.58, pan_rest=0.3, gain=0.45, seed=4)
    visit(put, T_GRID2 - 0.42, T_GRID2 + 0.5, T_XAI - 0.62, pan_rest=-0.1, gain=0.4, seed=5)
    visit(put, T_GRID2 - 0.36, T_GRID2 + 0.56, T_XAI - 0.58, pan_rest=0.1, gain=0.4, seed=6)

    # Anthropic: the paddock talk
    put("sfx", radio_beep(), T_ANT_RADIO, 0.3, p=-0.3)
    put("sfx", radio_static(T_ANT_LINE2 + 0.95 - T_ANT_LINE1, seed=20), T_ANT_LINE1 - 0.05, 0.22, p=-0.3)
    put("sfx", radio_beep(990), T_ANT_LINE2 + 0.95, 0.25, p=-0.3)
    for k, n in enumerate(["A5", "C6", "E6"]):
        put("bell", A.bell(hz(n), 1.0, ratio=2.0, index=0.6, decay=0.4), T_ANT_LINE1 + 0.05 * k, 0.07)
    for tb in (T_ANT_BOSS, T_OAI_BOSS, T_GDM_BOSS, T_MTA_BOSS, T_XAI_BOSS):
        put("sfx", A.whoosh(0.35, True, int(tb * 13), 400, 8000, 0.6, 0.2), tb - 0.12, 0.2)
        put("sfx", A.click(2400, 0.015, 0.002, 0.3), tb + 0.2, 0.2, p=0.5)
    # OpenAI: race control
    put("bell", chime(), T_RC, 0.22)
    put("sfx", A.click(3000, 0.012, 0.002, 0.3), T_RC + 0.2, 0.15)
    # also on the grid
    put("sfx", A.blip(1175, 0.08), T_STRAP, 0.18)
    for bar in (9, 10):
        root, voicing = chord(bar)
        for s in range(16):
            n = (voicing + [voicing[1]])[[0, 2, 1, 3, 4, 2][s % 6]]
            put("lead", A.pluck(hz(n) * 2, 0.2, bright=6000, decay=0.05, amp_decay=0.1), G.at(bar) + s * S16,
                0.08, p=(-0.4, 0.4)[s % 2])

    # xAI: the pit stop
    put("sfx", radio_beep(), T_XAI - 0.3, 0.3, p=0.4)
    put("sfx", radio_static(0.7, seed=21), T_XAI - 0.02, 0.25, p=0.4)
    rpm = [(T_XAI - 0.8, 11800), (T_XAI - 0.32, 11800), (T_XAI - 0.28, 8200), (T_XAI - 0.2, 9800),
           (T_XAI - 0.12, 7000), (T_XAI - 0.06, 8400), (T_BOX, 5200), (T_BOX + 0.3, 4400), (T_LAUNCH, 4500),
           (T_LAUNCH + 0.05, 9800), (T_LAUNCH + 0.35, 12400), (T_LAUNCH + 0.38, 10000), (T_LAUNCH + 0.8, 12300)]
    amp = [(T_XAI - 0.8, 0.0), (T_XAI - 0.45, 0.7), (T_XAI - 0.2, 1.0), (T_BOX, 0.55), (T_BOX + 0.3, 0.18),
           (T_LAUNCH, 0.2), (T_LAUNCH + 0.08, 1.0), (T_LAUNCH + 0.5, 0.6), (T_LAUNCH + 0.9, 0.0)]
    pan = [(T_XAI - 0.8, -1.0), (T_BOX, 0.05), (T_LAUNCH, 0.05), (T_LAUNCH + 0.5, 1.0)]
    put("engine", car_sound(T_XAI - 0.8, T_LAUNCH + 1.0, rpm, amp, pan, seed=7), T_XAI - 0.8, 0.5)
    put("sfx", screech(0.34, seed=22), T_BOX - 0.3, 0.3, p=-0.1)
    for k, (wt, pp) in enumerate(((0.0, -0.4), (0.03, 0.4))):
        put("sfx", wheel_gun(0.16, seed=30 + k), T_OFF - 0.02 + wt, 0.4, p=pp)
        put("sfx", wheel_gun(0.2, seed=40 + k), T_ON - 0.03 + wt, 0.45, p=pp)
    put("sfx", A.swish(0.3, seed=23), T_OFF + 0.05, 0.25)
    put("sfx", A.tom(80, 0.3, seed=24), T_ON - 0.02, 0.3)
    put("sfx", A.data_burst(0.2, 150, 25, 1500, 9000, decay_out=False), T_ON, 0.14)
    put("fx", A.impact(1.0, seed=26), T_ON, 0.12)
    put("sfx", A.tom(70, 0.35, seed=27), T_JACK, 0.45)
    put("sfx", A.click(1400, 0.03, 0.004, 0.8, seed=28), T_JACK, 0.35)
    put("bell", A.bell(hz("E6"), 0.8, ratio=2.0, index=0.4, decay=0.3), T_JACK + 0.02, 0.1)
    put("sfx", screech(0.55, seed=29, f0=1500), T_LAUNCH + 0.02, 0.26, p=0.3)
    for bar in (11, 12):
        root, _ = chord(bar)
        put("bass", A.reese(hz(root), G.bar_len * 0.95, cutoff=520, lfo=0.5), G.at(bar), 0.22)

    # ------------------------------------------------------------ DevDay: the build
    put("sfx", A.whoosh(0.45, True, 90, 300, 9000, -0.9, 0.9), T_DEV - 0.3, 0.45)
    pass_by(put, T_DEV - 0.12, length=1.6, rpm=12000, v=90, d=7, seed=8, gain=0.45)
    put("fx", A.impact(1.4, seed=91), T_DEV, 0.18)
    put("sfx", A.blip(1568, 0.09), T_DEV + 0.05, 0.2)
    put("sfx", A.data_burst(0.6, 60, 92, 1200, 6000), T_DEV + 0.3, 0.08)
    for k, tl in enumerate(T_LEDS):
        put("sfx", A.blip(880 * 2 ** (k / 12), 0.05), tl, 0.13 + 0.006 * k, p=-0.6 + 0.085 * k)
    for k in range(3):
        put("sfx", A.blip(2093, 0.035), T_SHIFT + k * 0.035, 0.2)
    rpm = [(T_BUILD - 0.6, 6800), (T_BUILD, 7600), (T_SHIFT - 0.02, 12600), (T_SHIFT, 12700)]
    amp = [(T_BUILD - 0.6, 0.0), (T_BUILD, 0.35), (T_SHIFT - 0.05, 0.9), (T_SHIFT, 0.0)]
    put("engine", car_sound(T_BUILD - 0.6, T_SHIFT, rpm, amp, [(0, 0.0), (DURATION, 0.0)], seed=9), T_BUILD - 0.6,
        0.55)
    put("engine", crack(95), T_SHIFT, 0.6)
    put("fx", A.riser(T_FLAG - T_BUILD + 0.9, lo=250, hi=11000, tone=0.35, f0=110, f1=1320), T_BUILD - 0.9, 0.28)
    roll = []
    t = T_BUILD
    while t < T_SHIFT - 1e-6:
        roll.append(t)
        frac = (t - T_BUILD) / (T_FLAG - T_BUILD)
        t += SPB / (2 if frac < 0.5 else 4 if frac < 0.75 else 8)
    for k, t in enumerate(roll):
        frac = (t - T_BUILD) / (T_FLAG - T_BUILD)
        put("snare", A.snare(200 + 120 * frac, 0.18, seed=100 + k), t, 0.1 + 0.28 * frac)
    put("fx", A.reverse(A.crash(1.2, seed=99)), T_FLAG - 1.2, 0.25)
    put("pad", A.pad([hz(n) for n in GM[1]], G.bar_len, attack=0.3, release=0.2, cutoff=1800), T_BUILD, 0.3)

    # ------------------------------------------------------------ the drop: AGI?
    put("fx", A.impact(2.6, seed=110), T_FLAG, 0.55)
    put("fx", A.sub_drop(1.8, 75, 28), T_FLAG, 0.6)
    put("fx", A.crash(2.4, seed=111), T_FLAG, 0.25)
    put("fx", A.braam(hz("A1"), 1.8, seed=112), T_FLAG, 0.32)
    put("lead", brass(["A3", "E4", "A4", "C5", "E5", "A5"], G.bar_len * 0.9, cutoff=6000), T_FLAG, 0.3)
    put("sfx", flag_flap(1.9, seed=113), T_FLAG, 0.4)
    put("fx", crowd(4.2, seed=114), T_FLAG + 0.05, 0.22)
    pass_by(put, T_CROSS - 0.07, length=2.0, rpm=12100, v=90, d=6, seed=10, gain=0.6)

    # ------------------------------------------------------------ P1: up to G
    for bar, beat, six, n, d in HOOK_P1:
        put("lead", brass([n], d * SPB * 0.95, cutoff=4400), G.at(bar, beat, six), 0.24)
    for k, tr in enumerate(T_BOARD_ROWS):
        put("sfx", A.flap(seed=131 + k, lock=True), tr, 0.45, p=0.5)
        put("sfx", A.flap(seed=141 + k), tr + 0.04, 0.3, p=0.5)
    put("sfx", A.whoosh(0.5, True, 150, 300, 7000, 0.6, 0.6), T_BOARD_ROWS[0] - 0.4, 0.25)
    put("bell", A.ding(hz("E7")), T_IPO + 0.05, 0.12)
    put("fx", A.crash(2.0, seed=151), T_ON_TOP, 0.18)
    put("lead", brass(["G3", "D4", "G4", "B4", "D5"], G.bar_len * 0.9, cutoff=4200), T_ON_TOP, 0.2)
    for k, n in enumerate(["D6", "G6", "B6", "D7"]):
        put("bell", A.bell(hz(n), 1.3, ratio=2.0, index=0.6, decay=0.5), T_ON_TOP + 0.05 * k, 0.09, p=-0.4 + 0.27 * k)

    # ------------------------------------------------------------ the end: C major, and a car fading away
    final = ["C2", "G2", "C3", "E3", "G3", "C4", "E4", "G4"]
    put("piano", sum(A.piano(hz(n), 3.4, vel=0.8) for n in final) * 0.3, T_END, 0.7)
    put("pad", A.pad([hz(n) for n in ["C3", "G3", "C4", "E4", "G4"]], 3.2, attack=0.05, release=1.2, cutoff=2600),
        T_END, 0.45)
    put("lead", brass(["C4", "G4", "C5", "E5", "G5"], SPB * 2, cutoff=4400), T_END, 0.22)
    put("fx", A.sub_drop(1.4, 65, 30), T_END, 0.4)
    put("snare", A.clap(0.4, 1300, tail=0.2, seed=160), T_END + SPB, 0.4)
    pass_by(put, T_END + 1.6, length=3.0, rpm=11400, v=70, d=40, seed=11, gain=0.35)
    for k, n in enumerate(["G6", "C7", "E7", "G7", "C8"]):
        put("bell", A.bell(hz(n), 1.4, ratio=2.0, index=0.5, decay=0.5), T_END + 0.08 + 0.06 * k, 0.08)
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
    out += g("lead") + A.delay(g("lead"), SPB * 0.75, 0.3) * 0.16 + A.reverb(g("lead"), t60=2.2, seed=4) * 0.28
    out += g("pad") + A.reverb(g("pad"), t60=3.0, seed=5) * 0.35
    out += g("piano") + A.reverb(g("piano"), t60=2.8, seed=6) * 0.4
    bell = g("bell")
    out += bell + A.delay(bell, SPB * 0.75, 0.35) * 0.2 + A.reverb(bell, t60=2.6, seed=7) * 0.4
    # the build closes the music behind a low-pass until the drop opens it
    t = np.arange(n) / SR
    sweep = np.clip((t - T_DEV) / (T_FLAG - T_DEV), 0, 1) * (t < T_FLAG)
    if sweep.max() > 0:
        low = A.filt(out, "lowpass", 700)
        m = (sweep ** 1.5)[:, None] * 0.7
        out = out * (1 - m) + low * m
    out += g("fx")
    eng = A.filt(g("engine"), "highpass", 60)
    out += eng * 0.9 + A.reverb(eng, t60=1.1, seed=9) * 0.12
    sfx = A.filt(g("sfx"), "highpass", 80)
    out += sfx * 1.1 + A.reverb(sfx, t60=0.8, seed=8) * 0.12
    return A.master(out, target=-11.0, ceiling=-1.0)


def render(path):
    mix, kicks = build()
    x = process(mix, kicks)[:A.n_of(DURATION)]
    A.write_wav(path, x)
    return x
