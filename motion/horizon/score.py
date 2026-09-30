"""HORIZON: the timing sheet. The soundtrack is the reference spot's own (112.5 BPM, a beat every 0.5333 s from
0.34 s), and the film cuts where it cuts: a line drawn on white (The frontier moves every week.), black bands
(Stay ahead of what's next.), Introducing, the mark, Your AI-race intelligence, a chart and a curve, a laptop on
green hills, the Frontier Index, Scout on a phone in a meadow (what's coming this week?), Radar (your early-warning
engine: watches, spots, alerts; a new launch spotted), the sea at sunset, and the mark."""

DURATION = 53.0
SIZE = (1920, 1080)
CX, CY = 960, 540
B0, BEAT = 0.34, 60.0 / 112.5


def beat(k):
    return B0 + BEAT * k


# 1 the line, on white
T_STROKE = (0.20, 2.30)                     # the pen draws, then the line settles into a horizon
T_WORDS = [beat(4), beat(4.35), beat(4.7), beat(5.05), beat(5.4)]   # The frontier / moves / every / week.
T_BANDS = 3.78                              # black bands sweep in...
T_INTRO = beat(8) - 0.04                    # ...4.57: Introducing
T_BARS = 6.05                               # bars rise as it blurs away
T_GRID = beat(12)                           # 6.74: the grid, the mark
T_TAG = beat(16)                            # 8.87: Your AI-race intelligence...
T_TAG_SET = beat(18)                        # ...9.94: settled, for builders
T_CHART = beat(20)                          # 11.01: a chart draws
T_CURVE = beat(22)                          # 12.07: the curve sweeps up

# 2 Scout
T_LAPTOP = beat(24)                         # 13.14: a laptop on the hills
T_PUSH = beat(27)                           # 14.74: into its screen
T_INDEX = beat(28)                          # 15.27: the Frontier Index
T_SCOUT = beat(30)                          # 16.34: Scout
T_PHONE = beat(32)                          # 17.41: the phone slides in
T_ASK = beat(33)                            # 17.94: what's coming this week?
T_THINK = beat(34)                          # 18.47: thinking
T_READ = beat(36)                           # 19.54: the read
T_MEADOW = beat(40)                         # 21.67: the phone in a meadow
T_CLOSE = beat(43)                          # 23.27: close on the read

# 3 Radar
T_EYE = beat(48)                            # 25.94: RADAR
T_ENGINE = beat(50)                         # 27.01: your early-warning engine
T_HILLS = beat(52)                          # 28.07: the hills; watches, spots, alerts
T_VERBS = [beat(53), beat(55), beat(57)]
T_ICON = beat(58)                           # 31.27: the icon
T_SEARCH = beat(61)                         # 32.87: searching
T_CARD = beat(64)                           # 34.47: new launch spotted
T_SUNSET = beat(70)                         # 37.67: the sea at sunset
T_CROSS = beat(72)                          # 38.74: stay ahead of the race

# 4 the end
T_POCKET = beat(74)                         # 39.81: right / from your...
T_POCKET_IMG = beat(76)                     # 40.87: ...pocket
T_NAME = beat(80)                           # 43.01: Horizon
T_MARK = beat(84)                           # 45.14: the mark over the hills
T_BLACK = beat(88)                          # 47.27: the mark on black
T_NOTE = beat(92)                           # 49.41: the small print
