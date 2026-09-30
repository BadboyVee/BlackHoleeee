"""VEEE: the timing sheet. The soundtrack is the reference's own, a beat every 0.4865 s (123 BPM) from 0.50 s, and
the film cuts where it cuts: the hook (Vee peeks in, winks, psst: Launch day coming soon?), a blue wipe into the
work (three of our films, playing on cards), the studio on a phone (VEEE turns it into a film, on the beat), a
whip into the render dashboard, Rendered., the black card (You launch. We make it move.) and the wordmark."""

DURATION = 15.0
SIZE = (1920, 1080)
B0, BEAT = 0.50, 0.4865


def beat(k):
    return B0 + BEAT * k


# 1 the hook
T_WINK = 0.56
T_PSST = (0.80, 1.24)
T_LABEL = 1.02
T_WORDS = [1.22, 1.40, 1.62, 1.78]          # Launch / day / coming / soon?
T_BLUE = 2.18                               # the blue grows out of "soon?"...
T_BLUE_FULL = beat(4)                       # ...and fills the frame on the beat (2.45)

# 2 the work
T_CARDS = (beat(5), beat(6), beat(7))       # 2.93 3.42 3.91: each card lands on its beat
T_PHONE = beat(8)                           # 4.39: the blue folds into the phone...
T_FOLD = T_PHONE - 0.05
T_PHONE_IN = T_PHONE + 0.34                 # ...which has it by 4.73

# 3 the studio
T_MARK = 4.60                               # VEEE
T_TURNS = (5.20, 5.36)                      # turns / it into
T_FILM = (5.70, beat(11))                   # a / film (5.85)
T_BEAT = (6.18, beat(12))                   # on the / beat. (6.34)
T_CURSOR = 6.50
T_CLICK = 6.93
T_WHIP = 7.00                               # whip into the button...
T_DASH = beat(14)                           # ...7.31, and out to the dashboard

# 4 rendered
T_TYPE = 7.50
T_SYNC = beat(16)                           # 8.28: the tempo locks, the sound row is synced
T_CHECK1, T_CHECK2 = beat(17), beat(19)     # 8.77 9.74: cut on every beat, the vertical cut
T_CHIPS = beat(18)                          # 9.26
T_DONE = 10.52                              # the render finishes...
T_STAMP = beat(21)                          # ...10.72: Rendered.
T_BLACK = 11.00                             # the black comes in...
T_BLACK_FULL = beat(22)                     # ...11.20

# 5 you
T_YOU = [11.40, beat(23), beat(24), 12.42, beat(25)]   # You / launch. / We / make it / move.
T_WHITE = beat(26)                          # 13.15: the white comes in from "move."...
T_END = 13.40                               # ...the wordmark
T_PEEK = 13.84
T_TAG, T_BUTTON, T_STATS = 14.0, 14.2, 14.36
