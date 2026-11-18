"""
Pisos reconstruidos de las placas fotografiadas y anotadas por el equipo.
Cada foto se lleva a pixeles de plano.png con una homografia ajustada sobre puntos del edificio. El esqueleto de pasillos,
escaleras y ascensor se define una vez por pabellon (en la foto de referencia) y se repite en todos los pisos, de modo que
los ejes se apilan; las salas y puertas de cada piso salen de su propia foto. Un piso con circulacion distinta puede traer
su propio esqueleto (clave "esq" del piso), pero escaleras y ascensor conservan la posicion fijada por el primer piso.

esq   = dict(pares, cadenas, accesos, inicio, fin, entradas, asc_ext, enlaces)
piso  = dict(pares, salas=[(nombre, centro, [puertas])], extras=[cadena...], esq=dict(cadenas, accesos, entradas)?)
Todas las coordenadas del esqueleto y del piso estan en pixeles de la foto correspondiente.
"""
import math

from modelo import puertas
from modelo.nomenclatura import numerar
from modelo.registro import ajustar, semejanza
from modelo.config import ALTO_PISO, BASE_Z, COSTO_ASCENSOR, COSTO_ESCALERA, ESCALA, ESPACIADO


def _d2(n, xy):
    return (n["x_px"] - xy[0]) ** 2 + (n["y_px"] - xy[1]) ** 2


def construir_piso(G, pab, p, z, esq, datos, fijos):
    esq_p = datos.get("esq")
    base = {**esq, **esq_p} if esq_p else esq
    aj = semejanza if datos.get("modelo") == "sim" else ajustar
    f = aj(datos["pares"])
    f0 = f if esq_p else ajustar(esq["pares"])
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

    for vs in base["cadenas"]:
        cadena(vs, f0)
    anc = {}
    for clave, vs in base["accesos"].items():
        cadena(vs[:-1], f0)
        xy = fijos.setdefault(clave, f0(*vs[-1]))
        i = f"{pre}{clave}"
        G.nodo(i, xy[0], xy[1], z, p, pab, "ascensor" if clave.startswith("asc") else "escalera",
               f"Ascensor {pab}" if clave.startswith("asc") else f"Escalera {clave[-1]}")
        G.arista(en[vs[-2]], i, "pasillo")
        anc[(p, clave)] = i

    base_ids = list(corr)
    for vs in datos.get("extras", []):
        cadena(vs, f, claves=False)
        nuevos = [i for i in corr if i not in base_ids]
        a, b = min(((x, y) for x in nuevos for y in base_ids), key=lambda t: _d2(G.nodos[t[0]], (G.nodos[t[1]]["x_px"], G.nodos[t[1]]["y_px"])))
        G.arista(a, b, "pasillo")
        base_ids += nuevos

    for j, (etq, centro, pts) in enumerate(numerar(datos["salas"])):
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
        if base.get(clave):
            i = en[base[clave]]   # KeyError si la clave no es un vertice del esqueleto de ese piso
            ids.remove(i)
            ids.insert(0, i) if pos == 0 else ids.append(i)
    return ids, anc, en, base


def construir(G, pab, esq, pisos):
    base_z = BASE_Z[pab]
    ids_por_piso, anc = {}, {}
    f_ref = ajustar(esq["pares"])
    fijos = {clave: f_ref(*vs[-1]) for clave, vs in esq["accesos"].items()}   # ejes verticales: posicion del esqueleto base
    for p in sorted(pisos):
        ids, a, en, base = construir_piso(G, pab, p, base_z + (p - 1) * ALTO_PISO, esq, pisos[p], fijos)
        ids_por_piso[p] = ids
        anc.update(a)
        if p == 1:
            for k, (ext, pt, *nota) in enumerate(base.get("entradas", [])):
                a_, b_ = G.nodos[ext], G.nodos[en[pt]]
                pid = f"{pab}1_puerta_{ext}" + (f"_{k + 1}" if k else "")
                G.nodo(pid, (a_["x_px"] + b_["x_px"]) / 2, (a_["y_px"] + b_["y_px"]) / 2, base_z, 1, pab, "puerta",
                       f"Puerta de ingreso {pab} ({a_['etiqueta'] or ext})", ancho_m=puertas.ANCHO_DEF, escalon=False)
                G.arista(ext, pid, "puerta", nota=nota[0] if nota else "")
                G.arista(pid, en[pt], "puerta", nota=nota[0] if nota else "")
    for p in sorted(pisos)[:-1]:
        for clave in sorted({k for _, k in anc}):
            if (p, clave) not in anc or (p + 1, clave) not in anc:
                continue
            if clave.startswith("asc"):
                G.arista(anc[(p, clave)], anc[(p + 1, clave)], "ascensor", acc=True, w=ALTO_PISO + COSTO_ASCENSOR)
            else:
                G.arista(anc[(p, clave)], anc[(p + 1, clave)], "escalera", acc=False, w=ALTO_PISO * COSTO_ESCALERA)
    if esq.get("asc_ext"):
        G.arista(esq["asc_ext"], anc[(1, "asc")], "puerta")
    return ids_por_piso
