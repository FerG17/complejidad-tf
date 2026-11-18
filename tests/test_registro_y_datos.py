"""Registro foto -> plano, archivos JSON de los pabellones y geometria de la vista 3D."""
import math

import numpy as np

from interfaz.geometria import casco, rectangulo
from modelo.pabellones import datos
from modelo.registro import ajustar, semejanza


def _cerca(a, b, tol=1e-6):
    return all(math.isclose(u, v, abs_tol=tol) for u, v in zip(a, b))


def test_afin_con_tres_pares_es_exacta():
    f = ajustar([((0, 0), (10, 20)), ((100, 0), (10, 120)), ((0, 100), (-90, 20))])
    assert _cerca(f(50, 50), (-40, 70))


def test_homografia_reproduce_los_puntos_de_control():
    pares = [((0, 0), (0, 0)), ((100, 0), (50, 0)), ((100, 100), (50, 50)), ((0, 100), (0, 50))]
    f = ajustar(pares)
    assert all(_cerca(f(*p), q) for p, q in pares)
    assert _cerca(f(50, 50), (25, 25))


def test_semejanza_recupera_giro_y_escala():
    a, k = 0.7, 0.15
    real = lambda x, y: (k * (math.cos(a) * x - math.sin(a) * y) + 30, k * (math.sin(a) * x + math.cos(a) * y) - 5)
    f = semejanza([(p, real(*p)) for p in [(0, 0), (300, 20), (310, 25), (50, 400)]])
    assert _cerca(f(120, 80), real(120, 80)) and _cerca(f(-40, 260), real(-40, 260))


def test_cada_pabellon_tiene_sus_cinco_pisos():
    for p in datos.PABELLONES:
        d = datos.cargar(p)
        assert sorted(d["pisos"]) == [1, 2, 3, 4, 5], p
        for piso, x in d["pisos"].items():
            assert len(x["pares"]) >= 3 and x["salas"], (p, piso)


def test_las_coordenadas_son_puntos_hashables():
    d = datos.cargar("H")
    assert all(isinstance(c, tuple) and len(c) == 2 for c in d["esq"]["cadenas"][0])
    etq, centro, puertas = d["pisos"][4]["salas"][0]
    assert isinstance(etq, str) and isinstance(centro, tuple) and all(isinstance(p, tuple) for p in puertas)


def test_rectangulo_minimo_contiene_los_puntos():
    pts = np.array([[0, 0], [10, 2], [12, 8], [1, 6], [5, 4]], float)
    r = rectangulo(pts, 0.0)
    assert len(r) == 4 and len(casco(pts)) >= 3
    area_rect = np.linalg.norm(r[1] - r[0]) * np.linalg.norm(r[3] - r[0])
    assert area_rect >= 0.5 * 12 * 8   # mayor que la mitad de la caja envolvente, nunca menor que el casco
