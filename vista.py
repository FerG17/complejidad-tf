"""
Dibujo.  Izquierda: plano oficial 2D con el grafo (piso 1).  Derecha: grafo 3D.

Vista 3D (modos):
  Auto            -> sigue la ruta: muestra por dentro SOLO los pabellones por donde pasa y hace zoom ahi
  Campus completo -> todo el campus con losas (una por piso, cada piso de un color)
  Pabellon X      -> interior de un solo pabellon, con zoom
  "Ver piso"      -> filtra un solo piso (0 = todos)

Rapidez: las capas estaticas (aristas, losas, salas) se crean UNA vez y solo se prenden/apagan;
lo que se mueve (nodos expandidos, ruta, caminante, barreras, textos) se dibuja con blitting,
asi que cada paso de la animacion NO redibuja todo el grafo.
"""
import textwrap

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.image import imread
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

ZEXAG_CAMPUS = 6.0
ALTO_PISO = 3.5
COL_PISO = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#d62728", "#8c564b", "#17becf"]   # pisos 1..7
COL_EXT = "#7a869a"
COL_ESC, COL_ASC = "#d62828", "#1b9e3e"
VERT = ("escalera", "escalera_ext", "ascensor")
COL_TIPO = {"pasillo": "#9aa7b8", "peatonal": "#3b6fb6", "rampa": "#d4a017", "puerta": "#f28c1b",
            "pasaje": "#2a9d8f", "escalera": COL_ESC, "escalera_ext": COL_ESC, "ascensor": COL_ASC}


def col_piso(p):
    return COL_EXT if p <= 0 else COL_PISO[(p - 1) % len(COL_PISO)]


def _hull(pts):
    """Envolvente convexa (monotone chain)."""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

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
    return lo[:-1] + up[:-1]


class Blit:
    """Dibuja solo los artistas animados sobre un fondo guardado (si el backend lo permite)."""

    def __init__(self, fig):
        self.fig, self.cv = fig, fig.canvas
        self.arts, self.bg = [], None
        self.activo = hasattr(self.cv, "copy_from_bbox")
        self.cv.mpl_connect("draw_event", self._on_draw)

    def add(self, a):
        if self.activo:
            a.set_animated(True)
        self.arts.append(a)
        return a

    def _on_draw(self, ev):
        if ev is not None and ev.canvas is not self.cv:
            return
        if self.activo:
            self.bg = self.cv.copy_from_bbox(self.fig.bbox)
            self._pintar()

    def _pintar(self):
        for a in self.arts:
            self.fig.draw_artist(a)

    def update(self):
        if not self.activo or self.bg is None:
            self.cv.draw_idle()
            return
        self.cv.restore_region(self.bg)
        self._pintar()
        self.cv.blit(self.fig.bbox)

    def suspender(self, si):
        """Para guardar PNG: los animados se dibujan normal."""
        if self.activo:
            for a in self.arts:
                a.set_animated(not si)


class Vista:
    def __init__(self, G, plano, fig=None):
        self.G = G
        self.fig = fig or Figure(figsize=(16, 8.8), dpi=100)
        self.fig.clf()
        self.ax2 = self.fig.add_axes([0.215, 0.36, 0.37, 0.60])
        self.ax3 = self.fig.add_axes([0.585, 0.02, 0.415, 0.96], projection="3d")
        self.blit = Blit(self.fig)
        self.modo = "Auto"       # "Auto" | "Campus" | letra de pabellon
        self.piso_ver = 0        # 0 = todos
        self._firma = None
        self._indexar()
        self._base2d(plano)
        self._base3d()
        self._dinamicos()

    # ------------------------------------------------------------------ indices
    def _indexar(self):
        N = self.G.nodos
        self.pabs = sorted({n["pab"] for n in N.values() if n["pab"]})
        self.bbox = {}
        for p in self.pabs:
            xs = [n["x"] for n in N.values() if n["pab"] == p]
            ys = [-n["y"] for n in N.values() if n["pab"] == p]
            self.bbox[p] = (min(xs), max(xs), min(ys), max(ys))
        # aristas agrupadas por (tag de pabellones, piso minimo, es_vertical)
        self.grupos = {}
        for e in self.G.aristas:
            a, b = N[e["a"]], N[e["b"]]
            tag = "".join(sorted({x for x in (a["pab"], b["pab"]) if x}))
            pmin = min(a["piso"], b["piso"])
            vert = e["tipo"] in VERT and a["piso"] != b["piso"]
            if e["tipo"] in ("escalera", "escalera_ext"):
                col = COL_ESC
            elif e["tipo"] == "ascensor":
                col = COL_ASC
            else:
                col = col_piso(pmin)
            segs, cols = self.grupos.setdefault((tag, pmin, vert), ([], []))
            segs.append([(a["x"], -a["y"], a["z"]), (b["x"], -b["y"], b["z"])])
            cols.append(to_rgba(col, 0.9))

    # ------------------------------------------------------------------ 2D
    def _base2d(self, plano):
        ax = self.ax2
        ax.imshow(imread(plano))
        segs, cols = [], []
        for e in self.G.aristas:
            a, b = self.G.nodos[e["a"]], self.G.nodos[e["b"]]
            if a["piso"] > 1 or b["piso"] > 1:
                continue
            segs.append([(a["x_px"], a["y_px"]), (b["x_px"], b["y_px"])])
            cols.append(COL_TIPO.get(e["tipo"], "#3b6fb6"))
        ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.9, alpha=0.8, zorder=3))
        pts = [n for n in self.G.nodos.values() if n["piso"] <= 1]
        ax.scatter([n["x_px"] for n in pts], [n["y_px"] for n in pts], s=3, c="#1f4fa0", zorder=4)
        for n in self.G.nodos.values():
            if n["tipo"] == "ascensor" and n["piso"] <= 1:
                ax.scatter([n["x_px"]], [n["y_px"]], marker="^", s=40, c=COL_ASC, edgecolors="k",
                           linewidths=0.4, zorder=5)
        for p in self.pabs:
            ns = [n for n in self.G.nodos.values() if n["pab"] == p and n["piso"] == 1]
            if ns:
                ax.text(np.mean([n["x_px"] for n in ns]), np.mean([n["y_px"] for n in ns]), p,
                        fontsize=11, fontweight="bold", ha="center", va="center", zorder=6,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))
        ax.set_xlim(30, 770)
        ax.set_ylim(765, 262)
        ax.axis("off")
        ax.set_title("Plano del campus  (clic izq = origen, clic der = destino)", fontsize=10)

    # ------------------------------------------------------------------ 3D estatico
    def _base3d(self):
        ax, N = self.ax3, self.G.nodos
        ax.set_axis_off()
        ax.view_init(elev=30, azim=-62)
        self.col_aristas = {}
        for key, (segs, cols) in self.grupos.items():
            vert = key[2]
            c = Line3DCollection(segs, colors=cols, linewidths=2.0 if vert else 0.9)
            c.set_visible(False)
            ax.add_collection3d(c)
            self.col_aristas[key] = c
        self.losas, self.salas, self.letras = {}, {}, {}
        for p in self.pabs:
            pisos = sorted({n["piso"] for n in N.values() if n["pab"] == p and n["piso"] >= 1})
            for pi in pisos:
                ns = [n for n in N.values() if n["pab"] == p and n["piso"] == pi]
                h = _hull([(n["x"], -n["y"]) for n in ns])
                z = float(np.mean([n["z"] for n in ns]))
                if len(h) >= 3:
                    pol = Poly3DCollection([[(x, y, z) for x, y in h]],
                                           facecolors=to_rgba(col_piso(pi), 0.13),
                                           edgecolors=to_rgba(col_piso(pi), 0.8), linewidths=0.7)
                    pol.set_visible(False)
                    ax.add_collection3d(pol)
                    self.losas[(p, pi)] = pol
                zs = [n for n in ns if n["tipo"] == "zona"]
                if zs:
                    sc = ax.scatter([n["x"] for n in zs], [-n["y"] for n in zs], [n["z"] for n in zs],
                                    s=7, c=col_piso(pi), depthshade=False, edgecolors="none")
                    sc.set_visible(False)
                    self.salas[(p, pi)] = sc
            ns = [n for n in N.values() if n["pab"] == p]
            top = max(n["z"] for n in ns)
            self.letras[p] = ax.text(np.mean([n["x"] for n in ns]), -np.mean([n["y"] for n in ns]),
                                     top + 5, p, fontsize=10, fontweight="bold", ha="center", color="#222")
        h = [Patch(fc=to_rgba(col_piso(i), 0.5), ec=col_piso(i), label=f"Piso {i}") for i in range(1, 8)]
        h += [Line2D([], [], color=COL_ESC, lw=2, label="Escalera (no accesible)"),
              Line2D([], [], color=COL_ASC, lw=2, label="Ascensor")]
        ax.legend(handles=h, loc="upper left", fontsize=7, frameon=False, ncol=1, borderaxespad=0.2)
        self.fig.text(0.79, 0.975, "Grafo 3D", fontsize=10, ha="center", va="center")

    # ------------------------------------------------------------------ dinamicos
    def _dinamicos(self):
        a2, a3, B = self.ax2, self.ax3, self.blit
        self.exp2 = B.add(a2.scatter([], [], s=9, c="#f6a21e", zorder=6))
        self.ruta2 = B.add(a2.plot([], [], color="#0b8a3e", lw=3.2, zorder=7, solid_capstyle="round")[0])
        self.rast2 = B.add(a2.plot([], [], color="#7b2cbf", lw=3.2, zorder=8)[0])
        self.walk2 = B.add(a2.plot([], [], "o", ms=10, mfc="#e91e8c", mec="w", mew=1.5, zorder=10)[0])
        self.bloq2 = B.add(a2.plot([], [], "X", ms=12, mfc="#d62828", mec="w", mew=1.2, ls="", zorder=9)[0])
        self.od2 = B.add(a2.plot([], [], "o", ms=17, mfc="none", mec="#111", mew=2.4, ls="", zorder=9)[0])

        self.exp3 = B.add(a3.plot([], [], [], ".", ms=3, color="#f6a21e")[0])
        self.ruta3 = B.add(a3.plot([], [], [], color="#0b8a3e", lw=3.0)[0])
        self.rast3 = B.add(a3.plot([], [], [], color="#7b2cbf", lw=3.0)[0])
        self.walk3 = B.add(a3.plot([], [], [], "o", ms=10, mfc="#e91e8c", mec="w")[0])
        self.bloq3 = B.add(a3.plot([], [], [], "X", ms=11, mfc="#d62828", mec="w", ls="")[0])
        self.od3 = B.add(a3.plot([], [], [], "o", ms=13, mfc="none", mec="#111", mew=2, ls="")[0])

        self.txt = B.add(self.fig.text(0.215, 0.325, "", fontsize=10.5, va="top", color="#111"))
        self.txt2 = B.add(self.fig.text(0.215, 0.215, "", fontsize=9.5, va="top", color="#333", linespacing=1.5))
        self.fig.text(0.215, 0.03, "Espacio = iniciar   |   b = barrera en el tramo   |   a = ascensor fuera de servicio   |   "
                                   "r = reiniciar", fontsize=8.5, color="#666")

    def _xy(self, ids):
        N = self.G.nodos
        return [N[i]["x_px"] for i in ids], [N[i]["y_px"] for i in ids]

    def _xyz(self, ids):
        N = self.G.nodos
        return [N[i]["x"] for i in ids], [-N[i]["y"] for i in ids], [N[i]["z"] for i in ids]

    # ------------------------------------------------------------------ capas 3D
    def _seleccion(self, sim):
        """-> (pabellones a mostrar por dentro, nodos de referencia para el zoom)"""
        N = self.G.nodos
        if self.modo == "Campus":
            return set(), []
        if self.modo != "Auto":
            return {self.modo}, []
        ids = list(sim.ruta) if sim.ruta else [i for i in (sim.origen, sim.destino) if i]
        return {N[i]["pab"] for i in ids if N[i]["pab"]}, ids

    def _aplicar_capas(self, sel, ids):
        N = self.G.nodos
        pv = self.piso_ver
        ext_vis = self.modo in ("Auto", "Campus")
        for (tag, pmin, vert), c in self.col_aristas.items():
            if tag == "":
                vis = ext_vis
            else:
                vis = any(ch in sel for ch in tag)
                if vis and pv:
                    vis = (pmin == 0) or (pmin == pv) or (vert and pmin + 1 == pv)
            c.set_visible(vis)
        sel_losa = sel if sel else set(self.pabs)
        for (p, pi), c in self.losas.items():
            c.set_visible(p in sel_losa and (pv == 0 or pv == pi))
        for (p, pi), c in self.salas.items():
            c.set_visible(p in sel and (pv == 0 or pv == pi))
        for p, t in self.letras.items():
            t.set_visible(p in sel_losa)
        # limites + proporciones
        if sel:
            xs, ys, zs = [], [], [0.0]
            for p in sel:
                b = self.bbox[p]
                xs += [b[0], b[1]]
                ys += [b[2], b[3]]
                zs += [n["z"] for n in N.values() if n["pab"] == p]
            for i in ids:
                xs.append(N[i]["x"])
                ys.append(-N[i]["y"])
            zoom = True
        else:
            xs = [n["x"] for n in N.values()]
            ys = [-n["y"] for n in N.values()]
            zs = [n["z"] for n in N.values()]
            zoom = False
        m = 0.06 * max(max(xs) - min(xs), max(ys) - min(ys)) + 4
        x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
        zmax = max(max(zs), ALTO_PISO) + 2
        dx, dy = x1 - x0, y1 - y0
        zex = ZEXAG_CAMPUS if not zoom else float(np.clip(0.55 * max(dx, dy) / zmax, 1.5, 8.0))
        ax = self.ax3
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_zlim(0, zmax)
        ax.set_box_aspect((dx, dy, zmax * zex), zoom=1.1)

    # ------------------------------------------------------------------ actualizar
    def actualizar(self, sim):
        """Actualiza los artistas. Devuelve True si cambiaron las capas estaticas (hace falta redibujar todo)."""
        N = self.G.nodos
        sel, ids = self._seleccion(sim)
        firma = (self.modo, self.piso_ver, tuple(sorted(sel)),
                 (id(sim.ruta), sim.origen, sim.destino) if self.modo == "Auto" else None)
        cambio = firma != self._firma
        if cambio:
            self._firma = firma
            self._aplicar_capas(sel, ids)

        ex = sim.expandidos
        x, y = self._xy(ex)
        self.exp2.set_offsets(np.c_[x, y] if ex else np.empty((0, 2)))
        self.exp3.set_data_3d(*self._xyz(ex))
        ruta = sim.ruta or []
        self.ruta2.set_data(*self._xy(ruta))
        self.ruta3.set_data_3d(*self._xyz(ruta))
        rec = sim.recorrido
        self.rast2.set_data(*self._xy(rec))
        self.rast3.set_data_3d(*self._xyz(rec))

        w = sim.pos_walker()
        piso_w = ""
        if w:
            self.walk2.set_data([w[0]], [w[1]])
            self.walk3.set_data_3d([w[2]], [-w[3]], [w[4]])
            piso_w = f"   |   piso del caminante: {int(round(w[4] / ALTO_PISO)) + 1}"
        else:
            self.walk2.set_data([], [])
            self.walk3.set_data_3d([], [], [])

        bl = list(sim.aristas_bloq)
        mid = [((N[a]["x_px"] + N[b]["x_px"]) / 2, (N[a]["y_px"] + N[b]["y_px"]) / 2) for a, b in bl]
        mid += [(N[n]["x_px"], N[n]["y_px"]) for n in sim.nodos_bloq]
        self.bloq2.set_data([m[0] for m in mid], [m[1] for m in mid])
        b3 = [((N[a]["x"] + N[b]["x"]) / 2, -(N[a]["y"] + N[b]["y"]) / 2, (N[a]["z"] + N[b]["z"]) / 2) for a, b in bl]
        b3 += [(N[n]["x"], -N[n]["y"], N[n]["z"]) for n in sim.nodos_bloq]
        self.bloq3.set_data_3d([m[0] for m in b3], [m[1] for m in b3], [m[2] for m in b3])

        od = [i for i in (sim.origen, sim.destino) if i]
        self.od2.set_data(*self._xy(od))
        self.od3.set_data_3d(*self._xyz(od))

        self.txt.set_text(textwrap.fill(sim.msg, 78))
        modo = "SOLO ACCESIBLE" if sim.solo_acc else "TODAS LAS RUTAS (con escaleras)"
        o = N[sim.origen]["nombre"] if sim.origen else "-"
        d = N[sim.destino]["nombre"] if sim.destino else "-"
        self.txt2.set_text(f"Origen: {o}\nDestino: {d}\nModo: {modo}\n"
                           f"Nodos expandidos por A*: {sim.n_exp}   |   recorrido: {sim.distancia_recorrida():.0f} m"
                           f"   |   recalculos: {sim.recalculos}{piso_w}")
        return cambio

    def refrescar(self, sim):
        """actualizar + dibujar: completo si cambiaron las capas, por blitting si no."""
        if self.actualizar(sim) or self.blit.bg is None:
            self.fig.canvas.draw_idle()
        else:
            self.blit.update()

    def guardar(self, ruta, dpi=90):
        self.blit.suspender(True)
        self.fig.savefig(ruta, dpi=dpi)
        self.blit.suspender(False)
