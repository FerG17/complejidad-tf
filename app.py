"""
Navegacion accesible en el Campus Monterrico (UPC) - Equipo 10 - 1ACC0184 Complejidad Algoritmica
Grafo 3D (exterior + pabellones por piso), BFS (conectividad) y A* (ruta optima) animados en tiempo real.

Uso:   python app.py            -> abre la ventana interactiva
       python app.py --prueba   -> genera capturas PNG de un escenario de ejemplo (sin ventana)

Controles:
  Barra lateral izquierda: escribe el nombre en Origen / Destino (ej. "cub 54", "aula a-34", "sshh i p3", "kata");
  aparecen sugerencias: clic en una para elegirla (Enter = la primera).
  O clic izquierdo en el plano = ORIGEN, clic derecho = DESTINO.
  Iniciar (espacio)   Barrera tramo (b)   Ascensor fuera (a)   Reiniciar (r)
  Vista 3D: Auto (sigue la ruta) / Campus completo / un pabellon;  'Ver piso' filtra un piso.
"""
import sys
from pathlib import Path

import matplotlib
if "--prueba" in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider, TextBox

import algoritmos as alg
import buscador
import generador
from simulador import Simulador
from vista import Vista

CARPETA = Path(__file__).resolve().parent
NSUG = 6


class App:
    def __init__(self):
        self.G = generador.construir()
        self.sim = Simulador(self.G)
        self.fig = plt.figure(figsize=(16, 8.8))
        if getattr(self.fig.canvas, "manager", None):
            self.fig.canvas.manager.set_window_title("Campus Monterrico - rutas accesibles 3D (A*)")
        self.vista = Vista(self.G, str(CARPETA / "plano.png"), self.fig)
        self.piso_o = self.piso_d = 1
        self._rol_sug = "origen"
        self._sug_ids = []
        self._widgets()
        self.fig.canvas.mpl_connect("button_press_event", self._clic)
        self.fig.canvas.mpl_connect("key_press_event", self._tecla)
        self.timer = self.fig.canvas.new_timer(interval=40)
        self.timer.add_callback(self.tick)
        self.timer.start()
        self.vista.actualizar(self.sim)

    # ------------------------------------------------------------ widgets
    def _widgets(self):
        f = self.fig
        f.text(0.012, 0.975, "BUSCAR POR NOMBRE", fontsize=9.5, fontweight="bold", va="center")
        self.tb_o = TextBox(f.add_axes([0.065, 0.925, 0.135, 0.035]), "Origen ", textalignment="left")
        self.tb_d = TextBox(f.add_axes([0.065, 0.882, 0.135, 0.035]), "Destino ", textalignment="left")
        self.tb_o.on_submit(lambda t: self.buscar("origen", t))
        self.tb_d.on_submit(lambda t: self.buscar("destino", t))
        self.tb_o.on_text_change(lambda t: self._sugerir("origen", t))
        self.tb_d.on_text_change(lambda t: self._sugerir("destino", t))
        f.text(0.012, 0.858, "Sugerencias (clic para elegir):", fontsize=7.5, color="#555", va="center")
        self.btn_sug = []
        for k in range(NSUG):
            b = Button(f.add_axes([0.01, 0.822 - 0.031 * k, 0.19, 0.028]), "", color="#eef3fb", hovercolor="#cfe0f7")
            b.label.set_fontsize(7.2)
            b.ax.set_visible(False)
            b.on_clicked(lambda _e, k=k: self._elegir_sug(k))
            self.btn_sug.append(b)

        self.chk = CheckButtons(f.add_axes([0.01, 0.595, 0.19, 0.04]), ["Solo ruta accesible"], [True])
        self.chk.on_clicked(self._toggle_acc)
        defs = [("Iniciar", self.iniciar, 0.01, 0.53), ("Reiniciar", self.reiniciar, 0.105, 0.53),
                ("Barrera\nen el tramo", self.sim_barrera, 0.01, 0.465),
                ("Ascensor fuera\nde servicio", self.sim_asc, 0.105, 0.465),
                ("Ejemplo", self.ejemplo, 0.01, 0.41)]
        self.btns = []
        for txt, fn, x, y in defs:
            w, h = (0.095, 0.055) if "\n" in txt or txt in ("Iniciar", "Reiniciar") else (0.19, 0.045)
            b = Button(f.add_axes([x, y, w - 0.005, h]), txt)
            b.label.set_fontsize(8.5)
            b.on_clicked(lambda _e, fn=fn: fn())
            self.btns.append(b)

        self.s_po = Slider(f.add_axes([0.075, 0.365, 0.12, 0.018]), "Piso origen", 1, 7, valinit=1, valstep=1)
        self.s_pd = Slider(f.add_axes([0.075, 0.335, 0.12, 0.018]), "Piso destino", 1, 7, valinit=1, valstep=1)
        self.s_v = Slider(f.add_axes([0.075, 0.305, 0.12, 0.018]), "Velocidad", 1, 30, valinit=8, valstep=1)
        self.s_ver = Slider(f.add_axes([0.075, 0.275, 0.12, 0.018]), "Ver piso 3D", 0, 7, valinit=0, valstep=1)
        for s in (self.s_po, self.s_pd, self.s_v, self.s_ver):
            s.label.set_fontsize(8)
            s.valtext.set_fontsize(8)
        self.s_po.on_changed(lambda v: setattr(self, "piso_o", int(v)))
        self.s_pd.on_changed(lambda v: setattr(self, "piso_d", int(v)))
        self.s_ver.on_changed(self._cambia_piso_ver)
        f.text(0.012, 0.250, "(Ver piso 3D: 0 = todos los pisos)", fontsize=7, color="#666", va="center")

        f.text(0.012, 0.222, "VISTA 3D", fontsize=9.5, fontweight="bold", va="center")
        self._modos = ["Auto"] + ["Campus"] + list(self.vista.pabs)
        etiquetas = ["Auto (sigue la ruta)", "Campus completo"] + [f"Pabellon {p}" for p in self.vista.pabs]
        self.radio = RadioButtons(f.add_axes([0.01, 0.015, 0.19, 0.195], facecolor="#f6f6f6"), etiquetas, active=0)
        for lab in self.radio.labels:
            lab.set_fontsize(8)
        self.radio.on_clicked(lambda lab: self._cambia_modo(etiquetas.index(lab)))

    def _cambia_modo(self, idx):
        self.vista.modo = self._modos[idx]
        self._refrescar()

    def _cambia_piso_ver(self, v):
        self.vista.piso_ver = int(v)
        self._refrescar()

    def _toggle_acc(self, _label):
        self.sim.solo_acc = self.chk.get_status()[0]
        self._refrescar()

    # ------------------------------------------------------------ busqueda por nombre
    def _sugerir(self, rol, texto):
        self._rol_sug = rol
        self._sug_ids = buscador.buscar(self.G, texto, n=NSUG) if texto.strip() else []
        for k, b in enumerate(self.btn_sug):
            if k < len(self._sug_ids):
                b.label.set_text(self.G.nodos[self._sug_ids[k]]["nombre"])
                b.ax.set_visible(True)
            else:
                b.ax.set_visible(False)
        self.fig.canvas.draw_idle()

    def _elegir_sug(self, k):
        if k >= len(self._sug_ids):
            return
        nid = self._sug_ids[k]
        self._asignar(self._rol_sug, nid, [])
        self._sug_ids = []
        for b in self.btn_sug:
            b.ax.set_visible(False)
        self._refrescar()

    def _asignar(self, rol, nid, otras):
        if self.sim.estado in ("buscando", "caminando"):
            self.sim.reiniciar(todo=False)
        setattr(self.sim, rol, nid)
        tb = self.tb_o if rol == "origen" else self.tb_d
        if tb.text != self.G.nodos[nid]["nombre"]:
            tb.eventson = False
            tb.set_val(self.G.nodos[nid]["nombre"])
            tb.eventson = True
        extra = "; ".join(self.G.nodos[i]["nombre"] for i in otras[:3])
        self.sim.msg = (f"{rol.capitalize()}: {self.G.nodos[nid]['nombre']}"
                        + (f"   (otras coincidencias: {extra})" if extra else "") + ".  Pulsa Iniciar.")

    def buscar(self, rol, texto):
        """Enter en la caja: elige la primera coincidencia."""
        if not texto.strip():
            return
        r = buscador.buscar(self.G, texto)
        if not r:
            self.sim.msg = f"No encontre '{texto}'. Prueba: 'cub 54', 'aula a-34', 'ascensor J', 'kata', 'entrada primavera'."
        else:
            self._asignar(rol, r[0], r[1:])
        self._refrescar()

    # ------------------------------------------------------------ acciones
    def iniciar(self):
        self.sim.iniciar()
        self._refrescar()

    def sim_barrera(self):
        self.sim.barrera_tramo()
        self._refrescar()

    def sim_asc(self):
        self.sim.ascensor_fuera()
        self._refrescar()

    def reiniciar(self):
        self.sim.reiniciar(todo=True)
        self._refrescar()

    def ejemplo(self):
        op = generador.opciones_destino(self.G)
        self.sim.reiniciar(todo=True)
        self.sim.origen = op["Entrada Av. Alonso de Molina"]
        self.sim.destino = op["Pabellon H - piso 3"]
        self.iniciar()

    def _refrescar(self):
        self.vista.refrescar(self.sim)

    # ------------------------------------------------------------ eventos
    def tick(self):
        v = int(self.s_v.val)
        if self.sim.tick(pasos_busqueda=v, dt=0.045, mult=v / 2.0):
            self.vista.refrescar(self.sim)

    def _tecla(self, ev):
        if self.tb_o.capturekeystrokes or self.tb_d.capturekeystrokes:
            return    # se esta escribiendo en una caja de texto
        acciones = {" ": self.iniciar, "b": self.sim_barrera, "a": self.sim_asc, "r": self.reiniciar}
        if ev.key in acciones:
            acciones[ev.key]()

    def _clic(self, ev):
        if ev.inaxes is not self.vista.ax2 or ev.xdata is None:
            return
        tb = getattr(self.fig.canvas, "toolbar", None)
        if tb is not None and getattr(tb, "mode", ""):
            return   # zoom/pan activo
        if ev.button not in (1, 3):
            return
        nodo = self.elegir_nodo(ev.xdata, ev.ydata, self.piso_o if ev.button == 1 else self.piso_d)
        if nodo is None:
            return
        self._asignar("origen" if ev.button == 1 else "destino", nodo, [])
        self.sim.msg = "Origen/destino actualizado. Pulsa Iniciar (espacio)."
        self._refrescar()

    def elegir_nodo(self, x, y, piso):
        cand = [n for n in self.G.nodos.values() if n["piso"] <= 1]
        n0 = min(cand, key=lambda n: (n["x_px"] - x) ** 2 + (n["y_px"] - y) ** 2)
        if (n0["x_px"] - x) ** 2 + (n0["y_px"] - y) ** 2 > 35 ** 2:
            return None
        if not n0["pab"]:
            return n0["id"]
        piso = min(piso, generador.PAB[n0["pab"]]["pisos"])
        if piso == 1:
            return n0["id"]
        c = [n for n in self.G.piso_nodos(n0["pab"], piso) if n["tipo"] == "pasillo"]
        return min(c, key=lambda n: (n["x_px"] - n0["x_px"]) ** 2 + (n["y_px"] - n0["y_px"]) ** 2)["id"]


def prueba():
    """Escenario de ejemplo sin ventana: guarda capturas en la carpeta capturas/."""
    app = App()
    app.timer.stop()
    out = CARPETA / "capturas"
    out.mkdir(exist_ok=True)
    app.buscar("origen", "entrada alonso")
    app.buscar("destino", "cub 54")
    print(app.sim.msg)
    app.iniciar()
    for _ in range(12):
        app.sim.tick(pasos_busqueda=20)
    app.vista.actualizar(app.sim)
    app.vista.guardar(out / "1_busqueda_A_estrella.png")
    while app.sim.estado == "buscando":
        app.sim.tick(pasos_busqueda=20)
    while app.sim.estado == "caminando":      # caminar hasta un tramo con desvio posible
        i = app.sim.walker_i
        a, b = app.sim.ruta[i], app.sim.ruta[i + 1]
        if i > 3 and alg.bfs_alcanzable(app.G, a, app.sim.destino, True, frozenset(), frozenset({(a, b)})):
            break
        app.sim.tick(dt=0.045, mult=6)
    app.sim.barrera_tramo()
    while app.sim.estado == "buscando":
        app.sim.tick(pasos_busqueda=40)
    for _ in range(30):
        app.sim.tick(dt=0.045, mult=6)
    app.vista.actualizar(app.sim)
    app.vista.guardar(out / "2_recorrido_con_barrera.png")
    print("Capturas en", out, "| estado:", app.sim.estado, "| recalculos:", app.sim.recalculos)


if __name__ == "__main__":
    if "--prueba" in sys.argv:
        prueba()
    else:
        App()
        plt.show()
