"""The broadcast-style frame: corner brackets, labels, timecode, bar counter, live level meter."""
from .core import FPS, W, H, clamp
from . import gfx as G


class HUD:
    def __init__(self, grid, bars, title, sub, sections, duration):
        self.grid = grid
        self.bars = bars
        self.title = title
        self.sub = sub
        self.sections = sorted(sections)
        self.duration = duration
        self.f_title = G.Font("mono", 15, wght=760)
        self.f_small = G.Font("mono", 15, wght=430)

    def section(self, t):
        label = self.sections[0][1]
        for t0, name in self.sections:
            if t >= t0:
                label = name
        return label

    @staticmethod
    def timecode(t):
        f = int(round(t * FPS))
        s, ff = divmod(f, FPS)
        m, ss = divmod(s, 60)
        hh, mm = divmod(m, 60)
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    def draw(self, c, t, ink="#f2f0ea", alpha=1.0, levels=None, accent=None):
        if alpha <= 0.01:
            return
        dim = 0.5 * alpha
        pb = G.P(ink, alpha, stroke=2.0)
        m, arm = 44, 26
        for x, y, dx, dy in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
            c.drawLine(x, y, x + arm * dx, y, pb)
            c.drawLine(x, y, x, y + arm * dy, pb)

        top, bot = 88, H - 76
        run = G.text(c, self.title, 88, top, self.f_title, G.P(ink, alpha), tracking=0.16)
        G.text(c, self.sub, 88 + run.width + 44, top, self.f_small, G.P(ink, dim), tracking=0.16)
        G.text(c, self.section(t), W - 88, top, self.f_title, G.P(ink, alpha), align=1.0, tracking=0.16)

        run = G.text(c, self.timecode(t), 88, bot, self.f_title, G.P(ink, alpha), tracking=0.12)
        G.text(c, f"{FPS} FPS", 88 + run.width + 44, bot, self.f_small, G.P(ink, dim), tracking=0.16)

        bar = min(self.grid.bar_of(t), self.bars)
        beat = self.grid.beat_of(t)
        r = G.text(c, f"BAR {bar:02d}/{self.bars:02d}", W - 88, bot, self.f_title, G.P(ink, alpha),
                   align=1.0, tracking=0.16)
        x = W - 88 - r.width - 22
        for i in range(4, 0, -1):
            x -= 12
            filled = i == beat
            p = G.P(accent if (filled and accent) else ink, alpha, stroke=0 if filled else 1.4)
            c.drawRect(G.skia.Rect.MakeXYWH(x, bot - 11, 11, 11), p)
            x -= 5
        x -= 20
        r = G.text(c, f"{self.grid.bpm:g} BPM", x, bot, self.f_small, G.P(ink, dim), align=1.0, tracking=0.16)
        if levels is not None:
            x -= r.width + 26
            n = len(levels)
            for i in range(n):
                v = clamp(float(levels[n - 1 - i]))
                hgt = 2 + 13 * v
                c.drawRect(G.skia.Rect.MakeXYWH(x - i * 5 - 3, bot - hgt, 3, hgt), G.P(ink, alpha * (0.35 + 0.65 * v)))

        prog = clamp(t / self.duration)
        c.drawLine(m, H - 26, m + (W - 2 * m) * prog, H - 26, G.P(ink, alpha, stroke=2.0))
