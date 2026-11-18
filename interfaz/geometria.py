"""Geometria pura (numpy, sin Qt) de la vista 3D: casco convexo, rectangulo minimo y malla de cascarones."""
import numpy as np


def casco(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return np.array(pts, float)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1], float)


def rectangulo(pts, margen):
    """Rectangulo orientado de area minima que contiene los puntos (esquinas en sentido antihorario)."""
    h = casco(pts)
    mejor = None
    for i in range(len(h)):
        d = h[(i + 1) % len(h)] - h[i]
        a = np.arctan2(d[1], d[0])
        c, s = np.cos(a), np.sin(a)
        M = np.array([[c, -s], [s, c]])
        q = h @ M
        mn, mx = q.min(0) - margen, q.max(0) + margen
        area = np.prod(mx - mn)
        if mejor is None or area < mejor[0]:
            mejor = (area, M, mn, mx)
    _, M, mn, mx = mejor
    esq = np.array([[mn[0], mn[1]], [mx[0], mn[1]], [mx[0], mx[1]], [mn[0], mx[1]]])
    return esq @ M.T


class Malla:
    """Acumula la geometria de los cascarones: superficies translucidas, aristas y columnas."""

    def __init__(self, zex):
        self.zex = zex
        self.v, self.f, self.c, self.nv = [], [], [], 0
        self.bp, self.bc, self.kp, self.kc = [], [], [], []

    def _z(self, H, z):
        return np.c_[H, np.full(len(H), z * self.zex)]

    def anillo(self, H, z, col):
        v = self._z(H, z)
        a = np.vstack([v, v[:1]])
        seg = np.repeat(a, 2, axis=0)[1:-1]
        self.bp.append(seg)
        self.bc.append(np.tile(col, (len(seg), 1)))

    def losa(self, H, z, col, borde):
        n = len(H)
        self.v.append(self._z(H, z))
        self.f.append(np.array([[self.nv, self.nv + k, self.nv + k + 1] for k in range(1, n - 1)]))
        self.c.append(np.tile(col, (n - 2, 1)))
        self.nv += n
        self.anillo(H, z, borde)

    def muro(self, H, z0, z1, col):
        n = len(H)
        self.v += [self._z(H, z0), self._z(H, z1)]
        caras = []
        for i in range(n):
            j = (i + 1) % n
            caras += [[self.nv + i, self.nv + j, self.nv + n + j], [self.nv + i, self.nv + n + j, self.nv + n + i]]
        self.f.append(np.array(caras))
        self.c.append(np.tile(col, (len(caras), 1)))
        self.nv += 2 * n

    def columnas(self, H, idx, z0, z1, col):
        for i in idx:
            self.kp.append(np.array([[H[i, 0], H[i, 1], z0 * self.zex], [H[i, 0], H[i, 1], z1 * self.zex]]))
            self.kc.append(np.tile(col, (2, 1)))
