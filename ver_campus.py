"""Vista general del campus: plano 2D con el grafo + 3D de todos los pabellones. python ver_campus.py [--png]"""
import sys
from pathlib import Path

import matplotlib
if "--png" in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib.lines import Line2D

import generador

CARPETA = Path(__file__).resolve().parent
DET = {"A": "#7b2cbf", "I": "#c2185b"}      # pabellones con detalle
ZE = 3.0


def main():
    G = generador.construir()
    N = G.nodos
    fig = plt.figure(figsize=(20, 10.5))
    n_det = sum(1 for n in N.values() if n["pab"] in DET)
    fig.suptitle(f"Campus Monterrico - grafo 3D | {len(N)} nodos, {len(G.aristas)} aristas | "
                 f"A-J modelados con salas y puertas ({sum(1 for n in N.values() if n['tipo'] == 'puerta')} puertas); K y L pendientes",
                 fontsize=12, fontweight="bold")
    a2 = fig.add_axes([0.0, 0.04, 0.5, 0.86])
    a2.imshow(imread(str(CARPETA / "plano.png")))
    for e in G.aristas:
        A, B = N[e["a"]], N[e["b"]]
        if A["piso"] > 1 or B["piso"] > 1:
            continue
        pab = A["pab"] or B["pab"]
        col = DET.get(pab, "#1f6fb2" if not pab else "#e08a00")
        a2.plot([A["x_px"], B["x_px"]], [A["y_px"], B["y_px"]], color=col, lw=1.0 if pab else 1.2, alpha=.85, zorder=3)
    for n in N.values():
        if n["piso"] <= 1 and n["tipo"] == "zona" and n["pab"] in DET:
            a2.scatter([n["x_px"]], [n["y_px"]], s=6, c=DET[n["pab"]], zorder=5)
        if n["tipo"] == "ascensor" and n["piso"] <= 1:
            a2.scatter([n["x_px"]], [n["y_px"]], marker="^", s=55, c="#1b9e3e", edgecolors="k", linewidths=.5, zorder=6)
    for p in "ABCDEFGHIJ":
        ns = [n for n in N.values() if n["pab"] == p and n["piso"] == 1 and n["tipo"] == "pasillo"]
        cx = sum(n["x_px"] for n in ns) / len(ns)
        cy = sum(n["y_px"] for n in ns) / len(ns)
        a2.text(cx, cy, p, fontsize=15, fontweight="bold", color="k", ha="center", va="center", zorder=7,
                bbox=dict(boxstyle="round,pad=.15", fc="w", ec=DET.get(p, "#e08a00"), alpha=.85))
    a2.set_xlim(30, 770)
    a2.set_ylim(765, 262)
    a2.axis("off")
    a2.set_title("Plano 2D (piso 1 y exterior)", fontsize=11)

    a3 = fig.add_axes([0.48, 0.02, 0.52, 0.9], projection="3d")
    # plano oficial como suelo del 3D (para ver distancias y espacios libres entre pabellones)
    import numpy as np
    from PIL import Image
    im = Image.open(CARPETA / "plano.png").convert("RGB").crop((30, 262, 770, 765)).resize((296, 200))
    tex = np.asarray(im) / 255.0
    X, Y = np.meshgrid(np.linspace(30, 770, 296) * generador.ESCALA, -np.linspace(262, 765, 200) * generador.ESCALA)
    a3.plot_surface(X, Y, np.full_like(X, -1.0), facecolors=tex, rstride=1, cstride=1, shade=False, zorder=0)
    for e in G.aristas:
        A, B = N[e["a"]], N[e["b"]]
        pab = A["pab"] or B["pab"]
        if e["tipo"] == "escalera":
            col, lw = "#d62828", .5
        elif e["tipo"] == "ascensor":
            col, lw = "#1b9e3e", 1.3
        else:
            col, lw = DET.get(pab, "#1f6fb2" if not pab else "#e08a00"), .45
        a3.plot([A["x"], B["x"]], [-A["y"], -B["y"]], [A["z"] * ZE, B["z"] * ZE], color=col, lw=lw, alpha=.7)
    xs = [n["x"] for n in N.values()]
    ys = [-n["y"] for n in N.values()]
    zs = [n["z"] * ZE for n in N.values()]
    a3.set_box_aspect((max(xs) - min(xs), max(ys) - min(ys), (max(zs) + 4) * 1.4))
    a3.view_init(elev=36, azim=-60)
    a3.set_axis_off()
    for p in "ABCDEFGHIJ":
        ns = [n for n in N.values() if n["pab"] == p]
        top = max(n["piso"] for n in ns)
        tn = [n for n in ns if n["piso"] == top]
        a3.text(sum(n["x"] for n in tn) / len(tn), -sum(n["y"] for n in tn) / len(tn), max(n["z"] for n in tn) * ZE + 5,
                p, fontsize=12, fontweight="bold", ha="center")
    h = [Line2D([0], [0], color="#1f6fb2", lw=2, label="Ruta exterior accesible"),
         Line2D([0], [0], color="#e08a00", lw=2, label="Pabellones B-H y J (salas + puertas)"),
         Line2D([0], [0], color="#7b2cbf", lw=2, label="A detallado (Aula Magna)"),
         Line2D([0], [0], color="#c2185b", lw=2, label="I detallado (Biblioteca)"),
         Line2D([0], [0], color="#d62828", lw=2, label="Escalera (no accesible)"),
         Line2D([0], [0], color="#1b9e3e", lw=2, label="Ascensor")]
    fig.legend(handles=h, loc="lower center", ncol=6, fontsize=9.5, frameon=False)
    if "--png" in sys.argv:
        out = CARPETA / "capturas"
        out.mkdir(exist_ok=True)
        fig.savefig(out / "campus_completo.png", dpi=105)
        print("Guardado", out / "campus_completo.png")
    else:
        plt.show()


if __name__ == "__main__":
    main()
