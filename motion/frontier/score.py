"""THE FRONTIER: one timing sheet shared by the music and the pictures.

150 BPM, so a beat is 0.4 s (24 frames) and a sixteenth is 0.1 s (6 frames).
"""
from engine.core import Grid

BPM = 150
G = Grid(BPM)
BARS = 16
DURATION = 26.4          # 16 bars plus a held last chord

T_DROP_A = G.at(3)       # ASTRA 6
T_DROP_B = G.at(6)       # GEMINI 3.8
T_DROP_C = G.at(9)       # FABLE 5.1
T_CLASH = G.at(12)
T_BUILD = G.at(13)
T_FINALE = G.at(14)
T_LAST = G.at(16)
BREATH = 0.15            # silence before each big downbeat

WORDS = [                # the cold open, one word per beat
    (G.at(1, 1), "THREE"), (G.at(1, 2), "LABS."), (G.at(1, 3), "THREE"), (G.at(1, 4), "MINDS."),
    (G.at(2, 1), "ONE"), (G.at(2, 2), "FRONTIER."),
]


def beats(bar0, bar1, every=1.0, offset=0.0):
    """Times of every `every` beats from the start of bar0 up to the start of bar1."""
    out = []
    b = 0.0
    total = (bar1 - bar0) * 4
    while b < total - 1e-9:
        out.append(G.at(bar0) + (b + offset) * G.spb)
        b += every
    return out


KICKS = beats(3, 12) + beats(12, 13) + beats(13, 14, 0.5)[:4] + beats(13, 14, 0.25)[8:] + beats(14, 16)
KICKS = sorted(t for t in KICKS if t < T_FINALE - BREATH or t >= T_FINALE)
CLAPS = beats(3, 13, 2.0, 1.0) + beats(14, 16, 2.0, 1.0)
STABS_CLASH = [(G.at(12, b), ch) for b, ch in zip((1, 2, 3, 4), ("Fm", "Db", "Eb", "C"))]
IMPACTS = [T_DROP_A, T_DROP_B, T_DROP_C, T_CLASH, T_FINALE, T_LAST]
