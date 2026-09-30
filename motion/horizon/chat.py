"""HORIZON: what Scout says. This week's read, as a builder would want it: what is likely, what is next, what to
watch, and what is only a rumour, each marked as such. Predictions, not news."""
from .look import GREEN, BLUE, GOLD, RED

ASK = "what's coming this week?"
TITLE = "This week · a structural read"
HEAT = "FRONTIER HEAT: HIGH"
ITEMS = [
    ("LIKELY TODAY", GREEN, "#0f2e1a",
     "Sonnet 5.5 is rolling out: routed from Sonnet 5 at the same price. Free users will likely get it too."),
    ("NEXT UP", BLUE, "#0e2240", "A new OpenAI model and Agent “O”, expected around DevDay."),
    ("WATCH", GOLD, "#33240c", "Grok 4.8, maybe, after 4.7's mixed reviews."),
    ("RUMOUR", RED, "#3a1412", "Anthropic IPO talk points to November. Unconfirmed."),
]
