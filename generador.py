"""
Generador del grafo 3D del Campus Monterrico (UPC) - Equipo 10, 1ACC0184.

Une el grafo exterior (exterior.py) con los pabellones por piso (pabellon_lineal, pabellon_a, biblioteca) y los
conecta con pasajes. Devuelve un Grafo en memoria y, como script, exporta datos/nodos.csv y datos/aristas.csv.

Supuestos (las aristas supuestas llevan nota en aristas.csv):
  * ESCALA 0.275 m/px: calibrada contra Google Maps y la medicion Primavera-Alonso de Molina (131.85 m), error ~7 m.
  * BASE_Z = 0 en todos los pabellones (el campus tiene pendiente).
  * Pasillos J-B, C-D y E-F-G a nivel y accesibles en todos los pisos; E-A solo por escaleras.
  * Pabellones K y L no incluidos todavia.
"""
import csv
import math
from pathlib import Path

import biblioteca
import pabellon_a
import pabellon_lineal
import pabellones_datos
import exterior

ESCALA = 0.275       # metros por pixel del plano
ALTO_PISO = 3.5      # metros entre pisos
ESPACIADO = 1.5      # metros entre nodos consecutivos de un pasillo
COSTO_ESCALERA = 3.0 # una escalera cuesta 3x el desnivel (esfuerzo)
COSTO_ASCENSOR = 8.0 # penalizacion fija por esperar/usar el ascensor (en metros equivalentes)

BASE_Z = {p: 0.0 for p in "ABCDEFGHIJ"}

PAB = {
    "A": dict(nombre="Pabellon A (16/17/18) + Aula Magna", pisos=5, tipo="detallado", modulo="A"),
    "B": dict(nombre="Pabellon B (34)", pisos=5, tipo="detallado", modulo="L"),
    "C": dict(nombre="Pabellon C (29)", pisos=5, tipo="detallado", modulo="L"),
    "D": dict(nombre="Pabellon D (28)", pisos=5, tipo="detallado", modulo="L"),
    "E": dict(nombre="Pabellon E (15)", pisos=5, tipo="detallado", modulo="L"),
    "F": dict(nombre="Pabellon F (14)", pisos=5, tipo="detallado", modulo="L"),
    "G": dict(nombre="Pabellon G (12/13)", pisos=5, tipo="detallado", modulo="L"),
    "H": dict(nombre="Pabellon H (8/9/10)", pisos=5, tipo="detallado", modulo="L"),
    "I": dict(nombre="Pabellon I - Biblioteca (23/24/25)", pisos=7, tipo="detallado", modulo="I"),
    "J": dict(nombre="Pabellon J (30-33)", pisos=5, tipo="detallado", modulo="L"),
}

# Pasillos entre pabellones (por piso): (pab1, t1, pab2, t2, nota)
PASAJES = [
    ("J", 1.0, "B", 0.0, "supuesto: pasillo J-B a nivel en todos los pisos (indicado por el equipo)"),
    ("E", 1.0, "F", 0.0, "supuesto: E-F continuo en todos los pisos"),
    ("F", 1.0, "G", 0.0, "supuesto: F-G continuo (un solo pasillo con su escalera)"),
    ("D", 0.16, "C", 0.185, "confirmado por el equipo: plataforma plana C-D en los pisos 1 a 5 (en el hueco entre ambos "
                            "hay escaleras); posicion aproximada en el extremo norte"),
]

ZONAS = []   # las salas de cada pabellon viven en pabellones_datos.py / pabellon_a.py / biblioteca.py
# Zonas exteriores: (id, etiqueta, nodo exterior al que se cuelgan, dx, dy en px)
ZONAS_EXT = [
    ("Z_KATA", "Restaurant Kata (G)", "X4", 14, -22),
    ("Z_GALERIA", "Galeria (19)", "L3", 0, -20),
]


def _nombre(n):
    """Nombre legible y buscable de cada nodo (ej. 'I p7 - CUB-54 (aprox)', 'Ascensor 1 (I) p3')."""
    t, e, p, pis = n["tipo"], n["etiqueta"], n["pab"], n["piso"]
    if not p:
        if t == "interseccion":
            return f"Cruce exterior {n['id']}"
        if t == "ascensor":
            return e or n["id"]
        if t in ("entrada_accesible", "rampa"):
            return f"{t.replace('_', ' ').capitalize()} {e}".strip()
        return e or n["id"]
    if t == "zona":
        return f"{p} p{pis} - {e}"
    if t == "ascensor":
        return f"{e or 'Ascensor'} p{pis}"
    if t == "escalera":
        return f"{e or 'Escalera'} {p} p{pis}"
    if t == "puerta":
        return f"{e} ({p} p{pis})"
    return f"Pasillo {p} p{pis} {n['id'].split('_', 1)[-1]}"


class Grafo:
    def __init__(self):
        self.nodos = {}      # id -> dict
        self.aristas = []    # dict(a,b,w,tipo,acc,nota)
        self._adj = None

    def nodo(self, i, xpx, ypx, z, piso, pab, tipo, etiqueta="", **extra):
        assert i not in self.nodos, f"nodo duplicado {i}"
        self.nodos[i] = dict(id=i, x_px=xpx, y_px=ypx, x=xpx * ESCALA, y=ypx * ESCALA, z=z,
                             piso=piso, pab=pab, tipo=tipo, etiqueta=etiqueta, **extra)
        self.nodos[i]["nombre"] = _nombre(self.nodos[i])

    def d3(self, a, b):
        A, B = self.nodos[a], self.nodos[b]
        return math.sqrt((A["x"] - B["x"]) ** 2 + (A["y"] - B["y"]) ** 2 + (A["z"] - B["z"]) ** 2)

    def arista(self, a, b, tipo, acc=True, w=None, nota=""):
        if w is None:
            w = max(self.d3(a, b), 0.5)
        self.aristas.append(dict(a=a, b=b, w=w, tipo=tipo, acc=acc, nota=nota))

    @property
    def adj(self):
        if self._adj is None:
            self._adj = {i: [] for i in self.nodos}
            for e in self.aristas:
                self._adj[e["a"]].append((e["b"], e["w"], e["tipo"], e["acc"]))
                self._adj[e["b"]].append((e["a"], e["w"], e["tipo"], e["acc"]))
        return self._adj

    def validar(self):
        for e in self.aristas:
            assert e["a"] in self.nodos and e["b"] in self.nodos, f"arista con nodo inexistente {e}"
            assert e["w"] + 1e-6 >= self.d3(e["a"], e["b"]), f"peso < distancia 3D (heuristica no admisible) {e}"

    def piso_nodos(self, pab, piso):
        return [n for n in self.nodos.values() if n["pab"] == pab and n["piso"] == piso]

    def resumen(self):
        por_pab = {}
        for n in self.nodos.values():
            por_pab[n["pab"] or "ext"] = por_pab.get(n["pab"] or "ext", 0) + 1
        return por_pab


def _recta(spec, espaciado):
    (x0, y0), (x1, y1) = spec["p0"], spec["p1"]
    largo_m = math.hypot(x1 - x0, y1 - y0) * ESCALA
    n = max(int(math.ceil(largo_m / espaciado)) + 1, 4)
    pts = [(x0 + (x1 - x0) * k / (n - 1), y0 + (y1 - y0) * k / (n - 1)) for k in range(n)]
    dx, dy = (x1 - x0), (y1 - y0)
    L = math.hypot(dx, dy) or 1
    normal = (-dy / L, dx / L)
    return pts, [normal] * n, False


def _anillo(spec, espaciado):
    cx, cy = spec["c"]
    r = spec["r"]
    n = max(int(round(2 * math.pi * r * ESCALA / espaciado)), 8)
    n += (-n) % 4  # multiplo de 4 para los radios
    pts, normales = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        normales.append((math.cos(a), math.sin(a)))
    return pts, normales, True


def construir(espaciado=ESPACIADO):
    G = Grafo()

    # 1) exterior
    for i, (x, y, tipo, etq) in exterior.N.items():
        G.nodo(i, x, y, 0.0, 0, "", tipo, etq)
    ext_ids = set(exterior.N)
    for a, b in exterior.E:
        tipo = "rampa" if "rampa" in (G.nodos[a]["tipo"], G.nodos[b]["tipo"]) else "peatonal"
        G.arista(a, b, tipo)
    # E <-> A: solo escaleras (no accesible), con penalizacion
    G.arista("V_E2", "SV3", "escalera_ext", acc=False, w=G.d3("V_E2", "SV3") * 1.5,
             nota="E-A solo por escaleras/desnivel (confirmado por el equipo): NO accesible")

    # 2) cascarones
    idx = {}   # (pab, piso) -> lista de ids del pasillo
    ancla = {} # (pab, piso, tipo, k) -> id
    for p, sp in PAB.items():
        if sp["tipo"] == "detallado":
            if sp["modulo"] == "L":
                spec = pabellones_datos.ESPEC[p]
                sp["pisos"] = spec["pisos"]
                for piso, ids in pabellon_lineal.construir(G, spec, ALTO_PISO, BASE_Z[p], espaciado, ESCALA,
                                                           COSTO_ESCALERA, COSTO_ASCENSOR, p).items():
                    idx[(p, piso)] = ids
            else:
                {"A": pabellon_a, "I": biblioteca}[sp["modulo"]].construir(G, sp, ALTO_PISO, BASE_Z[p], espaciado, ESCALA, COSTO_ESCALERA, COSTO_ASCENSOR)
            continue
        pts, normales, cerrado = (_recta if sp["tipo"] == "recta" else _anillo)(sp, espaciado)
        n = len(pts)
        for piso in range(1, sp["pisos"] + 1):
            z = BASE_Z[p] + (piso - 1) * ALTO_PISO
            ids = []
            for k, (x, y) in enumerate(pts):
                i = f"{p}{piso}_c{k:02d}"
                G.nodo(i, x, y, z, piso, p, "pasillo")
                ids.append(i)
            for k in range(n - 1):
                G.arista(ids[k], ids[k + 1], "pasillo")
            if cerrado:
                G.arista(ids[-1], ids[0], "pasillo")
                c = sp["c"]
                cid = f"{p}{piso}_centro"
                G.nodo(cid, c[0], c[1], z, piso, p, "pasillo", "nucleo")
                for q in range(4):
                    G.arista(cid, ids[q * n // 4], "pasillo")
            idx[(p, piso)] = ids

            def pos(t):
                return (round(t * n) % n) if cerrado else int(round(t * (n - 1)))

            for s, t in enumerate(sp["escaleras"]):
                k = pos(t)
                x, y = pts[k]
                nx, ny = normales[k]
                i = f"{p}{piso}_esc{s + 1}"
                G.nodo(i, x + 7 * nx, y + 7 * ny, z, piso, p, "escalera", f"Escalera {s + 1}")
                G.arista(ids[k], i, "pasillo")
                ancla[(p, piso, "esc", s)] = i
            if sp["ascensor"]:
                t, ext = sp["ascensor"]
                k = pos(t)
                x, y = pts[k]
                nx, ny = normales[k]
                i = f"{p}{piso}_asc"
                G.nodo(i, x - 7 * nx, y - 7 * ny, z, piso, p, "ascensor", f"Ascensor {p}")
                G.arista(ids[k], i, "pasillo")
                ancla[(p, piso, "asc", 0)] = i
        for piso in range(1, sp["pisos"]):
            for s in range(len(sp["escaleras"])):
                a, b = ancla[(p, piso, "esc", s)], ancla[(p, piso + 1, "esc", s)]
                G.arista(a, b, "escalera", acc=False, w=ALTO_PISO * COSTO_ESCALERA)
            if sp["ascensor"]:
                a, b = ancla[(p, piso, "asc", 0)], ancla[(p, piso + 1, "asc", 0)]
                G.arista(a, b, "ascensor", acc=True, w=ALTO_PISO + COSTO_ASCENSOR)
        n_ids = idx[(p, 1)]
        for ext_id, t in sp["entradas"]:
            k = (round(t * n) % n) if cerrado else int(round(t * (n - 1)))
            G.arista(ext_id, n_ids[k], "puerta")
        if sp["ascensor"] and sp["ascensor"][1]:
            G.arista(sp["ascensor"][1], ancla[(p, 1, "asc", 0)], "puerta")

    # 3) pasajes entre pabellones, por piso
    for p1, t1, p2, t2, nota in PASAJES:
        for piso in range(1, min(PAB[p1]["pisos"], PAB[p2]["pisos"]) + 1):
            a = idx[(p1, piso)][round(t1 * (len(idx[(p1, piso)]) - 1))]
            b = idx[(p2, piso)][round(t2 * (len(idx[(p2, piso)]) - 1))]
            G.arista(a, b, "pasaje", nota=nota)

    # 4) zonas
    for zid, etq, p, piso, t in ZONAS:
        ids = idx[(p, piso)]
        sp = PAB[p]
        k = (round(t * len(ids)) % len(ids)) if sp["tipo"] == "anillo" else int(round(t * (len(ids) - 1)))
        a = G.nodos[ids[k]]
        G.nodo(zid, a["x_px"] + 6, a["y_px"] + 6, a["z"], piso, p, "zona", etq)
        G.arista(ids[k], zid, "pasillo")
    for zid, etq, ext_id, dx, dy in ZONAS_EXT:
        a = G.nodos[ext_id]
        G.nodo(zid, a["x_px"] + dx, a["y_px"] + dy, 0.0, 0, "", "zona", etq)
        G.arista(ext_id, zid, "peatonal")

    G.validar()
    return G


def opciones_destino(G):
    """Puntos que se pueden elegir como origen/destino: {etiqueta: id}."""
    op = {}
    for i in ("E_SUR", "E_PRIM"):
        op[G.nodos[i]["etiqueta"]] = i
    for z in [z[0] for z in ZONAS] + [z[0] for z in ZONAS_EXT]:
        op[G.nodos[z]["etiqueta"]] = z
    op["Topico (22)"] = "A22"
    op["Rotonda central (11)"] = "RG0"
    for n in G.nodos.values():
        if n["pab"] and n["tipo"] == "zona":
            nom = "Biblioteca" if n["pab"] == "I" else f"Pabellon {n['pab']}"
            op[f"{nom} p{n['piso']} - {n['etiqueta']}"] = n["id"]
    for p, sp in PAB.items():
        if sp["tipo"] == "detallado":
            for piso in range(1, sp["pisos"] + 1):
                if p == "I":
                    op[f"Pabellon {p} - piso {piso}"] = f"{p}{piso}_hall"
                elif p == "A":
                    op[f"Pabellon {p} - piso {piso}"] = f"{p}{piso}_e00"
                else:
                    c = [n["id"] for n in G.piso_nodos(p, piso) if n["tipo"] == "pasillo"]
                    op[f"Pabellon {p} - piso {piso}"] = c[len(c) // 2]
            continue
        for piso in range(1, sp["pisos"] + 1):
            ids = [n["id"] for n in G.piso_nodos(p, piso) if n["tipo"] == "pasillo" and "_c" in n["id"]]
            op[f"Pabellon {p} - piso {piso}"] = ids[len(ids) // 2]
    return op


def exportar(G, carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(exist_ok=True)
    with open(carpeta / "nodos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "x_m", "y_m", "z_m", "piso", "pabellon", "tipo", "nombre", "ancho_puerta_m", "escalon"])
        for n in G.nodos.values():
            w.writerow([n["id"], round(n["x"], 2), round(n["y"], 2), round(n["z"], 2), n["piso"],
                        n["pab"], n["tipo"], n["nombre"], n.get("ancho_m", ""), n.get("escalon", "")])
    with open(carpeta / "aristas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["origen", "destino", "peso_m", "tipo", "accesible", "nota"])
        for e in G.aristas:
            w.writerow([e["a"], e["b"], round(e["w"], 2), e["tipo"], int(e["acc"]), e["nota"]])


if __name__ == "__main__":
    G = construir()
    exportar(G, Path(__file__).resolve().parent / "datos")
    print(f"Nodos: {len(G.nodos)}   Aristas: {len(G.aristas)}")
    print("Nodos por pabellon:", G.resumen())
    print("CSV guardados en carpeta datos/")
