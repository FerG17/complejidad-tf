"""Integridad del grafo del campus y de la base de datos exportada (datos/*.csv)."""
import collections

from logica.ascensores import _alcanzables
from modelo import construccion
from modelo.config import DATOS
from modelo.nomenclatura import problemas

MINIMO_NODOS = 1500


def test_grafo_valido(G):
    G.validar()   # aristas con nodos existentes y peso >= distancia 3D (heuristica admisible)


def test_cumple_minimo_de_nodos(G):
    assert len(G.nodos) >= MINIMO_NODOS


def test_csv_coincide_con_el_modelo(G, tmp_path):
    construccion.exportar(G, tmp_path)
    for nombre in ("nodos.csv", "aristas.csv"):
        assert (tmp_path / nombre).read_bytes() == (DATOS / nombre).read_bytes(), \
            f"{nombre} desactualizado: ejecutar python -m modelo.construccion"


def test_pisos_de_cada_pabellon(G):
    pisos = collections.defaultdict(set)
    for n in G.nodos.values():
        if n["pab"]:
            pisos[n["pab"]].add(n["piso"])
    for p in "ABCDEFGHJ":
        assert pisos[p] == {1, 2, 3, 4, 5}, p
    assert pisos["I"] == set(range(1, 8))


def test_pasajes_entre_pabellones(G):
    assert sum(1 for e in G.aristas if e["tipo"] == "pasaje") >= len(construccion.PASAJES) * 5


def test_salas_alcanzables_en_silla_de_ruedas(G):
    vis = _alcanzables(G, "E_SUR", set())
    sin = collections.defaultdict(set)
    for n in G.nodos.values():
        if n["pab"] and n["tipo"] == "zona" and n["id"] not in vis:
            sin[n["pab"]].add(n["piso"])
    # el pabellon A no tiene ascensor: solo su piso 1 es accesible; ningun otro pabellon queda aislado
    assert dict(sin) == {"A": {2, 3, 4, 5}}


def test_cada_sala_de_los_pabellones_de_placa_tiene_puerta(G):
    con_puerta = {x for e in G.aristas if e["tipo"] == "puerta" for x in (e["a"], e["b"])}
    sin = [n["nombre"] for n in G.nodos.values() if n["tipo"] == "zona" and n["pab"] in tuple("ABCDEFGHJ") and n["id"] not in con_puerta]
    assert not sin, sin[:5]


def test_nomenclatura_de_salas(G):
    malos = [(n["nombre"], problemas(n["etiqueta"])) for n in G.nodos.values()
             if n["tipo"] == "zona" and problemas(n["etiqueta"])]
    assert not malos, malos[:5]


def test_etiquetas_de_sala_unicas_por_piso(G):
    cuenta = collections.Counter((n["pab"], n["piso"], n["etiqueta"]) for n in G.nodos.values()
                                 if n["tipo"] == "zona" and n["pab"])
    assert [k for k, v in cuenta.items() if v > 1] == []
