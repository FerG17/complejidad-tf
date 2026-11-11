"""
Pabellon I - Biblioteca, pisos 1 a 7, a partir de las placas de evacuacion y mapa de riesgos.

Cada piso tiene una torre circular (anillo de circulacion + anillo interior unidos por radios; centro solo en
p1, p2, p6 y p7), una extension delgada al oeste con sus escaleras y banos, y el hall con los 2 ascensores en su
extremo sur. Las placas estan giradas 90 grados respecto de plano.png (el Control de la placa es la entrada
accesible P23, al este): (u, v) son desplazamientos en la orientacion de la placa y _g() los lleva al plano.
Medidas del plano: circulo de R = 51.5 px con centro (121, 620); la extension queda pegada al muro oeste (x = 61);
los ascensores estan sobre los iconos amarillos de plano.png, (97,688) y (113,682).
Los cubiculos marcados "(aprox)" pueden diferir en 1-2 numeros de las placas.
"""
import math

from modelo import puertas
from modelo.config import ALTO_PISO, BASE_Z, COSTO_ASCENSOR, COSTO_ESCALERA, ESCALA, ESPACIADO

CX, CY, R = 121.0, 620.0, 51.5
N_ANILLO, N_INTERIOR = 24, 12
R_ANILLO, R_INTERIOR = 0.68, 0.42     # fracciones de R
V_ANEXO = -1.07                       # pasillo del anexo (en R, orientacion de la placa)
U_ANEXO = (-0.95, 0.95)
DV_ANEXO = 0.3                        # las salas del anexo se acercan al pasillo: la extension del plano es angosta
OFF_ESC = 4                           # px que la escalera sobresale del pasillo del anexo
ASC1, ASC2, HALL = (98.0, 684.0), (113.0, 680.0), (105.0, 677.0)
N_ANEXO = max(int(math.ceil((U_ANEXO[1] - U_ANEXO[0]) * R * ESCALA / ESPACIADO)) + 1, 8)
NODO_ENLACE_K = f"a{N_ANEXO - 1:02d}"  # extremo norte del anexo: escalera de emergencia y plataforma hacia K

# ("anillo"|"interior"|"anexo"|"centro", etiqueta, angulo_grados | u, dv_anexo)
# angulos: y hacia abajo, 0 = este, 90 = sur, 180 = oeste, 270 = norte
SALAS = {1: [
    ("centro", "Hall de ingreso", 0, 0),
    ("interior", "Counter de atencion", 268, 0),
    ("interior", "Fotocopia auto-asistida", 300, 0),
    ("anillo", "Sala de computadoras", 140, 0),
    ("anillo", "Sala de computadoras 30 alumnos", 40, 0),
    ("anillo", "Control (ingreso sur)", 90, 0),
    ("anexo", "Libreria (25)", 0.45, -0.28),
    ("anexo", "SSHH", -0.45, -0.28),
], 2: [
    ("centro", "Hall central (vacio con piso)", 0, 0),
    ("interior", "Hall central", 268, 0),
    ("anillo", "Oficina / Asesoria Arizona", 212, 0),
    ("anillo", "Mediateca", 180, 0),
    ("anillo", "Sala de red", 20, 0),
    ("anillo", "Almacen / Of. Arizona", 105, 0),
    ("anexo", "SSHH", -0.45, -0.28),
    ("anexo", "Sala de capacitacion", -0.05, -0.28),
    ("anexo", "Oficina Editorial UPC", 0.25, -0.28),
    ("anexo", "Oficina coordinador CI", 0.45, -0.28),
    ("anexo", "Direccion de gestion del conocimiento", 0.65, -0.28),
], 3: [
    ("interior", "Modulos de busqueda", 250, 0),
    ("anillo", "Modulo de atencion central", 270, 0),
    ("anillo", "Sala de lectura", 90, 0),
    ("anexo", "SSHH", -0.45, -0.28),
    ("anexo", "Sala Bloomberg", -0.05, -0.28),
    ("anexo", "Almacen de libros", 0.12, -0.28),
    ("anexo", "Cubiculo", 0.3, -0.28),
    ("anexo", "Jefatura corporativa centros de informacion", 0.6, -0.28),
], 4: [
    ("interior", "Hall", 268, 0),
    ("anillo", "Sala de lectura", 90, 0),
    ("anexo", "SSHH", -0.45, -0.28),
    ("anexo", "Analisis de informacion", -0.05, -0.28),
    ("anexo", "Apoyo de produccion temporal", 0.2, -0.28),
    ("anexo", "Gestion de coleccion", 0.5, -0.28),
    ("anexo", "Jefe de apoyo de produccion temporal", 0.62, -0.28),
], 5: [
    ("interior", "Hall", 268, 0),
    ("anillo", "Modulo de atencion central", 275, 0),
    ("anillo", "Sala de lectura", 90, 0),
    ("anexo", "SSHH", -0.45, -0.28),
    ("anexo", "Estante compacto / hemeroteca", 0.0, -0.28),
    ("anexo", "Sala Mac", 0.33, -0.28),
    ("anexo", "Fotocopias Ricoh", 0.55, -0.28),
], 6: [], 7: []}

# p6: cubiculos del anexo CUB-02..09 (u, dv)
CUB6_ANEXO = {2: (-0.2, -0.45), 7: (0.1, -0.45), 8: (0.45, -0.45), 3: (-0.2, -0.28),
              6: (0.1, -0.28), 9: (0.45, -0.28), 4: (-0.1, -0.12), 5: (0.12, -0.12)}
SALAS[6] = ([("anexo", "SSHH", -0.45, -0.28), ("anillo", "Modulo de atencion", 235, 0), ("centro", "CUB-35 (aprox)", 0, 0)]
            + [("anillo", f"CUB-{10 + k:02d}", (320 + 265 / 16 * k) % 360, 0) for k in range(17)]     # CUB-10..26
            + [("interior", f"CUB-{27 + k:02d} (aprox)", (255 - 45 * k) % 360, 0) for k in range(8)]  # CUB-27..34
            + [("anexo", f"CUB-{n:02d}", u, dv) for n, (u, dv) in CUB6_ANEXO.items()])
SALAS[7] = ([("anexo", "SSHH", -0.45, -0.28), ("anexo", "Terraza (abierta)", 0.2, -0.35),
             ("anillo", "Modulo de atencion", 262, 0)]
            + [("anillo", f"CUB-{37 + k:02d}", (285 + 300 / 12 * k) % 360, 0) for k in range(13)]     # CUB-37..49
            + [("interior", f"CUB-{50 + k:02d} (aprox)", (235 - 47 * k) % 360, 0) for k in range(7)]   # CUB-50..56
            + [("centro", "CUB-57/58 (aprox)", 0, 0)])


def _g(u, v):
    """Desplazamiento (u derecha, v abajo, en R, orientacion de la placa) -> pixel de plano.png (giro de -90 grados)."""
    return CX + v * R, CY - u * R


def _pol(ang_deg, frac):
    a = math.radians(ang_deg - 90)
    return CX + frac * R * math.cos(a), CY + frac * R * math.sin(a)


def _circulo(cx, cy, r, lados=40):
    return [(cx + r * math.cos(2 * math.pi * k / lados), cy + r * math.sin(2 * math.pi * k / lados)) for k in range(lados)]


# huella 3D en px: torre, extension oeste con la plataforma hacia K y lobulo de los ascensores
HUELLAS = [_circulo(CX, CY, R + 0.5), [(61, 560), (98, 560), (98, 681), (61, 681)], [(94, 672), (118, 672), (118, 692), (94, 692)]]


PISOS = 7


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
        usados = set()
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
            puertas.poner_sala(G, ancla, zid, etq, (x, y), z, piso, "I", puerta=not abierta)
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
