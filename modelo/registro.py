"""
Registro de fotos: lleva puntos de una placa fotografiada a pixeles de plano.png.
"""
import numpy as np


def ajustar(pares):
    """Foto -> plano a partir de pares ((x, y), (X, Y)): afin exacta con 3 pares, homografia con 4 o mas."""
    if len(pares) == 3:
        m = np.linalg.solve(np.array([[x, y, 1.0] for (x, y), _ in pares]), np.array([q for _, q in pares], float))
        return lambda x, y: tuple(float(v) for v in np.array([x, y, 1.0]) @ m)
    filas = []
    for (x, y), (u, v) in pares:
        filas += [[x, y, 1, 0, 0, 0, -u * x, -u * y, -u], [0, 0, 0, x, y, 1, -v * x, -v * y, -v]]
    h = np.linalg.svd(np.array(filas, float))[2][-1].reshape(3, 3)

    def f(x, y):
        a, b, c = h @ (x, y, 1.0)
        return (float(a / c), float(b / c))
    return f


def semejanza(pares):
    """Foto -> plano con escala uniforme, giro y traslacion (minimos cuadrados): para pares casi alineados, donde una
    homografia extrapola mal."""
    a = np.array([p for p, _ in pares], float)
    b = np.array([q for _, q in pares], float)
    ma, mb = a.mean(0), b.mean(0)
    u, d, vt = np.linalg.svd((b - mb).T @ (a - ma))
    r = u @ np.diag([1, np.sign(np.linalg.det(u @ vt))]) @ vt
    k = (d * [1, np.sign(np.linalg.det(u @ vt))]).sum() / ((a - ma) ** 2).sum()
    return lambda x, y: tuple(float(v) for v in k * r @ (np.array([x, y]) - ma) + mb)
