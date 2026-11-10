"""
Buscador de nodos por nombre (sin tildes, sin importar mayusculas ni el orden de las palabras).
  buscar(G, "cub 54")        -> CUB-54 de la Biblioteca (piso 7)
  buscar(G, "aula a-34")     -> Aula A-34 (pabellon A, piso 3)
  buscar(G, "sshh I p3")     -> SSHH de la Biblioteca, piso 3
  buscar(G, "ascensor J")    -> ascensores de J en todos los pisos
Solo busca puntos "identificables": salas/aulas, ascensores, escaleras y entradas/rampas exteriores.
"""
import re
import unicodedata

TIPOS = {"zona", "ascensor", "escalera", "entrada_accesible", "entrada_campus", "rampa", "salida_emergencia"}


def _toks(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z]+|\d+", s)


def buscar(G, texto, n=8):
    q = _toks(texto)
    if not q:
        return []
    res = []
    for nodo in G.nodos.values():
        if nodo["tipo"] not in TIPOS:
            continue
        t = _toks(nodo["nombre"] + " " + nodo["id"])
        if not all(any(w.startswith(x) for w in t) for x in q):
            continue
        exactas = sum(1 for x in q if x in t)
        res.append((-exactas, len(nodo["nombre"]), nodo["piso"], nodo["id"]))
    res.sort()
    return [r[3] for r in res[:n]]


if __name__ == "__main__":
    import sys
    import generador
    G = generador.construir()
    for i in buscar(G, " ".join(sys.argv[1:])):
        print(i, "|", G.nodos[i]["nombre"])
