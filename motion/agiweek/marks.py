"""Brand marks for AGI WEEK. Claude, Gemini, Meta and X are the Simple Icons paths (CC0 path data on a 24-unit
grid); OpenAI comes from the engine's set; the Grok mark and Google's four-colour G are drawn here. The marks are
the companies' trademarks, shown in a fan-made news piece that names them; nothing here is official or endorsed."""
import math
from functools import lru_cache

import skia

from engine import gfx as G
from engine import logos as L

CLAUDE = (
    "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.121"
    "4-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.388"
    "6l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1"
    ".0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.1"
    "64-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6"
    "997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l."
    "1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.85"
    "17-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.03"
    "21l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 "
    "1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0"
    "607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.910"
    "7-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-"
    "1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.121"
    "4-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7"
    "468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.944"
    "6-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579"
    "h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"
)

META = (
    "M6.915 4.03c-1.968 0-3.683 1.28-4.871 3.113C.704 9.208 0 11.883 0 14.449c0 .706.07 1.369.21 1.973a6.624 6.62"
    "4 0 0 0 .265.86 5.297 5.297 0 0 0 .371.761c.696 1.159 1.818 1.927 3.593 1.927 1.497 0 2.633-.671 3.965-2.444"
    ".76-1.012 1.144-1.626 2.663-4.32l.756-1.339.186-.325c.061.1.121.196.183.3l2.152 3.595c.724 1.21 1.665 2.556 "
    "2.47 3.314 1.046.987 1.992 1.22 3.06 1.22 1.075 0 1.876-.355 2.455-.843a3.743 3.743 0 0 0 .81-.973c.542-.939"
    ".861-2.127.861-3.745 0-2.72-.681-5.357-2.084-7.45-1.282-1.912-2.957-2.93-4.716-2.93-1.047 0-2.088.467-3.053 "
    "1.308-.652.57-1.257 1.29-1.82 2.05-.69-.875-1.335-1.547-1.958-2.056-1.182-.966-2.315-1.303-3.454-1.303zm10.1"
    "6 2.053c1.147 0 2.188.758 2.992 1.999 1.132 1.748 1.647 4.195 1.647 6.4 0 1.548-.368 2.9-1.839 2.9-.58 0-1.0"
    "27-.23-1.664-1.004-.496-.601-1.343-1.878-2.832-4.358l-.617-1.028a44.908 44.908 0 0 0-1.255-1.98c.07-.109.141"
    "-.224.211-.327 1.12-1.667 2.118-2.602 3.358-2.602zm-10.201.553c1.265 0 2.058.791 2.675 1.446.307.327.737.871"
    " 1.234 1.579l-1.02 1.566c-.757 1.163-1.882 3.017-2.837 4.338-1.191 1.649-1.81 1.817-2.486 1.817-.524 0-1.038"
    "-.237-1.383-.794-.263-.426-.464-1.13-.464-2.046 0-2.221.63-4.535 1.66-6.088.454-.687.964-1.226 1.533-1.533a2"
    ".264 2.264 0 0 1 1.088-.285z"
)

GEMINI_SI = (
    "M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 "
    "12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0"
    " 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"
)

X = ("M14.234 10.162 22.977 0h-2.072l-7.591 8.824L7.251 0H.258l9.168 13.343L.258 24H2.33l8.016-9.318L16.749 24h6.993"
     "zm-2.837 3.299-.929-1.329L3.076 1.56h3.182l5.965 8.532.929 1.329 7.754 11.09h-3.182z")

_PATHS = {"claude": CLAUDE, "meta": META, "gemini": GEMINI_SI, "x": X}
GEMINI_GRAD = ["#3c78f0", "#6f86f5", "#b084e0"]
META_GRAD = ["#0064e0", "#0082fb"]
G_BLUE, G_RED, G_YELLOW, G_GREEN = "#4285f4", "#ea4335", "#fbbc05", "#34a853"


@lru_cache(maxsize=None)
def _path(name):
    if name in _PATHS:
        return G.svg_path(_PATHS[name])
    return L.path(name)


def mark(c, name, cx, cy, size, col="#ffffff", a=1.0, rot=0.0, shader=None):
    """A mark with its larger side `size` px, centred on (cx, cy)."""
    if name == "grok":
        grok(c, cx, cy, size, col, a, rot)
        return
    p = _path(name)
    b = p.getBounds()
    s = size / max(b.width(), b.height())
    c.save()
    c.translate(cx, cy)
    if rot:
        c.rotate(rot)
    c.scale(s, s)
    c.translate(-b.centerX(), -b.centerY())
    paint = G.P(col, a) if shader is None else G.P(col, a, shader=shader)
    c.drawPath(p, paint)
    c.restore()


def grok(c, cx, cy, size, col="#ffffff", a=1.0, rot=0.0):
    """The Grok mark: a thick ring, broken where a thin blade runs through it from lower left to upper right and out
    past both sides. The left arc runs into the blade low down, the right arc runs into it high up; the other two
    ends stop short of it."""
    R = size * 0.31
    w = size * 0.12
    c.save()
    c.translate(cx, cy)
    if rot:
        c.rotate(rot)
    box = skia.Rect.MakeLTRB(-R, -R, R, R)
    for start, sweep in ((318, 150), (132, 158)):
        arc = skia.Path()
        arc.addArc(box, start, sweep)
        c.drawPath(arc, G.P(col, a, stroke=w, cap="butt"))
    half = size * 0.5
    wmax = size * 0.024
    ux, uy = math.cos(math.radians(-45)), math.sin(math.radians(-45))
    nx, ny = -uy, ux
    ax, ay = -ux * half * 0.92, -uy * half * 0.92
    bx, by = ux * half * 0.94, uy * half * 0.94
    blade = skia.Path()
    blade.moveTo(ax, ay)
    blade.quadTo(nx * wmax * 2, ny * wmax * 2, bx, by)
    blade.quadTo(-nx * wmax * 2, -ny * wmax * 2, ax, ay)
    blade.close()
    c.drawPath(blade, G.P(col, a))
    c.restore()


def gemini(c, cx, cy, size, a=1.0, rot=0.0):
    """The Gemini sparkle in its blue-to-violet gradient."""
    h = size / 2
    mark(c, "gemini", cx, cy, size, a=a, rot=rot,
         shader=G.linear_grad(cx - h, cy + h, cx + h, cy - h, GEMINI_GRAD))


def meta(c, cx, cy, size, a=1.0):
    """The Meta infinity in its blue gradient."""
    h = size / 2
    mark(c, "meta", cx, cy, size, a=a, shader=G.linear_grad(cx - h, cy, cx + h, cy, META_GRAD))


def google_g(c, cx, cy, size, a=1.0, mono=None):
    """Google's G: a thick ring open at the upper right, a bar into the middle, in its four colours."""
    R = size * 0.5
    wd = size * 0.19
    rc = R - wd / 2
    box = skia.Rect.MakeLTRB(cx - rc, cy - rc, cx + rc, cy + rc)
    segs = [(G_RED, 216, 100), (G_YELLOW, 146, 70), (G_GREEN, 36, 110), (G_BLUE, -1, 38)]
    for col, start, sweep in segs:
        pth = skia.Path()
        pth.addArc(box, start, sweep)
        c.drawPath(pth, G.P(mono or col, a, stroke=wd, cap="butt"))
    c.drawRect(skia.Rect.MakeLTRB(cx - size * 0.02, cy - size * 0.05, cx + R, cy + wd - size * 0.05),
               G.P(mono or G_BLUE, a))


def mark_path(name, cx, cy, size, rot=0.0):
    """A mark's outline placed like mark() would draw it: larger side `size`, centred on (cx, cy), turned rot."""
    p = skia.Path(_path(name))
    b = p.getBounds()
    s = size / max(b.width(), b.height())
    m = skia.Matrix()
    m.setTranslate(-b.centerX(), -b.centerY())
    m.postScale(s, s)
    if rot:
        m.postRotate(rot)
    m.postTranslate(cx, cy)
    p.transform(m)
    return p
