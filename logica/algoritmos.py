"""
BFS y A* escritos a mano (sin networkx).

* bfs_alcanzable: BFS con deque -> responde si existe algun camino (conectividad).
* astar_pasos:    A* con heapq como GENERADOR: va emitiendo cada nodo expandido para poder
                  animar la busqueda en tiempo real. f(n) = g(n) + h(n),
                  h = distancia euclidiana 3D al destino (admisible: todo peso de arista >= distancia 3D).

Filtro de accesibilidad: si solo_accesible=True se ignoran las aristas con acc=False (escaleras).
"""
import heapq
import math
from collections import deque


def _vecinos(G, u, solo_acc, nodos_bloq, aristas_bloq):
    for v, w, tipo, acc in G.adj[u]:
        if solo_acc and not acc:
            continue
        if v in nodos_bloq:
            continue
        if (u, v) in aristas_bloq or (v, u) in aristas_bloq:
            continue
        yield v, w, tipo


def bfs_alcanzable(G, ini, fin, solo_acc=True, nodos_bloq=frozenset(), aristas_bloq=frozenset()):
    if ini in nodos_bloq or fin in nodos_bloq:
        return False
    vis = {ini}
    cola = deque([ini])
    while cola:
        u = cola.popleft()
        if u == fin:
            return True
        for v, _, _ in _vecinos(G, u, solo_acc, nodos_bloq, aristas_bloq):
            if v not in vis:
                vis.add(v)
                cola.append(v)
    return False


def h3d(G, u, fin):
    a, b = G.nodos[u], G.nodos[fin]
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2)


def astar_pasos(G, ini, fin, solo_acc=True, nodos_bloq=frozenset(), aristas_bloq=frozenset()):
    """Generador. Emite ('expand', nodo, g, n_expandidos) y al final ('fin', ruta, costo, n) o ('sin_ruta', None, inf, n)."""
    abierta = [(h3d(G, ini, fin), 0.0, ini)]
    g = {ini: 0.0}
    padre = {ini: None}
    cerrado = set()
    n = 0
    while abierta:
        _, gu, u = heapq.heappop(abierta)
        if u in cerrado:
            continue
        cerrado.add(u)
        n += 1
        yield ("expand", u, gu, n)
        if u == fin:
            ruta = []
            while u is not None:
                ruta.append(u)
                u = padre[u]
            yield ("fin", ruta[::-1], gu, n)
            return
        for v, w, _ in _vecinos(G, u, solo_acc, nodos_bloq, aristas_bloq):
            if v in cerrado:
                continue
            ng = gu + w
            if ng < g.get(v, math.inf):
                g[v] = ng
                padre[v] = u
                heapq.heappush(abierta, (ng + h3d(G, v, fin), ng, v))
    yield ("sin_ruta", None, math.inf, n)


def astar(G, ini, fin, **kw):
    """Version no animada: devuelve (ruta, costo, expandidos)."""
    ult = None
    for ev in astar_pasos(G, ini, fin, **kw):
        ult = ev
    return ult[1], ult[2], ult[3]
