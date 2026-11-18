"""Algoritmos (BFS y A*), buscador y retos de ascensores sobre el grafo real."""
import heapq
import math

from logica import algoritmos as alg
from logica import ascensores, buscador


def _dijkstra(G, ini, fin):
    dist = {ini: 0.0}
    cola = [(0.0, ini)]
    while cola:
        d, u = heapq.heappop(cola)
        if u == fin:
            return d
        if d > dist.get(u, math.inf):
            continue
        for v, w, _, acc in G.adj[u]:
            if acc and d + w < dist.get(v, math.inf):
                dist[v] = d + w
                heapq.heappush(cola, (d + w, v))
    return math.inf


def _mejor(G, q):
    r = buscador.buscar(G, q, n=1)[0]
    return G.nodos[r[0] if isinstance(r, tuple) else r]["nombre"]


def test_astar_es_optimo(G):
    for destino in ("H4_rp01", "J5_rp00", "B5_rp00", "C5_rp01", "D5_rp00", "A1_rp01", "I7_Z05", "E4_rp03"):
        ruta, costo, _ = alg.astar(G, "E_SUR", destino, solo_acc=True)
        assert ruta[0] == "E_SUR" and ruta[-1] == destino
        assert math.isclose(costo, _dijkstra(G, "E_SUR", destino), rel_tol=1e-9)


def test_bfs_coincide_con_la_existencia_de_ruta(G):
    assert alg.bfs_alcanzable(G, "E_SUR", "H5_rp02", True)
    assert not alg.bfs_alcanzable(G, "E_SUR", "A5_rp01", True)       # A no tiene ascensor
    assert alg.bfs_alcanzable(G, "E_SUR", "A5_rp01", False)          # por escaleras si


def test_hall_de_h_lleva_al_ascensor_sin_rodeos(G):
    ruta, _, _ = alg.astar(G, "P8b", "H1_asc", solo_acc=True)
    largo = sum(G.d3(a, b) for a, b in zip(ruta, ruta[1:]))
    assert largo < 2 * G.d3("P8b", "H1_asc")


def test_buscador_entiende_la_nomenclatura(G):
    assert _mejor(G, "aula H-41") == "H p4 - Salon/Lab. computo H-41"
    assert _mejor(G, "salon 41 h") == "H p4 - Salon/Lab. computo H-41"
    assert _mejor(G, "cub 54") == "I p7 - CUB-54"
    assert "SSHH hombres" in _mejor(G, "bano varones piso 4")
    assert "SSHH mujeres" in _mejor(G, "sshh damas")


def test_retos_de_ascensores(G):
    retos = ascensores.retos(G)
    assert len(retos) == 12
    cat = {c["clave"]: c["nodos"] for c in ascensores.catalogo(G)}
    reto = next(r for r in retos if r["titulo"].startswith("J sin ascensor"))
    bloq = frozenset(n for k in reto["fuera"] for n in cat[k])
    assert {"B", "J"} <= set(ascensores.pisos_sin_acceso(G, bloq))   # B se sirve por el ascensor de J
