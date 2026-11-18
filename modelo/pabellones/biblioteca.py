"""
Pabellon I - Biblioteca, pisos 1 a 7, a partir de las placas de evacuacion y mapa de riesgos.

Cada piso tiene una torre circular (anillo de circulacion + anillo interior unidos por radios; centro solo en
p1, p2, p6 y p7), una extension delgada al oeste con sus escaleras y banos, y el hall con los 2 ascensores en su
extremo sur. Las placas estan giradas 90 grados respecto de plano.png (el Control de la placa es la entrada
accesible P23, al este): (u, v) son desplazamientos en la orientacion de la placa y _g() los lleva al plano.
Medidas del plano: circulo de R = 51.5 px con centro (121, 620); la extension queda pegada al muro oeste (x = 61);
los ascensores estan sobre los iconos amarillos de plano.png, (97,688) y (113,682).
La numeracion de los cubiculos interiores (pisos 6 y 7) puede diferir en 1-2 numeros de las placas.
"""
import math

from modelo import puertas
from modelo.pabellones import datos
from modelo.config import ALTO_PISO, BASE_Z, COSTO_ASCENSOR, COSTO_ESCALERA, ESCALA, ESPACIADO

_D = datos.crudo("I")
_G = _D["geometria"]
CX, CY, R = _G["CX"], _G["CY"], _G["R"]
N_ANILLO, N_INTERIOR = _G["N_ANILLO"], _G["N_INTERIOR"]
R_ANILLO, R_INTERIOR = _G["R_ANILLO"], _G["R_INTERIOR"]     # fracciones de R
V_ANEXO = _G["V_ANEXO"]                                       # pasillo del anexo (en R, orientacion de la placa)
U_ANEXO = _G["U_ANEXO"]
DV_ANEXO = _G["DV_ANEXO"]            # las salas del anexo se acercan al pasillo: la extension del plano es angosta
OFF_ESC = _G["OFF_ESC"]              # px que la escalera sobresale del pasillo del anexo
ASC1, ASC2, HALL = _G["ASC1"], _G["ASC2"], _G["HALL"]
N_ANEXO = max(int(math.ceil((U_ANEXO[1] - U_ANEXO[0]) * R * ESCALA / ESPACIADO)) + 1, 8)
NODO_ENLACE_K = f"a{N_ANEXO - 1:02d}"  # extremo norte del anexo: escalera de emergencia y plataforma hacia K

# {piso: [("anillo"|"interior"|"anexo"|"centro", etiqueta, angulo_grados | u, dv_anexo)]}
# angulos: y hacia abajo, 0 = este, 90 = sur, 180 = oeste, 270 = norte
SALAS = {int(p): [tuple(s) for s in v] for p, v in _D["salas"].items()}

# Piso 7: puertas marcadas por el equipo en la placa (foto 1600x1200; circulo de ~345 x 325 px centrado en (835, 705))
PUERTAS_P7 = _D["puertas_p7"]


def _g(u, v):
    """Desplazamiento (u derecha, v abajo, en R, orientacion de la placa) -> pixel de plano.png (giro de -90 grados)."""
    return CX + v * R, CY - u * R


def _puerta_p7(xy, usadas):
    """Puerta marcada por el equipo mas cercana (a menos de 8 px de plano) a la sala en `xy`, o None."""
    cand = [(math.hypot(_g((px - 835) / 345, (py - 705) / 325)[0] - xy[0], _g((px - 835) / 345, (py - 705) / 325)[1] - xy[1]), k)
            for k, (px, py) in enumerate(PUERTAS_P7) if k not in usadas]
    if not cand or min(cand)[0] > 8:
        return None
    d, k = min(cand)
    usadas.add(k)
    px, py = PUERTAS_P7[k]
    return _g((px - 835) / 345, (py - 705) / 325)


def _pol(ang_deg, frac):
    a = math.radians(ang_deg - 90)
    return CX + frac * R * math.cos(a), CY + frac * R * math.sin(a)


def _circulo(cx, cy, r, lados=40):
    return [(cx + r * math.cos(2 * math.pi * k / lados), cy + r * math.sin(2 * math.pi * k / lados)) for k in range(lados)]


# huella 3D en px: torre, extension oeste con la plataforma hacia K y lobulo de los ascensores
HUELLAS = [_circulo(CX, CY, R + 0.5), [(61, 560), (98, 560), (98, 681), (61, 681)], [(94, 672), (118, 672), (118, 692), (94, 692)]]


PISOS = _D["pisos"]


def construir(G):
    n_anexo = N_ANEXO
    anexo_pts = [_g(U_ANEXO[0] + (U_ANEXO[1] - U_ANEXO[0]) * k / (n_anexo - 1), V_ANEXO) for k in range(n_anexo)]

    def k_anexo(u):
        return int(round((u - U_ANEXO[0]) / (U_ANEXO[1] - U_ANEXO[0]) * (n_anexo - 1)))

    anc = {}
    for piso in range(1, PISOS + 1):
        z = BASE_Z["I"] + (piso - 1) * ALTO_PISO
        pre = f"I{piso}_"
        for k in range(N_ANILLO):
            x, y = _pol(360 * k / N_ANILLO, R_ANILLO)
            G.nodo(f"{pre}o{k:02d}", x, y, z, piso, "I", "pasillo")
        for k in range(N_ANILLO):
            G.arista(f"{pre}o{k:02d}", f"{pre}o{(k + 1) % N_ANILLO:02d}", "pasillo")
        for k in range(N_INTERIOR):
            x, y = _pol(360 * k / N_INTERIOR, R_INTERIOR)
            G.nodo(f"{pre}n{k:02d}", x, y, z, piso, "I", "pasillo")
        for k in range(N_INTERIOR):
            G.arista(f"{pre}n{k:02d}", f"{pre}n{(k + 1) % N_INTERIOR:02d}", "pasillo")
            G.arista(f"{pre}n{k:02d}", f"{pre}o{2 * k:02d}", "pasillo")
        if piso in (1, 2, 6, 7):     # centro con piso (p3-p5: vacio central)
            G.nodo(f"{pre}centro", CX, CY, z, piso, "I", "pasillo", "centro")
            for k in range(0, N_INTERIOR, 3):
                G.arista(f"{pre}centro", f"{pre}n{k:02d}", "pasillo")
        for k, (x, y) in enumerate(anexo_pts):
            G.nodo(f"{pre}a{k:02d}", x, y, z, piso, "I", "pasillo")
        for k in range(n_anexo - 1):
            G.arista(f"{pre}a{k:02d}", f"{pre}a{k + 1:02d}", "pasillo")
        G.arista(f"{pre}a{k_anexo(-0.05):02d}", f"{pre}o{18:02d}", "pasillo")
        G.arista(f"{pre}a{k_anexo(-0.62):02d}", f"{pre}o{17:02d}", "pasillo")
        G.arista(f"{pre}a{k_anexo(0.7):02d}", f"{pre}o{20:02d}", "pasillo")
        for s, u in ((1, -0.87), (2, 0.96)):
            x, y = anexo_pts[k_anexo(u)]
            G.nodo(f"{pre}esc{s}", x - OFF_ESC, y, z, piso, "I", "escalera", f"Escalera {s}")
            G.arista(f"{pre}a{k_anexo(u):02d}", f"{pre}esc{s}", "pasillo")
            anc[(piso, f"esc{s}")] = f"{pre}esc{s}"
        G.nodo(f"{pre}hall", *HALL, z, piso, "I", "pasillo", "Hall de ascensores")
        G.nodo(f"{pre}asc1", *ASC1, z, piso, "I", "ascensor", "Ascensor 1 (I)")
        G.nodo(f"{pre}asc2", *ASC2, z, piso, "I", "ascensor", "Ascensor 2 (I)")
        G.arista(f"{pre}hall", f"{pre}asc1", "pasillo")
        G.arista(f"{pre}hall", f"{pre}asc2", "pasillo")
        G.arista(f"{pre}hall", f"{pre}a{k_anexo(-0.87):02d}", "pasillo")
        G.arista(f"{pre}hall", f"{pre}o{14:02d}", "pasillo")
        anc[(piso, "asc1")] = f"{pre}asc1"
        anc[(piso, "asc2")] = f"{pre}asc2"
        usados, p7 = set(), set()
        for tipo, etq, a, dv in SALAS[piso]:
            zid = f"{pre}Z{len(usados):02d}"
            usados.add(zid)
            if tipo == "anillo":
                x, y = _pol(a, 0.93)
                ancla = f"{pre}o{int(round(a / (360 / N_ANILLO))) % N_ANILLO:02d}"
            elif tipo == "interior":
                x, y = _pol(a, 0.27)
                ancla = f"{pre}n{int(round(a / (360 / N_INTERIOR))) % N_INTERIOR:02d}"
            elif tipo == "centro":
                x, y = CX + (6 if "58" in etq else 0), CY
                ancla = f"{pre}centro"
            else:   # anexo
                kk = k_anexo(a)
                x, y = anexo_pts[kk][0] + dv * DV_ANEXO * R, anexo_pts[kk][1]
                ancla = f"{pre}a{kk:02d}"
            if ancla not in G.nodos:      # p3-p5 no tienen centro
                continue
            abierta = etq.startswith(("Hall", "Sala de lectura", "Mediateca", "Modulo", "Counter", "Fotocopia auto",
                                      "Control", "Terraza", "Estante", "Libreria"))
            pxy = _puerta_p7((x, y), p7) if piso == 7 and not abierta else None
            puertas.poner_sala(G, ancla, zid, etq, (x, y), z, piso, "I", puerta=not abierta, puerta_xy=pxy)
    for piso in range(1, PISOS):
        for s in ("esc1", "esc2"):
            G.arista(anc[(piso, s)], anc[(piso + 1, s)], "escalera", acc=False, w=ALTO_PISO * COSTO_ESCALERA)
        for s in ("asc1", "asc2"):
            G.arista(anc[(piso, s)], anc[(piso + 1, s)], "ascensor", acc=True, w=ALTO_PISO + COSTO_ASCENSOR)
    # entrada accesible del campus (piso 1, lado este del anillo: el Control de la placa)
    G.arista("P23", "I1_o06", "puerta")
    # el icono amarillo de plano.png junto a la cruz roja es la entrada exterior de estos ascensores
    for a in ("asc1", "asc2"):
        G.arista("A22", f"I1_{a}", "puerta")
