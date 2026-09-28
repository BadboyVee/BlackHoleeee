"""DevDay 2026: the timing sheet. The soundtrack is the teaser's own (120 BPM, a bar every 2 s, first downbeat at
1.3 s into it). The film opens on white: "Introducing…" on the teaser's first second of clicks, played twice, the
last point of the ellipsis swelling into the teaser's big grey face. Then the teaser's own first 7.3 s, redrawn on
white: the face turning, the faces gathering, falling into the middle and bursting into the points of "1 day.",
then "1 day. 20+ launches.". On the drop a black iris closes and the twenty launches run on black, two to a bar,
over the teaser's four bars looped. The last of them, the official launch of AGI, takes the teaser's last bar and
its long low note, and the teaser's own ending, OpenAI DevDay[2026], closes the film, marked as a fan-made set of
predictions and signed MADE BY VEEE."""

SIZE = (1920, 1080)
CX, CY = 960, 540
BEAT = 0.5
BAR = 2.0

# ---------------------------------------------------------------- 0 Introducing…, on white
T_OPEN = 2.0                       # where the teaser's own 0 s falls in the film
T_WORD = 0.25                      # "Introducing" lands, point by point
T_DOTS = (1.05, 1.30, 1.55)        # the ellipsis, on the eighths
T_SWELL = 1.70                     # the last point swells into the teaser's face

# ---------------------------------------------------------------- 1 the teaser's opening, on white
# (these are the teaser's own times; the film plays them from T_OPEN)
T_TURN0, T_TURN1 = 0.33, 1.30      # the big face turns right round
T_SHRINK = 4.05                    # the faces fall into the middle...
T_LAND = 5.13                      # ...their points have landed on "1 day."
T_LINE = 6.19                      # the bass drops out: 1 day. 20+ launches.

# ---------------------------------------------------------------- 2 the launches, two to a bar, on black
T_LIST = T_OPEN + 7.30             # the drop
IRIS = 0.2                         # the black iris that closes on it
ITEM = 1.0
N_LIST = 19                        # the twentieth gets the ending


def t_item(i):
    return T_LIST + ITEM * i


# ---------------------------------------------------------------- 3 the official launch of AGI, and the end
T_AGI = t_item(N_LIST)             # everyone gathers
T_COUNT = T_AGI + 1.00             # 3, 2, 1 in their eyes
T_FALL = T_AGI + 2.25              # the bass has dropped out: into the middle
T_DECODE = T_AGI + 3.00            # the points spell it out
T_REVEAL = T_AGI + 3.76            # the bass comes back: AGI
T_LOCKUP = T_AGI + 5.92            # the long low note: OpenAI DevDay[2026]
T_NOTE = T_AGI + 6.95              # fan-made predictions
T_CREDIT = T_AGI + 8.15            # MADE BY VEEE
DURATION = T_AGI + 10.30

# ---------------------------------------------------------------- the sound, cut from the teaser's
OPEN_LOOP = (0.0, 1.0)             # its first two beats of clicks, played twice under "Introducing…"
PHRASE = [1.29, 3.29, 5.29, 7.29]  # its four bars, from a hair before each downbeat
LIST_BARS = PHRASE * 2 + PHRASE[:3]
T_ENDING = T_LIST - 0.01 + BAR * len(LIST_BARS)   # its last bar and its ending
