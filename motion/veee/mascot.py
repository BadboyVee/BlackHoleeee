"""Vee, the film's mascot: a kid in a knitted beanie and round glasses, drawn in soft greys like a little 3D toy
and printed in 1-bit dots, the way the reference prints its own. He peeks in, winks, says psst, watches the cards
go by, and pokes his head up behind the wordmark at the end."""
from collections import OrderedDict

import skia

from engine import gfx as G
from .dither import Layer, draw_pixels

R = 200.0                      # head radius in his own units; the drawing spans about -300..300 x -330..720
BOX = (-330.0, -392.0, 660.0, 1132.0)


class Pose:
    def __init__(self, look=(0.0, 0.0), blink=0.0, wink=0.0, mouth="smile", tilt=0.0, talk=0.0):
        self.look, self.blink, self.wink, self.mouth, self.tilt, self.talk = look, blink, wink, mouth, tilt, talk


def _radial(cx, cy, r, stops, cols):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, [G.cint(c) for c in cols], stops)


def body(c):
    """The hoodie, the neck and the little V patch."""
    p = skia.Path()
    p.moveTo(-300, 740)
    p.lineTo(-292, 340)
    p.cubicTo(-286, 222, -170, 178, 0, 178)
    p.cubicTo(170, 178, 286, 222, 292, 340)
    p.lineTo(300, 740)
    p.close()
    c.drawPath(p, G.P("#a8a8a8", 1, shader=_radial(-110, 250, 560, [0, 0.5, 1], ["#f0f0f0", "#b8b8b8", "#7a7a7a"])))
    # the hood's collar
    col = skia.Path()
    col.addOval(skia.Rect.MakeLTRB(-150, 150, 150, 245))
    c.drawPath(col, G.P("#8a8a8a", 1, shader=_radial(-40, 170, 170, [0, 1], ["#c8c8c8", "#6e6e6e"])))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-62, 120, 62, 212), 30, 30),
                G.P("#dcdcdc", 1, shader=_radial(-20, 140, 110, [0, 1], ["#f4f4f4", "#b8b8b8"])))
    # drawstrings
    for sx in (-1, 1):
        c.drawLine(sx * 40, 232, sx * 52, 330, G.P("#1c1c1c", 1, stroke=7, cap="round"))
        c.drawCircle(sx * 52, 336, 9, G.P("#1c1c1c"))
    # the patch
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(88, 420, 96, 96), 10, 10), G.P("#f2f2f2"))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(88, 420, 96, 96), 10, 10), G.P("#141414", 1, stroke=6))
    v = skia.Path()
    v.moveTo(110, 444)
    v.lineTo(136, 494)
    v.lineTo(162, 444)
    c.drawPath(v, G.P("#141414", 1, stroke=11, cap="round", join="round"))


def head(c, pose):
    lx, ly = pose.look
    # ears
    for sx in (-1, 1):
        c.drawCircle(sx * 196, 30, 40, G.P("#d8d8d8", 1, shader=_radial(sx * 186, 18, 50, [0, 1], ["#f6f6f6", "#b4b4b4"])))
    # the face
    c.drawCircle(0, 0, R, G.P("#eeeeee", 1, shader=_radial(-70, -60, 290, [0, 0.5, 0.82, 1],
                                                           ["#ffffff", "#f7f7f7", "#dedede", "#bcbcbc"])))
    # cheeks
    for sx in (-1, 1):
        c.drawCircle(sx * 124, 92, 34, G.P("#c6c6c6", 0.9, blur=6))
    # the beanie: a knitted dome and a ribbed cuff
    dome = skia.Path()
    dome.moveTo(-214, -60)
    dome.cubicTo(-214, -250, -120, -318, 0, -318)
    dome.cubicTo(120, -318, 214, -250, 214, -60)
    dome.close()
    c.drawPath(dome, G.P("#707070", 1, shader=_radial(-80, -250, 320, [0, 0.55, 1], ["#c4c4c4", "#7a7a7a", "#444444"])))
    for k in range(-5, 6):                                   # knit lines on the dome
        x = k * 38
        ln = skia.Path()
        ln.moveTo(x * 1.05, -70)
        ln.quadTo(x * 0.9, -220, x * 0.45, -300)
        c.drawPath(ln, G.P("#303030", 0.5, stroke=6))
    cuff = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-226, -118, 226, -40), 30, 30)
    c.drawRRect(cuff, G.P("#5a5a5a", 1, shader=_radial(-70, -100, 320, [0, 1], ["#a8a8a8", "#454545"])))
    c.save()
    c.clipRRect(cuff, True)
    for k in range(-13, 14):
        c.drawRect(skia.Rect.MakeXYWH(k * 17 - 3, -120, 7, 82), G.P("#262626", 0.7))
    c.restore()
    # the pompom
    c.drawCircle(0, -326, 46, G.P("#7a7a7a", 1, shader=_radial(-16, -344, 64, [0, 1], ["#d0d0d0", "#4a4a4a"])))
    # glasses and eyes
    for sx in (-1, 1):
        ex, ey = sx * 80, 24
        c.drawCircle(ex, ey, 60, G.P("#f7f7f7", 0.55))
        wink = pose.wink if sx == 1 else 0.0
        shut = max(pose.blink, wink)
        if shut < 0.5:
            c.drawOval(skia.Rect.MakeXYWH(ex + lx - 24, ey + ly - 30 * (1 - shut), 48, 60 * (1 - shut)), G.P("#0c0c0c"))
            c.drawCircle(ex + lx - 8, ey + ly - 12, 8, G.P("#ffffff"))
        else:
            arc = skia.Path()
            arc.addArc(skia.Rect.MakeXYWH(ex - 26, ey - 18, 52, 40), 200, 140)
            c.drawPath(arc, G.P("#0c0c0c", 1, stroke=10, cap="round"))
        c.drawCircle(ex, ey, 60, G.P("#141414", 1, stroke=11))
    c.drawLine(-22, 18, 22, 18, G.P("#141414", 1, stroke=10, cap="round"))
    # the mouth
    if pose.mouth == "o" or pose.talk > 0.5:
        c.drawOval(skia.Rect.MakeXYWH(-18, 104, 36, 40), G.P("#0c0c0c"))
    else:
        m = skia.Path()
        m.moveTo(-56, 110)
        m.quadTo(0, 124, 56, 110)
        m.quadTo(40, 164, 0, 166)
        m.quadTo(-40, 164, -56, 110)
        m.close()
        c.drawPath(m, G.P("#0c0c0c"))
        c.save()
        c.clipPath(m, doAntiAlias=True)
        c.drawOval(skia.Rect.MakeXYWH(-24, 146, 48, 28), G.P("#5e5e5e"))
        c.restore()


def draw(c, pose):
    body(c)
    with G.xf(c, 0, 0, rot=pose.tilt, px=0, py=160):
        head(c, pose)


class Vee:
    """Renders him through a dither layer at a given on-screen scale; cell is the size of one dot in pixels."""

    def __init__(self, cell=4):
        self.cell = cell
        self._layers = OrderedDict()           # a few sizes at a time: he grows and shrinks from frame to frame

    def layer(self, w, h):
        key = (w, h)
        lay = self._layers.get(key)
        if lay is None:
            lay = self._layers[key] = Layer(w, h)
            if len(self._layers) > 8:
                self._layers.popitem(last=False)
        else:
            self._layers.move_to_end(key)
        return lay

    def __call__(self, c, x, y, scale, pose, crop=None):
        """Draw him with his head centre at (x, y), `scale` screen pixels per unit."""
        bx, by, bw, bh = BOX
        k = scale / self.cell
        w, h = max(1, int(bw * k)), max(1, int(bh * k))
        img = self.layer(w, h).render(lambda cc: (cc.scale(k, k), cc.translate(-bx, -by), draw(cc, pose)))
        sx = int(round(x + bx * scale))
        sy = int(round(y + by * scale))
        if crop is not None:
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(*crop))
        draw_pixels(c, img, sx, sy, self.cell)
        if crop is not None:
            c.restore()


VEE = Vee()
VEE_FINE = Vee(cell=2)                     # for the small ones: the phone's avatar, the brief's thumbnail
