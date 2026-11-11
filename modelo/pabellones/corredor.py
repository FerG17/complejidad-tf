"""
Pabellones de pasillo B, C, D, E, F, G, H y J: constructor generico + datos de cada uno (placas de evacuacion/riesgos
fotografiadas por el equipo). El corredor se apoya en la huella real del edificio sobre plano.png (pixeles).
Nombres de salas tomados de las placas; "(aprox)" = numero/nombre no legible con certeza.

spec = dict(pisos, corredor=[(x,y)...] en px del plano, cerrado, prof, entradas=[(id_exterior, t)],
            ascensor=(t, id_exterior|None, offset_px)|None, escaleras=[(t, offset_px)],
            salas={piso: {"+": [nombres], "-": [nombres]}})
t = fraccion a lo largo del corredor; "+" = lado izquierdo del avance, "-" el otro; en anillos las salas van hacia afuera.
"""
import math

from modelo import puertas
from modelo.config import ALTO_PISO, BASE_Z, COSTO_ASCENSOR, COSTO_ESCALERA, ESCALA, ESPACIADO

ABIERTAS = ("Hall", "Terraza", "Ingreso", "Jardin", "Planta libre", "Ambiente")


def _muestrear(pts, cerrado):
    path = list(pts) + ([pts[0]] if cerrado else [])
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]
    total = sum(seg)
    n = max(int(math.ceil(total * ESCALA / ESPACIADO)), 4)
    ns = n if cerrado else n + 1
    out = []
    for k in range(ns):
        d = total * k / (ns - 1 if not cerrado else n)
        acc = 0.0
        for (a, b), L in zip(zip(path, path[1:]), seg):
            if d <= acc + L + 1e-9:
                f = (d - acc) / L if L else 0
                x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                out.append((x, y, -dy, dx))
                break
            acc += L
    return out


def construir(G, pab):
    sp = ESPEC[pab]
    base_z = BASE_Z[pab]
    pts = _muestrear(sp["corredor"], sp.get("cerrado", False))
    n = len(pts)
    cerrado = sp.get("cerrado", False)
    prof = sp.get("prof", 28)
    cx = sum(p[0] for p in sp["corredor"]) / len(sp["corredor"])
    cy = sum(p[1] for p in sp["corredor"]) / len(sp["corredor"])

    def normal(k, signo):
        x, y, nx, ny = pts[k]
        if cerrado:   # siempre hacia afuera del centroide
            if (x - cx) * nx + (y - cy) * ny < 0:
                nx, ny = -nx, -ny
            return nx, ny
        return nx * signo, ny * signo

    def k_de(t):
        return min(n - 1, max(0, int(round(t * (n - 1))))) if not cerrado else int(round(t * n)) % n

    anc, ids_por_piso = {}, {}
    for p in range(1, sp["pisos"] + 1):
        z = base_z + (p - 1) * ALTO_PISO
        pre = f"{pab}{p}_"
        ids = []
        for k, (x, y, _, _) in enumerate(pts):
            i = f"{pre}c{k:02d}"
            G.nodo(i, x, y, z, p, pab, "pasillo")
            ids.append(i)
        for a, b in zip(ids, ids[1:]):
            G.arista(a, b, "pasillo")
        if cerrado:
            G.arista(ids[-1], ids[0], "pasillo")
        ids_por_piso[p] = ids
        for s, (t, off) in enumerate(sp["escaleras"]):
            k = k_de(t)
            nx, ny = normal(k, 1 if off >= 0 else -1)
            i = f"{pre}esc{s + 1}"
            G.nodo(i, pts[k][0] + nx * abs(off), pts[k][1] + ny * abs(off), z, p, pab, "escalera", f"Escalera {s + 1}")
            G.arista(ids[k], i, "pasillo")
            anc[(p, f"esc{s + 1}")] = i
        if sp.get("ascensor"):
            t, _, off = sp["ascensor"]
            k = k_de(t)
            nx, ny = normal(k, 1 if off >= 0 else -1)
            i = f"{pre}asc"
            G.nodo(i, pts[k][0] + nx * abs(off), pts[k][1] + ny * abs(off), z, p, pab, "ascensor", f"Ascensor {pab}")
            G.arista(ids[k], i, "pasillo")
            anc[(p, "asc")] = i
        for lado, signo in (("+", 1), ("-", -1)):
            nombres = sp["salas"].get(p, {}).get(lado, [])
            for j, etq in enumerate(nombres):
                t = 0.06 + 0.88 * (j + 0.5) / len(nombres)
                k = k_de(t)
                nx, ny = normal(k, signo)
                zx, zy = pts[k][0] + nx * prof, pts[k][1] + ny * prof
                puertas.poner_sala(G, ids[k], f"{pre}r{'p' if signo > 0 else 'n'}{j:02d}", etq, (zx, zy), z, p, pab,
                                   puerta=not etq.startswith(ABIERTAS))
    for p in range(1, sp["pisos"]):
        for s in range(len(sp["escaleras"])):
            G.arista(anc[(p, f"esc{s + 1}")], anc[(p + 1, f"esc{s + 1}")], "escalera", acc=False, w=ALTO_PISO * COSTO_ESCALERA)
        if sp.get("ascensor"):
            G.arista(anc[(p, "asc")], anc[(p + 1, "asc")], "ascensor", acc=True, w=ALTO_PISO + COSTO_ASCENSOR)
    for ext, t in sp["entradas"]:
        k = k_de(t)
        a, b = G.nodos[ext], G.nodos[ids_por_piso[1][k]]
        pid = f"{pab}1_puerta_{ext}"
        G.nodo(pid, (a["x_px"] + b["x_px"]) / 2, (a["y_px"] + b["y_px"]) / 2, base_z, 1, pab, "puerta",
               f"Puerta de ingreso {pab} ({G.nodos[ext]['etiqueta'] or ext})", ancho_m=puertas.ANCHO_DEF, escalon=False)
        G.arista(ext, pid, "puerta")
        G.arista(pid, ids_por_piso[1][k], "puerta")
    if sp.get("ascensor") and sp["ascensor"][1]:
        G.arista(sp["ascensor"][1], anc[(1, "asc")], "puerta")
    return ids_por_piso


def _rango(pre, a, b, extra=""):
    return [f"{pre}{i}{extra}" for i in range(a, b + 1)]


def aulas(letra, piso, nums):
    return [f"Aula {letra}-{piso}{n}" for n in nums]


B = dict(pisos=5, corredor=[(337, 298), (337, 394)], prof=30, entradas=[("P34", 0.93)], ascensor=None,
         escaleras=[(0.04, -8), (0.5, -8), (0.96, -8)], salas={
    1: {"+": ["Aula B-10", "Aula B-11", "Aula B-12", "CICS", "Coordinacion de seguridad", "Objetos perdidos"],
        "-": ["Aula B-13", "Aula B-14", "Aula B-15", "Impresiones/fotocopiado", "Taller-almacen",
              "Centro de operaciones campus-soporte", "Almacen de topografia"]},
    2: {"+": ["Aula B-21", "Aula B-22", "SSHH", "Lactario", "Direccion de Inteligencia e Innovacion Digital"],
        "-": ["Aula B-25", "Aula B-26", "Asesor 1 (aprox)", "Asesor 2 (aprox)", "Almacen DIID"]},
    3: {"+": ["Aula B-31", "Aula B-32", "Aula B-33", "Aula B-34"], "-": ["Aula B-35", "Aula B-36", "SSHH mujeres", "SSHH hombres"]},
    4: {"+": ["Aula B-41", "Aula B-42", "Aula B-43", "SSHH (aprox)"], "-": ["Aula B-44", "Aula B-45"]},
    5: {"+": ["Aula B-51", "Aula B-52", "Aula B-53", "Terraza"], "-": ["Aula acustica de musica B-54", "Aula B-55"]},
})

C = dict(pisos=5, corredor=[(202, 298), (202, 428)], prof=32, entradas=[("P29", 0.58), ("P29w", 0.5)], ascensor=None,
         escaleras=[(0.04, 8), (0.5, 8), (0.96, 8)], salas={
    1: {"+": ["Almacen de quimica (C-10)", "Lab. de quimica C-11", "Aula C-12", "Aula C-13", "Capstone ing. industrial C-14"],
        "-": ["Aula C-15", "Aula C-16", "Aula C-17", "Almacen de fisica", "Aula C-18 (40)", "Aula C-19 (40)"]},
    2: {"+": ["Aula C-21 (40)", "Aula C-22 (40)", "Oficina", "Almacen marketing", "SSHH hombres"],
        "-": ["Aula C-26", "Aula C-27", "Aula C-28", "Aula C-29", "Almacen UAV", "SSHH damas"]},
    3: {"+": ["Aula C-31 (40)", "Aula C-32 (30)", "Aula C-33 (30)", "Aula C-34"], "-": ["Lab. computo C-35", "Lab. computo C-36", "Aula C-37 (40)", "Aula C-39 (40)"]},
    4: {"+": ["Lab. computo C-41", "Capstone ing. sistemas C-43", "Lab. computo C-44", "Sala de servidores"],
        "-": ["Lab. computo C-45", "Lab. computo C-48", "Lab. computo C-49", "Sala de practicantes", "SSHH damas", "SSHH hombres"]},
    5: {"+": ["Lab. procesamiento digital de imagenes", "Lab. sistemas embebidos", "Lab. bioquimica (aprox)"],
        "-": ["Aula C-57", "Aula C-59", "Lab. electronica (aprox)"]},
})

# D: p4 = p5 (plantilla tipica), solo p1 cambia
_D_TIP = lambda p: {"+": [f"Aula D-{p}1", f"Aula D-{p}2", f"Aula D-{p}3", f"Aula D-{p}4", f"Aula D-{p}5 (aprox)"],
                    "-": [f"Aula D-{p}6", f"Lab. computo D-{p}7", f"Aula D-{p}8", f"Lab. MAC D-{p}9", "SSHH varones", "SSHH damas"]}
D = dict(pisos=5, corredor=[(116, 298), (116, 448)], prof=28, entradas=[("P28", 0.86)], ascensor=(0.97, "A28", -9),
         escaleras=[(0.0, 8), (0.95, 8)], salas={
    1: {"+": ["Lab. MAC D-11 (20)", "Lab. MAC D-12 (20)", "Aula D-13 (25)", "Oficina creatividad empresarial"],
        "-": ["Aula D-14 (40)", "Aula D-15 (40)", "Lab. computo D-16", "Lab. computo D-17", "Lab. computo D-18", "Lab. computo D-19"]},
    2: {"+": ["Lab. MAC D-21 (20)", "Aula D-22 (40)", "Aula D-23 (40)", "Aula D-24 (40)", "Aula D-25 (40)", "Oficina creatividad empresarial"],
        "-": ["Aula D-26 (40)", "Lab. computo D-27", "Aula D-28 (40)", "Lab. MAC D-29 (20)", "SSHH DISCAP", "SSHH"]},
    3: {"+": ["Lab. MAC D-31", "Aula D-32", "Aula D-33", "Aula D-34", "Aula D-35"],
        "-": ["Aula D-36", "Lab. computo D-37", "Lab. MAC D-38", "Lab. MAC D-39", "SSHH DISCAP", "SSHH"]},
    4: _D_TIP(4), 5: _D_TIP(5),
})

_J_SS = ["SSHH varones", "SSHH mujeres"]
J = dict(pisos=5, corredor=[(230, 322), (298, 322)], prof=24, entradas=[("P31", 0.93)], ascensor=(1.0, "A32", -9),
         escaleras=[(0.0, 8), (0.86, 8)], salas={
    1: {"+": _J_SS + ["SSHH discapacitados", "Banco Interbank", "Oficina internacional", "Vida universitaria / oport. laborales"],
        "-": ["Oficinas Academicas (33)", "Of. jefe academico 01", "Of. jefe academico 02", "Sala de reuniones", "Prospeccion",
              "Servicios Universitarios (32)", "Cubiculo atencion al alumno", "Counter recepcion oficinas", "Ambiente disponible"]},
    2: {"+": _J_SS + ["Tutorias 1 (aprox)", "Tutorias 2 (aprox)"], "-": ["Oficina 1 (aprox)", "Oficina 2 (aprox)", "Oficina 3 (aprox)", "Oficina 4 (aprox)"]},
    3: {"+": _J_SS + ["Director ejecutivo", "Gerente de operaciones"], "-": ["Gobierno Campus", "Director", "Sala de reuniones (aprox)"]},
    4: {"+": _J_SS + ["PTC 1 (aprox)", "PTC 2 (aprox)"], "-": ["PTC 3 (aprox)", "PTC 4 (aprox)", "PTC 5 (aprox)"]},
    5: {"+": _J_SS + ["Asesoria riesgo", "Sala de reuniones"], "-": ["PTC 1 (aprox)", "PTC 2 (aprox)", "PTC 3 (aprox)"]},
})

def _E(p, lab=False):
    arriba = ([f"Aula E-{p}{n}" for n in (1, 2, 3, 4)] if not lab else ["Lab. multifuncional", "Lab. biologico", "Oficina (aprox)", "Lab. (aprox)"])
    return {"-": arriba, "+": ([f"Aula E-{p}{n}" for n in (5, 6, 7, 8)] if p != 1 else ["Taller 1 (aprox)", "Taller 2 (aprox)", "Lab. 1 (aprox)", "Lab. 2 (aprox)"]) + ["SSHH hombres", "SSHH mujeres"]}
E = dict(pisos=5, corredor=[(396, 648), (473, 648)], prof=34, entradas=[("P15", 0.0)], ascensor=(0.05, "A15", 10),
         escaleras=[(0.35, 8), (0.65, 8), (0.95, 8)], salas={1: _E(1), 2: _E(2), 3: _E(3, lab=True), 4: _E(4),
                                                              5: {"-": ["Lab. computo E-54", "Lab. computo E-53", "Aula E-52", "Aula E-51"],
                                                                  "+": ["Aula E-55", "Aula E-56", "Aula E-57", "Aula E-58", "SSHH hombres", "SSHH mujeres"]}})

# F: ala larga E-O
def _F(p):
    return {"-": [f"F-{p}1 (aprox)", f"F-{p}2 (aprox)", f"F-{p}3 (aprox)", f"F-{p}4 (aprox)"],
            "+": [f"F-{p}5 (aprox)", f"F-{p}6 (aprox)", f"F-{p}7 (aprox)", f"F-{p}8 (aprox)"]}
F = dict(pisos=5, corredor=[(480, 648), (606, 648)], prof=34, entradas=[], ascensor=None,
         escaleras=[(0.12, 8), (0.88, 8)], salas={p: _F(p) for p in range(1, 6)})

# G: ala NNE, con ascensor
def _G(p):
    return {"+": [f"Aula G-{p}1 (aprox)", f"Aula G-{p}2 (aprox)", "SSHH"], "-": [f"Aula G-{p}3 (aprox)", f"Aula G-{p}4 (aprox)"]}
G = dict(pisos=5, corredor=[(622, 630), (650, 540)], prof=22, entradas=[("P12", 0.08)], ascensor=(0.12, "A12", 8),
         escaleras=[(0.3, -8), (0.92, -8)], salas={p: _G(p) for p in range(1, 6)})

# H: anillo alrededor del vacio central
def _Hp(p, nombres):
    return {"+": nombres}
H = dict(pisos=5, corredor=[(612, 438), (722, 425), (708, 508), (612, 508)], cerrado=True, prof=26,
         entradas=[("P8b", 0.02)], ascensor=(0.58, None, -12), escaleras=[(0.12, 8), (0.62, 8), (0.92, 8)], salas={
    1: {"+": ["Ingreso principal", "Hall", "SSHH DISCAP 1", "SSHH DISCAP 2", "Cuarto de limpieza", "Ingreso de servicio",
              "Auditorio Bancalari (10)"]},
    2: {"+": [f"Aula H-2{n} (aprox)" for n in range(0, 8)]},
    3: {"+": [f"Aula H-3{n} (aprox)" for n in range(0, 8)]},
    4: {"+": ["Lab. software entretenimiento H-40", "Aula H-42", "Lab. computo H-43", "Aula H-44", "Aula H-45 (aprox)",
              "Taller de diseno H-46", "Aula H-47 (aprox)", "Sala de servidores", "SSHH hombres", "Oficina PTC"]},
    5: {"+": ["Lab. MAC H-50", "Lab. diseno de software H-51", "Lab. computo H-52", "Aula H-53", "Capstone ing. sistemas H-54",
              "Aula acustica comunicaciones H-55", "Lab. computo H-56", "Ambiente disponible H-57", "Lab. computo H-58",
              "Lab. fisica H-59", "Cuarto data y com"]},
})

ESPEC = {"B": B, "C": C, "D": D, "E": E, "F": F, "G": G, "H": H, "J": J}
