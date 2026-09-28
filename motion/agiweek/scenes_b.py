"""OpenAI, the race (Gemini and Muse) and xAI."""
import math

import skia

from engine import gfx as G
from engine.core import clamp, lerp, out_cubic, out_expo, spring
from . import marks as M
from . import motion as V
from .look import (BRANDS, BLACK, WHITE, GREY, T, ui, rr, ground, blob, chip, eyebrow, press_of, panel, chevron,
                   arrow_up, roll_digit, GEMINI_GRAD)
from .score import (T_OAI, T_OAI_TYPE, T_OAI_SEND, T_AGENT, T_OAI_FOUNDER, T_RACE, T_RACE_FOUNDERS,
                    T_XAI, T_ROLL, T_XAI_FOUNDER)

OAI_INK = "#0d0d0d"
OAI_SUB = "#6e6e80"
AGENT_GRAD = ["#10a37f", "#4f7cff"]


# ---------------------------------------------------------------- 4 OpenAI

def openai(c, t):
    ground(c, "#ffffff", "#f3f3f5")
    blob(c, 1400, 300, 800, "#e9ecf5", 0.8)
    eyebrow(c, "openai", 120, 150, t, T_OAI + 0.05, OAI_INK, status="DEVDAY · TOMORROW", status_fill=OAI_INK,
            status_ink=WHITE, dot=WHITE, mark_col=OAI_INK)
    V.mask_rise(c, "New model", 112, 390, 150, OAI_INK, t, T_OAI + 0.2, w0=150, w1=780, tr0=0.1, tr1=-0.02)
    agent_line(c, t)
    V.words_rise(c, [(T_OAI + 0.9 + 0.06 * k, w) for k, w in enumerate("Both expected this week.".split(" "))],
                 120, 640, 38, OAI_SUB, t, w0=250, w1=460)
    composer(c, t)
    agent_card(c, t)
    V.founder(c, "altman", 220, 860, 200, t, T_OAI_FOUNDER, ring=OAI_INK, text_col=OAI_INK, sub_col=OAI_SUB)


def agent_line(c, t):
    t0 = T_OAI + 0.45
    size = 110
    s = "+ Agent “O”"
    V.mask_rise(c, s, 116, 530, size, OAI_INK, t, t0, w0=150, w1=760, stagger=0.03, tr0=0.08)
    # the O is an agent loop: a ring draws round it, then an arc of colour runs laps
    f = V.vfont("inter", size, 760)
    run = f.shape(s, -0.01)
    i = s.index("O", s.index("“"))
    if i < len(run.xs) and t >= t0 + 0.35:
        cx, cy = 116 + run.xs[i] + run.adv[i] / 2, 530 - f.cap / 2
        r = f.cap * 0.74
        u = clamp((t - t0 - 0.35) / 0.5)
        ring = skia.Path()
        ring.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), -90, 359.9)
        V.trim_stroke(c, ring, out_cubic(u), OAI_INK, 5, a=0.18)
        spin = (t - t0) * 320
        arc = G.arc_path(cx, cy, r, spin - 90, 40 + 80 * out_cubic(u))
        c.drawPath(arc, G.P(OAI_INK, u, stroke=6, cap="round",
                            shader=G.linear_grad(cx - r, cy, cx + r, cy, AGENT_GRAD)))


def composer(c, t):
    x, y, w, h = 990, 290, 830, 196
    u = V.swing_in(t, T_OAI + 0.3, 2.2, 0.62)
    if u <= 0:
        return
    c.save()
    V.tilt(c, x + w / 2, y + h / 2, rx=12 * (1 - u), ry=30 * (1 - u))
    with G.xf(c, 0, 110 * (1 - u) + V.float_y(t, 1.1, 3)):
        panel(c, x, y, w, h, 34, WHITE, a=clamp(u * 2), shadow=0.1, rim=("#000000", 0.1))
        prompt = "What are you launching at DevDay?"
        k = clamp((t - T_OAI_TYPE[0]) / (T_OAI_TYPE[1] - T_OAI_TYPE[0]))
        n = int(len(prompt) * k)
        fp = ui(30, 450)
        lift = out_expo(clamp((t - T_OAI_SEND - 0.05) / 0.35))
        if n == 0 or lift >= 1:
            T(c, "Ask anything", x + 36, y + 64, fp, "#9a9aa6", a=1.0 if n == 0 else clamp((t - T_OAI_SEND - 0.3) / 0.2))
        if 0 < n and lift < 1:
            # the message lifts off the field when it's sent
            T(c, prompt[:n], x + 36, y + 64 - 70 * lift, fp, OAI_INK, a=1 - lift)
            if t < T_OAI_SEND and int(t * 3) % 2 == 0:
                c.drawRect(skia.Rect.MakeXYWH(x + 38 + fp.width(prompt[:n]), y + 36, 3, 38), G.P(OAI_INK))
        G.circle(c, x + 56, y + 146, 22, G.P("#000000", 1, stroke=1.4))
        c.drawLine(x + 48, y + 146, x + 64, y + 146, G.P(OAI_INK, 1, stroke=2.4, cap="round"))
        c.drawLine(x + 56, y + 138, x + 56, y + 154, G.P(OAI_INK, 1, stroke=2.4, cap="round"))
        fb = ui(22, 600)
        label = "New model"
        bw = fb.width(label) + 84
        c.drawRRect(rr(x + 94, y + 124, bw, 44, 22), G.P("#f1f1f3"))
        T(c, label, x + 116, y + 154, fb, OAI_INK)
        qx = x + 116 + fb.width(label) + 20
        pulse = 1 + 0.15 * math.sin(t * 8)
        with G.xf(c, qx, y + 146, s=pulse):
            G.circle(c, 0, 0, 11, G.P(OAI_INK))
            T(c, "?", 0, 7, ui(16, 800), WHITE, align=0.5)
        chevron(c, x + 94 + bw - 20, y + 146, 12, OAI_INK)
        pr = press_of(t, [T_OAI_SEND])
        sx, sy = x + w - 60, y + 146
        with G.xf(c, sx, sy, s=1 - 0.14 * pr):
            G.circle(c, 0, 0, 26, G.P(OAI_INK if n > 0 else "#d9d9de"))
            arrow_up(c, 0, 0 - 8 * pr, 22, WHITE)
        V.shockwave(c, sx, sy, t, T_OAI_SEND, OAI_INK, r0=26, r1=90, dur=0.45, width=3, a=0.5)
    c.restore()


def agent_card(c, t):
    if t < T_AGENT:
        return
    x, y, w, h = 990, 526, 830, 250
    grow = out_expo(clamp((t - T_AGENT) / 0.5))
    a = clamp((t - T_AGENT) / 0.15)
    hh = 84 + (h - 84) * grow
    with G.xf(c, 0, 40 * (1 - spring(t - T_AGENT, 2.4, 0.6))):
        panel(c, x, y, w, hh, 30, WHITE, a=a, shadow=0.1, rim=("#000000", 0.1))
        with G.clip_rect(c, x, y, w, hh):
            cx, cy = x + 60, y + 62
            G.circle(c, cx, cy, 22, G.P("#0d0d0d", a * 0.15, stroke=3))
            spin = (t - T_AGENT) * 360
            c.drawPath(G.arc_path(cx, cy, 22, spin, 110), G.P(OAI_INK, a, stroke=5, cap="round",
                                                             shader=G.linear_grad(cx - 22, 0, cx + 22, 0, AGENT_GRAD)))
            V.mask_rise(c, "Agent “O”", x + 100, y + 73, 32, OAI_INK, t, T_AGENT + 0.05, w0=300, w1=650,
                        stagger=0.015, dur=0.4, tr0=0.04)
            v = clamp((t - T_AGENT - 0.25) / 0.3)
            with G.xf(c, x + 100 + ui(32, 650).width("Agent “O”") + 20, y + 62, s=0.7 + 0.3 * V.overshoot(v, 2.2)):
                chip(c, 0, 0, "RUMOURED", OAI_SUB, WHITE, a=a * v, size=15)
            dots = "." * (int((t - T_AGENT) * 5) % 4)
            T(c, "Working" + dots, x + w - 170, y + 73, ui(24, 500), OAI_SUB, a=a * v)
            for k, lw in enumerate((0.86, 0.72, 0.54)):
                ly = y + 120 + 38 * k
                bw = (w - 120) * lw * out_expo(clamp((t - T_AGENT - 0.2 - 0.08 * k) / 0.5))
                if bw <= 1:
                    continue
                c.drawRRect(rr(x + 60, ly, bw, 16, 8), G.P("#ececf0", a))
                sh = ((t - T_AGENT) * 1.3 + k * 0.2) % 1.6 - 0.3
                sx = x + 60 + bw * sh
                with G.clip_rect(c, x + 60, ly, bw, 16):
                    c.drawRect(skia.Rect.MakeXYWH(sx - 90, ly, 180, 16),
                               G.P(WHITE, a, shader=G.linear_grad(sx - 90, 0, sx + 90, 0,
                                                                  ["#ececf0", "#ffffff", "#ececf0"])))


# ---------------------------------------------------------------- 5 also in the race: Gemini and Muse

def race(c, t):
    # left: Google DeepMind on white; right: Meta in blue
    c.drawRect(skia.Rect.MakeXYWH(0, 0, 960, 1080), G.P("#ffffff"))
    glows = (("#4285f4", 240, 260, 520), ("#9b72cb", 640, 760, 560), ("#d96570", 180, 900, 420))
    for k, (col, x, y, r) in enumerate(glows):
        blob(c, x + 40 * math.sin(t + k), y + 30 * math.cos(t * 0.8 + k), r, col, 0.16)
    slide = out_expo(clamp((t - T_RACE + 0.2) / 0.45))
    rx = 960 + 960 * (1 - slide)
    c.drawRect(skia.Rect.MakeXYWH(rx, 0, 960, 1080), G.P("#1a86ff", 1, shader=G.linear_grad(0, 0, 0, 1080,
                                                                                        ["#1a86ff", "#0048b8"])))
    blob(c, rx + 700 + 60 * math.sin(t * 0.7), 250, 520, "#6fb6ff", 0.35)
    # a line of light runs down the seam
    k = clamp((t - T_RACE) / 0.6)
    if k > 0:
        c.drawLine(rx, 0, rx, 1080 * out_expo(k), G.P(WHITE, 0.9, stroke=3))
        c.drawLine(rx, 0, rx, 1080 * out_expo(k), G.P("#9cc8ff", 0.5, stroke=26, blur=16))
    u = clamp((t - T_RACE - 0.1) / 0.3)
    if u > 0:
        with G.xf(c, 960, 120, s=0.6 + 0.4 * V.overshoot(u, 2.2)):
            c.drawRRect(rr(-190, -34 + 8, 380, 68, 34), G.P("#000000", 0.18 * u, blur=14))
            chip(c, 0, 0, "ALSO IN THE RACE", "#111114", WHITE, a=u, size=24, align=0.5)
    _lab(c, t, "google", 480, T_RACE + 0.15, "#1f1f1f", "#5f6368")
    _lab(c, t, "meta", rx + 480, T_RACE + 0.3, WHITE, "#d6e6ff")
    V.founder(c, "hassabis", 290, 880, 190, t, T_RACE_FOUNDERS, ring="#4285f4", text_col="#1f1f1f",
              sub_col="#5f6368")
    V.founder(c, "zuckerberg", rx + 290, 880, 190, t, T_RACE_FOUNDERS + 0.12, ring=WHITE, text_col=WHITE,
              sub_col="#d6e6ff")


def _lab(c, t, key, cx, t0, ink, sub):
    b = BRANDS[key]
    u = clamp((t - t0) / 0.5)
    if u <= 0:
        return
    s = spring(t - t0, 2.4, 0.5)
    size = 230
    my = 340
    c.save()
    if key == "google":
        # the sparkle spins in, its gradient turning
        ang = -45 + 30 * math.sin((t - t0) * 1.6)      # the gradient sways but stays blue to violet
        r = size / 2
        sh = G.linear_grad(cx + math.cos(math.radians(ang)) * r, my + math.sin(math.radians(ang)) * r,
                           cx - math.cos(math.radians(ang)) * r, my - math.sin(math.radians(ang)) * r, GEMINI_GRAD)
        with G.xf(c, cx, my, s=0.3 + 0.7 * s, rot=-180 * (1 - out_expo(u))):
            M.mark(c, "gemini", 0, 0, size, a=u, shader=sh)
        V.burst(c, cx, my, t, t0 + 0.15, n=20, cols=("#4285f4", "#9b72cb", "#d96570"), speed=700, life=0.8, size=4,
                seed=31, gravity=200)
    else:
        # the infinity flips round like a coin
        V.tilt(c, cx, my, ry=90 * (1 - out_expo(u)))
        with G.xf(c, cx, my, s=0.5 + 0.5 * s):
            M.mark(c, "meta", 0, 0, size, WHITE, u)
    c.restore()
    fm = V.vfont("inter", 170, 780)
    v_t0 = t0 + 0.25
    if t >= v_t0:
        wdt = fm.width(b["model"], -0.01)
        if key == "google":
            sh = G.linear_grad(cx - wdt / 2 - 200 + 200 * math.sin(t * 1.4), 0, cx + wdt / 2 + 200, 0, GEMINI_GRAD)
            V.mask_rise(c, b["model"], cx, 650, 170, WHITE, t, v_t0, w0=200, w1=780, align=0.5, shader=sh)
        else:
            V.mask_rise(c, b["model"], cx, 650, 170, ink, t, v_t0, w0=200, w1=780, align=0.5)
        v = clamp((t - v_t0 - 0.3) / 0.35)
        if v > 0:
            T(c, b["company"].upper(), cx, 715 + 10 * (1 - out_cubic(v)), ui(24, 650), sub, a=v, align=0.5,
              tracking=lerp(0.5, 0.2, out_expo(v)))


# ---------------------------------------------------------------- 6 xAI: Grok 4.8, maybe

def grok_draw(c, cx, cy, size, u, col=WHITE, a=1.0, rot=0.0):
    """The Grok mark drawing itself on: the arcs trace round, then the slash cuts through."""
    if u <= 0 or a <= 0:
        return
    if u >= 1:
        M.mark(c, "grok", cx, cy, size, col, a, rot=rot)
        return
    R = size * 0.36
    w = size * 0.085
    with G.xf(c, cx, cy, rot=rot):
        ring = skia.Path()
        ring.addArc(skia.Rect.MakeLTRB(-R, -R, R, R), -20, 205)
        V.trim_stroke(c, ring, clamp(u * 1.4), col, w, a=a, cap="butt")
        ring2 = skia.Path()
        ring2.addArc(skia.Rect.MakeLTRB(-R, -R, R, R), 212, 70)
        V.trim_stroke(c, ring2, clamp(u * 1.6 - 0.3), col, w, a=a, cap="butt")
        v = out_expo(clamp((u - 0.55) / 0.45))
        if v > 0:
            d = size * 0.5
            ang = math.radians(-50)
            x0, y0 = -math.cos(ang) * d, -math.sin(ang) * d
            x1, y1 = lerp(x0, math.cos(ang) * d * 1.02, v), lerp(y0, math.sin(ang) * d * 1.02, v)
            nx, ny = -math.sin(ang), math.cos(ang)
            t1 = w * 0.62 * v
            p = skia.Path()
            p.moveTo(x0, y0)
            p.lineTo(x1 + nx * t1, y1 + ny * t1)
            p.lineTo(x1 - nx * t1, y1 - ny * t1)
            p.close()
            c.drawPath(p, G.P(col, a))


def xai(c, t):
    ground(c, BLACK)
    blob(c, 1450, 540, 700, "#1a1a22", 0.8)
    grok_draw(c, 1500, 560, 900, clamp((t - T_XAI) / 0.9), WHITE, 0.06, rot=(t - T_XAI) * 6)
    eyebrow(c, "xai", 120, 150, t, T_XAI + 0.05, WHITE, status="MIGHT DROP THIS WEEK", status_fill=WHITE,
            status_ink=WHITE, outline=True)
    size = 210
    t0 = T_XAI + 0.2
    wd = V.mask_rise(c, "Grok 4.", 112, 470, size, WHITE, t, t0, w0=150, w1=800, stagger=0.035, tr0=0.1)
    f = V.vfont("inter", size, 800)
    u = clamp((t - t0 - 0.25) / 0.4)
    if u > 0:
        x = 112 + wd
        if t < T_ROLL:
            V.mask_rise(c, "7", x, 470, size, WHITE, t, t0 + 0.2, w0=150, w1=800)
        else:
            k = clamp((t - T_ROLL) / 0.35)
            glitch = math.exp(-(t - T_ROLL) / 0.14)
            if glitch > 0.05:
                # the new digit tears in: colour-split copies and slices knocked sideways
                T(c, "8", x + 16 * glitch, 470, f, "#ff2d55", a=0.65 * glitch)
                T(c, "8", x - 16 * glitch, 470, f, "#2de2ff", a=0.65 * glitch)
                for s in range(5):
                    off = 40 * glitch * math.sin(s * 12.7 + t * 90)
                    with G.clip_rect(c, x - 20, 470 - f.cap + s * f.cap / 5, 220, f.cap / 5):
                        T(c, "8", x + off, 470, f, WHITE, a=glitch)
            roll_digit(c, "7", "8", k, x, 470, f, WHITE)
    v_t0 = T_ROLL + 0.25
    V.words_rise(c, [(v_t0 + 0.05 * k, w) for k, w in enumerate("Expected after 4.7’s rough reviews.".split(" "))],
                 120, 560, 38, GREY, t, w0=250, w1=460)
    grok_composer(c, t)
    V.founder(c, "musk", 220, 860, 200, t, T_XAI_FOUNDER, ring=WHITE, text_col=WHITE, sub_col=GREY)


def grok_composer(c, t):
    u = V.swing_in(t, T_XAI + 0.35, 2.2, 0.62)
    if u <= 0:
        return
    cx = 1405
    c.save()
    V.tilt(c, cx, 420, rx=-16 * (1 - u), ry=26 * (1 - u))
    with G.xf(c, 0, 100 * (1 - u) + V.float_y(t, 2.0, 3)):
        a = clamp(u * 2)
        grok_draw(c, cx - 90, 330, 64, clamp((t - T_XAI - 0.4) / 0.6), WHITE, a)
        V.mask_rise(c, "Grok", cx - 44, 352, 64, WHITE, t, T_XAI + 0.5, w0=200, w1=560, stagger=0.03, dur=0.4)
        x, y, w, h = 990, 420, 830, 104
        c.drawRRect(rr(x, y, w, h, h / 2), G.P("#141416", a))
        c.drawRRect(rr(x, y, w, h, h / 2), G.P("#2c2c31", a, stroke=1.6))
        V.glint(c, rr(x, y, w, h, h / 2), t, T_XAI + 0.7, dur=0.8, a=0.18)
        prompt = "Is 4.8 dropping this week?"
        k = clamp((t - T_XAI - 0.9) / 1.0)
        n = int(len(prompt) * k)
        fp = ui(28, 450)
        if n == 0:
            T(c, "What do you want to know?", x + 44, y + 62, fp, "#6c6c74", a=a)
        else:
            T(c, prompt[:n], x + 44, y + 62, fp, WHITE, a=a)
            if k < 1 and int(t * 3) % 2 == 0:
                c.drawRect(skia.Rect.MakeXYWH(x + 46 + fp.width(prompt[:n]), y + 34, 3, 36), G.P(WHITE, a))
        fb = ui(22, 600)
        c.drawRRect(rr(x + w - 230, y + 30, 110, 44, 22), G.P("#232327", a))
        T(c, "Auto", x + w - 208, y + 60, fb, WHITE, a=a)
        chevron(c, x + w - 138, y + 52, 11, WHITE, a=a)
        G.circle(c, x + w - 58, y + 52, 26, G.P(WHITE, a))
        arrow_up(c, x + w - 58, y + 52, 22, "#0b0b0c", a=a)
    c.restore()
