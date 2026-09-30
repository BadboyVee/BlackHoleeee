"""CLAUDE CODE, a fan-made spot: the scenes, in order, each drawn only while it is on."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_back, hash01
from .look import INK, heavy, sans, T, line, caption, pop
from .cast import agent, Face, ORDER, idle_blink, hop
from . import ui
from .score import *                                                    # noqa: F401,F403 (the timing sheet)

TEXT_Y = 948
BIG = 124


def gone(t, t_out, dur=0.2):
    """1 until t_out, then shrinking back to nothing."""
    v = clamp((t - t_out) / dur)
    return 1.0 if v <= 0 else 1 - in_back(v, 1.8)


def solo(c, name, t, t_in, t_out, x, y=720, size=320, look=(0.0, 0.0), f=None, bounce=True):
    s = pop(t, t_in, 0.34, 2.4) * gone(t, t_out)
    if s <= 0.01:
        return
    lift, squash = hop(t, t_in, 0.62, 0.035) if bounce else (0.0, 0.0)
    agent(c, name, x, y - lift * size, size, t, f or Face(look=look, blink=idle_blink(t, hash(name) % 31)),
          s=s, squash=squash * 0.6)


# ---------------------------------------------------------------- meet, the name, the crew

def name_mark(c, t, t0, y=580, size=150, t_out=None, a=1.0):
    """Claude Code, the fixer standing in for the o of Code."""
    f = heavy(size)
    left, right = "Claude C", "de"
    tr = -0.045
    wl, wr = f.width(left, tr), f.width(right, tr)
    slot = size * 0.62
    total = wl + slot + wr
    x0 = 960 - total / 2
    u = clamp((t - t0) / 0.3)
    if u <= 0:
        return
    k = out_back(u, 1.8) if u < 1 else 1.0
    if t_out is not None:
        k *= gone(t, t_out)
    with G.layer(c, a * clamp(u * 3)):
        with G.xf(c, 960, y - size * 0.35, s=0.7 + 0.3 * k):
            c.translate(-960, -(y - size * 0.35))
            T(c, left, x0, y, f, INK, tracking=tr)
            T(c, right, x0 + wl + slot, y, f, INK, tracking=tr)
            s = pop(t, t0 + 0.12, 0.34, 2.6)
            agent(c, "fixer", x0 + wl + slot / 2, y + size * 0.06, size * 1.05, t, s=s, shadow=False,
                  f=Face(blink=idle_blink(t, 3)))


def lineup(c, t, t_in, t_out, y=640, size=260, spread=230, f_happy=None):
    for i, n in enumerate(ORDER):
        s = pop(t, t_in + 0.08 * i, 0.32, 2.6) * gone(t, t_out + 0.03 * i)
        if s <= 0.01:
            continue
        lift, squash = hop(t, t_in + 0.08 * i, 0.62, 0.04)
        happy = 1.0 if f_happy is not None and t >= f_happy else 0.0
        agent(c, n, 960 + (i - 2) * spread, y - lift * size, size, t,
              Face(look=(0.0, 0.3), blink=idle_blink(t, i + 1), happy=happy), s=s, squash=squash * 0.6, seed=i)


def opening(c, t):
    if t < T_NAME:
        line(c, t, "meet", T_MEET + 0.2, y=575, size=96, out=T_NAME - 0.12)
    elif t < T_LINEUP:
        name_mark(c, t, T_NAME, t_out=T_LINEUP - 0.12)
    else:
        lineup(c, t, T_LINEUP, T_READER - 0.05, f_happy=T_FOR)
        caption(c, t, "agents in your terminal", T_LINEUP + 0.35, 770, out=T_FOR - 0.1)
        if t >= T_FOR:
            line(c, t, "for your code.", T_FOR, y=TEXT_Y, size=BIG, out=T_READER - 0.1)


# ---------------------------------------------------------------- reads, runs, tools

def reader_part(c, t):
    x = lerp(960, 560, out_cubic(clamp((t - (T_READS - 0.35)) / 0.4)))
    x = lerp(x, 960, out_cubic(clamp((t - (T_TOOLS - 0.2)) / 0.35)))
    look = (1.0, 0.0) if T_READS <= t < T_TOOLS else (0.0, 0.0)
    solo(c, "reader", t, T_READER, T_TESTER - 0.18, x, look=look)
    if T_READS - 0.05 <= t < T_RUNS + 0.1:
        a = 1 - clamp((t - (T_RUNS - 0.1)) / 0.2)
        ui.file_tree(c, t, T_READS - 0.05, 860, 250, a=a)
    if T_RUNS - 0.05 <= t < T_TOOLS + 0.1:
        a = 1 - clamp((t - (T_TOOLS - 0.1)) / 0.2)
        ui.terminal(c, t, T_RUNS - 0.05, 830, 330, a=a)
    if t >= T_TOOLS - 0.05:
        a = gone(t, T_TESTER - 0.2)
        ui.tools(c, t, T_TOOLS - 0.05, 960, 520, a=max(0.0, a))
    line(c, t, "reads your repo", T_READS, y=TEXT_Y, size=BIG, out=T_RUNS - 0.1)
    line(c, t, "runs your terminal", T_RUNS, y=TEXT_Y, size=BIG, out=T_TOOLS - 0.1)
    line(c, t, "all your tools", T_TOOLS, y=TEXT_Y, size=BIG, out=T_TESTER - 0.1)


# ---------------------------------------------------------------- learns your rules

def tester_part(c, t):
    x = lerp(960, 560, out_cubic(clamp((t - (T_RULES - 0.3)) / 0.4)))
    solo(c, "tester", t, T_TESTER, T_PLANNER - 0.15, x, look=(1.0, -0.2) if t >= T_RULES else (0.0, 0.0))
    if t >= T_RULES - 0.05:
        a = 1 - clamp((t - (T_PLANNER - 0.2)) / 0.2)
        ui.claude_md(c, t, T_RULES - 0.05, T_RULE_ITEMS, 840, 300, a=a)
    line(c, t, "learns your rules", T_RULES, y=TEXT_Y, size=BIG, out=T_PLANNER - 0.1)


# ---------------------------------------------------------------- ask it anything, or just @claude

def planner_part(c, t):
    talk = 0.0
    for ti in T_ASK_ITEMS:
        if 0 <= t - ti < 0.25:
            talk = math.sin(math.pi * (t - ti) / 0.25)
    look = (0.0, 0.0)
    if T_ASK <= t < T_OR:
        k = int(((t - T_ASK) / 0.9)) % 4
        look = [(-1.0, -0.5), (1.0, -0.5), (1.0, 0.4), (-1.0, 0.4)][k]
    solo(c, "planner", t, T_PLANNER, T_BUG - 0.15, 960, y=700,
         f=Face(look=look, talk=talk, blink=idle_blink(t, 7), happy=1.0 if t >= T_MENTION else 0.0))
    if T_ASK <= t < T_OR + 0.2:
        a = 1 - clamp((t - (T_OR - 0.15)) / 0.2)
        ui.bubble(c, t, T_ASK_ITEMS[0], 600, 330, "fix the flaky test", a=a)
        ui.bubble(c, t, T_ASK_ITEMS[1], 1330, 300, "", typing=True, a=a)
        ui.bubble(c, t, T_ASK_ITEMS[2], 1380, 470, "why is login slow?", a=a)
        ui.bubble(c, t, T_ASK_ITEMS[3], 560, 520, "add dark mode", a=a)
    if t >= T_MENTION:                                                  # rings go out from it, like a call
        for k in range(3):
            v = clamp((t - (T_MENTION + 0.18 * k)) / 0.7)
            if 0 < v < 1:
                c.drawCircle(960, 600, 120 + 260 * out_cubic(v), G.P("#3b9bff", 0.6 * (1 - v), stroke=5 * (1 - v) + 1))
        s = pop(t, T_MENTION, 0.3, 2.6) * gone(t, T_BUG - 0.15)
        if s > 0.01:
            with G.xf(c, 960, 380, s=s):
                f = sans(26, 650)
                w = f.width("@claude") + 44
                c.drawRRect(ui.rr(-w / 2, -28, w, 56, 28), G.P("#3b9bff"))
                T(c, "@claude", 0, 9, f, "#ffffff", align=0.5)
    line(c, t, "ask it anything", T_ASK, y=TEXT_Y, size=BIG, out=T_OR - 0.1)
    line(c, t, "or just", T_OR, y=TEXT_Y, size=BIG, out=T_MENTION - 0.1)
    line(c, t, "@claude.", T_MENTION, y=TEXT_Y, size=BIG, out=T_BUG - 0.1)


# ---------------------------------------------------------------- a bug, on it, review, tests

CODE_X, CODE_Y = 650, 250


def bug_part(c, t):
    a = gone(t, T_REVIEW - 0.15)
    glow = clamp((t - (T_SQUASH + 0.15)) / 0.3)
    s = pop(t, T_BUG - 0.05, 0.3, 1.8) * a
    if s > 0.01:
        with G.xf(c, CODE_X + 310, CODE_Y + 220, s=s):
            c.translate(-310, -220)
            ui.code_card(c, 0, 0, glow=glow)
            # the bug wanders along the lines, until it is squashed
            if t < T_SQUASH + 0.35:
                tau = t - T_BUG
                bx = 150 + 300 * (0.5 + 0.5 * math.sin(0.9 * tau))
                by = 140 + 90 * math.sin(0.6 * tau + 1.0)
                sq = clamp((t - T_SQUASH) / 0.08)
                ui.bug(c, bx, by, 1.6, t if t < T_SQUASH else T_SQUASH, squash=sq,
                       a=1 - clamp((t - (T_SQUASH + 0.15)) / 0.2))
                if t >= T_SQUASH:                                        # a little puff
                    v = clamp((t - T_SQUASH) / 0.35)
                    for i in range(8):
                        ang = 2 * math.pi * i / 8
                        c.drawCircle(bx + math.cos(ang) * 60 * out_cubic(v), by + math.sin(ang) * 60 * out_cubic(v),
                                     7 * (1 - v), G.P("#ffb4a8", 1 - v))
            ui.check_badge(c, 600, 22, 26, pop(t, T_SQUASH + 0.2, 0.3, 2.6))
    if t >= T_ONIT - 0.05:                                               # the fixer jumps in
        u = clamp((t - (T_ONIT - 0.05)) / 0.45)
        x = lerp(1560, CODE_X + 470, out_cubic(u))
        y = lerp(760, CODE_Y + 250, out_cubic(u)) - 160 * math.sin(math.pi * u)
        stomp = clamp(1 - abs(t - T_SQUASH) / 0.1)
        agent(c, "fixer", x, y + 20 * stomp, 260, t, Face(look=(-1.0, 0.3), happy=1.0 if t >= T_SQUASH + 0.1 else 0.0,
                                                          blink=idle_blink(t, 11)),
              s=a, squash=0.8 * stomp - (0.3 if 0.05 < u < 0.7 else 0.0), shadow=False)
    line(c, t, "a bug?", T_BUG, y=TEXT_Y, size=BIG, out=T_ONIT - 0.1)
    line(c, t, "on it.", T_ONIT, y=TEXT_Y, size=BIG, out=T_REVIEW - 0.1)


def review_part(c, t):
    a = gone(t, T_CI - 0.15)
    ui.comments(c, t, T_REVIEW, 300, 260, a=max(0.0, a) * (1 - clamp((t - (T_TESTS - 0.1)) / 0.25)))
    x = lerp(900, 700, out_cubic(clamp((t - (T_TESTS - 0.1)) / 0.4)))
    ui.pr_card(c, t, T_REVIEW + 0.1, x, 280, checked_from=T_TESTS + 0.1, a=max(0.0, a))
    solo(c, "fixer", t, T_REVIEW + 0.2, T_CI - 0.15, x + 640, y=660, size=230, look=(-1.0, 0.0),
         f=Face(look=(-1.0, 0.0), happy=1.0 if t >= T_TESTS + 0.5 else 0.0, blink=idle_blink(t, 5)))
    line(c, t, "reviewed.", T_REVIEW, y=TEXT_Y, size=BIG, out=T_TESTS - 0.1)
    line(c, t, "tests pass.", T_TESTS, y=TEXT_Y, size=BIG, out=T_CI - 0.1)


# ---------------------------------------------------------------- CI

def ci_part(c, t):
    a = gone(t, T_OWL - 0.15)
    ui.ci_card(c, t, T_CI, 560, 260, green_from=T_GREEN + 0.05, a=max(0.0, a))
    worried = t < T_GREEN
    solo(c, "tester", t, T_CI + 0.15, T_OWL - 0.15, 1360, y=660, size=250,
         f=Face(look=(-1.0, 0.2), happy=0.0 if worried else 1.0, talk=0.6 if worried and (t * 3) % 1 < 0.3 else 0.0,
                blink=idle_blink(t, 9)))
    line(c, t, "CI red?", T_CI, y=TEXT_Y, size=BIG, out=T_GREEN - 0.1)
    line(c, t, "back to green.", T_GREEN, y=TEXT_Y, size=BIG, out=T_OWL - 0.1)


# ---------------------------------------------------------------- while you sleep, it asks first, the rules

def night_part(c, t):
    night = clamp((t - (T_OWL + 0.45)) / 0.4)
    if t < T_ONE0:
        a = 1 - clamp((t - (T_ONE0 - 0.25)) / 0.2)
        if night < 1:
            ui.sun(c, 1640, 180, 46, t, a=a * (1 - night))
        if night > 0:
            with G.xf(c, 1640, 180, s=0.6 + 0.4 * out_back(night, 2.0)):
                ui.moon(c, 0, 0, 34, a=a * night)
    x = 960
    if t >= T_SLEEP - 0.3:
        x = lerp(960, 560, out_cubic(clamp((t - (T_SLEEP - 0.3)) / 0.4)))
    if t >= T_RULES2 - 0.2:
        x = lerp(560, 1500, out_cubic(clamp((t - (T_RULES2 - 0.2)) / 0.45)))
    sleepy = 0.8 if T_SLEEP <= t < T_ASKS else 0.0
    solo(c, "nightowl", t, T_OWL, T_ONE0 - 0.1, x, y=700, size=300,
         f=Face(look=(1.0, 0.0) if t >= T_ASKS else (0.0, 0.0), sleepy=sleepy, blink=idle_blink(t, 13)))
    if T_SLEEP <= t < T_OWL + 3.0 and T_SLEEP <= t < T_ASKS:
        for k in range(3):                                               # zzz
            v = ((t - T_SLEEP) * 0.9 + k / 3) % 1
            T(c, "z", x + 110 + 60 * v, 470 - 120 * v, heavy(34 + 18 * v), "#5a5fd6", (1 - v) * 0.9)
    if T_SLEEP - 0.05 <= t < T_ASKS + 0.1:
        ui.job_card(c, t, T_SLEEP - 0.05, 830, 320, a=1 - clamp((t - (T_ASKS - 0.1)) / 0.2))
    if T_ASKS - 0.05 <= t < T_RULES2 + 0.1:
        ui.permission(c, t, T_ASKS - 0.05, T_CLICK, 830, 300, a=1 - clamp((t - (T_RULES2 - 0.1)) / 0.2))
    if t >= T_RULES2 - 0.05:
        ui.rules(c, t, T_RULES2 - 0.05, 560, 280, a=max(0.0, gone(t, T_ONE0 - 0.15)))
    line(c, t, "while you sleep", T_SLEEP, y=TEXT_Y, size=BIG, out=T_ASKS - 0.1)
    line(c, t, "it asks first.", T_ASKS, y=TEXT_Y, size=BIG, out=T_RULES2 - 0.1)
    line(c, t, "you're in control.", T_CONTROL, y=TEXT_Y, size=BIG, out=T_ONE0 - 0.1)


# ---------------------------------------------------------------- one agent, a whole team

SLOTS = {"tester": -2, "reader": -1, "planner": 1, "nightowl": 2}


def team_part(c, t):
    if t < T_FIVE:
        big = lerp(260, 380, out_cubic(clamp((t - T_ONE) / 0.4)))
        solo(c, "fixer", t, T_ONE0, T_TEAM - 0.1, 960, y=730, size=big)
    else:
        shrink = out_cubic(clamp((t - T_SUB) / 0.3))                    # "or subagents": they huddle up
        for n in ORDER:
            if n == "fixer":
                size = lerp(lerp(380, 300, out_cubic(clamp((t - T_FIVE) / 0.3))), 230, shrink)
                agent(c, n, 960, 730, size, t, s=gone(t, T_TEAM - 0.08), f=Face(blink=idle_blink(t, 3), happy=1.0))
                continue
            slot = SLOTS[n]
            k = ORDER.index(n)
            s = pop(t, T_FIVE + 0.06 * abs(slot), 0.3, 2.6) * gone(t, T_TEAM - 0.08 + 0.02 * abs(slot))
            x = 960 + slot * lerp(250, 200, shrink)
            agent(c, n, x, 700 + 30 * shrink, lerp(230, 200, shrink), t, s=s, seed=k,
                  f=Face(look=(-0.6 if slot > 0 else 0.6, 0.0), blink=idle_blink(t, k + 2),
                         happy=1.0 if t >= T_SUB else 0.0))
    if t >= T_TEAM - 0.05:                                               # a whole team: waves of them
        cols, rows = 9, 3
        for j in range(rows):
            for i in range(cols):
                n = ORDER[(i + 2 * j) % len(ORDER)]
                x = 960 + (i - (cols - 1) / 2) * 180 + (40 if j % 2 else -40)
                y = 330 + j * 190
                d = math.hypot(i - (cols - 1) / 2, (j - 1) * 1.5)
                s = pop(t, T_TEAM - 0.05 + 0.035 * d, 0.3, 2.6) * gone(t, T_END - 0.1 + 0.01 * d)
                lift, squash = hop(t, T_TEAM + 0.1 * hash01(i + 9 * j, 3), 0.5, 0.05)
                agent(c, n, x, y - lift * 150, 150, t, s=s, squash=squash * 0.5, seed=i + 9 * j,
                      f=Face(happy=1.0 if (i + j) % 3 == 0 else 0.0, blink=idle_blink(t, i + 9 * j)))
    line(c, t, "one agent.", T_ONE, y=TEXT_Y, size=BIG, out=T_SUB - 0.1)
    line(c, t, "or subagents,", T_SUB, y=TEXT_Y, size=BIG, out=T_TEAM - 0.1)
    line(c, t, "a whole team.", T_TEAM, y=TEXT_Y, size=BIG, out=T_END - 0.1)


# ---------------------------------------------------------------- the end

def ending(c, t):
    name_mark(c, t, T_END, y=560, size=150)
    caption(c, t, "Get back to building.", T_TAG, 660, size=32, col="#5f5f68")
    u = clamp((t - T_NOTE) / 0.4)
    if u > 0:
        T(c, "Fan-made  ·  not affiliated with Anthropic  ·  made by VEEE", 960, 1010, sans(19, 500), "#9a9aa2",
          u, align=0.5)
    fade = clamp((t - (T_BLACK - 0.25)) / 0.25)
    if fade > 0:
        c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", fade))


def draw(c, t):
    if t < T_READER:
        opening(c, t)
    elif t < T_TESTER:
        reader_part(c, t)
    elif t < T_PLANNER:
        tester_part(c, t)
    elif t < T_BUG:
        planner_part(c, t)
    elif t < T_REVIEW:
        bug_part(c, t)
    elif t < T_CI:
        review_part(c, t)
    elif t < T_OWL:
        ci_part(c, t)
    elif t < T_ONE0:
        night_part(c, t)
    elif t < T_END:
        team_part(c, t)
    elif t < T_BLACK:
        ending(c, t)
