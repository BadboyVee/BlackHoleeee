"""INTERFACE soundtrack: a light 120 BPM groove in E major under a UI foley track.

Every interaction on screen has a sound on the grid: mouse clicks, keystrokes, toggle clacks, the slider's
ratchet, the render counter's chatter and a chime when a job finishes.
"""
import numpy as np

from engine import audio as A
from engine.audio import hz
from .score import (G, DURATION, CLICKS, T_PICK, T_TYPE, PROMPT, T_CHIPS, T_GEN, T_CIRCLE, T_SPIN, T_EXPAND,
                    T_COUNT, T_DONE, T_PLAY, T_GRAB, T_DROP, T_TOG, T_SLIDE, T_SWITCH, T_HOVER, T_KEYS, T_ENTER,
                    PICKER, COMPOSER, PLAYER, SETTINGS, STATS, PALETTE, END)

S16 = G.spb / 4
CHORDS = [["E3", "G#3", "B3", "D#4"], ["C#3", "E3", "G#3", "B3"], ["A2", "C#3", "E3", "G#3"], ["B2", "D#3", "F#3", "A3"]]


def beats(bar0, bar1, every=1.0, offset=0.0):
    out, b = [], 0.0
    while b < (bar1 - bar0) * 4 - 1e-9:
        out.append(G.at(bar0) + (b + offset) * G.spb)
        b += every
    return out


def build():
    mix = A.Mix(DURATION, tail=1.0)
    put = mix.put
    rng = np.random.default_rng(3)

    # groove
    kick = A.kick(f_hi=160, f_lo=52, p_decay=0.04, a_decay=0.28, drive=1.3, click=0.45, length=0.45)
    kicks = beats(1, 9, 2.0) + beats(3, 7, 2.0, 1.5)
    kicks = sorted(t for t in kicks if t < 15.0)
    for t in kicks:
        put("kick", kick, t, 0.75)
    for t in beats(1, 8, 2.0, 1.0):
        put("rim", A.rim(), t, 0.45, p=0.1)
        put("rim", A.clap(0.3, 1500, tail=0.08, seed=int(t * 7)), t, 0.18)
    for t in beats(2, 8, 0.25):
        k = round(t / S16) % 4
        put("hats", A.hat(0.02, seed=int(t * 100) % 83), t, (0.1, 0.05, 0.16, 0.06)[k], p=0.35)
    # the click beat: an eleven-over-thirty-two euclid of tiny digital ticks
    pat = [((i * 11) % 32) < 11 for i in range(32)]
    for bar in range(2, 8):
        for s, on in enumerate(pat):
            if on:
                put("clicks", A.click((9500, 7000, 12000, 8000)[s % 4], 0.008, 0.0009, 0.1), G.at(bar) + s * S16 / 2,
                    0.22, p=(-0.6, 0.6)[s % 2])
    for bar in range(1, 9):
        ch = CHORDS[(bar - 1) % 4]
        for k in (0, 1.5, 3):
            for n in ch:
                put("keys", A.epiano(hz(n), 1.2, vel=0.55, decay=0.9), G.at(bar) + k * G.spb, 0.11, p=float(rng.uniform(-0.3, 0.3)))
        root = hz(ch[0]) / 2
        for k in (0, 2.5):
            n = A.n_of(0.4)
            put("bass", A.sine(root, n) * A.adsr(n, 0.005, 0.2, 0.7, 0.08, 0.32), G.at(bar) + k * G.spb, 0.5)
    for k, n in enumerate(["B5", "G#5", "E5", "F#5", "G#5", "B5", "C#6", "B5"]):
        put("pluck", A.pluck(hz(n), 0.4, bright=3500, decay=0.06, amp_decay=0.2, wave="square"), G.at(3 + k // 2, 1 + 2 * (k % 2)), 0.1, p=0.3)

    # ------------------------------------------------------------ foley
    for win in (PICKER, COMPOSER, PLAYER, SETTINGS, STATS, PALETTE):
        put("sfx", A.whoosh(0.35, True, int(win[0] * 10), 400, 6000, -0.3, 0.3), win[0] - 0.05, 0.16)
    for t in CLICKS:
        put("sfx", A.click(2600, 0.018, 0.0025, 0.5), t, 0.55)
        put("sfx", A.blip(180, 0.03), t, 0.25)
    n = len(PROMPT)
    for k in range(n):
        t = T_TYPE[0] + k * (T_TYPE[1] - T_TYPE[0]) / n
        put("sfx", A.key(seed=900 + k), t, 0.28, p=float(rng.uniform(-0.3, 0.3)))
    for k, t in enumerate(T_CHIPS):
        put("sfx", A.blip(1320 * 2 ** (k * 4 / 12), 0.06), t, 0.2)
    put("sfx", A.whoosh(0.45, False, 77, 300, 5000, 0.5, 0.0), T_GEN + 0.05, 0.3)
    for k in range(10):
        put("sfx", A.click(5000, 0.008, 0.0008), T_SPIN[0] + k * 0.07, 0.12 + 0.02 * (k % 3), p=0.2 * np.sin(k))
    put("sfx", A.whoosh(0.3, True, 78, 300, 6000, -0.6, 0.6), T_EXPAND, 0.25)
    put("sfx", A.data_burst(T_COUNT[1] - T_COUNT[0], 70, 79, 2000, 7000, decay_out=False), T_COUNT[0], 0.18)
    for f, dt in ((hz("E6"), 0.0), (hz("B6"), 0.09)):
        put("sfx", A.bell(f, 1.2, ratio=2.0, index=0.6, decay=0.5), T_DONE + dt, 0.2)
    put("sfx", A.swish(0.45, seed=80), T_GRAB, 0.3)
    for t, k in zip(T_TOG, range(2)):
        put("sfx", A.flap(seed=81 + k, lock=True), t + 0.02, 0.4)
    for k in range(12):
        put("sfx", A.click(3500 + 200 * k, 0.008, 0.0009), T_SLIDE[0] + k * (T_SLIDE[1] - T_SLIDE[0]) / 12, 0.2, p=-0.6 + 0.1 * k)
    put("sfx", A.data_burst(0.5, 90, 82), T_SWITCH + 0.05, 0.2)
    put("sfx", A.blip(1760, 0.08), T_HOVER[0], 0.15)
    for k, t in enumerate(T_KEYS):
        put("sfx", A.key(seed=950 + k), t, 0.4)
    put("sfx", A.click(2000, 0.03, 0.004, 0.4), T_ENTER, 0.55)
    put("sfx", A.whoosh(0.4, False, 83, 300, 5000, 0.0, 0.0), T_ENTER + 0.1, 0.25)
    for f, dt in ((hz("E6"), 0.0), (hz("G#6"), 0.08), (hz("B6"), 0.16)):
        put("sfx", A.bell(f, 1.6, ratio=2.0, index=0.6, decay=0.6), END[0] + 0.25 + dt, 0.18)
    put("keys", A.pad([hz("E3"), hz("B3"), hz("E4"), hz("G#4")], 2.6, attack=0.05, release=1.2, cutoff=2200), G.at(8), 0.4)
    return mix


def process(mix):
    b = mix.buses
    n = mix.n
    kicks = [t for t in beats(1, 9, 2.0) + beats(3, 7, 2.0, 1.5)]
    side = A.duck(n, kicks, depth=0.45, release=0.16)
    out = b["kick"] * 0.8 + b["rim"] + A.reverb(b["rim"], t60=1.0, seed=2) * 0.3 + b["hats"] * 0.8
    out += A.filt(b["clicks"], "highpass", 3000) * 1.2
    keys = b["keys"] + A.reverb(b["keys"], t60=2.0, seed=4) * 0.45
    out += keys * side[:, None] * 1.3
    out += b["bass"] * side[:, None]
    out += b["pluck"] + A.delay(b["pluck"], G.spb * 0.75, 0.4) * 0.4
    sfx = A.filt(b["sfx"], "highpass", 60)
    out += sfx * 1.4 + A.reverb(sfx, t60=0.9, seed=5) * 0.2
    return A.master(out, target=-13.0, ceiling=-1.0)


def render(path):
    x = process(build())[:A.n_of(DURATION)]
    A.write_wav(path, x)
    return x
