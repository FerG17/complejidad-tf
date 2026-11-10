"""
Dibujo.  Izquierda: plano oficial 2D del piso elegido (pyqtgraph).  Derecha: grafo 3D con OpenGL (GPU).

Vista 3D (modos):
  Auto            -> sigue la ruta: muestra por dentro SOLO los pabellones por donde pasa y hace zoom ahi
  Campus completo -> todo el campus: cada pabellon como edificio (muros por piso, columnas en las esquinas, techo)
  Pabellon X      -> interior de un solo pabellon, con zoom
  "Ver piso"      -> filtra un solo piso (0 = todos)
Los pabellones que no se estan viendo por dentro aparecen como masas tenues, y el plano del campus hace de suelo.

Las capas estaticas (aristas, cascarones, salas) se reensamblan solo cuando cambia el modo, el piso o la ruta;
lo que se mueve (expandidos, ruta, caminante, barreras) son items pequenos que se actualizan en cada paso.
Mouse en el 3D: arrastrar = rotar | rueda = zoom | boton central o Ctrl+arrastrar = mover.
"""
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from OpenGL import GL
from PySide6 import QtCore, QtGui, QtWidgets

from generador import ESCALA

CAPA = {GL.GL_DEPTH_TEST: False, GL.GL_BLEND: True, GL.GL_CULL_FACE: False,
        "glBlendFuncSeparate": (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE_MINUS_SRC_ALPHA)}

ZEXAG_CAMPUS = 2.0
ALTO_PISO = 3.5
COL_PISO = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#d62728", "#8c564b", "#17becf"]
COL_EXT = "#7a869a"
COL_ESC, COL_ASC = "#d62828", "#1b9e3e"
COL_COLUMNA, COL_MURO, COL_TECHO = "#334155", "#64748b", "#94a3b8"
VERT = ("escalera", "escalera_ext", "ascensor")
COL_TIPO = {"pasillo": "#9aa7b8", "peatonal": "#3b6fb6", "rampa": "#d4a017", "puerta": "#f28c1b",
            "pasaje": "#2a9d8f", "escalera": COL_ESC, "escalera_ext": COL_ESC, "ascensor": COL_ASC}
PESO_CLIC = {"zona": 1.0, "ascensor": 1.0, "escalera": 1.0, "entrada_accesible": 1.0, "entrada_campus": 1.0,
             "puerta": 1.3}
FONDO_3D = (247, 249, 252)
PISOS_MAX = 7
CIRCULARES = {"I"}
MARGEN_HUELLA = 1.5
SUELO_PX = (20, 790, 250, 780)


def col_piso(p):
    return COL_EXT if p <= 0 else COL_PISO[(p - 1) % len(COL_PISO)]


def rgba(hexa, a=1.0):
    c = QtGui.QColor(hexa)
    return (c.redF(), c.greenF(), c.blueF(), a)


def qcolor(hexa, a=1.0):
    c = QtGui.QColor(hexa)
    c.setAlphaF(a)
    return c


def _hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return np.array(pts, float)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1], float)


def _rectangulo(pts, margen):
    """Rectangulo orientado de area minima que contiene los puntos (esquinas en sentido antihorario)."""
    h = _hull(pts)
    mejor = None
    for i in range(len(h)):
        d = h[(i + 1) % len(h)] - h[i]
        a = np.arctan2(d[1], d[0])
        c, s = np.cos(a), np.sin(a)
        M = np.array([[c, -s], [s, c]])
        q = h @ M
        mn, mx = q.min(0) - margen, q.max(0) + margen
        area = np.prod(mx - mn)
        if mejor is None or area < mejor[0]:
            mejor = (area, M, mn, mx)
    _, M, mn, mx = mejor
    esq = np.array([[mn[0], mn[1]], [mx[0], mn[1]], [mx[0], mx[1]], [mn[0], mx[1]]])
    return esq @ M.T


def _circulo(pts, margen, lados=40):
    c = pts.mean(0)
    r = np.hypot(*(pts - c).T).max() + margen
    t = np.linspace(0, 2 * np.pi, lados, endpoint=False)
    return np.c_[c[0] + r * np.cos(t), c[1] + r * np.sin(t)]


class _Malla:
    """Acumula la geometria de los cascarones: superficies translucidas, aristas y columnas."""

    def __init__(self, zex):
        self.zex = zex
        self.v, self.f, self.c, self.nv = [], [], [], 0
        self.bp, self.bc, self.kp, self.kc = [], [], [], []

    def _z(self, H, z):
        return np.c_[H, np.full(len(H), z * self.zex)]

    def anillo(self, H, z, col):
        v = self._z(H, z)
        a = np.vstack([v, v[:1]])
        seg = np.repeat(a, 2, axis=0)[1:-1]
        self.bp.append(seg)
        self.bc.append(np.tile(col, (len(seg), 1)))

    def losa(self, H, z, col, borde):
        n = len(H)
        self.v.append(self._z(H, z))
        self.f.append(np.array([[self.nv, self.nv + k, self.nv + k + 1] for k in range(1, n - 1)]))
        self.c.append(np.tile(col, (n - 2, 1)))
        self.nv += n
        self.anillo(H, z, borde)

    def muro(self, H, z0, z1, col):
        n = len(H)
        self.v += [self._z(H, z0), self._z(H, z1)]
        caras = []
        for i in range(n):
            j = (i + 1) % n
            caras += [[self.nv + i, self.nv + j, self.nv + n + j], [self.nv + i, self.nv + n + j, self.nv + n + i]]
        self.f.append(np.array(caras))
        self.c.append(np.tile(col, (len(caras), 1)))
        self.nv += 2 * n

    def columnas(self, H, idx, z0, z1, col):
        for i in idx:
            self.kp.append(np.array([[H[i, 0], H[i, 1], z0 * self.zex], [H[i, 0], H[i, 1], z1 * self.zex]]))
            self.kc.append(np.tile(col, (2, 1)))


class Plano(pg.PlotWidget):
    """PlotWidget que conserva la proporcion del plano (sin franjas blancas)."""
    RELACION = 503 / 740

    def __init__(self):
        super().__init__(background="w")
        sp = self.sizePolicy()
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return int(w * self.RELACION) + 26


VACIO3 = np.empty((0, 3))


class Vista(QtCore.QObject):
    """Contiene los dos widgets: w2d (plano) y w3d (OpenGL); la ventana decide donde ponerlos."""
    clic = QtCore.Signal(str, str)

    def __init__(self, G, plano):
        super().__init__()
        self.G = G
        self.modo = "Auto"
        self.piso_ver = 0
        self.piso_plano = 1
        self.zex = ZEXAG_CAMPUS
        self.muros = True
        self.piso_caminante = None
        self._firma = None
        self._firma_region = None
        self._indexar()
        self._crear2d(plano)
        self._crear3d(plano)
        self.set_piso_plano(1)

    def _indexar(self):
        N = self.G.nodos
        self.ids = list(N)
        self.k = {i: j for j, i in enumerate(self.ids)}
        nodos = [N[i] for i in self.ids]
        self.X2 = np.array([n["x_px"] for n in nodos])
        self.Y2 = np.array([n["y_px"] for n in nodos])
        self.X3 = np.array([n["x"] for n in nodos])
        self.Y3 = -np.array([n["y"] for n in nodos])
        self.Z3 = np.array([n["z"] for n in nodos])
        self.PISO = np.array([n["piso"] for n in nodos])
        self.TIPO = np.array([n["tipo"] for n in nodos])
        self.PAB = np.array([n["pab"] for n in nodos])
        self.PESO = np.array([PESO_CLIC.get(n["tipo"], 1.6) for n in nodos])
        self.pabs = sorted({n["pab"] for n in nodos if n["pab"]})
        self.bbox = {}
        for p in self.pabs:
            m = self.PAB == p
            self.bbox[p] = (self.X3[m].min(), self.X3[m].max(), self.Y3[m].min(), self.Y3[m].max())

        g3, e2 = {}, {}
        self.asc_aristas = []
        for e in self.G.aristas:
            a, b = N[e["a"]], N[e["b"]]
            tag = "".join(sorted({x for x in (a["pab"], b["pab"]) if x}))
            pmin = min(a["piso"], b["piso"])
            vert = e["tipo"] in VERT and a["piso"] != b["piso"]
            if e["tipo"] in ("escalera", "escalera_ext"):
                col = COL_ESC
            elif e["tipo"] == "ascensor":
                col = COL_ASC
                self.asc_aristas.append((self.k[e["a"]], self.k[e["b"]]))
            else:
                col = col_piso(pmin)
            pts, cols = g3.setdefault((tag, pmin, vert), ([], []))
            pts += [(a["x"], -a["y"], a["z"]), (b["x"], -b["y"], b["z"])]
            cols += [rgba(col, 0.9)] * 2
            if a["piso"] == b["piso"]:
                clave = a["piso"]
            elif {a["piso"], b["piso"]} == {0, 1}:
                clave = 1
            else:
                continue
            e2.setdefault((clave, e["tipo"]), []).append((a["x_px"], a["y_px"], b["x_px"], b["y_px"]))
        self.grupos = {k: (np.array(p, float), np.array(c, float)) for k, (p, c) in g3.items()}
        self.e2 = {}
        for k, v in e2.items():
            v = np.array(v, float)
            self.e2[k] = (v[:, [0, 2]].ravel(), v[:, [1, 3]].ravel())

        self.huella, self.col_idx, self.npisos, self.zbase, self.zonas = {}, {}, {}, {}, {}
        for p in self.pabs:
            m = self.PAB == p
            pts = np.c_[self.X3[m], self.Y3[m]]
            if p in CIRCULARES:
                H = _circulo(pts, MARGEN_HUELLA)
                self.col_idx[p] = list(range(0, len(H), 5))
            else:
                H = _rectangulo(pts, MARGEN_HUELLA)
                self.col_idx[p] = [0, 1, 2, 3]
            self.huella[p] = H
            self.npisos[p] = int(self.PISO[m].max())
            self.zbase[p] = float(self.Z3[m & (self.PISO == 1)].mean())
            for pi in range(1, self.npisos[p] + 1):
                self.zonas[(p, pi)] = np.where(m & (self.PISO == pi) & (self.TIPO == "zona"))[0]

    def _crear2d(self, plano):
        self.w2d = Plano()
        pi = self.w2d.getPlotItem()
        pi.hideAxis("left")
        pi.hideAxis("bottom")
        pi.hideButtons()
        self.vb = pi.vb
        self.vb.setAspectLocked(True)
        self.vb.invertY(True)
        self.vb.setMenuEnabled(False)
        img = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap(plano))
        img.setZValue(-100)
        self.vb.addItem(img)
        self.vb.setRange(xRange=(30, 770), yRange=(262, 765), padding=0)
        self.titulo2d = pi
        self.cur_ext, self.cur_piso = {}, {}
        for tipo, col in COL_TIPO.items():
            self.cur_ext[tipo] = pg.PlotCurveItem(connect="pairs", pen=pg.mkPen(qcolor(col, 0.85), width=1.2))
            self.cur_piso[tipo] = pg.PlotCurveItem(connect="pairs", pen=pg.mkPen(qcolor(col, 0.95), width=1.6))
            for c, z in ((self.cur_ext[tipo], 3), (self.cur_piso[tipo], 4)):
                c.setZValue(z)
                self.vb.addItem(c)
            xy = self.e2.get((0, tipo))
            if xy:
                self.cur_ext[tipo].setData(*xy)
        ext = np.where(self.PISO == 0)[0]
        self.pts_ext = pg.ScatterPlotItem(x=self.X2[ext], y=self.Y2[ext], size=3, pen=None, brush=qcolor("#1f4fa0"))
        self.pts_ext.setZValue(5)
        self.pts_piso = pg.ScatterPlotItem(size=4, pen=None)
        self.pts_piso.setZValue(6)
        self.asc2 = pg.ScatterPlotItem(symbol="t", size=12, pen=pg.mkPen("k", width=0.8), brush=qcolor(COL_ASC))
        self.asc2.setZValue(7)
        for it in (self.pts_ext, self.pts_piso, self.asc2):
            self.vb.addItem(it)
        self.letras2 = {}
        for p in self.pabs:
            t = pg.TextItem(p, color="k", anchor=(0.5, 0.5), fill=qcolor("#ffffff", 0.75))
            t.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
            t.setZValue(9)
            self.vb.addItem(t)
            self.letras2[p] = t

        self.exp2 = pg.ScatterPlotItem(size=5, pen=None, brush=qcolor("#f6a21e"))
        self.ruta2 = pg.PlotCurveItem(connect="pairs", pen=pg.mkPen("#0b8a3e", width=4))
        self.ruta2b = pg.PlotCurveItem(connect="pairs", pen=pg.mkPen(qcolor("#0b8a3e", 0.35), width=3,
                                                                     style=QtCore.Qt.DashLine))
        self.rast2 = pg.PlotCurveItem(pen=pg.mkPen("#7b2cbf", width=4))
        self.walk2 = pg.ScatterPlotItem(size=15, pen=pg.mkPen("w", width=2), brush=qcolor("#e91e8c"))
        self.bloq2 = pg.ScatterPlotItem(symbol="x", size=16, pen=pg.mkPen("#d62828", width=3.5), brush=None)
        self.org2 = pg.ScatterPlotItem(size=22, pen=pg.mkPen("#1565c0", width=3), brush=None)
        self.des2 = pg.ScatterPlotItem(size=22, pen=pg.mkPen("#c62828", width=3), brush=None)
        for z, it in enumerate((self.exp2, self.ruta2b, self.ruta2, self.rast2, self.bloq2, self.walk2, self.org2,
                                self.des2), start=10):
            it.setZValue(z)
            self.vb.addItem(it)
        self.w2d.scene().sigMouseClicked.connect(self._click2d)

    def _suelo(self, plano):
        img = QtGui.QImage(plano).convertToFormat(QtGui.QImage.Format_RGBA8888)
        w, h = img.width(), img.height()
        arr = np.frombuffer(img.constBits(), np.uint8).reshape(h, img.bytesPerLine() // 4, 4)[:, :w]
        x0, x1, y0, y1 = SUELO_PX
        recorte = arr[y0:min(y1, h), x0:min(x1, w)].copy()
        recorte[..., 3] = 235
        item = gl.GLImageItem(np.ascontiguousarray(recorte.transpose(1, 0, 2)), smooth=True, glOptions=CAPA)
        t = pg.Transform3D()
        t.translate(x0 * ESCALA, -y0 * ESCALA, 0)
        t.scale(ESCALA, -ESCALA, 1)
        item.setTransform(t)
        return item

    def _crear3d(self, plano):
        self.w3d = gl.GLViewWidget()
        self.w3d.setBackgroundColor(FONDO_3D)
        self.w3d.setCameraPosition(distance=300, elevation=28, azimuth=-62)
        V = self.w3d

        def add(it, z=0):
            it.setDepthValue(z)
            V.addItem(it)
            return it
        self.g_suelo = add(self._suelo(plano), -100)
        self.g_losas = add(gl.GLMeshItem(vertexes=np.zeros((3, 3)), faces=np.array([[0, 1, 2]]),
                                         faceColors=np.zeros((1, 4)), smooth=False, computeNormals=False,
                                         glOptions=CAPA), -20)
        self.g_bordes = add(gl.GLLinePlotItem(mode="lines", width=1.4, antialias=True, glOptions=CAPA), -10)
        self.g_cols = add(gl.GLLinePlotItem(mode="lines", width=3.2, antialias=True, glOptions=CAPA), -9)
        self.g_lineas = add(gl.GLLinePlotItem(mode="lines", width=1.2, antialias=True, glOptions=CAPA), -5)
        self.g_vert = add(gl.GLLinePlotItem(mode="lines", width=3.5, antialias=True, glOptions=CAPA), -4)
        self.g_salas = add(gl.GLScatterPlotItem(size=5, pxMode=True, glOptions=CAPA), -3)
        self.g_losas.setVisible(False)
        self.letras3 = {}
        for p in self.pabs:
            t = gl.GLTextItem(pos=(0, 0, 0), text=p, color=QtGui.QColor("#222"),
                              font=QtGui.QFont("Segoe UI", 13, QtGui.QFont.Bold))
            V.addItem(t)
            self.letras3[p] = t

        self.g_exp = add(gl.GLScatterPlotItem(size=4, color=rgba("#f6a21e"), pxMode=True, glOptions=CAPA), 5)
        self.g_ruta = add(gl.GLLinePlotItem(mode="line_strip", width=4.5, color=rgba("#0b8a3e"), antialias=True,
                                            glOptions=CAPA), 6)
        self.g_rast = add(gl.GLLinePlotItem(mode="line_strip", width=4.5, color=rgba("#7b2cbf"), antialias=True,
                                            glOptions=CAPA), 7)
        self.g_fuera = add(gl.GLLinePlotItem(mode="lines", width=6, color=rgba("#d62828"), antialias=True,
                                             glOptions=CAPA), 7)
        self.g_bloq = add(gl.GLScatterPlotItem(size=14, color=rgba("#d62828"), pxMode=True,
                                               glOptions=CAPA), 8)
        self.g_walk = add(gl.GLScatterPlotItem(size=16, color=rgba("#e91e8c"), pxMode=True,
                                               glOptions=CAPA), 9)
        self.g_od = add(gl.GLScatterPlotItem(size=20, pxMode=True, glOptions=CAPA), 10)
        for it in (self.g_exp, self.g_ruta, self.g_rast, self.g_fuera, self.g_bloq, self.g_walk, self.g_od):
            it.setVisible(False)

    def set_piso_plano(self, f):
        f = max(1, min(PISOS_MAX, int(f)))
        self.piso_plano = f
        for tipo, c in self.cur_piso.items():
            xy = self.e2.get((f, tipo))
            c.setData(*xy) if xy else c.setData([], [])
        for tipo, c in self.cur_ext.items():
            c.setPen(pg.mkPen(qcolor(COL_TIPO[tipo], 0.85 if f == 1 else 0.3), width=c.opts["pen"].widthF()))
        self.pts_ext.setBrush(qcolor("#1f4fa0", 1.0 if f == 1 else 0.3))
        sel = np.where(self.PISO == f)[0]
        self.pts_piso.setData(x=self.X2[sel], y=self.Y2[sel], size=4, pen=None, brush=qcolor(col_piso(f)))
        asc = np.where((self.TIPO == "ascensor") & ((self.PISO == f) | (self.PISO == 0)))[0]
        self.asc2.setData(x=self.X2[asc], y=self.Y2[asc])
        self.clic_idx = np.concatenate([np.where(self.PISO == 0)[0], sel])
        for p, t in self.letras2.items():
            ns = sel[self.PAB[sel] == p]
            t.setVisible(bool(len(ns)))
            if len(ns):
                t.setPos(self.X2[ns].mean(), self.Y2[ns].mean())
        nom = "exterior y primer piso" if f == 1 else f"piso {f}"
        self.titulo2d.setTitle(f"Plano del campus - {nom}   (clic izq = origen, clic der = destino)", size="9pt")

    def _click2d(self, ev):
        if ev.double() or ev.button() not in (QtCore.Qt.LeftButton, QtCore.Qt.RightButton):
            return
        if not self.vb.sceneBoundingRect().contains(ev.scenePos()):
            return
        p = self.vb.mapSceneToView(ev.scenePos())
        idx = self.clic_idx
        d = np.hypot(self.X2[idx] - p.x(), self.Y2[idx] - p.y()) * self.PESO[idx]
        j = int(np.argmin(d))
        radio = 16 * self.vb.viewPixelSize()[0]
        if d[j] > radio:
            return
        self.clic.emit("origen" if ev.button() == QtCore.Qt.LeftButton else "destino", self.ids[idx[j]])

    def _seleccion(self, sim):
        N = self.G.nodos
        if self.modo == "Campus":
            return set(), []
        if self.modo != "Auto":
            return {self.modo}, []
        ids = list(sim.ruta) if sim.ruta else [i for i in (sim.origen, sim.destino) if i]
        return {N[i]["pab"] for i in ids if N[i]["pab"]}, ids

    def _region(self, sel, ids):
        N = self.G.nodos
        if sel:
            xs, ys, zs = [], [], [0.0]
            for p in sel:
                b = self.bbox[p]
                xs += [b[0], b[1]]
                ys += [b[2], b[3]]
                zs.append(self.zbase[p] + self.npisos[p] * ALTO_PISO)
            for i in ids:
                xs.append(N[i]["x"])
                ys.append(-N[i]["y"])
            zoom = True
        else:
            xs, ys, zs, zoom = self.X3, self.Y3, [max(self.zbase[p] + self.npisos[p] * ALTO_PISO for p in self.pabs)], False
        m = 0.06 * max(max(xs) - min(xs), max(ys) - min(ys)) + 4
        x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
        zmax = max(max(zs), ALTO_PISO) + 2
        zex = ZEXAG_CAMPUS if not zoom else float(np.clip(0.55 * max(x1 - x0, y1 - y0) / zmax, 1.2, 3.0))
        return x0, x1, y0, y1, zmax, zex

    def _cascaron(self, M, p, pv, detalle):
        H, n, zb = self.huella[p], self.npisos[p], self.zbase[p]
        cols = self.col_idx[p]
        if detalle:
            pisos = range(1, n + 1) if not pv else ([pv] if pv <= n else [])
            for k in pisos:
                z = zb + (k - 1) * ALTO_PISO
                M.losa(H, z, rgba(col_piso(k), 0.13), rgba(col_piso(k), 0.85))
                if self.muros:
                    M.muro(H, z, z + ALTO_PISO, rgba(col_piso(k), 0.10))
            if not pisos:
                return
            z0 = zb + (pisos[0] - 1) * ALTO_PISO
            z1 = zb + pisos[-1] * ALTO_PISO
            M.losa(H, z1, rgba(COL_TECHO, 0.20), rgba(COL_MURO, 0.9))
            M.columnas(H, cols, z0, z1, rgba(COL_COLUMNA, 0.9))
        elif not pv:
            z1 = zb + n * ALTO_PISO
            if self.muros:
                M.muro(H, zb, z1, rgba(COL_MURO, 0.06))
            M.losa(H, z1, rgba(COL_TECHO, 0.10), rgba(COL_MURO, 0.45))
            M.anillo(H, zb, rgba(COL_MURO, 0.45))
            M.columnas(H, cols, zb, z1, rgba(COL_COLUMNA, 0.45))

    def _aplicar_capas(self, sel, recentrar, ids):
        pv = self.piso_ver
        x0, x1, y0, y1, zmax, self.zex = self._region(sel, ids)
        zex = self.zex
        ext_vis = self.modo in ("Auto", "Campus")
        lin, col, lv, cv = [], [], [], []
        for (tag, pmin, vert), (p, c) in self.grupos.items():
            if tag == "":
                vis = ext_vis
            else:
                vis = any(ch in sel for ch in tag)
                if vis and pv:
                    vis = pmin == 0 or pmin == pv or (vert and pmin + 1 == pv)
            if vis:
                q = p.copy()
                q[:, 2] *= zex
                (lv if vert else lin).append(q)
                (cv if vert else col).append(c)
        self._set_lineas(self.g_lineas, lin, col)
        self._set_lineas(self.g_vert, lv, cv)

        M = _Malla(zex)
        for p in self.pabs:
            self._cascaron(M, p, pv, p in sel or not sel)
        if M.v:
            self.g_losas.setMeshData(vertexes=np.vstack(M.v), faces=np.vstack(M.f), faceColors=np.vstack(M.c),
                                     smooth=False, computeNormals=False)
        self.g_losas.setVisible(bool(M.v))
        self._set_lineas(self.g_bordes, M.bp, M.bc)
        self._set_lineas(self.g_cols, M.kp, M.kc)

        sp, sc = [], []
        for (p, pi), zonas in self.zonas.items():
            if p in sel and len(zonas) and (pv == 0 or pv == pi):
                sp.append(np.c_[self.X3[zonas], self.Y3[zonas], self.Z3[zonas] * zex])
                sc.append(np.tile(rgba(col_piso(pi), 1.0), (len(zonas), 1)))
        if sp:
            self.g_salas.setData(pos=np.vstack(sp), color=np.vstack(sc), size=5)
        self.g_salas.setVisible(bool(sp))
        for p, t in self.letras3.items():
            t.setVisible(not pv or p in sel or not sel)
            b = self.bbox[p]
            t.setData(pos=((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (self.zbase[p] + self.npisos[p] * ALTO_PISO + 4) * zex))
        if recentrar:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            ext = max(x1 - x0, y1 - y0, zmax * zex)
            self.w3d.setCameraPosition(pos=pg.Vector(cx, cy, zmax * zex * 0.5), distance=ext * (1.5 if sel else 1.0))

    @staticmethod
    def _set_lineas(item, pos, col):
        if pos:
            item.setData(pos=np.vstack(pos), color=np.vstack(col))
        item.setVisible(bool(pos))

    def _xyz(self, ids):
        j = [self.k[i] for i in ids]
        return np.c_[self.X3[j], self.Y3[j], self.Z3[j] * self.zex] if j else VACIO3

    def _set(self, item, pos, **kw):
        if len(pos):
            item.setData(pos=pos, **kw)
        item.setVisible(len(pos) > 0)

    def actualizar(self, sim):
        """Actualiza lo estatico si hace falta y todos los items dinamicos. Devuelve True si cambiaron las capas."""
        N = self.G.nodos
        sel, ids = self._seleccion(sim)
        region = (self.modo, tuple(sorted(sel)), (id(sim.ruta), sim.origen, sim.destino) if self.modo == "Auto" else None)
        firma = (region, self.piso_ver, self.muros)
        cambio = firma != self._firma
        if cambio:
            self._aplicar_capas(sel, region != self._firma_region, ids)
            self._firma, self._firma_region = firma, region

        f = self.piso_plano
        ex = sim.expandidos
        jx = np.array([self.k[i] for i in ex], int)
        if len(jx):
            m = (self.PISO[jx] == 0) | (self.PISO[jx] == f)
            self.exp2.setData(x=self.X2[jx[m]], y=self.Y2[jx[m]], size=5, pen=None, brush=qcolor("#f6a21e"))
        else:
            self.exp2.setData([], [])
        self._set(self.g_exp, self._xyz(ex))

        ruta = sim.ruta or []
        jr = np.array([self.k[i] for i in ruta], int)
        if len(jr) > 1:
            en = (self.PISO[jr] == 0) | (self.PISO[jr] == f)
            seg = en[:-1] & en[1:]
            xa, ya = self.X2[jr[:-1]], self.Y2[jr[:-1]]
            xb, yb = self.X2[jr[1:]], self.Y2[jr[1:]]

            def pares(m):
                return np.c_[xa[m], xb[m]].ravel(), np.c_[ya[m], yb[m]].ravel()
            self.ruta2.setData(*pares(seg))
            self.ruta2b.setData(*pares(~seg))
        else:
            self.ruta2.setData([], [])
            self.ruta2b.setData([], [])
        self._set(self.g_ruta, self._xyz(ruta) if len(ruta) > 1 else VACIO3)

        rec = sim.recorrido
        jc = [self.k[i] for i in rec]
        if len(jc) > 1:
            self.rast2.setData(self.X2[jc], self.Y2[jc])
        else:
            self.rast2.setData([], [])
        self._set(self.g_rast, self._xyz(rec) if len(rec) > 1 else VACIO3)

        w = sim.pos_walker()
        piso_w = None
        if w:
            self.walk2.setData(x=[w[0]], y=[w[1]], size=15, pen=pg.mkPen("w", width=2), brush=qcolor("#e91e8c"))
            self._set(self.g_walk, np.array([[w[2], -w[3], w[4] * self.zex]]))
            piso_w = int(round(w[4] / ALTO_PISO)) + 1
        else:
            self.walk2.setData([], [])
            self.g_walk.setVisible(False)

        piso_de = lambda i: N[i]["piso"] in (0, f)
        bl = [(a, b) for a, b in sim.aristas_bloq]
        mid = [((N[a]["x_px"] + N[b]["x_px"]) / 2, (N[a]["y_px"] + N[b]["y_px"]) / 2) for a, b in bl
               if piso_de(a) and piso_de(b)]
        bq = set(sim.nodos_bloq) | set(sim.fuera)
        mid += [(N[n]["x_px"], N[n]["y_px"]) for n in bq if piso_de(n)]
        self.bloq2.setData(x=[m[0] for m in mid], y=[m[1] for m in mid], symbol="x", size=16,
                           pen=pg.mkPen("#d62828", width=3.5), brush=None)
        b3 = [((N[a]["x"] + N[b]["x"]) / 2, -(N[a]["y"] + N[b]["y"]) / 2, (N[a]["z"] + N[b]["z"]) / 2) for a, b in bl]
        b3 += [(N[n]["x"], -N[n]["y"], N[n]["z"]) for n in bq]
        b3 = np.array(b3, float).reshape(-1, 3)
        b3[:, 2] *= self.zex
        self._set(self.g_bloq, b3)
        ejes = [(ia, ib) for ia, ib in self.asc_aristas if self.ids[ia] in sim.fuera and self.ids[ib] in sim.fuera]
        if ejes:
            pos = np.array([[[self.X3[j], self.Y3[j], self.Z3[j] * self.zex] for j in par] for par in ejes]).reshape(-1, 3)
            self.g_fuera.setData(pos=pos)
        self.g_fuera.setVisible(bool(ejes))

        for it2, nid in ((self.org2, sim.origen), (self.des2, sim.destino)):
            if nid and self.PISO[self.k[nid]] in (0, f):
                it2.setData(x=[self.X2[self.k[nid]]], y=[self.Y2[self.k[nid]]])
            else:
                it2.setData([], [])
        od = [i for i in (sim.origen, sim.destino) if i]
        if od:
            col = np.array([rgba("#1565c0") if i == sim.origen else rgba("#c62828") for i in od])
            self.g_od.setData(pos=self._xyz(od), color=col, size=20)
        self.g_od.setVisible(bool(od))
        self.piso_caminante = piso_w
        return cambio

    def piso_nodo_caminante(self, sim):
        if not sim.ruta:
            return None
        return self.G.nodos[sim.ruta[min(sim.walker_i, len(sim.ruta) - 1)]]["piso"]
