"""
Pisos reconstruidos de las placas fotografiadas y anotadas por el equipo.
Cada foto se lleva a pixeles de plano.png con una homografia ajustada sobre las esquinas del edificio. El esqueleto de
pasillos, escaleras y ascensor se define una vez por pabellon (en la foto de referencia) y se repite en todos los pisos,
de modo que los ejes se apilan; las salas y puertas de cada piso salen de su propia foto.

esq   = dict(pares, cadenas, accesos, inicio, fin, entradas, asc_ext)
piso  = dict(pares, salas=[(nombre, centro, [puertas])], extras=[cadena...])   # coordenadas de la foto
"""
import math

import numpy as np

from modelo import puertas
from modelo.config import ALTO_PISO, BASE_Z, COSTO_ASCENSOR, COSTO_ESCALERA, ESCALA, ESPACIADO


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


def _d2(n, xy):
    return (n["x_px"] - xy[0]) ** 2 + (n["y_px"] - xy[1]) ** 2


def construir_piso(G, pab, p, z, esq, datos):
    f0, f = ajustar(esq["pares"]), ajustar(datos["pares"])
    pre = f"{pab}{p}_"
    en, corr = {}, []   # punto de la foto de referencia -> id; ids de pasillo

    def pasillo(xy, clave=None):
        i = f"{pre}c{len(corr):02d}"
        G.nodo(i, xy[0], xy[1], z, p, pab, "pasillo")
        corr.append(i)
        if clave is not None:
            en[clave] = i
        return i

    def cadena(vs, fn, claves=True):
        previo = None
        pts = [fn(*v) for v in vs]
        for k, v in enumerate(vs):
            if k:
                a, b = pts[k - 1], pts[k]
                n = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) * ESCALA / ESPACIADO))
                for j in range(1, n):
                    i = pasillo((a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n))
                    G.arista(previo, i, "pasillo")
                    previo = i
            i = en.get(v) if claves else None
            if i is None:
                i = pasillo(pts[k], v if claves else None)
            if previo and previo != i:
                G.arista(previo, i, "pasillo")
            previo = i

    for vs in esq["cadenas"]:
        cadena(vs, f0)
    anc = {}
    for clave, vs in esq["accesos"].items():
        cadena(vs[:-1], f0)
        xy = f0(*vs[-1])
        i = f"{pre}{clave}"
        G.nodo(i, xy[0], xy[1], z, p, pab, "ascensor" if clave == "asc" else "escalera",
               f"Ascensor {pab}" if clave == "asc" else f"Escalera {clave[-1]}")
        G.arista(en[vs[-2]], i, "pasillo")
        anc[(p, clave)] = i

    base = list(corr)
    for vs in datos.get("extras", []):
        cadena(vs, f, claves=False)
        nuevos = [i for i in corr if i not in base]
        a, b = min(((x, y) for x in nuevos for y in base), key=lambda t: _d2(G.nodos[t[0]], (G.nodos[t[1]]["x_px"], G.nodos[t[1]]["y_px"])))
        G.arista(a, b, "pasillo")
        base += nuevos

    for j, (etq, centro, pts) in enumerate(datos["salas"]):
        sid = f"{pre}rp{j:02d}"
        G.nodo(sid, *f(*centro), z, p, pab, "zona", etq)
        for n, pt in enumerate(pts or [None]):
            xy = f(*pt) if pt else f(*centro)
            ancla = min(corr, key=lambda i: _d2(G.nodos[i], xy))
            if not pt:   # sin puerta marcada: se supone a mitad de camino entre la sala y el pasillo
                xy = ((xy[0] + G.nodos[ancla]["x_px"]) / 2, (xy[1] + G.nodos[ancla]["y_px"]) / 2)
            puertas.poner_puerta(G, ancla, sid, sid + ("_p" if n == 0 else f"_p{n + 1}"), xy, z, p, pab,
                                 etq if n == 0 else f"{etq} ({n + 1})")
    ids = list(corr)
    for clave, pos in (("inicio", 0), ("fin", None)):
        if esq.get(clave):
            i = en[esq[clave]]
            ids.remove(i)
            ids.insert(0, i) if pos == 0 else ids.append(i)
    return ids, anc, en


def construir(G, pab, esq, pisos):
    base_z = BASE_Z[pab]
    ids_por_piso, anc = {}, {}
    for p in sorted(pisos):
        ids, a, en = construir_piso(G, pab, p, base_z + (p - 1) * ALTO_PISO, esq, pisos[p])
        ids_por_piso[p] = ids
        anc.update(a)
        if p == 1:
            for ext, pt in esq.get("entradas", []):
                a_, b_ = G.nodos[ext], G.nodos[en[pt]]
                pid = f"{pab}1_puerta_{ext}"
                G.nodo(pid, (a_["x_px"] + b_["x_px"]) / 2, (a_["y_px"] + b_["y_px"]) / 2, base_z, 1, pab, "puerta",
                       f"Puerta de ingreso {pab} ({a_['etiqueta'] or ext})", ancho_m=puertas.ANCHO_DEF, escalon=False)
                G.arista(ext, pid, "puerta")
                G.arista(pid, en[pt], "puerta")
    for p in sorted(pisos)[:-1]:
        for clave in esq["accesos"]:
            if clave == "asc":
                G.arista(anc[(p, clave)], anc[(p + 1, clave)], "ascensor", acc=True, w=ALTO_PISO + COSTO_ASCENSOR)
            else:
                G.arista(anc[(p, clave)], anc[(p + 1, clave)], "escalera", acc=False, w=ALTO_PISO * COSTO_ESCALERA)
    if esq.get("asc_ext"):
        G.arista(esq["asc_ext"], anc[(1, "asc")], "puerta")
    return ids_por_piso
