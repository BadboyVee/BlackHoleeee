"""SPARKS, a fan concept: the scenes, in order, each drawn only while it is on."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_back, in_back, hash01
from .look import INK, heavy, sans, T, line, caption, pop
from .cast import agent, ORDER, CLOSED, hop, blinking, sprite
from . import ui
from .score import *                                                    # noqa: F401,F403 (the timing sheet)

TEXT_Y = 948
BIG = 124
FLOOR = 760


def gone(t, t_out, dur=0.2):
    """1 until t_out, then shrinking back to nothing."""
    v = clamp((t - t_out) / dur)
    return 1.0 if v <= 0 else 1 - in_back(v, 1.8)


def face(name, t, happy=False, asleep=False, seed=0):
    if asleep:
        return "asleep"
    if happy:
        return CLOSED[name]
    return CLOSED[name] if blinking(t, seed) and name != "sleeper" else "open"


def solo(c, name, t, t_in, t_out, x, y=FLOOR, size=520, happy=False, asleep=False, bounce=True):
    s = pop(t, t_in, 0.34, 2.4) * gone(t, t_out)
    if s <= 0.01:
        return
    lift, squash = hop(t, t_in, 0.62, 0.03) if bounce else (0.0, 0.0)
    agent(c, name, x, y, size, t, face(name, t, happy, asleep, hash(name) % 31), s=s, lift=lift * size,
          squash=squash * 0.6)


# ---------------------------------------------------------------- meet, the name, the crew

def wordmark(c, t, t0, y=585, size=170, t_out=None, a=1.0):
    """sparks, the lead sitting in for the a."""
    f = heavy(size)
    left, right = "sp", "rks"
    tr = -0.045
    wl, wr = f.width(left, tr), f.width(right, tr)
    slot = size * 0.66
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
            agent(c, "lead", x0 + wl + slot / 2, y + size * 0.02, size * 1.55, t,
                  face("lead", t, seed=3), s=s, shadow_a=0.0)


def lineup(c, t, t_in, t_out, y=FLOOR - 40, size=400, spread=300, happy_from=None):
    for i, n in enumerate(ORDER):
        s = pop(t, t_in + 0.08 * i, 0.32, 2.6) * gone(t, t_out + 0.03 * i)
        if s <= 0.01:
            continue
        lift, squash = hop(t, t_in + 0.08 * i, 0.62, 0.04)
        happy = happy_from is not None and t >= happy_from
        agent(c, n, 960 + (i - 2) * spread, y, size, t, face(n, t, happy, seed=i), s=s, lift=lift * size,
              squash=squash * 0.6)


def opening(c, t):
    if t < T_NAME:
        line(c, t, "meet", T_MEET + 0.2, y=575, size=96, out=T_NAME - 0.12)
    elif t < T_LINEUP:
        wordmark(c, t, T_NAME, t_out=T_LINEUP - 0.12)
    else:
        lineup(c, t, T_LINEUP, T_READER - 0.05, happy_from=T_FOR)
        caption(c, t, "always-on Claude agents", T_LINEUP + 0.35, 800, out=T_FOR - 0.1)
        if t >= T_FOR:
            line(c, t, "for you.", T_FOR, y=TEXT_Y, size=BIG, out=T_READER - 0.1)


# ---------------------------------------------------------------- its own computer, browser, your apps

def lead_part(c, t):
    x = lerp(960, 470, out_cubic(clamp((t - (T_READS - 0.35)) / 0.4)))
    x = lerp(x, 960, out_cubic(clamp((t - (T_TOOLS - 0.2)) / 0.35)))
    solo(c, "lead", t, T_READER, T_TESTER - 0.18, x, size=500)
    if T_READS - 0.05 <= t < T_RUNS + 0.1:
        ui.computer(c, t, T_READS - 0.05, 800, 190, a=1 - clamp((t - (T_RUNS - 0.1)) / 0.2))
    if T_RUNS - 0.05 <= t < T_TOOLS + 0.1:
        ui.browser(c, t, T_RUNS - 0.05, 790, 190, a=1 - clamp((t - (T_TOOLS - 0.1)) / 0.2))
    if t >= T_TOOLS - 0.05:
        ui.apps(c, t, T_TOOLS - 0.05, 960, 520, a=max(0.0, gone(t, T_TESTER - 0.2)))
    line(c, t, "its own computer", T_READS, y=TEXT_Y, size=BIG, out=T_RUNS - 0.1)
    line(c, t, "its own browser", T_RUNS, y=TEXT_Y, size=BIG, out=T_TOOLS - 0.1)
    line(c, t, "all your apps", T_TOOLS, y=TEXT_Y, size=BIG, out=T_TESTER - 0.1)


# ---------------------------------------------------------------- learns how you work

def reader_part(c, t):
    x = lerp(960, 520, out_cubic(clamp((t - (T_RULES - 0.3)) / 0.4)))
    solo(c, "reader", t, T_TESTER, T_PLANNER - 0.15, x, size=500, happy=t >= T_RULE_ITEMS[-1] + 0.3)
    if t >= T_RULES - 0.05:
        ui.memory(c, t, T_RULES - 0.05, T_RULE_ITEMS, 860, 290, a=1 - clamp((t - (T_PLANNER - 0.2)) / 0.2))
    line(c, t, "learns how you work", T_RULES, y=TEXT_Y, size=BIG, out=T_PLANNER - 0.1)


# ---------------------------------------------------------------- message it, or just talk

def talker_part(c, t):
    ringing = t >= T_MENTION
    solo(c, "talker", t, T_PLANNER, T_BUG - 0.15, 960, y=FLOOR - 20, size=470, happy=ringing)
    if T_ASK <= t < T_OR + 0.2:
        a = 1 - clamp((t - (T_OR - 0.15)) / 0.2)
        ui.bubble(c, t, T_ASK_ITEMS[0], 560, 330, "Slack", a=a)
        ui.bubble(c, t, T_ASK_ITEMS[1], 1350, 300, "", typing=True, a=a)
        ui.bubble(c, t, T_ASK_ITEMS[2], 1400, 470, "email", a=a)
        ui.bubble(c, t, T_ASK_ITEMS[3], 520, 520, "a text", a=a)
    if ringing:
        with G.layer(c, gone(t, T_BUG - 0.15)):
            ui.call(c, t, T_MENTION, 960, FLOOR - 190, r=230)
    line(c, t, "message it", T_ASK, y=TEXT_Y, size=BIG, out=T_OR - 0.1)
    line(c, t, "or just", T_OR, y=TEXT_Y, size=BIG, out=T_MENTION - 0.1)
    line(c, t, "talk.", T_MENTION, y=TEXT_Y, size=BIG, out=T_BUG - 0.1)


# ---------------------------------------------------------------- a bug, on it, feedback, tested fixes

CODE_X, CODE_Y = 600, 190


def bug_part(c, t):
    a = gone(t, T_REVIEW - 0.15)
    glow = clamp((t - (T_SQUASH + 0.15)) / 0.3)
    s = pop(t, T_BUG - 0.05, 0.3, 1.8) * a
    if s > 0.01:
        with G.xf(c, CODE_X + 310, CODE_Y + 220, s=s):
            c.translate(-310, -220)
            ui.code_card(c, 0, 0, glow=glow)
            if t < T_SQUASH + 0.35:
                tau = t - T_BUG
                bx = 150 + 300 * (0.5 + 0.5 * math.sin(0.9 * tau))
                by = 140 + 90 * math.sin(0.6 * tau + 1.0)
                sq = clamp((t - T_SQUASH) / 0.08)
                ui.bug(c, bx, by, 1.6, t if t < T_SQUASH else T_SQUASH, squash=sq,
                       a=1 - clamp((t - (T_SQUASH + 0.15)) / 0.2))
                if t >= T_SQUASH:
                    v = clamp((t - T_SQUASH) / 0.35)
                    for i in range(8):
                        ang = 2 * math.pi * i / 8
                        c.drawCircle(bx + math.cos(ang) * 60 * out_cubic(v), by + math.sin(ang) * 60 * out_cubic(v),
                                     7 * (1 - v), G.P("#ffb4a8", 1 - v))
            ui.check_badge(c, 600, 22, 26, pop(t, T_SQUASH + 0.2, 0.3, 2.6))
    if t >= T_ONIT - 0.05:                                               # the builder jumps in and lands on it
        u = clamp((t - (T_ONIT - 0.05)) / 0.45)
        x = lerp(1600, CODE_X + 480, out_cubic(u))
        y = lerp(FLOOR + 40, CODE_Y + 300, out_cubic(u))
        lift = 240 * math.sin(math.pi * u) if u < 1 else 0.0
        stomp = clamp(1 - abs(t - T_SQUASH) / 0.1)
        agent(c, "builder", x, y, 380, t, face("builder", t, happy=t >= T_SQUASH + 0.1, seed=11), s=a,
              lift=lift - 18 * stomp, squash=0.8 * stomp - (0.3 if 0.05 < u < 0.7 else 0.0), shadow_a=0.0)
    line(c, t, "a bug?", T_BUG, y=TEXT_Y, size=BIG, out=T_ONIT - 0.1)
    line(c, t, "on it.", T_ONIT, y=TEXT_Y, size=BIG, out=T_REVIEW - 0.1)


def feedback_part(c, t):
    a = gone(t, T_CI - 0.15)
    ui.feedback(c, t, T_REVIEW, 270, 230, a=max(0.0, a) * (1 - clamp((t - (T_TESTS - 0.1)) / 0.25)))
    x = lerp(900, 640, out_cubic(clamp((t - (T_TESTS - 0.1)) / 0.4)))
    ui.fixes(c, t, T_REVIEW + 0.1, x, 250, checked_from=T_TESTS + 0.1, a=max(0.0, a))
    solo(c, "builder", t, T_REVIEW + 0.2, T_CI - 0.15, x + 760, y=FLOOR - 80, size=360,
         happy=t >= T_TESTS + 0.5)
    line(c, t, "feedback.", T_REVIEW, y=TEXT_Y, size=BIG, out=T_TESTS - 0.1)
    line(c, t, "tested fixes.", T_TESTS, y=TEXT_Y, size=BIG, out=T_CI - 0.1)


# ---------------------------------------------------------------- new numbers, it reruns itself

def numbers_part(c, t):
    a = gone(t, T_OWL - 0.15)
    ui.chart(c, t, T_CI, 520, 200, rerun=T_GREEN + 0.05, a=max(0.0, a))
    solo(c, "reader", t, T_CI + 0.15, T_OWL - 0.15, 1420, y=FLOOR - 70, size=380, happy=t >= T_GREEN + 0.3)
    line(c, t, "new numbers?", T_CI, y=TEXT_Y, size=BIG, out=T_GREEN - 0.1)
    line(c, t, "reruns itself.", T_GREEN, y=TEXT_Y, size=BIG, out=T_OWL - 0.1)


# ---------------------------------------------------------------- while you sleep, it asks first, the rules

def night_part(c, t):
    night = clamp((t - (T_OWL + 0.45)) / 0.4)
    if t < T_ONE0:
        a = 1 - clamp((t - (T_ONE0 - 0.25)) / 0.2)
        if night < 1:
            ui.sun(c, 1660, 170, 46, t, a=a * (1 - night))
        if night > 0:
            with G.xf(c, 1660, 170, s=0.6 + 0.4 * out_back(night, 2.0)):
                ui.moon(c, 0, 0, 34, a=a * night)
    x = 960
    if t >= T_SLEEP - 0.3:
        x = lerp(960, 500, out_cubic(clamp((t - (T_SLEEP - 0.3)) / 0.4)))
    if t >= T_RULES2 - 0.2:
        x = lerp(500, 1480, out_cubic(clamp((t - (T_RULES2 - 0.2)) / 0.45)))
    asleep = T_SLEEP <= t < T_ASKS
    solo(c, "sleeper", t, T_OWL, T_ONE0 - 0.1, x, y=FLOOR - 20, size=470, asleep=asleep)
    if asleep:
        for k in range(3):                                               # zzz
            v = ((t - T_SLEEP) * 0.9 + k / 3) % 1
            T(c, "z", x + 150 + 60 * v, 420 - 120 * v, heavy(34 + 18 * v), "#4f5bd5", (1 - v) * 0.9)
    if T_SLEEP - 0.05 <= t < T_ASKS + 0.1:
        ui.job(c, t, T_SLEEP - 0.05, 830, 320, a=1 - clamp((t - (T_ASKS - 0.1)) / 0.2))
    if T_ASKS - 0.05 <= t < T_RULES2 + 0.1:
        ui.approval(c, t, T_ASKS - 0.05, T_CLICK, 830, 300, a=1 - clamp((t - (T_RULES2 - 0.1)) / 0.2))
    if t >= T_RULES2 - 0.05:
        ui.rules(c, t, T_RULES2 - 0.05, 520, 270, a=max(0.0, gone(t, T_ONE0 - 0.15)))
    line(c, t, "while you sleep", T_SLEEP, y=TEXT_Y, size=BIG, out=T_ASKS - 0.1)
    line(c, t, "it asks first.", T_ASKS, y=TEXT_Y, size=BIG, out=T_RULES2 - 0.1)
    line(c, t, "you set the rules.", T_CONTROL, y=TEXT_Y, size=BIG, out=T_ONE0 - 0.1)


# ---------------------------------------------------------------- one spark, a whole team

SLOTS = {"builder": -2, "talker": -1, "reader": 1, "sleeper": 2}


def team_part(c, t):
    if t < T_FIVE:
        big = lerp(440, 600, out_cubic(clamp((t - T_ONE) / 0.4)))
        solo(c, "lead", t, T_ONE0, T_TEAM - 0.1, 960, y=FLOOR + 10, size=big, happy=t >= T_ONE + 0.4)
    else:
        huddle = out_cubic(clamp((t - T_SUB) / 0.3))
        for n in ORDER:
            if n == "lead":
                size = lerp(lerp(600, 420, out_cubic(clamp((t - T_FIVE) / 0.3))), 330, huddle)
                agent(c, n, 960, FLOOR + 10, size, t, face(n, t, happy=True), s=gone(t, T_TEAM - 0.08))
                continue
            slot = SLOTS[n]
            k = ORDER.index(n)
            s = pop(t, T_FIVE + 0.06 * abs(slot), 0.3, 2.6) * gone(t, T_TEAM - 0.08 + 0.02 * abs(slot))
            x = 960 + slot * lerp(330, 270, huddle)
            agent(c, n, x, FLOOR - 10, lerp(360, 300, huddle), t, face(n, t, happy=t >= T_SUB, seed=k), s=s)
    if t >= T_TEAM - 0.05:                                               # a whole team: waves of them
        cols, rows = 9, 3
        for j in range(rows):
            for i in range(cols):
                n = ORDER[(i + 2 * j) % len(ORDER)]
                x = 960 + (i - (cols - 1) / 2) * 190 + (45 if j % 2 else -45)
                y = 360 + j * 200
                d = math.hypot(i - (cols - 1) / 2, (j - 1) * 1.5)
                s = pop(t, T_TEAM - 0.05 + 0.035 * d, 0.3, 2.6) * gone(t, T_END - 0.1 + 0.01 * d)
                lift, squash = hop(t, T_TEAM + 0.1 * hash01(i + 9 * j, 3), 0.5, 0.05)
                agent(c, n, x, y, 230, t, face(n, t, happy=(i + j) % 3 == 0, seed=i + 9 * j), s=s,
                      lift=lift * 230, squash=squash * 0.5)
    line(c, t, "one spark.", T_ONE, y=TEXT_Y, size=BIG, out=T_SUB - 0.1)
    line(c, t, "or", T_SUB, y=TEXT_Y, size=BIG, out=T_TEAM - 0.1)
    line(c, t, "a whole team.", T_TEAM, y=TEXT_Y, size=BIG, out=T_END - 0.1)


# ---------------------------------------------------------------- the end

def ending(c, t):
    wordmark(c, t, T_END, y=560, size=170)
    caption(c, t, "Your time, back.", T_TAG, 660, size=34, col="#5f5f68")
    u = clamp((t - T_NOTE) / 0.4)
    if u > 0:
        T(c, "A fan concept  ·  not affiliated with Anthropic", 960, 1010, sans(19, 500), "#9a9aa2", u, align=0.5)
    fade = clamp((t - (T_BLACK - 0.25)) / 0.25)
    if fade > 0:
        c.drawRect(skia.Rect.MakeWH(1920, 1080), G.P("#000000", fade))


def draw(c, t):
    if t < T_READER:
        opening(c, t)
    elif t < T_TESTER:
        lead_part(c, t)
    elif t < T_PLANNER:
        reader_part(c, t)
    elif t < T_BUG:
        talker_part(c, t)
    elif t < T_REVIEW:
        bug_part(c, t)
    elif t < T_CI:
        feedback_part(c, t)
    elif t < T_OWL:
        numbers_part(c, t)
    elif t < T_ONE0:
        night_part(c, t)
    elif t < T_END:
        team_part(c, t)
    elif t < T_BLACK:
        ending(c, t)


def preload():
    from .cast import shadow
    for n in ORDER:
        for v in ("open", CLOSED[n]):
            sprite(n, v)
        shadow(n)
