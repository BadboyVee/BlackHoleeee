"""INTERFACE: the timing sheet for a square UI reel. 120 BPM, 12 bars.

A camera travels over a board of components. You pick Fable 5.1, type a prompt, and the model streams its
answer: it thinks, plans, writes code, renders the film and hands it to a player. Then the board goes dark,
tilts back into an overview of everything the cursor touched, and ships. Every click lands on the grid.
"""
from engine.core import Grid

BPM = 120
G = Grid(BPM)            # a beat is 0.5 s (30 frames), a bar 2 s
BARS = 12
DURATION = 25.0
SIZE = (1440, 1440)
CX, CY = 720, 720

# ---------------------------------------------------------------- 1 model picker
T_PICKER_IN = 0.08
T_PICK = [G.at(1, 3), G.at(1, 4)]          # click Gemini 3.8, then Fable 5.1
T_CARD = 1.62                              # Fable's model card drops in

# ---------------------------------------------------------------- 2 composer
T_TO_COMPOSER = G.at(2)                    # 2.0, camera whip
T_TYPE = (2.32, 3.3)
PROMPT = ["make a motion film about the three", "frontier models, every frame in code"]
T_CHIPS = [3.34, 3.44, 3.54, 3.64]
T_SEND = G.at(2, 4, 2)                     # 3.75

# ---------------------------------------------------------------- 3 Fable 5.1 answers
T_RESP = 3.84                              # the answer card opens
T_THINK = (4.0, 5.3)
T_THINK_LINES = [4.12, 4.46, 4.8]
T_THOUGHT = 5.3                            # "Thought for 12s"
T_PROSE = (5.46, 6.94)
T_LIST = [7.0, 7.18, 7.36]
T_CODE = 7.62                              # the code block opens
T_CODE_LINES = [7.8, 8.0, 8.2, 8.4]
T_COPY = 8.62                              # click Copy on the code block
T_TOOL = 8.74                              # tool call: render the film
T_PROG = (8.9, 10.04)
T_DONE = 10.08
T_TOAST = (10.14, 12.5)
T_OPEN = G.at(6, 2)                        # 10.5, click "Open"

# ---------------------------------------------------------------- 4 player
T_TO_PLAYER = 10.56
T_PLAY = G.at(6, 3)                        # 11.0
T_GRAB, T_DROP = G.at(7, 1, 2), G.at(7, 2, 2)   # scrub 12.25 -> 12.75
FILM_AT_PLAY = 2.2                         # seconds into THE FRONTIER when play is pressed
FILM_AT_DROP = 12.62                       # where the scrub lets go: just before the FABLE drop

# ---------------------------------------------------------------- 5 settings, dark mode
T_TO_SETTINGS = 13.2
T_TOG = [13.75, G.at(8)]                   # film grain on; dark mode on at 14.0
T_WIPE = G.at(8)
WIPE_LEN = 0.62
T_SLIDE = (14.75, 15.25)

# ---------------------------------------------------------------- 6 stats
T_TO_STATS = 15.5
T_SWITCH = [G.at(9), G.at(9, 2, 2)]        # Tribute at 16.0, Interface at 16.75
T_HOVER = (17.1, 17.72)

# ---------------------------------------------------------------- 7 overview
T_OVER = G.at(10)                          # 18.0, the drop: pull back and tilt
T_PATH = (18.36, 20.3)                     # the cursor's path draws across the board
T_FLY = 20.9                               # fly down to the palette

# ---------------------------------------------------------------- 8 palette, end
T_CMDK = 21.44
T_KEYS = [21.58, 21.68, 21.78, 21.88]      # "ship"
T_ENTER = G.at(12)                         # 22.0
END = (22.06, DURATION)
T_LOGOS = [22.58, 22.72, 22.86]
T_CREDIT = 23.1
T_FADE = (24.3, DURATION)

WHIPS = [T_TO_COMPOSER, T_TO_PLAYER, T_TO_SETTINGS, T_TO_STATS, T_FLY]
