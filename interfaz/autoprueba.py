"""Escenario de ejemplo de la interfaz (python app.py --prueba): busca, anima A*, pone una barrera y guarda capturas PNG."""
import sys

from PySide6 import QtWidgets

from interfaz.estilo import preparar
from interfaz.ventana import App
from logica import algoritmos as alg


def prueba(salida):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    preparar(app)
    w = App()
    w.timer.stop()
    w.resize(1650, 940)
    w.show()
    for _ in range(6):
        app.processEvents()
    salida.mkdir(parents=True, exist_ok=True)
    w.buscar("origen", "entrada alonso")
    w.buscar("destino", "cub 54")
    w.cb_plano.setCurrentIndex(0)
    print(w.sim.msg)
    w.iniciar()
    for _ in range(12):
        w.sim.tick(pasos_busqueda=20)
    w.capturar(salida / "1_busqueda_A_estrella.png")
    while w.sim.estado == "buscando":
        w.sim.tick(pasos_busqueda=20)
    while w.sim.estado == "caminando":
        i = w.sim.walker_i
        a, b = w.sim.ruta[i], w.sim.ruta[i + 1]
        if i > 3 and alg.bfs_alcanzable(w.G, a, w.sim.destino, True, frozenset(), frozenset({(a, b)})):
            break
        w.sim.tick(dt=0.045, mult=6)
    w.sim_barrera()
    while w.sim.estado == "buscando":
        w.sim.tick(pasos_busqueda=40)
    for _ in range(30):
        w.sim.tick(dt=0.045, mult=6)
    w.capturar(salida / "2_recorrido_con_barrera.png")
    print("Capturas en", salida, "| estado:", w.sim.estado, "| recalculos:", w.sim.recalculos)
    w.close()
