"""
Pabellon A (Aula Magna incluida), pisos 1-5, a partir de las placas EV-M-01 (dic 2020).
Estructura (placas con el norte arriba):
  * Ovalo OESTE = Aula Magna (103 alumnos, p1 y p3). p2 y p4: solo vacio. p5: GEA, set de fotografia (14),
    almacen de audiovisuales y maquillaje.
  * HALL ESCALERA (oeste del bloque central) con la escalera 1 semicircular.
  * Bloque central: 4 aulas (x1 SO, x2 SE, x3 NO, x4 NE) alrededor del cruce de la circulacion E-O.
  * Circulacion N-S en el lado este, con el bloque este (aulas x5/x6 o SSHH) y la escalera 2 (NE).
  * NO TIENE ASCENSOR: solo el piso 1 es accesible. Las escaleras no son accesibles.
Conversion placa->plano campus: (205 + (px-120)*0.154, 618 + (py-565)*0.154) (calibrada con P16 y P18 del plano oficial).
"""
import math

import puertas

K = 0.154


def cp(px, py):
    return 205 + (px - 120) * K, 618 + (py - 565) * K


# (id corto, etiqueta, (x,y) sala en placa, (x,y) puerta en placa, donde engancha: ("ew"|"ns"|"hall", coordenada))
def _aulas(p):
    c = lambda n: f"Aula A-{p}{n}"
    base = [
        ("1", c(1), (670, 710), (755, 645), ("ew", 755)),
        ("2", c(2), (910, 710), (825, 645), ("ew", 825)),
        ("3", c(3), (670, 470), (755, 525), ("ew", 755)),
        ("4", c(4), (910, 470), (825, 525), ("ew", 825)),
    ]
    este = {
        1: [("5", "Aula A-15", (1200, 470), (1098, 500), ("ns", 500)), ("6", "Aula A-16", (1200, 700), (1098, 700), ("ns", 700))],
        2: [("5", "Aula A-25", (1200, 480), (1098, 500), ("ns", 500)),
            ("SD", "SSHH damas", (1215, 675), (1098, 670), ("ns", 670)), ("SV", "SSHH varones", (1215, 750), (1098, 745), ("ns", 745))],
        3: [("6", "Aula A-36", (1200, 500), (1098, 520), ("ns", 520)), ("5", "Aula A-35", (1200, 740), (1098, 720), ("ns", 720))],
        4: [("6", "Aula A-46 (25)", (1200, 505), (1098, 510), ("ns", 510)), ("5", "Aula A-45 (25)", (1200, 690), (1098, 690), ("ns", 690)),
            ("SV", "SSHH varones", (1215, 795), (1098, 790), ("ns", 790)), ("SD", "SSHH damas", (1215, 850), (1098, 840), ("ns", 840))],
        5: [("6", "Aula A-56", (1200, 520), (1098, 520), ("ns", 520)), ("5", "Aula A-55 (30)", (1200, 740), (1098, 720), ("ns", 720))],
    }[p]
    return base + este


OVALO = {
    1: [("AM", "Aula Magna (103)", (290, 570), (425, 585))],
    3: [("AM", "Aula Magna (103) - nivel superior", (290, 600), (425, 600))],
    5: [("GEA", "GEA", (290, 470), (430, 540)), ("SET", "Set de fotografia (14)", (290, 640), (430, 600)),
        ("AUD", "Almacen de audiovisuales", (240, 780), (430, 700)), ("MAQ", "Maquillaje", (340, 790), (430, 740))],
}


def construir(G, sp, alto_piso, base_z, espaciado, escala, costo_esc, costo_asc):
    m_por_placa = K * escala     # metros por pixel de placa
    n_ew = int(math.ceil((1062 - 470) * m_por_placa / espaciado)) + 1
    n_n = int(math.ceil((585 - 340) * m_por_placa / espaciado))
    n_s = int(math.ceil((830 - 585) * m_por_placa / espaciado))
    ew_x = [470 + (1062 - 470) * k / (n_ew - 1) for k in range(n_ew)]
    ns_n = [585 - (585 - 340) * (j + 1) / n_n for j in range(n_n)]      # hacia el norte
    ns_s = [585 + (830 - 585) * (j + 1) / n_s for j in range(n_s)]      # hacia el sur

    anc = {}
    for p in range(1, sp["pisos"] + 1):
        z = base_z + (p - 1) * alto_piso
        pre = f"A{p}_"
        ew = []
        for k, x in enumerate(ew_x):
            i = f"{pre}e{k:02d}"
            G.nodo(i, *cp(x, 585), z, p, "A", "pasillo", "Hall escalera" if k == 0 else "")
            ew.append(i)
        for a, b in zip(ew, ew[1:]):
            G.arista(a, b, "pasillo")
        junta = ew[-1]
        ns_ids = {}
        prev = junta
        for j, y in enumerate(ns_n):
            i = f"{pre}n{j:02d}"
            G.nodo(i, *cp(1062, y), z, p, "A", "pasillo")
            G.arista(prev, i, "pasillo")
            prev = i
            ns_ids[y] = i
        ns_ids[585] = junta
        prev = junta
        for j, y in enumerate(ns_s):
            i = f"{pre}s{j:02d}"
            G.nodo(i, *cp(1062, y), z, p, "A", "pasillo")
            G.arista(prev, i, "pasillo")
            prev = i
            ns_ids[y] = i
        ys = sorted(ns_ids)

        def ancla(donde):
            tipo, c = donde
            if tipo == "ew":
                return ew[min(range(n_ew), key=lambda k: abs(ew_x[k] - c))]
            return ns_ids[min(ys, key=lambda y: abs(y - c))]

        # escaleras
        G.nodo(f"{pre}esc1", *cp(490, 700), z, p, "A", "escalera", "Escalera 1")
        G.arista(ew[0], f"{pre}esc1", "pasillo")
        G.nodo(f"{pre}esc2", *cp(1160, 345), z, p, "A", "escalera", "Escalera 2")
        G.arista(ns_ids[min(ys)], f"{pre}esc2", "pasillo")
        anc[(p, 1)] = f"{pre}esc1"
        anc[(p, 2)] = f"{pre}esc2"
        # salas con puerta
        for n, etq, sala, pu, donde in _aulas(p):
            puertas.poner_sala(G, ancla(donde), f"{pre}{n}", etq, cp(*sala), z, p, "A", puerta_xy=cp(*pu))
        for n, etq, sala, pu in OVALO.get(p, []):
            puertas.poner_sala(G, ew[0], f"{pre}{n}", etq, cp(*sala), z, p, "A", puerta_xy=cp(*pu))
    for p in range(1, sp["pisos"]):
        for s in (1, 2):
            G.arista(anc[(p, s)], anc[(p + 1, s)], "escalera", acc=False, w=alto_piso * costo_esc)
    # --- entradas desde el exterior (piso 1)
    def con_puerta(ext, ancla_id, etq, nota):
        a, b = G.nodos[ext], G.nodos[ancla_id]
        pid = f"A1_puerta_{ext}"
        G.nodo(pid, (a["x_px"] + b["x_px"]) / 2, (a["y_px"] + b["y_px"]) / 2, 0.0, 1, "A", "puerta", etq,
               ancho_m=puertas.ANCHO_DEF, escalon=False)
        G.arista(ext, pid, "puerta", nota=nota)
        G.arista(pid, ancla_id, "puerta", nota=nota)
    p1 = {n["id"]: n for n in G.piso_nodos("A", 1)}
    centro_ew = f"A1_e{min(range(n_ew), key=lambda k: abs(ew_x[k] - 790)):02d}"
    con_puerta("P16", centro_ew, "Puerta P16 (hall A)", "supuesto: P16 entra al cruce de circulacion")
    con_puerta("P18", "A1_e00", "Puerta P18 (Aula Magna / hall)", "supuesto: P18 entra al hall escalera")
    sur = f"A1_s{n_s - 1:02d}"
    con_puerta("V_E2", sur, "Salida sur circulacion N-S", "supuesto: V_E2 = salida sur de la circulacion N-S")
