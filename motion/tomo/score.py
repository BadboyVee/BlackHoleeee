"""TOMO: the timing sheet. The soundtrack is the reference's own, a beat every 0.4865 s (123 BPM) from 0.50 s, and
the film cuts where it cuts: the hook (Tomo peeks in, winks, says hey: Could use an extra hand?), a blue wipe into
what it does (laundry, dishes, plants, on cards), its app on a phone (Tomo turns chores into free time, every
day), a whip into its dashboard, Done., the black card (You rest. Tomo does the rest.) and the wordmark."""

DURATION = 15.0
SIZE = (1920, 1080)
B0, BEAT = 0.50, 0.4865


def beat(k):
    return B0 + BEAT * k


# 1 the hook
T_WINK = 0.56
T_PSST = (0.80, 1.24)
T_LABEL = 1.02
T_WORDS = [1.22, 1.40, 1.62, 1.78]          # Could / use / an extra / hand?
T_BLUE = 2.18                               # the blue grows out of "hand?"...
T_BLUE_FULL = beat(4)                       # ...and fills the frame on the beat (2.45)

# 2 the work
T_CARDS = (beat(5), beat(6), beat(7))       # 2.93 3.42 3.91: each card lands on its beat
T_PHONE = beat(8)                           # 4.39: the blue folds into the phone...
T_FOLD = T_PHONE - 0.05
T_PHONE_IN = T_PHONE + 0.34                 # ...which has it by 4.73

# 3 the studio
T_MARK = 4.60                               # tomo
T_TURNS = (5.20, 5.36)                      # turns chores / into
T_FILM = (5.70, beat(11))                   # free / time, (5.85)
T_BEAT = (6.18, beat(12))                   # every / day. (6.34)
T_CURSOR = 6.50
T_CLICK = 6.93
T_WHIP = 7.00                               # whip into the button...
T_DASH = beat(14)                           # ...7.31, and out to the dashboard

# 4 rendered
T_TYPE = 7.50
T_SYNC = beat(16)                           # 8.28: the tempo locks, the sound row is synced
T_CHECK1, T_CHECK2 = beat(17), beat(19)     # 8.77 9.74: cut on every beat, the vertical cut
T_CHIPS = beat(18)                          # 9.26
T_DONE = 10.52                              # the day's chores are done...
T_STAMP = beat(21)                          # ...10.72: Done.
T_BLACK = 11.00                             # the black comes in...
T_BLACK_FULL = beat(22)                     # ...11.20

# 5 you
T_YOU = [11.40, beat(23), beat(24), 12.42, beat(25)]   # You / rest. / Tomo / does the / rest.
T_WHITE = beat(26)                          # 13.15: the white comes in...
T_END = 13.40                               # ...the wordmark
T_PEEK = 13.84
T_TAG, T_BUTTON, T_STATS = 14.0, 14.2, 14.36
