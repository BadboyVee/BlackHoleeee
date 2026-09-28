"""AGI WEEK look: fonts, the founders (their photos, the crops for their team-boss cards, and their names and roles
as the user gave them), and the soft light every ground uses."""
import os
from functools import lru_cache

import skia

from engine import gfx as G

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "..", "photos", "agiweek")

# founders: the photo, a head-and-shoulders crop for the card (x0, y0, x1, y1 in the photo), the caption
FOUNDERS = {
    "amodei": dict(file="amodei.jpg", crop=(8, 0, 574, 390), name="Dario & Daniela Amodei",
                   role="Co-founders · Anthropic"),
    "altman": dict(file="altman.jpg", crop=(133, 0, 403, 300), name="Sam Altman", role="Co-founder & CEO · OpenAI"),
    "hassabis": dict(file="hassabis.jpg", crop=(29, 0, 207, 198), name="Demis Hassabis",
                     role="Co-founder & CEO · Google DeepMind"),
    "zuckerberg": dict(file="zuckerberg.jpg", crop=(18, 0, 198, 200), name="Mark Zuckerberg",
                       role="Founder & CEO · Meta"),
    "musk": dict(file="musk.jpg", crop=(177, 20, 447, 320), name="Elon Musk", role="Founder · xAI & SpaceX"),
}


@lru_cache(maxsize=None)
def F(fam, size, **axes):
    return G.Font(fam, size, **axes)


def rr(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def blob(c, x, y, r, col, a=1.0):
    """A soft pool of light: col at the centre fading to nothing at r."""
    c.drawCircle(x, y, r, G.P(col, a, shader=G.radial_grad(x, y, r, [col, col], alphas=[a, 0.0])))
