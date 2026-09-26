"""ARNAUD'S: the timing sheet for a 16:9 AI-concierge spot in the style of a UI ad. 120 BPM, 13 bars.

A chandelier of light turns into the name. On a phone you ask for pizza, sushi or ramen but want
something special; the assistant thinks, flips through the usual cravings, and books a table at
Arnaud's in the French Quarter instead. A map, a confirmation, and the name again.
"""
from engine.core import Grid

BPM = 120
G = Grid(BPM)            # a beat is 0.5 s, a bar 2 s
DURATION = 25.5
SIZE = (1920, 1080)
CX, CY = 960, 540

# ---------------------------------------------------------------- 1 intro: a chandelier becomes the name
T_LINES = (0.05, 1.2)                    # the chandelier draws itself
T_BULBS = [G.at(1, 1, s) for s in range(2, 12)]   # a tier of lights on every sixteenth, 0.25 -> 1.375
T_MORPH = (1.5, 2.25)                    # the lights fly into the letters
T_NAME = G.at(2)                         # 2.0, the name lands on the bar
T_INK = (2.1, 2.7)
T_TAG = 2.75                             # EST. 1918 · NEW ORLEANS
T_SWEEP = 3.05
T_WIPE = (3.62, 4.08)                    # the caret wipes to the phone

# ---------------------------------------------------------------- 2 the ask
T_PHONE = 3.9
T_TYPE = (4.32, 6.05)
PROMPT = "It’s our anniversary tonight. Pizza, sushi or ramen? I want something special."
T_SEND = 6.12                            # the send button, just before the words take over

# ---------------------------------------------------------------- 3 giant words
T_GIANT = 6.2                            # the caret swells to fill the frame
WORDS = [(G.at(4, 1, 2), "Pizza,", "pizza"), (G.at(4, 2, 2), "sushi,", "sushi"), (G.at(4, 3, 2), "ramen?", "ramen"),
         (G.at(4, 4), "something", None), (G.at(4, 4, 2), "special.", "glow")]

# ---------------------------------------------------------------- 4 finding
T_FIND = G.at(5)                         # 8.0
T_DROPS = [G.at(5, 2), G.at(5, 3), G.at(5, 4)]   # pizza, sushi, ramen fall into the bowl
T_RISE = G.at(5, 4, 2)                   # a spark rises out of it

# ---------------------------------------------------------------- 5 carousel
T_LIME = G.at(6)                         # 10.0, the lime panel opens
T_CARDS = 10.2
T_PICK = G.at(6, 3)                      # 11.0, Arnaud's lifts out of the row
T_FULL = G.at(6, 3, 2)                   # 11.25, its card opens to the whole frame: the dining room
T_TO_CHAT = G.at(7, 1, 1)                # 12.125

# ---------------------------------------------------------------- 6 chat
T_CHAT = G.at(7, 1, 2)                   # 12.25
T_MSG = [12.5, 12.95, 13.45, 14.05, 14.4, 14.85, 15.1]   # user, reply, card, dishes line, dish chips, question, buttons
T_TAP = G.at(8, 4)                       # 15.5, tap "Book the table"

# ---------------------------------------------------------------- 7 map
T_MAP = G.at(9)                          # 16.0
T_ROUTE = (16.5, 18.0)
T_CONFIRM = G.at(10)                     # 18.0
T_GO = (17.2, 19.8)                      # the dot travels the route

# ---------------------------------------------------------------- 8 kinetic words
T_CRAVE = G.at(11)                       # 20.0
T_ROLL = [20.5, 20.75, 21.0]             # pizza -> sushi -> ramen -> something special
T_WAIT = G.at(11, 3, 2)                  # 21.25, "Now your table is waiting."

# ---------------------------------------------------------------- 9 end
T_END = G.at(12)                         # 22.0
T_FADE = (24.7, DURATION)

CUTS = [T_WIPE[0], T_GIANT, T_FIND, T_LIME, T_TO_CHAT, T_MAP, T_CRAVE, T_END]
