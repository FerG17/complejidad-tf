"""
Pabellones K y L: constructor y datos de ambos. Pasillos y ramales son poligonales en pixeles de plano.png; las salas,
escaleras y ascensores se colocaron a mano a partir de las placas de evacuacion y mapa de riesgos.

K: pisos 1, 2, 3 y 5 leidos de las placas; el piso 4 repite el 3. Sin ascensor: se llega en silla de ruedas por
P26/P27 (piso 1) y por la plataforma plana que lo une con la Biblioteca en los pisos 1 a 5.
L: pisos 1 y 2 leidos; los pisos 3 a 5 repiten el 2. Dos ascensores propios, tres escaleras, ingresos P4/P3 y el
ascensor exterior A4. El subsuelo no se modela.
Los recintos sin rotulo legible tienen nombre y posicion estimados; precision geometrica ~2-3 m. Datos en datos/pabellones/K.json y L.json.
"""
import math

from modelo import puertas
from modelo.pabellones import biblioteca, datos
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
    # K y la Biblioteca se unen en los pisos 1 a 5 por una plataforma plana junto a la escalera de emergencia (extremo norte del anexo)
    for piso in range(1, DATOS_K["pisos"] + 1):
        k0, i0 = f"K{piso}_c00", f"I{piso}_{biblioteca.NODO_ENLACE_K}"
        A, B = G.nodos[k0], G.nodos[i0]
        pid = f"K{piso}_puerta_I"
        G.nodo(pid, (A["x_px"] + B["x_px"]) / 2, (A["y_px"] + B["y_px"]) / 2, A["z"], piso, "K", "puerta",
               "Puerta de paso Biblioteca (I) - K", ancho_m=puertas.ANCHO_DEF, escalon=False)
        nota = "K se une a la extension de la Biblioteca en los pisos 1 a 5 (indicado por el equipo)"
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


_NO_DATOS = ("pabellon", "nota", "huellas")
_K, _L = datos.crudo("K"), datos.crudo("L")
HUELLAS = {"K": _K["huellas"], "L": _L["huellas"]}   # huellas 3D (px de plano.png): contorno gris de cada edificio en el plano
DATOS_K = {k: v for k, v in _K.items() if k not in _NO_DATOS}
DATOS_K["piso_plantilla"] = {int(k): v for k, v in DATOS_K["piso_plantilla"].items()}   # piso 4 usa la plantilla del piso 3
DATOS_L = {k: v for k, v in _L.items() if k not in _NO_DATOS}
