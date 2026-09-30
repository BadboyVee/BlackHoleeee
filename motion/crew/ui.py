"""CLAUDE CODE: the little screens around the crew. A file tree, a terminal, tool chips, CLAUDE.md, prompts, a
code card with a bug in it, a pull request, CI runs, a job going overnight, a permission prompt and the rules."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, hash01
from .look import (WHITE, INK, GREY, SOFT, CARD, CARD_LINE, CORAL, MINT, LAVENDER, INDIGO, RED, GREEN, BLUE,
                   sans, mono, T, rr, card, pop)


def appear(t, t0, dur=0.3):
    u = clamp((t - t0) / dur)
    return u, (out_back(u, 1.6) if u < 1 else 1.0)


# ---------------------------------------------------------------- reads your repo

TREE = [(0, "src", True), (1, "app.ts", False), (1, "auth", True), (2, "login.ts", False), (2, "session.ts", False),
        (1, "billing.ts", False), (0, "tests", True), (1, "login.test.ts", False), (0, "CLAUDE.md", False)]


def file_tree(c, t, t0, x, y, w=520, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    h = 64 + 44 * len(TREE)
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
                c.drawCircle(26 + i * 20, 28, 6, G.P(col))
            reading = (t - t0 - 0.2) / 0.11
            for i, (d, name, folder) in enumerate(TREE):
                yy = 64 + i * 44
                if 0 <= reading - i < 1.4:
                    c.drawRRect(rr(12, yy - 4, w - 24, 38, 9), G.P("#efe9ff", 1 - max(0.0, reading - i - 0.4)))
                if reading > i:
                    c.drawCircle(w - 34, yy + 15, 5, G.P(LAVENDER))
                ix = 28 + d * 30
                if folder:
                    c.drawRRect(rr(ix, yy + 6, 22, 16, 3), G.P("#9aa0b4"))
                    c.drawRRect(rr(ix, yy + 3, 10, 6, 2), G.P("#9aa0b4"))
                else:
                    c.drawRRect(rr(ix + 3, yy + 3, 16, 22, 3), G.P("#c9ccd8"))
                T(c, name + ("/" if folder else ""), ix + 34, yy + 22, mono(21, 460 if folder else 400), INK)


# ---------------------------------------------------------------- runs your terminal

TERM = [("$ ", "npm test", "#e6e6ea"), ("", "  ✓ 128 passed  (4.2s)", "#4ade80"), ("$ ", "git status", "#e6e6ea"),
        ("", "  nothing to commit, working tree clean", "#9aa0b4")]


def terminal(c, t, t0, x, y, w=620, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    h = 300
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            c.drawRRect(rr(0, 10, w, h, 18), G.P("#000000", 0.14, blur=22))
            c.drawRRect(rr(0, 0, w, h, 18), G.P("#141418"))
            for i, col in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
                c.drawCircle(26 + i * 20, 26, 6, G.P(col))
            T(c, "claude", w / 2, 32, mono(16, 500), "#6b6b76", align=0.5)
            f = mono(22, 440)
            chars = int(max(0.0, t - t0 - 0.15) * 38)
            yy = 84
            for pre, cmd, col in TERM:
                s = pre + cmd
                shown = s[:max(0, chars)]
                chars -= len(s) + 4
                if pre:
                    T(c, shown[:2], 26, yy, f, CORAL)
                    T(c, shown[2:], 26 + f.width("$ "), yy, f, col)
                else:
                    T(c, shown, 26, yy, f, col)
                yy += 50
            if (t * 2) % 1 < 0.6:
                c.drawRect(skia.Rect.MakeXYWH(26, yy - 22, 12, 26), G.P("#e6e6ea", 0.8))


# ---------------------------------------------------------------- all your tools

TOOLS = [("git", "#f05033"), ("CI", "#2f7bff"), ("db", "#22c55e"), ("docs", "#a78bfa"), ("logs", "#f59e0b"),
         ("issues", "#ec4899"), ("web", "#0ea5e9"), ("design", "#ef4444"), ("tests", "#10b981"), ("deploy", "#6366f1"),
         ("chat", "#14b8a6"), ("API", "#f97316")]


def tools(c, t, t0, cx, cy, a=1.0):
    for i, (name, col) in enumerate(TOOLS):
        s = pop(t, t0 + 0.03 * i, 0.3, 2.4)
        if s <= 0.01:
            continue
        ang = 2 * math.pi * (i / len(TOOLS)) + 0.35 * (t - t0)
        rx, ry = 330 + 40 * hash01(i, 3), 210 + 30 * hash01(i, 4)
        x = cx + rx * math.cos(ang) * s
        y = cy + ry * math.sin(ang) * s + 8 * math.sin(3 * t + i)
        f = sans(20, 650)
        w = f.width(name) + 58
        with G.layer(c, a):
            with G.xf(c, x, y, s=s):
                c.drawRRect(rr(-w / 2, -26 + 6, w, 52, 16), G.P("#000000", 0.08, blur=10))
                c.drawRRect(rr(-w / 2, -26, w, 52, 16), G.P(WHITE))
                c.drawRRect(rr(-w / 2 + 10, -14, 28, 28, 8), G.P(col))
                T(c, name, -w / 2 + 46, 7, f, INK)


# ---------------------------------------------------------------- learns your rules

RULES = ["run the tests before you commit", "use pnpm, not npm", "keep diffs small"]


def claude_md(c, t, t0, times, x, y, w=600, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    h = 90 + 64 * len(RULES)
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "CLAUDE.md", 30, 50, mono(24, 560), INK)
            T(c, "project memory", w - 30, 50, sans(17, 500), SOFT, align=1.0)
            for i, (rule, ti) in enumerate(zip(RULES, times)):
                v, kk = appear(t, ti, 0.28)
                if v <= 0:
                    continue
                yy = 100 + i * 64
                with G.layer(c, clamp(v * 2)):
                    c.drawRRect(rr(20, yy, w - 40, 50, 12), G.P(CARD))
                    c.drawCircle(46, yy + 25, 11 * kk, G.P(MINT))
                    p = skia.Path()
                    p.moveTo(40, yy + 25)
                    p.lineTo(44.5, yy + 29.5)
                    p.lineTo(52, yy + 20)
                    c.drawPath(p, G.P(WHITE, 1, stroke=3, cap="round", join="round"))
                    T(c, rule, 70, yy + 33, sans(22, 500), INK)


# ---------------------------------------------------------------- ask it anything

def bubble(c, t, t0, x, y, s, typing=False, tail=1, a=1.0):
    k = pop(t, t0, 0.3, 2.4)
    if k <= 0.01:
        return
    f = sans(22, 560)
    w = (f.width(s) if not typing else 44) + 44
    h = 54
    with G.layer(c, a):
        with G.xf(c, x, y, s=k):
            c.drawRRect(rr(-w / 2, -h / 2 + 8, w, h, 20), G.P("#000000", 0.07, blur=12))
            c.drawRRect(rr(-w / 2, -h / 2, w, h, 20), G.P(WHITE))
            c.drawRRect(rr(-w / 2 + 0.5, -h / 2 + 0.5, w - 1, h - 1, 20), G.P(CARD_LINE, 1, stroke=1.2))
            if typing:
                for i in range(3):
                    g = 0.3 + 0.7 * max(0.0, math.sin(2 * math.pi * (1.6 * (t - t0) - i * 0.2)))
                    c.drawCircle(-14 + i * 14, 0, 5, G.P("#6b6b76", g))
            else:
                T(c, s, 0, 8, f, INK, align=0.5)


# ---------------------------------------------------------------- a bug, on it

CODE = [(0, 0.34, RED), (1, 0.52, None), (1, 0.44, None), (2, 0.30, RED), (2, 0.58, None), (1, 0.40, None),
        (0, 0.22, RED), (1, 0.50, None), (1, 0.36, None)]


def code_card(c, x, y, w=620, h=440, a=1.0, glow=0.0):
    card(c, x, y, w, h, fill=WHITE, a=a)
    for i, (d, ln, col) in enumerate(CODE):
        yy = y + 50 + i * 42
        c.drawRRect(rr(x + 30, yy, 26, 10, 5), G.P("#ff9ab0" if col else "#ffc9d6", a))
        c.drawRRect(rr(x + 70 + d * 30, yy, w * ln, 10, 5), G.P("#d8dae3", a))
    if glow > 0:
        c.drawRRect(rr(x, y, w, h, 18), G.P(GREEN, 0.9 * glow, stroke=3))


def bug(c, x, y, s, t, squash=0.0, a=1.0):
    """A small red beetle, legs going."""
    if a <= 0:
        return
    with G.layer(c, a):
        with G.xf(c, x, y, s=s, sx=s * (1 + 0.5 * squash), sy=s * (1 - 0.7 * squash)):
            for i in range(3):
                for sx in (-1, 1):
                    ph = math.sin(2 * math.pi * (6 * t + i * 0.33 + (0.5 if sx > 0 else 0)))
                    p = skia.Path()
                    p.moveTo(sx * 6, -6 + i * 7)
                    p.lineTo(sx * 16, -9 + i * 8 + 3 * ph)
                    p.lineTo(sx * 21, -2 + i * 8 + 3 * ph)
                    c.drawPath(p, G.P("#7a1010", 1, stroke=2.4, cap="round", join="round"))
            c.drawOval(skia.Rect.MakeXYWH(-11, -14, 22, 30), G.P(RED, 1, shader=G.radial_grad(-4, -6, 22,
                                                                                             ["#ff8a80", RED, "#b3161b"])))
            c.drawLine(0, -12, 0, 15, G.P("#7a1010", 0.8, stroke=1.6))
            c.drawCircle(0, -17, 7, G.P("#3a0a0a"))
            for sx in (-1, 1):
                c.drawLine(sx * 3, -22, sx * 9, -30, G.P("#3a0a0a", 1, stroke=2, cap="round"))
            for (dx, dy) in [(-5, -3), (5, 2), (-4, 8)]:
                c.drawCircle(dx, dy, 2.4, G.P("#3a0a0a", 0.7))


def check_badge(c, x, y, r, s=1.0, col=GREEN):
    if s <= 0.01:
        return
    with G.xf(c, x, y, s=s):
        c.drawCircle(0, 0, r, G.P(col))
        p = skia.Path()
        p.moveTo(-r * 0.42, 0)
        p.lineTo(-r * 0.1, r * 0.32)
        p.lineTo(r * 0.45, -r * 0.3)
        c.drawPath(p, G.P(WHITE, 1, stroke=r * 0.22, cap="round", join="round"))


# ---------------------------------------------------------------- review, tests

COMMENTS = [("nit: rename to isExpired", CORAL), ("add a test for the retry?", LAVENDER), ("LGTM once green", MINT)]
CHECKS = ["handles expired sessions", "retries once, then fails", "no change to the API"]


def comments(c, t, t0, x, y, a=1.0):
    for i, (s, col) in enumerate(COMMENTS):
        u, k = appear(t, t0 + 0.12 * i)
        if u <= 0:
            continue
        yy = y + i * 120
        with G.layer(c, a * clamp(u * 2)):
            with G.xf(c, x + 230, yy + 44, s=0.85 + 0.15 * k):
                c.translate(-230, -44)
                card(c, 0, 0, 460, 88, fill=WHITE)
                c.drawCircle(40, 44, 16, G.P(col))
                T(c, s, 70, 52, sans(21, 520), INK)


def pr_card(c, t, t0, x, y, checked_from=None, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 520, 330
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            p = skia.Path()                                             # a branch glyph
            p.moveTo(34, 30)
            p.lineTo(34, 58)
            p.moveTo(34, 44)
            p.quadTo(52, 44, 52, 30)
            c.drawPath(p, G.P(CORAL, 1, stroke=3, cap="round"))
            c.drawCircle(34, 30, 4, G.P(CORAL))
            c.drawCircle(52, 30, 4, G.P(CORAL))
            T(c, "fix #214", 70, 52, sans(26, 700), INK, tracking=-0.02)
            T(c, "login: expired sessions", 70, 80, sans(17, 500), GREY)
            for i, s in enumerate(CHECKS):
                yy = 118 + i * 64
                c.drawRRect(rr(20, yy, w - 40, 50, 12), G.P(CARD))
                done = checked_from is not None and t >= checked_from + 0.28 * i
                if done:
                    kk = pop(t, checked_from + 0.28 * i, 0.25, 2.6)
                    check_badge(c, 46, yy + 25, 12, kk)
                else:
                    c.drawCircle(46, yy + 25, 11, G.P("#c9ccd8", 1, stroke=2))
                T(c, s, 70, yy + 33, sans(21, 500), INK if done else GREY)


# ---------------------------------------------------------------- CI

RUNS = [0.42, 0.78, 0.55, 0.9, 0.62, 0.84, 0.48, 0.95]


def ci_card(c, t, t0, x, y, green_from=None, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 620, 380
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "CI · main", 30, 50, sans(24, 700), INK, tracking=-0.02)
            g = 0.0 if green_from is None else clamp((t - green_from) / 0.5)
            badge_col = G.mixc(RED, GREEN, g)
            label = "passing" if g > 0.5 else "failing"
            f = sans(17, 650)
            bw = f.width(label) + 28
            c.drawRRect(rr(w - 30 - bw, 26, bw, 32, 16), G.P(badge_col, 0.14))
            T(c, label, w - 30 - bw / 2, 48, f, badge_col, align=0.5)
            for i, v in enumerate(RUNS):
                bh = 220 * v * out_cubic(clamp((t - t0 - 0.05 * i) / 0.4))
                gi = 0.0 if green_from is None else clamp((t - green_from - 0.07 * i) / 0.25)
                col = G.mixc(RED, GREEN, gi)
                bx = 40 + i * 70
                c.drawRRect(rr(bx, 330 - bh, 44, bh, 8), G.P(col, 0.9))


# ---------------------------------------------------------------- while you sleep

def moon(c, x, y, r, a=1.0):
    p = skia.Path()
    p.addCircle(x, y, r)
    q = skia.Path()
    q.addCircle(x + r * 0.45, y - r * 0.3, r * 0.85)
    m = skia.Op(p, q, skia.PathOp.kDifference_PathOp)
    c.drawPath(m, G.P("#1a1a22", a))


def sun(c, x, y, r, t, a=1.0):
    c.drawCircle(x, y, r * 0.5, G.P("#ffb020", a))
    for i in range(8):
        ang = 2 * math.pi * i / 8 + 0.4 * t
        c.drawLine(x + math.cos(ang) * r * 0.72, y + math.sin(ang) * r * 0.72, x + math.cos(ang) * r,
                   y + math.sin(ang) * r, G.P("#ffb020", a, stroke=r * 0.14, cap="round"))


def job_card(c, t, t0, x, y, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 580, 200
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "Migrating to v2", 30, 56, sans(24, 700), INK, tracking=-0.02)
            n = min(18, int(4 + 14 * clamp((t - t0) / 1.2)))
            T(c, f"{n} of 18 files", w - 30, 56, sans(18, 520), GREY, align=1.0)
            c.drawRRect(rr(30, 104, w - 60, 14, 7), G.P("#ececf0"))
            c.drawRRect(rr(30, 104, (w - 60) * n / 18, 14, 7), G.P(INDIGO))
            T(c, "running in the cloud · you'll get a PR", 30, 160, sans(18, 500), GREY)


# ---------------------------------------------------------------- it asks first

def permission(c, t, t0, click, x, y, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 560, 250
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "Run this command?", 30, 56, sans(26, 700), INK, tracking=-0.02)
            c.drawRRect(rr(30, 82, w - 60, 52, 12), G.P("#141418"))
            T(c, "$ npm install zod", 50, 116, mono(21, 460), "#e6e6ea")
            pressed = clamp(1 - abs(t - click) / 0.08) if t >= click - 0.08 else 0.0
            done = t >= click + 0.05
            s = 1 - 0.06 * pressed
            with G.xf(c, 30 + 90, 196, s=s):
                c.drawRRect(rr(-90, -26, 180, 52, 26), G.P(INK))
                T(c, "Allowed" if done else "Allow", 0, 8, sans(21, 650), WHITE, align=0.5)
            c.drawRRect(rr(230, 170, 150, 52, 26), G.P(CARD))
            T(c, "Deny", 305, 204, sans(21, 650), INK, align=0.5)
            if t >= click - 0.9:                                      # the cursor comes to Allow
                v = out_cubic(clamp((t - (click - 0.9)) / 0.8))
                cx, cy = lerp(w + 80, 128, v), lerp(h + 60, 206, v)
                p = skia.Path()
                for px, py in [(0, 0), (0, 25), (6.5, 19.5), (11, 29.5), (15, 27.6), (10.8, 18), (19, 18)]:
                    (p.moveTo if p.isEmpty() else p.lineTo)(px, py)
                p.close()
                with G.xf(c, cx, cy, s=1.4 * (1 - 0.12 * pressed)):
                    c.drawPath(p, G.P(INK))
                    c.drawPath(p, G.P(WHITE, 1, stroke=1.6, join="round"))


RULE_ROWS = [("allow", "Bash(npm test)", GREEN, "✓"), ("ask", "Bash(git push)", BLUE, "?"),
             ("deny", "Read(./.env)", RED, "⊘")]


def rules(c, t, t0, x, y, a=1.0):
    u, k = appear(t, t0)
    if u <= 0:
        return
    w, h = 600, 290
    with G.layer(c, a * clamp(u * 2)):
        with G.xf(c, x + w / 2, y + h / 2, s=0.9 + 0.1 * k):
            c.translate(-w / 2, -h / 2)
            card(c, 0, 0, w, h, fill=WHITE)
            T(c, "permissions", 30, 50, mono(20, 520), GREY)
            for i, (kind, rule, col, glyph) in enumerate(RULE_ROWS):
                yy = 76 + i * 66
                c.drawRRect(rr(20, yy, w - 40, 54, 14), G.P(CARD))
                T(c, kind, 44, yy + 35, sans(22, 700), col)
                T(c, rule, 140, yy + 35, mono(20, 460), INK)
                on = clamp((t - (t0 + 0.35 + 0.22 * i)) / 0.18)
                tx = w - 92
                c.drawRRect(rr(tx, yy + 13, 56, 28, 14), G.P(G.mixc("#d6d8e0", BLUE, on)))
                c.drawCircle(tx + 14 + 28 * out_cubic(on), yy + 27, 11, G.P(WHITE))
