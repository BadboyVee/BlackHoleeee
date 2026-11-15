"""The duplex: plan-driven shell (walls, slabs, openings, windows, doors, stairs,
balconies, roof).  Footprint x 0..15 (east), y 0..11 (north); the front faces -Y.
"""
import math

from mathutils import Matrix, Vector

import kit
from kit import MB

W, D = 15.0, 11.0
Z0, Z1, ZR = 0.45, 3.75, 6.95      # ground floor, first floor, roof slab top
SL = 0.20                          # slab thickness
TE, TI = 0.24, 0.14                # exterior / interior wall thickness
PAR = 7.75                         # parapet top
TOWER = 8.35                       # centre (wood) volume top
RISE, TREAD, NR = 3.3 / 19, 0.27, 19


def materials(palette=None):
    """palette: optional {key: (texture, kwargs)} or ready materials to restyle a variant."""
    M = {}
    M["white"] = kit.mat_pbr("ext_white", "painted_plaster_wall", size=3.0, sat=0.15, val=1.5, rough_add=0.1, normal=0.5)
    M["grey"] = kit.mat_pbr("ext_grey", "painted_plaster_wall", size=3.0, tint=(0.25, 0.235, 0.22), sat=0.3, normal=0.6)
    M["wood"] = kit.mat_pbr("ext_wood", "oak_wood_planks", size=1.6, rot=math.pi / 2, tint=(0.95, 0.52, 0.26),
                            rough_mul=0.9, normal=1.0)
    M["wood_dark"] = kit.mat_pbr("wood_dark", "wood_table_001", size=1.2, rot=math.pi / 2, val=1.1, rough_mul=0.8)
    M["stone"] = kit.mat_pbr("ext_stone", "stacked_stone_wall", size=1.6, val=2.3, sat=0.35, normal=1.5,
                             tint=(0.9, 0.88, 0.86))
    M["plinth"] = kit.mat_pbr("plinth", "concrete_floor_02", size=3.0, tint=(0.45, 0.45, 0.45))
    M["concrete"] = kit.mat_pbr("concrete", "concrete_floor_02", size=3.0, val=1.0)
    M["int"] = kit.mat_plain("int_paint", (0.86, 0.84, 0.80), rough=0.85)
    M["int_accent"] = kit.mat_plain("int_accent", (0.33, 0.37, 0.36), rough=0.8)
    M["ceil"] = kit.mat_plain("ceiling", (0.9, 0.9, 0.88), rough=0.9)
    M["tile"] = kit.mat_pbr("floor_tile", "marble_01", size=2.4, rough_mul=0.35, val=1.05, normal=0.4)
    M["parquet"] = kit.mat_pbr("floor_parquet", "herringbone_parquet", size=1.6, rough_mul=0.7, val=0.9)
    M["bath_tile"] = kit.mat_pbr("bath_tile", "large_floor_tiles_02", size=1.6, rough_mul=0.5, val=1.15)
    M["out_tile"] = kit.mat_pbr("out_tile", "concrete_pavement", size=2.0, val=0.9, rough_mul=0.9)
    M["alu"] = kit.mat_plain("alu_black", (0.02, 0.02, 0.022), rough=0.35, metal=0.8)
    M["steel"] = kit.mat_plain("steel", (0.6, 0.6, 0.6), rough=0.25, metal=1.0)
    M["glass"] = kit.mat_glass("glass", tint=(0.82, 0.9, 0.88), darkness=0.9)
    M["glass_rail"] = kit.mat_glass("glass_rail", tint=(0.86, 0.95, 0.93), darkness=1.0)
    M["door_int"] = kit.mat_pbr("door_int", "oak_veneer_01", size=1.2, rot=math.pi / 2, tint=(0.75, 0.6, 0.45))
    M["roof"] = kit.mat_pbr("roof_screed", "concrete_floor_02", size=4.0, val=0.8)
    M["skirt"] = kit.mat_plain("skirting", (0.93, 0.93, 0.92), rough=0.5)
    M.update(palette or {})
    return M


class House:
    def __init__(self, collection, palette=None, name="house"):
        self.c = collection
        self.name = name
        self.M = materials(palette)
        self.shell, self.frames, self.glass, self.trim = MB(), MB(), MB(), MB()
        self.doors = []       # (kind, hinge xy, ...) for interior use
        self.spots = []       # ceiling downlight positions

    # ------------------------------------------------------------ walls ---
    def wall(self, ax, c, a0, a1, z0, z1, t, ops, m_lo, m_hi, m_rev=None):
        """Wall along `ax` ('x' or 'y') at cross coordinate c. ops = [(u0,u1,v0,v1)]
        absolute openings. m_lo faces the lower cross side, m_hi the higher."""
        m_rev = m_rev or m_lo
        mb = self.shell

        def piece(ua, ub, za, zb):
            if ub - ua < 1e-4 or zb - za < 1e-4:
                return
            if ax == "x":
                mb.box(ua, c - t / 2, za, ub, c + t / 2, zb, m_rev, {"-y": m_lo, "+y": m_hi})
            else:
                mb.box(c - t / 2, ua, za, c + t / 2, ub, zb, m_rev, {"-x": m_lo, "+x": m_hi})

        cur = a0
        for (u0, u1, v0, v1) in sorted(ops):
            piece(cur, u0, z0, z1)
            piece(u0, u1, z0, v0)
            piece(u0, u1, v1, z1)
            cur = u1
        piece(cur, a1, z0, z1)

    def _fbox(self, ax, c, u0, u1, v0, v1, d, mat, mb=None, off=0.0):
        mb = mb or self.frames
        if ax == "x":
            mb.box(u0, c + off - d / 2, v0, u1, c + off + d / 2, v1, mat)
        else:
            mb.box(c + off - d / 2, u0, v0, c + off + d / 2, u1, v1, mat)

    def window(self, ax, c, u0, u1, v0, v1, n=2, fr=0.055, depth=0.08, transom=None, off=0.0, sill=0,
               sliding=False):
        """Aluminium window/door set filling an opening. n = number of lights.
        sill = +1/-1 puts a projecting sill on that cross side."""
        A = self.M["alu"]
        f = self._fbox
        f(ax, c, u0, u1, v0, v0 + fr, depth, A, off=off)
        f(ax, c, u0, u1, v1 - fr, v1, depth, A, off=off)
        f(ax, c, u0, u0 + fr, v0 + fr, v1 - fr, depth, A, off=off)
        f(ax, c, u1 - fr, u1, v0 + fr, v1 - fr, depth, A, off=off)
        w = (u1 - u0 - 2 * fr) / n
        for i in range(1, n):
            um = u0 + fr + i * w
            if sliding:  # overlapping stiles, slightly staggered
                o2 = off + (0.02 if i % 2 else -0.02)
                f(ax, c, um - 0.035, um + 0.035, v0 + fr, v1 - fr, depth * 0.6, A, off=o2)
            else:
                f(ax, c, um - fr / 2, um + fr / 2, v0 + fr, v1 - fr, depth, A, off=off)
        if transom:
            f(ax, c, u0 + fr, u1 - fr, transom - fr / 2, transom + fr / 2, depth, A, off=off)
        self._fbox(ax, c, u0 + fr * 0.5, u1 - fr * 0.5, v0 + fr * 0.5, v1 - fr * 0.5, 0.012, self.M["glass"],
                   mb=self.glass, off=off)
        if sill:
            s = self.M["grey"]
            if ax == "x":
                self.trim.box(u0 - 0.05, c + sill * 0.10, v0 - 0.05, u1 + 0.05, c + sill * 0.18, v0, s)
            else:
                self.trim.box(c + sill * 0.10, u0 - 0.05, v0 - 0.05, c + sill * 0.18, u1 + 0.05, v0, s)

    def door(self, ax, c, u0, u1, z, h=2.1, mat=None, hinge="lo", open_deg=0.0, swing=1, t=0.045, frame=True,
             handle=True):
        """Hinged door leaf in an opening. hinge 'lo' = at u0. swing = +1/-1 cross direction."""
        mat = mat or self.M["door_int"]
        A = self.M["skirt"] if mat is self.M["door_int"] else self.M["alu"]
        if frame:
            self._fbox(ax, c, u0, u0 + 0.04, z, z + h, TI + 0.04, A, mb=self.trim)
            self._fbox(ax, c, u1 - 0.04, u1, z, z + h, TI + 0.04, A, mb=self.trim)
            self._fbox(ax, c, u0, u1, z + h - 0.04, z + h, TI + 0.04, A, mb=self.trim)
        wdt = u1 - u0 - 0.08
        hu = u0 + 0.04 if hinge == "lo" else u1 - 0.04
        sgn = 1 if hinge == "lo" else -1
        ang = math.radians(open_deg) * swing * sgn
        if ax == "x":
            base = Matrix.Translation((hu, c, z)) @ Matrix.Rotation(ang, 4, "Z")
            m = base @ Matrix.Translation((sgn * wdt / 2, 0, (h - 0.05) / 2 + 0.005))
            self.trim.obox(m, wdt, t, h - 0.05, mat)
            if handle:
                for s in (-1, 1):
                    hm = base @ Matrix.Translation((sgn * (wdt - 0.09), s * (t / 2 + 0.03), 1.0))
                    self.trim.obox(hm, 0.13, 0.02, 0.02, self.M["steel"])
                    hm2 = base @ Matrix.Translation((sgn * (wdt - 0.035), s * (t / 2 + 0.015), 1.0))
                    self.trim.obox(hm2, 0.02, 0.03, 0.02, self.M["steel"])
        else:
            base = Matrix.Translation((c, hu, z)) @ Matrix.Rotation(-ang, 4, "Z")
            m = base @ Matrix.Translation((0, sgn * wdt / 2, (h - 0.05) / 2 + 0.005))
            self.trim.obox(m, t, wdt, h - 0.05, mat)
            if handle:
                for s in (-1, 1):
                    hm = base @ Matrix.Translation((s * (t / 2 + 0.03), sgn * (wdt - 0.09), 1.0))
                    self.trim.obox(hm, 0.02, 0.13, 0.02, self.M["steel"])
                    hm2 = base @ Matrix.Translation((s * (t / 2 + 0.015), sgn * (wdt - 0.035), 1.0))
                    self.trim.obox(hm2, 0.03, 0.02, 0.02, self.M["steel"])

    def skirting(self, x0, y0, x1, y1, z, gaps=()):
        """Skirting board around a rectangular room; gaps = [(side, a, b)] door gaps."""
        S, h, t = self.M["skirt"], 0.09, 0.012

        def run(side, a, b):
            segs, cur = [], a
            for (s, g0, g1) in sorted(g for g in gaps if g[0] == side):
                if g0 > cur:
                    segs.append((cur, g0))
                cur = max(cur, g1)
            if cur < b:
                segs.append((cur, b))
            for (p, q) in segs:
                if side == "s":
                    self.trim.box(p, y0, z, q, y0 + t, z + h, S)
                elif side == "n":
                    self.trim.box(p, y1 - t, z, q, y1, z + h, S)
                elif side == "w":
                    self.trim.box(x0, p, z, x0 + t, q, z + h, S)
                else:
                    self.trim.box(x1 - t, p, z, x1, q, z + h, S)

        run("s", x0, x1), run("n", x0, x1), run("w", y0, y1), run("e", y0, y1)

    def glass_rail(self, p0, p1, z, h=1.05, posts=True):
        """Frameless glass balustrade with a slim steel top rail along an axis line."""
        (x0, y0), (x1, y1) = p0, p1
        G, S = self.M["glass_rail"], self.M["steel"]
        if abs(x1 - x0) > abs(y1 - y0):
            self.glass.box(x0, y0 - 0.008, z + 0.04, x1, y0 + 0.008, z + h, G)
            self.trim.box(x0, y0 - 0.025, z + h, x1, y0 + 0.025, z + h + 0.03, S)
            self.trim.box(x0, y0 - 0.03, z, x1, y0 + 0.03, z + 0.06, self.M["alu"])
        else:
            self.glass.box(x0 - 0.008, y0, z + 0.04, x0 + 0.008, y1, z + h, G)
            self.trim.box(x0 - 0.025, y0, z + h, x0 + 0.025, y1, z + h + 0.03, S)
            self.trim.box(x0 - 0.03, y0, z, x0 + 0.03, y1, z + 0.06, self.M["alu"])

    # ------------------------------------------------------------ build ---
    def build(self):
        M, sh, tr = self.M, self.shell, self.trim
        Wh, Gy, Wd, St, In, Ce = M["white"], M["grey"], M["wood"], M["stone"], M["int"], M["ceil"]
        zc0 = Z1 - SL          # ground ceiling
        zc1 = ZR - SL          # first ceiling

        # ---- plinth / ground slab and floor finishes
        sh.box(-0.04, -0.04, 0.0, W + 0.04, D + 0.04, Z0 - 0.001, M["plinth"], skip="+z")
        T, P, B = M["tile"], M["parquet"], M["bath_tile"]
        for (x0, y0, x1, y1, m) in [
            (0, 0, 7.5, 6.2, T), (0, 6.2, 5.2, D, T), (5.2, 6.2, 10, D, T), (7.5, 1.2, 11.2, 6.2, T),
            (10, 6.2, 11.2, 7.4, T), (11.2, 0, W, 5.2, P), (11.2, 5.2, W, 7.4, B), (10, 7.4, W, D, B),
            (7.5, 0, 11.2, 1.2, M["out_tile"]),
        ]:
            sh.face([(x0, y0, Z0), (x1, y0, Z0), (x1, y1, Z0), (x0, y1, Z0)], m)

        # ---- GROUND FLOOR exterior walls
        g = Z0
        self.wall("x", TE / 2, 0, 7.5, g, Z1, TE, [(1.2, 6.3, g, g + 2.6)], Wh, In)
        self.wall("x", 1.2, 7.5, 11.2, g, zc0, TE, [(8.45, 9.65, g, g + 2.5), (9.85, 10.6, g, g + 2.5)], St, In)
        self.wall("x", TE / 2, 11.2, W, g, Z1, TE, [(12.0, 14.2, g + 0.9, g + 2.5)], St, In)
        self.wall("y", 7.5 + TE / 2, 0, 1.2 - TE / 2, g, zc0, TE, [], In, St, St)          # porch west cheek
        self.wall("y", 11.2 - TE / 2, 0, 1.2 - TE / 2, g, zc0, TE, [], St, In, St)         # porch east cheek
        self.wall("y", W - TE / 2, TE, D - TE, g, Z1, TE,
                  [(1.6, 3.4, g + 0.9, g + 2.5), (5.9, 6.7, g + 1.7, g + 2.3), (8.5, 9.3, g + 1.7, g + 2.3)], In, Wh, Wh)
        self.wall("y", TE / 2, TE, D - TE, g, Z1, TE,
                  [(1.6, 4.6, g, g + 2.6), (7.2, 10.0, g + 0.9, g + 2.5)], Wh, In)
        self.wall("x", D - TE / 2, 0, W, g, Z1, TE,
                  [(1.0, 4.2, g + 0.9, g + 2.5), (6.2, 8.8, g + 1.1, g + 2.3), (11.3, 12.5, g + 1.1, g + 2.3),
                   (13.3, 14.2, g, g + 2.1)], In, Wh, Wh)
        # ground windows
        self.window("x", TE / 2, 1.2, 6.3, g, g + 2.6, n=4, sliding=True)
        self.window("x", 1.2, 9.85, 10.6, g, g + 2.5, n=1)
        self.window("x", TE / 2, 12.0, 14.2, g + 0.9, g + 2.5, n=3, sill=-1)
        self.window("y", W - TE / 2, 1.6, 3.4, g + 0.9, g + 2.5, n=2, sill=1)
        self.window("y", W - TE / 2, 5.9, 6.7, g + 1.7, g + 2.3, n=1, sill=1)
        self.window("y", W - TE / 2, 8.5, 9.3, g + 1.7, g + 2.3, n=1, sill=1)
        self.window("y", TE / 2, 1.6, 4.6, g, g + 2.6, n=3, sliding=True)
        self.window("y", TE / 2, 7.2, 10.0, g + 0.9, g + 2.5, n=3, sill=-1)
        self.window("x", D - TE / 2, 1.0, 4.2, g + 0.9, g + 2.5, n=3, sill=1)
        self.window("x", D - TE / 2, 6.2, 8.8, g + 1.1, g + 2.3, n=3, sill=1)
        self.window("x", D - TE / 2, 11.3, 12.5, g + 1.1, g + 2.3, n=2, sill=1)
        self.door("x", D - TE / 2, 13.3, 14.2, g, mat=M["alu"], frame=False)
        # front door: tall timber pivot door with a long steel pull
        tr.box(8.45, 1.17, g, 9.65, 1.23, g + 2.5, M["wood_dark"])
        for k in range(1, 6):
            tr.box(8.45, 1.155, g + k * 0.42 - 0.006, 9.65, 1.17, g + k * 0.42 + 0.006, M["alu"])
        tr.box(9.45, 1.09, g + 0.7, 9.49, 1.13, g + 1.9, M["steel"])
        tr.box(9.455, 1.13, g + 0.8, 9.485, 1.17, g + 0.84, M["steel"])
        tr.box(9.455, 1.13, g + 1.76, 9.485, 1.17, g + 1.8, M["steel"])
        self._fbox("x", 1.2, 8.39, 8.45, g, g + 2.56, 0.12, M["alu"])
        self._fbox("x", 1.2, 9.65, 9.71, g, g + 2.56, 0.12, M["alu"])
        self._fbox("x", 1.2, 8.39, 9.71, g + 2.5, g + 2.56, 0.12, M["alu"])

        # ---- GROUND FLOOR interior walls
        self.wall("y", 7.5, 3.2, 6.2, g, zc0, TI, [], In, In)
        self.wall("y", 11.2, 1.2 + TE / 2, 7.4, g, zc0, TI, [(1.55, 2.45, g, g + 2.1)], In, In)
        self.wall("x", 5.2, 11.2, W - TE, g, zc0, TI, [(11.6, 12.4, g, g + 2.1)], In, In)
        self.wall("x", 7.4, 10.0, W - TE, g, zc0, TI, [], In, In)
        self.wall("y", 10.0, 7.4, D - TE, g, zc0, TI, [(8.5, 9.4, g, g + 2.1)], In, In)
        self.wall("x", 6.2, TE, 5.2, g, zc0, TI, [(0.9, 4.5, g, g + 2.7)], In, In)
        self.wall("x", 6.2, 5.2, 11.2, g, zc0, TI, [(7.72, 8.62, g, g + 2.1)], In, In)
        self.wall("y", 5.2, 6.2, D - TE, g, zc0, TI, [(7.0, 8.7, g, g + 2.4)], In, In)
        self.door("y", 11.2, 1.55, 2.45, g, hinge="hi", open_deg=0, swing=1)
        self.door("x", 5.2, 11.6, 12.4, g, hinge="lo", open_deg=0)
        self.door("y", 10.0, 8.5, 9.4, g, hinge="lo", open_deg=0)
        self.door("x", 6.2, 7.72, 8.62, g, hinge="lo", open_deg=75, swing=1)

        # ---- FIRST FLOOR slab (with stair void) – top faces are the floor finishes
        def slab(x0, y0, x1, y1, top):
            sh.box(x0, y0, zc0, x1, y1, Z1, Ce, {"+z": top})

        slab(TE, TE, 7.5, 1.38, M["out_tile"])          # master balcony strip (inside wall line)
        slab(TE, 1.38, 7.5, 6.2, P)                      # master bedroom
        slab(TE, 6.2, 3.4, D - TE, B)                    # master bath
        slab(3.4, 6.2, 7.5, D - TE, P)                   # closet
        slab(7.5, 1.2 - TE / 2, 8.9, D - TE, P)          # corridor
        slab(8.9, 1.2 - TE / 2, 11.2, 2.8, P)            # lounge
        slab(8.9, 2.8, 9.95, 3.07, P)
        slab(8.9, 6.13, 11.13, 7.4, P)                   # lobby
        slab(7.5 + 1.4, 7.4, W - TE, D - TE, P)          # bedrooms 3/4 (x>8.9)
        slab(11.13, 1.2 - TE / 2, W - TE, 5.2, P)        # bedroom 2
        slab(11.13, 5.2, W - TE, 7.4, B)                 # bath 2
        # soffit over porch + projecting centre volume floor
        sh.box(7.5, -0.5, Z1 - 0.3, 11.2, 1.2 - TE / 2, Z1, Wd, {"+z": P, "-z": M["wood"]})

        # ---- FIRST FLOOR exterior walls
        f = Z1
        # left block: recessed front with balcony slider
        self.wall("x", 1.5, 0, 7.5, f, ZR, TE, [(1.4, 6.1, f, f + 2.5)], Wh, In)
        self.window("x", 1.5, 1.4, 6.1, f, f + 2.5, n=4, sliding=True)
        self.wall("y", TE / 2, 1.5 + TE / 2, D - TE, f, ZR, TE,
                  [(2.6, 3.3, f + 0.5, f + 2.4), (4.4, 5.1, f + 0.5, f + 2.4), (8.0, 9.2, f + 1.5, f + 2.3)], Wh, In)
        for (a, b, v0, v1) in [(2.6, 3.3, 0.5, 2.4), (4.4, 5.1, 0.5, 2.4)]:
            self.window("y", TE / 2, a, b, f + v0, f + v1, n=1)
            # projecting dark surround, like a picture frame
            tr.box(-0.22, a - 0.16, f + v0 - 0.16, 0.0, a, f + v1 + 0.16, Gy)
            tr.box(-0.22, b, f + v0 - 0.16, 0.0, b + 0.16, f + v1 + 0.16, Gy)
            tr.box(-0.22, a, f + v0 - 0.16, 0.0, b, f + v0, Gy)
            tr.box(-0.22, a, f + v1, 0.0, b, f + v1 + 0.16, Gy)
        self.window("y", TE / 2, 8.0, 9.2, f + 1.5, f + 2.3, n=2, sill=-1)
        # centre projecting wood volume
        self.wall("x", -0.5 + TE / 2, 7.5, 11.2, Z1 - 0.3, TOWER, TE, [(8.2, 10.5, f + 0.7, f + 2.5)], Wd, In, Wd)
        self.window("x", -0.5 + TE / 2, 8.2, 10.5, f + 0.7, f + 2.5, n=3)
        self.wall("y", 7.5 + TE / 2, -0.5 + TE, 1.5 - TE / 2, f, ZR, TE, [], Wd, In, Wd)
        self.wall("y", 11.2 - TE / 2, -0.5 + TE, 1.0 - TE / 2, f, ZR, TE, [], In, Wd, Wd)
        # right block: recessed front with small balcony
        self.wall("x", 1.0, 11.2, W, f, ZR, TE, [(12.0, 14.3, f, f + 2.4)], Wh, In)
        self.window("x", 1.0, 12.0, 14.3, f, f + 2.4, n=3, sliding=True)
        self.wall("y", W - TE / 2, 1.0 + TE / 2, D - TE, f, ZR, TE,
                  [(2.0, 3.8, f + 0.9, f + 2.4), (5.9, 6.7, f + 1.6, f + 2.3), (8.3, 10.1, f + 0.9, f + 2.4)], In, Wh, Wh)
        self.window("y", W - TE / 2, 2.0, 3.8, f + 0.9, f + 2.4, n=2, sill=1)
        self.window("y", W - TE / 2, 5.9, 6.7, f + 1.6, f + 2.3, n=1, sill=1)
        self.window("y", W - TE / 2, 8.3, 10.1, f + 0.9, f + 2.4, n=2, sill=1)
        self.wall("x", D - TE / 2, 0, W, f, ZR, TE,
                  [(1.0, 2.4, f + 1.5, f + 2.3), (6.6, 9.2, f + 0.9, f + 2.4), (11.3, 13.7, f + 0.9, f + 2.4)], In, Wh, Wh)
        self.window("x", D - TE / 2, 1.0, 2.4, f + 1.5, f + 2.3, n=2, sill=1)
        self.window("x", D - TE / 2, 6.6, 9.2, f + 0.9, f + 2.4, n=3, sill=1)
        self.window("x", D - TE / 2, 11.3, 13.7, f + 0.9, f + 2.4, n=3, sill=1)

        # ---- FIRST FLOOR interior walls
        self.wall("y", 7.5, 1.5 + TE / 2, 7.4, f, zc1, TI, [(1.75, 2.65, f, f + 2.1)], In, In)
        self.wall("x", 6.2, TE, 7.5, f, zc1, TI, [(1.2, 2.0, f, f + 2.1), (4.3, 5.1, f, f + 2.1)], In, In)
        self.wall("x", 6.2, 8.9, 11.2, f, zc1, TI, [], In, In)
        self.wall("y", 3.4, 6.2, D - TE, f, zc1, TI, [], In, In)
        self.wall("y", 6.2, 7.4, D - TE, f, zc1, TI, [], In, In)
        self.wall("x", 7.4, 6.2, W - TE, f, zc1, TI, [(8.0, 8.9, f, f + 2.1), (10.2, 11.1, f, f + 2.1)], In, In)
        self.wall("y", 10.0, 7.4, D - TE, f, zc1, TI, [], In, In)
        self.wall("y", 11.2, 1.0 + TE / 2, 7.4, f, zc1, TI,
                  [(1.8, 2.7, f, f + 2.1), (6.35, 7.15, f, f + 2.1)], In, In)
        self.wall("x", 5.2, 11.2, W - TE, f, zc1, TI, [], In, In)
        self.door("y", 7.5, 1.75, 2.65, f, hinge="hi", open_deg=80, swing=-1)
        self.door("x", 6.2, 1.2, 2.0, f, hinge="lo")
        self.door("x", 6.2, 4.3, 5.1, f, hinge="lo")
        self.door("x", 7.4, 8.0, 8.9, f, hinge="lo")
        self.door("x", 7.4, 10.2, 11.1, f, hinge="hi")
        self.door("y", 11.2, 1.8, 2.7, f, hinge="lo")
        self.door("y", 11.2, 6.35, 7.15, f, hinge="lo")

        # ---- ROOF slab, parapets and copings
        sh.box(TE, 1.5, zc1, W - TE, D - TE, ZR, Ce, {"+z": M["roof"]})
        sh.box(7.5, -0.5 + TE, zc1, 11.2, 1.5, ZR, Ce, {"+z": M["roof"]})
        sh.box(11.2, 1.0, zc1, W - TE, 1.5, ZR, Ce, {"+z": M["roof"]})
        pt = 0.2

        def parapet(ax, c, a0, a1, top, m_lo, m_hi, cap=True):
            self.wall(ax, c, a0, a1, ZR, top, pt, [], m_lo, m_hi, m_lo)
            if cap:
                if ax == "x":
                    tr.box(a0 - 0.03, c - pt / 2 - 0.03, top, a1 + 0.03, c + pt / 2 + 0.03, top + 0.04, M["alu"])
                else:
                    tr.box(c - pt / 2 - 0.03, a0 - 0.03, top, c + pt / 2 + 0.03, a1 + 0.03, top + 0.04, M["alu"])

        parapet("x", 1.5, 0, 7.5, PAR, Wh, Wh)
        parapet("y", pt / 2, 1.6, D, PAR, Wh, Wh)
        parapet("x", D - pt / 2, pt, W - pt, PAR, Wh, Wh)
        parapet("y", W - pt / 2, 1.0, D, PAR, Wh, Wh)
        parapet("x", 1.0, 11.2, W - pt, PAR, Wh, Wh)
        # tower (wood) parapet box x 7.5..11.2, y -0.5..4.0
        parapet("y", 7.5 + pt / 2, -0.5 + TE, 4.0, TOWER, Wd, Wd)
        parapet("y", 11.2 - pt / 2, -0.5 + TE, 4.0, TOWER, Wd, Wd)
        parapet("x", 4.0, 7.5 + pt, 11.2 - pt, TOWER, Wd, Wd)
        tr.box(7.47, -0.53, TOWER, 11.23, -0.5 + TE + 0.03, TOWER + 0.04, M["alu"])
        # vertical timber battens on the tower front and cheeks
        bw, gap = 0.045, 0.085
        x = 7.5 + 0.02
        while x < 11.2 - bw:
            segs = [(Z1 - 0.3, f + 0.62), (f + 2.58, TOWER)] if 8.12 < x + bw / 2 < 10.58 else [(Z1 - 0.3, TOWER)]
            for (a, b) in segs:
                tr.box(x, -0.5 - 0.03, a, x + bw, -0.5, b, Wd)
            x += gap
        for xs, sgn in ((7.5, -1), (11.2, 1)):
            y = -0.5 + 0.02
            lim = 4.0
            while y < lim - bw:
                lo = ZR + 0.62 if (xs == 7.5 and y > -0.5) else Z1 - 0.3   # west cheek hidden by the frame below 7.55
                lo = max(lo, 7.57) if xs == 7.5 else (Z1 - 0.3 if y < 1.0 else PAR + 0.05)
                tr.box(xs + (0 if sgn > 0 else -0.03), y, lo, xs + (0.03 if sgn > 0 else 0), y + bw, TOWER, Wd)
                y += gap

        # ---- master balcony "picture frame" (dark grey) and glass rail
        fx0, fx1, fy0, fy1 = -0.28, 7.5, -0.95, 1.5 - TE / 2
        sh.box(fx0, fy0, Z1 - 0.34, fx1, 0.0, Z1, Gy, {"+z": M["out_tile"]})          # floor projecting part
        sh.box(fx0, 0.0, Z1 - 0.34, 0.0, fy1, Z1, Gy)
        sh.box(fx0, fy0, 7.22, fx1, fy1, 7.56, Gy)                                     # top
        sh.box(fx0, fy0, Z1, fx0 + 0.3, fy1, 7.22, Gy)                                 # west cheek
        sh.box(fx1 - 0.3, fy0, Z1, fx1, -0.5, 7.22, Gy)                                # east cheek (front part)
        self.glass_rail((fx0 + 0.3, fy0 + 0.1), (fx1 - 0.3, fy0 + 0.1), Z1)
        for sx in (1.5, 3.75, 6.0):
            self.spots.append((sx, 0.3, 7.22))
        # ---- right balcony + canopy
        sh.box(11.2, -0.4, Z1 - 0.22, W + 0.12, 1.0 - TE / 2, Z1, Wh, {"+z": M["out_tile"]})
        self.glass_rail((11.2, -0.32), (W + 0.04, -0.32), Z1)
        self.glass_rail((W + 0.04, -0.32), (W + 0.04, 0.88), Z1)
        sh.box(11.2, -1.0, ZR - 0.16, W + 0.65, 1.2, ZR, Gy)
        for sx in (12.2, 14.0):
            self.spots.append((sx, 0.2, ZR - 0.16))
        for sx in (8.3, 9.35, 10.4):
            self.spots.append((sx, 0.4, Z1 - 0.3))

        # ---- side-door canopies and details
        sh.box(W - 2.0, D, Z0 + 2.3, W - 0.6, D + 0.9, Z0 + 2.38, Gy)

        # ---- stairs
        self.stairs()

        # ---- skirtings (main rooms)
        self.skirting(TE, TE, 7.5 - TI / 2, 6.2 - TI / 2, Z0, gaps=[("s", 1.2, 6.3), ("w", 1.6, 4.6), ("n", 0.9, 4.5), ("e", TE, 3.2)])
        self.skirting(TE, 6.2 + TI / 2, 5.2 - TI / 2, D - TE, Z0, gaps=[("s", 0.9, 4.5), ("e", 7.0, 8.7)])
        self.skirting(TE, 1.5 + TE / 2, 7.5 - TI / 2, 6.2 - TI / 2, Z1, gaps=[("s", 1.4, 6.1), ("e", 1.75, 2.65), ("n", 1.2, 2.0), ("n", 4.3, 5.1)])
        self.skirting(11.2 + TI / 2, TE, W - TE, 5.2 - TI / 2, Z0, gaps=[("w", 1.55, 2.45), ("n", 11.6, 12.4)])

        n = self.name
        objs = [self.shell.build(n + "_shell", self.c), self.frames.build(n + "_frames", self.c),
                self.glass.build(n + "_glass", self.c), self.trim.build(n + "_trim", self.c)]
        return objs

    def stairs(self):
        M, tr, sh = self.M, self.trim, self.shell
        T, Wt = M["wood_dark"], M["int"]
        x_e0, x_e1 = 10.05, 11.13      # first (east) flight
        x_w0, x_w1 = 8.9, 9.98         # second (west) flight
        y0 = 2.8
        for i in range(1, 10):                      # 9 treads going north
            z = Z0 + i * RISE
            ya = y0 + (i - 1) * TREAD
            sh.box(x_e0, ya, z - RISE, x_e1, ya + TREAD, z - 0.04, Wt)
            tr.box(x_e0 - 0.01, ya - 0.025, z - 0.04, x_e1, ya + TREAD, z, T)
        yl = y0 + 9 * TREAD                         # landing start (5.23)
        zl = Z0 + 10 * RISE
        sh.box(x_w0, yl, zl - 0.16, x_e1, 6.2 - TI / 2, zl - 0.04, Wt)
        tr.box(x_w0, yl - 0.025, zl - 0.04, x_e1, 6.2 - TI / 2, zl, T)
        for j in range(1, 9):                       # 8 treads going south
            z = zl + j * RISE
            yb = yl - (j - 1) * TREAD
            sh.box(x_w0, yb - TREAD, z - RISE - 0.02, x_w1, yb, z - 0.04, Wt)
            tr.box(x_w0, yb - TREAD, z - 0.04, x_w1 + 0.01, yb + 0.025, z, T)
        # balustrades: glass along the open side of each flight and round the void
        G, S = M["glass_rail"], M["steel"]

        def sloped_glass(x, ya, za, yb, zb, h=0.95):
            self.glass.face([(x, ya, za + 0.05), (x, yb, zb + 0.05), (x, yb, zb + h), (x, ya, za + h)], G)
            self.glass.face([(x + 0.012, yb, zb + 0.05), (x + 0.012, ya, za + 0.05), (x + 0.012, ya, za + h), (x + 0.012, yb, zb + h)], G)
            tr.cyl((x + 0.006, ya, za + h + 0.02), (x + 0.006, yb, zb + h + 0.02), 0.02, S, seg=10)

        sloped_glass(x_e0 - 0.03, y0, Z0 + RISE, yl, zl + RISE * 0.5)
        sloped_glass(x_w1 + 0.02, yl, zl + RISE, 3.07, Z1)
        self.glass_rail((8.9 - 0.02, 3.07), (8.9 - 0.02, 6.13), Z1, h=1.0)
        self.glass_rail((9.98, 2.8), (11.13, 2.8), Z1, h=1.0)
        self.glass_rail((9.98, 2.8), (9.98, 3.07), Z1, h=1.0)
