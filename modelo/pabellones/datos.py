"""
Carga de los datos de los pabellones: un archivo JSON por pabellon en datos/pabellones/.
Cada archivo trae el esqueleto de circulacion (pasillos, escaleras, ascensor, entradas), las salas y puertas de cada
piso en coordenadas de su foto y los puntos de registro foto -> plano.png; el motor es modelo/pabellones/pabellon_foto.py.
"""
import json

from modelo.config import DATOS

CARPETA = DATOS / "pabellones"
PABELLONES = "ABCDEFGHJ"   # reconstruidos con pabellon_foto; I, K y L tienen su propio constructor y JSON


def _tuplas(x):
    """Las listas de dos numeros son puntos (x, y): se vuelven tuplas para poder usarlas como claves."""
    if isinstance(x, list):
        if len(x) == 2 and all(isinstance(v, (int, float)) for v in x):
            return tuple(x)
        return [_tuplas(v) for v in x]
    if isinstance(x, dict):
        return {k: _tuplas(v) for k, v in x.items()}
    return x


def crudo(pab):
    """Contenido del JSON de `pab` con los puntos como tuplas."""
    with open(CARPETA / f"{pab}.json", encoding="utf-8") as f:
        return _tuplas(json.load(f))


def cargar(pab):
    """-> dict(esq, pisos={piso: datos}, huellas) de un pabellon reconstruido de las placas (huellas puede ser None)."""
    d = crudo(pab)
    pisos = {}
    for piso, datos in d["pisos"].items():
        datos = dict(datos)
        datos["salas"] = [(etq, centro, puertas) for etq, centro, puertas in datos["salas"]]
        pisos[int(piso)] = datos
    return dict(esq=d["esqueleto"], pisos=pisos, huellas=d.get("huellas"))
