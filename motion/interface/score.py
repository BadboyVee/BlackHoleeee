"""INTERFACE: timing for a square UI micro-interaction reel. 120 BPM, 8 bars, every click on the grid."""
from engine.core import Grid

BPM = 120
G = Grid(BPM)
BARS = 8
DURATION = 16.4
SIZE = (1440, 1440)
CX, CY = 720, 720

# scene windows (in, out)
PICKER = (0.05, 1.7)
COMPOSER = (2.0, 3.6)
MORPH = (3.55, 6.0)
PLAYER = (6.0, 7.8)
SETTINGS = (8.0, 9.8)
STATS = (10.0, 11.8)
PALETTE = (12.0, 13.75)
END = (13.7, DURATION)

T_PICK = G.at(1, 3)          # click Fable 5.1
T_TYPE = (2.25, 3.15)        # prompt typing
PROMPT = "make a dynamic 15-second motion graphics video about the frontier"
T_CHIPS = [3.15, 3.25, 3.35]
T_GEN = G.at(2, 4)           # click Generate
T_CIRCLE = 4.0
T_SPIN = (4.2, 4.9)
T_EXPAND = 4.9
T_COUNT = (5.0, 5.85)
T_DONE = 5.85
T_PLAY = G.at(4, 2)          # 6.5
T_GRAB, T_DROP = G.at(4, 3), G.at(4, 4)   # scrub 7.0 -> 7.5
T_TOG = [G.at(5, 2), G.at(5, 3)]           # 8.5, 9.0
T_SLIDE = (9.25, 9.75)
T_SWITCH = G.at(6, 2)        # 10.5
T_HOVER = (11.0, 11.6)
T_KEYS = [12.3, 12.4, 12.5, 12.6]           # "ship"
T_ENTER = G.at(7, 4)         # 13.5

# the cursor, as (time, x, y); clicks happen where it rests
CURSOR = [
    (0.0, 1210, 1260), (0.85, 1010, 736), (1.25, 1010, 736), (1.7, 1060, 820),
    (2.9, 1150, 1030), (3.35, 1116, 866), (3.62, 1116, 866), (4.1, 1180, 1010), (5.9, 1080, 1060),
    (6.35, 962, 862), (6.62, 962, 862), (6.95, 732, 712), (7.0, 732, 712), (7.5, 1018, 712), (7.9, 1110, 900),
    (8.35, 1082, 652), (8.6, 1082, 652), (8.88, 1082, 742), (9.1, 1082, 742), (9.2, 603, 904), (9.25, 603, 904),
    (9.75, 1110, 904), (10.05, 1150, 1000),
    (10.38, 600, 440), (10.62, 600, 440), (11.0, 942, 836), (11.6, 942, 836), (11.9, 1100, 1060),
    (12.2, 1040, 1080), (13.4, 1000, 1000), (14.0, 1010, 960), (16.4, 1030, 980),
]
CLICKS = [T_PICK, T_GEN, T_PLAY, T_GRAB, T_TOG[0], T_TOG[1], T_SLIDE[0], T_SWITCH]
