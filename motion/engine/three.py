"""Just enough 3D: rotations, a look-at camera with perspective, and point/mesh generators."""
import math

import numpy as np

from .core import W, H


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Cam:
    """Right-handed, y up. project() returns screen x, y, camera depth and a visibility mask."""

    def __init__(self, eye, target=(0, 0, 0), fov=40.0, up=(0, 1, 0), cx=W / 2, cy=H / 2, roll=0.0):
        self.eye = np.asarray(eye, np.float64)
        f = np.asarray(target, np.float64) - self.eye
        f /= np.linalg.norm(f)
        r = np.cross(f, np.asarray(up, np.float64))
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        if roll:
            cr, sr = math.cos(roll), math.sin(roll)
            r, u = r * cr + u * sr, -r * sr + u * cr
        self.R = np.stack([r, u, f])
        self.focal = (H / 2) / math.tan(math.radians(fov) / 2)
        self.cx, self.cy = cx, cy

    def to_cam(self, pts):
        return (np.asarray(pts, np.float64) - self.eye) @ self.R.T

    def project(self, pts, near=0.05):
        pc = self.to_cam(pts)
        z = pc[:, 2]
        vis = z > near
        zs = np.where(vis, z, near)
        x = self.cx + pc[:, 0] * self.focal / zs
        y = self.cy - pc[:, 1] * self.focal / zs
        return x, y, z, vis


def fib_sphere(n, r=1.0):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([r * np.cos(th) * np.sin(phi), r * np.cos(phi), r * np.sin(th) * np.sin(phi)], 1)


def torus(nu, nv, R=1.0, r=0.35):
    u = np.linspace(0, 2 * math.pi, nu, endpoint=False)
    v = np.linspace(0, 2 * math.pi, nv, endpoint=False)
    uu, vv = np.meshgrid(u, v, indexing="ij")
    x = (R + r * np.cos(vv)) * np.cos(uu)
    z = (R + r * np.cos(vv)) * np.sin(uu)
    y = r * np.sin(vv)
    return np.stack([x.ravel(), y.ravel(), z.ravel()], 1)


def ring(n, r=1.0, y=0.0):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([r * np.cos(a), np.full(n, y), r * np.sin(a)], 1)


def icosahedron():
    p = (1 + 5 ** 0.5) / 2
    v = np.array([[-1, p, 0], [1, p, 0], [-1, -p, 0], [1, -p, 0], [0, -1, p], [0, 1, p],
                  [0, -1, -p], [0, 1, -p], [p, 0, -1], [p, 0, 1], [-p, 0, -1], [-p, 0, 1]], float)
    v /= np.linalg.norm(v[0])
    f = np.array([[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4],
                  [11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8],
                  [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]])
    return v, f


def edges_of(faces):
    e = set()
    for a, b, c in faces:
        for i, j in ((a, b), (b, c), (c, a)):
            e.add((min(i, j), max(i, j)))
    return np.array(sorted(e))


def subdivide(v, f, levels=1):
    for _ in range(levels):
        cache = {}
        verts = list(v)

        def mid(i, j):
            k = (min(i, j), max(i, j))
            if k not in cache:
                m = (verts[i] + verts[j]) / 2
                verts.append(m / np.linalg.norm(m))
                cache[k] = len(verts) - 1
            return cache[k]
        nf = []
        for a, b, c in f:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        v, f = np.array(verts), np.array(nf)
    return v, f
