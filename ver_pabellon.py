"""
Vista de un pabellon modelado en detalle: todos los pisos en 2D + torre 3D + ruta de ejemplo.
Uso:  python ver_pabellon.py A            (ventana)         python ver_pabellon.py I --png
      python ver_pabellon.py A --destino "Pabellon A p5 - Aula A-54"      (nombres: ver generador.opciones_destino)
Si no existe ruta accesible, se muestra la mas corta CON escaleras y se avisa en el titulo.
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
DESTINO = {"A": "Pabellon A p5 - Aula A-54", "I": "Biblioteca p7 - CUB-54 (aprox)"}
NOMBRE = {"A": "Pabellon A + Aula Magna", "I": "Biblioteca (Pabellon I)"}
NOMBRE_DEF = lambda p: f"Pabellon {p}"


def main():
    pab = next((a for a in sys.argv[1:] if len(a) == 1 and a.isalpha()), "A")
    G = generador.construir()
    op = generador.opciones_destino(G)
    if "--destino" in sys.argv:
        dest = op[sys.argv[sys.argv.index("--destino") + 1]]
    elif pab in DESTINO:
        dest = op[DESTINO[pab]]
    else:   # por defecto: una sala del ultimo piso
        zs = [n for n in G.nodos.values() if n["pab"] == pab and n["tipo"] == "zona"]
        dest = max(zs, key=lambda n: (n["piso"], n["id"]))["id"]
    ini = op["Entrada Av. Alonso de Molina"]
    ruta, costo, exp = alg.astar(G, ini, dest, solo_acc=True)
    aviso = "ruta ACCESIBLE"
    if ruta is None:
        ruta, costo, exp = alg.astar(G, ini, dest, solo_acc=False)
        aviso = "SIN RUTA ACCESIBLE (sin ascensor): se muestra la ruta con escaleras"
    pares = set(zip(ruta, ruta[1:])) | set(zip(ruta[1:], ruta))
    nodos = [n for n in G.nodos.values() if n["pab"] == pab]
    aristas = [e for e in G.aristas if G.nodos[e["a"]]["pab"] == pab and G.nodos[e["b"]]["pab"] == pab]
    pisos = max(n["piso"] for n in nodos)
    n_puertas = sum(1 for n in nodos if n["tipo"] == "puerta")

    fig = plt.figure(figsize=(20, 11))
    fig.suptitle(f"{NOMBRE.get(pab, NOMBRE_DEF(pab))} - {pisos} pisos | Entrada Alonso de Molina -> {G.nodos[dest]['etiqueta']} | {aviso}\n"
                 f"A*: {len(ruta)} nodos, costo {costo:.0f} m-eq, {exp} expandidos | {len(nodos)} nodos, {len(aristas)} aristas, "
                 f"{n_puertas} puertas (nodos)", fontsize=11.5, fontweight="bold")
    # ---- 3D
    a3 = fig.add_axes([-0.02, 0.03, 0.34, 0.86], projection="3d")
    COL = {"pasillo": "#aab4c2", "escalera": "#d62828", "ascensor": "#1b9e3e", "puerta": "#f28c1b"}
    for e in aristas:
        A, B = G.nodos[e["a"]], G.nodos[e["b"]]
        on = (e["a"], e["b"]) in pares
        a3.plot([A["x"], B["x"]], [-A["y"], -B["y"]], [A["z"] * ZE, B["z"] * ZE],
                color="#0b8a3e" if on else COL.get(e["tipo"], "#aab4c2"), lw=2.6 if on else 0.4, alpha=1 if on else .55)
    for tipo, c, m, s in (("zona", "#7b2cbf", "o", 5), ("puerta", "#f28c1b", "D", 7)):
        s_ = [n for n in nodos if n["tipo"] == tipo]
        a3.scatter([n["x"] for n in s_], [-n["y"] for n in s_], [n["z"] * ZE for n in s_], s=s, c=c, marker=m)
    xs3 = [n["x"] for n in nodos]
    ys3 = [-n["y"] for n in nodos]
    a3.set_box_aspect((max(xs3) - min(xs3), max(ys3) - min(ys3), 3.5 * (pisos - 1) * ZE + 4))
    a3.view_init(elev=24, azim=-58)
    a3.set_axis_off()
    for p in range(1, pisos + 1):
        a3.text(min(xs3) - 3, max(ys3), (p - 1) * 3.5 * ZE, f"p{p}", fontsize=9)
    # ---- 2D por piso
    xs = [n["x_px"] for n in nodos]
    ys = [n["y_px"] for n in nodos]
    cols = 3 if pisos <= 6 else 4
    w, h = 0.64 / cols, 0.42
    for p in range(1, pisos + 1):
        c, f = (p - 1) % cols, (p - 1) // cols
        ax = fig.add_axes([0.345 + c * (w + 0.005), 0.50 - f * 0.46, w, h])
        for e in aristas:
            A, B = G.nodos[e["a"]], G.nodos[e["b"]]
            if A["piso"] != p or B["piso"] != p:
                continue
            on = (e["a"], e["b"]) in pares
            ax.plot([A["x_px"], B["x_px"]], [A["y_px"], B["y_px"]],
                    color="#0b8a3e" if on else ("#f28c1b" if e["tipo"] == "puerta" else "#9aa7b8"),
                    lw=2.4 if on else 0.6, zorder=3 if on else 2)
        for n in nodos:
            if n["piso"] != p:
                continue
            t = n["tipo"]
            if t == "zona":
                ax.scatter([n["x_px"]], [n["y_px"]], s=14, c="#7b2cbf", zorder=4)
                ax.text(n["x_px"], n["y_px"] - 1.2, n["etiqueta"].replace("Aula ", "")[:26], fontsize=5, ha="center",
                        va="bottom", color="#4a1d7a")
            elif t == "puerta":
                ax.scatter([n["x_px"]], [n["y_px"]], marker="D", s=14, c="#f28c1b", edgecolors="k", linewidths=.3, zorder=5)
            elif t == "escalera":
                ax.scatter([n["x_px"]], [n["y_px"]], marker="v", s=55, c="#d62828", edgecolors="k", linewidths=.4, zorder=5)
            elif t == "ascensor":
                ax.scatter([n["x_px"]], [n["y_px"]], marker="^", s=55, c="#1b9e3e", edgecolors="k", linewidths=.4, zorder=5)
            else:
                ax.scatter([n["x_px"]], [n["y_px"]], s=3, c="#5b6b80", zorder=3)
        ax.set_xlim(min(xs) - 6, max(xs) + 6)
        ax.set_ylim(max(ys) + 6, min(ys) - 6)
        ax.set_aspect("equal")
        ax.set_title(f"Piso {p}", fontsize=10, fontweight="bold")
        ax.axis("off")
    leg = fig.add_axes([0.345 + 2 * (w + .005) if pisos <= 6 and pisos <= 4 else 0.345 + (pisos % cols) * (w + .005), 0.04, w, 0.4]) \
        if pisos % cols else fig.add_axes([0.345, 0.0, 0.01, 0.01])
    leg.axis("off")
    hd = [Line2D([0], [0], marker="v", color="w", mfc="#d62828", mec="k", ms=9, label="Escalera (no accesible)"),
          Line2D([0], [0], marker="^", color="w", mfc="#1b9e3e", mec="k", ms=9, label="Ascensor"),
          Line2D([0], [0], marker="D", color="w", mfc="#f28c1b", mec="k", ms=7, label="Puerta (nodo, ancho y escalon)"),
          Line2D([0], [0], marker="o", color="w", mfc="#7b2cbf", ms=7, label="Sala / aula (zona)"),
          Line2D([0], [0], color="#9aa7b8", lw=1.5, label="Pasillo"),
          Line2D([0], [0], color="#0b8a3e", lw=3, label="Ruta A*")]
    leg.legend(handles=hd, loc="upper left", fontsize=9.5, frameon=False)
    if "--png" in sys.argv:
        out = CARPETA / "capturas"
        out.mkdir(exist_ok=True)
        f = out / f"pabellon_{pab}_detalle.png"
        fig.savefig(f, dpi=105)
        print("Guardado", f)
    else:
        plt.show()


if __name__ == "__main__":
    main()
