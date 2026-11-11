"""Film timeline shared by the animation and the soundtrack.

120 BPM at 24 fps: 1 beat = 0.5 s = 12 frames, 1 bar = 2 s = 48 frames.
All times in seconds from the first frame.  Total 40 s = 20 bars = 960 frames.
"""
FPS = 24
BPM = 120
BEAT = 60.0 / BPM          # 0.5 s
BAR = 4 * BEAT             # 2.0 s
DURATION = 40.0
FRAMES = int(DURATION * FPS)


def frame(t):
    """Seconds -> frame number (frame 1 = t 0)."""
    return int(round(t * FPS)) + 1


# name, start, end, description
SECTIONS = [
    ("intro",     0.0,  2.0, "black, dark showroom fades up, a single light sweep, low drone"),
    ("assembly",  2.0, 12.0, "parts fly in and lock onto the carbon chassis, one hit per part"),
    ("exterior", 12.0, 24.0, "three beauty shots: front 3/4 push-in, side tracking, rear 3/4 crane"),
    ("details",  24.0, 28.0, "macro: wheel + brake, then horseshoe grille"),
    ("interior", 28.0, 36.0, "doors swing up, camera glides into the cabin, cabin lights come on"),
    ("finale",   36.0, 40.0, "doors close, wide hero shot, lights pulse, fade to black"),
]

# (time, strength 0..1, label) — mechanical 'lock' accents the music must land on
HITS = [
    (2.0, 0.50, "chassis revealed"),
    (3.0, 0.60, "powertrain drops in"),
    (4.0, 0.55, "front wheels"),
    (4.5, 0.55, "rear wheels"),
    (5.0, 0.45, "seats"),
    (5.5, 0.45, "dashboard"),
    (6.5, 0.70, "rear clamshell"),
    (7.5, 0.70, "front clamshell"),
    (8.5, 0.65, "doors"),
    (9.5, 0.60, "roof and glass"),
    (10.5, 0.60, "wing and light bar"),
    (11.5, 0.40, "final latch"),
    (12.0, 1.00, "LIGHTS ON — main theme enters"),
    (16.0, 0.50, "cut to side profile"),
    (20.0, 0.60, "cut to rear, tail light bar sweeps on"),
    (24.0, 0.50, "cut to wheel macro"),
    (26.0, 0.50, "cut to grille macro"),
    (28.0, 0.70, "doors begin to rise"),
    (32.0, 0.50, "inside the cabin, ambient lights on"),
    (36.0, 0.80, "finale wide shot"),
    (38.0, 0.60, "lights pulse"),
    (39.0, 0.30, "fade"),
]

# camera shots: name, start, end
SHOTS = [
    ("s01_reveal",        0.0,  2.0),
    ("s02_assembly_orbit", 2.0, 8.0),
    ("s03_assembly_close", 8.0, 12.0),
    ("s04_front34",      12.0, 16.0),
    ("s05_side_track",   16.0, 20.0),
    ("s06_rear34",       20.0, 24.0),
    ("s07_wheel_macro",  24.0, 26.0),
    ("s08_grille_macro", 26.0, 28.0),
    ("s09_doors_open",   28.0, 32.0),
    ("s10_cabin_wheel",  32.0, 34.0),
    ("s11_cabin_console", 34.0, 36.0),
    ("s12_finale",       36.0, 40.0),
]
