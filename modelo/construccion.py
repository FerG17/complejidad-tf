"""
Generador del grafo 3D del Campus Monterrico (UPC) - Equipo 10, 1ACC0184.

Une el grafo exterior (exterior.py) con los pabellones de modelo/pabellones/ y los conecta con pasajes. Devuelve un
Grafo en memoria y, como script (python -m modelo.construccion), exporta datos/nodos.csv y datos/aristas.csv.
Numeros del plano oficial: A 16/17/18, B 34, C 29, D 28, E 15, F 14, G 12/13, H 8/9/10, I 23/24/25, J 30-33, K 26/27, L 1/3/4.

Supuestos (las aristas supuestas llevan nota en aristas.csv):
  * ESCALA 0.275 m/px: calibrada contra Google Maps y la medicion Primavera-Alonso de Molina (131.85 m), error ~7 m.
  * BASE_Z = 0 en todos los pabellones (el campus tiene pendiente).
  * Pasillos J-B, C-D y E-F-G a nivel y accesibles en todos los pisos; E-A solo por escaleras.
  * K y la Biblioteca se unen en los pisos 1 a 5; K y L: ver pabellones/planta_libre.py.
"""
import csv
from functools import partial
from pathlib import Path

from modelo import exterior
from modelo.config import DATOS
from modelo.grafo import Grafo
from modelo.pabellones import biblioteca, datos, pabellon_foto, planta_libre

_FOTO = {p: datos.cargar(p) for p in datos.PABELLONES}   # pabellones reconstruidos de las placas (datos/pabellones/*.json)
ESPECIALES = {**{p: partial(pabellon_foto.construir, pab=p, esq=d["esq"], pisos=d["pisos"]) for p, d in _FOTO.items()},
              "I": biblioteca.construir, "K": planta_libre.construir_k, "L": planta_libre.construir_l}
HUELLAS = {"I": biblioteca.HUELLAS, **{p: d["huellas"] for p, d in _FOTO.items() if d["huellas"]},
           **planta_libre.HUELLAS}   # explicitas; las demas salen de los nodos
CONSTRUCTORES = {p: ESPECIALES[p] for p in "ABCDEFGHIJKL"}

# Pasillos entre pabellones (por piso): (pab1, ancla1, pab2, ancla2, nota); ancla = "inicio" | "fin" del pasillo del pabellon
PASAJES = [
    ("J", "fin", "B", "inicio", "supuesto: pasillo J-B a nivel en todos los pisos (indicado por el equipo)"),
    ("E", "fin", "F", "inicio", "supuesto: E-F continuo en todos los pisos"),
    ("F", "fin", "G", "inicio", "supuesto: F-G continuo (un solo pasillo con su escalera)"),
    ("D", "inicio", "C", "inicio", "confirmado por el equipo: plataforma plana C-D en los pisos 1 a 5 (en el hueco entre ambos "
                         "hay escaleras); posicion aproximada en el extremo norte"),
]

# Zonas exteriores: (id, etiqueta, nodo exterior al que se cuelgan, dx, dy en px)
ZONAS_EXT = [
    ("Z_KATA", "Restaurant Kata (G)", "X4", 14, -22),
    ("Z_GALERIA", "Galeria (19)", "L3", 0, -20),
]


def construir():
    G = Grafo()

    for i, (x, y, tipo, etq) in exterior.N.items():
        G.nodo(i, x, y, 0.0, 0, "", tipo, etq)
    for a, b in exterior.E:
        tipo = "rampa" if "rampa" in (G.nodos[a]["tipo"], G.nodos[b]["tipo"]) else "peatonal"
        G.arista(a, b, tipo)
    G.arista("V_E2", "SV3", "escalera_ext", acc=False, w=G.d3("V_E2", "SV3") * 1.5,
             nota="E-A solo por escaleras/desnivel (confirmado por el equipo): NO accesible")

    pasillos = {}   # (pabellon, piso) -> ids del pasillo, solo para los de tipo corredor
    for p, construir_pab in CONSTRUCTORES.items():
        for piso, ids in (construir_pab(G) or {}).items():
            pasillos[(p, piso)] = ids

    ancla = lambda ids, cual: ids[0] if cual == "inicio" else ids[-1]
    for p1, a1, p2, a2, nota in PASAJES:
        for piso in range(1, 6):
            G.arista(ancla(pasillos[(p1, piso)], a1), ancla(pasillos[(p2, piso)], a2), "pasaje", nota=nota)

    for zid, etq, ext_id, dx, dy in ZONAS_EXT:
        a = G.nodos[ext_id]
        G.nodo(zid, a["x_px"] + dx, a["y_px"] + dy, 0.0, 0, "", "zona", etq)
        G.arista(ext_id, zid, "peatonal")

    G.validar()
    return G


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
    exportar(G, DATOS)
    print(f"Nodos: {len(G.nodos)}   Aristas: {len(G.aristas)}")
    print("Nodos por pabellon:", G.resumen())
    print("CSV guardados en carpeta datos/")
