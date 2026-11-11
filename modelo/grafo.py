"""Grafo ponderado 3D del campus: nodos (id, posicion en px y m, piso, pabellon, tipo) y aristas no dirigidas con
peso en metros equivalentes y marca de accesibilidad. Lista de adyacencia perezosa en `adj`."""
import math

from modelo.config import ESCALA


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
