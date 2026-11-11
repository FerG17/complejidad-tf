"""
Pabellones K y L: constructor y datos de ambos. Pasillos y ramales son poligonales en pixeles de plano.png; las salas,
escaleras y ascensores se colocaron a mano a partir de las placas de evacuacion y mapa de riesgos.

K: pisos 1, 2, 3 y 5 leidos de las placas; el piso 4 repite el 3. Sin ascensor: se llega en silla de ruedas por
P26/P27 (piso 1) y por la plataforma plana que lo une con la Biblioteca en los pisos 1 a 5.
L: pisos 1 y 2 leidos; los pisos 3 a 5 repiten el 2. Dos ascensores propios, tres escaleras, ingresos P4/P3 y el
ascensor exterior A4. El subsuelo no se modela.
Los recintos "(aprox)" no tienen rotulo legible (nombre y posicion estimados); precision geometrica ~2-3 m.
"""
import math

from modelo import puertas
from modelo.config import ALTO_PISO, BASE_Z, COSTO_ASCENSOR, COSTO_ESCALERA, ESCALA, ESPACIADO

def _muestrear(pts):
    """Puntos equiespaciados (~ESPACIADO m) sobre la poligonal `pts` (px). Incluye los extremos."""
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    n = max(int(math.ceil(total * ESCALA / ESPACIADO)), 1)
    out = []
    for k in range(n + 1):
        d = total * k / n
        acc = 0.0
        for (a, b), L in zip(zip(pts, pts[1:]), seg):
            if d <= acc + L + 1e-9:
                f = (d - acc) / L if L else 0.0
                out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                break
            acc += L
    return out


def _cercano(G, ids, xy):
    return min(ids, key=lambda i: math.hypot(G.nodos[i]["x_px"] - xy[0], G.nodos[i]["y_px"] - xy[1]))


def _planta(G, pab, piso, z, plt, escaleras, ascensores, salas, entradas):
    """Construye un piso: pasillo + ramales + escaleras + ascensores + salas + ingresos. Devuelve (ancla_esc, ancla_asc)."""
    pre = f"{pab}{piso}_"
    ids_pas = []
    for k, (x, y) in enumerate(_muestrear(plt["pasillo"])):
        i = f"{pre}c{k:02d}"
        G.nodo(i, x, y, z, piso, pab, "pasillo")
        if ids_pas:
            G.arista(ids_pas[-1], i, "pasillo")
        ids_pas.append(i)
    ids_ram = {"pasillo": ids_pas}
    for nom, pts in plt["ramales"].items():
        ids = []
        for k, (x, y) in enumerate(_muestrear(pts)):
            i = f"{pre}{nom[:3]}{k:02d}"
            G.nodo(i, x, y, z, piso, pab, "pasillo")
            if ids:
                G.arista(ids[-1], i, "pasillo")
            ids.append(i)
        # el ramal nace de un punto del pasillo
        G.arista(_cercano(G, ids_pas, pts[0]), ids[0], "pasillo")
        ids_ram[nom] = ids
    todos = [i for v in ids_ram.values() for i in v]

    anc_esc, anc_asc = {}, {}
    for s, nom, xy in escaleras:          # s = numero fijo de la escalera (id ..._esc{s})
        i = f"{pre}esc{s}"
        G.nodo(i, xy[0], xy[1], z, piso, pab, "escalera", f"Escalera {nom}")
        G.arista(_cercano(G, todos, xy), i, "pasillo")
        anc_esc[s] = i
    for nom, xy in ascensores:
        i = f"{pre}{nom}"
        G.nodo(i, xy[0], xy[1], z, piso, pab, "ascensor", f"Ascensor {nom[-1]} ({pab})")
        G.arista(_cercano(G, todos, xy), i, "pasillo")
        anc_asc[nom] = i
    for j, (etq, xy, con_puerta, ramal) in enumerate(salas):
        ancla = _cercano(G, ids_ram.get(ramal, ids_pas), xy)
        puertas.poner_sala(G, ancla, f"{pre}rp{j:02d}", etq, xy, z, piso, pab, puerta=con_puerta)
    for ext, xy in entradas:
        pid = f"{pab}1_puerta_{ext}"
        a = G.nodos[ext]
        G.nodo(pid, xy[0], xy[1], z, piso, pab, "puerta", f"Puerta de ingreso {pab} ({a['etiqueta'] or ext})",
               ancho_m=puertas.ANCHO_DEF, escalon=False)
        G.arista(ext, pid, "puerta")
        G.arista(pid, _cercano(G, todos, xy), "puerta")
    return anc_esc, anc_asc


def construir_k(G):
    base_z = BASE_Z["K"]
    nombre = {"N": "Norte", "NE": "Noreste", "S": "Sur"}
    esc = [(s, n, d["xy"], d["pisos"]) for s, (n, d) in enumerate(DATOS_K["escaleras"].items(), 1)]
    anc = {}
    for piso in range(1, DATOS_K["pisos"] + 1):
        plt = DATOS_K["plantillas"][DATOS_K["piso_plantilla"][piso]]     # piso 4 usa la plantilla del piso 3
        z = base_z + (piso - 1) * ALTO_PISO
        e_piso = [(s, nombre[n], xy) for s, n, xy, ps in esc if piso in ps]
        ae, _ = _planta(G, "K", piso, z, plt, e_piso, [], plt["salas"],
                        plt["entradas"] if piso == 1 else [])
        for s, i in ae.items():
            anc[(piso, s)] = i
    for piso in range(1, DATOS_K["pisos"]):
        for s, n, xy, ps in esc:
            if piso in ps and piso + 1 in ps:
                G.arista(anc[(piso, s)], anc[(piso + 1, s)], "escalera", acc=False, w=ALTO_PISO * COSTO_ESCALERA)
    # K y la Biblioteca se unen en los pisos 1 a 5 por una plataforma plana junto a la escalera de emergencia
    for piso in range(1, DATOS_K["pisos"] + 1):
        k0, i0 = f"K{piso}_c00", f"I{piso}_a04"
        A, B = G.nodos[k0], G.nodos[i0]
        pid = f"K{piso}_puerta_I"
        G.nodo(pid, (A["x_px"] + B["x_px"]) / 2, (A["y_px"] + B["y_px"]) / 2, A["z"], piso, "K", "puerta",
               "Puerta de paso Biblioteca (I) - K", ancho_m=puertas.ANCHO_DEF, escalon=False)
        nota = "K se une al anexo norte de la Biblioteca en los pisos 1 a 5 (indicado por el equipo)"
        G.arista(i0, pid, "pasaje", nota=nota)
        G.arista(pid, k0, "pasaje", nota=nota)


def construir_l(G):
    base_z = BASE_Z["L"]
    nombre = {"O": "Oeste", "C": "Central", "E": "Este"}
    esc = [(s, nombre[n], xy) for s, (n, xy) in enumerate(DATOS_L["escaleras"].items(), 1)]
    asc = list(DATOS_L["ascensores"].items())          # [("asc1", xy), ("asc2", xy)]
    plt = dict(pasillo=DATOS_L["pasillo"], ramales=DATOS_L["ramales"])
    anc_e, anc_a = {}, {}
    for piso in range(1, DATOS_L["pisos"] + 1):
        z = base_z + (piso - 1) * ALTO_PISO
        salas = DATOS_L["salas_p1"] if piso == 1 else DATOS_L["salas_up"]
        ae, aa = _planta(G, "L", piso, z, plt, esc, asc, salas, DATOS_L["entradas_p1"] if piso == 1 else [])
        anc_e[piso], anc_a[piso] = ae, aa
    for piso in range(1, DATOS_L["pisos"]):
        for s in anc_e[piso]:
            G.arista(anc_e[piso][s], anc_e[piso + 1][s], "escalera", acc=False, w=ALTO_PISO * COSTO_ESCALERA)
        for nom in anc_a[piso]:
            G.arista(anc_a[piso][nom], anc_a[piso + 1][nom], "ascensor", acc=True, w=ALTO_PISO + COSTO_ASCENSOR)
    for nom in anc_a[1]:     # ascensor exterior A4 (plano oficial) <-> ascensores de L en el piso 1
        G.arista("A4", anc_a[1][nom], "puerta")


DATOS_K = {'escaleras': {'N': {'pisos': (1, 2, 3, 4, 5), 'xy': (102, 469)},
                         'NE': {'pisos': (1, 2, 3, 4), 'xy': (133, 483)},
                         'S': {'pisos': (1, 2, 3, 4, 5), 'xy': (77, 557)}},
           'piso_plantilla': {1: 'p1', 2: 'p2', 3: 'p3', 4: 'p3', 5: 'p5'},
           'pisos': 5,
           'plantillas': {'p1': {'entradas': [('P27', (100.6, 518.4)), ('P26', (125.4, 514.0))],
                                 'pasillo': [(75.9, 551.9), (78.8, 538.0), (82.4, 524.9), (87.5, 511.8), (93.3, 500.2),
                                             (100.6, 492.2), (110.8, 485.6), (121.0, 486.3)],
                                 'ramales': {'hall': [(87.5, 511.8), (97.7, 515.0), (109.3, 516.9), (119.5, 513.3),
                                                      (123.9, 510.4)],
                                             'norte': [(100.6, 492.2), (101.5, 481.2), (102.1, 471.0)]},
                                 'salas': [('Hall principal (26)', (115.2, 511.8), False, 'hall'),
                                           ('Cocina-almacen (aprox)', (68.6, 465.2), True, 'norte')]},
                          'p2': {'entradas': [],
                                 'pasillo': [(76.8, 547.3), (80.6, 540.6), (83.5, 533.8), (85.7, 524.0), (89.5, 508.9),
                                             (92.4, 500.0), (95.0, 492.0), (97.3, 482.6), (98.4, 475.8)],
                                 'ramales': {'cocina': [(97.3, 482.3), (87.6, 479.5), (78.1, 476.5), (67.6, 473.4),
                                                        (67.3, 465.0)],
                                             'comedor': [(92.4, 500.0), (82.2, 499.4), (71.4, 497.1)],
                                             'ne': [(97.3, 482.3), (109.2, 484.6), (120.0, 485.5), (128.0, 482.6)]},
                                 'salas': [('Cocina concesionario', (72.7, 457.6), True, 'cocina'),
                                           ('Almacen', (90.9, 469.7), True, 'pasillo'),
                                           ('Comedor 49 sillas', (71.4, 497.4), False, 'comedor'),
                                           ('Terraza 24 sillas', (101.3, 485.9), False, 'ne')]},
                          'p3': {'entradas': [],
                                 'pasillo': [(80.4, 555.2), (83.9, 544.7), (84.9, 530.6), (87.4, 516.6), (90.9, 502.5),
                                             (94.2, 488.5), (96.6, 478.6)],
                                 'ramales': {'ne': [(94.2, 488.5), (105.7, 488.5), (117.0, 485.9), (131.0, 482.8)],
                                             'norte': [(96.6, 478.6), (90.2, 471.6), (83.2, 464.6)]},
                                 'salas': [('SSHH hombres', (67.7, 530.6), True, 'pasillo'),
                                           ('SSHH mujeres', (67.7, 544.7), True, 'pasillo'),
                                           ('Hall', (88.8, 541.9), False, 'pasillo'),
                                           ('Comedor', (86.3, 501.1), False, 'pasillo'),
                                           ('Terraza', (100.4, 507.3), False, 'pasillo'),
                                           ('Ambiente norte (aprox)', (73.4, 454.7), True, 'norte')]},
                          'p5': {'entradas': [],
                                 'pasillo': [(84.1, 551.7), (87.1, 539.2), (87.9, 514.2), (87.5, 489.2), (87.5, 471.6),
                                             (87.5, 462.3)],
                                 'ramales': {},
                                 'salas': [('Sala de reuniones (aprox)', (70.6, 452.9), True, 'pasillo'),
                                           ('Oficina abierta (aprox)', (73.1, 489.2), False, 'pasillo'),
                                           ('SSHH hombres', (71.9, 530.4), True, 'pasillo'),
                                           ('SSHH mujeres', (71.9, 544.8), True, 'pasillo'),
                                           ('Hall', (87.5, 537.9), False, 'pasillo')]}}}

DATOS_L = {'ascensores': {'asc1': (598.9, 336.7), 'asc2': (597.6, 346.1)},
           'entradas_p1': [('P4', (610, 353)), ('P3', (694, 353))],
           'escaleras': {'C': (614.4, 315.6), 'E': (738.1, 302.9), 'O': (507.8, 301.0)},
           'pasillo': [(510.8, 308.5), (512.6, 313.8), (517.7, 320.5), (525.4, 326.9), (532.7, 328.3), (563.2, 328.2),
                       (590.7, 327.5), (603.1, 325.1), (615.1, 323.9), (625.9, 323.2), (658.2, 323.1), (694.2, 323.0),
                       (725.7, 322.1), (737.9, 314.5)],
           'pisos': 5,
           'ramales': {'cuna': [(512.6, 313.8), (496.5, 314.3), (484.5, 313.2)],
                       'nucleo': [(608.5, 324.8), (609.5, 313.8)],
                       'vestibulo': [(608.5, 324.8), (608.0, 333.6), (606.8, 342.0)]},
           'salas_p1': [('Informes y Admision (1)', (498.5, 324.0), False, 'cuna'),
                        ('Hall principal (4)', (616.0, 335.6), False, 'vestibulo'),
                        ('Cafeteria (3)', (680.9, 325.8), False, 'pasillo'), ('SSHH (aprox)', (601.4, 299.8), True, 'nucleo'),
                        ('SSHH discapacitados (aprox)', (612.5, 305.0), True, 'nucleo')],
           'salas_up': [('Sala triangular oeste (aprox)', (475.3, 312.8), True, 'cuna'),
                        ('Ambiente oeste (aprox)', (561.0, 304.6), False, 'pasillo'),
                        ('SSHH (aprox)', (601.4, 299.8), True, 'nucleo'),
                        ('SSHH discapacitados (aprox)', (612.5, 305.0), True, 'nucleo'),
                        ('Ambiente este (aprox)', (680.2, 304.7), False, 'pasillo')]}
