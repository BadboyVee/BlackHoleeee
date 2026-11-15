"""Lagos 2090 - original hand-painted / illuminated shop signs, generated with Pillow.
All wording is invented for this film (Yoruba / English / Pidgin mix); no real brand marks.
"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .core import ROOT

OUT = ROOT / "blender" / "gen" / "signs"
BOLD = ["/usr/share/fonts/opentype/inter/Inter-Black.otf", "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
        "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", "/usr/share/fonts/opentype/inter/Inter-BoldItalic.otf"]
FALLBACK = str(ROOT / "fonts" / "Montserrat-Light.ttf")

# (key, main line, sub line, background, text, accent)
SIGNS = [
    ("pure_water", "OMI TUTU", "PURE WATER · ICE BLOCK", (20, 70, 150), (245, 240, 225), (250, 200, 40)),
    ("phone_charging", "PHONE CHARGING", "SOLAR FAST CHARGE · 24HRS", (235, 190, 30), (25, 25, 25), (200, 30, 30)),
    ("okada_park", "OKADA PARK", "E-BIKE CHARGE POINT", (25, 110, 60), (250, 245, 230), (250, 205, 40)),
    ("mama_put", "MAMA SADE", "BUKA · AMALA · EWEDU", (185, 35, 30), (250, 240, 215), (250, 205, 40)),
    ("provisions", "IRE-AKARI STORES", "PROVISIONS & MINERALS", (240, 235, 220), (175, 30, 30), (20, 70, 150)),
    ("suya", "SUYA SPOT", "FRESH EVERY EVENING", (30, 30, 30), (250, 200, 40), (220, 60, 30)),
    ("barbing", "KINGS BARBING SALON", "SHARP CUT · DYE · DREADS", (20, 100, 120), (250, 245, 230), (250, 205, 40)),
    ("tailor", "IYA BOLA FASHION", "ASO-OKE · ANKARA · AGBADA", (120, 40, 110), (250, 240, 215), (250, 205, 40)),
    ("recharge", "RECHARGE & DATA", "SIM REG · POS · TRANSFER", (245, 240, 225), (20, 110, 60), (200, 30, 30)),
    ("fruit", "ESO TUNTUN", "FRESH FRUIT · AGBALUMO · IBEPE", (250, 150, 30), (40, 30, 20), (25, 110, 60)),
    ("hover_stop", "HOVER-DANFO STOP", "CMS · OSHODI · IKEJA · YABA", (245, 195, 20), (20, 20, 20), (20, 20, 20)),
    ("akara", "AKARA ELEPO", "HOT · MORNING & NIGHT", (150, 80, 30), (250, 240, 215), (250, 205, 40)),
    ("vulcanizer", "VULCANIZER", "HOVER PAD & TYRE REPAIR", (30, 30, 35), (245, 240, 225), (230, 60, 30)),
    ("chemist", "ALAFIA CHEMIST", "PATENT MEDICINE STORE", (245, 245, 240), (20, 110, 60), (200, 30, 30)),
    ("kaabo", "E KAABO", "WELCOME TO LAGOS 2090", (20, 110, 60), (250, 245, 230), (250, 205, 40)),
    ("cold_drinks", "COLD ZOBO & KUNU", "CHILLED · SOLAR FRIDGE", (150, 20, 60), (250, 240, 215), (250, 205, 40)),
]
ROUTES = ["CMS", "OSHODI", "IKEJA", "YABA", "OJUELEGBA", "OBALENDE", "3RD MAINLAND"]


def _font(px, bold=True, idx=0):
    try:
        return ImageFont.truetype(BOLD[idx % len(BOLD)] if bold else FALLBACK, px)
    except Exception:
        return ImageFont.truetype(FALLBACK, px)


def _fit(d, text, maxw, maxh, idx=0, bold=True):
    px = int(maxh)
    while px > 8:
        f = _font(px, bold, idx)
        b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= maxw and b[3] - b[1] <= maxh:
            return f, b
        px -= 3
    return _font(8, bold, idx), d.textbbox((0, 0), text, font=_font(8, bold, idx))


def _weather(im, rnd, amount=1.0):
    """Sun fade, grime, drips and a few scratches."""
    w, h = im.size
    noise = Image.effect_noise((w // 4, h // 4), 60).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    dark = Image.new("RGB", (w, h), (70, 55, 40))
    im = Image.composite(dark, im, noise.point(lambda v: int(max(0, v - 150) * 1.4 * amount)))
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(int(14 * amount)):
        x = rnd.randrange(w); y0 = rnd.randrange(0, h // 3); ln = rnd.randrange(h // 6, h)
        d.line([(x, y0), (x + rnd.randint(-3, 3), min(h, y0 + ln))], fill=(40, 30, 20, rnd.randint(25, 70)), width=rnd.randint(1, 4))
    for _ in range(int(30 * amount)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        d.line([(x, y), (x + rnd.randint(-40, 40), y + rnd.randint(-6, 6))], fill=(230, 225, 210, rnd.randint(30, 90)), width=1)
    return im.filter(ImageFilter.GaussianBlur(0.6))


def make_sign(key, main, sub, bg, fg, accent, w=1024, h=256, seed=0, weather=1.0):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{key}.png"
    if p.exists():
        return p
    rnd = random.Random(hash(key) % 9999 + seed)
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    m = int(h * 0.06)
    d.rectangle([m, m, w - m, h - m], outline=accent, width=max(3, h // 40))
    f, b = _fit(d, main, w - 6 * m, h * (0.50 if sub else 0.7), rnd.randrange(4))
    x = (w - (b[2] - b[0])) / 2 - b[0]
    y = h * (0.12 if sub else 0.15) - b[1] + m
    d.text((x + h // 50, y + h // 50), main, font=f, fill=tuple(int(c * 0.35) for c in bg))   # painted drop shadow
    d.text((x, y), main, font=f, fill=fg)
    if sub:
        f2, b2 = _fit(d, sub, w - 8 * m, h * 0.17, 1)
        d.text(((w - (b2[2] - b2[0])) / 2 - b2[0], h * 0.70 - b2[1]), sub, font=f2, fill=accent if sum(accent) != sum(bg) else fg)
    im = _weather(im, rnd, weather)
    im.save(p)
    return p


def all_signs():
    return {s[0]: make_sign(*s) for s in SIGNS}


def route_board(key="route_board", lines=("CMS", "OSHODI", "YABA"), w=768, h=256):
    """Danfo route board: black stencil letters on off-white, like a hand-painted destination board."""
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{key}.png"
    if p.exists():
        return p
    im = Image.new("RGB", (w, h), (236, 228, 200))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 6, h - 6], outline=(20, 20, 20), width=6)
    text = " · ".join(lines)
    f, b = _fit(d, text, w - 60, h * 0.62, 0)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=f, fill=(15, 15, 15))
    im = _weather(im, random.Random(4), 0.7)
    im.save(p)
    return p


def sticker_sheet(key="danfo_stickers", w=1024, h=256):
    """Bumper stickers / painted slogans for the danfo tail (transparent background)."""
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{key}.png"
    if p.exists():
        return p
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    items = [("NO SHAKING", (200, 30, 30), (250, 245, 230)), ("GOD'S TIME", (20, 70, 150), (250, 220, 60)),
             ("EKO O NI BAJE", (25, 110, 60), (250, 245, 230)), ("HOVER SMALL SMALL", (20, 20, 20), (250, 200, 40))]
    x = 20
    rnd = random.Random(3)
    for text, bg, fg in items:
        f = _font(54, True, rnd.randrange(4))
        b = d.textbbox((0, 0), text, font=f)
        tw = b[2] - b[0] + 36
        if x + tw > w - 10:
            break
        y = rnd.randint(40, 110)
        d.rounded_rectangle([x, y, x + tw, y + 92], 10, fill=bg + (255,))
        d.text((x + 18 - b[0], y + 46 - (b[3] + b[1]) / 2), text, font=f, fill=fg + (255,))
        x += tw + 22
    im.save(p)
    return p


def wall_writing(key="not_for_sale", text="THIS HOUSE IS NOT FOR SALE", sub="BEWARE OF 419", w=1536, h=384):
    """The classic warning painted on Lagos walls (transparent, rough brush letters)."""
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{key}.png"
    if p.exists():
        return p
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f, b = _fit(d, text, w - 40, h * 0.5, 3)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], h * 0.08 - b[1]), text, font=f, fill=(150, 20, 15, 235))
    f2, b2 = _fit(d, sub, w * 0.6, h * 0.26, 3)
    d.text(((w - (b2[2] - b2[0])) / 2 - b2[0], h * 0.64 - b2[1]), sub, font=f2, fill=(150, 20, 15, 225))
    a = im.split()[3]
    n = Image.effect_noise((w // 2, h // 2), 90).resize((w, h), Image.BICUBIC)
    a = Image.composite(a, Image.new("L", (w, h), 0), n.point(lambda v: 255 if v > 95 else 90))
    im.putalpha(a.filter(ImageFilter.GaussianBlur(0.8)))
    im.save(p)
    return p
