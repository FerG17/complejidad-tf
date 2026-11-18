"""Humo de la interfaz: los modulos importan y la autoprueba corre sin pantalla (Qt offscreen)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_modulos_de_la_interfaz_importan():
    import interfaz.autoprueba, interfaz.estilo, interfaz.geometria, interfaz.vista, interfaz.ventana  # noqa: F401


def test_autoprueba_genera_las_capturas(tmp_path):
    from interfaz.autoprueba import prueba
    prueba(tmp_path)
    assert (tmp_path / "1_busqueda_A_estrella.png").stat().st_size > 10_000
    assert (tmp_path / "2_recorrido_con_barrera.png").stat().st_size > 10_000
