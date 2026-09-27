"""ARNAUD'S: the timing sheet for a 16:9 AI-concierge spot in the style of a UI ad. 120 BPM, 13 bars.

Props land on a kitchen table while the headline says choosing dinner for your anniversary is a lot, and a card
drops in to become a phone's input box. You ask for pizza, sushi or ramen but want something special; the assistant
thinks, flips through the usual cravings and picks Arnaud's in the French Quarter. A receipt prints, a card taps the
terminal, a map walks you there, and the name again.
"""
from engine.core import Grid

BPM = 120
G = Grid(BPM)            # a beat is 0.5 s, a bar 2 s
DURATION = 27.5
SIZE = (1920, 1080)
CX, CY = 960, 540

# ---------------------------------------------------------------- 1 intro: the kitchen table
T_NAME = G.at(2)                         # 2.0, "is a lot." lands and the fruit comes on every sixteenth
T_WIPE = (3.45, 3.95)                    # the props fly off; the card becomes the phone's input box

# ---------------------------------------------------------------- 2 the ask
T_PHONE = 3.95
T_TYPE = (4.32, 6.05)
PROMPT = "It’s our anniversary tonight. Pizza, sushi or ramen? I want something special."
T_SEND = 6.12                            # the send button, just before the words take over

# ---------------------------------------------------------------- 3 giant words
T_GIANT = 6.2                            # the camera has dived in behind the caret
WORDS = [(G.at(4, 1, 2), "Pizza,", "pizza"), (G.at(4, 2, 2), "sushi,", "sushi"), (G.at(4, 3, 2), "ramen?", "ramen"),
         (G.at(4, 4), "something", None), (G.at(4, 4, 2), "special.", "glow")]

# ---------------------------------------------------------------- 4 finding
T_FIND = G.at(5)                         # 8.0
T_DROPS = [G.at(5, 2), G.at(5, 3), G.at(5, 4)]   # pizza, sushi, ramen are tossed out of the ring
T_RISE = G.at(5, 4, 2)                   # the doubloon flips into the middle

# ---------------------------------------------------------------- 5 carousel
T_LIME = G.at(6)                         # 10.0, the thinking fades and the cards come
T_CARDS = 10.2
T_PICK = G.at(6, 3)                      # 11.0, Arnaud's lifts out of the row
T_FULL = G.at(6, 3, 2)                   # 11.25, its card opens to the whole frame: the dining room
T_TO_CHAT = G.at(7, 1, 1)                # 12.125

# ---------------------------------------------------------------- 6 checkout: the cashier
T_CHAT = G.at(7, 1, 2)                   # 12.25, the counter is in frame
T_PRINT = (12.45, 14.55)                 # the receipt prints, line by line
T_TERMINAL = 13.1                        # the payment terminal slides in
T_AMOUNT = G.at(8, 1)                    # 14.0, the due-now amount rolls as the receipt prints it
T_CARD = 14.9                            # the card flies in
T_TAP = G.at(8, 4)                       # 15.5, tap: approved
T_STAMP = 15.62                          # CONFIRMED stamped on the receipt

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
T_END = G.at(12)                         # 22.0, the ribbons burst into the frame and the name
T_OFF = 24.25                            # the frame folds back into the orb
T_CREDIT = G.at(13, 2)                   # 24.5, MADE BY VEEE
T_FADE = (26.8, DURATION)

CUTS = [T_WIPE[0], T_GIANT, T_FIND, T_LIME, T_TO_CHAT, T_MAP, T_CRAVE, T_END]
