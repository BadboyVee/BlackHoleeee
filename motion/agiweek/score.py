"""AGI WEEK: the timing sheet. The soundtrack is the reference clip's own sound (19.8 s), and the edit follows that
clip's edit on it: the wordmarks flash on the clicks with each lab's model on top, the sparkle opens on the drop,
and every product moment (Gemini, ChatGPT, Claude, Grok) starts on the hit the original gave it. What those
moments say is the post: another week closer to AGI, a stacked final week of September, Sonnet 5.5 expected
today, a new OpenAI model and Agent "O" with DevDay tomorrow (AGI?), Grok 4.8 maybe, Anthropic's IPO planned for
November, and a big week ahead. The founders are in the collage and in their own labs' moments."""

DURATION = 19.8
SIZE = (1920, 1080)
CX, CY = 960, 540

# ---------------------------------------------------------------- 1 the wordmarks, one on every click
FLASH = [0.0, 0.25, 0.548, 0.815, 1.082, 1.348, 1.615, 1.882, 2.148, 2.415, 2.682]
T_SHRINK = 2.98            # the last wordmark shrinks away
T_DROP = 3.296             # the drop: a sparkle
T_HOLE = 3.47              # the sparkle opens into the collage
T_COLLAGE_OUT = 4.12       # the collage blurs away

# ---------------------------------------------------------------- 2 Gemini
T_SEARCH = 4.256           # the search pill
T_MORPH = 4.95             # the sparkle slides into the pill
T_DARK = 5.141             # the dark Gemini pill
T_HEADLINE = 5.70          # Another week closer to AGI.
T_PHONE = 6.52             # the phone: the final week of September is looking stacked

# ---------------------------------------------------------------- 3 ChatGPT
T_OAI = 7.12               # the blossom
T_COMPOSER = 8.17          # the question types
T_SEND = 9.10
T_SOURCES = 9.38           # reading: Sam Altman, OpenAI DevDay
T_ANSWER = 9.78            # the answer streams in

# ---------------------------------------------------------------- 4 Claude
T_CLAUDE = 10.74           # into Claude's cream
T_SPARK = 10.98
T_WORDMARK = 11.52         # Claude types in, Sonnet 5.5 on top
T_GRID = 12.02             # the wall of canvases
T_CANVAS = 13.22           # the canvas
T_SWATCH = 13.55           # a swatch is picked
T_TOOLBAR = 13.82          # into the toolbar
T_CLICK = 14.45            # Comment, and the note: IPO planned for November

# ---------------------------------------------------------------- 5 Grok
T_GROK = 14.78
T_INPUT = 15.74            # the question types
T_LAPTOP = 16.68           # the week, in a terminal
T_ANSWER2 = 17.64          # Grok answers
T_OUT = 18.70              # everything goes to black
T_END = 18.98              # Big week ahead.

CUTS = [T_DROP, T_SEARCH, T_DARK, T_HEADLINE, T_PHONE, T_OAI, T_COMPOSER, T_SOURCES, T_ANSWER, T_CLAUDE, T_GRID,
        T_CANVAS, T_TOOLBAR, T_GROK, T_INPUT, T_LAPTOP, T_ANSWER2]
