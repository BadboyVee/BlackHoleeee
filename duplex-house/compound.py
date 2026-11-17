"""Compound (fence, gate, drive, pool, carport, BQ, services, planting) and the
surrounding neighbourhood (street, drains, poles, neighbouring houses, trees).
Plot: x -13..25, y -13..23.  Street runs along X, south of the plot.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import kit
import plants
from kit import MB

PX0, PX1, PY0, PY1 = -13.0, 25.0, -13.0, 23.0
GATE = (15.5, 20.5)          # main sliding gate opening along the south wall
PGATE = (13.3, 14.3)         # pedestrian gate
ROAD_Y0, ROAD_Y1 = -22.0, -15.0


def site_materials(M):
    S = dict(M)
    S["pavers"] = kit.mat_pbr("pavers", "concrete_pavers", size=1.6, val=1.15, sat=0.6, rough_mul=1.0)
    S["lawn"] = kit.mat_pbr("lawn", "sparse_grass", size=3.0, normal=1.0,
                            ramp=[(0.05, (0.03, 0.09, 0.015)), (0.35, (0.1, 0.24, 0.04)), (0.8, (0.26, 0.42, 0.09))])
    S["asphalt"] = kit.mat_pbr("asphalt", "asphalt_02", size=5.0, val=0.75)
    S["deck"] = kit.mat_pbr("deck", "wood_floor_deck", size=1.8, tint=(0.75, 0.62, 0.5), rough_mul=0.9)
    S["pool_tile"] = kit.mat_pbr("pool_tile", "long_white_tiles", size=1.0, tint=(0.2, 0.62, 0.85), rough_mul=0.4)
    S["coping"] = kit.mat_pbr("coping", "marble_01", size=2.0, val=1.1, rough_mul=0.8)
    S["water"] = kit.mat_water("pool_water", color=(0.62, 0.9, 0.95))
    S["soil"] = kit.mat_pbr("soil", "dirt", size=2.0, val=0.55)
    S["laterite"] = kit.mat_pbr("laterite", "red_laterite_soil_stones", size=4.0, val=0.9, sat=0.8)
    S["gravel"] = kit.mat_pbr("gravel", "gravel_floor_02", size=2.0, val=0.8)
    S["kerb"] = kit.mat_pbr("kerb", "concrete_floor_02", size=2.0, val=1.25)
    S["black_metal"] = kit.mat_plain("black_metal", (0.015, 0.015, 0.017), rough=0.45, metal=0.6)
    S["gate_slat"] = kit.mat_plain("gate_slat", (0.03, 0.03, 0.035), rough=0.4, metal=0.7)
    S["tank"] = kit.mat_plain("tank_black", (0.02, 0.02, 0.02), rough=0.55)
    S["panel"] = kit.mat_plain("solar_panel", (0.01, 0.015, 0.05), rough=0.12, spec=0.8, coat=0.5)
    S["ac"] = kit.mat_plain("ac_white", (0.82, 0.82, 0.8), rough=0.45)
    S["lamp"] = kit.mat_emit("lamp_warm", (1.0, 0.85, 0.6), 3.0)
    S["cushion"] = kit.mat_pbr("cushion", "rough_linen", size=0.6, val=1.1)
    S["umbrella"] = kit.mat_pbr("umbrella", "rough_linen", size=0.6, tint=(0.95, 0.93, 0.85))
    S["roof_red"] = kit.mat_pbr("roof_red", "box_profile_metal_sheet", size=1.6, val=0.8, rot=math.pi / 2)
    S["roof_brown"] = kit.mat_pbr("roof_brown", "clay_roof_tiles_02", size=2.2, tint=(0.55, 0.4, 0.33), sat=0.6)
    S["roof_char"] = kit.mat_pbr("roof_char", "grey_roof_tiles_02", size=2.2, tint=(0.4, 0.4, 0.42))
    S["nb_cream"] = kit.mat_pbr("nb_cream", "painted_plaster_wall", size=3.0, tint=(1.0, 0.9, 0.72), val=1.25, sat=0.2)
    S["nb_peach"] = kit.mat_pbr("nb_peach", "painted_plaster_wall", size=3.0, tint=(1.0, 0.8, 0.66), val=1.2, sat=0.2)
    S["nb_grey"] = kit.mat_pbr("nb_grey", "painted_plaster_wall", size=3.0, tint=(0.72, 0.74, 0.76), val=1.2, sat=0.2)
    S["nb_white"] = kit.mat_pbr("nb_white", "painted_plaster_wall", size=3.0, val=1.3, sat=0.2)
    S["nb_glass"] = kit.mat_plain("nb_glass", (0.02, 0.03, 0.035), rough=0.04, spec=1.0, metal=0.2)
    S["trim_brown"] = kit.mat_plain("trim_brown", (0.12, 0.07, 0.04), rough=0.5)
    S["kerb_w"] = kit.mat_plain("kerb_white", (0.82, 0.82, 0.78), rough=0.8)
    S["kerb_b"] = kit.mat_plain("kerb_black", (0.035, 0.035, 0.035), rough=0.8)
    S["road_paint"] = kit.mat_plain("road_paint", (0.75, 0.74, 0.68), rough=0.9)
    S["bump_y"] = kit.mat_plain("bump_yellow", (0.85, 0.62, 0.05), rough=0.8)
    S["bin"] = kit.mat_plain("bin_green", (0.03, 0.2, 0.08), rough=0.45)
    S["sign"] = kit.mat_plain("sign_green", (0.02, 0.22, 0.12), rough=0.4)
    S["flower_a"] = kit.mat_plain("bougainvillea", (0.75, 0.05, 0.3), rough=0.6)
    S["flower_b"] = kit.mat_plain("ixora", (0.9, 0.3, 0.05), rough=0.6)
    return S


class Site:
    def __init__(self, collection, M, seed=7):
        self.c = collection
        self.S = site_materials(M)
        self.rnd = random.Random(seed)
        self.g, self.d, self.gl = MB(), MB(), MB()     # ground, details, glass/water
        self.nb = MB()                                 # neighbourhood
        self.lights = []
        self.trees = []          # (kind, x, y, scale)
        self.palms = []          # (x, y, height)
        self.shrubs = []         # (x, y, scale, variant)
        self.flowers = []        # (x, y, scale): flowering ground cover along the walls
        self.variants = []       # library collections of restyled duplexes for the neighbours
        self.street_cars = []    # library collections of real cars for drives and kerbs
        self.cars_placed = []    # (collection, x, y, heading_deg)

    def ring(self, x0, y0, x1, y1, hole, z0, z1, mat, mb=None):
        """Slab x0..x1,y0..y1 with a rectangular hole (hx0,hy0,hx1,hy1)."""
        mb = mb or self.g
        hx0, hy0, hx1, hy1 = hole
        for (a, b, c, d) in [(x0, y0, x1, hy0), (x0, hy1, x1, y1), (x0, hy0, hx0, hy1), (hx1, hy0, x1, hy1)]:
            mb.box(a, b, z0, c, d, z1, mat, skip="-z")

    # ------------------------------------------------------- ground ---
    def ground(self):
        S, g = self.S, self.g
        # big earth plane + grass verge far field
        hole = (-10.6, 0.4, -4.0, 5.4)                       # the pool
        self.ring(-420, -420, 420, 420, hole, -0.5, -0.12, S["laterite"])
        # plot base lawn
        self.ring(PX0, PY0, PX1, PY1, hole, -0.12, 0.0, S["lawn"])
        # drive / parking court (pavers) with concrete kerb
        g.box(7.5, PY0 + 0.1, -0.1, PX1 - 0.1, 14.0, 0.03, S["pavers"], skip="-z")
        g.box(11.5, 14.0, -0.1, PX1 - 0.1, PY1 - 0.1, 0.03, S["concrete"], skip="-z")
        g.box(7.35, PY0 + 0.1, -0.1, 7.5, -2.6, 0.09, S["kerb"])
        g.box(-0.5, 11.6, -0.1, 11.5, 11.75, 0.09, S["kerb"])
        g.box(-0.5, 11.0, -0.1, 11.5, 11.6, 0.03, S["pavers"], skip="-z")     # back path
        g.box(11.35, 14.0, -0.1, 11.5, PY1 - 0.1, 0.09, S["kerb"])
        # front terrace (L-shape round the living room) + steps
        T, Gy = S["out_tile"], S["grey"]
        g.box(-2.4, -2.6, 0.0, 7.5, -0.04, 0.42, Gy, {"+z": T})
        g.box(-2.4, -0.04, 0.0, -0.04, 5.6, 0.42, Gy, {"+z": T})
        for i, (yy, zz) in enumerate([(-3.2, 0.14), (-2.9, 0.28)]):
            g.box(1.0, yy, 0.0, 6.5, -2.6, zz, Gy, {"+z": T})
        # porch steps
        for (yy, zz) in [(-0.9, 0.15), (-0.6, 0.30), (-0.3, 0.449)]:
            g.box(7.5, yy, 0.0, 11.2, -0.04, zz, Gy, {"+z": T})
        # low planters each side of the porch steps
        for (xa, xb) in [(6.6, 7.5), (11.2, 12.1)]:
            g.box(xa, -1.5, 0.0, xb, -0.05, 0.62, Gy, {"+z": S["soil"]})
            for k in range(3):
                self.shrubs.append((xa + 0.45, -1.25 + k * 0.5, 0.33, k % 4, 0.55))

    # --------------------------------------------------------- pool ---
    def pool(self):
        S, g = self.S, self.g
        x0, x1, y0, y1 = -10.6, -4.0, 0.4, 5.4
        dz = 0.12
        D = S["deck"]
        # deck (box ring round the pool)
        dx0, dx1, dy0, dy1 = -12.3, -2.4, -1.4, 8.6
        for (a, b, c, d) in [(dx0, dy0, dx1, y0), (dx0, y1, dx1, dy1), (dx0, y0, x0, y1), (x1, y0, dx1, y1)]:
            g.box(a, b, 0.0, c, d, dz, D)
        cw = 0.32
        C = S["coping"]
        for (a, b, c, d) in [(x0 - cw, y0 - cw, x1 + cw, y0), (x0 - cw, y1, x1 + cw, y1 + cw),
                             (x0 - cw, y0, x0, y1), (x1, y0, x1 + cw, y1)]:
            g.box(a, b, dz - 0.02, c, d, dz + 0.035, C)
        P = S["pool_tile"]
        zb = -1.45
        g.face([(x0, y0, zb), (x1, y0, zb), (x1, y1, zb), (x0, y1, zb)], P)
        g.face([(x0, y0, zb), (x0, y0, dz), (x1, y0, dz), (x1, y0, zb)], P)
        g.face([(x1, y1, zb), (x1, y1, dz), (x0, y1, dz), (x0, y1, zb)], P)
        g.face([(x0, y1, zb), (x0, y1, dz), (x0, y0, dz), (x0, y0, zb)], P)
        g.face([(x1, y0, zb), (x1, y0, dz), (x1, y1, dz), (x1, y1, zb)], P)
        # entry steps in the shallow corner
        for i in range(4):
            g.box(x1 - 1.6, y0, zb, x1, y0 + 0.35 * (4 - i), -0.25 - 0.28 * (3 - i) + 0.0, P)
        self.gl.box(x0, y0, zb + 0.01, x1, y1, 0.02, S["water"], skip="-z")
        # steel ladder
        St = S["steel"]
        for yy in (y1 - 0.9, y1 - 0.4):
            self.d.cyl((x0 + 0.02, yy, -0.8), (x0 + 0.02, yy, 0.85), 0.02, St, seg=8)
            self.d.cyl((x0 + 0.02, yy, 0.85), (x0 - 0.35, yy, 0.85), 0.02, St, seg=8)
            self.d.cyl((x0 - 0.35, yy, 0.85), (x0 - 0.35, yy, dz), 0.02, St, seg=8)
        for zz in (-0.7, -0.4, -0.1):
            self.d.box(x0 + 0.0, y1 - 0.9, zz, x0 + 0.06, y1 - 0.4, zz + 0.03, St)
        # sun loungers + umbrella on the north deck
        for lx in (-9.2, -7.4):
            self.lounger(lx, 7.3, math.pi)
        self.umbrella(-8.3, 7.6, dz)
        self.lounger(-5.2, 7.3, math.pi)
        # outdoor shower post
        self.d.cyl((-11.9, 8.2, dz), (-11.9, 8.2, 2.25), 0.025, St, seg=10)
        self.d.cyl((-11.9, 8.2, 2.25), (-11.9, 7.85, 2.25), 0.02, St, seg=10)
        self.d.cyl((-11.9, 7.85, 2.25), (-11.9, 7.85, 2.2), 0.09, St, seg=14)

    def lounger(self, x, y, rz):
        S = self.S
        m = Matrix.Translation((x, y, 0.12)) @ Matrix.Rotation(rz, 4, "Z")
        Wd, Cu = S["wood_dark"], S["cushion"]
        self.d.obox(m @ Matrix.Translation((0, 0.3, 0.26)), 0.68, 1.45, 0.05, Wd)
        back = m @ Matrix.Translation((0, -0.42, 0.285)) @ Matrix.Rotation(math.radians(-32), 4, "X") @ Matrix.Translation((0, -0.3, 0.0))
        self.d.obox(back, 0.68, 0.72, 0.05, Wd)
        for sx in (-0.3, 0.3):
            for sy in (-0.3, 0.9):
                self.d.obox(m @ Matrix.Translation((sx, sy, 0.12)), 0.05, 0.05, 0.24, Wd)
        self.d.obox(m @ Matrix.Translation((0, 0.3, 0.33)), 0.62, 1.4, 0.09, Cu)
        self.d.obox(back @ Matrix.Translation((0, 0, 0.07)), 0.62, 0.68, 0.09, Cu)

    def umbrella(self, x, y, z):
        S = self.S
        self.d.cyl((x, y, z), (x, y, z + 2.5), 0.025, S["steel"], seg=10)
        self.d.cyl((x, y, z), (x, y, z + 0.06), 0.28, S["black_metal"], seg=20)
        n, R = 8, 1.5
        top = Vector((x, y, z + 2.62))
        ring = [Vector((x + R * math.cos(2 * math.pi * i / n), y + R * math.sin(2 * math.pi * i / n), z + 2.15)) for i in range(n)]
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            self.d.face([a, b, top], S["umbrella"])
            self.d.face([b, a, top - Vector((0, 0, 0.01))], S["umbrella"])
            self.d.cyl(top, a, 0.008, S["steel"], seg=5, caps=False)

    # -------------------------------------------------------- fence ---
    def fence_run(self, ax, c, a0, a1, mb=None, h=2.3, front=False, gaps=(), wire=True, mats=None):
        """Wall with pillars along an axis; gaps = [(u0,u1)] openings."""
        S = self.S
        mb = mb or self.d
        Wm = (mats or {}).get("wall", S["white"])
        Pm = (mats or {}).get("pillar", S["stone"] if front else S["white"])
        cap = S["grey"]
        t, pw = 0.2, 0.42
        spans, cur = [], a0
        for (u0, u1) in sorted(gaps):
            spans.append((cur, u0))
            cur = u1
        spans.append((cur, a1))

        def bx(u0, u1, z0, z1, tt, m, extra=None):
            if ax == "x":
                mb.box(u0, c - tt / 2, z0, u1, c + tt / 2, z1, m, extra)
            else:
                mb.box(c - tt / 2, u0, z0, c + tt / 2, u1, z1, m, extra)

        for (s0, s1) in spans:
            L = s1 - s0
            if L < 0.3:
                continue
            n = max(1, round(L / 3.3))
            for i in range(n + 1):
                u = s0 + L * i / n
                bx(u - pw / 2, u + pw / 2, 0, h + 0.25, pw, Pm)
                bx(u - pw / 2 - 0.05, u + pw / 2 + 0.05, h + 0.25, h + 0.33, pw + 0.1, cap)
                if wire:
                    # electric-fence bracket
                    bx(u - 0.015, u + 0.015, h + 0.33, h + 0.95, 0.03, S["black_metal"])
            for i in range(n):
                u0, u1 = s0 + L * i / n + pw / 2, s0 + L * (i + 1) / n - pw / 2
                bx(u0, u1, 0, 0.35, t + 0.04, S["grey"])
                bx(u0, u1, 0.35, h, t, Wm)
                bx(u0, u1, h, h + 0.06, t + 0.08, cap)
            if wire:
                for k in range(5):
                    z = h + 0.42 + k * 0.12
                    if ax == "x":
                        mb.cyl((s0, c, z), (s1, c, z), 0.005, S["steel"], seg=4, caps=False, smooth=False)
                    else:
                        mb.cyl((c, s0, z), (c, s1, z), 0.005, S["steel"], seg=4, caps=False, smooth=False)

    def fence(self):
        self.fence_run("x", PY0, PX0, PX1, front=True, gaps=[PGATE, GATE])
        self.fence_run("x", PY1, PX0, PX1)
        self.fence_run("y", PX0, PY0, PY1)
        self.fence_run("y", PX1, PY0, PY1)
        self.gate()

    def gate(self):
        S, d = self.S, self.d
        g0, g1 = GATE
        y = PY0 + 0.18            # gate slides just inside the wall
        slide = float(self.__dict__.get("gate_open", 0.0)) * (g1 - g0)
        a0, a1 = g0 - 0.25 - slide, g1 + 0.05 - slide
        B, Sl = S["black_metal"], S["gate_slat"]
        d.box(a0, y - 0.035, 0.08, a1, y + 0.035, 0.16, B)
        d.box(a0, y - 0.035, 2.25, a1, y + 0.035, 2.33, B)
        for u in (a0, a1 - 0.07, (a0 + a1) / 2 - 0.035):
            d.box(u, y - 0.035, 0.08, u + 0.07, y + 0.035, 2.33, B)
        z = 0.2
        while z < 2.2:
            d.box(a0 + 0.07, y - 0.012, z, a1 - 0.07, y + 0.012, z + 0.11, Sl)
            z += 0.135
        # track, guide post and motor box
        d.box(g0 - 5.4, y - 0.03, 0.03, g1 + 0.2, y + 0.03, 0.055, S["steel"])
        d.box(g0 - 0.55, y + 0.1, 0.03, g0 - 0.3, y + 0.38, 0.45, S["grey"])
        # pedestrian gate
        p0, p1 = PGATE
        d.box(p0, PY0 - 0.03, 0.05, p1, PY0 + 0.03, 2.2, Sl)
        d.box(p0, PY0 - 0.04, 0.05, p0 + 0.05, PY0 + 0.04, 2.25, B)
        d.box(p1 - 0.05, PY0 - 0.04, 0.05, p1, PY0 + 0.04, 2.25, B)
        d.box(p1 - 0.2, PY0 - 0.07, 1.0, p1 - 0.08, PY0 - 0.03, 1.04, S["steel"])
        # gate-pillar lanterns and house number plate
        for u in (g0, g1, p0, p1):
            d.box(u - 0.09, PY0 - 0.09, 2.63, u + 0.09, PY0 + 0.09, 2.66, B)
            d.box(u - 0.07, PY0 - 0.07, 2.66, u + 0.07, PY0 + 0.07, 2.86, S["lamp"])
            d.box(u - 0.1, PY0 - 0.1, 2.86, u + 0.1, PY0 + 0.1, 2.9, B)
        # gatehouse (security post)
        self.small_building(21.2, PY0 + 0.5, 24.3, PY0 + 3.5, 2.7, door=("w", 1.0), win=[("n", 0.8, 1.9), ("w", 2.0, 2.7)])

    def small_building(self, x0, y0, x1, y1, h, door=None, win=(), mb=None):
        S = self.S
        mb = mb or self.d
        mb.box(x0, y0, 0, x1, y1, h, S["white"])
        mb.box(x0 - 0.02, y0 - 0.02, 0, x1 + 0.02, y1 + 0.02, 0.4, S["grey"])
        mb.box(x0 - 0.45, y0 - 0.45, h, x1 + 0.45, y1 + 0.45, h + 0.16, S["grey"])

        def panel(side, a, b, z0, z1, m, t=0.03):
            if side == "w":
                mb.box(x0 - t, y0 + a, z0, x0, y0 + b, z1, m)
            elif side == "e":
                mb.box(x1, y0 + a, z0, x1 + t, y0 + b, z1, m)
            elif side == "s":
                mb.box(x0 + a, y0 - t, z0, x0 + b, y0, z1, m)
            else:
                mb.box(x0 + a, y1, z0, x0 + b, y1 + t, z1, m)

        if door:
            panel(door[0], door[1] - 0.45, door[1] + 0.45, 0.05, 2.1, S["wood_dark"])
        for (side, a, b) in win:
            panel(side, a, b, 1.0, 2.1, S["nb_glass"], t=0.02)
            panel(side, a - 0.05, b + 0.05, 0.95, 1.0, S["alu"], t=0.05)
            panel(side, a - 0.05, b + 0.05, 2.1, 2.15, S["alu"], t=0.05)

    # ------------------------------------------------------ carport ---
    def carport(self):
        S, d = self.S, self.d
        x0, x1, y0, y1 = 16.4, 23.4, 1.2, 7.6
        B = S["black_metal"]
        for (x, y) in [(x0 + 0.1, y0 + 0.3), (x1 - 0.1, y0 + 0.3), (x0 + 0.1, y1 - 0.3), (x1 - 0.1, y1 - 0.3)]:
            d.box(x - 0.07, y - 0.07, 0.03, x + 0.07, y + 0.07, 2.75, B)
        d.box(x0 - 0.3, y0 - 0.4, 2.75, x1 + 0.3, y1 + 0.3, 2.95, S["grey"], {"-z": S["wood"]})
        d.box(x0 - 0.33, y0 - 0.43, 2.95, x1 + 0.33, y1 + 0.33, 2.98, S["alu"])
        for sx in (x0 + 1.8, x1 - 1.8):
            self.lights.append(("spot", (sx, (y0 + y1) / 2, 2.74)))

    # ------------------------------------------- back-yard buildings ---
    def backyard(self):
        S, d = self.S, self.d
        # boys' quarters: two rooms, doors facing the house (south)
        x0, y0, x1, y1 = 15.8, 17.2, 24.4, 22.4
        self.small_building(x0, y0, x1, y1, 3.1, win=[("s", 0.7, 1.9), ("s", 5.0, 6.2), ("w", 1.5, 2.6)])
        for dx in (2.9, 7.2):
            d.box(x0 + dx - 0.45, y0 - 0.04, 0.2, x0 + dx + 0.45, y0, 2.3, S["wood_dark"])
        d.box(x0 - 0.2, y0 - 1.2, 0.0, x1 + 0.2, y0, 0.2, S["grey"], {"+z": S["out_tile"]})
        # generator house with louvred doors
        gx0, gy0, gx1, gy1 = 22.2, 10.2, 24.6, 13.0
        d.box(gx0, gy0, 0, gx1, gy1, 2.2, S["white"])
        d.box(gx0 - 0.2, gy0 - 0.2, 2.2, gx1 + 0.2, gy1 + 0.2, 2.32, S["grey"])
        z = 0.25
        while z < 1.95:
            d.box(gx0 - 0.03, gy0 + 0.35, z, gx0, gy1 - 0.35, z + 0.07, S["black_metal"])
            z += 0.11
        # water tower: steel stand with two black tanks
        tx, ty = 13.3, 19.6
        B = S["black_metal"]
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                d.box(tx + sx - 0.05, ty + sy - 0.05, 0, tx + sx + 0.05, ty + sy + 0.05, 4.5, B)
        for zz in (1.5, 3.0):
            d.box(tx - 1.05, ty - 1.05, zz, tx + 1.05, ty - 0.97, zz + 0.06, B)
            d.box(tx - 1.05, ty + 0.97, zz, tx + 1.05, ty + 1.05, zz + 0.06, B)
            d.box(tx - 1.05, ty - 1.05, zz, tx - 0.97, ty + 1.05, zz + 0.06, B)
            d.box(tx + 0.97, ty - 1.05, zz, tx + 1.05, ty + 1.05, zz + 0.06, B)
        d.box(tx - 1.2, ty - 1.2, 4.5, tx + 1.2, ty + 1.2, 4.6, B)
        self.tank(tx, ty, 4.6, 1.05, 1.9)
        # clothes line
        d.cyl((2.0, 16.5, 0), (2.0, 16.5, 1.9), 0.03, S["steel"], seg=8)
        d.cyl((8.0, 16.5, 0), (8.0, 16.5, 1.9), 0.03, S["steel"], seg=8)
        for dy in (-0.3, 0.3):
            d.cyl((2.0, 16.5 + dy, 1.85), (8.0, 16.5 + dy, 1.85), 0.004, S["steel"], seg=4, caps=False)
        d.cyl((2.0, 16.2, 1.85), (2.0, 16.8, 1.85), 0.02, S["steel"], seg=6)
        d.cyl((8.0, 16.2, 1.85), (8.0, 16.8, 1.85), 0.02, S["steel"], seg=6)

    def tank(self, x, y, z, r, h, mb=None):
        mb = mb or self.d
        T = self.S["tank"]
        n = 7
        for i in range(n):
            z0 = z + h * i / n
            mb.cyl((x, y, z0), (x, y, z0 + h / n - 0.03), r, T, seg=28, caps=False)
            mb.cyl((x, y, z0 + h / n - 0.03), (x, y, z0 + h / n), r * 0.97, T, seg=28, caps=False)
        mb.cyl((x, y, z + h), (x, y, z + h + 0.3), r, T, seg=28, r1=r * 0.35)
        mb.cyl((x, y, z + h + 0.3), (x, y, z + h + 0.38), r * 0.36, T, seg=16)

    # ------------------------------------------------ house services ---
    def services(self):
        """Things bolted to the house: AC units, roof tanks, solar, lights, pipes."""
        S, d = self.S, self.d
        A = S["ac"]

        def ac(x, y, z, facing):
            # outdoor condenser on a bracket; facing = '+x', '-x', '+y'
            if facing == "+x":
                d.box(x, y - 0.42, z, x + 0.32, y + 0.42, z + 0.6, A)
                d.cyl((x + 0.325, y - 0.1, z + 0.3), (x + 0.33, y - 0.1, z + 0.3), 0.23, S["black_metal"], seg=20)
            elif facing == "-x":
                d.box(x - 0.32, y - 0.42, z, x, y + 0.42, z + 0.6, A)
                d.cyl((x - 0.325, y - 0.1, z + 0.3), (x - 0.33, y - 0.1, z + 0.3), 0.23, S["black_metal"], seg=20)
            else:
                d.box(x - 0.42, y, z, x + 0.42, y + 0.32, z + 0.6, A)
                d.cyl((x - 0.1, y + 0.325, z + 0.3), (x - 0.1, y + 0.33, z + 0.3), 0.23, S["black_metal"], seg=20)

        ac(15.0, 4.6, 0.8, "+x"), ac(15.0, 4.6, 4.2, "+x"), ac(15.0, 7.7, 4.2, "+x")
        ac(0.0, 6.6, 4.3, "-x"), ac(5.0, 11.0, 0.7, "+y"), ac(10.2, 11.0, 4.2, "+y")
        # rainwater downpipes
        for (x, y) in [(15.06, 10.8), (-0.06, 10.8), (15.06, 1.3)]:
            d.cyl((x, y, 0.1), (x, y, 6.9), 0.045, S["white"], seg=10)
        # roof: solar array, tank, sat dish
        for i in range(4):
            for j in range(2):
                x, y = 1.2 + i * 1.15, 3.0 + j * 2.15
                m = Matrix.Translation((x + 0.5, y + 1.0, 7.22)) @ Matrix.Rotation(math.radians(-12), 4, "X")
                d.obox(m, 1.05, 2.0, 0.04, S["panel"])
                d.obox(m @ Matrix.Translation((0, 0, -0.03)), 1.07, 2.02, 0.03, S["steel"])
        self.tank(9.4, 2.2, 6.95, 0.75, 1.15)
        d.cyl((13.0, 9.0, 6.95), (13.0, 9.0, 7.9), 0.03, S["steel"], seg=8)
        d.cyl((13.0, 9.0, 7.95), (13.25, 8.8, 8.1), 0.42, S["ac"], seg=22, r1=0.05)
        # exterior wall lights (up/down sconces)
        for (x, y, z) in [(7.9, -0.56, 3.1), (10.8, -0.56, 3.1), (-0.3, -1.0, 2.6), (15.02, 9.9, 2.6), (3.0, 11.02, 2.7), (12.9, 11.02, 2.7)]:
            d.box(x - 0.05, y - 0.05, z, x + 0.05, y + 0.05, z + 0.22, S["black_metal"])
        # CCTV domes
        for (x, y, z) in [(0.1, -0.1, 3.3), (14.9, -0.1, 3.3), (14.9, 11.1, 3.3)]:
            d.cyl((x, y, z), (x, y, z - 0.08), 0.06, S["ac"], seg=12, r1=0.03)

    # ----------------------------------------------------- planting ---
    def planting(self):
        S, g, r = self.S, self.g, self.rnd
        # beds along the inside of the front and west walls
        g.box(PX0 + 0.25, PY0 + 0.25, 0.0, 12.6, PY0 + 1.5, 0.08, S["kerb"], {"+z": S["soil"]})
        g.box(PX0 + 0.25, PY0 + 1.5, 0.0, PX0 + 1.5, PY1 - 0.3, 0.08, S["kerb"], {"+z": S["soil"]})
        g.box(PX0 + 1.5, PY1 - 1.5, 0.0, 11.0, PY1 - 0.3, 0.08, S["kerb"], {"+z": S["soil"]})
        g.box(PX1 - 1.3, -8.5, 0.0, PX1 - 0.25, 9.8, 0.1, S["kerb"], {"+z": S["soil"]})
        x = PX0 + 1.0
        k = 0
        while x < 12.2:
            self.shrubs.append((x, PY0 + 0.9, r.uniform(0.38, 0.6), k % 4, 0.0))
            x += r.uniform(1.0, 1.6)
            k += 1
        y = PY0 + 2.2
        while y < PY1 - 1.0:
            self.shrubs.append((PX0 + 0.9, y, r.uniform(0.4, 0.62), k % 4, 0.0))
            y += r.uniform(1.1, 1.8)
            k += 1
        y = -8.0
        while y < 9.5:
            self.shrubs.append((PX1 - 0.8, y, r.uniform(0.3, 0.45), k % 4, 0.0))
            y += r.uniform(1.0, 1.5)
            k += 1
        x = PX0 + 2.5
        while x < 10.5:
            self.shrubs.append((x, PY1 - 0.9, r.uniform(0.45, 0.7), k % 4, 0.0))
            x += r.uniform(1.4, 2.2)
            k += 1
        # palms (royal palms lining the drive edge and pool) and shade trees
        self.palms += [(8.4, -4.2, 6.6), (8.4, -9.4, 7.4), (-11.6, -1.9, 6.0), (-11.8, 9.6, 7.0), (-2.0, -11.6, 5.6),
                       (24.0, -5.5, 6.4), (24.0, 0.3, 5.8), (-6.5, 9.9, 6.2)]
        self.trees += [("island_tree_01", -11.0, -11.0, 1.25), ("island_tree_02", 3.5, 18.5, 1.9),
                       ("tree_small_02", -9.0, 17.5, 1.5), ("island_tree_02", 9.0, 20.5, 1.5)]

    # --------------------------------------------------- the street ---
    def street(self):
        S, g, d = self.S, self.g, self.d
        X0, X1 = -160.0, 170.0
        g.box(X0, ROAD_Y0, -0.3, X1, ROAD_Y1, -0.06, S["asphalt"], skip="-z")
        # estate kerbs painted black and white, one metre apiece
        for (ya, yb) in [(ROAD_Y1, ROAD_Y1 + 0.18), (ROAD_Y0 - 0.18, ROAD_Y0)]:
            x, k = X0, 0
            while x < X1:
                if not (GATE[0] - 0.4 < x + 0.5 < GATE[1] + 0.4 and ya == ROAD_Y1):
                    g.box(x, ya, -0.3, x + 1.0, yb, 0.06, S["kerb_w"] if k % 2 else S["kerb_b"])
                x += 1.0
                k += 1
        # worn centre line, speed bumps, manholes
        ym = (ROAD_Y0 + ROAD_Y1) / 2
        x = X0 + 2
        while x < X1:
            g.box(x, ym - 0.06, -0.3, x + 3.0, ym + 0.06, -0.057, S["road_paint"], skip="-z")
            x += 9.0
        for bx in (-36.0, 50.0):
            n = 14
            w = (ROAD_Y1 - ROAD_Y0) / n
            for i in range(n):
                y0b = ROAD_Y0 + i * w
                m = S["bump_y"] if i % 2 else S["kerb_b"]
                g.face([(bx - 0.45, y0b, -0.06), (bx + 0.45, y0b, -0.06), (bx + 0.2, y0b, 0.02), (bx - 0.2, y0b, 0.02)], m)
                g.face([(bx - 0.2, y0b, 0.02), (bx + 0.2, y0b, 0.02), (bx + 0.2, y0b + w, 0.02), (bx - 0.2, y0b + w, 0.02)], m)
                g.face([(bx - 0.45, y0b, -0.06), (bx - 0.2, y0b, 0.02), (bx - 0.2, y0b + w, 0.02), (bx - 0.45, y0b + w, -0.06)], m)
                g.face([(bx + 0.2, y0b, 0.02), (bx + 0.45, y0b, -0.06), (bx + 0.45, y0b + w, -0.06), (bx + 0.2, y0b + w, 0.02)], m)
        for (mx, my) in [(-22.0, ym + 1.6), (9.0, ym - 1.8), (37.0, ym + 1.2), (-70.0, ym - 1.0), (90.0, ym + 1.5)]:
            d.cyl((mx, my, -0.062), (mx, my, -0.054), 0.33, S["black_metal"], seg=20)
        # street-name sign at the west junction, wheelie bins by a few gates
        import suv as _suv
        sg = _suv.decal_material("street_sign", "plate", "PALM GROVE CL.")
        sx_, sy_ = -49.5, ROAD_Y1 + 1.5
        d.cyl((sx_, sy_, 0), (sx_, sy_, 2.9), 0.03, S["steel"], seg=8)
        d.box(sx_ - 0.75, sy_ - 0.015, 2.55, sx_ + 0.75, sy_ + 0.015, 2.9, S["sign"])
        d.face([(sx_ - 0.7, sy_ - 0.017, 2.6), (sx_ + 0.7, sy_ - 0.017, 2.6), (sx_ + 0.7, sy_ - 0.017, 2.86), (sx_ - 0.7, sy_ - 0.017, 2.86)],
               sg, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
        for (bxn, byn) in [(12.6, PY0 - 0.65), (-17.5, PY0 - 0.65), (33.0, PY0 - 0.65), (-4.0, ROAD_Y0 - 1.6), (41.0, ROAD_Y0 - 1.6)]:
            d.box(bxn, byn - 0.28, 0.02, bxn + 0.55, byn + 0.28, 0.98, S["bin"])
            d.box(bxn - 0.03, byn - 0.31, 0.98, bxn + 0.58, byn + 0.31, 1.04, S["bin"])
            for wy in (-0.24, 0.24):
                d.cyl((bxn + 0.5, byn + wy - 0.02, 0.1), (bxn + 0.5, byn + wy + 0.02, 0.1), 0.09, S["black_metal"], seg=10)
        # planting strip along the outside of our own front wall
        r = self.rnd
        x = PX0 + 1.0
        k = 0
        while x < PX1 - 1.0:
            if not (PGATE[0] - 1.2 < x < GATE[1] + 1.2):
                self.shrubs.append((x, PY0 - 0.55, r.uniform(0.28, 0.42), k % 4, 0.0))
                if r.random() < 0.5:
                    self.flowers.append((x + r.uniform(-0.3, 0.3), PY0 - 0.5, r.uniform(0.7, 1.0)))
            x += r.uniform(1.3, 2.0)
            k += 1
        self.palms += [(-9.0, PY0 - 0.9, 6.2), (3.5, PY0 - 0.9, 7.0), (23.5, PY0 - 0.9, 6.4)]
        # covered drains (precast slabs) + paved walkway on both sides
        for (ya, yb) in [(ROAD_Y1 + 0.18, ROAD_Y1 + 1.0), (ROAD_Y0 - 1.0, ROAD_Y0 - 0.18)]:
            x = X0
            while x < X1:
                g.box(x, ya, -0.2, x + 0.96, yb, 0.03, S["concrete"])
                x += 1.0
        g.box(X0, ROAD_Y1 + 1.0, -0.2, X1, PY0 - 0.2, 0.02, S["pavers"], skip="-z")
        g.box(X0, ROAD_Y0 - 2.0, -0.2, X1, ROAD_Y0 - 1.0, 0.02, S["pavers"], skip="-z")
        # driveway apron from road to gate
        g.box(GATE[0] - 0.4, ROAD_Y1, -0.2, GATE[1] + 0.4, PY0, 0.035, S["concrete"], skip="-z")
        # cross street on the east side of the block
        g.box(66.0, -160, -0.3, 73.0, 170, -0.065, S["asphalt"], skip="-z")
        g.box(-58.0, -160, -0.3, -51.5, 170, -0.065, S["asphalt"], skip="-z")
        # power poles + lines along the far side of the road
        py = ROAD_Y0 - 1.5
        xs = list(range(-140, 160, 32))
        for x in xs:
            d.cyl((x, py, 0), (x, py, 8.6), 0.14, S["concrete"], seg=10, r1=0.09)
            d.box(x - 0.05, py - 1.1, 8.0, x + 0.05, py + 1.1, 8.1, S["concrete"])
            d.box(x - 0.05, py - 0.7, 7.2, x + 0.05, py + 0.7, 7.28, S["concrete"])
            for oy in (-1.0, 0.0, 1.0):
                d.cyl((x, py + oy, 8.1), (x, py + oy, 8.28), 0.035, S["trim_brown"], seg=6)
        for a, b in zip(xs[:-1], xs[1:]):
            for (oy, zz) in [(-1.0, 8.28), (0.0, 8.28), (1.0, 8.28), (-0.6, 7.3), (0.6, 7.3)]:
                prev = None
                for i in range(9):
                    t = i / 8
                    p = (a + (b - a) * t, py + oy, zz - 0.9 * 4 * t * (1 - t))
                    if prev:
                        d.cyl(prev, p, 0.012, S["black_metal"], seg=4, caps=False, smooth=False)
                    prev = p
        # street lights on our side
        for x in range(-130, 150, 28):
            sx, sy = x - 2, ROAD_Y1 + 1.4
            d.cyl((sx, sy, 0), (sx, sy, 7.0), 0.08, S["steel"], seg=10, r1=0.05)
            d.cyl((sx, sy, 7.0), (sx, sy - 1.6, 7.25), 0.04, S["steel"], seg=8)
            d.box(sx - 0.12, sy - 2.1, 7.18, sx + 0.12, sy - 1.5, 7.28, S["black_metal"], {"-z": S["lamp"]})

    # ------------------------------------------------- neighbours ---
    def hip_roof(self, x0, y0, x1, y1, z, pitch, mat, over=0.6):
        nb = self.nb
        x0, y0, x1, y1 = x0 - over, y0 - over, x1 + over, y1 + over
        w, dd = x1 - x0, y1 - y0
        run = min(w, dd) / 2
        h = run * math.tan(math.radians(pitch))
        sl = math.hypot(run, h)
        if w >= dd:
            r0, r1 = Vector((x0 + run, y0 + run, z + h)), Vector((x1 - run, y0 + run, z + h))
            A, B, C, Dp = Vector((x0, y0, z)), Vector((x1, y0, z)), Vector((x1, y1, z)), Vector((x0, y1, z))
            nb.face([A, B, r1, r0], mat, uvs=[(0, 0), (w, 0), (w - run, sl), (run, sl)])
            nb.face([C, Dp, r0, r1], mat, uvs=[(0, 0), (w, 0), (w - run, sl), (run, sl)])
            nb.face([B, C, r1], mat, uvs=[(0, 0), (dd, 0), (run, sl)])
            nb.face([Dp, A, r0], mat, uvs=[(0, 0), (dd, 0), (run, sl)])
        else:
            r0, r1 = Vector((x0 + run, y0 + run, z + h)), Vector((x0 + run, y1 - run, z + h))
            A, B, C, Dp = Vector((x0, y0, z)), Vector((x1, y0, z)), Vector((x1, y1, z)), Vector((x0, y1, z))
            nb.face([B, C, r1, r0], mat, uvs=[(0, 0), (dd, 0), (dd - run, sl), (run, sl)])
            nb.face([Dp, A, r0, r1], mat, uvs=[(0, 0), (dd, 0), (dd - run, sl), (run, sl)])
            nb.face([A, B, r0], mat, uvs=[(0, 0), (w, 0), (run, sl)])
            nb.face([C, Dp, r1], mat, uvs=[(0, 0), (w, 0), (run, sl)])
        # fascia + soffit
        nb.box(x0, y0, z - 0.22, x1, y1, z, self.S["trim_brown"], {"-z": self.S["nb_white"]}, skip="+z")

    def nb_windows(self, x0, y0, x1, y1, z, seed, storey_h=3.0):
        nb, S, r = self.nb, self.S, random.Random(seed)
        G, F = S["nb_glass"], S["alu"]
        for side in ("s", "n", "w", "e"):
            L = (x1 - x0) if side in "sn" else (y1 - y0)
            n = max(1, int(L / 3.2))
            for i in range(n):
                c = (i + 0.5) * L / n + r.uniform(-0.3, 0.3)
                ww = r.choice([1.2, 1.5, 1.8])
                hh = r.choice([1.2, 1.4])
                zs = z + 0.95
                a, b = c - ww / 2, c + ww / 2
                t = 0.03
                if side == "s":
                    nb.box(x0 + a, y0 - t, zs, x0 + b, y0, zs + hh, G)
                    nb.box(x0 + a - 0.06, y0 - 0.06, zs - 0.06, x0 + b + 0.06, y0 - 0.02, zs, F)
                    nb.box(x0 + c - 0.02, y0 - 0.05, zs, x0 + c + 0.02, y0 - 0.02, zs + hh, F)
                elif side == "n":
                    nb.box(x0 + a, y1, zs, x0 + b, y1 + t, zs + hh, G)
                    nb.box(x0 + c - 0.02, y1 + 0.02, zs, x0 + c + 0.02, y1 + 0.05, zs + hh, F)
                elif side == "w":
                    nb.box(x0 - t, y0 + a, zs, x0, y0 + b, zs + hh, G)
                    nb.box(x0 - 0.05, y0 + c - 0.02, zs, x0 - 0.02, y0 + c + 0.02, zs + hh, F)
                else:
                    nb.box(x1, y0 + a, zs, x1 + t, y0 + b, zs + hh, G)
                    nb.box(x1 + 0.02, y0 + c - 0.02, zs, x1 + 0.05, y0 + c + 0.02, zs + hh, F)

    def nb_house(self, cx, cy, seed, face="s"):
        """A neighbouring house: 1–2 storeys, hipped or flat roof, porch, balcony."""
        nb, S = self.nb, self.S
        r = random.Random(seed)
        w, dd = r.uniform(11, 15), r.uniform(9, 12)
        floors = r.choice([2, 2, 2, 1])
        wall = S[r.choice(["nb_cream", "nb_peach", "nb_grey", "nb_white", "nb_cream"])]
        style = r.choice(["hip", "hip", "hip", "flat"])
        roof = S[r.choice(["roof_brown", "roof_red", "roof_char", "roof_brown"])]
        x0, y0, x1, y1 = cx - w / 2, cy - dd / 2, cx + w / 2, cy + dd / 2
        h = 0.4 + floors * 3.1
        nb.box(x0 - 0.03, y0 - 0.03, 0, x1 + 0.03, y1 + 0.03, 0.4, S["grey"])
        nb.box(x0, y0, 0.4, x1, y1, h, wall)
        for fl in range(floors):
            self.nb_windows(x0, y0, x1, y1, 0.4 + fl * 3.1, seed * 7 + fl)
            nb.box(x0 - 0.04, y0 - 0.04, 0.4 + fl * 3.1 + 2.95, x1 + 0.04, y1 + 0.04, 0.4 + fl * 3.1 + 3.1, S["nb_white"])
        # porch block with columns on the facing side
        sgn = -1 if face == "s" else 1
        py = y0 if face == "s" else y1
        px0 = cx - r.uniform(1.5, 3.0)
        px1 = px0 + r.uniform(3.2, 4.5)
        nb.box(px0, py, 0.0, px1, py + sgn * 2.2, 0.4, S["grey"])
        for px in (px0 + 0.2, px1 - 0.2):
            nb.box(px - 0.16, py + sgn * 2.0 - 0.16, 0.4, px + 0.16, py + sgn * 2.0 + 0.16, 3.3, S["nb_white"])
        nb.box(px0 - 0.15, py, 3.3, px1 + 0.15, py + sgn * 2.3, 3.55, S["nb_white"])
        nb.box((px0 + px1) / 2 - 0.55, py + sgn * 0.02, 0.4, (px0 + px1) / 2 + 0.55, py + sgn * 0.06, 2.6, S["wood_dark"])
        if floors == 2:   # balcony rail over the porch
            for px in [px0 + 0.1 * k for k in range(int((px1 - px0) / 0.1))]:
                nb.box(px, py + sgn * 2.2 - 0.01, 3.55, px + 0.02, py + sgn * 2.2 + 0.01, 4.5, S["black_metal"])
            nb.box(px0, py + sgn * 2.2 - 0.03, 4.5, px1, py + sgn * 2.2 + 0.03, 4.55, S["black_metal"])
        if style == "hip":
            self.hip_roof(x0, y0, x1, y1, h + 0.22, r.uniform(22, 30), roof)
        else:
            nb.box(x0 - 0.3, y0 - 0.3, h, x1 + 0.3, y1 + 0.3, h + 0.7, wall)
            nb.box(x0 - 0.33, y0 - 0.33, h + 0.7, x1 + 0.33, y1 + 0.33, h + 0.75, S["alu"])
            if r.random() < 0.7:
                self.tank(cx + 2, cy, h + 0.1, 0.8, 1.3, mb=nb)
        return (x0, y0, x1, y1)

    def nb_plot(self, x0, y0, x1, y1, seed, face="s", sides="snwe"):
        r = random.Random(seed)
        S, nb = self.S, self.nb
        nb.box(x0, y0, -0.12, x1, y1, 0.0, r.choice([S["pavers"], S["lawn"], S["concrete"], S["lawn"]]), skip="-z")
        fm = {"wall": r.choice([S["nb_cream"], S["nb_white"], S["nb_grey"], S["nb_peach"]]), "pillar": S["nb_white"]}
        gx = r.uniform(x0 + 6, x1 - 10)
        gaps_s = [(gx, gx + 4.5)] if face == "s" else []
        gaps_n = [(gx, gx + 4.5)] if face == "n" else []
        wire = r.random() < 0.5
        if "s" in sides:
            self.fence_run("x", y0, x0, x1, mb=nb, gaps=gaps_s, mats=fm, wire=wire)
        if "n" in sides:
            self.fence_run("x", y1, x0, x1, mb=nb, gaps=gaps_n, mats=fm, wire=wire)
        if "w" in sides:
            self.fence_run("y", x0, y0, y1, mb=nb, mats=fm, wire=wire)
        if "e" in sides:
            self.fence_run("y", x1, y0, y1, mb=nb, mats=fm, wire=wire)
        gy = y0 if face == "s" else y1
        gcol = r.choice([S["black_metal"], S["trim_brown"], S["gate_slat"]])
        for u in (gx, gx + 2.25 - 0.03, gx + 4.5 - 0.06):
            nb.box(u, gy - 0.035, 0.08, u + 0.06, gy + 0.035, 2.3, gcol)
        nb.box(gx, gy - 0.035, 2.24, gx + 4.5, gy + 0.035, 2.3, gcol)
        nb.box(gx, gy - 0.035, 0.08, gx + 4.5, gy + 0.035, 0.14, gcol)
        zz = 0.18
        solid = r.random() < 0.4
        while zz < 2.2:
            nb.box(gx + 0.06, gy - 0.012, zz, gx + 4.44, gy + 0.012, zz + (0.16 if solid else 0.1), gcol)
            zz += 0.165 if solid else 0.14
        for u in (gx, gx + 4.5):
            nb.box(u - 0.07, gy - 0.07, 2.63, u + 0.07, gy + 0.07, 2.84, S["lamp"])
            nb.box(u - 0.1, gy - 0.1, 2.84, u + 0.1, gy + 0.1, 2.88, S["black_metal"])
        # shrubs and flowers along the street side of the wall
        sgn = -1 if face == "s" else 1
        xx = x0 + 1.2
        kk = seed
        while xx < x1 - 1.2:
            if not (gx - 1.0 < xx < gx + 5.5) and r.random() < 0.7:
                self.shrubs.append((xx, gy + sgn * 0.55, r.uniform(0.26, 0.44), kk % 4, 0.0))
                if r.random() < 0.4:
                    self.flowers.append((xx + r.uniform(-0.3, 0.3), gy + sgn * 0.5, r.uniform(0.7, 1.0)))
            xx += r.uniform(1.6, 2.6)
            kk += 1
        cx = (x0 + x1) / 2 + r.uniform(-4, 4)
        cy = (y0 + y1) / 2 + r.uniform(-3, 5) * (1 if face == "s" else -1)
        if self.variants and r.random() < 0.6:
            # a restyled copy of the modern duplex (15 x 11 m footprint), sometimes mirrored
            v = r.choice(self.variants)
            cx = min(max(cx, x0 + 10.5), x1 - 10.5)
            cy = min(max(cy, y0 + 9.0), y1 - 9.0)
            mir = r.random() < 0.5
            e = bpy.data.objects.new("nb_duplex", None)
            e.instance_type = "COLLECTION"
            e.instance_collection = v
            if face == "s":
                e.location = (cx + (7.5 if mir else -7.5), cy - 5.5, 0)
                e.scale = (-1 if mir else 1, 1, 1)
            else:
                e.location = (cx + (-7.5 if mir else 7.5), cy + 5.5, 0)
                e.rotation_euler = (0, 0, math.pi)
                e.scale = (-1 if mir else 1, 1, 1)
            self.c.objects.link(e)
            nb.box(cx - 9.5, cy - 8.5, 0.0, cx + 9.5, cy + 8.0, 0.03, S["pavers"], skip="-z")
            hx0, hy0, hx1, hy1 = cx - 7.5, cy - 5.5, cx + 7.5, cy + 5.5
        else:
            hx0, hy0, hx1, hy1 = self.nb_house(cx, cy, seed, face=face)
        if self.street_cars:           # a car on the drive, just inside the gate
            for k in range(r.randint(1, 2)):
                px = gx + 1.3 + k * 2.6
                py = (y0 + 4.5) if face == "s" else (y1 - 4.5)
                if not (hx0 - 1.6 < px < hx1 + 1.6 and hy0 - 2.8 < py < hy1 + 2.8):
                    self.cars_placed.append((r.choice(self.street_cars), px, py, 90 if face == "s" else -90))
        # yard trees / palms
        for _ in range(r.randint(2, 4)):
            tx, ty = r.uniform(x0 + 2, x1 - 2), r.uniform(y0 + 2, y1 - 2)
            if hx0 - 2.5 < tx < hx1 + 2.5 and hy0 - 2.5 < ty < hy1 + 2.5:
                continue
            if r.random() < 0.45:
                self.palms.append((tx, ty, r.uniform(5.5, 8.5)))
            else:
                self.trees.append((r.choice(["island_tree_01", "island_tree_02", "tree_small_02"]), tx, ty, r.uniform(1.4, 2.4)))
        return gx

    def neighbourhood(self):
        r = self.rnd
        w, dp = PX1 - PX0, PY1 - PY0
        seed = 100
        self.nb_gates = []
        # same row as us (west and east neighbours), and rows across the street / behind
        rows = [(PY0, PY1, "s"), (ROAD_Y0 - 2.0 - dp, ROAD_Y0 - 2.0, "n"), (PY1, PY1 + dp, "n")]
        def blocked(xa):
            return (xa + w > 66 and xa < 73) or (xa < -51.5 and xa + w > -58)

        def row(ya, yb, face, skip_s=False, ours=False):
            nonlocal seed
            for k in range(-3, 4):
                xa = PX0 + k * w
                if (ours and k == 0) or blocked(xa):
                    continue
                seed += 1
                sides = "n" + ("" if skip_s else "s")
                if not (ours and k == 1):
                    sides += "w"                 # our own east wall already stands there
                if k == 3 or blocked(xa + w):
                    sides += "e"                 # last plot before a cross street / end of row
                self.nb_plot(xa, ya, xa + w, yb, seed, face=face, sides=sides)

        row(PY0, PY1, "s", ours=True)
        row(ROAD_Y0 - 2.0 - dp, ROAD_Y0 - 2.0, "n")
        row(PY1, PY1 + dp, "n", skip_s=True)
        # far rows (cheap filler so the horizon is built up)
        row(ROAD_Y0 - 2.0 - 2 * dp - 9, ROAD_Y0 - 2.0 - dp - 9, "s")
        row(PY1 + dp + 9, PY1 + 2 * dp + 9, "s")
        if self.street_cars:
            for x in range(-140, 150, 23):
                if GATE[0] - 9 < x < GATE[1] + 9 or r.random() < 0.35:
                    continue
                side = r.random() < 0.5
                self.cars_placed.append((r.choice(self.street_cars), x + r.uniform(-3, 3),
                                         ROAD_Y1 - 1.25 if side else ROAD_Y0 + 1.25, 180 if side else 0))
        # trees along the street verge and a scattered far belt
        for x in range(-150, 160, 17):
            if GATE[0] - 6 < x < GATE[1] + 6:
                continue
            self.trees.append((r.choice(["island_tree_01", "island_tree_02"]), x + r.uniform(-2, 2), ROAD_Y1 + 1.6, r.uniform(1.3, 1.9)))
        for _ in range(170):
            a = r.uniform(0, 6.283)
            rad = r.uniform(120, 330)
            x, y = math.cos(a) * rad, math.sin(a) * rad
            if r.random() < 0.3:
                self.palms.append((x, y, r.uniform(7, 11)))
            else:
                self.trees.append((r.choice(["island_tree_01", "island_tree_02", "tree_small_02"]), x, y, r.uniform(2.2, 4.5)))

    # -------------------------------------------------------- build ---
    def build(self, gate_open=0.0, far=True):
        self.gate_open = gate_open
        self.ground(), self.pool(), self.fence(), self.carport(), self.backyard(), self.services(), self.planting()
        self.street()
        self.neighbourhood()
        objs = [self.g.build("site_ground", self.c), self.d.build("site_details", self.c),
                self.gl.build("site_water", self.c), self.nb.build("neighbourhood", self.c)]
        self.vegetation()
        return objs

    def vegetation(self):
        c = kit.coll("Vegetation", self.c)
        r = self.rnd
        # palms: a few generated variants, instanced
        lib = kit.coll("LIB", hide=True)
        variants = []
        for i, (h, fl) in enumerate([(6.0, 3.0), (7.2, 3.4), (8.5, 3.6), (5.4, 2.8)]):
            pc = bpy.data.collections.new(f"LIB_palm{i}")
            lib.children.link(pc)
            plants.palm_mesh(f"palm{i}", height=h, frond_len=fl, seed=i + 3, lean=0.3 + 0.2 * i, collection=pc)
            variants.append((h, pc))
        for (x, y, h) in self.palms:
            hv, pc = min(variants, key=lambda v: abs(v[0] - h))
            e = bpy.data.objects.new("i_palm", None)
            e.instance_type = "COLLECTION"
            e.instance_collection = pc
            e.location = (x, y, 0)
            e.rotation_euler = (0, 0, r.uniform(0, 6.283))
            s = h / hv
            e.scale = (s, s, s)
            c.objects.link(e)
        for (kind, x, y, s) in self.trees:
            kit.place(kind, (x, y, 0), rz=r.uniform(0, 6.283), scale=s, collection=c)
        self.grass(c)
        for (x, y, s) in self.flowers:            # flowering ground cover, laid along the wall line
            kit.place("shrub_01", (x, y, 0.0), rz=r.choice((0.0, math.pi)) + r.uniform(-0.08, 0.08), scale=s, collection=c)
        picks = ["shrub_02_a", "shrub_02_b", "shrub_02_c", "shrub_02_d"]
        for (x, y, s, v, z) in self.shrubs:
            kit.place("shrub_02", (x, y, z), rz=r.uniform(0, 6.283), scale=s, collection=c, pick=picks[v])

    def grass(self, c):
        """Real grass tufts instanced over the lawns (dense in front, thinner behind)."""
        import bmesh
        r = random.Random(11)
        objs = kit.import_gltf(kit.ph.model("grass_medium_01", kit.MODEL_RES))
        keep = [o for o in objs if o.type == "MESH" and ("mid_" in o.name or "small_" in o.name)][:6]
        for o in objs:
            if o not in keep:
                bpy.data.objects.remove(o, do_unlink=True)
        # lawn rectangles: (x0, y0, x1, y1, tufts per m2)
        areas = [(-12.7, -11.4, 7.3, -3.3, 110), (-12.7, -3.3, -2.5, -1.5, 110), (-11.4, 8.7, -0.6, 21.3, 28),
                 (-0.5, 11.9, 11.2, 21.3, 28), (-2.3, 5.7, -0.1, 8.6, 60), (-12.7, -1.5, -12.35, 8.7, 60)]
        pts = [[] for _ in keep]
        for (x0, y0, x1, y1, dens) in areas:
            n = int((x1 - x0) * (y1 - y0) * dens)
            for _ in range(n):
                pts[r.randrange(len(keep))].append((r.uniform(x0, x1), r.uniform(y0, y1), 0.0))
        for i, o in enumerate(keep):
            kit.link(o, c)
            # put the tuft's base centre on its origin
            xs = [v.co.x for v in o.data.vertices]
            ys = [v.co.y for v in o.data.vertices]
            zs = [v.co.z for v in o.data.vertices]
            off = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs) + 0.01))
            for v in o.data.vertices:
                v.co -= off
            o.parent = None
            o.location = (0, 0, 0)
            o.rotation_euler = (0, 0, 0)
            o.rotation_mode = "XYZ"
            o.scale = (1, 1, 1)
            sizes = [r.uniform(0.75, 1.25) for _ in pts[i]]
            kit.face_instancer(f"lawn_tufts_{i}", o, pts[i], sizes, collection=c, seed=i)
        # greener, fresher blades than the scan's dry-season colour
        for m in {m for o in keep for m in o.data.materials}:
            b = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
            if not b:
                continue
            lk = [l for l in m.node_tree.links if l.to_socket == b[0].inputs["Base Color"]]
            if lk:
                h = m.node_tree.nodes.new("ShaderNodeHueSaturation")
                h.inputs["Hue"].default_value = 0.52
                h.inputs["Saturation"].default_value = 1.1
                h.inputs["Value"].default_value = 1.9
                m.node_tree.links.new(lk[0].from_socket, h.inputs["Color"])
                m.node_tree.links.new(h.outputs[0], b[0].inputs["Base Color"])
