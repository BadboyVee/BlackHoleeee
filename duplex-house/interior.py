"""Interior fit-out: furniture, kitchen, bathrooms, beds, curtains, art, lights."""
import math
import random

import bpy
from mathutils import Matrix, Vector

import kit
from house import Z0, Z1, ZR, SL, TE, TI
from kit import MB

R90 = math.pi / 2


def mats(M):
    I = dict(M)
    I["sofa"] = kit.mat_pbr("sofa_fabric", "cotton_jersey", size=0.5, tint=(0.78, 0.74, 0.68), sat=0.0, val=1.25)
    I["sofa_dark"] = kit.mat_pbr("sofa_dark", "rough_linen", size=0.4, tint=(0.22, 0.26, 0.3))
    I["pillow_a"] = kit.mat_pbr("pillow_a", "velour_velvet", size=0.4, tint=(0.95, 0.6, 0.22), sat=0.0, val=1.5)
    I["pillow_b"] = kit.mat_pbr("pillow_b", "rough_linen", size=0.3, tint=(0.2, 0.42, 0.4), sat=0.0, val=1.2)
    I["linen"] = kit.mat_pbr("bed_linen", "cotton_jersey", size=0.5, sat=0.0, val=1.6)
    I["duvet"] = kit.mat_pbr("duvet", "rough_linen", size=0.5, tint=(0.9, 0.88, 0.84), sat=0.0, val=1.2)
    I["throw"] = kit.mat_pbr("throw", "velour_velvet", size=0.5, tint=(0.75, 0.42, 0.18), sat=0.0, val=1.5)
    I["rug"] = kit.mat_pbr("rug", "wool_boucle", size=1.1, val=1.1, sat=0.35)
    I["rug2"] = kit.mat_pbr("rug2", "cotton_jersey", size=0.7, tint=(0.62, 0.6, 0.56), sat=0.0)
    I["oak"] = kit.mat_pbr("oak", "oak_veneer_01", size=1.2, val=0.95)
    I["walnut"] = kit.mat_pbr("walnut", "wood_table_001", size=1.0, val=1.25)
    I["cab"] = kit.mat_plain("cabinet_matt", (0.82, 0.82, 0.8), rough=0.35)
    I["cab_dark"] = kit.mat_plain("cabinet_dark", (0.07, 0.08, 0.09), rough=0.35)
    I["marble"] = kit.mat_pbr("marble_top", "marble_01", size=1.8, val=1.15, sat=0.5, rough_mul=0.25, normal=0.2)
    I["inox"] = kit.mat_plain("inox", (0.62, 0.62, 0.62), rough=0.28, metal=1.0)
    I["black"] = kit.mat_plain("black_gloss", (0.01, 0.01, 0.012), rough=0.08, spec=0.8)
    I["screen"] = kit.mat_plain("tv_screen", (0.005, 0.005, 0.007), rough=0.05, spec=1.0)
    I["ceramic"] = kit.mat_plain("ceramic", (0.92, 0.92, 0.9), rough=0.12, spec=0.7)
    I["mirror"] = kit.mat_plain("mirror", (0.9, 0.9, 0.9), rough=0.0, metal=1.0)
    I["brass"] = kit.mat_plain("brass", (0.75, 0.55, 0.25), rough=0.25, metal=1.0)
    I["wall_tile"] = kit.mat_pbr("wall_tile", "long_white_tiles", size=1.2, rough_mul=0.4)
    I["spot"] = kit.mat_emit("spot_emit", (1.0, 0.86, 0.68), 25.0)
    I["bulb"] = kit.mat_emit("bulb_emit", (1.0, 0.82, 0.6), 12.0)
    I["art1"] = kit.mat_plain("art_ochre", (0.7, 0.42, 0.12), rough=0.7)
    I["art2"] = kit.mat_plain("art_teal", (0.08, 0.3, 0.32), rough=0.7)
    I["art3"] = kit.mat_plain("art_cream", (0.85, 0.8, 0.7), rough=0.7)
    I["art4"] = kit.mat_plain("art_black", (0.03, 0.03, 0.03), rough=0.6)
    # sheer curtain: mostly diffuse white with some see-through
    m, nt, b, out = kit._new("sheer")
    b.inputs["Base Color"].default_value = (0.95, 0.94, 0.9, 1)
    b.inputs["Roughness"].default_value = 0.9
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ms = nt.nodes.new("ShaderNodeMixShader")
    ms.inputs[0].default_value = 0.45
    nt.links.new(b.outputs[0], ms.inputs[1])
    nt.links.new(tr.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs[0])
    I["sheer"] = m
    I["drape"] = kit.mat_pbr("drape", "rough_linen", size=0.5, tint=(0.62, 0.58, 0.52), sat=0.0)
    return I


class Interior:
    def __init__(self, c, H):
        self.c, self.H = c, H
        self.I = mats(H.M)
        self.soft, self.hard, self.flat = MB(), MB(), MB()
        self.rnd = random.Random(5)

    # ---------------------------------------------------------- helpers ---
    def T(self, x, y, z, rz=0.0):
        return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, "Z")

    def sb(self, m, cx, cy, cz, sx, sy, sz, mat, mb=None):
        (mb or self.soft).obox(m @ Matrix.Translation((cx, cy, cz)), sx, sy, sz, mat)

    def spot(self, x, y, z):
        self.flat.cyl((x, y, z - 0.004), (x, y, z - 0.012), 0.045, self.I["spot"], seg=12)
        self.flat.cyl((x, y, z - 0.001), (x, y, z - 0.006), 0.065, self.I["skirt"], seg=14)

    def spots(self, x0, y0, x1, y1, z, nx, ny):
        for i in range(nx):
            for j in range(ny):
                self.spot(x0 + (i + 0.5) * (x1 - x0) / nx, y0 + (j + 0.5) * (y1 - y0) / ny, z)

    def lamp(self, loc, power=60, radius=0.12):
        kit.point_light(loc, power, radius=radius, collection=self.c)

    def curtain(self, ax, c, u0, u1, z0, z1, mat, amp=0.045, wave=0.16):
        """Pleated curtain hanging in a plane (ax='x' → runs along x at y=c)."""
        n = max(4, int((u1 - u0) / (wave / 6)))
        pts = []
        for i in range(n + 1):
            u = u0 + (u1 - u0) * i / n
            off = amp * math.sin(2 * math.pi * (u - u0) / wave) + 0.01 * math.sin(7.3 * u)
            pts.append((u, off))
        for i in range(n):
            (ua, oa), (ub, ob) = pts[i], pts[i + 1]
            if ax == "x":
                q = [(ua, c + oa, z0), (ub, c + ob, z0), (ub, c + ob, z1), (ua, c + oa, z1)]
            else:
                q = [(c + oa, ua, z0), (c + ob, ub, z0), (c + ob, ub, z1), (c + oa, ua, z1)]
            self.flat.face(q, mat, uvs=[(ua, z0), (ub, z0), (ub, z1), (ua, z1)], smooth=True)
        # rail
        if ax == "x":
            self.flat.box(u0 - 0.05, c - 0.02, z1, u1 + 0.05, c + 0.02, z1 + 0.03, self.I["alu"])
        else:
            self.flat.box(c - 0.02, u0 - 0.05, z1, c + 0.02, u1 + 0.05, z1 + 0.03, self.I["alu"])

    def art(self, ax, c, u, z, w, h, sgn, palette=None):
        """Framed abstract canvas on a wall; sgn = side of the wall plane it faces."""
        I, r = self.I, self.rnd
        cols = palette or [I["art1"], I["art2"], I["art3"], I["art4"]]
        d = 0.03 * sgn

        def b(u0, u1, z0, z1, d0, d1, m):
            if ax == "x":
                self.flat.box(u0, c + d0, z0, u1, c + d1, z1, m)
            else:
                self.flat.box(c + d0, u0, z0, c + d1, u1, z1, m)

        b(u - w / 2, u + w / 2, z - h / 2, z + h / 2, 0, d, I["art3"])
        b(u - w / 2 - 0.02, u + w / 2 + 0.02, z - h / 2 - 0.02, z + h / 2 + 0.02, 0, d * 0.8, I["cab_dark"])
        for _ in range(4):
            bw, bh = r.uniform(0.2, 0.55) * w, r.uniform(0.2, 0.55) * h
            bu = u + r.uniform(-0.5, 0.5) * (w - bw)
            bz = z + r.uniform(-0.5, 0.5) * (h - bh)
            dd = d * r.uniform(1.02, 1.12)
            b(bu - bw / 2, bu + bw / 2, bz - bh / 2, bz + bh / 2, 0, dd, r.choice(cols))

    # -------------------------------------------------------- furniture ---
    def sofa(self, x, y, z, rz, length=2.6, mat=None, chaise=False):
        I = self.I
        mat = mat or I["sofa"]
        m = self.T(x, y, z, rz)          # sofa faces local -Y, centred
        d = 0.95
        self.sb(m, 0, 0, 0.21, length, d, 0.22, mat)                       # base
        self.sb(m, 0, d / 2 - 0.11, 0.55, length, 0.22, 0.5, mat)          # back
        for s in (-1, 1):
            self.sb(m, s * (length / 2 - 0.1), 0, 0.42, 0.2, d, 0.36, mat)   # arms
        n = 3 if length > 2.2 else 2
        w = (length - 0.4) / n
        for i in range(n):
            cx = -length / 2 + 0.2 + (i + 0.5) * w
            self.sb(m, cx, -0.07, 0.4, w - 0.02, d - 0.3, 0.17, mat)      # seat cushions
            bm = m @ Matrix.Translation((cx, d / 2 - 0.27, 0.66)) @ Matrix.Rotation(math.radians(-12), 4, "X")
            self.soft.obox(bm, w - 0.04, 0.16, 0.42, mat)                 # back cushions
        if chaise:
            self.sb(m, length / 2 - 0.2 - w / 2, -d / 2 - 0.35, 0.21, w + 0.2, 0.75, 0.22, mat)
            self.sb(m, length / 2 - 0.2 - w / 2, -d / 2 - 0.33, 0.4, w - 0.02, 0.72, 0.17, mat)
        for (px, pm, a) in [(-length / 2 + 0.42, I["pillow_a"], 18), (length / 2 - 0.42, I["pillow_b"], -15),
                            (-length / 2 + 0.75, I["pillow_b"], 8)]:
            pmx = m @ Matrix.Translation((px, 0.12, 0.66)) @ Matrix.Rotation(math.radians(-20), 4, "X") @ Matrix.Rotation(math.radians(a), 4, "Y")
            self.soft.obox(pmx, 0.42, 0.13, 0.42, pm)
        for sx in (-1, 1):
            for sy in (-1, 1):
                self.sb(m, sx * (length / 2 - 0.08), sy * (d / 2 - 0.08), 0.05, 0.04, 0.04, 0.1, I["cab_dark"], self.hard)

    def bed(self, x, y, z, rz, w=1.8, L=2.05, mat_frame=None, throw=True):
        """Bed centred at x,y; head at local +Y."""
        I = self.I
        fr = mat_frame or I["walnut"]
        m = self.T(x, y, z, rz)
        self.sb(m, 0, 0, 0.17, w + 0.08, L + 0.08, 0.22, fr, self.hard)
        self.sb(m, 0, L / 2 + 0.06, 0.62, w + 0.3, 0.1, 1.15, I["sofa_dark"])        # upholstered headboard
        self.sb(m, 0, 0, 0.4, w, L, 0.24, I["linen"])                              # mattress
        self.sb(m, 0, -0.28, 0.54, w + 0.06, L - 0.62, 0.1, I["duvet"])            # duvet
        if throw:
            self.sb(m, 0, -L / 2 + 0.38, 0.565, w + 0.1, 0.55, 0.07, I["throw"])
        for s in (-1, 1):
            pm = m @ Matrix.Translation((s * w * 0.25, L / 2 - 0.3, 0.6)) @ Matrix.Rotation(math.radians(18), 4, "X")
            self.soft.obox(pm, w * 0.44, 0.42, 0.15, I["linen"])
            pm2 = m @ Matrix.Translation((s * w * 0.25, L / 2 - 0.5, 0.62)) @ Matrix.Rotation(math.radians(30), 4, "X")
            self.soft.obox(pm2, w * 0.36, 0.36, 0.13, I["pillow_a"] if s < 0 else I["pillow_b"])
        for s in (-1, 1):           # bedside tables + lamps
            bx = s * (w / 2 + 0.36)
            self.sb(m, bx, L / 2 - 0.25, 0.25, 0.48, 0.42, 0.5, fr, self.hard)
            self.sb(m, bx, L / 2 - 0.47, 0.33, 0.4, 0.012, 0.14, I["cab_dark"], self.hard)
            p = m @ Vector((bx, L / 2 - 0.25, 0.5))
            self.flat.cyl(p, p + Vector((0, 0, 0.22)), 0.03, I["brass"], seg=10)
            self.flat.cyl(p + Vector((0, 0, 0.22)), p + Vector((0, 0, 0.45)), 0.13, I["art3"], seg=16, r1=0.09, caps=False)
            self.lamp(p + Vector((0, 0, 0.33)), 8, 0.05)

    def wardrobe(self, x0, y0, x1, y1, z, h=2.4, ax="x", face=1, mat=None):
        """Fitted wardrobe block; doors along `ax`, facing +/- across."""
        I = self.I
        mat = mat or I["cab"]
        self.hard.box(x0, y0, z, x1, y1, z + h, mat)
        n = max(2, int(((x1 - x0) if ax == "x" else (y1 - y0)) / 0.5))
        for i in range(1, n):
            if ax == "x":
                u = x0 + (x1 - x0) * i / n
                yy = y1 if face > 0 else y0
                self.flat.box(u - 0.002, yy - 0.004, z + 0.05, u + 0.002, yy + 0.004, z + h - 0.02, I["cab_dark"])
                self.flat.box(u + (0.03 if i % 2 else -0.045), yy + face * 0.0, z + 0.95, u + (0.045 if i % 2 else -0.03), yy + face * 0.03, z + 1.25, I["inox"])
            else:
                u = y0 + (y1 - y0) * i / n
                xx = x1 if face > 0 else x0
                self.flat.box(xx - 0.004, u - 0.002, z + 0.05, xx + 0.004, u + 0.002, z + h - 0.02, I["cab_dark"])
                self.flat.box(xx + face * 0.0, u + (0.03 if i % 2 else -0.045), z + 0.95, xx + face * 0.03, u + (0.045 if i % 2 else -0.03), z + 1.25, I["inox"])

    def toilet(self, x, y, z, rz):
        I = self.I
        m = self.T(x, y, z, rz)        # back against local +Y
        C = I["ceramic"]
        self.sb(m, 0, 0.22, 0.42, 0.38, 0.18, 0.84, C)             # cistern
        self.sb(m, 0, -0.1, 0.2, 0.36, 0.5, 0.4, C)                # bowl
        self.sb(m, 0, -0.1, 0.415, 0.38, 0.5, 0.03, C)             # seat
        self.sb(m, 0, 0.22, 0.86, 0.1, 0.05, 0.015, I["inox"], self.hard)

    def vanity(self, x, y, z, rz, w=1.2, double=False):
        I = self.I
        m = self.T(x, y, z, rz)        # back against local +Y, wall at +0.25
        self.sb(m, 0, 0, 0.55, w, 0.5, 0.5, I["oak"], self.hard)
        self.sb(m, 0, 0, 0.82, w + 0.02, 0.52, 0.04, I["marble"], self.hard)
        for sx in ([-w / 4, w / 4] if double else [0]):
            self.sb(m, sx, -0.02, 0.9, 0.42, 0.32, 0.12, I["ceramic"])
            p = m @ Vector((sx, 0.2, 0.84))
            self.flat.cyl(p, p + Vector((0, 0, 0.22)), 0.015, I["inox"], seg=8)
        # mirror with backlight glow
        self.sb(m, 0, 0.245, 1.55, w, 0.01, 0.9, I["mirror"], self.flat)
        self.sb(m, 0, 0.25, 1.55, w + 0.04, 0.008, 0.94, I["bulb"], self.flat)

    def shower(self, x0, y0, x1, y1, z):
        """Walk-in shower: glass screen on the open sides is left to the caller; tray + head here."""
        I = self.I
        self.flat.box(x0, y0, z, x1, y1, z + 0.03, I["bath_tile"])
        hx, hy = (x0 + x1) / 2, (y0 + y1) / 2
        self.flat.cyl((hx, hy, z + 2.25), (hx, hy, z + 2.28), 0.13, I["inox"], seg=18)
        self.flat.cyl((hx, hy, z + 2.28), (hx, hy, z + 2.6), 0.012, I["inox"], seg=6)

    # ----------------------------------------------------------- rooms ---
    def living(self):
        I, z = self.I, Z0
        cg = Z1 - SL
        # rug, sofa group, coffee table
        self.flat.box(2.2, 2.9, z, 6.3, 6.0, z + 0.015, I["rug"])
        self.sofa(2.75, 4.55, z, -R90, length=2.9, chaise=False)             # faces +x (TV)
        self.sofa(4.6, 2.55, z, math.pi, length=2.2, mat=I["sofa_dark"])     # faces north
        kit.place("modern_coffee_table_02", (4.55, 4.5, z + 0.015), collection=self.c, scale=0.9)
        kit.place("mid_century_lounge_chair", (1.5, 1.35, z), rz=math.radians(-140), collection=self.c)
        kit.place("side_table_01", (2.65, 1.2, z), collection=self.c)
        kit.place("potted_plant_01", (0.7, 5.75, z), collection=self.c, scale=1.15)
        kit.place("potted_plant_02", (6.9, 0.75, z), collection=self.c, scale=1.2)
        # TV wall: timber slat panel, console, screen
        px = 7.5 - TI / 2
        self.flat.box(px - 0.03, 3.35, z + 0.1, px, 6.05, cg - 0.1, I["walnut"])
        y = 3.37
        while y < 6.03:
            self.flat.box(px - 0.055, y, z + 0.1, px - 0.03, y + 0.03, cg - 0.1, I["walnut"])
            y += 0.075
        kit.place("modern_wooden_cabinet", (px - 0.36, 4.7, z), rz=-R90, collection=self.c)
        self.flat.box(px - 0.1, 3.85, z + 1.05, px - 0.065, 5.55, z + 2.02, I["cab_dark"])
        self.flat.box(px - 0.103, 3.87, z + 1.07, px - 0.1, 5.53, z + 2.0, I["screen"])
        self.art("y", TE, 5.4, z + 1.6, 1.0, 1.3, 1)
        self.spots(0.6, 0.6, 7.2, 5.9, cg, 4, 3)
        # LED cove strip along the TV wall + two warm fill lights
        kit.area_light((3.7, 3.2, cg - 0.05), 2.5, 260, rot=(0, 0, 0), collection=self.c, size_y=2.5, name="living_fill")
        # floor lamp behind the lounge chair
        self.flat.cyl((0.75, 2.2, z), (0.75, 2.2, z + 0.03), 0.16, I["cab_dark"], seg=16)
        self.flat.cyl((0.75, 2.2, z), (0.75, 2.2, z + 1.5), 0.012, I["brass"], seg=8)
        self.flat.cyl((0.75, 2.2, z + 1.45), (0.75, 2.2, z + 1.8), 0.2, I["art3"], seg=18, r1=0.14, caps=False)
        self.lamp((0.75, 2.2, z + 1.62), 25, 0.06)
        # drapes gathered at the ends of both sliders
        self.curtain("x", 0.34, 0.5, 1.15, z + 0.02, z + 2.75, I["drape"])
        self.curtain("x", 0.34, 6.35, 7.0, z + 0.02, z + 2.75, I["drape"])
        self.curtain("y", 0.34, 4.7, 5.3, z + 0.02, z + 2.75, I["drape"])

    def dining(self):
        I, z = self.I, Z0
        cg = Z1 - SL
        cx, cy = 2.7, 8.55
        self.flat.box(cx - 1.75, cy - 1.3, z, cx + 1.75, cy + 1.3, z + 0.012, I["rug2"])
        # table: thick oak top on black steel legs
        self.hard.box(cx - 1.2, cy - 0.5, z + 0.71, cx + 1.2, cy + 0.5, z + 0.76, I["walnut"])
        for sx in (-0.95, 0.95):
            self.hard.box(cx + sx - 0.04, cy - 0.38, z, cx + sx + 0.04, cy + 0.38, z + 0.71, I["cab_dark"])
            self.hard.box(cx + sx - 0.3, cy - 0.38, z, cx + sx + 0.3, cy - 0.3, z + 0.03, I["cab_dark"])
            self.hard.box(cx + sx - 0.3, cy + 0.3, z, cx + sx + 0.3, cy + 0.38, z + 0.03, I["cab_dark"])
        for i in range(3):
            x = cx - 0.75 + i * 0.75
            kit.place("dining_chair_02", (x, cy - 0.72, z), rz=0.0 + self.rnd.uniform(-0.06, 0.06), collection=self.c)
            kit.place("dining_chair_02", (x, cy + 0.72, z), rz=math.pi + self.rnd.uniform(-0.06, 0.06), collection=self.c)
        kit.place("dining_chair_02", (cx - 1.45, cy, z), rz=-R90, collection=self.c)
        kit.place("dining_chair_02", (cx + 1.45, cy, z), rz=R90, collection=self.c)
        for dx in (-0.75, 0.0, 0.75):
            kit.place("modern_ceiling_lamp_01", (cx + dx, cy, cg - 1.17), collection=self.c)
            self.lamp((cx + dx, cy, cg - 0.85), 18, 0.1)
        # table setting: runner, bowl, plates
        self.flat.box(cx - 1.0, cy - 0.16, z + 0.76, cx + 1.0, cy + 0.16, z + 0.764, I["drape"])
        self.flat.cyl((cx, cy, z + 0.765), (cx, cy, z + 0.84), 0.1, I["ceramic"], seg=18, r1=0.17, caps=False)
        for i in range(3):
            for s in (-1, 1):
                self.flat.cyl((cx - 0.75 + i * 0.75, cy + s * 0.33, z + 0.762), (cx - 0.75 + i * 0.75, cy + s * 0.33, z + 0.772), 0.13, I["ceramic"], seg=20)
        # sideboard + art on the south wall stub, plant in the corner
        self.hard.box(4.55, 9.2, z, 5.1, 10.6, z + 0.85, I["oak"])
        self.art("y", 5.2 - TI / 2, 9.9, z + 1.6, 0.9, 0.7, -1)
        kit.place("potted_plant_01", (0.7, 10.3, z), collection=self.c, scale=1.2)
        self.spots(0.6, 6.6, 4.9, 10.5, cg, 2, 2)
        self.curtain("y", 0.36, 6.55, 7.1, z + 0.02, z + 2.7, I["sheer"])
        self.curtain("y", 0.36, 10.1, 10.65, z + 0.02, z + 2.7, I["sheer"])

    def kitchen(self):
        I, z = self.I, Z0
        cg = Z1 - SL
        C, Cd, Mb = I["cab"], I["cab_dark"], I["marble"]
        yb = 11.0 - TE
        # north run: base units, worktop, sink under the window, hob + hood
        self.hard.box(5.3, yb - 0.6, z + 0.1, 9.93, yb, z + 0.88, Cd)
        self.hard.box(5.3, yb - 0.55, z, 9.93, yb, z + 0.1, I["cab_dark"])
        self.hard.box(5.28, yb - 0.63, z + 0.88, 9.93, yb, z + 0.92, Mb)
        self.flat.box(5.3, yb - 0.02, z + 0.92, 9.93, yb, z + 1.1, Mb)              # upstand
        x = 5.3
        while x < 9.9:                                                              # door lines + handles
            self.flat.box(x - 0.002, yb - 0.604, z + 0.12, x + 0.002, yb - 0.6, z + 0.86, I["black"])
            self.flat.box(x + 0.06, yb - 0.625, z + 0.8, x + 0.4, yb - 0.6, z + 0.815, I["inox"])
            x += 0.58
        self.flat.box(7.1, yb - 0.5, z + 0.9, 7.9, yb - 0.12, z + 0.925, I["inox"])    # sink
        self.flat.box(7.14, yb - 0.46, z + 0.921, 7.86, yb - 0.16, z + 0.926, I["cab_dark"])
        self.flat.cyl((7.5, yb - 0.08, z + 0.92), (7.5, yb - 0.08, z + 1.22), 0.014, I["inox"], seg=8)
        self.flat.cyl((7.5, yb - 0.08, z + 1.22), (7.5, yb - 0.26, z + 1.2), 0.012, I["inox"], seg=8)
        self.flat.box(8.95, yb - 0.52, z + 0.92, 9.75, yb - 0.08, z + 0.928, I["black"])   # induction hob
        self.hard.box(8.95, yb - 0.45, z + 1.75, 9.75, yb, z + 1.85, I["inox"])            # hood
        self.hard.box(9.2, yb - 0.3, z + 1.85, 9.5, yb, cg, I["inox"])
        self.hard.box(5.3, yb - 0.35, z + 1.5, 6.1, yb, z + 2.3, C)                         # wall units
        self.flat.box(5.698, yb - 0.354, z + 1.52, 5.702, yb - 0.35, z + 2.28, I["black"])
        # tall units on the south wall: fridge-freezer + oven tower
        ys = 6.2 + TI / 2
        self.hard.box(5.3, ys, z, 6.25, ys + 0.68, z + 2.05, I["inox"])                    # fridge
        self.flat.box(5.77, ys + 0.68, z + 0.05, 5.776, ys + 0.684, z + 2.0, I["black"])
        for xx in (5.72, 5.8):
            self.flat.box(xx, ys + 0.68, z + 0.9, xx + 0.02, ys + 0.72, z + 1.5, I["cab_dark"])
        self.hard.box(6.3, ys, z, 7.55, ys + 0.62, z + 2.3, C)
        self.flat.box(6.38, ys + 0.62, z + 0.85, 6.98, ys + 0.63, z + 1.4, I["black"])     # oven
        self.flat.box(6.38, ys + 0.62, z + 1.48, 6.98, ys + 0.63, z + 1.85, I["black"])    # microwave
        self.flat.box(6.4, ys + 0.63, z + 1.36, 6.96, ys + 0.66, z + 1.38, I["inox"])
        # island with waterfall marble top and three stools
        ix0, ix1, iy0, iy1 = 6.2, 8.5, 8.15, 9.1
        self.hard.box(ix0 + 0.04, iy0 + 0.25, z, ix1 - 0.04, iy1 - 0.04, z + 0.88, I["walnut"])
        self.hard.box(ix0, iy0, z + 0.88, ix1, iy1, z + 0.93, Mb)
        self.hard.box(ix0, iy0, z, ix0 + 0.05, iy1, z + 0.88, Mb)
        self.hard.box(ix1 - 0.05, iy0, z, ix1, iy1, z + 0.88, Mb)
        for i in range(3):
            kit.place("bar_chair_round_01", (6.75 + i * 0.6, iy0 - 0.25, z), collection=self.c, rz=self.rnd.uniform(0, 3))
        for dx in (6.8, 7.9):
            kit.place("modern_ceiling_lamp_01", (dx, 8.62, cg - 1.17), collection=self.c)
            self.lamp((dx, 8.62, cg - 0.85), 18, 0.1)
        # worktop dressing
        kit.place("potted_plant_04", (6.6, 8.7, z + 0.93), collection=self.c, scale=1.3)
        self.flat.cyl((8.05, 8.6, z + 0.93), (8.05, 8.6, z + 1.0), 0.14, I["oak"], seg=18, r1=0.17, caps=False)
        self.flat.cyl((6.0, yb - 0.3, z + 0.92), (6.0, yb - 0.3, z + 1.17), 0.07, I["inox"], seg=14)       # kettle
        self.spots(5.6, 6.9, 9.7, 10.4, cg, 3, 2)
        kit.area_light((7.5, 8.6, cg - 0.05), 2.0, 180, collection=self.c, size_y=2.0, name="kitchen_fill")
        # store / laundry: shelving and washing machine
        self.hard.box(10.2, 11.0 - TE - 0.6, z, 10.8, 11.0 - TE, z + 0.85, I["ceramic"])
        self.flat.cyl((10.5, 11.0 - TE - 0.605, z + 0.45), (10.5, 11.0 - TE - 0.6, z + 0.45), 0.2, I["black"], seg=20)

    def hall(self):
        I, z = self.I, Z0
        cg = Z1 - SL
        # console + round mirror by the entrance, plant under the landing
        self.hard.box(7.75, 1.45, z + 0.76, 8.25, 1.5 + 1.3, z + 0.8, I["walnut"])
        for yy in (1.5, 2.72):
            self.hard.box(7.78, yy, z, 7.81, yy + 0.03, z + 0.76, I["cab_dark"])
            self.hard.box(8.19, yy, z, 8.22, yy + 0.03, z + 0.76, I["cab_dark"])
        kit.place("potted_plant_02", (9.4, 5.75, z), collection=self.c, scale=1.3)
        self.flat.box(8.4, 1.5, z, 10.0, 2.6, z + 0.012, I["rug2"])
        self.spots(7.8, 1.5, 10.9, 2.7, cg, 2, 1)
        # stairwell pendant cluster hanging from the roof slab
        for (dx, dy, dl) in [(0, 0, 2.6), (0.35, 0.25, 3.2), (-0.3, 0.3, 2.1), (0.1, -0.35, 3.7)]:
            p = Vector((10.0 + dx, 4.3 + dy, ZR - SL))
            self.flat.cyl(p, p - Vector((0, 0, dl)), 0.004, I["cab_dark"], seg=4, caps=False)
            q = p - Vector((0, 0, dl + 0.09))
            self.flat.cyl(q + Vector((0, 0, 0.09)), q + Vector((0, 0, 0.14)), 0.03, I["brass"], seg=10)
            self.flat.cyl(q - Vector((0, 0, 0.09)), q + Vector((0, 0, 0.09)), 0.09, I["bulb"], seg=14)
            self.lamp(q, 14, 0.09)

    def guest_room(self):
        I, z = self.I, Z0
        self.bed(13.6, 4.3, z, -R90, w=1.6)            # head against the east wall
        self.flat.box(11.9, 3.2, z, 13.9, 5.0, z + 0.012, I["rug2"])
        self.wardrobe(11.3, 0.3, 11.9, 1.45, z, ax="y", face=1)
        self.curtain("x", 0.36, 11.7, 14.5, z + 0.3, z + 2.7, I["sheer"])
        self.spots(11.8, 0.8, 14.4, 4.8, Z1 - SL, 2, 2)
        # guest bath
        self.vanity(11.95, 7.4 - TI / 2 - 0.27, z, 0.0, w=1.0)
        self.toilet(13.2, 7.4 - TI / 2 - 0.32, z, 0.0)
        self.shower(13.9, 5.3, 14.74, 6.3, z)
        self.H_glass(13.88, 5.3, 13.88, 6.3, z, 2.0)

    def H_glass(self, x0, y0, x1, y1, z, h):
        G = self.I["glass_rail"]
        if x0 == x1:
            self.flat.box(x0 - 0.005, y0, z + 0.03, x0 + 0.005, y1, z + h, G)
        else:
            self.flat.box(x0, y0 - 0.005, z + 0.03, x1, y0 + 0.005, z + h, G)

    def master(self):
        I, z = self.I, Z1
        cg = ZR - SL
        self.flat.box(1.6, 2.7, z, 4.7, 5.6, z + 0.014, I["rug"])
        self.bed(3.15, 5.05, z, 0.0, w=2.0)
        # bench at the foot, lounge corner by the balcony door, dresser + mirror, TV
        self.sb(self.T(3.15, 3.7, z), 0, 0, 0.3, 1.5, 0.42, 0.16, I["sofa_dark"])
        for s in (-0.6, 0.6):
            self.hard.box(3.15 + s - 0.02, 3.55, z, 3.15 + s + 0.02, 3.85, z + 0.22, I["brass"])
        kit.place("modern_arm_chair_01", (5.6, 2.0, z), rz=math.radians(150), collection=self.c)
        kit.place("side_table_01", (6.35, 1.85, z), collection=self.c)
        kit.place("potted_plant_01", (0.7, 2.1, z), collection=self.c, scale=1.1)
        px = 7.5 - TI / 2
        self.hard.box(px - 0.45, 3.4, z, px, 5.2, z + 0.75, I["walnut"])
        self.flat.box(px - 0.06, 3.6, z + 1.0, px - 0.03, 5.0, z + 1.8, I["cab_dark"])
        self.flat.box(px - 0.063, 3.62, z + 1.02, px - 0.06, 4.98, z + 1.78, I["screen"])
        self.art("y", TE, 3.85, z + 1.5, 0.7, 0.9, 1)
        self.curtain("x", 1.5 + 0.2, 0.5, 1.35, z + 0.02, z + 2.65, I["drape"])
        self.curtain("x", 1.5 + 0.2, 6.15, 7.0, z + 0.02, z + 2.65, I["drape"])
        self.curtain("x", 1.5 + 0.26, 1.4, 3.2, z + 0.02, z + 2.65, I["sheer"])
        self.spots(0.8, 2.2, 7.0, 5.8, cg, 3, 2)
        kit.area_light((3.6, 3.6, cg - 0.05), 2.0, 160, collection=self.c, size_y=2.0, name="master_fill")
        # master bath: freestanding tub, double vanity, wc, walk-in shower
        bz = z
        tub = self.T(1.75, 10.1, bz)
        self.sb(tub, 0, 0, 0.3, 1.75, 0.8, 0.58, I["ceramic"])
        self.sb(tub, 0, 0, 0.56, 1.55, 0.6, 0.08, I["wall_tile"])
        self.flat.cyl((0.85, 10.3, bz), (0.85, 10.3, bz + 0.95), 0.02, I["brass"], seg=8)
        self.flat.cyl((0.85, 10.3, bz + 0.95), (1.05, 10.2, bz + 0.92), 0.015, I["brass"], seg=8)
        self.vanity(TE + 0.27, 7.7, bz, R90, w=1.7, double=True)
        self.toilet(3.4 - TI / 2 - 0.3, 9.9, bz, -R90)
        self.shower(2.2, 6.2 + TI / 2, 3.33, 7.5, bz)
        self.H_glass(2.18, 6.3, 2.18, 7.5, bz, 2.1)
        self.spots(0.7, 6.8, 3.0, 10.4, cg, 2, 2)
        # walk-in closet
        self.wardrobe(3.4 + TI / 2, 7.9, 4.05, 10.7, z, ax="y", face=1, mat=I["oak"])
        self.wardrobe(5.5, 7.9, 6.2 - TI / 2, 10.7, z, ax="y", face=-1, mat=I["oak"])
        self.sb(self.T(4.8, 9.2, z), 0, 0, 0.22, 0.5, 1.1, 0.44, I["sofa_dark"])
        self.spots(4.2, 6.8, 5.4, 10.4, cg, 1, 2)

    def bedrooms(self):
        I, z = self.I, Z1
        cg = ZR - SL
        # bedroom 2 (front right) – head against the north wall
        self.bed(13.0, 4.05, z, 0.0, w=1.6, mat_frame=I["oak"])
        self.flat.box(11.9, 2.2, z, 14.2, 4.4, z + 0.012, I["rug2"])
        self.wardrobe(11.2 + TI / 2, 3.0, 11.85, 5.1, z, ax="y", face=1)
        self.curtain("x", 1.0 + 0.2, 11.6, 12.3, z + 0.02, z + 2.6, I["drape"])
        self.curtain("x", 1.0 + 0.2, 14.0, 14.7, z + 0.02, z + 2.6, I["drape"])
        self.hard.box(14.2, 1.3, z + 0.72, 14.74, 2.6, z + 0.76, I["oak"])          # desk
        self.hard.box(14.22, 1.32, z, 14.26, 1.36, z + 0.72, I["cab_dark"])
        self.hard.box(14.22, 2.54, z, 14.26, 2.58, z + 0.72, I["cab_dark"])
        self.spots(11.8, 1.6, 14.4, 4.8, cg, 2, 2)
        # bedroom 3 (back centre) – head against the west wall
        self.bed(7.4, 9.2, z, R90, w=1.5, mat_frame=I["oak"], throw=False)
        self.wardrobe(8.6, 7.4 + TI / 2, 9.9, 8.0, z, ax="x", face=1)
        self.curtain("x", 11.0 - TE - 0.12, 6.4, 9.4, z + 0.3, z + 2.6, I["sheer"])
        self.spots(6.8, 8.0, 9.6, 10.4, cg, 2, 1)
        # bedroom 4 (back right) – head against the west wall
        self.bed(11.2, 9.25, z, R90, w=1.6)
        self.wardrobe(13.4, 7.4 + TI / 2, 14.74, 8.05, z, ax="x", face=1)
        self.curtain("x", 11.0 - TE - 0.12, 11.1, 13.9, z + 0.3, z + 2.6, I["sheer"])
        self.spots(10.6, 8.0, 14.4, 10.4, cg, 2, 1)
        # bath 2
        self.vanity(12.0, 7.4 - TI / 2 - 0.27, z, 0.0, w=1.0)
        self.toilet(13.3, 7.4 - TI / 2 - 0.32, z, 0.0)
        self.shower(13.9, 5.3, 14.74, 6.3, z)
        self.H_glass(13.88, 5.3, 13.88, 6.3, z, 2.0)
        # upstairs lounge by the front window + corridor
        kit.place("modern_arm_chair_01", (9.3, 0.75, z), rz=math.radians(200), collection=self.c)
        kit.place("modern_arm_chair_01", (10.5, 0.8, z), rz=math.radians(160), collection=self.c)
        kit.place("coffee_table_round_01", (9.9, 1.6, z), collection=self.c, scale=0.55)
        kit.place("potted_plant_02", (8.1, 0.2, z), collection=self.c, scale=1.1)
        self.art("y", 7.5 + TI / 2, 4.6, z + 1.5, 1.2, 0.8, 1)
        self.spots(7.8, 0.2, 10.9, 2.4, cg, 2, 1)
        self.spots(7.9, 3.4, 8.6, 7.0, cg, 1, 3)
        kit.area_light((9.4, 1.4, cg - 0.05), 1.5, 90, collection=self.c, size_y=1.5, name="lounge_fill")
        # master balcony: two chairs + table, planter
        kit.place("outdoor_table_chair_set_01", (5.6, 0.5, z), rz=R90, collection=self.c)
        kit.place("potted_plant_01", (0.55, 0.9, z), collection=self.c, scale=1.2)
        kit.place("potted_plant_02", (11.7, 0.4, z), collection=self.c, scale=1.0)

    def build(self):
        self.living(), self.dining(), self.kitchen(), self.hall(), self.guest_room(), self.master(), self.bedrooms()
        # exterior downlights recorded by the shell
        for (x, y, z) in self.H.spots:
            self.spot(x, y, z)
        a = self.soft.build("int_soft", self.c, bevel=0.035)
        b = self.hard.build("int_hard", self.c, bevel=0.004)
        f = self.flat.build("int_flat", self.c)
        return [a, b, f]


def build(c, H, S=None):
    return Interior(c, H).build()
