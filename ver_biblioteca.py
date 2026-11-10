"""
Vista dedicada de la Biblioteca (pabellon I): los 7 pisos en 2D + torre 3D, con una ruta accesible de ejemplo.
Uso:  python ver_biblioteca.py                      (ventana)
      python ver_biblioteca.py --png                (guarda capturas/biblioteca_7_pisos.png)
      python ver_biblioteca.py --destino "Biblioteca p6 - CUB-12"   (otro destino; ver opciones en generador.opciones_destino)
"""
import sys
from pathlib import Path

import matplotlib
if "--png" in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import algoritmos as alg
import generador

CARPETA = Path(__file__).resolve().parent
ZE = 5.0
COL = {"pasillo": "#aab4c2", "escalera": "#d62828", "ascensor": "#1b9e3e", "puerta": "#f28c1b"}


def main():
    G = generador.construir()
    op = generador.opciones_destino(G)
    destino = op["Biblioteca p7 - CUB-37"]
    if "--destino" in sys.argv:
        destino = op[sys.argv[sys.argv.index("--destino") + 1]]
    ruta, costo, exp = alg.astar(G, op["Entrada Av. Alonso de Molina"], destino, solo_acc=True)
    en_ruta = set(ruta)
    pares = set(zip(ruta, ruta[1:])) | set(zip(ruta[1:], ruta))

    fig = plt.figure(figsize=(19, 10.5))
    fig.suptitle(f"Biblioteca (Pabellon I) - 7 pisos | ruta accesible Entrada Alonso de Molina -> {G.nodos[destino]['etiqueta']} "
                 f"(A*, {len(ruta)} nodos, costo {costo:.0f} m-eq, {exp} expandidos)", fontsize=12, fontweight="bold")
    nodosI = [n for n in G.nodos.values() if n["pab"] == "I"]
    aristasI = [e for e in G.aristas if G.nodos[e["a"]]["pab"] == "I" and G.nodos[e["b"]]["pab"] == "I"]

    a3 = fig.add_axes([0.0, 0.03, 0.30, 0.9], projection="3d")
    for e in aristasI:
        A, B = G.nodos[e["a"]], G.nodos[e["b"]]
        on = (e["a"], e["b"]) in pares
        a3.plot([A["x"], B["x"]], [-A["y"], -B["y"]], [A["z"] * ZE, B["z"] * ZE],
                color="#0b8a3e" if on else COL.get(e["tipo"], "#aab4c2"), lw=2.4 if on else 0.4,
                alpha=1 if on else 0.6)
    z = [n for n in nodosI if n["tipo"] == "zona"]
    a3.scatter([n["x"] for n in z], [-n["y"] for n in z], [n["z"] * ZE for n in z], s=4, c="#7b2cbf")
    a3.set_axis_off()
    a3.set_box_aspect((1.3, 1.3, 1.6))
    a3.view_init(elev=22, azim=-68)
    for p in range(1, 8):
        a3.text(min(n["x"] for n in nodosI) - 8, -min(n["y"] for n in nodosI), (p - 1) * 3.5 * ZE, f"p{p}", fontsize=8)

    xs = [n["x_px"] for n in nodosI]
    ys = [n["y_px"] for n in nodosI]
    for p in range(1, 8):
        col, fila = (p - 1) % 4, (p - 1) // 4
        ax = fig.add_axes([0.31 + col * 0.172, 0.50 - fila * 0.47, 0.168, 0.43])
        for e in aristasI:
            A, B = G.nodos[e["a"]], G.nodos[e["b"]]
            if A["piso"] != p or B["piso"] != p:
                continue
            on = (e["a"], e["b"]) in pares
            ax.plot([A["x_px"], B["x_px"]], [A["y_px"], B["y_px"]], color="#0b8a3e" if on else "#9aa7b8",
                    lw=2.2 if on else 0.6, zorder=3 if on else 2)
        for n in nodosI:
            if n["piso"] != p:
                continue
            if n["tipo"] == "zona":
                ax.scatter([n["x_px"]], [n["y_px"]], s=9, c="#7b2cbf", zorder=4)
                et = n["etiqueta"].replace("(aprox)", "").replace("Oficina", "Of.").replace("Direccion de gestion del conocimiento", "Dir. gest. conoc.").replace("Jefatura corporativa centros de informacion", "Jef. corp. CI")
                ann = n["y_px"] < 560
                ax.text(n["x_px"], n["y_px"] - 2, et[:30], fontsize=3.8, ha="center", va="bottom", color="#4a1d7a",
                        rotation=90 if ann else 0)
            elif n["tipo"] == "escalera":
                ax.scatter([n["x_px"]], [n["y_px"]], marker="v", s=40, c="#d62828", edgecolors="k", linewidths=.4, zorder=5)
            elif n["tipo"] == "ascensor":
                ax.scatter([n["x_px"]], [n["y_px"]], marker="^", s=46, c="#1b9e3e", edgecolors="k", linewidths=.4, zorder=5)
            else:
                ax.scatter([n["x_px"]], [n["y_px"]], s=2.5, c="#5b6b80", zorder=3)
        ax.set_xlim(min(xs) - 8, max(xs) + 8)
        ax.set_ylim(max(ys) + 8, min(ys) - 8)
        ax.set_aspect("equal")
        ax.set_title(f"Piso {p}", fontsize=10, fontweight="bold")
        ax.axis("off")
    leg = fig.add_axes([0.31 + 3 * 0.172, 0.03, 0.168, 0.43])
    leg.axis("off")
    h = [Line2D([0], [0], marker="v", color="w", mfc="#d62828", mec="k", ms=9, label="Escalera (no accesible)"),
         Line2D([0], [0], marker="^", color="w", mfc="#1b9e3e", mec="k", ms=9, label="Ascensor (2 torres)"),
         Line2D([0], [0], marker="o", color="w", mfc="#7b2cbf", ms=6, label="Sala / cubiculo (zona)"),
         Line2D([0], [0], color="#9aa7b8", lw=1.5, label="Pasillo / anillo"),
         Line2D([0], [0], color="#0b8a3e", lw=3, label="Ruta A* accesible")]
    leg.legend(handles=h, loc="upper left", fontsize=9, frameon=False)
    leg.text(0, 0.35, f"Nodos de la Biblioteca: {len(nodosI)}\nAristas: {len(aristasI)}\n"
             "Centro con piso: p1, p2, p6, p7\n(p3-p5: vacio central)\nNumeracion CUB-xx: aproximada",
             fontsize=9, va="top")
    if "--png" in sys.argv:
        out = CARPETA / "capturas"
        out.mkdir(exist_ok=True)
        fig.savefig(out / "biblioteca_7_pisos.png", dpi=110)
        print("Guardado", out / "biblioteca_7_pisos.png", "| nodos I:", len(nodosI), "aristas:", len(aristasI))
    else:
        plt.show()


if __name__ == "__main__":
    main()
