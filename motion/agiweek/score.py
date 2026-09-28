"""AGI WEEK, cut as THE RACE TO AGI: the timing sheet for a 16:9 race broadcast about the last week of September
2026. 128 BPM, 18 bars.

Five labs sit on the start-light gantry, a light each, the model over the company. Lights out on the drop: another
week closer to AGI, and the lap counter (the week of the year) ticks from 39 to 40. Then each team in turn:
Anthropic on the radio (Sonnet 5.5 expected today), OpenAI with two new entries (a new model and Agent "O"),
Gemini and Muse also on the grid, xAI in the pits (4.7 off, 4.8 might go on this week). DevDay is up next,
tomorrow, the anticipation maxes out, the chequered flag asks "AGI?", Anthropic takes P1 with the pit board
reading IPO: NOV, and it's a big week ahead.
"""
from engine.core import Grid

BPM = 128
G = Grid(BPM)            # a beat is 0.46875 s, a bar 1.875 s
DURATION = 35.25
SIZE = (1920, 1080)
CX, CY = 960, 540

# ---------------------------------------------------------------- 1 the gantry: five lights, five labs
LIGHT_ORDER = ["meta", "google", "xai", "openai", "anthropic"]        # left to right; Anthropic's is the last
T_LIGHTS = [G.at(1, 2), G.at(1, 3), G.at(1, 4), G.at(2, 1), G.at(2, 2)]
T_CAPTION = 0.12                         # "THE FINAL WEEK OF SEPTEMBER"
T_STACKED = G.at(2, 3)                   # "IS LOOKING STACKED."
T_OUT = G.at(3)                          # 3.75, lights out

# ---------------------------------------------------------------- 2 the title and the lap
T_LINE1 = T_OUT                          # ANOTHER WEEK
T_LINE2 = G.at(3, 3)                     # CLOSER TO AGI.
T_AGI_BOX = G.at(3, 4)
T_LAP = G.at(4, 1)                       # LAP 39/???
T_FLIP = G.at(4, 2)                      # 39 -> 40: week 40 of the year
T_BUG = G.at(4, 4)                       # the counter flies to the corner and stays there

# ---------------------------------------------------------------- 3 Anthropic: team radio
T_ANT = G.at(5)                          # 7.5
T_ANT_RADIO = G.at(5, 3)
T_ANT_LINE1 = G.at(5, 3, 2)              # "SONNET 5.5 EXPECTED TODAY."
T_ANT_BOSS = G.at(6, 1)
T_ANT_LINE2 = G.at(6, 2)                 # "BIG STEP UP. A FABLE MOMENT?"

# ---------------------------------------------------------------- 4 OpenAI: two new entries
T_OAI = G.at(7)                          # 11.25
T_OAI_CAR2 = G.at(7, 2)                  # Agent "O" rolls in
T_OAI_BOSS = G.at(8, 1)
T_RC = G.at(8, 3)                        # race control: DevDay tomorrow

# ---------------------------------------------------------------- 5 also on the grid: Gemini, Muse
T_GRID2 = G.at(9)                        # 15.0
T_STRAP = G.at(9, 2)
T_GDM_BOSS = G.at(9, 4)
T_MTA_BOSS = G.at(10, 1)

# ---------------------------------------------------------------- 6 xAI in the pits: 4.7 off, 4.8 on?
T_XAI = G.at(11)                         # 18.75
T_BOX = T_XAI + 0.24                     # the car stops in its box
T_OFF = G.at(11, 2)                      # the 4.7s come off
T_ON = G.at(11, 3)                       # the 4.8s go on
T_JACK = G.at(12, 1, 2)                  # jack down, the clock stops
T_XAI_BOSS = G.at(12, 1)
T_LAUNCH = G.at(12, 4)

# ---------------------------------------------------------------- 7 up next: DevDay, tomorrow
T_DEV = G.at(13)                         # 22.5
T_BUILD = G.at(14)                       # 24.375: the shift lights fill
T_LEDS = [T_BUILD + i * G.spb / 4 for i in range(15)]   # one a sixteenth, the sixteenth sixteenth is the shift
T_SHIFT = T_BUILD + 15 * G.spb / 4

# ---------------------------------------------------------------- 8 the drop: AGI?
T_FLAG = G.at(15)                        # 26.25
T_CROSS = G.at(15, 4)                    # Anthropic crosses the line

# ---------------------------------------------------------------- 9 P1: staying on top, IPO in November
T_P1 = G.at(16)                          # 28.125
T_BOARD = G.at(16, 3)
T_BOARD_ROWS = [G.at(16, 3, 1), G.at(16, 3, 3), G.at(16, 4, 1), G.at(16, 4, 3)]
T_IPO = G.at(16, 4)
T_ON_TOP = G.at(17, 1)

# ---------------------------------------------------------------- 10 end: big week ahead
T_END = G.at(18)                         # 31.875
T_FADE = (34.45, DURATION)

STING = 0.5                              # a stinger starts this long before the downbeat it lands on
CUTS = [T_OUT, T_ANT, T_OAI, T_GRID2, T_XAI, T_DEV, T_FLAG, T_P1, T_END]
