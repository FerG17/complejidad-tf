"""
Navegacion accesible en el Campus Monterrico (UPC) - Equipo 10 - 1ACC0184 Complejidad Algoritmica
Grafo 3D (exterior + pabellones por piso), BFS (conectividad) y A* (ruta optima) animados en tiempo real.

Uso:   python app.py                       -> abre la ventana interactiva
       python app.py --prueba [--salida D] -> escenario de ejemplo que guarda capturas PNG (abre la ventana unos segundos)

Controles:
  Panel izquierdo: escribe en Origen / Destino ("salon 51", "e 51", "cub 54", "bano piso 3", "labs computo c")
  o filtra por pabellon y piso, y haz clic en un resultado (Enter = el primero).
  Plano 2D: clic izquierdo = ORIGEN, clic derecho = DESTINO sobre el piso que se muestra.
  Iniciar (espacio)   Barrera tramo (b)   Ascensor fuera (a)   Reiniciar (r)
  3D: arrastrar = rotar, rueda = zoom, boton central o Ctrl+arrastrar = mover.
"""
import sys
from pathlib import Path

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

import algoritmos as alg
import ascensores
import buscador
import generador
from simulador import Simulador
from vista import COL_ASC, COL_ESC, COL_PISO, Vista

CARPETA = Path(__file__).resolve().parent
MAX_RESULTADOS = 150
INTERVALO_MS = 30


class App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Campus Monterrico - rutas accesibles 3D (A*)")
        self.G = generador.construir()
        self.sim = Simulador(self.G)
        self.vista = Vista(self.G, str(CARPETA / "plano.png"))
        self.vista.clic.connect(self._clic_plano)
        self.retos = ascensores.retos(self.G)
        self._rol = "origen"
        self._construir_ui()
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(INTERVALO_MS)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self._refrescar()

    def _construir_ui(self):
        centro = QtWidgets.QWidget()
        self.setCentralWidget(centro)
        raiz = QtWidgets.QHBoxLayout(centro)
        raiz.setContentsMargins(8, 8, 8, 8)
        raiz.addWidget(self._panel_lateral())
        medio = QtWidgets.QVBoxLayout()
        medio.setContentsMargins(0, 0, 0, 0)
        medio.addWidget(self.vista.w2d)
        self.lbl_msg = QtWidgets.QLabel()
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setStyleSheet("font-size: 13px; font-weight: 600; color: #111;")
        self.lbl_info = QtWidgets.QLabel()
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("font-size: 12px; color: #333;")
        medio.addWidget(self.lbl_msg)
        medio.addWidget(self.lbl_info)
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._grupo_vista(), "Vista")
        tabs.addTab(self._grupo_ascensores(), "Ascensores y retos")
        medio.addWidget(tabs)
        medio.addWidget(self._leyenda())
        medio.addStretch(1)
        col = QtWidgets.QWidget()
        col.setLayout(medio)
        col.setMinimumWidth(520)
        raiz.addWidget(col, 5)
        raiz.addWidget(self.vista.w3d, 6)
        for tecla, fn in (("Space", self.iniciar), ("B", self.sim_barrera), ("A", self.sim_asc), ("R", self.reiniciar)):
            QtGui.QShortcut(QtGui.QKeySequence(tecla), self, activated=fn)

    def _panel_lateral(self):
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(360)
        lay = QtWidgets.QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)

        g = QtWidgets.QGroupBox("Buscar origen y destino")
        gl_ = QtWidgets.QVBoxLayout(g)
        self.le_o = QtWidgets.QLineEdit()
        self.le_o.setPlaceholderText("Origen: ej. entrada alonso")
        self.le_d = QtWidgets.QLineEdit()
        self.le_d.setPlaceholderText("Destino: ej. salon 51, cub 54, bano")
        for le in (self.le_o, self.le_d):
            le.setClearButtonEnabled(True)
            le.textEdited.connect(self._buscar)
            le.returnPressed.connect(self._elegir_primero)
            le.installEventFilter(self)
            gl_.addWidget(le)
        fila = QtWidgets.QHBoxLayout()
        self.cb_pab = QtWidgets.QComboBox()
        self.cb_pab.addItem("Todos los pabellones", None)
        for p in self.vista.pabs:
            self.cb_pab.addItem("Biblioteca (I)" if p == "I" else f"Pabellon {p}", p)
        self.cb_piso = QtWidgets.QComboBox()
        self.cb_piso.addItem("Todos los pisos", None)
        for k in range(1, 8):
            self.cb_piso.addItem(f"Piso {k}", k)
        for cb in (self.cb_pab, self.cb_piso):
            cb.currentIndexChanged.connect(self._buscar)
            fila.addWidget(cb)
        gl_.addLayout(fila)
        self.lbl_res = QtWidgets.QLabel()
        self.lbl_res.setStyleSheet("color: #555; font-size: 11px;")
        gl_.addWidget(self.lbl_res)
        self.lista = QtWidgets.QListWidget()
        self.lista.setMinimumHeight(190)
        self.lista.itemClicked.connect(self._elegir_item)
        gl_.addWidget(self.lista, 1)
        lay.addWidget(g, 1)

        self.chk = QtWidgets.QCheckBox("Solo ruta accesible")
        self.chk.setChecked(True)
        self.chk.toggled.connect(self._toggle_acc)
        lay.addWidget(self.chk)
        grid = QtWidgets.QGridLayout()
        for k, (txt, fn) in enumerate((("Iniciar (espacio)", self.iniciar), ("Reiniciar (r)", self.reiniciar),
                                       ("Barrera en el tramo (b)", self.sim_barrera),
                                       ("Ascensor fuera de servicio (a)", self.sim_asc))):
            b = QtWidgets.QPushButton(txt)
            b.setFocusPolicy(QtCore.Qt.NoFocus)
            b.clicked.connect(lambda _c=False, fn=fn: fn())
            grid.addWidget(b, k // 2, k % 2)
        b = QtWidgets.QPushButton("Ejemplo")
        b.setFocusPolicy(QtCore.Qt.NoFocus)
        b.clicked.connect(self.ejemplo)
        grid.addWidget(b, 2, 0, 1, 2)
        lay.addLayout(grid)
        vel = QtWidgets.QHBoxLayout()
        vel.addWidget(QtWidgets.QLabel("Velocidad"))
        self.s_v = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.s_v.setRange(1, 30)
        self.s_v.setValue(8)
        vel.addWidget(self.s_v, 1)
        lay.addLayout(vel)
        return panel

    def _grupo_vista(self):
        v = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(v)
        self.cb_modo = QtWidgets.QComboBox()
        self.cb_modo.addItem("Auto (sigue la ruta)", "Auto")
        self.cb_modo.addItem("Campus completo", "Campus")
        for p in self.vista.pabs:
            self.cb_modo.addItem("Biblioteca (I)" if p == "I" else f"Pabellon {p}", p)
        self.cb_modo.currentIndexChanged.connect(self._cambia_modo)
        self.cb_ver = QtWidgets.QComboBox()
        self.cb_ver.addItem("Todos", 0)
        for k in range(1, 8):
            self.cb_ver.addItem(f"Piso {k}", k)
        self.cb_ver.currentIndexChanged.connect(self._cambia_piso_ver)
        self.cb_plano = QtWidgets.QComboBox()
        for k in range(1, 8):
            self.cb_plano.addItem(f"Piso {k}", k)
        self.cb_plano.currentIndexChanged.connect(self._cambia_piso_plano)
        self.chk_seguir = QtWidgets.QCheckBox("El plano sigue al caminante")
        self.chk_seguir.setChecked(True)
        form.addRow("Vista 3D:", self.cb_modo)
        form.addRow("Piso en 3D:", self.cb_ver)
        form.addRow("Piso en el plano:", self.cb_plano)
        self.chk_muros = QtWidgets.QCheckBox("Muros de los edificios en el 3D")
        self.chk_muros.setChecked(True)
        self.chk_muros.toggled.connect(self._toggle_muros)
        form.addRow(self.chk_seguir)
        form.addRow(self.chk_muros)
        return v

    def _grupo_ascensores(self):
        g = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(g)
        fila = QtWidgets.QHBoxLayout()
        self.cb_reto = QtWidgets.QComboBox()
        for r in self.retos:
            self.cb_reto.addItem(r["titulo"])
        self.cb_reto.currentIndexChanged.connect(self._muestra_reto)
        b = QtWidgets.QPushButton("Cargar reto")
        b.setFocusPolicy(QtCore.Qt.NoFocus)
        b.clicked.connect(self.cargar_reto)
        fila.addWidget(self.cb_reto, 1)
        fila.addWidget(b)
        lay.addLayout(fila)
        self.lbl_reto = QtWidgets.QLabel()
        self.lbl_reto.setWordWrap(True)
        self.lbl_reto.setStyleSheet("color: #555; font-size: 11px;")
        lay.addWidget(self.lbl_reto)
        lay.addWidget(QtWidgets.QLabel("Marca un ascensor para sacarlo de servicio:"))
        grid = QtWidgets.QGridLayout()
        self.chk_asc = {}
        for k, a in enumerate(self.sim.catalogo):
            c = QtWidgets.QCheckBox(a["nombre"])
            c.setFocusPolicy(QtCore.Qt.NoFocus)
            c.toggled.connect(lambda estado, clave=a["clave"]: self._toggle_asc(clave, estado))
            self.chk_asc[a["clave"]] = c
            grid.addWidget(c, k // 3, k % 3)
        lay.addLayout(grid)
        self.lbl_aislados = QtWidgets.QLabel()
        self.lbl_aislados.setWordWrap(True)
        self.lbl_aislados.setStyleSheet("font-size: 12px; color: #7a1f1f;")
        lay.addWidget(self.lbl_aislados)
        self._muestra_reto()
        self._actualizar_aislados()
        return g

    def _actualizar_aislados(self):
        s = self.sim
        t = f"Siempre sin ruta accesible (sin ascensor propio): {ascensores.texto_pisos(s.sin_acceso_base)}."
        if s.fuera:
            extra = s.sin_acceso_por_fuera()
            t += f"\nPor los ascensores fuera de servicio: {ascensores.texto_pisos(extra) if extra else 'ninguno (hay otro camino)'}."
        self.lbl_aislados.setText(t)

    def _muestra_reto(self, *_):
        self.lbl_reto.setText(self.retos[self.cb_reto.currentIndex()]["nota"])

    def _toggle_asc(self, clave, estado):
        self.sim.poner_ascensor(clave, estado)
        self._actualizar_aislados()
        self._refrescar()

    def _sync_ascensores(self):
        for clave, c in self.chk_asc.items():
            c.blockSignals(True)
            c.setChecked(any(i in self.sim.fuera for i in self.sim.asc_clave[clave]["nodos"]))
            c.blockSignals(False)
        self._actualizar_aislados()

    def _toggle_muros(self, estado):
        self.vista.muros = estado
        self._refrescar()

    def cargar_reto(self):
        r = self.retos[self.cb_reto.currentIndex()]
        self.sim.reiniciar(todo=True)
        for clave in r["fuera"]:
            self.sim.poner_ascensor(clave, True)
        self._sync_ascensores()
        self.chk.setChecked(True)
        self._asignar("origen", r["origen"])
        self._asignar("destino", r["destino"])
        self.iniciar()

    def _leyenda(self):
        leyenda = "".join(f"<span style='color:{c}'>&#9632;</span> {i + 1} &nbsp;" for i, c in enumerate(COL_PISO))
        lbl = QtWidgets.QLabel(
            f"<small>Pisos: {leyenda}<br><span style='color:{COL_ESC}'>&#9632;</span> escalera (no accesible) &nbsp; "
            f"<span style='color:{COL_ASC}'>&#9632;</span> ascensor<br>"
            "<span style='color:#1565c0'>&#9711;</span> origen &nbsp; <span style='color:#c62828'>&#9711;</span> destino "
            "&nbsp; <span style='color:#e91e8c'>&#9679;</span> caminante<br>"
            "3D: arrastrar = rotar &nbsp; rueda = zoom &nbsp; boton central o Ctrl+arrastrar = mover</small>")
        return lbl

    def eventFilter(self, obj, ev):
        if ev.type() == QtCore.QEvent.FocusIn and obj in (self.le_o, self.le_d):
            self._rol = "origen" if obj is self.le_o else "destino"
            self._buscar()
        return super().eventFilter(obj, ev)

    def _cambia_modo(self, _i):
        self.vista.modo = self.cb_modo.currentData()
        self._refrescar()

    def _cambia_piso_ver(self, _i):
        self.vista.piso_ver = self.cb_ver.currentData()
        self._refrescar()

    def _cambia_piso_plano(self, _i):
        self.vista.set_piso_plano(self.cb_plano.currentData())
        self._refrescar()

    def _toggle_acc(self, estado):
        self.sim.solo_acc = estado
        self._refrescar()

    def _buscar(self, *_):
        le = self.le_o if self._rol == "origen" else self.le_d
        texto = le.text()
        pab, piso = self.cb_pab.currentData(), self.cb_piso.currentData()
        self.lista.clear()
        if not texto.strip() and pab is None and piso is None:
            self.lbl_res.setText(f"Eligiendo {self._rol.upper()}: escribe un nombre o elige pabellon / piso.")
            return
        ids = buscador.buscar(self.G, texto, n=MAX_RESULTADOS, pab=pab, piso=piso)
        for i in ids:
            it = QtWidgets.QListWidgetItem(self.G.nodos[i]["nombre"])
            it.setData(QtCore.Qt.UserRole, i)
            self.lista.addItem(it)
        extra = f" (mostrando {MAX_RESULTADOS})" if len(ids) == MAX_RESULTADOS else ""
        self.lbl_res.setText(f"Eligiendo {self._rol.upper()}: {len(ids)} resultado(s){extra}" if ids else
                             f"Eligiendo {self._rol.upper()}: sin resultados. Prueba otra palabra o quita filtros.")

    def _elegir_item(self, item):
        rol = self._rol
        self._asignar(rol, item.data(QtCore.Qt.UserRole))
        if rol == "origen" and not self.sim.destino:
            self.le_d.setFocus()
        elif rol == "destino" and not self.sim.origen:
            self.le_o.setFocus()
        self._refrescar()

    def _elegir_primero(self):
        if self.lista.count():
            self._elegir_item(self.lista.item(0))

    def _asignar(self, rol, nid):
        if self.sim.estado in ("buscando", "caminando"):
            self.sim.reiniciar(todo=False)
        setattr(self.sim, rol, nid)
        le = self.le_o if rol == "origen" else self.le_d
        le.setText(self.G.nodos[nid]["nombre"])
        le.setCursorPosition(0)
        piso = self.G.nodos[nid]["piso"]
        if piso >= 1:
            self.cb_plano.setCurrentIndex(piso - 1)
        self.sim.msg = f"{rol.capitalize()}: {self.G.nodos[nid]['nombre']}.  Pulsa Iniciar (espacio)."

    def buscar(self, rol, texto):
        r = buscador.buscar(self.G, texto)
        if not r:
            self.sim.msg = f"No encontre '{texto}'. Prueba: 'salon 51', 'cub 54', 'bano', 'ascensor J', 'kata'."
        else:
            self._asignar(rol, r[0])
        self._refrescar()

    def _clic_plano(self, rol, nid):
        self._asignar(rol, nid)
        self.sim.msg += "  Origen/destino actualizado."
        self._refrescar()

    def iniciar(self):
        self.sim.iniciar()
        self._refrescar()

    def sim_barrera(self):
        self.sim.barrera_tramo()
        self._refrescar()

    def sim_asc(self):
        self.sim.ascensor_fuera()
        self._sync_ascensores()
        self._refrescar()

    def reiniciar(self):
        self.sim.reiniciar(todo=True)
        self.le_o.clear()
        self.le_d.clear()
        self._sync_ascensores()
        self._refrescar()

    def ejemplo(self):
        op = generador.opciones_destino(self.G)
        self.sim.reiniciar(todo=True)
        self._sync_ascensores()
        self._asignar("origen", op["Entrada Av. Alonso de Molina"])
        self._asignar("destino", op["Pabellon H - piso 3"])
        self.iniciar()

    def _refrescar(self):
        self.vista.actualizar(self.sim)
        N, s = self.G.nodos, self.sim
        modo = "SOLO ACCESIBLE" if s.solo_acc else "TODAS LAS RUTAS (con escaleras)"
        piso_w = f"   |   piso del caminante: {self.vista.piso_caminante}" if self.vista.piso_caminante else ""
        self.lbl_msg.setText(s.msg)
        self.lbl_info.setText(
            f"Origen: {N[s.origen]['nombre'] if s.origen else '-'}    Destino: {N[s.destino]['nombre'] if s.destino else '-'}"
            f"    Modo: {modo}\nNodos expandidos por A*: {s.n_exp}   |   recorrido: {s.distancia_recorrida():.0f} m"
            f"   |   recalculos: {s.recalculos}{piso_w}")

    def tick(self):
        v = self.s_v.value()
        if self.sim.tick(pasos_busqueda=v, dt=0.045, mult=v / 2.0):
            if self.chk_seguir.isChecked() and self.sim.estado == "caminando":
                f = self.vista.piso_nodo_caminante(self.sim)
                if f and f >= 1 and f != self.vista.piso_plano:
                    self.cb_plano.setCurrentIndex(f - 1)
            self._refrescar()

    def capturar(self, ruta):
        self._refrescar()
        for _ in range(4):
            QtWidgets.QApplication.processEvents()
        self.grab().save(str(ruta))

    def closeEvent(self, ev):
        self.timer.stop()
        super().closeEvent(ev)


def preparar(app):
    app.setStyle("Fusion")
    app.styleHints().setColorScheme(QtCore.Qt.ColorScheme.Light)
    pal = QtGui.QPalette()
    for rol, col in ((QtGui.QPalette.Window, "#f3f4f6"), (QtGui.QPalette.WindowText, "#111111"),
                     (QtGui.QPalette.Base, "#ffffff"), (QtGui.QPalette.AlternateBase, "#f3f4f6"),
                     (QtGui.QPalette.Text, "#111111"), (QtGui.QPalette.Button, "#e5e7eb"),
                     (QtGui.QPalette.ButtonText, "#111111"), (QtGui.QPalette.Highlight, "#2563eb"),
                     (QtGui.QPalette.HighlightedText, "#ffffff"), (QtGui.QPalette.PlaceholderText, "#7a7f87")):
        pal.setColor(rol, QtGui.QColor(col))
    app.setPalette(pal)
    pg.setConfigOptions(antialias=True)


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


def main():
    if "--prueba" in sys.argv:
        salida = CARPETA / "capturas"
        if "--salida" in sys.argv:
            salida = Path(sys.argv[sys.argv.index("--salida") + 1])
        prueba(salida)
        return
    app = QtWidgets.QApplication(sys.argv)
    preparar(app)
    w = App()
    w.resize(1650, 940)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
