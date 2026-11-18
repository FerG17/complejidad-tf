"""Grafo exterior (ruta accesible del plano oficial): nodos y aristas en datos/exterior.json, en pixeles del plano.png."""
import json

from modelo.config import DATOS

with open(DATOS / "exterior.json", encoding="utf-8") as _f:
    _D = json.load(_f)

N = {i: (x, y, tipo, etq) for i, x, y, tipo, etq in _D["nodos"]}   # id -> (x, y, tipo, etiqueta)
E = [tuple(a) for a in _D["aristas"]]
