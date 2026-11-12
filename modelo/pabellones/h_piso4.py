"""
Pabellon H, piso 4, reconstruido de la placa de evacuacion fotografiada y anotada por el equipo.
Las coordenadas estan en pixeles de la foto (1600x1200) y se llevan a pixeles de plano.png con un ajuste afin calculado
sobre 6 esquinas de la huella (error maximo ~0.7 m). Pasillo en L (sur + este), salas dentro de la huella, una puerta
por cada rectangulo rojo marcado en la placa.
"""
import math

from modelo import puertas
from modelo.config import ESCALA, ESPACIADO

_M = ((0.147034, -0.003137, 533.685484), (-0.000364, 0.147243, 371.802623))
PASO_FOTO = ESPACIADO / ESCALA / _M[0][0]


def px(x, y):
    return (_M[0][0] * x + _M[0][1] * y + _M[0][2], _M[1][0] * x + _M[1][1] * y + _M[1][2])


PASILLO = [(330, 780), (410, 780), (535, 780), (730, 780), (760, 780), (850, 780), (915, 780), (958, 780), (1005, 780),
           (1005, 680), (1005, 642), (1005, 490), (1005, 452), (1005, 410), (1005, 380), (1005, 335), (1005, 316)]
VESTIBULO = [(410, 780), (410, 725), (410, 700), (410, 672), (432, 672)]
ACCESOS = {"esc1": ((1005, 335), (965, 335), (925, 320)),
           "esc2": ((730, 780), (730, 740), (755, 690)),
           "esc3": ((410, 700), (345, 700), (305, 700)),
           "asc": ((915, 780), (915, 745), (915, 715))}

# nombre, centro, [(puerta, ancla en el pasillo)]
SALAS = [
    ("Lab. software entretenimiento H-40", (365, 520), [((432, 641), (432, 672))]),
    ("Lab. computo H-41", (418, 905), [((535, 810), (535, 780))]),
    ("Aula H-42", (665, 905), [((760, 808), (760, 780))]),
    ("Taller de diseno H-43", (1050, 905), [((958, 807), (958, 780))]),
    ("Aula H-44", (1130, 735), [((1040, 680), (1005, 680))]),
    ("Lab. computo H-45", (1140, 560), [((1040, 490), (1005, 490)), ((1040, 642), (1005, 642))]),
    ("Taller de diseno H-46", (1170, 385), [((1040, 316), (1005, 316)), ((1040, 452), (1005, 452))]),
    ("Sala H-47 (aprox)", (865, 540), [((970, 410), (1005, 410))]),
    ("Sala de servidores", (512, 640), [((445, 725), (410, 725))]),
    ("SSHH hombres", (815, 915), [((825, 800), (850, 780))]),
    ("SSHH mujeres", (890, 915), [((875, 800), (850, 780))]),
    ("Oficina PTC", (840, 345), [((970, 380), (1005, 380))]),
]

CONTORNO = [(281, 287), (580, 565), (775, 563), (775, 292), (1360, 298), (1195, 976), (285, 998)]
HUELLAS = [[px(*p) for p in CONTORNO]]
EJES = {"esc": [px(*ACCESOS[k][-1]) for k in ("esc1", "esc2", "esc3")], "asc": px(*ACCESOS["asc"][-1])}


def _tramos(vertices):
    """Puntos del pasillo: cada vertice y subdivisiones de ~ESPACIADO entre vertices consecutivos."""
    out = [vertices[0]]
    for (x0, y0), (x1, y1) in zip(vertices, vertices[1:]):
        n = max(1, round(math.hypot(x1 - x0, y1 - y0) / PASO_FOTO))
        out += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(1, n + 1)]
    return out


def construir(G, z, piso, pab="H"):
    pre = f"{pab}{piso}_"
    en = {}   # punto de la foto -> id

    def nodo(pt, tipo="pasillo", i=None, etq=""):
        i = i or f"{pre}c{len(en):02d}"
        G.nodo(i, *px(*pt), z, piso, pab, tipo, etq)
        en[pt] = i
        return i

    def cadena(vertices):
        previo = None
        for pt in _tramos(vertices):
            i = en.get(pt) or nodo(pt)
            if previo and previo != i:
                G.arista(previo, i, "pasillo")
            previo = i

    cadena(PASILLO)
    ids = list(en.values())
    cadena(VESTIBULO)
    anc = {}
    for clave, (junta, medio, fin) in ACCESOS.items():
        cadena([junta, medio])
        nombre = {"asc": f"Ascensor {pab}"}.get(clave, f"Escalera {clave[-1]}")
        i = nodo(fin, "ascensor" if clave == "asc" else "escalera", f"{pre}{clave}", nombre)
        G.arista(en[medio], i, "pasillo")
        anc[(piso, clave)] = i

    for j, (etq, centro, puertas_) in enumerate(SALAS):
        sid = f"{pre}rp{j:02d}"
        G.nodo(sid, *px(*centro), z, piso, pab, "zona", etq)
        for n, (pt, ancla) in enumerate(puertas_):
            puertas.poner_puerta(G, en[ancla], sid, sid + ("_p" if n == 0 else f"_p{n + 1}"), px(*pt), z, piso, pab,
                                 etq if n == 0 else f"{etq} ({n + 1})")
    return ids, anc
