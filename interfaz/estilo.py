"""Colores, constantes de dibujo y widgets base compartidos por la ventana y las vistas 2D/3D."""
import numpy as np
import pyqtgraph as pg
from OpenGL import GL
from PySide6 import QtCore, QtGui

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
