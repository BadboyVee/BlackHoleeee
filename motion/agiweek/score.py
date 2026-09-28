"""AGI WEEK: the timing sheet for a 16:9 news hype film about the last week of September 2026. 128 BPM, 18 bars.

Another week closer to AGI. The labs stack up with their models on top: Sonnet 5.5 expected today, a new OpenAI
model and Agent "O" before DevDay, Gemini and Muse in the race, Grok 4.8 maybe. DevDay is tomorrow (AGI?),
Anthropic plans its IPO for November, and it's a big week ahead.
"""
from engine.core import Grid

BPM = 128
G = Grid(BPM)            # a beat is 0.46875 s, a bar 1.875 s
DURATION = 35.25
SIZE = (1920, 1080)
CX, CY = 960, 540

# ---------------------------------------------------------------- 1 cold open: Another week closer to AGI.
OPEN_WORDS = [(G.at(1, 1), "Another"), (G.at(1, 2), "week"), (G.at(1, 3), "closer"), (G.at(1, 4), "to"),
              (G.at(2, 1), "AGI.")]
T_AGI = G.at(2, 1)                       # 1.875, AGI. lands
T_TICK = G.at(2, 3)                      # the progress bar moves one week closer

# ---------------------------------------------------------------- 2 the slate: stacked
T_SLATE = G.at(3)                        # 3.75
DROP_ORDER = ["meta", "google", "xai", "openai", "anthropic"]    # the last lands on top
T_DROPS = [G.at(3, 1), G.at(3, 2), G.at(3, 3), G.at(3, 4), G.at(4, 1)]
T_STACKED = G.at(4, 1, 2)                # "stacked." lands
T_FAN = G.at(4, 2, 2)                    # the stack fans out into a row
ROW_ORDER = ["anthropic", "openai", "google", "meta", "xai"]
T_DIVE = G.at(4, 4, 2)                   # into the Anthropic card

# ---------------------------------------------------------------- 3 Anthropic: Sonnet 5.5, expected today
T_ANT = G.at(5)                          # 7.5
T_PICKER = G.at(5, 3)                    # the model picker opens
T_PICK = G.at(6, 1)                      # Sonnet 5.5 is chosen
T_ANT_FOUNDERS = G.at(6, 2)
T_FABLE = G.at(6, 3)                     # "A Fable moment?"

# ---------------------------------------------------------------- 4 OpenAI: a new model and Agent "O"
T_OAI = G.at(7)                          # 11.25
T_OAI_TYPE = (G.at(7, 2), G.at(8, 1))    # the prompt types
T_OAI_SEND = G.at(8, 1, 1)
T_AGENT = G.at(8, 2)                     # the Agent "O" card
T_OAI_FOUNDER = G.at(7, 4)

# ---------------------------------------------------------------- 5 also in the race: Gemini, Muse
T_RACE = G.at(9)                         # 15.0
T_RACE_FOUNDERS = G.at(10, 1)

# ---------------------------------------------------------------- 6 xAI: Grok 4.8, maybe
T_XAI = G.at(11)                         # 18.75
T_ROLL = G.at(11, 3)                     # 4.7 rolls to 4.8
T_XAI_FOUNDER = G.at(12, 1)

# ---------------------------------------------------------------- 7 DevDay tomorrow
T_DEV = G.at(13)                         # 22.5
T_TOMORROW = G.at(13, 3)
T_BUILD = G.at(14)                       # the build to the drop
T_MYSTERY = [G.at(14, 1), G.at(14, 1, 2), G.at(14, 2), G.at(14, 2, 2), G.at(14, 3), G.at(14, 3, 2)]

# ---------------------------------------------------------------- 8 the drop: (AGI?)
T_DROP = G.at(15)                        # 26.25

# ---------------------------------------------------------------- 9 Anthropic IPO: November
T_IPO = G.at(16)                         # 28.125
T_RISE = G.at(16, 3)                     # Anthropic rises to the top of the stack
T_ON_TOP = G.at(17, 1)                   # "Staying on top."

# ---------------------------------------------------------------- 10 end
T_END = G.at(18)                         # 31.875
T_FADE = (34.45, DURATION)

CUTS = [T_SLATE, T_ANT, T_OAI, T_RACE, T_XAI, T_DEV, T_DROP, T_IPO, T_END]
