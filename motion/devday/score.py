"""DevDay 2026: the timing sheet. The soundtrack is the teaser's own (120 BPM, a bar every 2 s, first downbeat at
1.3 s). The film opens on the teaser's own first 7.3 s: the big face turning, the faces gathering, falling into the
middle and bursting into the points of "1 day.", then "1 day. 20+ launches.". On the drop the twenty launches run,
two to a bar, over the teaser's four bars looped. The last of them, the official launch of AGI, takes the teaser's
last bar and its long low note, and the teaser's own ending, OpenAI DevDay[2026], closes the film, marked as a
fan-made set of predictions and signed MADE BY VEEE."""

SIZE = (1920, 1080)
CX, CY = 960, 540
BEAT = 0.5
BAR = 2.0

# ---------------------------------------------------------------- 1 the teaser's opening
T_TURN0, T_TURN1 = 0.33, 1.30     # the big face turns right round
T_SHRINK = 4.05                    # the faces fall into the middle...
T_LAND = 5.13                      # ...their points have landed on "1 day."
T_LINE = 6.19                      # the bass drops out: 1 day. 20+ launches.

# ---------------------------------------------------------------- 2 the launches, two to a bar
T_LIST = 7.30                      # the drop
ITEM = 1.0
N_LIST = 19                        # the twentieth gets the ending


def t_item(i):
    return T_LIST + ITEM * i


# ---------------------------------------------------------------- 3 the official launch of AGI, and the end
T_AGI = t_item(N_LIST)             # 26.30: everyone gathers
T_COUNT = 27.30                    # 3, 2, 1 in their eyes
T_FALL = 28.55                     # the bass has dropped out: into the middle
T_DECODE = 29.30                   # the points spell it out
T_REVEAL = 30.06                   # the bass comes back: AGI
T_LOCKUP = 32.22                   # the long low note: OpenAI DevDay[2026]
T_NOTE = 33.25                     # fan-made predictions
T_CREDIT = 34.45                   # MADE BY VEEE
DURATION = 36.6

# ---------------------------------------------------------------- the sound, cut from the teaser's
TEASER_DOWNBEAT = 1.29             # a hair before the first downbeat, so every cut keeps its attack
PHRASE = [1.29, 3.29, 5.29, 7.29]  # the teaser's four bars
LIST_BARS = PHRASE * 2 + PHRASE[:3]
T_ENDING = T_LIST - 0.01 + BAR * len(LIST_BARS)   # 29.29: the teaser's last bar and its ending
