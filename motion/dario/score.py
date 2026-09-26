"""DARIO AMODEI, a tribute: one timing sheet for the music and the pictures.

120 BPM: a beat is 0.5 s (30 frames), a bar 2 s.
"""
import numpy as np

from engine.core import Grid

BPM = 120
G = Grid(BPM)
BARS = 16
DURATION = 32.8

T_PHYS = G.at(3)      # 01 PHYSICS
T_SAFE = G.at(5)      # 02 SAFETY
T_SCALE = G.at(7)     # 03 SCALE
T_ANTH = G.at(9)      # 04 ANTHROPIC
T_GRACE = G.at(11)    # 05 MACHINES OF LOVING GRACE
T_CENTURY = G.at(12, 2)
T_DOMAINS = G.at(13)
T_FIN = G.at(14)      # 06 DARIO AMODEI
T_LAST = G.at(16)
BREATH = 0.12

CHORD_OF_BAR = {3: "Bm", 4: "G", 5: "D", 6: "A", 7: "Bm", 8: "G", 9: "D", 10: "A",
                11: "Bm", 12: "G", 13: "D", 14: "G", 15: "A", 16: "D"}


def beats(bar0, bar1, every=1.0, offset=0.0):
    out, b, total = [], 0.0, (bar1 - bar0) * 4
    while b < total - 1e-9:
        out.append(G.at(bar0) + (b + offset) * G.spb)
        b += every
    return out


KICKS = beats(5, 7, 2.0) + beats(7, 16) + [T_LAST]
KICKS = sorted(t for t in KICKS if not (T_GRACE - BREATH <= t < T_GRACE) and not (T_FIN - BREATH <= t < T_FIN))
CLAPS = beats(9, 11, 2.0, 1.0) + beats(11, 16, 2.0, 1.0)

# neuron spikes: random in bar 1, pulled onto the sixteenth-note grid through bar 2
_r = np.random.default_rng(1)
SPIKES = []
t = 0.25
while t < G.at(2):
    SPIKES.append(t)
    t += _r.exponential(0.16)
for k in range(16):
    tt = G.at(2) + k * G.spb / 4
    if k in (0, 3, 6, 8, 10, 11, 12, 13, 14, 15) and tt < T_PHYS - 0.2:
        SPIKES.append(tt)
SPIKES = sorted(SPIKES)
