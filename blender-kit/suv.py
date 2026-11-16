"""A boxy long-wheelbase 4x4 station wagon (generic expedition truck), built from
code with a real cabin so passengers show through the glass.

Local frame: +X forward, +Y left, Z up, ground at z=0, origin under the centre.
    c = suv.build("truck", paint=(0.62, 0.5, 0.33), rack=True)   -> collection
    suv.SEATS["driver"]  -> (x, y, z_floor) hip reference for a seated figure
"""
import math
import os
import random

import bpy
from mathutils import Matrix, Vector

import kit
from kit import MB

HW = 0.95                 # half width at the belt line
HR = 0.80                 # half width at the roof
AX_F, AX_R = 1.45, -1.35  # axle x positions
TR = 0.41                 # tyre radius
TW = 0.27                 # tyre width
TRACK = 0.80              # wheel centre |y|
ZS, ZB, ZR_ = 0.50, 1.22, 1.92     # sill, belt line, roof
FLOOR = 0.60
ARCH = 0.53

SEATS = {
    "driver": (0.12, 0.42), "front": (0.12, -0.42),
    "rear_l": (-0.82, 0.50), "rear_c": (-0.82, 0.0), "rear_r": (-0.82, -0.50),
}
SEAT_TOP = 0.90


def _mats(paint, dusty):
    M = {}
    key = "_".join(f"{c:.2f}" for c in paint) + ("d" if dusty else "")
    name = "suv_paint_" + key
    if name in kit._mats:
        body = kit._mats[name]
    else:
        body, nt, b, out = kit._new(name)
        b.inputs["Base Color"].default_value = tuple(paint) + (1,)
        b.inputs["Roughness"].default_value = 0.32
        b.inputs["Metallic"].default_value = 0.0
        b.inputs["Coat Weight"].default_value = 0.9
        b.inputs["Coat Roughness"].default_value = 0.06
        if dusty:        # sand dust: heavy low down, fading up the body, broken up by noise
            N, L = nt.nodes, nt.links
            tc = N.new("ShaderNodeTexCoord")
            sep = N.new("ShaderNodeSeparateXYZ")
            L.new(tc.outputs["Object"], sep.inputs[0])
            mr = N.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = 1.35
            mr.inputs["From Max"].default_value = 0.45
            mr.inputs["To Min"].default_value = 0.0
            mr.inputs["To Max"].default_value = 1.0
            L.new(sep.outputs["Z"], mr.inputs["Value"])
            nz = N.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 7.0
            nz.inputs["Detail"].default_value = 6.0
            L.new(tc.outputs["Object"], nz.inputs["Vector"])
            mul = N.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            L.new(mr.outputs[0], mul.inputs[0])
            L.new(nz.outputs[0], mul.inputs[1])
            cr = N.new("ShaderNodeValToRGB")
            cr.color_ramp.elements[0].position = 0.18
            cr.color_ramp.elements[1].position = 0.62
            L.new(mul.outputs[0], cr.inputs[0])
            mx = N.new("ShaderNodeMix")
            mx.data_type = "RGBA"
            L.new(cr.outputs[0], mx.inputs["Factor"])
            mx.inputs["A"].default_value = tuple(paint) + (1,)
            mx.inputs["B"].default_value = (0.55, 0.42, 0.27, 1)
            L.new(mx.outputs["Result"], b.inputs["Base Color"])
            m2 = N.new("ShaderNodeMapRange")
            m2.inputs["To Min"].default_value = 0.32
            m2.inputs["To Max"].default_value = 0.9
            L.new(cr.outputs[0], m2.inputs["Value"])
            L.new(m2.outputs[0], b.inputs["Roughness"])
            m3 = N.new("ShaderNodeMapRange")
            m3.inputs["To Min"].default_value = 0.9
            m3.inputs["To Max"].default_value = 0.0
            L.new(cr.outputs[0], m3.inputs["Value"])
            L.new(m3.outputs[0], b.inputs["Coat Weight"])
        kit._mats[name] = body
    M["body"] = body
    M["black"] = kit.mat_plain("suv_plastic", (0.025, 0.025, 0.027), rough=0.6)
    M["rubber"] = kit.mat_plain("suv_rubber", (0.022, 0.022, 0.022), rough=0.82) if not dusty else \
        kit.mat_plain("suv_rubber_dusty", (0.07, 0.06, 0.05), rough=0.92)
    M["steel"] = kit.mat_plain("suv_steel", (0.5, 0.5, 0.5), rough=0.3, metal=1.0)
    M["chrome"] = kit.mat_plain("suv_chrome", (0.85, 0.85, 0.85), rough=0.08, metal=1.0)
    M["rim"] = kit.mat_plain("suv_rim", (0.55, 0.55, 0.56), rough=0.32, metal=1.0)
    M["glass"] = kit.mat_glass("suv_glass", tint=(0.78, 0.86, 0.84), darkness=0.9)
    M["lens"] = kit.mat_glass("suv_lens", tint=(0.95, 0.95, 0.95))
    M["red"] = kit.mat_plain("suv_tail", (0.5, 0.01, 0.01), rough=0.15, spec=0.8, emit=(1, 0.02, 0.02), emit_strength=0.4)
    M["amber"] = kit.mat_plain("suv_amber", (0.9, 0.35, 0.02), rough=0.15, spec=0.8)
    M["lamp"] = kit.mat_plain("suv_lamp", (0.75, 0.75, 0.72), rough=0.12, metal=1.0, emit=(1, 0.95, 0.85), emit_strength=0.12)
    M["lampface"] = kit.mat_plain("suv_lampface", (0.8, 0.82, 0.8), rough=0.08, metal=0.85, spec=1.0, coat=1.0,
                                  emit=(1, 0.97, 0.9), emit_strength=0.25)
    M["seat"] = kit.mat_plain("suv_seat", (0.09, 0.08, 0.07), rough=0.7)
    M["dash"] = kit.mat_plain("suv_dash", (0.04, 0.04, 0.045), rough=0.55)
    M["plate"] = kit.mat_plain("suv_plate", (0.9, 0.9, 0.85), rough=0.4)
    M["can"] = kit.mat_plain("suv_jerry", (0.2, 0.24, 0.13), rough=0.5)
    M["case"] = kit.mat_plain("suv_case", (0.06, 0.06, 0.06), rough=0.5)
    M["canvas"] = kit.mat_plain("suv_canvas", (0.45, 0.36, 0.22), rough=0.9)
    M["ladder"] = kit.mat_plain("suv_sandladder", (0.03, 0.03, 0.032), rough=0.55)
    M["well"] = kit.mat_plain("suv_well", (0.012, 0.012, 0.012), rough=0.9)
    return M


DECALS = "/home/user/assets/decals"


def _font(size):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def decal_material(name, kind, text):
    """A small generated texture (number plate or door graphic) as a material."""
    from PIL import Image, ImageDraw
    key = "decal_" + name
    if key in kit._mats:
        return kit._mats[key]
    os.makedirs(DECALS, exist_ok=True)
    path = os.path.join(DECALS, name + ".png")
    if kind == "plate":
        im = Image.new("RGBA", (520, 120), (238, 238, 232, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([3, 3, 516, 116], outline=(20, 20, 20, 255), width=5)
        f = _font(78)
        w = d.textlength(text, font=f)
        d.text(((520 - w) / 2, 14), text, font=f, fill=(15, 15, 15, 255))
    else:
        im = Image.new("RGBA", (1024, 420), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i, col in enumerate([(196, 78, 24, 255), (226, 150, 40, 255), (60, 50, 44, 255)]):
            d.polygon([(30 + i * 34, 300 + i * 26), (990, 300 + i * 26), (960, 318 + i * 26), (0 + i * 34, 318 + i * 26)], fill=col)
        d.ellipse([40, 30, 250, 240], outline=(40, 34, 30, 255), width=10)
        d.polygon([(145, 46), (165, 135), (145, 224), (125, 135)], fill=(196, 78, 24, 255))
        d.polygon([(56, 135), (145, 118), (234, 135), (145, 152)], fill=(40, 34, 30, 255))
        f1, f2 = _font(78), _font(42)
        lines = text.split("|")
        d.text((282, 52), lines[0], font=f1, fill=(40, 34, 30, 255))
        if len(lines) > 1:
            d.text((294, 150), lines[1], font=f2, fill=(196, 78, 24, 255))
    im.save(path)
    m, nt, b, out = kit._new(key)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    t.extension = "CLIP"
    nt.links.new(t.outputs[0], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.4
    kit._mats[key] = m
    return m


def _arc(cx, r, n=14, z0=ZS, cz=TR):
    """Wheel-arch points from the rear foot to the front foot (x ascending)."""
    a0 = math.acos(max(-1, min(1, (z0 - cz) / r)))
    out = []
    for i in range(n + 1):
        a = math.pi / 2 + (math.pi / 2 - a0 + math.pi / 2 - math.pi / 2) * 0  # placeholder for clarity
        t = i / n
        ang = (math.pi - (math.pi / 2 - a0) - math.pi / 2) * 0
        # sweep from angle (pi - b) to b where b is the foot angle from +x
        b = math.asin((z0 - cz) / r)
        ang = (math.pi - b) + (b - (math.pi - b)) * t
        out.append((cx + r * math.cos(ang), cz + r * math.sin(ang)))
    return out


def _lathe(mb, prof, cx, cy, cz, mat, seg=36, side=1, smooth=True):
    """Revolve a (radius, y_offset) profile about the Y axis through (cx, cz)."""
    rings = []
    for (r, oy) in prof:
        rings.append([Vector((cx + r * math.cos(2 * math.pi * k / seg), cy + side * oy, cz + r * math.sin(2 * math.pi * k / seg)))
                      for k in range(seg)])
    for i in range(len(rings) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            q = [rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]]
            if side < 0:
                q.reverse()
            mb.face(q, mat, smooth=smooth)


def wheel(mb, M, cx, cy, cz, side=1, steer=0.0):
    """All-terrain tyre on an alloy rim; side=+1 for the left (outer face toward +Y)."""
    R, w = TR, TW / 2
    RB = M["rubber"]
    # carcass: flat-ish crown, rounded shoulders, bulged sidewalls, bead
    tyre = [(0.262, -w + 0.035), (0.275, -w + 0.012), (0.30, -w - 0.004), (0.335, -w - 0.01), (0.365, -w - 0.004),
            (R - 0.022, -w + 0.012), (R - 0.008, -w + 0.035), (R - 0.001, -w + 0.065),
            (R, -0.04), (R, 0.04),
            (R - 0.001, w - 0.065), (R - 0.008, w - 0.035), (R - 0.022, w - 0.012),
            (0.365, w + 0.004), (0.335, w + 0.01), (0.30, w + 0.004), (0.275, w - 0.012), (0.262, w - 0.035)]
    _lathe(mb, tyre, cx, cy, cz, RB, seg=64, side=side)
    # raised sidewall rings (where the lettering band sits)
    for (r0, r1) in ((0.312, 0.318), (0.352, 0.356)):
        for sgn in (-1, 1):
            _lathe(mb, [(r0, sgn * (w + 0.008)), (r0, sgn * (w + 0.013)), (r1, sgn * (w + 0.013)), (r1, sgn * (w + 0.007))],
                   cx, cy, cz, RB, seg=48, side=side)
    # tread: five staggered rows of small blocks, plus shoulder lugs that wrap onto the sidewall
    n = 46
    rows = [(-0.098, 0.036, 0.0), (-0.05, 0.038, 0.5), (0.0, 0.034, 0.0), (0.05, 0.038, 0.5), (0.098, 0.036, 0.0)]
    for k in range(n):
        a = 2 * math.pi * k / n
        for (oy, wy, ph) in rows:
            aa = a + ph * 2 * math.pi / n
            skew = 0.22 if oy < 0 else (-0.22 if oy > 0 else 0.0)
            m = (Matrix.Translation((cx, cy + oy, cz)) @ Matrix.Rotation(-aa, 4, "Y") @ Matrix.Translation((R + 0.003, 0, 0))
                 @ Matrix.Rotation(skew, 4, "X"))
            mb.obox(m, 0.014, wy, 0.036, RB)
        if k % 2 == 0:
            for sgn in (-1, 1):
                m = (Matrix.Translation((cx, cy + sgn * (w - 0.012), cz)) @ Matrix.Rotation(-a, 4, "Y")
                     @ Matrix.Translation((R - 0.016, 0, 0)) @ Matrix.Rotation(sgn * 0.75, 4, "Z"))
                mb.obox(m, 0.03, 0.03, 0.05, RB)
    # rim: barrel, outer lip, dished face, six tapered spokes, hub, lug nuts
    RM = M["rim"]
    barrel = [(0.262, -w + 0.035), (0.24, -w + 0.03), (0.225, -w + 0.06), (0.225, w - 0.1), (0.24, w - 0.05),
              (0.262, w - 0.035), (0.268, w - 0.02), (0.262, w - 0.008), (0.248, w - 0.014), (0.236, w - 0.04)]
    _lathe(mb, barrel, cx, cy, cz, RM, seg=48, side=side)
    yo = cy + side * (w - 0.075)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.26
        base = Matrix.Translation((cx, yo, cz)) @ Matrix.Rotation(-a, 4, "Y")
        mb.obox(base @ Matrix.Translation((0.115, side * 0.004, 0)), 0.11, 0.03, 0.075, RM)       # root
        mb.obox(base @ Matrix.Translation((0.19, side * 0.012, 0)) @ Matrix.Rotation(side * 0.12, 4, "Z"), 0.1, 0.026, 0.05, RM)   # tip
    _lathe(mb, [(0.0, w - 0.045), (0.05, w - 0.042), (0.082, w - 0.055), (0.09, w - 0.085), (0.09, w - 0.12)], cx, cy, cz, RM, seg=24, side=side)
    for k in range(5):
        a = 2 * math.pi * k / 5
        p = Vector((cx + 0.058 * math.cos(a), cy + side * (w - 0.05), cz + 0.058 * math.sin(a)))
        mb.cyl(p, p + Vector((0, side * 0.014, 0)), 0.011, M["chrome"], seg=6)
    mb.cyl((cx, cy + side * (w - 0.044), cz), (cx, cy + side * (w - 0.03), cz), 0.03, M["chrome"], seg=14)
    mb.cyl((cx, cy - side * 0.03, cz), (cx, cy - side * 0.02, cz), 0.19, M["steel"], seg=28)       # brake disc
    mb.obox(Matrix.Translation((cx - 0.13, cy - side * 0.02, cz + 0.08)), 0.09, 0.05, 0.12, M["red"])  # caliper


def build(name="suv", paint=(0.62, 0.5, 0.33), rack=True, dusty=True, snorkel=True, bullbar=True, plate="SAH 204 KJ",
          roof=(0.9, 0.9, 0.87), livery="TRANS-SAHARA|EXPEDITION 2026"):
    """Returns a hidden library collection holding the truck (instance it or link it)."""
    key = "LIB_" + name
    if key in bpy.data.collections:
        return bpy.data.collections[key]
    M = _mats(paint, dusty)
    lib = kit.coll("LIB", hide=True)
    c = bpy.data.collections.new(key)
    lib.children.link(c)
    B, K, G = M["body"], M["black"], M["glass"]
    RF = kit.mat_plain(name + "_roofpaint", roof, rough=0.35, coat=0.6) if roof else B
    CK = kit.mat_plain("suv_checker", (0.16, 0.16, 0.17), rough=0.45, metal=0.9)
    body, trim, glass, whl = MB(), MB(), MB(), MB()

    # ---------------- lower body: extruded side profile with wheel arches
    top_f, top_r = (1.10, ZB + 0.04), (-2.35, ZB)
    prof = [(2.34, 0.56), (2.40, 0.66), (2.40, 1.04), (2.32, 1.15), top_f, top_r, (-2.35, 0.62), (-2.28, ZS + 0.02)]
    prof += _arc(AX_R, ARCH)
    prof += _arc(AX_F, ARCH)
    n = len(prof)
    for s in (-1, 1):
        pts = [(x, s * HW, z) for (x, z) in prof]
        if s > 0:
            pts.reverse()
        body.face(pts, B)
    for i in range(n):
        (x0, z0), (x1, z1) = prof[i], prof[(i + 1) % n]
        if prof[i] == top_f and prof[(i + 1) % n] == top_r:
            continue                      # cabin is open at the belt line
        in_arch = (abs(math.hypot(x0 - AX_F, z0 - TR) - ARCH) < 1e-3 and abs(math.hypot(x1 - AX_F, z1 - TR) - ARCH) < 1e-3) or \
                  (abs(math.hypot(x0 - AX_R, z0 - TR) - ARCH) < 1e-3 and abs(math.hypot(x1 - AX_R, z1 - TR) - ARCH) < 1e-3)
        mat = M["well"] if in_arch else (K if z0 < 0.6 and z1 < 0.6 else B)
        body.face([(x0, -HW, z0), (x1, -HW, z1), (x1, HW, z1), (x0, HW, z0)], mat, smooth=in_arch)
    # bonnet power bulge + cowl
    body.box(1.02, -HW + 0.02, ZB + 0.03, 1.14, HW - 0.02, ZB + 0.06, K)
    # cabin tub: floor, firewall, door cards, sill caps, rear wall
    iw = HW - 0.08
    body.face([(1.0, -iw, FLOOR), (1.0, iw, FLOOR), (-2.27, iw, FLOOR), (-2.27, -iw, FLOOR)], M["dash"])
    body.face([(1.0, -iw, FLOOR), (1.0, -iw, ZB + 0.04), (1.0, iw, ZB + 0.04), (1.0, iw, FLOOR)], M["dash"])
    for s in (-1, 1):
        body.face([(1.0, s * iw, FLOOR), (-2.27, s * iw, FLOOR), (-2.27, s * iw, ZB), (1.0, s * iw, ZB + 0.04)], M["seat"])
        body.face([(1.10, s * iw, ZB + 0.04), (-2.35, s * iw, ZB), (-2.35, s * HW, ZB), (1.10, s * HW, ZB + 0.04)], K)
    body.face([(-2.27, -iw, FLOOR), (-2.27, iw, FLOOR), (-2.27, iw, ZB), (-2.27, -iw, ZB)], M["seat"])

    # ---------------- greenhouse: pillars, roof, glass
    def side_pt(x, z):          # point on the tumblehome side plane
        t = (z - ZB) / (ZR_ - 0.04 - ZB)
        return HW + (HR - HW) * t

    def pillar(xb, xt, w=0.09, z0=None, z1=ZR_ - 0.04):
        z0 = ZB if z0 is None else z0
        for s in (-1, 1):
            a = Vector((xb, s * (side_pt(xb, z0) - 0.03), z0))
            b_ = Vector((xt, s * (side_pt(xt, z1) - 0.03), z1))
            d = b_ - a
            m = Matrix.Translation((a + b_) / 2) @ d.to_track_quat("Z", "X").to_matrix().to_4x4()
            trim.obox(m, w, 0.065, d.length + 0.02, B)

    ws_b, ws_t = 1.10, 0.62
    pillar(ws_b - 0.02, ws_t - 0.02, w=0.1)        # A
    pillar(0.02, 0.0, w=0.11)                      # B
    pillar(-1.05, -1.05, w=0.11)                   # C
    pillar(-2.29, -2.29, w=0.13)                   # D
    # roof with a slight crown and drip rails
    body.box(ws_t - 0.06, -HR, ZR_ - 0.06, -2.35, HR, ZR_, RF)
    body.box(ws_t + 0.02, -HR + 0.1, ZR_, -2.25, HR - 0.1, ZR_ + 0.02, RF)
    for yy in (-0.4, 0.0, 0.4):            # pressed roof ribs
        body.box(ws_t + 0.15, yy - 0.04, ZR_ + 0.02, -2.15, yy + 0.04, ZR_ + 0.032, RF)
    for s in (-1, 1):
        trim.box(ws_t - 0.05, s * HR - 0.012, ZR_ - 0.075, -2.34, s * HR + 0.012, ZR_ - 0.055, K)
    # header rails front/rear
    trim.box(ws_t - 0.08, -HR, ZR_ - 0.1, ws_t - 0.0, HR, ZR_ - 0.04, B)
    trim.box(-2.35, -HR, ZR_ - 0.12, -2.27, HR, ZR_ - 0.04, B)
    # windscreen (laminated: one slab) + black surround
    wb, wt = ZB + 0.06, ZR_ - 0.09
    glass.face([(ws_b, -HW + 0.07, wb), (ws_b, HW - 0.07, wb), (ws_t, HR - 0.05, wt), (ws_t, -HR + 0.05, wt)], G)
    glass.face([(ws_b - 0.008, HW - 0.07, wb), (ws_b - 0.008, -HW + 0.07, wb), (ws_t - 0.008, -HR + 0.05, wt), (ws_t - 0.008, HR - 0.05, wt)], G)
    # side glass between pillars (three lights per side) and the rear screen
    for s in (-1, 1):
        for (xa, xb_) in [(ws_b - 0.42, 0.07), (-0.05, -1.0), (-1.1, -2.23)]:
            za, zb_ = ZB + 0.03, ZR_ - 0.09
            fa = xa if xa < 0.6 else ws_b - 0.1          # front light follows the raked A-pillar
            ya, yb_ = s * (side_pt(0, za) - 0.035), s * (side_pt(0, zb_) - 0.035)
            top_a = xa if xa < 0.6 else ws_t + 0.03
            q = [(fa, ya, za), (xb_, ya, za), (xb_, yb_, zb_), (top_a, yb_, zb_)]
            if s > 0:
                q.reverse()
            glass.face(q, G)
            q2 = [(p[0], p[1] - s * 0.006, p[2]) for p in reversed(q)]
            glass.face(q2, G)
            for i in range(4):
                pa, pb = Vector(q[i]), Vector(q[(i + 1) % 4])
                trim.cyl(pa, pb, 0.014, K, seg=6, caps=False)
    glass.box(-2.335, -HR + 0.12, ZB + 0.12, -2.325, HR - 0.12, ZR_ - 0.14, G)
    trim.box(-2.36, -HW, ZB - 0.02, -2.34, HW, ZB + 0.1, B)          # tailgate top edge
    for s in (-1, 1):                                                 # rear quarter posts (wide, body colour)
        trim.box(-2.36, s * (HR - 0.0), ZB, -2.3, s * (HR - 0.14), ZR_ - 0.1, B)
        trim.box(-2.36, s * HW, ZB, -2.3, s * (HW - 0.16), ZB + 0.42, B)

    # ---------------- shut lines, handles, mirrors, steps, cladding
    for s in (-1, 1):
        y = s * (HW + 0.001)
        for x in (1.06, 0.0, -1.06):
            trim.box(x - 0.004, y - 0.002, ZS + 0.12, x + 0.004, y + 0.002, ZB + 0.01, K)
        trim.box(-1.06, y - 0.002, ZS + 0.115, 1.06, y + 0.002, ZS + 0.123, K)
        for x in (0.12, -0.92):
            trim.box(x - 0.09, s * HW, ZB - 0.14, x + 0.09, s * (HW + 0.03), ZB - 0.1, K)
        trim.box(AX_R + ARCH + 0.05, s * HW, 0.36, AX_F - ARCH - 0.05, s * (HW + 0.16), 0.41, K)       # running board
        for x in (AX_R + ARCH + 0.3, 0.2, AX_F - ARCH - 0.3):
            trim.box(x - 0.02, s * (HW - 0.1), 0.38, x + 0.02, s * (HW + 0.02), 0.5, K)
        # mirror
        trim.box(0.92, s * HW, ZB + 0.12, 0.96, s * (HW + 0.14), ZB + 0.15, K)
        trim.box(0.9, s * (HW + 0.1), ZB + 0.07, 0.98, s * (HW + 0.25), ZB + 0.25, K)
        trim.box(0.893, s * (HW + 0.115), ZB + 0.085, 0.9, s * (HW + 0.235), ZB + 0.235, M["chrome"])
        # arch flares
        for cxa in (AX_F, AX_R):
            pts = _arc(cxa, ARCH, n=14, z0=ZS)
            for i in range(len(pts) - 1):
                (xa, za), (xb_, zb_) = pts[i], pts[i + 1]
                ra, rb = ARCH + 0.07, ARCH + 0.07
                oa = (cxa + (xa - cxa) * ra / ARCH, TR + (za - TR) * ra / ARCH)
                ob = (cxa + (xb_ - cxa) * rb / ARCH, TR + (zb_ - TR) * rb / ARCH)
                y0, y1 = s * HW, s * (HW + 0.05)
                q = [(xa, y1, za), (xb_, y1, zb_), (ob[0], y1, ob[1]), (oa[0], y1, oa[1])]
                trim.face(q if s < 0 else list(reversed(q)), K)
                q = [(oa[0], y0, oa[1]), (ob[0], y0, ob[1]), (ob[0], y1, ob[1]), (oa[0], y1, oa[1])]
                trim.face(q if s > 0 else list(reversed(q)), K)
                q = [(xa, y0, za), (xb_, y0, zb_), (xb_, y1, zb_), (xa, y1, za)]
                trim.face(q if s < 0 else list(reversed(q)), K)
        # mud flaps
        trim.box(AX_R - ARCH - 0.04, s * (TRACK - 0.14), 0.2, AX_R - ARCH - 0.02, s * (TRACK + 0.16), ZS + 0.05, K)

    # ---------------- front end
    xg = 2.40
    trim.box(xg - 0.01, -0.5, 0.74, xg + 0.012, 0.5, 1.08, K)                 # grille opening
    for zz in (0.74, 1.065):
        trim.box(xg, -0.52, zz - 0.02, xg + 0.03, 0.52, zz + 0.02, B)
    for yy in (-0.52, 0.52):
        trim.box(xg, yy - 0.02, 0.72, xg + 0.03, yy + 0.02, 1.085, B)
    z = 0.78
    while z < 1.05:                                                           # fine horizontal bars
        trim.box(xg + 0.008, -0.5, z, xg + 0.022, 0.5, z + 0.012, K)
        z += 0.03
    for yy in (-0.25, 0.0, 0.25):
        trim.box(xg + 0.012, yy - 0.012, 0.76, xg + 0.026, yy + 0.012, 1.05, K)
    for s in (-1, 1):
        y = s * 0.735
        trim.box(xg - 0.005, y - 0.16, 0.76, xg + 0.02, y + 0.16, 1.08, K)   # lamp panel
        c0 = Vector((xg + 0.022, y, 0.95))
        trim.cyl(c0, c0 + Vector((0.03, 0, 0)), 0.118, M["chrome"], seg=28, caps=False)       # bezel ring
        trim.cyl(c0 - Vector((0.09, 0, 0)), c0 + Vector((0.01, 0, 0)), 0.03, M["chrome"], seg=28, r1=0.105, caps=False)  # reflector bowl
        trim.cyl(c0 - Vector((0.06, 0, 0)), c0 - Vector((0.02, 0, 0)), 0.018, M["lamp"], seg=10)                         # bulb
        trim.cyl(c0 + Vector((0.004, 0, 0)), c0 + Vector((0.012, 0, 0)), 0.104, M["lampface"], seg=28)                   # fluted lens face
        for (dy, zz, mm) in [(0.0, 0.8, M["amber"]), ]:
            trim.cyl((xg + 0.02, y + dy, zz), (xg + 0.04, y + dy, zz), 0.042, mm, seg=16)
            trim.cyl((xg + 0.015, y + dy, zz), (xg + 0.03, y + dy, zz), 0.05, K, seg=16, caps=False)
        # wing-side air vent and wing-top chequer plate
        trim.box(1.45, s * HW, 1.0, 1.85, s * (HW + 0.006), 1.09, K)
        for k in range(5):
            trim.box(1.47 + k * 0.075, s * (HW + 0.004), 1.01, 1.50 + k * 0.075, s * (HW + 0.012), 1.08, K)
        mck = Matrix.Translation((1.72, s * 0.76, 1.213)) @ Matrix.Rotation(math.radians(5.15), 4, "Y")
        trim.obox(mck, 1.02, 0.3, 0.008, CK)
        # door hinges (two per door)
        for xh in (1.045, -0.012):
            for zh in (ZS + 0.3, ZB - 0.14):
                trim.cyl((xh, s * (HW + 0.014), zh - 0.045), (xh, s * (HW + 0.014), zh + 0.045), 0.017, B, seg=10)
    # bonnet centre rise
    mbn = Matrix.Translation((1.72, 0, 1.214)) @ Matrix.Rotation(math.radians(5.15), 4, "Y")
    body.obox(mbn, 1.1, 0.95, 0.022, B)
    # bumper + bull bar + winch + plate
    trim.box(2.36, -HW - 0.02, 0.5, 2.56, HW + 0.02, 0.7, K)
    PL = decal_material("plate_" + plate.replace(" ", "_"), "plate", plate)
    trim.face([(2.566, -0.26, 0.52), (2.566, 0.26, 0.52), (2.566, 0.26, 0.64), (2.566, -0.26, 0.64)], PL,
              uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    trim.box(2.555, -0.27, 0.51, 2.564, 0.27, 0.65, K)
    trim.box(2.44, -0.2, 0.7, 2.56, 0.2, 0.78, M["steel"])
    if bullbar:
        for s in (-1, 1):
            trim.cyl((2.57, s * 0.4, 0.52), (2.6, s * 0.4, 1.09), 0.021, K, seg=10)
            trim.cyl((2.6, s * 0.4, 1.09), (2.5, s * 0.9, 1.0), 0.021, K, seg=10)
            trim.cyl((2.5, s * 0.9, 1.0), (2.5, s * 0.92, 0.66), 0.021, K, seg=10)
            cs = Vector((2.6, s * 0.24, 1.2))                                                  # driving lamps
            trim.cyl(cs, cs + Vector((0.075, 0, 0)), 0.092, K, seg=24, r1=0.098)
            trim.cyl(cs + Vector((0.01, 0, 0)), cs + Vector((0.07, 0, 0)), 0.03, M["chrome"], seg=24, r1=0.088, caps=False)
            trim.cyl(cs + Vector((0.066, 0, 0)), cs + Vector((0.076, 0, 0)), 0.088, M["lampface"], seg=24)
            trim.cyl((2.62, s * 0.24, 1.09), (2.62, s * 0.24, 1.12), 0.012, K, seg=6)
        trim.cyl((2.6, -0.4, 1.09), (2.6, 0.4, 1.09), 0.021, K, seg=10)
    # wipers
    for y in (-0.35, 0.3):
        trim.cyl((1.13, y, ZB + 0.07), (1.07, y + 0.42, ZB + 0.16), 0.008, K, seg=6)

    # ---------------- rear end
    for s in (-1, 1):
        trim.box(-2.37, s * (HW - 0.13), 0.9, -2.35, s * (HW - 0.01), ZB - 0.02, M["red"])
        trim.box(-2.37, s * (HW - 0.13), 0.8, -2.35, s * (HW - 0.01), 0.89, M["amber"])
    trim.box(-2.52, -HW, 0.5, -2.34, HW, 0.66, K)
    trim.box(-2.53, -0.25, 0.68, -2.525, 0.25, 0.8, M["plate"]) if False else trim.face([(-2.372, -0.14, 0.7), (-2.372, -0.62, 0.7), (-2.372, -0.62, 0.81), (-2.372, -0.14, 0.81)], PL, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    trim.box(-2.365, 0.3, 1.0, -2.35, 0.42, 1.04, M["chrome"])        # tailgate handle
    # spare wheel on the tailgate
    m_sp = Matrix.Translation((-2.36 - TW / 2 - 0.05, 0.12, 1.02)) @ Matrix.Rotation(math.pi / 2, 4, "Z")
    sp = MB()
    wheel(sp, M, 0, 0, 0, side=1)
    spo = sp.build(name + "_spare", c)
    spo.matrix_world = m_sp
    trim.cyl((-2.35, 0.12, 1.02), (-2.44, 0.12, 1.02), 0.08, K, seg=12)
    # rear ladder
    for y in (-0.72, -0.44):
        trim.cyl((-2.4, y, 0.7), (-2.4, y, ZR_ + 0.02), 0.014, K, seg=8)
    for zz in (0.95, 1.2, 1.45, 1.7):
        trim.cyl((-2.4, -0.72, zz), (-2.4, -0.44, zz), 0.012, K, seg=8)

    if livery:
        LV = decal_material(name + "_livery", "livery", livery)
        for s in (-1, 1):
            y = s * (HW + 0.004)
            q = [(0.95, y, 0.7), (-0.95, y, 0.7), (-0.95, y, 1.12), (0.95, y, 1.12)]
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)] if s > 0 else [(1, 0), (0, 0), (0, 1), (1, 1)]
            trim.face(q if s > 0 else list(reversed(q)), LV, uvs=uv if s > 0 else list(reversed(uv)))
    # ---------------- snorkel, antenna
    if snorkel:
        trim.box(1.3, -HW - 0.07, ZB - 0.16, 1.62, -HW, ZB - 0.02, K)
        trim.cyl((1.34, -HW - 0.045, ZB - 0.06), (0.98, -HW - 0.02, ZB + 0.1), 0.04, K, seg=10)
        trim.cyl((0.98, -HW - 0.02, ZB + 0.1), (0.58, -HR - 0.06, ZR_ + 0.02), 0.04, K, seg=10)
        trim.cyl((0.58, -HR - 0.06, ZR_ + 0.02), (0.7, -HR - 0.06, ZR_ + 0.1), 0.055, K, seg=12)
    trim.cyl((1.5, 0.8, ZB + 0.05), (1.38, 0.8, ZB + 1.25), 0.004, K, seg=5)

    # ---------------- interior: dash, wheel, seats
    D, S = M["dash"], M["seat"]
    body.box(0.72, -iw, ZB - 0.28, 1.0, iw, ZB + 0.02, D)
    body.box(0.6, -0.16, FLOOR, 0.98, 0.16, ZB - 0.3, D)                 # centre console
    body.box(-0.4, -0.13, FLOOR, 0.6, 0.13, FLOOR + 0.26, D)
    swc = Vector((0.66, 0.42, ZB - 0.06))
    ax = Vector((-1, 0, 0.42)).normalized()
    u = ax.orthogonal().normalized()
    v = ax.cross(u)
    prev = None
    for k in range(25):
        a = 2 * math.pi * k / 24
        p = swc + 0.185 * (math.cos(a) * u + math.sin(a) * v)
        if prev is not None:
            trim.cyl(prev, p, 0.016, D, seg=6, caps=False)
        prev = p
    trim.cyl(swc, swc - ax * 0.18, 0.03, D, seg=8)
    for a in (0.5, 2.6, 4.7):
        trim.cyl(swc, swc + 0.185 * (math.cos(a) * u + math.sin(a) * v), 0.012, D, seg=5)
    seat = MB()

    def seat_at(x, y, w=0.5):
        seat.box(x - 0.3, y - w / 2, FLOOR + 0.12, x + 0.24, y + w / 2, SEAT_TOP, S)
        m = Matrix.Translation((x - 0.31, y, SEAT_TOP - 0.05)) @ Matrix.Rotation(math.radians(-14), 4, "Y") @ Matrix.Translation((0, 0, 0.33))
        seat.obox(m, 0.13, w, 0.66, S)
        m2 = Matrix.Translation((x - 0.31, y, SEAT_TOP - 0.05)) @ Matrix.Rotation(math.radians(-14), 4, "Y") @ Matrix.Translation((0, 0, 0.78))
        seat.obox(m2, 0.1, 0.26, 0.2, S)

    seat_at(0.12, 0.42), seat_at(0.12, -0.42)
    seat.box(-1.12, -iw + 0.02, FLOOR + 0.12, -0.55, iw - 0.02, SEAT_TOP, S)
    mbk = Matrix.Translation((-1.13, 0, SEAT_TOP - 0.05)) @ Matrix.Rotation(math.radians(-12), 4, "Y") @ Matrix.Translation((0, 0, 0.32))
    seat.obox(mbk, 0.13, 2 * iw - 0.06, 0.64, S)
    for y in (-0.5, 0.0, 0.5):
        mh_ = Matrix.Translation((-1.13, y, SEAT_TOP - 0.05)) @ Matrix.Rotation(math.radians(-12), 4, "Y") @ Matrix.Translation((0, 0, 0.76))
        seat.obox(mh_, 0.1, 0.24, 0.18, S)
    # cargo behind the seats
    seat.box(-2.2, -0.6, FLOOR, -1.4, 0.0, FLOOR + 0.45, M["case"])
    seat.box(-2.2, 0.05, FLOOR, -1.5, 0.7, FLOOR + 0.35, M["canvas"])

    # ---------------- roof rack and load
    if rack:
        z0 = ZR_ + 0.11
        x0, x1, yw = 0.45, -2.25, 0.74
        for y in (-yw, yw):
            trim.cyl((x0, y, z0), (x1, y, z0), 0.018, K, seg=8)
            trim.cyl((x0, y, z0 + 0.13), (x1, y, z0 + 0.13), 0.014, K, seg=8)
            for x in (0.4, -0.3, -1.0, -1.7, -2.2):
                trim.cyl((x, y, z0), (x, y, z0 + 0.13), 0.012, K, seg=6)
                trim.box(x - 0.04, y - 0.02, ZR_ - 0.02, x + 0.04, y + 0.02, z0, K)
        for x in (x0, x1):
            trim.cyl((x, -yw, z0), (x, yw, z0), 0.018, K, seg=8)
            trim.cyl((x, -yw, z0 + 0.13), (x, yw, z0 + 0.13), 0.014, K, seg=8)
        x = x0 - 0.12
        while x > x1:
            trim.box(x - 0.02, -yw, z0 - 0.008, x + 0.02, yw, z0 + 0.008, K)
            x -= 0.2
        # LED bar
        trim.box(x0 + 0.03, -0.55, z0 + 0.0, x0 + 0.09, 0.55, z0 + 0.08, K)
        trim.box(x0 + 0.09, -0.53, z0 + 0.01, x0 + 0.095, 0.53, z0 + 0.07, M["lamp"])
        load = MB()
        # jerry cans, hard cases, bed-rolls, a second spare, sand ladders
        for i, y in enumerate((-0.55, -0.36, -0.17)):
            load.box(-2.1, y - 0.085, z0 + 0.01, -1.75, y + 0.085, z0 + 0.48, M["can"])
            load.box(-1.98, y - 0.02, z0 + 0.48, -1.86, y + 0.02, z0 + 0.53, M["can"])
        load.box(-1.6, -0.62, z0 + 0.01, -0.85, -0.05, z0 + 0.34, M["case"])
        load.box(-1.55, 0.05, z0 + 0.01, -0.95, 0.62, z0 + 0.26, M["case"])
        load.cyl((-0.7, -0.6, z0 + 0.16), (-0.7, 0.6, z0 + 0.16), 0.15, M["canvas"], seg=16)
        load.cyl((-0.36, -0.55, z0 + 0.14), (-0.36, 0.5, z0 + 0.14), 0.13, M["can"], seg=16)
        load.box(-0.15, -0.5, z0 + 0.01, 0.35, 0.5, z0 + 0.2, M["canvas"])
        lo = load.build(name + "_load", c, bevel=0.02)
        for s in (1,):
            for k in range(2):
                yy = s * (yw + 0.035 + k * 0.035)
                trim.box(-1.75, yy - 0.01, z0 - 0.05, -0.6, yy + 0.01, z0 + 0.27, M["ladder"])
                for q in range(9):                                     # cleats moulded into the board
                    xq = -1.68 + q * 0.13
                    trim.box(xq, yy + s * 0.008, z0 - 0.03, xq + 0.05, yy + s * 0.022, z0 + 0.25, M["ladder"])
        sp2 = MB()
        wheel(sp2, M, 0, 0, 0, side=1)
        o2 = sp2.build(name + "_spare2", c)
        o2.matrix_world = Matrix.Translation((-1.95, 0.32, z0 + 0.16)) @ Matrix.Rotation(math.pi / 2, 4, "X")

    # ---------------- wheels and running gear
    wheel_objs = []
    for (cx, st) in ((AX_F, 0.0), (AX_R, 0.0)):
        for s in (-1, 1):
            wm = MB()                       # each wheel is its own object so it can spin
            wheel(wm, M, 0, 0, 0, side=s)
            wo = wm.build(f"{name}_wheel_{len(wheel_objs)}", c)
            wo.location = (cx, s * TRACK, TR)
            wheel_objs.append(wo)
        trim.cyl((cx, -TRACK + 0.1, TR), (cx, TRACK - 0.1, TR), 0.05, K, seg=10)
        trim.cyl((cx, 0.0, TR - 0.0), (cx - 0.0, 0.14, TR), 0.13, K, seg=14)
    trim.box(AX_R + 0.1, -0.5, 0.3, AX_F - 0.1, 0.5, ZS + 0.02, K)        # chassis / underbody
    trim.cyl((AX_R - 0.4, -0.45, 0.33), (-2.5, -0.45, 0.38), 0.035, M["steel"], seg=10)   # exhaust

    ob = body.build(name + "_body", c, weld=True)
    ob.modifiers.new("bevel", "BEVEL").width = 0.045
    ob.modifiers["bevel"].segments = 4
    ob.modifiers["bevel"].limit_method = "ANGLE"
    ob.modifiers["bevel"].angle_limit = math.radians(40)
    trim.build(name + "_trim", c, bevel=0.006)
    glass.build(name + "_glass", c)
    seat.build(name + "_seats", c, bevel=0.03)
    c["size"] = (5.1, 2.3, 2.5)
    return c


def instance(lib_coll, loc=(0, 0, 0), rz=0.0, collection=None, name="suv"):
    e = bpy.data.objects.new(name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = lib_coll
    e.location = loc
    e.rotation_euler = (0, 0, rz)
    (collection or bpy.context.scene.collection).objects.link(e)
    return e


def seat_people(truck_obj, people, collection=None):
    """Place baked seated figures (facing -Y in their own frame) on named seats.
    people = {seat_name: object}; each figure is parented to the truck."""
    for seat_name, ob in people.items():
        x, y = SEATS[seat_name]
        ob.parent = truck_obj
        ob.location = (x + 0.02, y, FLOOR - 0.0)
        ob.rotation_euler = (0, 0, math.pi / 2)


def wheels(lib_coll):
    return [o for o in lib_coll.objects if "_wheel_" in o.name]
